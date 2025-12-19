import pandas as pd
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
import matplotlib.pyplot as plt
from ax.modelbridge.registry import Generators

from ax.core.observation import ObservationFeatures
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
import json
import subprocess
import os
import re
from ax.core.parameter_constraint import SumConstraint

from pathlib import Path

# helpers.py is in:  .../drug_surfactant/utils/helpers.py
THIS_DIR = Path(__file__).resolve().parent          # .../drug_surfactant/utils
PROJECT_ROOT = THIS_DIR.parent                      # .../drug_surfactant

optimizer_file_path = PROJECT_ROOT /'experiments/optimizers/optimizer_'
design_data_path = PROJECT_ROOT /'experiments/design_data/design_i'
raw_data_file_path = PROJECT_ROOT /'experiments/raw_data/raw_absorbance_'
otflex_template_file_path = PROJECT_ROOT /'utils/drug_surfactant_otflex_template.py'
otflex_output_file_path = PROJECT_ROOT /'experiments/protocol/otflex_'
#results_file_path = 'result/result_'

drug_stock_conc = 25  # mg/mL
surfactant_stock_conc = 100  # represents percent of the stock solution
actual_surfactant_stock_conc = 50 # mg/mL represents the actual conc
drug_total_volume = 0.18  # mL
surfactant_total_volume = 1.2  # mL
number_of_surfactants = 8  # s1 to s8

normalize_drug_properties_dict = {

    'IBP': {
        'full_name': 'Ibuprofen',
        'normalized_properties': {"Drug_MW": 0.2063, "Drug_LogP": 0.3073,  "Drug_TPSA": 0.0373},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'DCF': {
        'full_name': 'Diclofenac',
        'normalized_properties': {"Drug_MW": 0.2962, "Drug_LogP": 0.4364,  "Drug_TPSA": 0.0493},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'LOV': {
        'full_name': 'Lovastatin',
        'normalized_properties': {"Drug_MW": 0.4045, "Drug_LogP": 0.4196,  "Drug_TPSA": 0.0728},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'ITZ': {
        'full_name': 'Itraconazole',
        'normalized_properties': {"Drug_MW": 0.7056, "Drug_LogP": 0.5577,  "Drug_TPSA": 0.1047},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'RPD': {
        'full_name': 'Risperidone',
        'normalized_properties': {"Drug_MW": 0.4105, "Drug_LogP": 0.3590,  "Drug_TPSA": 0.0642},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'GLV': {
        'full_name': 'Griseofulvin',
        'normalized_properties': {"Drug_MW": 0.3528, "Drug_LogP": 0.2810,  "Drug_TPSA": 0.0711},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'CTZ': {
        'full_name': 'Clotrimazole',
        'normalized_properties': {"Drug_MW": 0.3448, "Drug_LogP": 0.5377,  "Drug_TPSA": 0.0178},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

    'GBC': {
        'full_name': 'Glibenclamide/Glyburide',
        'normalized_properties': {"Drug_MW": 0.4940, "Drug_LogP": 0.3642,  "Drug_TPSA": 0.1136},  # normalized values /1000; /10; /1000
        'drug_stock_conc': 25, # mg/mL
    },

}


def optimizer_init():
    
    # generation strategy
    gs = GenerationStrategy(
        steps=[
            GenerationStep(
                model=Generators.SOBOL,
                num_trials=1000,  # how many sobol trials to perform (rule of thumb: 2 * number of params)
                model_kwargs={"seed": 0},
            ),
            GenerationStep(

                model=Generators.BOTORCH_MODULAR,
                num_trials=1000,
                model_kwargs={},
            
            ),
            GenerationStep(

                model=Generators.SAASBO,
                num_trials=1000,
                model_kwargs={},
            
            ),
        ]
    )

    # initialize the AxClient
    ax_client = AxClient(generation_strategy=gs)

    # create the design space and objective space
    ax_client.create_experiment(
        name="drug_surfactant",
        parameters=[
            # drug properties…
            {"name": "Drug_MW",   "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "Drug_LogP", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},
            {"name": "Drug_TPSA", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"},

            {"name": "surf_1", "type": "choice", "is_ordered": False, "values": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
            {"name": "surf_1_conc", "type": "range", "bounds": [0.0, surfactant_stock_conc], "value_type": "int"},

            {"name": "surf_2", "type": "choice", "is_ordered": False, "values": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
            {"name": "surf_2_conc", "type": "range", "bounds": [0.0, surfactant_stock_conc], "value_type": "int"},

            # {"name": "surf_3", "type": "choice", "is_ordered": False, "values": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
            # {"name": "surf_3_conc", "type": "range", "bounds": [0.0, surfactant_stock_conc], "value_type": "int"},

            {"name": "drug_conc",       "type": "range", "bounds": [0.0, drug_stock_conc], "value_type": "float"},
        ],
        objectives={
            'obj_surf_conc':           ObjectiveProperties(minimize=True),
        },

        parameter_constraints=[
            # exactly two surfactants active
            f"surf_1_conc + surf_2_conc  <= {surfactant_stock_conc-1}",
            'surf_1_conc + surf_2_conc   >= 1',
        ],
    )


    return ax_client


def conc_to_vol_helper(conc, total_volume, stock_conc):
    vol = (conc * total_volume) / stock_conc
    return vol

def conc_to_vol(df, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume): # in mg/mL or mL

    # start output
    df_vol = pd.DataFrame({
        'trial_index': df['trial_index'],
        'drug_name':  df['drug_name']
    })

    # drug volume (mL)
    df_vol['drug'] = df['drug_conc'] \
        .apply(lambda c: conc_to_vol_helper(c, drug_total_volume, drug_stock_conc))

    # initialize surfactant volume columns s1…sN
    s_cols = [f"s{i}" for i in range(1, number_of_surfactants + 1)]
    for s in s_cols:
        df_vol[s] = 0.0

    # find all "surf_X" slots dynamically
    surf_slots = sorted(
        [col for col in df.columns if re.match(r"^surf_\d+$", col)],
        key=lambda x: int(x.split("_")[1])
    )

    # for each slot, compute its volume and add it into the correct s# column
    for slot in surf_slots:
        conc_col = f"{slot}_conc"
        # volume from that slot (in mL)
        slot_volumes = df[conc_col] \
            .apply(lambda c: conc_to_vol_helper(c, surfactant_total_volume, surfactant_stock_conc))
        # which surfactant it is
        surf_names = df[slot]
        for idx, surf in surf_names.items():
            if pd.isna(surf):
                continue
            if surf not in s_cols:
                # skip unknown or out‑of‑range surfactants
                continue
            df_vol.at[idx, surf] += slot_volumes.at[idx]

    # calculate dmso and water (mL)
    df_vol['dmso'] = drug_total_volume - df_vol['drug']
    df_vol['water'] = surfactant_total_volume - df_vol[s_cols].sum(axis=1)

    # convert everything except trial_index & drug_name to µL
    data_cols = df_vol.columns.difference(['trial_index', 'drug_name'])
    df_vol.loc[:, data_cols] *= 1000

    return df_vol


def add_drug_columns(df):
    unique_drugs = df['drug_name'].unique()
    for d in unique_drugs:
        df[d] = df.apply(lambda row: row['drug'] if row['drug_name'] == d else 0, axis=1)
    return df

def design_to_vol(iteration, drug_stock_conc=drug_stock_conc, drug_total_volume=drug_total_volume, surfactant_stock_conc=surfactant_stock_conc, surfactant_total_volume=surfactant_total_volume): # in mg/mL or mL
    
    df_design = pd.read_csv(f'{design_data_path}{iteration}.csv')

    df_vol = conc_to_vol(df_design, drug_stock_conc, drug_total_volume, surfactant_stock_conc, surfactant_total_volume)

    df_vol_drug = add_drug_columns(df_vol)

    return df_design, df_vol_drug



def process_absorbance(iteration, replicates=3, threshold=0.06):
    # 1) read your raw block exactly as before
    core_df = pd.read_excel(
        raw_data_file_path + f'i{iteration}.xlsx',
        sheet_name=0, usecols="B:N", skiprows=23, nrows=9
    )
    
    # 2) grab just the numeric part and flatten row-major
    arr = core_df.iloc[:, 1:].to_numpy().flatten(order='C')
    
    # 3) drop all the NaNs
    arr = arr[~np.isnan(arr)]
    
    # 4) binarize
    binary = (arr < threshold).astype(int)
    
    # 5) chop into consecutive chunks of size=replicates
    n_chunks = len(binary) // replicates
    summary = []
    for i in range(n_chunks):
        block   = binary[i*replicates : (i+1)*replicates]
        success = int(block.all())
        summary.append({
            "trial_index": i,
            "success":     success
        })
    
    return pd.DataFrame(summary)

def results_so_far (current_iteration):

    ax_client = AxClient.load_from_json_file(optimizer_file_path + str(current_iteration-1) + '_loaded.json')
    results = ax_client.get_trials_data_frame()

    return results

def lowest_so_far(df, list_of_drugs):

    result = {}
    for drug in list_of_drugs:
        filtered_df = df[df['drug_name'] == drug]
        if not filtered_df.empty:
            result[drug] = filtered_df['obj_surf_conc'].min()
        else:
            result[drug] = None  # or np.nan or skip, depending on your preference
    return result

def add_drug_names(df):
    abbr_map = {
        props["normalized_properties"]["Drug_MW"]: abbr
        for abbr, props in normalize_drug_properties_dict.items()
    }
    full_map = {
        props["normalized_properties"]["Drug_MW"]: props["full_name"]
        for props in normalize_drug_properties_dict.values()
    }

    # add the two new columns
    df["drug_name"] = df["Drug_MW"].map(abbr_map)
    df["drug_full"] = df["Drug_MW"].map(full_map)

    return df

def run_optimizer(current_iteration, drug_list, bopt,n_trials=1):
    # Load optimzer data
    if current_iteration == 0:
        ax_client = AxClient.load_from_json_file(f'{optimizer_file_path}00.json')
        best_concs = None
        best_conc = None
        data_so_far = None
    else:
        ax_client = AxClient.load_from_json_file(
            f"{optimizer_file_path}{current_iteration-1}_loaded.json"
        )
        data_so_far = ax_client.get_trials_data_frame()
        data_so_far = add_drug_names(data_so_far)
        best_concs = lowest_so_far(data_so_far, drug_list)

    # 2. 切换到对应的 generation step（sobol/bo）
    ax_client.generation_strategy._curr = ax_client.generation_strategy._steps[bopt]

    trials_data = []
    count = 0

    for drug in drug_list:
        count += 1
        print(f"\n{'*'*80} {count}/{len(drug_list)} {'*'*80}\n")

        # 3. 构造固定的药物特征
        drug_props = normalize_drug_properties_dict[drug]["normalized_properties"].copy()
        drug_props["drug_conc"] = 100  # 固定药浓度
        drug_features = ObservationFeatures(parameters=drug_props)

        # 4. 取出该 drug 的最新 best_conc
        if current_iteration > 0:
            best_conc = best_concs[drug]

        # 5. 构造并替换新的 search_space 约束
        space = ax_client.experiment.search_space
        param_objs = [
            space._parameters["surf_1_conc"],
            space._parameters["surf_2_conc"],
        ]

        if best_concs is not None and isinstance(best_conc, (int, float)): 
            new_constraints = [
                # 上界：surf_1_conc + surf_2_conc <= best_conc - 1
                SumConstraint(parameters=param_objs, is_upper_bound=True,  bound=best_conc -2),
                # 下界：surf_1_conc + surf_2_conc >= 1
                SumConstraint(parameters=param_objs, is_upper_bound=False, bound=1),
            ]
            space._parameter_constraints = new_constraints
            print(f"Update constraints (drug={drug})：surf_1_conc+surf_2_conc <= {best_conc -2}，>=1")

        # 6. 清除 BoTorch/SAASBO 的拟合缓存，确保使用最新约束重新 fit
        gs = ax_client.generation_strategy
        curr = gs._curr
        # BoTorchAdapter：清除每个 model_spec 的 _fitted_model
        if hasattr(curr, "model_specs"):
            for spec in curr.model_specs:
                spec._fitted_model = None
        # SAASBO：清除 _model
        if hasattr(curr, "_model"):
            curr._model = None
        # 也清除 generation_strategy 级别的 _model （保险起见）
        if hasattr(gs, "_model"):
            gs._model = None

        # 7. 用单条 get_next_trial(force=True) 循环生成 n_trials
        for _ in range(n_trials):
            parameters, trial_index = ax_client.get_next_trial(
                fixed_features=drug_features,
                force=True,
            )
            trials_data.append({
                "trial_index": trial_index,
                "drug_name":   drug,
                **parameters,
            })

    # 8. 整理返回的 DataFrame
    df_design = pd.DataFrame(trials_data)
    df_design['surf_conc'] = df_design['surf_1_conc'] + df_design['surf_2_conc']
    df_design['obj_surf_conc'] = None

    # 9. 保存状态
    ax_client.save_to_json_file(f"{optimizer_file_path}{current_iteration}.json")
    df_design.to_csv(f"{design_data_path}{current_iteration}.csv", index=False)

    return df_design, ax_client, data_so_far, best_concs


def generate_protocol(df_vol, iteration, plate_well, deepplate_well):
    n = iteration

    # Input file (template)
    input_path = otflex_template_file_path

    # Output file (update name as needed)
    output_path = f'{otflex_output_file_path}{n}.py'


    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Replace plate wells in lines (modify in place)
    found_plate = False
    found_deep = False
 
    for i, line in enumerate(lines):
        # Replace next_plate_well
        if not found_plate and re.search(r"next_plate_well\s*=", line):
            lines[i] = re.sub(
                r"next_plate_well\s*=.*",
                f"next_plate_well = '{plate_well}'",
                line
            )
            found_plate = True

    # Replace next_deepplate_well
        if not found_deep and re.search(r"next_deepplate_well\s*=", line):
            lines[i] = re.sub(
                r"next_deepplate_well\s*=.*",
                f"next_deepplate_well = '{deepplate_well}'",
                line
            )
            found_deep = True

        if found_plate and found_deep:
            break

    df_vol_list = []
    for idx, row in df_vol.iterrows():
        df_vol_row = {'': str(idx)}  
        df_vol_row.update({col: str(row[col]) for col in df_vol.columns})
        df_vol_list.append(df_vol_row)

    # Format your df_vol_list
    data_string = json.dumps(df_vol_list, indent=4)

    # Check that the input file exists
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Target file does not exist: {input_path}")

    # Locate the data block
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if re.match(r"\s*#{20,}", line):   # at least 20 '#' in a row
            if start_idx is None:
                start_idx = i
            elif end_idx is None:
                end_idx = i
                break
    

    # Extract indent prefix AFTER finding start_idx
    if start_idx is not None:
        indent_prefix = lines[start_idx][:len(lines[start_idx]) - len(lines[start_idx].lstrip())]
    else:
        indent_prefix = "    "

    # Replace block and write new file
    if start_idx is not None and end_idx is not None:
        hash_line = indent_prefix + "#" * 136 + "\n"
        data_lines = data_string.split('\n')
        first_line = indent_prefix + "    " + "data = " + data_lines[0].lstrip() + "\n"
        rest_lines = '\n'.join(indent_prefix + line for line in data_lines[1:]) + "\n"
        data_line = first_line + rest_lines
        replacement = [hash_line, data_line, hash_line]
        new_lines = lines[:start_idx] + replacement + lines[end_idx:]

        # Only create directory if needed
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Write to new output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        print(f"✅ Successfully wrote to: {output_path}")
    else:
        print("❌ Could not locate the block to replace.")

def load_design_optimizer(iteration):

    n = iteration

    ax_client = AxClient.load_from_json_file(f'{optimizer_file_path}{n}.json')

    return ax_client

def absorbance_to_results_df(
    absorbance: dict,
    surf_conc_per_trial: list,
    replicates: int = 3,
    threshold: float = 0.06,
    fallback_surf_conc: float = None,
):

    # 1) enforce A1→H12 row-major order
    ordered_vals = []
    for row in "ABCDEFGH":
        for col in range(1, 13):
            well = f"{row}{col}"
            if well in absorbance:
                ordered_vals.append(absorbance[well])

    arr = np.array(ordered_vals)

    # 2) binarize absorbance
    binary = (arr < threshold).astype(int)

    # 3) chunk into trials
    n_trials = len(binary) // replicates
    rows = []

    for i in range(n_trials):
        block = binary[i * replicates : (i + 1) * replicates]
        success = block.all()

        surf_conc = surf_conc_per_trial[i]

        obj_surf_conc = (
            surf_conc if success else fallback_surf_conc
        )

        rows.append({
            "trial_index": i,
            "obj_surf_conc": obj_surf_conc
        })

    return pd.DataFrame(rows)

def load_data_to_optimizer(iteration, results):
    
    n=iteration
    ax_client = AxClient.load_from_json_file(optimizer_file_path + str(n) + '.json')
    labeled_data = results.copy()

    for _, row in labeled_data.iterrows():
        trial_index = int(row["trial_index"])
        # pull the original values
        obj_surf_conc = row["obj_surf_conc"]


        # build the payload
        raw_data = {
            "obj_surf_conc": obj_surf_conc,
        }
        
        ax_client.complete_trial(trial_index=trial_index, raw_data=raw_data)
    
    ax_client.save_to_json_file(optimizer_file_path + str(n) + '_loaded.json')

    return ax_client


def update_data_to_optimizer(iteration, list_of_new_failures):


    # Load the existing optimizer state
    json_path = optimizer_file_path + f"{iteration}.json"
    ax_client = AxClient.load_from_json_file(json_path)


    before_updated_path = optimizer_file_path + f"{iteration}_before_updated.json"
    ax_client.save_to_json_file(before_updated_path)

    # Fetch current trials
    trials_df = ax_client.get_trials_data_frame()

    for trial_index in list_of_new_failures:
        # Make sure we actually have this trial
        if trial_index not in trials_df["trial_index"].values:
            print(f"Trial {trial_index} not found – skipping.")
            continue

        # Build the forced-failure payload
        new_data = {
            "success": 0,
            "surfactant_input": 1,
            "complexity": 1,
        }

        # Update the trial in-place
        ax_client.update_trial_data(trial_index=trial_index, raw_data=new_data)
        print(f"Updated trial {trial_index}: set success=0, surfactant_input=1, complexity=1")

    # Save out the updated optimizer state
    updated_path = optimizer_file_path + f"{iteration}_loaded.json"
    ax_client.save_to_json_file(updated_path)

    return ax_client

def get_iteration_number():

    current_dir = os.getcwd()

    folder_name = os.path.basename(current_dir)

    match = re.search(r"iteration_(\d+)", folder_name)
    if match:
        return int(match.group(1))
    else:
        raise ValueError("Wrong file")

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
