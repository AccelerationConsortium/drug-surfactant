"""
Example: Using safe_complete_trial for robust experiment handling

This script demonstrates how to use the new safe_complete_trial function
to handle failed experiments when parameters lead to invalid experimental conditions.
"""

import helper_functions as hf

# Initialize the Ax client
ax_client = hf.optimizer_init()

# Save initial state
ax_client.save_to_json_file('optimizer/optimizer_init.json')

optimizer_file_path = 'optimizer/optimizer_'

# Run optimization loop with error handling
for i in range(20):
    batch_size = 1
    parameterizations, optimization_complete = ax_client.get_next_trials(batch_size)
    
    for trial_index, parameterization in list(parameterizations.items()):
        print(f"\n--- Trial {trial_index} ---")
        print(f"Parameters: surfactant_conc={parameterization['surfactant_conc']}, "
              f"drug_conc={parameterization['drug_conc']}")
        
        # Use safe_complete_trial instead of manual complete_trial
        # This will automatically mark the trial as failed if parameters are invalid
        success = hf.safe_complete_trial(
            ax_client=ax_client,
            trial_index=trial_index,
            parameterization=parameterization,
            drug_stock_conc=50,
            drug_total_volume=0.12,
            surfactant_stock_conc=50,
            surfactant_total_volume=1
        )
        
        if success:
            print(f"✓ Trial {trial_index} completed successfully")
        else:
            print(f"✗ Trial {trial_index} failed - marked as FAILED")
        
        # Save state after each trial
        ax_client.save_to_json_file(optimizer_file_path + str(i) + '.json')

# Get results
df = ax_client.get_trials_data_frame()
print("\nExperiment Summary:")
print(df[['trial_index', 'trial_status', 'surfactant_conc', 'drug_conc']])

# Note: Failed trials will have trial_status == 'FAILED' and won't have metric values
