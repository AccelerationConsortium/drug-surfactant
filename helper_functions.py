import pandas as pd
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
from ax.modelbridge.factory import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
import subprocess


def virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12):

    complexity = sum(1 for x in [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12] if x != 0)
    cost = s1+s2+s3+s4+s5+s6+s7+s8+s9+s10+s11+s12
    performance = 0.3*s1*(1+s2) - 0.5*s3*s4 + s5**2 + 0.8*s9 - s10*s11 + 0.2*s12
    return {'complexity': complexity, 'cost': cost, 'performance': performance}

def optimizer_init():
    
    # generation strategy
    gs = GenerationStrategy(
        steps=[
            GenerationStep(
                model=Models.SOBOL,
                num_trials=8,  # how many sobol trials to perform (rule of thumb: 2 * number of params)
                model_kwargs={"seed": 0},
            ),
            GenerationStep(
                model=Models.SAASBO,
                num_trials=-1,
                model_kwargs={},
            ),
        ]
    )

    # initialize the AxClient
    ax_client = AxClient(generation_strategy=gs)

    # create the design space and objective space
    ax_client.create_experiment(

        name="drug_surfactant",
        parameters = [
            {"name": f"s{i}", "type": "range", "bounds": [0, 20], "value_type": "int"} for i in range(1, 13)] + 

            [{"name": "surfactant_conc", "type": "range", "bounds": [1, 50], "value_type": "int"},
             {"name": "drug_conc",       "type": "range", "bounds": [1, 50], "value_type": "int"}],

        objectives={
            'complexity': ObjectiveProperties(minimize=True, threshold=5),
            'cost': ObjectiveProperties(minimize=True, threshold=0.5),
            'performance': ObjectiveProperties(minimize=False),
        },

        parameter_constraints=[
            "s1 + s2 + s3 + s4 + s5 + s6 + s7 + s8 + s9 + s10 + s11 + s12 >= 1", 
        ],
    )

    return ax_client


def design_to_conc(df):

    df_conc = pd.DataFrame()
    df_conc['trial_index'] = df['trial_index']
    df_conc['surfactant_conc'] = df['surfactant_conc']
    df_conc['drug_conc'] = df['drug_conc']
    total_ratios = [f's{i}' for i in range(1, 13)]
    total_sum = df[total_ratios].sum(axis=1)
    for i in range(1, 13):
        df_conc[f's{i}'] = df[f's{i}'] / total_sum * df_conc['surfactant_conc']
    return df_conc

def conc_to_vol_helper(conc, total_volume, stock_conc):
    vol = (conc * total_volume) / stock_conc
    return vol

def conc_to_vol(df, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume): # in mg/mL or mL

    df_vol = pd.DataFrame()
    df_vol['trial_index'] = df['trial_index']
    df_vol['drug'] = df['drug_conc'].apply(lambda conc: conc_to_vol_helper(conc, total_volume=drug_total_volume, stock_conc=drug_stock_conc))
    s_cols = [f"s{i}" for i in range(1, 13) if f"s{i}" in df.columns]
    for s_col in s_cols:
        df_vol[s_col] = df[s_col].apply(lambda conc: conc_to_vol_helper(conc, total_volume=surfactant_total_volume, stock_conc=surfactant_stock_conc))
    df_vol['dmso'] = drug_total_volume - df_vol['drug']

    df_vol['water'] = surfactant_total_volume - df_vol[s_cols].sum(axis=1)
    
    # Check for invalid volumes (negative values indicate infeasible experiments)
    if (df_vol['dmso'] < 0).any() or (df_vol['water'] < 0).any():
        raise ValueError("Invalid experimental parameters: negative volumes calculated. "
                        "This indicates concentrations are too high for the available stock solutions.")
    
    df_vol.loc[:, df_vol.columns != 'trial_index'] *= 1000 # convert to uL

    return df_vol

def design_to_conc_to_vol(df, drug_stock_conc=50, drug_total_volume=0.12, surfactant_stock_conc=50, surfactant_total_volume=1): # in mg/mL or mL
    
    df_conc = design_to_conc(df)
    df_vol = conc_to_vol(df_conc, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume)

    return df_conc, df_vol


def safe_complete_trial(ax_client, trial_index, parameterization, drug_stock_conc=50, drug_total_volume=0.12, 
                        surfactant_stock_conc=50, surfactant_total_volume=1):
    """
    Safely complete a trial with error handling for failed experiments.
    
    If the experiment fails due to invalid parameters (e.g., concentrations too high),
    the trial is marked as failed instead of completed.
    
    Args:
        ax_client: The Ax client instance
        trial_index: Index of the trial to complete
        parameterization: Dictionary of parameter values for the trial
        drug_stock_conc: Stock concentration of drug (mg/mL)
        drug_total_volume: Total volume for drug solution (mL)
        surfactant_stock_conc: Stock concentration of surfactant (mg/mL)
        surfactant_total_volume: Total volume for surfactant solution (mL)
        
    Returns:
        True if trial completed successfully, False if trial failed
    """
    try:
        # Extract surfactant parameters
        s_params = {f"s{i}": parameterization[f"s{i}"] for i in range(1, 13)}
        
        # Run virtual experiment
        results = virtual_exp(**s_params)
        
        # Create a temporary dataframe to validate volumes can be calculated
        temp_df = pd.DataFrame([{
            'trial_index': trial_index,
            **s_params,
            'surfactant_conc': parameterization['surfactant_conc'],
            'drug_conc': parameterization['drug_conc']
        }])
        
        # Validate that volumes can be calculated (this will raise ValueError if invalid)
        df_conc, df_vol = design_to_conc_to_vol(
            temp_df, 
            drug_stock_conc=drug_stock_conc,
            drug_total_volume=drug_total_volume,
            surfactant_stock_conc=surfactant_stock_conc,
            surfactant_total_volume=surfactant_total_volume
        )
        
        # If we get here, the experiment is valid
        ax_client.complete_trial(trial_index=trial_index, raw_data=results)
        return True
        
    except (ValueError, KeyError, Exception) as e:
        # Mark trial as failed if any error occurs
        ax_client.mark_trial_failed(trial_index=trial_index)
        print(f"Trial {trial_index} marked as FAILED. Reason: {str(e)}")
        return False


def upload_file_to_robot(local_file_path, remote_file_name):

    remote_user = 'root'
    remote_host = '192.168.10.143'

    remote_folder = '/var/lib/jupyter/notebooks/Zeqing_Bao/drug_surfactant/'
    remote_file_path = remote_folder + remote_file_name

    mkdir_command = [
        'ssh',
        f'{remote_user}@{remote_host}',
        f'mkdir -p {remote_folder}'
    ]

    mkdir_result = subprocess.run(mkdir_command, capture_output=True, text=True)
    if mkdir_result.returncode == 0:
        print("Remote notebooks directory ready.")
    else:
        print("Failed to verify/create notebooks directory.")
        print("Error:", mkdir_result.stderr)

    scp_command = [
        'scp',
        local_file_path,
        f'{remote_user}@{remote_host}:{remote_file_path}'
    ]

    scp_result = subprocess.run(scp_command, capture_output=True, text=True)
    if scp_result.returncode == 0:
        print("File transfer successful!")
    else:
        print("File transfer failed.")
        print("Error:", scp_result.stderr)
