#!/usr/bin/env python3
"""
MQTT Demo Workflow
Demonstrates a complete experiment workflow using MQTT messaging.
"""

import sys
import time
import threading
import json
from datetime import datetime
sys.path.append('.')

from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics

class OrchestratorDemo(MQTTClientBase):
    """Demo orchestrator that designs and monitors experiments."""
    
    def __init__(self):
        super().__init__(client_id="demo_orchestrator", role="orchestrator")
        self.experiment_status = "idle"
        self.results_received = False
        
        # Register handlers for robot responses
        self.register_message_handler(mqtt_topics.Status.ROBOT_STATUS, self.handle_robot_status)
        self.register_message_handler(mqtt_topics.Status.PROTOCOL_STATUS, self.handle_protocol_status)
        self.register_message_handler(mqtt_topics.Data.EXPERIMENT_RESULTS, self.handle_results)
    
    def handle_robot_status(self, topic, data):
        """Handle robot status updates."""
        print(f"🤖 Robot Status: {data.get('status', 'unknown')}")
    
    def handle_protocol_status(self, topic, data):
        """Handle protocol execution updates."""
        status = data.get('status', 'unknown')
        progress = data.get('progress', 0)
        print(f"📋 Protocol Status: {status} ({progress*100:.1f}% complete)")
        self.experiment_status = status
    
    def handle_results(self, topic, data):
        """Handle experiment results."""
        print(f"📊 Results received for experiment {data.get('experiment_id')}")
        print(f"   Absorbance data points: {len(data.get('absorbance_data', []))}")
        self.results_received = True
    
    def design_experiment(self):
        """Design and send experiment parameters."""
        experiment_design = {
            'experiment_id': 'demo_exp_001',
            'design': {
                'drugs': ['IBP', 'LOV'],
                'surfactants': ['s1', 's2', 's4', 's8'],
                'concentrations': [90, 180],
                'replicates': 2,
                'controls': True
            },
            'protocol_version': '2.1',
            'objectives': ['maximize_solubility', 'minimize_surfactant_use']
        }
        
        print("🧪 Sending experiment design to robot...")
        return self.publish_message(mqtt_topics.Commands.LOAD_EXPERIMENT, experiment_design)
    
    def start_protocol(self):
        """Start protocol execution."""
        protocol_params = {
            'protocol_id': 'demo_protocol_001',
            'experiment_id': 'demo_exp_001',
            'parameters': {
                'temperature': 25,
                'shaking_speed': 1000,
                'shaking_duration': 5,
                'measurement_wavelength': 595
            }
        }
        
        print("▶️  Starting protocol execution...")
        return self.publish_message(mqtt_topics.Commands.START_PROTOCOL, protocol_params)
    
    def monitor_experiment(self, timeout=60):
        """Monitor experiment progress."""
        print("👁️  Monitoring experiment progress...")
        
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.results_received:
                print("✅ Experiment completed successfully!")
                return True
            
            if self.experiment_status == 'error':
                print("❌ Experiment failed!")
                return False
            
            # Send periodic heartbeats
            if int(time.time() - start_time) % 10 == 0:
                self.send_heartbeat()
            
            time.sleep(1)
        
        print("⏰ Monitoring timeout reached")
        return False

class RobotDemo(MQTTClientBase):
    """Demo robot that executes protocols and reports results."""
    
    def __init__(self):
        super().__init__(client_id="demo_robot", role="robot")
        self.current_experiment = None
        self.protocol_running = False
        
        # Register handlers for orchestrator commands
        self.register_message_handler(mqtt_topics.Commands.LOAD_EXPERIMENT, self.handle_load_experiment)
        self.register_message_handler(mqtt_topics.Commands.START_PROTOCOL, self.handle_start_protocol)
        self.register_message_handler(mqtt_topics.Commands.STOP_PROTOCOL, self.handle_stop_protocol)
    
    def handle_load_experiment(self, topic, data):
        """Handle experiment loading."""
        self.current_experiment = data
        experiment_id = data.get('experiment_id', 'unknown')
        
        print(f"📥 Loaded experiment: {experiment_id}")
        print(f"   Drugs: {data.get('design', {}).get('drugs', [])}")
        print(f"   Surfactants: {data.get('design', {}).get('surfactants', [])}")
        
        # Send acknowledgment
        status = {
            'status': 'experiment_loaded',
            'experiment_id': experiment_id,
            'ready_for_protocol': True
        }
        self.publish_message(mqtt_topics.Status.ROBOT_STATUS, status)
    
    def handle_start_protocol(self, topic, data):
        """Handle protocol start command."""
        protocol_id = data.get('protocol_id', 'unknown')
        
        print(f"🚀 Starting protocol: {protocol_id}")
        
        # Send protocol started status
        status = {
            'status': 'started',
            'protocol_id': protocol_id,
            'progress': 0.0
        }
        self.publish_message(mqtt_topics.Status.PROTOCOL_STATUS, status)
        
        # Start protocol execution in separate thread
        self.protocol_running = True
        threading.Thread(target=self.execute_protocol, args=(data,), daemon=True).start()
    
    def handle_stop_protocol(self, topic, data):
        """Handle protocol stop command."""
        print("🛑 Stopping protocol...")
        self.protocol_running = False
        
        status = {
            'status': 'stopped',
            'protocol_id': data.get('protocol_id', 'unknown')
        }
        self.publish_message(mqtt_topics.Status.PROTOCOL_STATUS, status)
    
    def execute_protocol(self, protocol_data):
        """Simulate protocol execution."""
        protocol_id = protocol_data.get('protocol_id')
        experiment_id = protocol_data.get('experiment_id')
        
        steps = [
            "Preparing reagents",
            "Dispensing drugs",
            "Dispensing surfactants", 
            "Mixing solutions",
            "Incubating",
            "Reading absorbance",
            "Cleaning up"
        ]
        
        for i, step in enumerate(steps):
            if not self.protocol_running:
                break
                
            print(f"🔬 Executing: {step}")
            
            # Send progress update
            progress = (i + 1) / len(steps)
            status = {
                'status': 'running',
                'protocol_id': protocol_id,
                'progress': progress,
                'current_step': step
            }
            self.publish_message(mqtt_topics.Status.PROTOCOL_STATUS, status)
            
            # Simulate step execution time
            time.sleep(2)
        
        if self.protocol_running:
            # Protocol completed successfully
            print("✅ Protocol execution completed")
            
            # Send completion status
            status = {
                'status': 'completed',
                'protocol_id': protocol_id,
                'progress': 1.0
            }
            self.publish_message(mqtt_topics.Status.PROTOCOL_STATUS, status)
            
            # Generate and send mock results
            self.send_mock_results(experiment_id)
    
    def send_mock_results(self, experiment_id):
        """Send mock experimental results."""
        import random
        
        # Generate mock absorbance data
        absorbance_data = []
        for drug in ['IBP', 'LOV']:
            for surfactant in ['s1', 's2', 's4', 's8']:
                for replicate in [1, 2]:
                    absorbance_data.append({
                        'drug': drug,
                        'surfactant': surfactant,
                        'replicate': replicate,
                        'absorbance': random.uniform(0.1, 0.8),
                        'well_position': f"{chr(65+len(absorbance_data)//12)}{(len(absorbance_data)%12)+1}"
                    })
        
        results = {
            'experiment_id': experiment_id,
            'protocol_completed': True,
            'absorbance_data': absorbance_data,
            'summary': {
                'total_measurements': len(absorbance_data),
                'successful_measurements': len(absorbance_data),
                'failed_measurements': 0,
                'execution_time_minutes': 14
            }
        }
        
        print(f"📤 Sending results for {len(absorbance_data)} measurements...")
        self.publish_message(mqtt_topics.Data.EXPERIMENT_RESULTS, results)
    
    def run_demo_robot(self):
        """Run the demo robot."""
        print("🤖 Demo robot starting up...")
        
        if not self.connect():
            print("❌ Failed to connect robot to broker")
            return False
        
        print("🔗 Robot connected and ready for commands")
        
        # Send initial status
        status = {
            'status': 'ready',
            'capabilities': ['liquid_handling', 'heating', 'shaking', 'absorbance_reading'],
            'version': '1.0.0'
        }
        self.publish_message(mqtt_topics.Status.ROBOT_STATUS, status)
        
        # Keep running and sending heartbeats
        try:
            while True:
                time.sleep(5)
                self.send_heartbeat()
        except KeyboardInterrupt:
            print("🛑 Robot demo stopped by user")
            return True

def run_orchestrator_demo():
    """Run the orchestrator side of the demo."""
    orchestrator = OrchestratorDemo()
    
    print("🎯 Demo Orchestrator starting...")
    
    if not orchestrator.connect():
        print("❌ Failed to connect orchestrator to broker")
        return False
    
    print("🔗 Orchestrator connected")
    
    try:
        # Step 1: Design experiment
        time.sleep(2)
        if not orchestrator.design_experiment():
            print("❌ Failed to send experiment design")
            return False
        
        # Step 2: Wait for robot to load experiment
        time.sleep(3)
        
        # Step 3: Start protocol
        if not orchestrator.start_protocol():
            print("❌ Failed to start protocol")
            return False
        
        # Step 4: Monitor progress
        success = orchestrator.monitor_experiment(timeout=30)
        
        return success
        
    except KeyboardInterrupt:
        print("🛑 Orchestrator demo stopped by user")
        return False
    finally:
        orchestrator.disconnect()

def run_robot_demo():
    """Run the robot side of the demo."""
    robot = RobotDemo()
    return robot.run_demo_robot()

def main():
    """Main demo function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MQTT Demo Workflow')
    parser.add_argument('--role', choices=['orchestrator', 'robot', 'both'], 
                       default='both', help='Which role to run')
    
    args = parser.parse_args()
    
    print("🚀 MQTT Demo Workflow Starting")
    print("=" * 40)
    
    if args.role == 'orchestrator':
        success = run_orchestrator_demo()
    elif args.role == 'robot':
        success = run_robot_demo()
    elif args.role == 'both':
        # Run robot in separate thread
        robot_thread = threading.Thread(target=run_robot_demo, daemon=True)
        robot_thread.start()
        
        # Wait for robot to start
        time.sleep(3)
        
        # Run orchestrator
        success = run_orchestrator_demo()
    
    print("=" * 40)
    if success:
        print("🎉 Demo completed successfully!")
    else:
        print("❌ Demo failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()