#!/usr/bin/env python3
"""
MQTT Test Subscriber
Tests subscription capabilities from HiveMQ broker.
"""

import sys
import time
import json
from datetime import datetime
sys.path.append('.')

from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics

class TestSubscriber(MQTTClientBase):
    """Test MQTT subscriber for verification."""
    
    def __init__(self):
        super().__init__(client_id="test_subscriber", role="robot")
        self.message_count = 0
        self.received_messages = []
        
        # Register message handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register handlers for different message types."""
        
        # Command handlers
        self.register_message_handler(mqtt_topics.Commands.START_PROTOCOL, self._handle_start_protocol)
        self.register_message_handler(mqtt_topics.Commands.STOP_PROTOCOL, self._handle_stop_protocol)
        self.register_message_handler(mqtt_topics.Commands.LOAD_EXPERIMENT, self._handle_load_experiment)
        self.register_message_handler(mqtt_topics.Commands.SET_PARAMETERS, self._handle_set_parameters)
        
        # Heartbeat handler
        self.register_message_handler(mqtt_topics.Heartbeat.ORCHESTRATOR, self._handle_heartbeat)
        
        # Discovery handler
        self.register_message_handler(mqtt_topics.Discovery.PING, self._handle_discovery_ping)
    
    def _handle_start_protocol(self, topic: str, data: dict):
        """Handle start protocol command."""
        print(f"📋 START PROTOCOL received:")
        print(f"   Protocol ID: {data.get('protocol_id', 'N/A')}")
        print(f"   Drug: {data.get('parameters', {}).get('drug', 'N/A')}")
        print(f"   Concentration: {data.get('parameters', {}).get('concentration', 'N/A')}")
        
        # Simulate sending acknowledgment
        self._send_acknowledgment(topic, data)
    
    def _handle_stop_protocol(self, topic: str, data: dict):
        """Handle stop protocol command."""
        print(f"🛑 STOP PROTOCOL received: {data}")
        self._send_acknowledgment(topic, data)
    
    def _handle_load_experiment(self, topic: str, data: dict):
        """Handle load experiment command."""
        print(f"🧪 LOAD EXPERIMENT received:")
        print(f"   Experiment ID: {data.get('experiment_id', 'N/A')}")
        print(f"   Drugs: {data.get('design', {}).get('drugs', 'N/A')}")
        print(f"   Surfactants: {len(data.get('design', {}).get('surfactants', []))} types")
        
        self._send_acknowledgment(topic, data)
    
    def _handle_set_parameters(self, topic: str, data: dict):
        """Handle set parameters command."""
        print(f"⚙️  SET PARAMETERS received:")
        print(f"   Sequence: {data.get('sequence_number', 'N/A')}")
        print(f"   Message: {data.get('test_message', 'N/A')}")
        
        self._send_acknowledgment(topic, data)
    
    def _handle_heartbeat(self, topic: str, data: dict):
        """Handle heartbeat message."""
        print(f"💓 HEARTBEAT from {data.get('client_id', 'unknown')}: {data.get('status', 'N/A')}")
    
    def _handle_discovery_ping(self, topic: str, data: dict):
        """Handle discovery ping."""
        print(f"🔍 DISCOVERY PING received: {data}")
        
        # Send pong response
        pong_data = {
            'device_type': 'opentrons_flex',
            'capabilities': ['liquid_handling', 'heating', 'shaking', 'absorbance_reading'],
            'version': '1.0.0',
            'status': 'ready'
        }
        
        self.publish_message(mqtt_topics.Discovery.PONG, pong_data)
        print("   Sent PONG response")
    
    def _send_acknowledgment(self, original_topic: str, original_data: dict):
        """Send acknowledgment for received commands."""
        ack_data = {
            'original_topic': original_topic,
            'status': 'received',
            'message_id': original_data.get('message_id', 'unknown')
        }
        
        self.publish_message(mqtt_topics.Status.ROBOT_STATUS, ack_data)
        print("   ✓ Acknowledgment sent")
    
    def _generic_message_handler(self, topic: str, data):
        """Generic handler for all messages."""
        self.message_count += 1
        self.received_messages.append({
            'topic': topic,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"\n📨 Message #{self.message_count} received on '{topic}':")
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"   {key}: {value}")
        else:
            print(f"   Content: {data}")
    
    def run_test(self, duration: int = 60):
        """
        Run subscriber test.
        
        Args:
            duration: How long to run the test in seconds
        """
        print("Starting MQTT Subscriber Test...")
        print(f"Will listen for messages for {duration} seconds...")
        
        if not self.connect():
            print("Failed to connect to MQTT broker")
            return False
        
        try:
            print("\n🎧 Listening for messages...")
            print("Subscribed topics:")
            
            subscription_topics = mqtt_topics.get_subscription_topics(self.role)
            for i, topic in enumerate(subscription_topics, 1):
                print(f"   {i}. {topic}")
            
            print(f"\nPress Ctrl+C to stop listening before {duration}s timeout...\n")
            
            # Listen for messages
            start_time = time.time()
            while (time.time() - start_time) < duration:
                time.sleep(1)
                
                # Send periodic heartbeat
                if int(time.time() - start_time) % 10 == 0:
                    self.send_heartbeat()
            
            print(f"\n📊 Test Summary:")
            print(f"   Messages received: {self.message_count}")
            print(f"   Duration: {duration} seconds")
            print(f"   Average rate: {self.message_count / duration:.2f} messages/second")
            
            return True
            
        except KeyboardInterrupt:
            print(f"\n⏹️  Test stopped by user after {int(time.time() - start_time)} seconds")
            print(f"📊 Messages received: {self.message_count}")
            return True
        except Exception as e:
            print(f"Test failed with error: {e}")
            return False
        finally:
            self.disconnect()
            print("Disconnected from broker")

def main():
    """Main function to run the subscriber test."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MQTT Subscriber Test')
    parser.add_argument('--duration', type=int, default=60, 
                       help='Duration to listen for messages (seconds)')
    
    args = parser.parse_args()
    
    subscriber = TestSubscriber()
    success = subscriber.run_test(duration=args.duration)
    
    if success:
        print("\n🎉 Subscriber test completed successfully!")
    else:
        print("\n❌ Subscriber test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()