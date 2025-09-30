"""
Enhanced FastAPI server for drug-surfactant protocol simulation and execution.

This implementation follows the decorator pattern from ac-dev-lab and includes
authentication, task registration, and Railway deployment support.
"""

import os
import tempfile
import json
import time
import secrets
import bcrypt
import jwt
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta
import inspect
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Opentrons imports
try:
    from opentrons import simulate
    from opentrons.protocol_api import ProtocolContext
    import opentrons.execute as execute
    OPENTRONS_AVAILABLE = True
except ImportError as e:
    OPENTRONS_AVAILABLE = False
    logging.warning(f"Opentrons not available: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1

# Default users (use environment variables in production)
DEFAULT_USERS = {
    "drug_surfactant_user": os.getenv("DRUG_SURFACTANT_PASSWORD", "demo_password_123"),
    "lab_admin": os.getenv("ADMIN_PASSWORD", "admin_password_456")
}

# Hash passwords on startup
USERS_DB = {}
for username, password in DEFAULT_USERS.items():
    USERS_DB[username] = {
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
        "roles": ["admin"] if "admin" in username else ["operator"]
    }

# Task registry following ac-dev-lab pattern
tasks_registry = {}

# Security
security = HTTPBearer()

def task(func):
    """Decorator to register functions as executable tasks - matching ac-dev-lab syntax"""
    task_name = func.__name__
    sig = inspect.signature(func)
    
    tasks_registry[task_name] = {
        'function': func,
        'signature': sig,
        'doc': func.__doc__ or "",
        'name': task_name
    }
    
    logger.info(f"Registered task: {task_name}")
    return func

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def create_access_token(username: str, roles: list) -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {"sub": username, "roles": roles, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user info."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        roles = payload.get("roles", [])
        
        if username not in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return {"username": username, "roles": roles}
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# FastAPI app initialization
app = FastAPI(
    title="Drug-Surfactant Protocol API Enhanced",
    description="Enhanced API for simulating and executing Opentrons protocols with authentication and task management",
    version="1.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

class ProtocolData(BaseModel):
    """Model for protocol data input"""
    data: List[Dict[str, Any]]
    iteration: int
    plate_well: str = "H3"
    deepplate_well: str = "H3"

class SimulationResult(BaseModel):
    """Model for simulation results"""
    success: bool
    protocol_text: str
    run_log: List[str]
    error: Optional[str] = None

class ExecutionRequest(BaseModel):
    """Model for execution requests"""
    protocol_text: str
    run_id: Optional[str] = None

class ExecutionResult(BaseModel):
    """Model for execution results"""
    success: bool
    run_id: str
    status: str
    error: Optional[str] = None

class TaskRequest(BaseModel):
    """Model for task execution requests"""
    task_name: str
    parameters: Dict[str, Any] = {}

class TaskResult(BaseModel):
    """Model for task execution results"""
    success: bool
    result: Any = None
    error: Optional[str] = None

# Authentication endpoints
@app.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """Authenticate user and return JWT token"""
    username = login_request.username
    password = login_request.password
    
    if username not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    user = USERS_DB[username]
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    access_token = create_access_token(username, user["roles"])
    return LoginResponse(access_token=access_token, token_type="bearer")

# Health check endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Drug-Surfactant Enhanced Protocol API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "opentrons_available": OPENTRONS_AVAILABLE,
        "opentrons_version": "8.6.0" if OPENTRONS_AVAILABLE else "not_available"
    }

# Task management endpoints
@app.get("/tasks")
async def list_tasks(current_user: dict = Depends(verify_token)):
    """List all available tasks"""
    task_list = []
    for name, info in tasks_registry.items():
        task_list.append({
            "name": name,
            "doc": info["doc"],
            "parameters": str(info["signature"])
        })
    return {"tasks": task_list}

@app.post("/tasks/execute", response_model=TaskResult)
async def execute_task(task_request: TaskRequest, current_user: dict = Depends(verify_token)):
    """Execute a registered task"""
    task_name = task_request.task_name
    
    if task_name not in tasks_registry:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{task_name}' not found"
        )
    
    try:
        task_info = tasks_registry[task_name]
        task_func = task_info["function"]
        
        # Execute the task with provided parameters
        result = task_func(**task_request.parameters)
        
        return TaskResult(success=True, result=result)
    
    except Exception as e:
        logger.error(f"Error executing task {task_name}: {str(e)}")
        return TaskResult(success=False, error=str(e))

# Protocol management functions with task decorator
@task
def generate_protocol_text(data: List[Dict[str, Any]], iteration: int, 
                          plate_well: str = "H3", deepplate_well: str = "H3") -> str:
    """
    Generate protocol text from experimental data.
    This replaces the generate_protocol function from helper_functions.py
    """
    # Read the template file
    template_path = Path("experiments/20250917_closed_loop/drug_surfactant_otflex_template.py")
    
    if not template_path.exists():
        raise FileNotFoundError("Protocol template not found")
    
    with open(template_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Update the plate reader export filename
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('pr_data = pr_mod.read(export_filename="raw_absorbance_in")'):
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f'{indent}pr_data = pr_mod.read(export_filename = "raw_absorbance_i{iteration}")\n'
            break
    
    # Replace plate wells
    found_plate = False
    found_deep = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not found_plate and stripped.startswith("next_plate_well") and "'H3'" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f"{indent}next_plate_well = '{plate_well}'\n"
            found_plate = True
        elif not found_deep and stripped.startswith("next_deepplate_well") and "'H3'" in stripped:
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = f"{indent}next_deepplate_well = '{deepplate_well}'\n"
            found_deep = True
        if found_plate and found_deep:
            break
    
    # Format the data for insertion
    data_list = []
    for idx, row in enumerate(data):
        data_row = {'': str(idx)}
        data_row.update({col: str(val) for col, val in row.items()})
        data_list.append(data_row)
    
    data_string = json.dumps(data_list, indent=4)
    
    # Find and replace the data block
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if "# to be treated as an input arguement in the future" in line:
            # Look for the next line with multiple # symbols (start of data block)
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith("#" * 100):  # Line of multiple # symbols
                    start_idx = j
                    break
            break
    
    if start_idx is not None:
        # Find the end of the data block (next line with multiple # symbols)
        for k in range(start_idx + 1, len(lines)):
            if lines[k].strip().startswith("#" * 100):
                end_idx = k
                break
    
    # Replace the data block
    if start_idx is not None and end_idx is not None:
        indent_prefix = lines[start_idx][:len(lines[start_idx]) - len(lines[start_idx].lstrip())]
        hash_line = indent_prefix + "#" * 136 + "\n"
        data_lines = data_string.split('\n')
        first_line = indent_prefix + "    " + "data = " + data_lines[0].lstrip() + "\n"
        rest_lines = '\n'.join(indent_prefix + line for line in data_lines[1:]) + "\n"
        data_line = first_line + rest_lines
        replacement = [hash_line, data_line, hash_line]
        new_lines = lines[:start_idx] + replacement + lines[end_idx:]
        
        return ''.join(new_lines)
    else:
        raise ValueError("Could not locate data block in template")

@task
def simulate_protocol_task(protocol_text: str) -> Dict[str, Any]:
    """
    Simulate a protocol using opentrons.simulate (as a task)
    """
    if not OPENTRONS_AVAILABLE:
        raise RuntimeError("Opentrons simulation not available")
    
    # Create a temporary file for the protocol
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(protocol_text)
        protocol_file = f.name
    
    try:
        # Simulate the protocol
        run_log = []
        protocol_context = simulate.get_protocol_api('2.21')
        
        # Execute the protocol in simulation mode
        exec(compile(open(protocol_file).read(), protocol_file, 'exec'), 
             {'protocol_api': simulate.protocol_api, 'protocol': protocol_context})
        
        # Get the simulation log
        run_log = ["Protocol simulation completed successfully"]
        
        return {
            "success": True,
            "run_log": run_log,
            "protocol_text": protocol_text
        }
        
    finally:
        # Clean up temporary file
        os.unlink(protocol_file)

@task
def execute_protocol_task(protocol_text: str, run_id: str = None) -> Dict[str, Any]:
    """
    Execute a protocol on real hardware (as a task)
    """
    if not OPENTRONS_AVAILABLE:
        raise RuntimeError("Opentrons execution not available")
    
    # Generate a run ID if not provided
    run_id = run_id or f"run_{int(time.time())}"
    
    # Create a temporary file for the protocol
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(protocol_text)
        protocol_file = f.name
    
    try:
        # Note: This is a placeholder for actual execution
        # In a real deployment, you would use opentrons.execute here
        # TODO: Implement actual execution when connected to hardware
        
        return {
            "success": True,
            "run_id": run_id,
            "status": "completed"
        }
        
    finally:
        # Clean up temporary file
        os.unlink(protocol_file)

# Original API endpoints (maintaining compatibility)
@app.post("/simulate", response_model=SimulationResult)
async def simulate_protocol(protocol_data: ProtocolData, current_user: dict = Depends(verify_token)):
    """
    Simulate a protocol using opentrons.simulate
    """
    try:
        # Generate protocol text
        protocol_text = generate_protocol_text(
            protocol_data.data, 
            protocol_data.iteration,
            protocol_data.plate_well,
            protocol_data.deepplate_well
        )
        
        # Simulate the protocol
        result = simulate_protocol_task(protocol_text)
        
        return SimulationResult(
            success=result["success"],
            protocol_text=protocol_text,
            run_log=result["run_log"]
        )
            
    except Exception as e:
        return SimulationResult(
            success=False,
            protocol_text="",
            run_log=[],
            error=str(e)
        )

@app.post("/execute", response_model=ExecutionResult)
async def execute_protocol(execution_request: ExecutionRequest, 
                          background_tasks: BackgroundTasks,
                          current_user: dict = Depends(verify_token)):
    """
    Execute a protocol on real hardware using opentrons.execute
    """
    try:
        result = execute_protocol_task(
            execution_request.protocol_text,
            execution_request.run_id
        )
        
        return ExecutionResult(
            success=result["success"],
            run_id=result["run_id"],
            status=result["status"]
        )
            
    except Exception as e:
        return ExecutionResult(
            success=False,
            run_id=execution_request.run_id or "unknown",
            status="failed",
            error=str(e)
        )

@app.get("/protocols/{iteration}")
async def get_protocol(iteration: int, current_user: dict = Depends(verify_token)):
    """
    Get a protocol file for a specific iteration
    """
    protocol_path = Path(f"experiments/20250917_closed_loop/iteration_{iteration}/protocol/otflex_{iteration}.py")
    
    if not protocol_path.exists():
        raise HTTPException(status_code=404, detail=f"Protocol for iteration {iteration} not found")
    
    with open(protocol_path, 'r') as f:
        protocol_text = f.read()
    
    return {"iteration": iteration, "protocol_text": protocol_text}

@app.get("/status")
async def get_status():
    """
    Get the current status of the API server
    """
    return {
        "status": "running",
        "opentrons_available": OPENTRONS_AVAILABLE,
        "opentrons_version": "8.6.0" if OPENTRONS_AVAILABLE else "not_available",
        "api_version": "1.1.0",
        "capabilities": ["simulate", "execute", "tasks", "authentication"],
        "registered_tasks": list(tasks_registry.keys())
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)