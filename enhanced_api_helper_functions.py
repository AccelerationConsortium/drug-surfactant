"""
Enhanced API helper functions for drug-surfactant protocol management.

This module provides helper functions that interface with the enhanced FastAPI server
featuring authentication, task management, and improved error handling.
"""

import os
import requests
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

# API Configuration
# Default to Railway production URL if available, fallback to localhost
API_BASE_URL = os.getenv("DRUG_SURFACTANT_API_URL") or os.getenv("RAILWAY_PUBLIC_DOMAIN") or "http://localhost:8000"
if "RAILWAY_PUBLIC_DOMAIN" in os.environ and not API_BASE_URL.startswith("http"):
    API_BASE_URL = f"https://{API_BASE_URL}"
API_USERNAME = os.getenv("DRUG_SURFACTANT_USERNAME", "drug_surfactant_user")
API_PASSWORD = os.getenv("DRUG_SURFACTANT_PASSWORD", "demo_password_123")

# Global token storage
_access_token = None

class APIError(Exception):
    """Custom exception for API errors"""
    pass

def get_access_token() -> str:
    """Get or refresh access token"""
    global _access_token
    
    if _access_token is None:
        _access_token = login()
    
    return _access_token

def login(username: str = None, password: str = None) -> str:
    """
    Login to the API and get access token
    
    Args:
        username: Username (defaults to environment variable)
        password: Password (defaults to environment variable)
        
    Returns:
        Access token string
        
    Raises:
        APIError: If login fails
    """
    username = username or API_USERNAME
    password = password or API_PASSWORD
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/login",
            json={"username": username, "password": password},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        token = data["access_token"]
        
        logger.info(f"Successfully logged in as {username}")
        return token
        
    except requests.exceptions.RequestException as e:
        raise APIError(f"Login failed: {e}")

def get_auth_headers() -> Dict[str, str]:
    """Get authorization headers with current token"""
    token = get_access_token()
    return {"Authorization": f"Bearer {token}"}

def api_health_check() -> Dict[str, Any]:
    """
    Check API health status
    
    Returns:
        Health status dictionary
        
    Raises:
        APIError: If health check fails
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise APIError(f"Health check failed: {e}")

def list_available_tasks() -> List[Dict[str, Any]]:
    """
    List all available tasks from the API
    
    Returns:
        List of task information dictionaries
        
    Raises:
        APIError: If task listing fails
    """
    try:
        headers = get_auth_headers()
        response = requests.get(
            f"{API_BASE_URL}/tasks",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        return data["tasks"]
        
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to list tasks: {e}")

def execute_task(task_name: str, parameters: Dict[str, Any]) -> Any:
    """
    Execute a specific task via the API
    
    Args:
        task_name: Name of the task to execute
        parameters: Parameters to pass to the task
        
    Returns:
        Task execution result
        
    Raises:
        APIError: If task execution fails
    """
    try:
        headers = get_auth_headers()
        response = requests.post(
            f"{API_BASE_URL}/tasks/execute",
            headers=headers,
            json={"task_name": task_name, "parameters": parameters},
            timeout=120
        )
        response.raise_for_status()
        
        data = response.json()
        if not data["success"]:
            raise APIError(f"Task execution failed: {data.get('error', 'Unknown error')}")
        
        return data["result"]
        
    except requests.exceptions.RequestException as e:
        raise APIError(f"Task execution failed: {e}")

def generate_and_simulate_protocol(df_vol: pd.DataFrame, iteration: int, 
                                   plate_well: str = "H3", deepplate_well: str = "H3") -> Tuple[str, Dict[str, Any]]:
    """
    Generate protocol from volume data and simulate it via API
    
    Args:
        df_vol: DataFrame containing volume data for the experiment
        iteration: Iteration number for the experiment
        plate_well: Starting plate well (default: "H3")
        deepplate_well: Starting deep plate well (default: "H3")
        
    Returns:
        Tuple of (protocol_text, simulation_result)
        
    Raises:
        APIError: If protocol generation or simulation fails
    """
    try:
        # Convert DataFrame to list of dictionaries
        data = df_vol.to_dict('records')
        
        # Use the API to simulate the protocol
        headers = get_auth_headers()
        response = requests.post(
            f"{API_BASE_URL}/simulate",
            headers=headers,
            json={
                "data": data,
                "iteration": iteration,
                "plate_well": plate_well,
                "deepplate_well": deepplate_well
            },
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        
        if not result["success"]:
            raise APIError(f"Protocol simulation failed: {result.get('error', 'Unknown error')}")
        
        logger.info(f"Protocol for iteration {iteration} generated and simulated successfully")
        
        return result["protocol_text"], {
            "success": result["success"],
            "run_log": result["run_log"]
        }
        
    except requests.exceptions.RequestException as e:
        raise APIError(f"Protocol generation/simulation failed: {e}")

def run_protocol_on_robot(protocol_text: str, iteration: int, run_id: str = None) -> Dict[str, Any]:
    """
    Execute protocol on Opentrons robot via API
    
    Args:
        protocol_text: Complete protocol code to execute
        iteration: Iteration number
        run_id: Optional run ID (will be generated if not provided)
        
    Returns:
        Execution result dictionary
        
    Raises:
        APIError: If protocol execution fails
    """
    try:
        run_id = run_id or f"iteration_{iteration}"
        
        headers = get_auth_headers()
        response = requests.post(
            f"{API_BASE_URL}/execute",
            headers=headers,
            json={
                "protocol_text": protocol_text,
                "run_id": run_id
            },
            timeout=300  # Longer timeout for execution
        )
        response.raise_for_status()
        
        result = response.json()
        
        if not result["success"]:
            raise APIError(f"Protocol execution failed: {result.get('error', 'Unknown error')}")
        
        logger.info(f"Protocol executed successfully with run_id: {result['run_id']}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        raise APIError(f"Protocol execution failed: {e}")

def get_api_status() -> Dict[str, Any]:
    """
    Get comprehensive API status including capabilities and registered tasks
    
    Returns:
        Status dictionary
        
    Raises:
        APIError: If status check fails
    """
    try:
        response = requests.get(f"{API_BASE_URL}/status", timeout=10)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise APIError(f"Status check failed: {e}")

def generate_protocol_via_task(data: List[Dict[str, Any]], iteration: int, 
                               plate_well: str = "H3", deepplate_well: str = "H3") -> str:
    """
    Generate protocol using the task-based API
    
    Args:
        data: Experimental data as list of dictionaries
        iteration: Iteration number
        plate_well: Starting plate well
        deepplate_well: Starting deep plate well
        
    Returns:
        Generated protocol text
        
    Raises:
        APIError: If protocol generation fails
    """
    return execute_task("generate_protocol_text", {
        "data": data,
        "iteration": iteration,
        "plate_well": plate_well,
        "deepplate_well": deepplate_well
    })

def simulate_protocol_via_task(protocol_text: str) -> Dict[str, Any]:
    """
    Simulate protocol using the task-based API
    
    Args:
        protocol_text: Protocol code to simulate
        
    Returns:
        Simulation result dictionary
        
    Raises:
        APIError: If simulation fails
    """
    return execute_task("simulate_protocol_task", {
        "protocol_text": protocol_text
    })

def execute_protocol_via_task(protocol_text: str, run_id: str = None) -> Dict[str, Any]:
    """
    Execute protocol using the task-based API
    
    Args:
        protocol_text: Protocol code to execute
        run_id: Optional run ID
        
    Returns:
        Execution result dictionary
        
    Raises:
        APIError: If execution fails
    """
    return execute_task("execute_protocol_task", {
        "protocol_text": protocol_text,
        "run_id": run_id
    })

# Deprecated functions for backward compatibility
def upload_file_to_robot(local_file_path: str, remote_file_name: str) -> None:
    """
    DEPRECATED: This function is deprecated in favor of API-based protocol execution.
    
    Use generate_and_simulate_protocol() and run_protocol_on_robot() instead.
    """
    import warnings
    warnings.warn(
        "upload_file_to_robot() is deprecated. Use the new API-based functions: "
        "generate_and_simulate_protocol() and run_protocol_on_robot()",
        DeprecationWarning,
        stacklevel=2
    )
    logger.warning("upload_file_to_robot() called - this function is deprecated")

# Convenience function for testing
def test_api_connection() -> bool:
    """
    Test connection to the API
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        health = api_health_check()
        status = get_api_status()
        
        print(f"✅ API Connection Test Results:")
        print(f"   Health Status: {health['status']}")
        print(f"   Opentrons Available: {health['opentrons_available']}")
        print(f"   API Version: {status['api_version']}")
        print(f"   Capabilities: {', '.join(status['capabilities'])}")
        print(f"   Registered Tasks: {len(status['registered_tasks'])}")
        
        return True
        
    except APIError as e:
        print(f"❌ API Connection Failed: {e}")
        return False

if __name__ == "__main__":
    # Test the API connection when run directly
    test_api_connection()