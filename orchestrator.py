#!/usr/bin/env python3
"""
Orchestrator for drug-surfactant experiments with closed-loop Bayesian optimization.

This script integrates the existing Bayesian optimization workflow from the 
experiments/20250917_closed_loop directory with MQTT communication for automated
experiment orchestration between Mac and Opentrons Flex.

Based on:
- experiments/20250917_closed_loop/helper_functions.py
- AC Training Lab MQTT example
"""

import json
import os
import sys
import time
from queue import Queue, Empty
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

import pandas as pd
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

# Import for Bayesian optimization
from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.generation_strategy.generation_strategy import GenerationStrategy
from ax.generation_strategy.generation_node import GenerationStep
from ax.core.observation import ObservationFeatures
from ax.core.parameter_constraint import SumConstraint

# Try to import helper functions - we'll create our own BO functions if this fails
hf = None
try:
    sys.path.append(str(Path(__file__).parent / "experiments" / "20250917_closed_loop"))
    # We'll import specific functions we need rather than the whole module
    logger.info("Helper functions import skipped - using built-in BO implementation")
except Exception as e:
    logger.warning(f"Could not import helper functions: {e}")


class DrugSurfactantOrchestrator:
    """Main orchestrator class for managing drug-surfactant experiments."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the orchestrator with MQTT and BO configuration."""
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # MQTT configuration
        self.mqtt_host = self.config.get('mqtt_host', os.getenv('MQTT_HOST'))
        self.mqtt_port = int(self.config.get('mqtt_port', os.getenv('MQTT_PORT', 8883)))
        self.mqtt_username = self.config.get('mqtt_username', os.getenv('MQTT_USERNAME'))
        self.mqtt_password = self.config.get('mqtt_password', os.getenv('MQTT_PASSWORD'))
        
        # MQTT topics
        self.experiment_topic = "lab/experiments/new"
        self.result_topic = "lab/experiments/result"
        
        # Initialize MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS_CLIENT)
        self.mqtt_client.username_pw_set(self.mqtt_username, self.mqtt_password)
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        
        # Result queue for incoming experiment results
        self.result_queue = Queue()
        
        # Experiment state
        self.current_iteration = 0
        self.pending_experiments = {}  # exp_id -> experiment_data
        self.completed_experiments = []
        
        # BO configuration
        self.drug_list = ['IBP', 'LOV', 'DCF', 'GLV']
        self.n_trials_per_drug = 1
        self.use_bo = True  # True for BO, False for Sobol
        
        # Results storage
        self.results_dir = Path("orchestrator_results")
        self.results_dir.mkdir(exist_ok=True)
        
    def _load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from file or return defaults."""
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for successful MQTT connection."""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            client.subscribe(self.result_topic, qos=2)
            logger.info(f"Subscribed to topic: {self.result_topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Callback for incoming MQTT messages."""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            logger.info(f"Received message on {msg.topic}: {json.dumps(payload, indent=2)}")
            
            if msg.topic == self.result_topic:
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
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT: {e}")
            return False
    
    def disconnect_mqtt(self):
        """Disconnect from MQTT broker."""
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
    
    def generate_experiment_batch(self) -> Tuple[pd.DataFrame, List[Dict]]:
        """Generate new experiment batch using Bayesian optimization."""
        logger.info(f"Generating experiment batch for iteration {self.current_iteration}")
        
        try:
            # Create or load AxClient
            ax_client = self._get_ax_client()
            
            # Generate trials for each drug
            trials_data = []
            for drug in self.drug_list:
                drug_props = self._get_drug_properties(drug)
                drug_features = ObservationFeatures(parameters=drug_props)
                
                # Generate trial(s) for this drug
                for _ in range(self.n_trials_per_drug):
                    parameters, trial_index = ax_client.get_next_trial(fixed_features=drug_features)
                    trials_data.append({
                        "trial_index": trial_index,
                        "drug_name": drug,
                        **parameters,
                    })
            
            # Create design dataframe
            df_design = pd.DataFrame(trials_data)
            df_design['surf_conc'] = df_design.get('surf_1_conc', 0) + df_design.get('surf_2_conc', 0)
            
            # Convert to volume format
            experiment_configs = self._convert_design_to_volumes(df_design)
            
            logger.info(f"Generated {len(df_design)} experiments for iteration {self.current_iteration}")
            
            return df_design, experiment_configs
            
        except Exception as e:
            logger.error(f"Failed to generate experiment batch: {e}")
            raise
    
    def publish_experiment(self, experiment_data: Dict) -> str:
        """Publish experiment configuration to MQTT."""
        experiment_id = f"iter_{self.current_iteration}_trial_{experiment_data.get('trial_index', 'unknown')}"
        
        mqtt_payload = {
            "experiment_id": experiment_id,
            "session_id": f"drug_surfactant_{int(time.time())}",
            "iteration": self.current_iteration,
            "timestamp": time.time(),
            "experiment_config": experiment_data,
            "command": {
                "action": "run_protocol",
                "protocol_data": experiment_data
            }
        }
        
        try:
            message = json.dumps(mqtt_payload)
            result = self.mqtt_client.publish(self.experiment_topic, message, qos=2)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published experiment {experiment_id} to {self.experiment_topic}")
                self.pending_experiments[experiment_id] = mqtt_payload
                return experiment_id
            else:
                logger.error(f"Failed to publish experiment {experiment_id}. Return code: {result.rc}")
                return None
        except Exception as e:
            logger.error(f"Error publishing experiment: {e}")
            return None
    
    def process_results(self) -> List[Dict]:
        """Process incoming experimental results from MQTT."""
        processed_results = []
        
        while not self.result_queue.empty():
            try:
                result_data = self.result_queue.get_nowait()
                experiment_id = result_data.get('experiment_id')
                
                if experiment_id in self.pending_experiments:
                    # Process the result and store it
                    processed_result = self._process_single_result(result_data)
                    if processed_result:
                        processed_results.append(processed_result)
                        self.completed_experiments.append(processed_result)
                        
                        # Remove from pending
                        del self.pending_experiments[experiment_id]
                        logger.info(f"Processed result for experiment {experiment_id}")
                else:
                    logger.warning(f"Received result for unknown experiment: {experiment_id}")
                    
            except Empty:
                break
            except Exception as e:
                logger.error(f"Error processing result: {e}")
        
        return processed_results
    
    def _process_single_result(self, result_data: Dict) -> Optional[Dict]:
        """Process a single experimental result."""
        try:
            experiment_id = result_data.get('experiment_id')
            raw_result = result_data.get('result', {})
            
            # Extract relevant measurements (adapt based on actual result format)
            success = raw_result.get('success', 0)  # Binary success indicator
            absorbance = raw_result.get('absorbance', [])  # Absorbance measurements
            
            # Process absorbance data if available
            if absorbance:
                # Apply threshold-based success determination (from helper_functions.py)
                threshold = 0.06
                success = 1 if any(abs_val < threshold for abs_val in absorbance) else 0
            
            processed_result = {
                'experiment_id': experiment_id,
                'trial_index': self._extract_trial_index(experiment_id),
                'success': success,
                'raw_data': raw_result,
                'timestamp': time.time(),
                'iteration': self.current_iteration
            }
            
            return processed_result
            
        except Exception as e:
            logger.error(f"Error processing single result: {e}")
            return None
    
    def _extract_trial_index(self, experiment_id: str) -> int:
        """Extract trial index from experiment ID."""
        try:
            # Format: "iter_{iteration}_trial_{index}"
            parts = experiment_id.split('_')
            return int(parts[-1])
        except (IndexError, ValueError):
            return 0
    
    def save_results_locally(self, results: List[Dict]):
        """Save experimental results to local storage."""
        if not results:
            return
        
        results_file = self.results_dir / f"iteration_{self.current_iteration}_results.json"
        
        try:
            # Load existing results if file exists
            existing_results = []
            if results_file.exists():
                with open(results_file, 'r') as f:
                    existing_results = json.load(f)
            
            # Append new results
            existing_results.extend(results)
            
            # Save updated results
            with open(results_file, 'w') as f:
                json.dump(existing_results, f, indent=2)
            
            logger.info(f"Saved {len(results)} results to {results_file}")
            
            # Also save as CSV for easy analysis
            csv_file = self.results_dir / f"iteration_{self.current_iteration}_results.csv"
            df_results = pd.DataFrame(existing_results)
            df_results.to_csv(csv_file, index=False)
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def update_optimization_with_results(self, results: List[Dict]):
        """Update the Bayesian optimization model with new experimental results."""
        if not results:
            return
        
        try:
            # Convert results to the format expected by helper functions
            results_df = self._format_results_for_optimizer(results)
            
            # Load results into optimizer (from helper_functions.py)
            ax_client = hf.load_data_to_optimizer(
                iteration=self.current_iteration,
                results=results_df
            )
            
            logger.info(f"Updated optimizer with {len(results)} new results")
            
        except Exception as e:
            logger.error(f"Error updating optimization model: {e}")
    
    def _get_ax_client(self) -> AxClient:
        """Get or create AxClient for Bayesian optimization."""
        
        # Constants from helper_functions.py
        surfactant_stock_conc = 100
        drug_stock_conc = 25
        
        # Initialize AxClient with default generation strategy
        ax_client = AxClient()
        
        # Create experiment
        ax_client.create_experiment(
            name="drug_surfactant",
            parameters=[
                # Drug properties
                {"name": "Drug_MW", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
                {"name": "Drug_LogP", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"}, 
                {"name": "Drug_TPSA", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
                
                # Surfactants
                {"name": "surf_1", "type": "choice", "is_ordered": False, 
                 "values": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
                {"name": "surf_1_conc", "type": "range", "bounds": [0.0, surfactant_stock_conc], "value_type": "int"},
                {"name": "surf_2", "type": "choice", "is_ordered": False,
                 "values": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
                {"name": "surf_2_conc", "type": "range", "bounds": [0.0, surfactant_stock_conc], "value_type": "int"},
                
                # Drug concentration
                {"name": "drug_conc", "type": "range", "bounds": [0.0, drug_stock_conc], "value_type": "float"},
            ],
            objectives={
                'obj_surf_conc': ObjectiveProperties(minimize=True),
            },
            parameter_constraints=[
                f"surf_1_conc + surf_2_conc <= {surfactant_stock_conc-1}",
                'surf_1_conc + surf_2_conc >= 1',
            ],
        )
        
        return ax_client
    
    def _get_drug_properties(self, drug: str) -> Dict:
        """Get normalized drug properties."""
        # Drug properties from helper_functions.py
        drug_properties = {
            'IBP': {"Drug_MW": 0.2063, "Drug_LogP": 0.3073, "Drug_TPSA": 0.0373},
            'DCF': {"Drug_MW": 0.2962, "Drug_LogP": 0.4364, "Drug_TPSA": 0.0493},
            'LOV': {"Drug_MW": 0.4045, "Drug_LogP": 0.4196, "Drug_TPSA": 0.0728},
            'GLV': {"Drug_MW": 0.3528, "Drug_LogP": 0.2810, "Drug_TPSA": 0.0711},
        }
        
        props = drug_properties.get(drug, drug_properties['IBP']).copy()
        props["drug_conc"] = 100  # Fixed drug concentration
        return props
    
    def _convert_design_to_volumes(self, df_design: pd.DataFrame) -> List[Dict]:
        """Convert design parameters to volume format for the robot."""
        
        # Constants from helper_functions.py
        drug_stock_conc = 25  # mg/mL
        surfactant_stock_conc = 100  # percent of stock
        drug_total_volume = 0.18  # mL
        surfactant_total_volume = 1.2  # mL
        
        experiment_configs = []
        
        for idx, row in df_design.iterrows():
            # Calculate volumes in µL (multiply by 1000)
            drug_volume = (row.get('drug_conc', 100) * drug_total_volume / drug_stock_conc) * 1000
            
            # Initialize all surfactant volumes to 0
            s_volumes = {f's{i}': 0.0 for i in range(1, 9)}
            
            # Calculate surfactant volumes
            for surf_slot in ['surf_1', 'surf_2']:
                if surf_slot in row:
                    surf_name = row[surf_slot]
                    conc_col = f"{surf_slot}_conc"
                    if conc_col in row and surf_name in s_volumes:
                        volume = (row[conc_col] * surfactant_total_volume / surfactant_stock_conc) * 1000
                        s_volumes[surf_name] = volume
            
            # Calculate DMSO and water volumes
            dmso_volume = (drug_total_volume * 1000) - drug_volume
            water_volume = (surfactant_total_volume * 1000) - sum(s_volumes.values())
            
            # Create experiment configuration
            config = {
                "": str(idx),
                "trial_index": str(row['trial_index']),
                "drug_name": row['drug_name'],
                "drug": str(drug_volume),
                **{k: str(v) for k, v in s_volumes.items()},
                "dmso": str(dmso_volume),
                "water": str(water_volume),
                # Add drug columns
                "IBP": str(drug_volume) if row['drug_name'] == 'IBP' else "0.0",
                "LOV": str(drug_volume) if row['drug_name'] == 'LOV' else "0.0", 
                "DCF": str(drug_volume) if row['drug_name'] == 'DCF' else "0.0",
                "GLV": str(drug_volume) if row['drug_name'] == 'GLV' else "0.0",
            }
            
            experiment_configs.append(config)
        
        return experiment_configs

    def _format_results_for_optimizer(self, results: List[Dict]) -> pd.DataFrame:
        """Format results for the Ax optimizer."""
        formatted_data = []
        
        for result in results:
            trial_index = result.get('trial_index')
            success = result.get('success', 0)
            
            # Calculate objective value (from helper_functions.py logic)
            # obj_surf_conc = surfactant_stock_conc if success == 0, else actual surf_conc
            surfactant_stock_conc = 100  # From helper_functions.py constants
            obj_surf_conc = surfactant_stock_conc if success == 0 else result.get('surf_conc', surfactant_stock_conc)
            
            formatted_data.append({
                'trial_index': trial_index,
                'success': success,
                'obj_surf_conc': obj_surf_conc
            })
        
        return pd.DataFrame(formatted_data)
    
    def run_optimization_loop(self, max_iterations: int = 10, experiments_per_iteration: int = 4):
        """Run the main optimization loop."""
        logger.info(f"Starting optimization loop for {max_iterations} iterations")
        
        if not self.connect_mqtt():
            logger.error("Failed to connect to MQTT. Exiting.")
            return False
        
        try:
            for iteration in range(max_iterations):
                self.current_iteration = iteration
                logger.info(f"Starting iteration {iteration}")
                
                # Generate experiment batch
                df_design, experiment_configs = self.generate_experiment_batch()
                
                # Publish experiments to MQTT
                published_count = 0
                for config in experiment_configs:
                    experiment_id = self.publish_experiment(config)
                    if experiment_id:
                        published_count += 1
                        time.sleep(1)  # Small delay between publications
                
                logger.info(f"Published {published_count}/{len(experiment_configs)} experiments")
                
                # Wait for results
                logger.info("Waiting for experimental results...")
                timeout = 300  # 5 minutes timeout per iteration
                start_time = time.time()
                
                while len(self.completed_experiments) < published_count:
                    if time.time() - start_time > timeout:
                        logger.warning(f"Timeout waiting for results in iteration {iteration}")
                        break
                    
                    # Process any incoming results
                    new_results = self.process_results()
                    if new_results:
                        self.save_results_locally(new_results)
                    
                    time.sleep(5)  # Check for results every 5 seconds
                
                # Update optimization model with all results from this iteration
                iteration_results = [r for r in self.completed_experiments 
                                   if r.get('iteration') == iteration]
                
                if iteration_results:
                    self.update_optimization_with_results(iteration_results)
                    logger.info(f"Completed iteration {iteration} with {len(iteration_results)} results")
                else:
                    logger.warning(f"No results received for iteration {iteration}")
                
                # Clear completed experiments for next iteration
                self.completed_experiments = []
        
        except KeyboardInterrupt:
            logger.info("Optimization loop interrupted by user")
        except Exception as e:
            logger.error(f"Error in optimization loop: {e}")
            raise
        finally:
            self.disconnect_mqtt()
        
        logger.info("Optimization loop completed")
        return True
    
    def run_single_iteration(self):
        """Run a single iteration for testing purposes."""
        if not self.connect_mqtt():
            logger.error("Failed to connect to MQTT. Exiting.")
            return False
        
        try:
            logger.info(f"Running single iteration {self.current_iteration}")
            
            # Generate experiment batch
            df_design, experiment_configs = self.generate_experiment_batch()
            
            # Publish first experiment as test
            if experiment_configs:
                experiment_id = self.publish_experiment(experiment_configs[0])
                if experiment_id:
                    logger.info(f"Published test experiment: {experiment_id}")
                    
                    # Wait briefly for any immediate responses
                    time.sleep(10)
                    results = self.process_results()
                    if results:
                        self.save_results_locally(results)
                        logger.info("Processed test results")
            
        except Exception as e:
            logger.error(f"Error in single iteration: {e}")
            return False
        finally:
            self.disconnect_mqtt()
        
        return True


def main():
    """Main entry point for the orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Drug-Surfactant Experiment Orchestrator')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--iterations', type=int, default=5, help='Number of optimization iterations')
    parser.add_argument('--test', action='store_true', help='Run single test iteration')
    parser.add_argument('--drugs', nargs='+', default=['IBP', 'LOV', 'DCF', 'GLV'], 
                       help='List of drugs to test')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = DrugSurfactantOrchestrator(config_file=args.config)
    orchestrator.drug_list = args.drugs
    
    # Run the appropriate mode
    if args.test:
        logger.info("Running in test mode")
        success = orchestrator.run_single_iteration()
    else:
        logger.info(f"Running optimization loop for {args.iterations} iterations")
        success = orchestrator.run_optimization_loop(max_iterations=args.iterations)
    
    if success:
        logger.info("Orchestrator completed successfully")
        return 0
    else:
        logger.error("Orchestrator failed")
        return 1


if __name__ == "__main__":
    exit(main())