#!/usr/bin/env python3
"""
Example usage of the Opentrons Flex device listener

This script demonstrates how to configure and run the device listener
with different modes and settings.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def example_simulation_mode():
    """Example of running in simulation mode."""
    
    print("=== Running in Simulation Mode ===")
    
    # Set environment variables for simulation
    os.environ['OPENTRONS_MODE'] = 'simulate'
    os.environ['MQTT_HOST'] = 'localhost'  # Would be your actual MQTT broker
    os.environ['MQTT_PORT'] = '1883'
    os.environ['DEVICE_ID'] = 'flex-demo-001'
    
    # Import and create device (this would normally run the listener)
    try:
        from device import FlexDeviceListener
        
        device = FlexDeviceListener()
        print(f"Device created with ID: {os.environ['DEVICE_ID']}")
        print(f"Mode: {os.environ['OPENTRONS_MODE']}")
        print("Note: This is a demo - actual MQTT connection would require a broker")
        
        # Demonstrate protocol generation
        sample_experiment = {
            "experiment_id": "demo_exp_001",
            "session_id": "demo_session",
            "data": [
                {
                    "": "0",
                    "trial_index": "0",
                    "drug": "IBP",
                    "s1": "25.0",
                    "s2": "15.0", 
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
        
        print("\nGenerating protocol for sample experiment...")
        try:
            protocol_file = device.generate_protocol_from_experiment(sample_experiment)
            print(f"✓ Protocol generated: {protocol_file}")
            
            # Clean up
            os.unlink(protocol_file)
            print("✓ Cleanup completed")
            
        except FileNotFoundError as e:
            print(f"⚠ Template file not found: {e}")
            print("This is expected in a test environment without the full project structure")
            
    except ImportError as e:
        print(f"⚠ Import error: {e}")
        print("This may be due to missing dependencies like paho-mqtt or opentrons")


def example_execute_mode():
    """Example of configuration for execute mode."""
    
    print("\n=== Execute Mode Configuration ===")
    
    # This would be the configuration for actual execution on the Flex
    config = {
        'OPENTRONS_MODE': 'execute',
        'MQTT_HOST': 'your-mqtt-broker.com',
        'MQTT_PORT': '8883',
        'MQTT_USERNAME': 'your-username',
        'MQTT_PASSWORD': 'your-password',
        'DEVICE_ID': 'flex-lab-001'
    }
    
    print("Environment variables for execute mode:")
    for key, value in config.items():
        if 'PASSWORD' in key:
            print(f"  {key}=***hidden***")
        else:
            print(f"  {key}={value}")
    
    print("\nTo run in execute mode:")
    print("1. Set the above environment variables")
    print("2. Ensure the Flex is properly connected and calibrated")
    print("3. Run: python device.py")


def example_mqtt_messages():
    """Show example MQTT message formats."""
    
    print("\n=== MQTT Message Examples ===")
    
    # Example experiment message (published to lab/experiments/new)
    experiment_message = {
        "experiment_id": "exp_20250101_001",
        "session_id": "session_001",
        "timestamp": 1704067200.0,
        "data": [
            {
                "": "0",
                "trial_index": "0",
                "drug": "IBP",
                "s1": "30.0",
                "s2": "20.0",
                "s3": "0.0",
                "s4": "0.0",
                "s5": "0.0",
                "s6": "0.0",
                "s7": "0.0", 
                "s8": "0.0",
                "water": "280.0",
                "IBP": "180.0",
                "LOV": "0.0",
                "DCF": "0.0",
                "GLV": "0.0"
            }
        ]
    }
    
    print("Experiment message (lab/experiments/new):")
    import json
    print(json.dumps(experiment_message, indent=2))
    
    # Example result message (published to lab/experiments/result)
    result_message = {
        "experiment_id": "exp_20250101_001",
        "device_id": "flex-lab-001",
        "status": "completed",
        "execution_mode": "execute",
        "timestamp": 1704067800.0,
        "command_count": 156,
        "result_files": [
            "raw_absorbance_exp_20250101_001.csv"
        ]
    }
    
    print("\nResult message (lab/experiments/result):")
    print(json.dumps(result_message, indent=2))


def main():
    """Run all examples."""
    print("Opentrons Flex Device Listener - Usage Examples")
    print("=" * 60)
    
    example_simulation_mode()
    example_execute_mode() 
    example_mqtt_messages()
    
    print("\n" + "=" * 60)
    print("For more information, see device.py and the README.md")


if __name__ == '__main__':
    main()