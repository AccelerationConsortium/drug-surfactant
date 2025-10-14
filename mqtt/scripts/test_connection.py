#!/usr/bin/env python3
"""
MQTT Connection Test
Comprehensive test of MQTT broker connectivity and message exchange.
"""

import sys
import time
import threading
import json
from datetime import datetime
sys.path.append('.')

from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics
from mqtt.config.mqtt_config import mqtt_config

class ConnectionTester:
    """Comprehensive MQTT connection and messaging test."""
    
    def __init__(self):
        self.publisher = None
        self.subscriber = None
        self.test_results = {
            'connection': False,
            'publish': False,
            'subscribe': False,
            'message_exchange': False,
            'messages_sent': 0,
            'messages_received': 0
        }
    
    def test_configuration(self):
        """Test MQTT configuration validity."""
        print("🔧 Testing MQTT Configuration...")
        
        print(f"   Broker Host: {mqtt_config.broker_host}")
        print(f"   Broker Port: {mqtt_config.broker_port}")
        print(f"   Use TLS: {mqtt_config.use_tls}")
        print(f"   Username: {'✓' if mqtt_config.username else '✗'}")
        print(f"   Password: {'✓' if mqtt_config.password else '✗'}")
        
        is_valid = mqtt_config.validate()
        print(f"   Configuration Valid: {'✓' if is_valid else '✗'}")
        
        if not is_valid:
            print("\n❌ Configuration validation failed!")
            print("   Please check your .env file settings.")
            return False
        
        return True
    
    def test_basic_connection(self):
        """Test basic connection to MQTT broker."""
        print("\n🔌 Testing Basic Connection...")
        
        try:
            # Create a simple client for connection test
            test_client = MQTTClientBase(client_id="connection_test", role="orchestrator")
            
            print("   Attempting to connect to broker...")
            success = test_client.connect()
            
            if success:
                print("   ✓ Successfully connected to MQTT broker")
                test_client.disconnect()
                self.test_results['connection'] = True
                return True
            else:
                print("   ✗ Failed to connect to MQTT broker")
                return False
                
        except Exception as e:
            print(f"   ✗ Connection test failed: {e}")
            return False
    
    def setup_subscriber(self):
        """Set up the test subscriber."""
        class TestSubscriber(MQTTClientBase):
            def __init__(self, parent_tester):
                super().__init__(client_id="test_subscriber", role="robot")
                self.parent = parent_tester
                self.register_message_handler(mqtt_topics.Commands.START_PROTOCOL, self.handle_test_message)
                self.register_message_handler(mqtt_topics.Discovery.PING, self.handle_ping)
            
            def handle_test_message(self, topic, data):
                print(f"   📨 Subscriber received: {data.get('test_id', 'unknown')}")
                self.parent.test_results['messages_received'] += 1
                
                # Send response
                response = {
                    'test_id': data.get('test_id'),
                    'status': 'received',
                    'response_from': 'subscriber'
                }
                self.publish_message(mqtt_topics.Status.ROBOT_STATUS, response)
            
            def handle_ping(self, topic, data):
                print(f"   🏓 Ping received, sending pong...")
                pong_data = {
                    'ping_id': data.get('ping_id'),
                    'pong_from': 'test_subscriber'
                }
                self.publish_message(mqtt_topics.Discovery.PONG, pong_data)
        
        self.subscriber = TestSubscriber(self)
        return self.subscriber.connect()
    
    def setup_publisher(self):
        """Set up the test publisher."""
        class TestPublisher(MQTTClientBase):
            def __init__(self, parent_tester):
                super().__init__(client_id="test_publisher", role="orchestrator")
                self.parent = parent_tester
                self.register_message_handler(mqtt_topics.Status.ROBOT_STATUS, self.handle_response)
                self.register_message_handler(mqtt_topics.Discovery.PONG, self.handle_pong)
            
            def handle_response(self, topic, data):
                print(f"   📨 Publisher received response: {data.get('test_id', 'unknown')}")
                self.parent.test_results['messages_received'] += 1
            
            def handle_pong(self, topic, data):
                print(f"   🏓 Pong received from: {data.get('pong_from', 'unknown')}")
                self.parent.test_results['messages_received'] += 1
        
        self.publisher = TestPublisher(self)
        return self.publisher.connect()
    
    def test_message_exchange(self):
        """Test bidirectional message exchange."""
        print("\n💬 Testing Message Exchange...")
        
        if not self.setup_subscriber():
            print("   ✗ Failed to connect subscriber")
            return False
        
        if not self.setup_publisher():
            print("   ✗ Failed to connect publisher")
            return False
        
        print("   ✓ Both clients connected")
        time.sleep(2)  # Allow subscriptions to complete
        
        try:
            # Test 1: Send command message
            print("\n   Test 1: Command message...")
            test_data = {
                'test_id': 'cmd_001',
                'command': 'test_command',
                'timestamp': datetime.now().isoformat()
            }
            
            success = self.publisher.publish_message(mqtt_topics.Commands.START_PROTOCOL, test_data)
            if success:
                self.test_results['messages_sent'] += 1
                print("   ✓ Command message sent")
            else:
                print("   ✗ Command message failed to send")
            
            time.sleep(2)
            
            # Test 2: Send discovery ping
            print("\n   Test 2: Discovery ping...")
            ping_data = {
                'ping_id': 'ping_001',
                'sender': 'test_publisher'
            }
            
            success = self.publisher.publish_message(mqtt_topics.Discovery.PING, ping_data)
            if success:
                self.test_results['messages_sent'] += 1
                print("   ✓ Discovery ping sent")
            else:
                print("   ✗ Discovery ping failed to send")
            
            time.sleep(2)
            
            # Test 3: Heartbeat exchange
            print("\n   Test 3: Heartbeat exchange...")
            self.publisher.send_heartbeat()
            self.subscriber.send_heartbeat()
            self.test_results['messages_sent'] += 2
            print("   ✓ Heartbeats sent")
            
            time.sleep(3)  # Wait for message processing
            
            # Evaluate results
            if self.test_results['messages_received'] > 0:
                self.test_results['message_exchange'] = True
                print(f"   ✓ Message exchange successful!")
                print(f"   📊 Sent: {self.test_results['messages_sent']}, Received: {self.test_results['messages_received']}")
                return True
            else:
                print("   ✗ No messages received - check broker connectivity")
                return False
                
        except Exception as e:
            print(f"   ✗ Message exchange test failed: {e}")
            return False
        finally:
            if self.publisher:
                self.publisher.disconnect()
            if self.subscriber:
                self.subscriber.disconnect()
    
    def run_comprehensive_test(self):
        """Run all tests in sequence."""
        print("🚀 Starting MQTT Comprehensive Connection Test")
        print("=" * 50)
        
        # Test 1: Configuration
        if not self.test_configuration():
            return False
        
        # Test 2: Basic connection
        if not self.test_basic_connection():
            return False
        
        # Test 3: Message exchange
        if not self.test_message_exchange():
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! MQTT infrastructure is working correctly.")
        
        # Print summary
        print("\n📋 Test Summary:")
        print(f"   Configuration: {'✓' if self.test_results['connection'] else '✗'}")
        print(f"   Connection: {'✓' if self.test_results['connection'] else '✗'}")
        print(f"   Message Exchange: {'✓' if self.test_results['message_exchange'] else '✗'}")
        print(f"   Messages Sent: {self.test_results['messages_sent']}")
        print(f"   Messages Received: {self.test_results['messages_received']}")
        
        return True

def main():
    """Main function to run comprehensive test."""
    tester = ConnectionTester()
    
    try:
        success = tester.run_comprehensive_test()
        if success:
            print("\n✅ MQTT infrastructure test completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ MQTT infrastructure test failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()