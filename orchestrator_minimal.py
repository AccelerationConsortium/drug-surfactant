#!/usr/bin/env python3
"""
Minimal orchestrator for testing MQTT functionality.
This bypasses the helper_functions import issues for testing purposes.
"""

import json
import os
import sys
import time
from queue import Queue, Empty
from pathlib import Path
from typing import Dict, List, Optional
import logging

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("paho-mqtt is required. Install with: pip install paho-mqtt>=1.6.1")
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DrugSurfactantOrchestratorMinimal:
    """Minimal orchestrator for testing MQTT functionality."""
    
    def __init__(self):
        """Initialize the orchestrator with MQTT configuration."""
        
        # MQTT configuration - using placeholder values for testing
        self.mqtt_host = os.getenv('MQTT_HOST', 'test.mosquitto.org')
        self.mqtt_port = int(os.getenv('MQTT_PORT', 1883))
        self.mqtt_username = os.getenv('MQTT_USERNAME', '')
        self.mqtt_password = os.getenv('MQTT_PASSWORD', '')
        
        # MQTT topics
        self.experiment_topic = "lab/experiments/new"
        self.result_topic = "lab/experiments/result"
        
        # Initialize MQTT client
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.mqtt_username and self.mqtt_password:
            self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        
        # Result queue for incoming experiment results
        self.result_queue = Queue()
        
        # Experiment state
        self.current_iteration = 0
        self.pending_experiments = {}
        
    def _on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        """Callback for successful MQTT connection."""
        if reason_code.is_failure:
            logger.error(f"Failed to connect to MQTT broker: {reason_code}")
        else:
            logger.info("Connected to MQTT broker successfully")
            client.subscribe(self.result_topic, qos=1)
            logger.info(f"Subscribed to topic: {self.result_topic}")
    
    def _on_mqtt_message(self, client, userdata, message):
        """Callback for incoming MQTT messages."""
        try:
            payload = json.loads(message.payload.decode('utf-8'))
            logger.info(f"Received message on {message.topic}: {json.dumps(payload, indent=2)}")
            
            if message.topic == self.result_topic:
                self.result_queue.put(payload)
                logger.info(f"Added result to queue for experiment ID: {payload.get('experiment_id', 'unknown')}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON payload: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def connect_mqtt(self) -> bool:
        """Connect to MQTT broker."""
        try:
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            return False
    
    def disconnect_mqtt(self):
        """Disconnect from MQTT broker."""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def publish_test_experiment(self) -> str:
        """Publish a test experiment configuration to MQTT."""
        experiment_id = f"test_experiment_{int(time.time())}"
        
        # Create a sample experiment configuration based on the existing protocol structure
        test_experiment = {
            "": "0",
            "trial_index": "0",
            "drug_name": "IBP",
            "drug": "180.0",
            "s1": "0.0",
            "s2": "120.0",
            "s3": "0.0",
            "s4": "0.0",
            "s5": "0.0",
            "s6": "168.0",
            "s7": "0.0",
            "s8": "0.0",
            "dmso": "0.0",
            "water": "396.0",
            "IBP": "180.0",
            "LOV": "0.0",
            "DCF": "0.0",
            "GLV": "0.0"
        }
        
        mqtt_payload = {
            "experiment_id": experiment_id,
            "session_id": f"drug_surfactant_test_{int(time.time())}",
            "iteration": self.current_iteration,
            "timestamp": time.time(),
            "experiment_config": test_experiment,
            "command": {
                "action": "run_protocol",
                "protocol_data": test_experiment
            }
        }
        
        try:
            message = json.dumps(mqtt_payload, indent=2)
            result = self.mqtt_client.publish(self.experiment_topic, message, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published test experiment {experiment_id} to {self.experiment_topic}")
                self.pending_experiments[experiment_id] = mqtt_payload
                return experiment_id
            else:
                logger.error(f"Failed to publish experiment {experiment_id}. Return code: {result.rc}")
                return None
        except Exception as e:
            logger.error(f"Error publishing experiment: {e}")
            return None
    
    def test_mqtt_connection(self):
        """Test MQTT connection and basic pub/sub functionality."""
        logger.info("Testing MQTT connection...")
        
        if not self.connect_mqtt():
            return False
        
        # Wait a moment for connection to establish
        time.sleep(2)
        
        # Publish a test experiment
        experiment_id = self.publish_test_experiment()
        if not experiment_id:
            logger.error("Failed to publish test experiment")
            return False
        
        # Wait for potential responses
        logger.info("Waiting 10 seconds for any responses...")
        time.sleep(10)
        
        # Check if any results were received
        result_count = 0
        while not self.result_queue.empty():
            try:
                result = self.result_queue.get_nowait()
                result_count += 1
                logger.info(f"Received result #{result_count}: {json.dumps(result, indent=2)}")
            except Empty:
                break
        
        if result_count > 0:
            logger.info(f"Successfully received {result_count} results")
        else:
            logger.info("No results received (this is normal for testing without lab equipment)")
        
        self.disconnect_mqtt()
        return True


def main():
    """Main entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Drug-Surfactant Orchestrator (Minimal Test)')
    parser.add_argument('--test-mqtt', action='store_true', help='Test MQTT connectivity')
    
    args = parser.parse_args()
    
    orchestrator = DrugSurfactantOrchestratorMinimal()
    
    if args.test_mqtt:
        success = orchestrator.test_mqtt_connection()
        if success:
            logger.info("MQTT test completed successfully")
            return 0
        else:
            logger.error("MQTT test failed")
            return 1
    else:
        print("Use --test-mqtt to test MQTT connectivity")
        print("Use --help for more options")
        return 0


if __name__ == "__main__":
    exit(main())