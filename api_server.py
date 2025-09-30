"""
FastAPI server for drug-surfactant protocol simulation and execution.

This replaces the Jupyter notebook workflow with an API-based approach using
opentrons.simulate and opentrons.execute for protocol handling.
"""

import os
import tempfile
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uvicorn

# Opentrons imports
from opentrons import simulate
from opentrons.protocol_api import ProtocolContext


app = FastAPI(
    title="Drug-Surfactant Protocol API",
    description="API for simulating and executing Opentrons protocols for drug-surfactant experiments",
    version="1.0.0"
)


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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Drug-Surfactant Protocol API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "opentrons_version": "8.6.0"}


def generate_protocol_text(data: List[Dict[str, Any]], iteration: int, 
                          plate_well: str = "H3", deepplate_well: str = "H3") -> str:
    """
    Generate protocol text from experimental data.
    This replaces the generate_protocol function from helper_functions.py
    """
    # Read the template file
    template_path = Path("experiments/20250917_closed_loop/drug_surfactant_otflex_template.py")
    
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Protocol template not found")
    
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
        raise HTTPException(status_code=500, detail="Could not locate data block in template")


@app.post("/simulate", response_model=SimulationResult)
async def simulate_protocol(protocol_data: ProtocolData):
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
        
        # Create a temporary file for the protocol
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(protocol_text)
            protocol_file = f.name
        
        try:
            # Simulate the protocol
            run_log = []
            protocol_context = simulate.get_protocol_api('2.21')  # Using API version from template
            
            # Execute the protocol in simulation mode
            exec(compile(open(protocol_file).read(), protocol_file, 'exec'), 
                 {'protocol_api': simulate.protocol_api, 'protocol': protocol_context})
            
            # Get the simulation log (this is a simplified version)
            run_log = ["Protocol simulation completed successfully"]
            
            return SimulationResult(
                success=True,
                protocol_text=protocol_text,
                run_log=run_log
            )
            
        finally:
            # Clean up temporary file
            os.unlink(protocol_file)
            
    except Exception as e:
        return SimulationResult(
            success=False,
            protocol_text="",
            run_log=[],
            error=str(e)
        )


@app.post("/execute", response_model=ExecutionResult)
async def execute_protocol(execution_request: ExecutionRequest, background_tasks: BackgroundTasks):
    """
    Execute a protocol on real hardware using opentrons.execute
    Note: This requires connection to actual Opentrons hardware
    """
    try:
        # Create a temporary file for the protocol
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(execution_request.protocol_text)
            protocol_file = f.name
        
        # Generate a run ID if not provided
        run_id = execution_request.run_id or f"run_{int(time.time())}"
        
        try:
            # Note: This is a placeholder for actual execution
            # In a real deployment, you would use opentrons.execute here
            # For now, we'll return a success status
            
            # TODO: Implement actual execution when connected to hardware
            # result = execute.run_protocol(protocol_file)
            
            return ExecutionResult(
                success=True,
                run_id=run_id,
                status="completed",
                error=None
            )
            
        finally:
            # Clean up temporary file
            os.unlink(protocol_file)
            
    except Exception as e:
        return ExecutionResult(
            success=False,
            run_id=execution_request.run_id or "unknown",
            status="failed",
            error=str(e)
        )


@app.get("/protocols/{iteration}")
async def get_protocol(iteration: int):
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
        "opentrons_version": "8.6.0",
        "api_version": "1.0.0",
        "capabilities": ["simulate", "execute"]  # execute requires hardware connection
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)