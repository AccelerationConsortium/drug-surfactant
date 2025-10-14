#!/usr/bin/env python3
"""
MQTT Device Listener for Opentrons Flex

This module implements an MQTT listener that runs on the Opentrons Flex robot.
It subscribes to experiment messages, generates protocol scripts, executes them,
and publishes results back to the broker.

Environment Variables:
- OPENTRONS_MODE: "simulate" or "execute" (default: simulate)
- MQTT_HOST: MQTT broker host
- MQTT_PORT: MQTT broker port (default: 8883)
- MQTT_USERNAME: MQTT username
- MQTT_PASSWORD: MQTT password
- DEVICE_ID: Unique device identifier (default: auto-generated)
"""

import json
import logging
import os
import tempfile
import time
from queue import Empty, Queue
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

import paho.mqtt.client as mqtt

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OPENTRONS_MODE = os.getenv('OPENTRONS_MODE', 'simulate')
MQTT_HOST = os.getenv('MQTT_HOST', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '8883'))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
DEVICE_ID = os.getenv('DEVICE_ID', f"flex-{uuid.uuid4().hex[:8]}")

# MQTT Topics
EXPERIMENTS_NEW_TOPIC = "lab/experiments/new"
EXPERIMENTS_RESULT_TOPIC = "lab/experiments/result"

# Import opentrons modules based on mode
try:
    if OPENTRONS_MODE == 'execute':
        import opentrons.execute as opentrons_api
        logger.info("Using Opentrons execute mode")
    else:
        import opentrons.simulate as opentrons_api
        logger.info("Using Opentrons simulate mode")
except ImportError as e:
    logger.error(f"Failed to import Opentrons API: {e}")
    # Fall back to simulate mode if execute is not available
    try:
        import opentrons.simulate as opentrons_api
        logger.info("Falling back to Opentrons simulate mode")
    except ImportError:
        logger.error("Opentrons API not available. Please install opentrons package.")
        raise


class FlexDeviceListener:
    """MQTT listener for Opentrons Flex device."""
    
    def __init__(self):
        self.client = None
        self.experiment_queue = Queue()
        self.running = False
        
        # Path to the template file (relative to experiments/20250917_closed_loop)
        self.template_path = Path("experiments/20250917_closed_loop/drug_surfactant_otflex_template.py")
        
    def setup_mqtt_client(self) -> mqtt.Client:
        """Set up and configure MQTT client."""
        client = mqtt.Client()
        
        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
        if MQTT_PORT == 8883:
            client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS_CLIENT)
            
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect
        
        return client
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
            client.subscribe(EXPERIMENTS_NEW_TOPIC, qos=2)
            logger.info(f"Subscribed to topic: {EXPERIMENTS_NEW_TOPIC}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Result code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Callback for receiving MQTT messages."""
        try:
            payload = msg.payload.decode('utf-8')
            logger.info(f"Received message on {msg.topic}")
            
            experiment_data = json.loads(payload)
            
            if msg.topic == EXPERIMENTS_NEW_TOPIC:
                self.experiment_queue.put(experiment_data)
                logger.info(f"Added experiment to queue: {experiment_data.get('experiment_id', 'unknown')}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        if rc != 0:
            logger.warning("Unexpected MQTT disconnection. Attempting to reconnect...")
        else:
            logger.info("MQTT client disconnected.")
    
    def generate_protocol_from_experiment(self, experiment_data: Dict[str, Any]) -> str:
        """
        Generate a protocol file from experiment data.
        
        Args:
            experiment_data: Dictionary containing experiment configuration
            
        Returns:
            Path to the generated protocol file
        """
        try:
            # Check if template exists
            if not self.template_path.exists():
                raise FileNotFoundError(f"Template file not found: {self.template_path}")
            
            # Read template
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Create temporary protocol file
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.py', 
                prefix=f"protocol_{experiment_data.get('experiment_id', 'unknown')}_",
                delete=False
            )
            
            # Process experiment data and modify template
            modified_content = self._modify_template_for_experiment(template_content, experiment_data)
            
            temp_file.write(modified_content)
            temp_file.close()
            
            logger.info(f"Generated protocol file: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Failed to generate protocol: {e}")
            raise
    
    def _modify_template_for_experiment(self, template_content: str, experiment_data: Dict[str, Any]) -> str:
        """
        Modify template content based on experiment data.
        
        This is a simplified version - in production you would want to use
        the full generate_protocol function from helper_functions.py
        """
        # Extract experiment parameters
        experiment_id = experiment_data.get('experiment_id', 'unknown')
        
        # Replace data section if experiment has volume data
        if 'data' in experiment_data:
            data_json = json.dumps(experiment_data['data'], indent=4)
            
            # Find the data section in the template and replace it
            lines = template_content.split('\n')
            start_idx = None
            end_idx = None
            
            for i, line in enumerate(lines):
                if "# to be treated as an input arguement in the future" in line:
                    # Find the start of data block
                    for j in range(i + 1, len(lines)):
                        if "data = [" in lines[j]:
                            start_idx = j
                            break
                    break
            
            if start_idx is not None:
                # Find the end of data block
                bracket_count = 0
                for k in range(start_idx, len(lines)):
                    line = lines[k]
                    bracket_count += line.count('[') - line.count(']')
                    if bracket_count == 0 and k > start_idx:
                        end_idx = k
                        break
                
                if end_idx is not None:
                    # Replace the data section
                    indent = "    "  # Assuming standard indentation
                    data_lines = data_json.split('\n')
                    replacement = [f"{indent}data = {data_lines[0]}"]
                    replacement.extend([f"{indent}{line}" for line in data_lines[1:]])
                    
                    lines = lines[:start_idx] + replacement + lines[end_idx + 1:]
                    template_content = '\n'.join(lines)
        
        # Update filename for plate reader export
        template_content = template_content.replace(
            'export_filename="raw_absorbance_in"',
            f'export_filename="raw_absorbance_{experiment_id}"'
        )
        
        return template_content
    
    def execute_protocol(self, protocol_file: str, experiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a protocol file using the Opentrons API.
        
        Args:
            protocol_file: Path to the protocol file to execute
            experiment_data: Original experiment data
            
        Returns:
            Dictionary containing execution results
        """
        try:
            experiment_id = experiment_data.get('experiment_id', 'unknown')
            logger.info(f"Executing protocol for experiment {experiment_id}")
            
            # Get protocol API
            protocol = opentrons_api.get_protocol_api('2.21')
            
            # Execute the protocol file
            with open(protocol_file, 'r') as f:
                protocol_code = f.read()
            
            # Execute the protocol code
            exec_globals = {
                'protocol_api': opentrons_api.protocol_api,
                'protocol': protocol
            }
            
            exec(protocol_code, exec_globals)
            
            # In simulate mode, we can get command log
            if OPENTRONS_MODE == 'simulate':
                commands = protocol.commands()
                command_count = len(commands)
            else:
                command_count = None
            
            # Create result data
            result = {
                'experiment_id': experiment_id,
                'device_id': DEVICE_ID,
                'status': 'completed',
                'execution_mode': OPENTRONS_MODE,
                'timestamp': time.time(),
                'command_count': command_count,
                'result_files': [
                    f"raw_absorbance_{experiment_id}.csv"  # Expected output file
                ]
            }
            
            logger.info(f"Protocol execution completed for experiment {experiment_id}")
            return result
            
        except Exception as e:
            logger.error(f"Protocol execution failed: {e}")
            return {
                'experiment_id': experiment_data.get('experiment_id', 'unknown'),
                'device_id': DEVICE_ID,
                'status': 'failed',
                'error': str(e),
                'execution_mode': OPENTRONS_MODE,
                'timestamp': time.time()
            }
    
    def publish_result(self, result_data: Dict[str, Any]):
        """Publish experiment results via MQTT."""
        try:
            message = json.dumps(result_data)
            self.client.publish(EXPERIMENTS_RESULT_TOPIC, message, qos=2)
            logger.info(f"Published result for experiment {result_data.get('experiment_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to publish result: {e}")
    
    def process_experiments(self):
        """Main loop to process experiments from the queue."""
        while self.running:
            try:
                # Wait for an experiment with timeout
                experiment_data = self.experiment_queue.get(timeout=1)
                
                experiment_id = experiment_data.get('experiment_id', 'unknown')
                logger.info(f"Processing experiment {experiment_id}")
                
                # Generate protocol
                protocol_file = self.generate_protocol_from_experiment(experiment_data)
                
                try:
                    # Execute protocol
                    result = self.execute_protocol(protocol_file, experiment_data)
                    
                    # Publish result
                    self.publish_result(result)
                    
                finally:
                    # Clean up temporary protocol file
                    try:
                        os.unlink(protocol_file)
                        logger.debug(f"Cleaned up protocol file: {protocol_file}")
                    except OSError:
                        logger.warning(f"Could not clean up protocol file: {protocol_file}")
                
            except Empty:
                # No experiments in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing experiment: {e}")
    
    def start(self):
        """Start the device listener."""
        logger.info(f"Starting Opentrons Flex device listener (ID: {DEVICE_ID})")
        logger.info(f"Mode: {OPENTRONS_MODE}")
        logger.info(f"MQTT Broker: {MQTT_HOST}:{MQTT_PORT}")
        
        try:
            # Set up MQTT client
            self.client = self.setup_mqtt_client()
            
            # Connect to MQTT broker
            self.client.connect(MQTT_HOST, MQTT_PORT, 60)
            
            # Start MQTT loop in background
            self.client.loop_start()
            
            # Set running flag
            self.running = True
            
            logger.info("Device listener started. Waiting for experiments...")
            
            # Start processing experiments
            self.process_experiments()
            
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Error starting device listener: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop the device listener."""
        logger.info("Stopping device listener...")
        
        self.running = False
        
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        
        logger.info("Device listener stopped")


def main():
    """Main entry point."""
    # Check required environment variables
    if not MQTT_HOST or MQTT_HOST == 'localhost':
        logger.warning("MQTT_HOST not set or using localhost. Set MQTT_HOST environment variable.")
    
    if not MQTT_USERNAME:
        logger.warning("MQTT_USERNAME not set. MQTT authentication may fail.")
    
    # Create and start device listener
    device = FlexDeviceListener()
    device.start()


if __name__ == '__main__':
    main()