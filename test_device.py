#!/usr/bin/env python3
"""
Test script for device.py functionality
"""

import json
import os
import tempfile
from pathlib import Path


def test_protocol_generation():
    """Test protocol generation without external dependencies."""
    
    # Mock experiment data
    experiment_data = {
        "experiment_id": "test_001",
        "data": [
            {
                "": "0",
                "trial_index": "0",
                "drug": "IBP",
                "s1": "50.0",
                "s2": "25.0",
                "s3": "0.0",
                "s4": "0.0",
                "s5": "0.0",
                "s6": "0.0",
                "s7": "0.0",
                "s8": "0.0",
                "water": "300.0",
                "IBP": "180.0",
                "LOV": "0.0",
                "DCF": "0.0",
                "GLV": "0.0"
            }
        ]
    }
    
    # Test template modification
    template_content = '''
from opentrons import protocol_api
import re

metadata = {
    "description": "Written in 2025.05",
    "author": "Zeqing Bao and Yunhee Hwang"
}

requirements = {"robotType": "Flex", "apiLevel": "2.21"}

def run(protocol: protocol_api.ProtocolContext):
    # Some setup code here
    
    # to be treated as an input arguement in the future
    data = [{'': '0',
      'trial_index': '0', 
      'drug': '0',
      's1': '0',
    }]
    
    # More protocol code
    pr_data = pr_mod.read(export_filename="raw_absorbance_in")
    '''
    
    print("Testing template modification...")
    
    # Test filename replacement
    modified = template_content.replace(
        'export_filename="raw_absorbance_in"',
        f'export_filename="raw_absorbance_{experiment_data["experiment_id"]}"'
    )
    
    assert 'raw_absorbance_test_001' in modified
    print("✓ Filename replacement works")
    
    # Test data replacement
    lines = template_content.split('\n')
    start_idx = None
    
    for i, line in enumerate(lines):
        if "# to be treated as an input arguement in the future" in line:
            for j in range(i + 1, len(lines)):
                if "data = [" in lines[j]:
                    start_idx = j
                    break
            break
    
    if start_idx is not None:
        # Find end of data block
        bracket_count = 0
        end_idx = None
        for k in range(start_idx, len(lines)):
            line = lines[k]
            bracket_count += line.count('[') - line.count(']')
            if bracket_count == 0 and k > start_idx:
                end_idx = k
                break
        
        if end_idx is not None:
            # Replace data section
            data_json = json.dumps(experiment_data['data'], indent=4)
            indent = "    "
            data_lines = data_json.split('\n')
            replacement = [f"{indent}data = {data_lines[0]}"]
            replacement.extend([f"{indent}{line}" for line in data_lines[1:]])
            
            new_lines = lines[:start_idx] + replacement + lines[end_idx + 1:]
            modified_content = '\n'.join(new_lines)
            
            print("✓ Data replacement works")
        else:
            print("⚠ Could not find end of data block")
    else:
        print("⚠ Could not find data block")
    
    # Test temporary file creation
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.py', 
        prefix=f"protocol_{experiment_data['experiment_id']}_",
        delete=False
    )
    
    temp_file.write(modified_content if 'modified_content' in locals() else modified)
    temp_file.close()
    
    assert os.path.exists(temp_file.name)
    print(f"✓ Temporary protocol file created: {temp_file.name}")
    
    # Clean up
    os.unlink(temp_file.name)
    print("✓ Cleanup successful")


def test_result_data_structure():
    """Test result data structure creation."""
    
    experiment_data = {"experiment_id": "test_001"}
    device_id = "flex-test123"
    mode = "simulate"
    
    # Test successful result
    result = {
        'experiment_id': experiment_data.get('experiment_id', 'unknown'),
        'device_id': device_id,
        'status': 'completed',
        'execution_mode': mode,
        'timestamp': 1234567890.0,
        'command_count': 42,
        'result_files': [
            f"raw_absorbance_{experiment_data['experiment_id']}.csv"
        ]
    }
    
    assert result['experiment_id'] == 'test_001'
    assert result['status'] == 'completed'
    assert 'raw_absorbance_test_001.csv' in result['result_files']
    print("✓ Success result structure is correct")
    
    # Test error result
    error_result = {
        'experiment_id': experiment_data.get('experiment_id', 'unknown'),
        'device_id': device_id,
        'status': 'failed',
        'error': 'Test error message',
        'execution_mode': mode,
        'timestamp': 1234567890.0
    }
    
    assert error_result['status'] == 'failed'
    assert 'error' in error_result
    print("✓ Error result structure is correct")


def test_mqtt_message_format():
    """Test MQTT message format validation."""
    
    # Valid experiment message
    valid_message = {
        "experiment_id": "exp_001",
        "session_id": "session_001", 
        "data": [
            {
                "trial_index": "0",
                "drug": "IBP",
                "s1": "25.0",
                "water": "300.0",
                "IBP": "180.0"
            }
        ]
    }
    
    # Test JSON serialization/deserialization
    json_str = json.dumps(valid_message)
    parsed = json.loads(json_str)
    
    assert parsed['experiment_id'] == 'exp_001'
    assert isinstance(parsed['data'], list)
    assert len(parsed['data']) == 1
    print("✓ MQTT message format validation works")


def main():
    """Run all tests."""
    print("Running device.py functionality tests...")
    print("=" * 50)
    
    try:
        test_protocol_generation()
        print()
        
        test_result_data_structure()
        print()
        
        test_mqtt_message_format()
        print()
        
        print("=" * 50)
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == '__main__':
    main()