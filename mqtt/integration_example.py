"""
Integration Example for MQTT in Closed-Loop System
Shows how to integrate MQTT messaging with existing helper functions.
"""

import sys
import json
from datetime import datetime

# Add project root to path for imports
sys.path.append('.')

from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics

class ClosedLoopOrchestrator(MQTTClientBase):
    """
    Orchestrator that integrates MQTT with existing optimization system.
    
    This class shows how to integrate the MQTT infrastructure with
    the existing helper_functions.py and optimization workflow.
    """
    
    def __init__(self):
        super().__init__(client_id="closed_loop_orchestrator", role="orchestrator")
        
        # State tracking
        self.current_iteration = 0
        self.experiment_running = False
        self.latest_results = None
        
        # Register handlers for robot responses
        self.register_message_handler(mqtt_topics.Status.ROBOT_STATUS, self.handle_robot_status)
        self.register_message_handler(mqtt_topics.Status.PROTOCOL_STATUS, self.handle_protocol_status)
        self.register_message_handler(mqtt_topics.Data.EXPERIMENT_RESULTS, self.handle_experiment_results)
        self.register_message_handler(mqtt_topics.Data.ABSORBANCE_DATA, self.handle_absorbance_data)
    
    def handle_robot_status(self, topic, data):
        """Handle robot status updates."""
        status = data.get('status', 'unknown')
        print(f"🤖 Robot status: {status}")
        
        if status == 'ready' and not self.experiment_running:
            print("✅ Robot is ready for commands")
        elif status == 'error':
            print("❌ Robot reported an error!")
            self.experiment_running = False
    
    def handle_protocol_status(self, topic, data):
        """Handle protocol execution updates."""
        status = data.get('status', 'unknown')
        progress = data.get('progress', 0)
        
        print(f"📋 Protocol: {status} ({progress*100:.1f}% complete)")
        
        if status == 'completed':
            print("✅ Protocol execution completed")
            self.experiment_running = False
        elif status == 'error':
            print("❌ Protocol execution failed")
            self.experiment_running = False
    
    def handle_experiment_results(self, topic, data):
        """Handle final experiment results."""
        experiment_id = data.get('experiment_id', 'unknown')
        print(f"📊 Received results for experiment: {experiment_id}")
        
        # Store results for optimization
        self.latest_results = data
        
        # Extract absorbance data for integration with helper_functions.py
        absorbance_data = data.get('absorbance_data', [])
        print(f"   📈 Absorbance measurements: {len(absorbance_data)}")
        
        # This is where you would integrate with existing code:
        # from experiments.20250917_closed_loop.helper_functions import load_data_to_optimizer
        # results_df = self.convert_to_dataframe(absorbance_data)
        # ax_client = load_data_to_optimizer(self.current_iteration, results_df)
    
    def handle_absorbance_data(self, topic, data):
        """Handle real-time absorbance data."""
        measurement_type = data.get('measurement_type', 'unknown')
        values = data.get('data', {}).get('values', [])
        print(f"📊 Real-time absorbance data: {len(values)} measurements")
    
    def send_experiment_design(self, iteration):
        """
        Send experiment design to robot.
        
        This method integrates with the existing optimizer workflow.
        """
        # This would integrate with existing code:
        # from experiments.20250917_closed_loop.helper_functions import optimizer_init, generate_design
        # ax_client = optimizer_init() if iteration == 0 else load_design_optimizer(iteration)
        # design_data = generate_design(ax_client, n_trials=8)
        
        # For demonstration, create a mock design
        experiment_design = {
            'experiment_id': f'closed_loop_exp_{iteration:03d}',
            'iteration': iteration,
            'design': {
                'drugs': ['IBP', 'LOV', 'DCF', 'GLV'],
                'surfactants': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'],
                'trials': [
                    {
                        'trial_index': f'{iteration * 8 + i}',
                        'drug_name': 'IBP',
                        'drug': '180.0',
                        's1': '100.0',
                        's2': '0.0',
                        's3': '0.0',
                        's4': '200.0',
                        'water': '500.0'
                    } for i in range(8)  # 8 trials per iteration
                ],
                'protocol_template': 'otflex_template.py'
            },
            'optimization_state': {
                'method': 'bayesian_optimization',
                'objective': 'maximize_solubility',
                'constraints': ['minimize_surfactant_use']
            }
        }
        
        print(f"📤 Sending experiment design for iteration {iteration}")
        success = self.publish_message(mqtt_topics.Commands.LOAD_EXPERIMENT, experiment_design)
        
        if success:
            self.current_iteration = iteration
            print(f"✅ Experiment design sent successfully")
        else:
            print(f"❌ Failed to send experiment design")
        
        return success
    
    def start_protocol_execution(self):
        """Start protocol execution on the robot."""
        protocol_params = {
            'protocol_id': f'protocol_{self.current_iteration:03d}',
            'experiment_id': f'closed_loop_exp_{self.current_iteration:03d}',
            'parameters': {
                'temperature': 25,
                'shaking_speed': 1000,
                'shaking_duration': 5,
                'measurement_wavelength': 595,
                'protocol_file': f'otflex_{self.current_iteration}.py'
            }
        }
        
        print(f"▶️  Starting protocol execution for iteration {self.current_iteration}")
        success = self.publish_message(mqtt_topics.Commands.START_PROTOCOL, protocol_params)
        
        if success:
            self.experiment_running = True
            print(f"✅ Protocol execution started")
        else:
            print(f"❌ Failed to start protocol execution")
        
        return success
    
    def convert_to_dataframe(self, absorbance_data):
        """
        Convert MQTT absorbance data to pandas DataFrame.
        
        This method converts the MQTT message format to the format
        expected by the existing helper_functions.py code.
        """
        import pandas as pd
        
        # Convert list of measurement dicts to DataFrame
        df_data = []
        for measurement in absorbance_data:
            row = {
                'trial_index': measurement.get('trial_index', ''),
                'drug_name': measurement.get('drug', ''),
                'obj_surf_conc': measurement.get('absorbance', 0.0),
                # Add other columns as needed to match existing format
            }
            df_data.append(row)
        
        return pd.DataFrame(df_data)
    
    def run_closed_loop_iteration(self, iteration=0):
        """
        Run a complete closed-loop iteration.
        
        This method orchestrates:
        1. Generate experiment design using optimizer
        2. Send design to robot via MQTT
        3. Start protocol execution
        4. Wait for results
        5. Update optimizer with results
        """
        print(f"🔄 Starting closed-loop iteration {iteration}")
        
        if not self.connect():
            print("❌ Failed to connect to MQTT broker")
            return False
        
        try:
            # Step 1: Send experiment design
            if not self.send_experiment_design(iteration):
                return False
            
            # Step 2: Start protocol execution
            import time
            time.sleep(2)  # Wait for robot to load experiment
            
            if not self.start_protocol_execution():
                return False
            
            # Step 3: Wait for completion
            print("⏳ Waiting for experiment completion...")
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            
            while self.experiment_running and (time.time() - start_time) < timeout:
                time.sleep(5)
                self.send_heartbeat()
            
            # Step 4: Check results
            if self.latest_results:
                print("📊 Results received, updating optimizer...")
                # Here you would integrate with existing code:
                # results_df = self.convert_to_dataframe(self.latest_results['absorbance_data'])
                # updated_optimizer = load_data_to_optimizer(iteration, results_df)
                print("✅ Iteration completed successfully")
                return True
            else:
                print("❌ No results received within timeout")
                return False
                
        except Exception as e:
            print(f"❌ Iteration failed: {e}")
            return False
        finally:
            self.disconnect()


def example_integration():
    """
    Example of how to integrate MQTT with existing closed-loop system.
    """
    print("🚀 Closed-Loop MQTT Integration Example")
    print("=" * 50)
    
    # Create orchestrator
    orchestrator = ClosedLoopOrchestrator()
    
    # Run multiple iterations
    for iteration in range(3):
        print(f"\n🔄 Running iteration {iteration}")
        
        success = orchestrator.run_closed_loop_iteration(iteration)
        
        if success:
            print(f"✅ Iteration {iteration} completed")
        else:
            print(f"❌ Iteration {iteration} failed")
            break
        
        # In real system, you would generate next design based on results
        print(f"📈 Generating design for next iteration...")
    
    print("\n🎉 Closed-loop example completed")


if __name__ == "__main__":
    example_integration()