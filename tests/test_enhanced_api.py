#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced drug-surfactant API.

This script validates the enhanced API implementation including:
- Authentication system
- Task management with decorator pattern
- Protocol generation and simulation
- Railway deployment readiness
"""

import subprocess
import time
import requests
import json
import pandas as pd
import signal
import os
import sys
from pathlib import Path

def run_test(test_name: str, test_func):
    """Run a test and report results"""
    print(f"🧪 {test_name}...")
    try:
        result = test_func()
        if result:
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED")
        return result
    except Exception as e:
        print(f"❌ {test_name} - ERROR: {e}")
        return False

def test_enhanced_file_structure():
    """Test that all enhanced files are present"""
    required_files = [
        "enhanced_api_server.py",
        "enhanced_api_helper_functions.py",
        "enhanced_api_workflow_demo.ipynb",
        "deploy_railway.sh",
        "requirements.txt",
        "railway.toml",
        "Dockerfile"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"Missing files: {missing_files}")
        return False
    
    return True

def test_enhanced_dependencies():
    """Test that enhanced dependencies can be imported"""
    try:
        import fastapi
        import uvicorn
        import jwt
        import bcrypt
        from jose import jwt as jose_jwt
        import requests
        import pandas as pd
        print("All enhanced dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False

def start_enhanced_api_server():
    """Start the enhanced API server"""
    print("Starting enhanced API server...")
    process = subprocess.Popen(
        [sys.executable, "enhanced_api_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(8)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Enhanced API server started successfully")
            return process
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            process.terminate()
            return None
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        process.terminate()
        return None

def test_enhanced_authentication():
    """Test JWT authentication system"""
    try:
        # Test health endpoint (no auth required)
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            return False
        
        # Test login with correct credentials
        login_response = requests.post(
            "http://localhost:8000/login",
            json={"username": "drug_surfactant_user", "password": "demo_password_123"}
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            return False
        
        token_data = login_response.json()
        if "access_token" not in token_data:
            print("No access token in response")
            return False
        
        # Test authenticated endpoint
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        tasks_response = requests.get("http://localhost:8000/tasks", headers=headers)
        
        if tasks_response.status_code != 200:
            print(f"Authenticated request failed: {tasks_response.status_code}")
            return False
        
        # Test invalid credentials
        bad_login = requests.post(
            "http://localhost:8000/login",
            json={"username": "invalid", "password": "invalid"}
        )
        
        if bad_login.status_code != 401:
            print("Invalid credentials should return 401")
            return False
        
        print("Authentication system working correctly")
        return True
        
    except Exception as e:
        print(f"Authentication test error: {e}")
        return False

def test_task_management():
    """Test task registration and execution"""
    try:
        # Login first
        login_response = requests.post(
            "http://localhost:8000/login",
            json={"username": "drug_surfactant_user", "password": "demo_password_123"}
        )
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # List tasks
        tasks_response = requests.get("http://localhost:8000/tasks", headers=headers)
        if tasks_response.status_code != 200:
            return False
        
        tasks_data = tasks_response.json()
        tasks = tasks_data["tasks"]
        
        # Check expected tasks are registered
        expected_tasks = ["generate_protocol_text", "simulate_protocol_task", "execute_protocol_task"]
        registered_task_names = [task["name"] for task in tasks]
        
        for expected_task in expected_tasks:
            if expected_task not in registered_task_names:
                print(f"Missing expected task: {expected_task}")
                return False
        
        # Test task execution
        sample_data = [{
            "trial_index": 0,
            "drug": 25.5,
            "s1": 10, "s2": 5, "s3": 15, "s4": 8, "s5": 12, "s6": 3,
            "s7": 7, "s8": 20, "s9": 1, "s10": 9, "s11": 6, "s12": 4,
            "surfactant_conc": 30,
            "drug_conc": 25
        }]
        
        task_response = requests.post(
            "http://localhost:8000/tasks/execute",
            headers=headers,
            json={
                "task_name": "generate_protocol_text",
                "parameters": {
                    "data": sample_data,
                    "iteration": 99,
                    "plate_well": "A1",
                    "deepplate_well": "A1"
                }
            }
        )
        
        if task_response.status_code != 200:
            print(f"Task execution failed: {task_response.status_code}")
            print(task_response.text)
            return False
        
        task_result = task_response.json()
        if not task_result["success"]:
            print(f"Task execution unsuccessful: {task_result.get('error')}")
            return False
        
        print(f"Task management working correctly - {len(tasks)} tasks registered")
        return True
        
    except Exception as e:
        print(f"Task management test error: {e}")
        return False

def test_enhanced_protocol_simulation():
    """Test enhanced protocol simulation"""
    try:
        # Login first
        login_response = requests.post(
            "http://localhost:8000/login",
            json={"username": "drug_surfactant_user", "password": "demo_password_123"}
        )
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test protocol simulation
        sample_data = [
            {
                "trial_index": 0,
                "drug": 25.5,
                "s1": 10, "s2": 5, "s3": 15, "s4": 8, "s5": 12, "s6": 3,
                "s7": 7, "s8": 20, "s9": 1, "s10": 9, "s11": 6, "s12": 4,
                "surfactant_conc": 30,
                "drug_conc": 25
            }
        ]
        
        simulate_response = requests.post(
            "http://localhost:8000/simulate",
            headers=headers,
            json={
                "data": sample_data,
                "iteration": 999,
                "plate_well": "A1",
                "deepplate_well": "A1"
            },
            timeout=60
        )
        
        if simulate_response.status_code != 200:
            print(f"Simulation failed: {simulate_response.status_code}")
            print(simulate_response.text)
            return False
        
        sim_result = simulate_response.json()
        if not sim_result["success"]:
            print(f"Simulation unsuccessful: {sim_result.get('error')}")
            return False
        
        if len(sim_result["protocol_text"]) < 1000:
            print("Generated protocol seems too short")
            return False
        
        print("Enhanced protocol simulation working correctly")
        return True
        
    except Exception as e:
        print(f"Protocol simulation test error: {e}")
        return False

def test_enhanced_helper_functions():
    """Test enhanced helper functions"""
    try:
        # Import the enhanced helper functions
        sys.path.insert(0, '.')
        import enhanced_api_helper_functions as eapi_hf
        
        # Test connection
        health = eapi_hf.api_health_check()
        if health["status"] != "healthy":
            return False
        
        # Test login
        token = eapi_hf.login()
        if not token:
            return False
        
        # Test task listing
        tasks = eapi_hf.list_available_tasks()
        if len(tasks) < 3:
            return False
        
        print("Enhanced helper functions working correctly")
        return True
        
    except Exception as e:
        print(f"Helper functions test error: {e}")
        return False

def test_api_status():
    """Test comprehensive API status"""
    try:
        response = requests.get("http://localhost:8000/status")
        if response.status_code != 200:
            return False
        
        status = response.json()
        
        # Check expected fields
        required_fields = ["status", "opentrons_available", "api_version", "capabilities", "registered_tasks"]
        for field in required_fields:
            if field not in status:
                print(f"Missing status field: {field}")
                return False
        
        # Check capabilities
        expected_capabilities = ["simulate", "execute", "tasks", "authentication"]
        for capability in expected_capabilities:
            if capability not in status["capabilities"]:
                print(f"Missing capability: {capability}")
                return False
        
        print(f"API Status: {status['status']}, Version: {status['api_version']}")
        return True
        
    except Exception as e:
        print(f"API status test error: {e}")
        return False

def test_railway_deployment_readiness():
    """Test Railway deployment configuration"""
    try:
        # Check railway.toml exists and has required sections
        railway_config = Path("railway.toml")
        if not railway_config.exists():
            print("railway.toml not found")
            return False
        
        # Check Dockerfile exists
        dockerfile = Path("Dockerfile")
        if not dockerfile.exists():
            print("Dockerfile not found")
            return False
        
        # Check deployment script
        deploy_script = Path("deploy_railway.sh")
        if not deploy_script.exists():
            print("deploy_railway.sh not found")
            return False
        
        # Check if script is executable
        if not os.access(deploy_script, os.X_OK):
            print("deploy_railway.sh is not executable")
            return False
        
        # Check requirements.txt has authentication dependencies
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        auth_deps = ["pyjwt", "bcrypt", "python-jose"]
        for dep in auth_deps:
            if dep not in requirements:
                print(f"Missing authentication dependency: {dep}")
                return False
        
        print("Railway deployment configuration ready")
        return True
        
    except Exception as e:
        print(f"Railway deployment test error: {e}")
        return False

def main():
    """Run all enhanced tests"""
    print("🚀 Enhanced Drug-Surfactant API Test Suite")
    print("=" * 50)
    
    # Test file structure
    if not run_test("Enhanced File Structure", test_enhanced_file_structure):
        print("❌ Critical files missing - stopping tests")
        return False
    
    # Test dependencies
    if not run_test("Enhanced Dependencies", test_enhanced_dependencies):
        print("❌ Dependencies not available - stopping tests")
        return False
    
    # Start the enhanced API server
    server_process = start_enhanced_api_server()
    if not server_process:
        print("❌ Cannot start enhanced API server - stopping tests")
        return False
    
    try:
        # Run all tests
        tests_passed = 0
        total_tests = 6
        
        if run_test("Authentication System", test_enhanced_authentication):
            tests_passed += 1
        
        if run_test("Task Management", test_task_management):
            tests_passed += 1
        
        if run_test("Enhanced Protocol Simulation", test_enhanced_protocol_simulation):
            tests_passed += 1
        
        if run_test("Enhanced Helper Functions", test_enhanced_helper_functions):
            tests_passed += 1
        
        if run_test("API Status", test_api_status):
            tests_passed += 1
        
        if run_test("Railway Deployment Readiness", test_railway_deployment_readiness):
            tests_passed += 1
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All enhanced tests passed! The enhanced API is ready for deployment.")
            return True
        else:
            print(f"⚠️  {total_tests - tests_passed} tests failed. Please fix issues before deployment.")
            return False
    
    finally:
        # Clean up: stop the server
        if server_process:
            print("\n🧹 Cleaning up: stopping API server...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)