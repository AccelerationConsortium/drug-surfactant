"""
API-based helper functions for drug-surfactant experiments.

This module replaces the SSH/SCP-based workflow with API calls to the FastAPI server
that handles protocol simulation and execution using opentrons.simulate and opentrons.execute.
The API server is designed to be deployed on Railway for cloud hosting.
"""

import requests
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.generation_strategy.generation_strategy import GenerationStep, GenerationStrategy
from ax.modelbridge.registry import Models
from ax.core.observation import ObservationFeatures
from ax.core.parameter_constraint import SumConstraint
import re
import os


# Configuration - Railway deployment URL or local development
API_BASE_URL = os.getenv("DRUG_SURFACTANT_API_URL", "http://localhost:8000")
# For Railway deployment, set environment variable to: https://your-railway-app.railway.app

# Keep the same constants from the original helper_functions.py
optimizer_file_path = 'optimizer/optimizer_'
raw_data_file_path = 'raw_data/raw_absorbance_'
design_file_path = 'optimizer/design_'
drug_stock_conc = 25  # mg/mL
surfactant_stock_conc = 100  # represents percent of the stock solution
actual_surfactant_stock_conc = 50 # mg/mL represents the actual conc
drug_total_volume = 0.18  # mL
surfactant_total_volume = 1.2  # mL
number_of_surfactants = 8  # s1 to s8

normalize_drug_properties_dict = {
    'IBP': {
        'full_name': 'Ibuprofen',
        'normalized_properties': {"Drug_MW": 0.2063, "Drug_LogP": 0.3073,  "Drug_TPSA": 0.0373},
        'drug_stock_conc': 25,
    },
    'DCF': {
        'full_name': 'Diclofenac',
        'normalized_properties': {"Drug_MW": 0.2962, "Drug_LogP": 0.4364,  "Drug_TPSA": 0.0493},
        'drug_stock_conc': 25,
    },
    'LOV': {
        'full_name': 'Lovastatin',
        'normalized_properties': {"Drug_MW": 0.4045, "Drug_LogP": 0.4196,  "Drug_TPSA": 0.0728},
        'drug_stock_conc': 25,
    },
    'ITZ': {
        'full_name': 'Itraconazole',
        'normalized_properties': {"Drug_MW": 0.7056, "Drug_LogP": 0.5577,  "Drug_TPSA": 0.1047},
        'drug_stock_conc': 25,
    },
    'RPD': {
        'full_name': 'Risperidone',
        'normalized_properties': {"Drug_MW": 0.4105, "Drug_LogP": 0.3590,  "Drug_TPSA": 0.0642},
        'drug_stock_conc': 25,
    },
    'GLV': {
        'full_name': 'Griseofulvin',
        'normalized_properties': {"Drug_MW": 0.3528, "Drug_LogP": 0.2810,  "Drug_TPSA": 0.0711},
        'drug_stock_conc': 25,
    },
    'CTZ': {
        'full_name': 'Clotrimazole',
        'normalized_properties': {"Drug_MW": 0.3448, "Drug_LogP": 0.5377,  "Drug_TPSA": 0.0178},
        'drug_stock_conc': 25,
    },
    'GBC': {
        'full_name': 'Glibenclamide/Glyburide',
        'normalized_properties': {"Drug_MW": 0.4940, "Drug_LogP": 0.3642,  "Drug_TPSA": 0.1136},
        'drug_stock_conc': 25,
    },
}


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass


def check_api_health() -> bool:
    """Check if the API server is running and healthy"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def simulate_protocol(data: List[Dict[str, Any]], iteration: int, 
                     plate_well: str = "H3", deepplate_well: str = "H3") -> Dict[str, Any]:
    """
    Simulate a protocol using the API server
    
    Args:
        data: List of experimental data dictionaries
        iteration: Iteration number
        plate_well: Starting plate well position
        deepplate_well: Starting deep plate well position
    
    Returns:
        Dictionary containing simulation results
    """
    if not check_api_health():
        raise APIError("API server is not available")
    
    payload = {
        "data": data,
        "iteration": iteration,
        "plate_well": plate_well,
        "deepplate_well": deepplate_well
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/simulate", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to simulate protocol: {str(e)}")


def execute_protocol(protocol_text: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute a protocol on the Opentrons robot using the API server
    
    Args:
        protocol_text: The protocol code to execute
        run_id: Optional run identifier
    
    Returns:
        Dictionary containing execution results
    """
    if not check_api_health():
        raise APIError("API server is not available")
    
    payload = {
        "protocol_text": protocol_text,
        "run_id": run_id
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/execute", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to execute protocol: {str(e)}")


def generate_and_simulate_protocol(df_vol: pd.DataFrame, iteration: int, 
                                 plate_well: str = "H3", deepplate_well: str = "H3") -> Tuple[str, Dict[str, Any]]:
    """
    Generate and simulate a protocol from experimental design data
    
    This replaces the generate_protocol function from the original helper_functions.py
    and adds simulation capability.
    
    Args:
        df_vol: DataFrame with volume data
        iteration: Iteration number
        plate_well: Starting plate well position
        deepplate_well: Starting deep plate well position
    
    Returns:
        Tuple of (protocol_text, simulation_result)
    """
    # Convert DataFrame to list of dictionaries
    data = df_vol.to_dict('records')
    
    # Simulate the protocol
    simulation_result = simulate_protocol(data, iteration, plate_well, deepplate_well)
    
    if not simulation_result['success']:
        raise APIError(f"Protocol simulation failed: {simulation_result.get('error', 'Unknown error')}")
    
    protocol_text = simulation_result['protocol_text']
    
    # Save the protocol file locally (maintaining compatibility with existing workflow)
    output_path = f'protocol/otflex_{iteration}.py'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(protocol_text)
    
    print(f"✅ Protocol generated and simulated successfully: {output_path}")
    print(f"✅ Simulation log: {simulation_result['run_log']}")
    
    return protocol_text, simulation_result


def run_protocol_on_robot(protocol_text: str, iteration: int) -> Dict[str, Any]:
    """
    Execute a protocol on the Opentrons robot
    
    This replaces the SSH/SCP upload mechanism with API-based execution.
    
    Args:
        protocol_text: The protocol code to execute
        iteration: Iteration number for run ID
    
    Returns:
        Dictionary containing execution results
    """
    run_id = f"iteration_{iteration}"
    
    try:
        execution_result = execute_protocol(protocol_text, run_id)
        
        if execution_result['success']:
            print(f"✅ Protocol executed successfully on robot. Run ID: {execution_result['run_id']}")
        else:
            print(f"❌ Protocol execution failed: {execution_result.get('error', 'Unknown error')}")
        
        return execution_result
        
    except APIError as e:
        print(f"❌ API Error: {str(e)}")
        return {"success": False, "error": str(e)}


# Keep all the existing helper functions from the original file
# These are not modified as they don't involve protocol execution

def optimizer_init():
    """Initialize the optimizer (unchanged from original)"""
    gs = GenerationStrategy(
        steps=[
            GenerationStep(
                model=Models.SOBOL,
                num_trials=1000,
                model_kwargs={"seed": 0},
            ),
            GenerationStep(
                model=Models.BOTORCH_MODULAR,
                num_trials=1000,
                model_kwargs={},
            ),
            GenerationStep(
                model=Models.SAASBO,
                num_trials=1000,
                model_kwargs={},
            ),
        ]
    )

    ax_client = AxClient(generation_strategy=gs)

    ax_client.create_experiment(
        name="drug_surfactant",
        parameters=[
            {"name": "Drug_MW",   "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "Drug_LogP", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "Drug_TPSA", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "surf_1", "type": "choice", "is_ordered": False, "values": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
            {"name": "surf_1_conc", "type": "range", "bounds": [0.0, surfactant_stock_conc], "value_type": "int"},
            {"name": "surf_2", "type": "choice", "is_ordered": False, "values": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
            {"name": "surf_2_conc", "type": "range", "bounds": [0.0, surfactant_stock_conc], "value_type": "int"},
            {"name": "drug_conc", "type": "range", "bounds": [0.0, drug_stock_conc], "value_type": "float"},
        ],
        objectives={
            'obj_surf_conc': ObjectiveProperties(minimize=True),
        },
        parameter_constraints=[
            f"surf_1_conc + surf_2_conc  <= {surfactant_stock_conc-1}",
            'surf_1_conc + surf_2_conc   >= 1',
        ],
    )

    return ax_client


def conc_to_vol_helper(conc, total_volume, stock_conc):
    """Helper function for concentration to volume conversion (unchanged)"""
    vol = (conc * total_volume) / stock_conc
    return vol


def conc_to_vol(df, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume):
    """Convert concentrations to volumes (unchanged from original)"""
    df_vol = pd.DataFrame({
        'trial_index': df['trial_index'],
        'drug_name':  df['drug_name']
    })

    df_vol['drug'] = df['drug_conc'].apply(lambda c: conc_to_vol_helper(c, drug_total_volume, drug_stock_conc))

    s_cols = [f"s{i}" for i in range(1, number_of_surfactants + 1)]
    for s in s_cols:
        df_vol[s] = 0.0

    surf_slots = sorted(
        [col for col in df.columns if re.match(r"^surf_\d+$", col)],
        key=lambda x: int(x.split("_")[1])
    )

    for slot in surf_slots:
        conc_col = f"{slot}_conc"
        slot_volumes = df[conc_col].apply(lambda c: conc_to_vol_helper(c, surfactant_total_volume, surfactant_stock_conc))
        surf_names = df[slot]
        for idx, surf in surf_names.items():
            if pd.isna(surf):
                continue
            if surf not in s_cols:
                continue
            df_vol.at[idx, surf] += slot_volumes.at[idx]

    df_vol['dmso'] = drug_total_volume - df_vol['drug']
    df_vol['water'] = surfactant_total_volume - df_vol[s_cols].sum(axis=1)

    data_cols = df_vol.columns.difference(['trial_index', 'drug_name'])
    df_vol.loc[:, data_cols] *= 1000

    return df_vol


def add_drug_columns(df):
    """Add drug columns (unchanged from original)"""
    unique_drugs = df['drug_name'].unique()
    for d in unique_drugs:
        df[d] = df.apply(lambda row: row['drug'] if row['drug_name'] == d else 0, axis=1)
    return df


def design_to_vol(iteration, drug_stock_conc=drug_stock_conc, drug_total_volume=drug_total_volume, 
                  surfactant_stock_conc=surfactant_stock_conc, surfactant_total_volume=surfactant_total_volume):
    """Convert design to volume (unchanged from original)"""
    df_design = pd.read_csv(design_file_path + 'i' + str(iteration) + '.csv')
    df_vol = conc_to_vol(df_design, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume)
    df_vol_drug = add_drug_columns(df_vol)
    return df_design, df_vol_drug


def process_absorbance(iteration, replicates=3, threshold=0.06):
    """Process absorbance data (unchanged from original)"""
    core_df = pd.read_excel(
        raw_data_file_path + f'i{iteration}.xlsx',
        sheet_name=0, usecols="B:N", skiprows=23, nrows=9
    )
    
    arr = core_df.iloc[:, 1:].to_numpy().flatten(order='C')
    arr = arr[~np.isnan(arr)]
    binary = (arr < threshold).astype(int)
    
    n_chunks = len(binary) // replicates
    summary = []
    for i in range(n_chunks):
        block = binary[i*replicates : (i+1)*replicates]
        success = int(block.all())
        summary.append({
            "trial_index": i,
            "success": success
        })
    
    return pd.DataFrame(summary)


def build_results(iteration, df_absorbance):
    """Build results (unchanged from original)"""
    df_design = pd.read_csv(design_file_path + 'i' + str(iteration) + '.csv')
    results = df_design.copy()
    results['success'] = df_absorbance['success']
    results['obj_surf_conc'] = np.where(results['success'] == 1, results['surf_conc'], surfactant_stock_conc)
    return results


def results_so_far(current_iteration):
    """Get results so far (unchanged from original)"""
    ax_client = AxClient.load_from_json_file("../iteration_" + str(current_iteration-1) + "/" + optimizer_file_path + str(current_iteration-1) + '_loaded.json')
    results = ax_client.get_trials_data_frame()
    return results


def lowest_so_far(df, list_of_drugs):
    """Get lowest values so far (unchanged from original)"""
    result = {}
    for drug in list_of_drugs:
        filtered_df = df[df['drug_name'] == drug]
        if not filtered_df.empty:
            result[drug] = filtered_df['obj_surf_conc'].min()
        else:
            result[drug] = None
    return result


def add_drug_names(df):
    """Add drug names (unchanged from original)"""
    abbr_map = {
        props["normalized_properties"]["Drug_MW"]: abbr
        for abbr, props in normalize_drug_properties_dict.items()
    }
    full_map = {
        props["normalized_properties"]["Drug_MW"]: props["full_name"]
        for props in normalize_drug_properties_dict.values()
    }

    df["drug_name"] = df["Drug_MW"].map(abbr_map)
    df["drug_full"] = df["Drug_MW"].map(full_map)

    return df


def run_optimizer(current_iteration, drug_list, bopt, n_trials=1):
    """Run optimizer (unchanged from original)"""
    if current_iteration == 0:
        ax_client = AxClient.load_from_json_file(optimizer_file_path + '00.json')
    else:
        ax_client = AxClient.load_from_json_file(
            f"../iteration_{current_iteration-1}/{optimizer_file_path}{current_iteration-1}_loaded.json"
        )
        data_so_far = ax_client.get_trials_data_frame()
        data_so_far = add_drug_names(data_so_far)
        best_concs = lowest_so_far(data_so_far, drug_list)

    ax_client.generation_strategy._curr = ax_client.generation_strategy._steps[bopt]

    trials_data = []
    count = 0

    for drug in drug_list:
        count += 1
        print(f"\n{'*'*80} {count}/{len(drug_list)} {'*'*80}\n")

        drug_props = normalize_drug_properties_dict[drug]["normalized_properties"].copy()
        drug_props["drug_conc"] = 100
        drug_features = ObservationFeatures(parameters=drug_props)

        best_conc = best_concs[drug]

        space = ax_client.experiment.search_space
        param_objs = [
            space._parameters["surf_1_conc"],
            space._parameters["surf_2_conc"],
        ]
        new_constraints = [
            SumConstraint(parameters=param_objs, is_upper_bound=True,  bound=best_conc -2),
            SumConstraint(parameters=param_objs, is_upper_bound=False, bound=1),
        ]
        space._parameter_constraints = new_constraints
        print(f"Update constraints (drug={drug})：surf_1_conc+surf_2_conc <= {best_conc -2}，>=1")

        gs = ax_client.generation_strategy
        curr = gs._curr
        if hasattr(curr, "model_specs"):
            for spec in curr.model_specs:
                spec._fitted_model = None
        if hasattr(curr, "_model"):
            curr._model = None
        if hasattr(gs, "_model"):
            gs._model = None

        for _ in range(n_trials):
            parameters, trial_index = ax_client.get_next_trial(
                fixed_features=drug_features,
                force=True,
            )
            trials_data.append({
                "trial_index": trial_index,
                "drug_name": drug,
                **parameters,
            })

    df_design = pd.DataFrame(trials_data)
    df_design['surf_conc'] = df_design['surf_1_conc'] + df_design['surf_2_conc']
    df_design['obj_surf_conc'] = None

    ax_client.save_to_json_file(f"{optimizer_file_path}{current_iteration}.json")
    df_design.to_csv(f"{design_file_path}i{current_iteration}.csv", index=False)

    return df_design, ax_client, data_so_far, best_concs


def load_design_optimizer(iteration):
    """Load design optimizer (unchanged from original)"""
    ax_client = AxClient.load_from_json_file(optimizer_file_path + str(iteration) + '.json')
    return ax_client


def load_data_to_optimizer(iteration, results):
    """Load data to optimizer (unchanged from original)"""
    ax_client = AxClient.load_from_json_file(optimizer_file_path + str(iteration) + '.json')
    labeled_data = results.copy()

    for _, row in labeled_data.iterrows():
        trial_index = int(row["trial_index"])
        obj_surf_conc = row["obj_surf_conc"]

        raw_data = {
            "obj_surf_conc": obj_surf_conc,
        }
        
        ax_client.complete_trial(trial_index=trial_index, raw_data=raw_data)
    
    ax_client.save_to_json_file(optimizer_file_path + str(iteration) + '_loaded.json')
    return ax_client


def update_data_to_optimizer(iteration, list_of_new_failures):
    """Update data to optimizer (unchanged from original)"""
    json_path = optimizer_file_path + f"{iteration}.json"
    ax_client = AxClient.load_from_json_file(json_path)

    before_updated_path = optimizer_file_path + f"{iteration}_before_updated.json"
    ax_client.save_to_json_file(before_updated_path)

    trials_df = ax_client.get_trials_data_frame()

    for trial_index in list_of_new_failures:
        if trial_index not in trials_df["trial_index"].values:
            print(f"Trial {trial_index} not found – skipping.")
            continue

        new_data = {
            "success": 0,
            "surfactant_input": 1,
            "complexity": 1,
        }

        ax_client.update_trial_data(trial_index=trial_index, raw_data=new_data)
        print(f"Updated trial {trial_index}: set success=0, surfactant_input=1, complexity=1")

    updated_path = optimizer_file_path + f"{iteration}_loaded.json"
    ax_client.save_to_json_file(updated_path)
    return ax_client


def get_iteration_number():
    """Get iteration number (unchanged from original)"""
    current_dir = os.getcwd()
    folder_name = os.path.basename(current_dir)
    match = re.search(r"iteration_(\d+)", folder_name)
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Wrong file")


# Deprecated function - replaced by API-based approach
def upload_file_to_robot(local_file_path, remote_file_name):
    """
    DEPRECATED: This function used SSH/SCP to upload files to the robot.
    Use generate_and_simulate_protocol() and run_protocol_on_robot() instead.
    """
    print("⚠️  WARNING: upload_file_to_robot() is deprecated.")
    print("   Use generate_and_simulate_protocol() and run_protocol_on_robot() instead.")
    print("   These new functions use the FastAPI server with opentrons.simulate and opentrons.execute.")
    
    # Keep the old implementation for backward compatibility if needed
    import subprocess
    
    remote_user = 'root'
    remote_host = '192.168.10.143'
    remote_folder = '/var/lib/jupyter/notebooks/Zeqing_Bao/drug_surfactant/'
    remote_file_path = remote_folder + remote_file_name

    mkdir_command = ['ssh', f'{remote_user}@{remote_host}', f'mkdir -p {remote_folder}']
    mkdir_result = subprocess.run(mkdir_command, capture_output=True, text=True)
    
    if mkdir_result.returncode == 0:
        print("Remote notebooks directory ready.")
    else:
        print("Failed to verify/create notebooks directory.")
        print("Error:", mkdir_result.stderr)

    scp_command = ['scp', local_file_path, f'{remote_user}@{remote_host}:{remote_file_path}']
    scp_result = subprocess.run(scp_command, capture_output=True, text=True)
    
    if scp_result.returncode == 0:
        print("File transfer successful!")
    else:
        print("File transfer failed.")
        print("Error:", scp_result.stderr)