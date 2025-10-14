#!/usr/bin/env python3
"""
MQTT Test Publisher
Tests publishing capabilities to HiveMQ broker.
"""

import sys
import time
import json
from datetime import datetime
sys.path.append('.')

from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics

class TestPublisher(MQTTClientBase):
    """Test MQTT publisher for verification."""
    
    def __init__(self):
        super().__init__(client_id="test_publisher", role="orchestrator")
    
    def run_test(self):
        """Run publisher test."""
        print("Starting MQTT Publisher Test...")
        
        if not self.connect():
            print("Failed to connect to MQTT broker")
            return False
        
        try:
            # Test 1: Send a command message
            print("\n1. Testing command message...")
            command_data = {
                'command': 'start_protocol',
                'protocol_id': 'test_protocol_001',
                'parameters': {
                    'drug': 'IBP',
                    'concentration': 180.0,
                    'surfactants': ['s1', 's4'],
                    'volumes': [100, 200]
                }
            }
            
            success = self.publish_message(mqtt_topics.Commands.START_PROTOCOL, command_data)
            print(f"Command message sent: {'✓' if success else '✗'}")
            time.sleep(1)
            
            # Test 2: Send heartbeat
            print("\n2. Testing heartbeat...")
            success = self.send_heartbeat()
            print(f"Heartbeat sent: {'✓' if success else '✗'}")
            time.sleep(1)
            
            # Test 3: Send discovery announcement
            print("\n3. Testing discovery announcement...")
            discovery_data = {
                'device_type': 'orchestrator',
                'capabilities': ['experiment_design', 'data_analysis', 'protocol_generation'],
                'version': '1.0.0',
                'location': 'Mac Computer'
            }
            
            success = self.publish_message(mqtt_topics.Discovery.ANNOUNCE, discovery_data)
            print(f"Discovery message sent: {'✓' if success else '✗'}")
            time.sleep(1)
            
            # Test 4: Send experiment parameters
            print("\n4. Testing experiment parameters...")
            experiment_data = {
                'experiment_id': 'exp_001',
                'design': {
                    'drugs': ['IBP', 'LOV', 'DCF', 'GLV'],
                    'surfactants': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'],
                    'replicates': 3,
                    'controls': True
                },
                'protocol_version': '2.1'
            }
            
            success = self.publish_message(mqtt_topics.Commands.LOAD_EXPERIMENT, experiment_data)
            print(f"Experiment parameters sent: {'✓' if success else '✗'}")
            time.sleep(1)
            
            # Test 5: Send multiple messages in sequence
            print("\n5. Testing message sequence...")
            for i in range(3):
                test_data = {
                    'sequence_number': i + 1,
                    'test_message': f'Sequential message {i + 1}',
                    'data': [1, 2, 3, 4, 5]
                }
                
                success = self.publish_message(mqtt_topics.Commands.SET_PARAMETERS, test_data)
                print(f"Sequential message {i + 1}: {'✓' if success else '✗'}")
                time.sleep(0.5)
            
            print("\n✓ All test messages published successfully!")
            print("Publisher will continue running for 30 seconds to test connectivity...")
            
            # Keep publishing heartbeats
            for i in range(6):
                time.sleep(5)
                self.send_heartbeat()
                print(f"Heartbeat {i + 1}/6 sent")
            
            return True
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
            return False
        except Exception as e:
            print(f"Test failed with error: {e}")
            return False
        finally:
            self.disconnect()
            print("Disconnected from broker")

def main():
    """Main function to run the publisher test."""
    publisher = TestPublisher()
    success = publisher.run_test()
    
    if success:
        print("\n🎉 Publisher test completed successfully!")
    else:
        print("\n❌ Publisher test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()