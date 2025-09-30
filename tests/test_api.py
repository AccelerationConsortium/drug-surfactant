"""
Test script for the API-based drug-surfactant protocol system
"""

import requests
import json

# Test data similar to what's in the template
test_data = [
    {
        'trial_index': '0',
        'drug': '0',
        's1': '0',
        's2': '00',
        's3': '0.0',
        's4': '0.0',
        's5': '0',
        's6': '0.0',
        's7': '0.0',
        's8': '0.0',
        's9': '0.0',
        's10': '0.0',
        's11': '0.0',
        's12': '0.0',
        'dmso': '0',
        'water': '500.0'
    },
    {
        'trial_index': '1',
        'drug': '120',
        's1': '300',
        's2': '00',
        's3': '0.0',
        's4': '0.0',
        's5': '0',
        's6': '0.0',
        's7': '0.0',
        's8': '0.0',
        's9': '0.0',
        's10': '0.0',
        's11': '0.0',
        's12': '0.0',
        'dmso': '0',
        'water': '500.0'
    }
]

def test_api_health():
    """Test the API health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_protocol_simulation():
    """Test protocol simulation"""
    if not test_api_health():
        print("API is not healthy, skipping simulation test")
        return False
    
    payload = {
        "data": test_data,
        "iteration": 0,
        "plate_well": "H3",
        "deepplate_well": "H3"
    }
    
    try:
        print("\nTesting protocol simulation...")
        response = requests.post("http://localhost:8000/simulate", json=payload, timeout=30)
        print(f"Simulation response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Simulation success: {result['success']}")
            if result['success']:
                print("✅ Protocol simulation completed successfully!")
                print(f"Protocol text length: {len(result['protocol_text'])} characters")
                print(f"Run log: {result['run_log']}")
                return True
            else:
                print(f"❌ Simulation failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during simulation test: {e}")
        return False

def test_using_api_helper():
    """Test using the new API helper functions"""
    try:
        print("\nTesting API helper functions...")
        import api_helper_functions as api_hf
        
        # Test API health check
        if api_hf.check_api_health():
            print("✅ API health check passed")
        else:
            print("❌ API health check failed")
            return False
        
        # Test simulation through helper function
        simulation_result = api_hf.simulate_protocol(test_data, 0)
        
        if simulation_result['success']:
            print("✅ API helper simulation successful!")
            return True
        else:
            print(f"❌ API helper simulation failed: {simulation_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during API helper test: {e}")
        return False

if __name__ == "__main__":
    print("Testing Drug-Surfactant API System")
    print("=" * 50)
    
    # Test basic API functionality
    if test_protocol_simulation():
        print("\n✅ Direct API test passed!")
    else:
        print("\n❌ Direct API test failed!")
    
    # Test API helper functions
    if test_using_api_helper():
        print("\n✅ API helper function test passed!")
    else:
        print("\n❌ API helper function test failed!")
    
    print("\n" + "=" * 50)
    print("Testing complete!")