"""
Simplified test for API helper functions without Ax dependencies
"""

import sys
sys.path.append('/home/runner/work/drug-surfactant/drug-surfactant')

import requests
import json

# Test data
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
        'dmso': '0',
        'water': '500.0'
    }
]

def test_api_simulation():
    """Test the core API simulation functionality"""
    try:
        # Simple health check
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("❌ API health check failed")
            return False
        print("✅ API health check passed")
        
        # Test simulation endpoint
        payload = {
            "data": test_data,
            "iteration": 0,
            "plate_well": "H3",
            "deepplate_well": "H3"
        }
        
        response = requests.post("http://localhost:8000/simulate", json=payload)
        if response.status_code != 200:
            print(f"❌ Simulation failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        result = response.json()
        if not result['success']:
            print(f"❌ Simulation returned failure: {result.get('error')}")
            return False
            
        print("✅ Protocol simulation successful!")
        print(f"Protocol length: {len(result['protocol_text'])} characters")
        
        # Test that the protocol was properly generated
        protocol_text = result['protocol_text']
        if 'def run(protocol: protocol_api.ProtocolContext):' not in protocol_text:
            print("❌ Protocol doesn't contain expected function definition")
            return False
            
        if 'data = [' not in protocol_text:
            print("❌ Protocol doesn't contain data block")
            return False
            
        print("✅ Protocol content validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        return False

if __name__ == "__main__":
    print("Testing API Simulation Core Functionality")
    print("=" * 50)
    
    if test_api_simulation():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")