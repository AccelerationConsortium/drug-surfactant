#!/usr/bin/env python3
"""
OpenTrons HTTP API Integration Example for Drug-Surfactant Experiments

This script demonstrates how to integrate OpenTrons HTTP API into your
centralized experiment orchestration workflow.
"""

import json
import time
from opentrons_api_client import OpenTronsAPI
import sys
import os

# # Add experiments directory to path for helper functions - more robust approach
# script_dir = os.path.dirname(os.path.abspath(__file__))
# experiments_path = os.path.join(script_dir, 'experiments', '20250917_closed_loop')
# sys.path.insert(0, experiments_path)
from utils import helpers as hf

def run_automated_experiment_cycle():
    """
    Complete automated experiment cycle using OpenTrons HTTP API

    Args:
        robot_ip: IP address of the OpenTrons robot
    """

    # Initialize API client
    api = OpenTronsAPI()

    # Test robot connectivity
    robot_info = api.get_robot_info()
    if not robot_info:
        print("Cannot connect to robot")
        return False
    print(f"Connected to robot: {robot_info.get('name', 'Unknown')}")

    n = 1 #number of iterations
    for i in range(0,n):
        print(f"Current Iteration is {i}")
        # list_of_drugs = (['IBP']  + ['LOV']  + ['DCF']  + ['GLV']) * 1 # TODO: update it back to 2
        list_of_drugs = (['IBP']) * 1 # TODO: update it back to 2
        print(f"List of drugs are {list_of_drugs}")

        # Generate recommendations
        time_start = time.time()
        df_design, ax_client, data_so_far, best_concs = hf.run_optimizer(current_iteration=i, drug_list= list_of_drugs, bopt=0)
        time_end = time.time()
        time_duration = round((time_end - time_start)/60,2)

        print("Time taken for optimization: " + str(time_duration) + " mins")
        print("Time taken for optimization: " + str(time_duration * 60) + " seconds")

        # process results
        ax_client = hf.load_design_optimizer(i)
        ax_client.get_trials_data_frame()
        df_design, df_vol = hf.design_to_vol (i)
        if i > 0:
            df_design['constraint'] = df_design['drug_name'].map(best_concs).fillna(0.0)


        # TODO: How to get rid of these inputs
        plate_well = input("Enter the plate well starting well (e.g., F1): ").strip()
        deepplate_well = input("Enter the deep plate well starting well (e.g., F1): ").strip()

        print("Wellplate will start at: " + plate_well)
        print("Deep plate will start at: " + deepplate_well)

        # Generate protocol
        try:
            hf.generate_protocol(
                df_vol=df_vol,
                iteration=i,
                plate_well=plate_well,
                deepplate_well=deepplate_well
            )
            protocol_path = f"experiments/protocol/otflex_{i}.py"
            print(f"Protocol generated: {protocol_path}")
        except Exception as e:
            print(f"Protocol generation failed: {e}")
            return False

        # Run experiment on robot via HTTP API
        print("Starting experiment on OpenTrons robot...")
        try:
            status = api.run_protocol_from_file(protocol_path)

            if status == "succeeded":
                print("Experiment completed successfully!")
                return True
            else:
                print(f"Experiment failed with status: {status}")
                return False

        except Exception as e:
            print(f"Robot communication failed: {e}")
            return False


def monitor_running_experiment(robot_ip: str, run_id: str):
    """
    Monitor a running experiment in real-time

    Args:
        robot_ip: IP address of the OpenTrons robot
        run_id: ID of the run to monitor
    """
    api = OpenTronsAPI(robot_ip)

    print(f"📊 Monitoring experiment {run_id}...")

    while True:
        run_data = api.get_run(run_id)
        status = run_data.get('data', {}).get('status')
        current_command = run_data.get('data', {}).get('currentCommand')

        print(f"📊 Status: {status}")

        if current_command:
            cmd_type = current_command.get('commandType', 'Unknown')
            print(f"⚙️  Current: {cmd_type}")

        if status in ['succeeded', 'failed', 'stopped']:
            print(f"🏁 Final status: {status}")
            break

        time.sleep(15)  # Check every 15 seconds


if __name__ == "__main__":
    print("OpenTrons HTTP API Integration Demo")

    # Test connection
    # api = OpenTronsAPI()
    # robot_info = api.get_robot_info()

    run_automated_experiment_cycle()