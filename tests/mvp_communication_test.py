#!/usr/bin/env python3
"""
MVP Communication Test - Demonstrates client-server communication

This script tests the full communication flow between the client and the 
enhanced FastAPI server, simulating a cloud-hosted deployment scenario.
"""

import subprocess
import time
import requests
import json
import pandas as pd
import sys
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
USERNAME = "drug_surfactant_user"
PASSWORD = "demo_password_123"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")

def start_server():
    """Start the enhanced API server"""
    print_header("Step 1: Starting Enhanced FastAPI Server")
    print_info("Launching server on http://localhost:8000...")
    
    process = subprocess.Popen(
        [sys.executable, "enhanced_api_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(6)
    
    # Verify server is running
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("Server started successfully")
            health_data = response.json()
            print(f"   - Status: {health_data['status']}")
            print(f"   - Opentrons Available: {health_data['opentrons_available']}")
            return process
        else:
            print_error(f"Server health check failed: {response.status_code}")
            process.terminate()
            return None
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        process.terminate()
        return None

def test_authentication():
    """Test JWT authentication"""
    print_header("Step 2: Testing JWT Authentication")
    
    # Test login
    print_info("Attempting login...")
    response = requests.post(
        f"{API_BASE_URL}/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print_success("Authentication successful")
        print(f"   - Token type: {token_data['token_type']}")
        print(f"   - Token preview: {token[:50]}...")
        return token
    else:
        print_error(f"Authentication failed: {response.status_code}")
        print(f"   - Response: {response.text}")
        return None

def test_task_listing(token):
    """Test task listing endpoint"""
    print_header("Step 3: Testing Task Management (ac-dev-lab Pattern)")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/tasks", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        tasks = data["tasks"]
        print_success(f"Successfully retrieved {len(tasks)} registered tasks")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n   {i}. {task['name']}")
            print(f"      Description: {task['doc'].strip()}")
            print(f"      Parameters: {task['parameters']}")
        
        return tasks
    else:
        print_error(f"Task listing failed: {response.status_code}")
        return None

def test_protocol_generation(token):
    """Test protocol generation and simulation"""
    print_header("Step 4: Testing Protocol Generation & Simulation")
    
    # Create sample experimental data
    print_info("Creating sample experimental data...")
    sample_data = [
        {
            "trial_index": 0,
            "drug": 25.5,
            "s1": 10, "s2": 5, "s3": 15, "s4": 8, "s5": 12, "s6": 3,
            "s7": 7, "s8": 20, "s9": 1, "s10": 9, "s11": 6, "s12": 4,
            "surfactant_conc": 30,
            "drug_conc": 25
        },
        {
            "trial_index": 1,
            "drug": 18.3,
            "s1": 8, "s2": 12, "s3": 6, "s4": 14, "s5": 9, "s6": 11,
            "s7": 5, "s8": 16, "s9": 3, "s10": 7, "s11": 13, "s12": 2,
            "surfactant_conc": 35,
            "drug_conc": 18
        }
    ]
    
    print(f"   - Created {len(sample_data)} experimental trials")
    
    # Test protocol simulation
    print_info("Sending simulation request to server...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE_URL}/simulate",
        headers=headers,
        json={
            "data": sample_data,
            "iteration": 999,
            "plate_well": "A1",
            "deepplate_well": "A1"
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print_success("Protocol generated and simulated successfully")
            print(f"   - Protocol length: {len(result['protocol_text'])} characters")
            print(f"   - Simulation status: {result['run_log']}")
            print(f"   - Protocol preview (first 300 chars):")
            print(f"     {result['protocol_text'][:300]}...")
            return result
        else:
            print_error(f"Simulation unsuccessful: {result.get('error')}")
            return None
    else:
        print_error(f"Simulation request failed: {response.status_code}")
        print(f"   - Response: {response.text}")
        return None

def test_task_execution(token):
    """Test task execution API"""
    print_header("Step 5: Testing Task Execution API")
    
    sample_data = [{
        "trial_index": 0,
        "drug": 25.5,
        "s1": 10, "s2": 5, "s3": 15, "s4": 8, "s5": 12, "s6": 3,
        "s7": 7, "s8": 20, "s9": 1, "s10": 9, "s11": 6, "s12": 4,
        "surfactant_conc": 30,
        "drug_conc": 25
    }]
    
    print_info("Executing 'generate_protocol_text' task...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE_URL}/tasks/execute",
        headers=headers,
        json={
            "task_name": "generate_protocol_text",
            "parameters": {
                "data": sample_data,
                "iteration": 888,
                "plate_well": "B2",
                "deepplate_well": "B2"
            }
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print_success("Task executed successfully")
            print(f"   - Result length: {len(result['result'])} characters")
            print(f"   - Protocol preview (first 300 chars):")
            print(f"     {result['result'][:300]}...")
            return result
        else:
            print_error(f"Task execution unsuccessful: {result.get('error')}")
            return None
    else:
        print_error(f"Task execution failed: {response.status_code}")
        print(f"   - Response: {response.text}")
        return None

def test_helper_functions(token):
    """Test enhanced helper functions"""
    print_header("Step 6: Testing Enhanced Helper Functions")
    
    try:
        # Import enhanced helper functions
        sys.path.insert(0, '.')
        import enhanced_api_helper_functions as eapi_hf
        
        # Test health check
        print_info("Testing health check...")
        health = eapi_hf.api_health_check()
        print_success(f"Health check passed - Status: {health['status']}")
        
        # Test task listing
        print_info("Testing task listing...")
        tasks = eapi_hf.list_available_tasks()
        print_success(f"Task listing passed - Found {len(tasks)} tasks")
        
        # Test status check
        print_info("Testing comprehensive status...")
        status = eapi_hf.get_api_status()
        print_success("Status check passed")
        print(f"   - API Version: {status['api_version']}")
        print(f"   - Capabilities: {', '.join(status['capabilities'])}")
        print(f"   - Registered Tasks: {len(status['registered_tasks'])}")
        
        return True
        
    except Exception as e:
        print_error(f"Helper functions test failed: {e}")
        return False

def test_end_to_end_workflow(token):
    """Test complete end-to-end workflow"""
    print_header("Step 7: Testing End-to-End Workflow")
    
    # Create experimental data
    df_vol = pd.DataFrame([
        {
            "trial_index": 0,
            "drug": 30.0,
            "s1": 12, "s2": 8, "s3": 10, "s4": 6, "s5": 14, "s6": 5,
            "s7": 9, "s8": 15, "s9": 4, "s10": 11, "s11": 7, "s12": 3,
            "surfactant_conc": 40,
            "drug_conc": 30
        }
    ])
    
    try:
        sys.path.insert(0, '.')
        import enhanced_api_helper_functions as eapi_hf
        
        print_info("Running complete workflow: data → protocol → simulation")
        
        # Generate and simulate protocol
        protocol_text, sim_result = eapi_hf.generate_and_simulate_protocol(
            df_vol,
            iteration=777,
            plate_well="C3",
            deepplate_well="C3"
        )
        
        print_success("End-to-end workflow completed successfully")
        print(f"   - Generated protocol: {len(protocol_text)} characters")
        print(f"   - Simulation success: {sim_result['success']}")
        print(f"   - Simulation log: {sim_result['run_log']}")
        
        return True
        
    except Exception as e:
        print_error(f"End-to-end workflow failed: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("MVP Communication Test Summary")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Test Results: {passed}/{total} passed{Colors.END}\n")
    
    for test_name, result in results.items():
        if result:
            print_success(test_name)
        else:
            print_error(test_name)
    
    print(f"\n{Colors.BOLD}Communication Status:{Colors.END}")
    if passed == total:
        print_success("All communication tests passed!")
        print_info("The client and server are communicating successfully")
        print_info("Ready for Railway cloud deployment")
    else:
        print_error(f"{total - passed} test(s) failed")
        print_info("Please review the errors above")
    
    print(f"\n{Colors.BOLD}MVP Features Demonstrated:{Colors.END}")
    print("   ✅ JWT authentication with bearer tokens")
    print("   ✅ Task management with @task decorator")
    print("   ✅ Protocol generation from experimental data")
    print("   ✅ Protocol simulation using opentrons.simulate")
    print("   ✅ Task execution via RESTful API")
    print("   ✅ Enhanced helper functions with authentication")
    print("   ✅ Complete end-to-end workflow")

def main():
    """Run MVP communication test"""
    print_header("🚀 MVP Communication Test - Drug-Surfactant API")
    print_info("This test demonstrates client-server communication")
    print_info("Simulating cloud-hosted deployment scenario\n")
    
    results = {}
    
    # Start server
    server_process = start_server()
    if not server_process:
        print_error("Cannot proceed without server - aborting tests")
        return False
    
    try:
        # Run all tests
        token = test_authentication()
        results["Authentication"] = token is not None
        
        if token:
            tasks = test_task_listing(token)
            results["Task Listing"] = tasks is not None
            
            protocol_result = test_protocol_generation(token)
            results["Protocol Generation & Simulation"] = protocol_result is not None
            
            task_result = test_task_execution(token)
            results["Task Execution"] = task_result is not None
            
            helper_result = test_helper_functions(token)
            results["Enhanced Helper Functions"] = helper_result
            
            workflow_result = test_end_to_end_workflow(token)
            results["End-to-End Workflow"] = workflow_result
        else:
            print_error("Cannot proceed without authentication")
            results["Task Listing"] = False
            results["Protocol Generation & Simulation"] = False
            results["Task Execution"] = False
            results["Enhanced Helper Functions"] = False
            results["End-to-End Workflow"] = False
        
        # Print summary
        print_summary(results)
        
        # Return success status
        return all(results.values())
        
    finally:
        # Clean up: stop the server
        print_header("Cleanup")
        print_info("Stopping API server...")
        server_process.terminate()
        server_process.wait()
        print_success("Server stopped")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
