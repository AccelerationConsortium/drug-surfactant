# Migration Guide: Adding Failed Experiment Handling to Existing Workflows

This guide shows how to update existing optimization workflows to use the new failed experiment handling.

## Quick Migration

### Step 1: Update your optimization loop

**Before:**
```python
for i in range(num_iterations):
    parameterizations, optimization_complete = ax_client.get_next_trials(batch_size)
    for trial_index, parameterization in list(parameterizations.items()):
        # Extract parameters
        s1 = parameterization["s1"]
        s2 = parameterization["s2"]
        # ... etc ...
        
        # Run experiment
        results = hf.virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12)
        
        # Complete trial
        ax_client.complete_trial(trial_index=trial_index, raw_data=results)
```

**After:**
```python
for i in range(num_iterations):
    parameterizations, optimization_complete = ax_client.get_next_trials(batch_size)
    for trial_index, parameterization in list(parameterizations.items()):
        # Use safe_complete_trial - no need to extract individual parameters
        success = hf.safe_complete_trial(
            ax_client=ax_client,
            trial_index=trial_index,
            parameterization=parameterization
        )
        
        if success:
            print(f"✓ Trial {trial_index} completed successfully")
        else:
            print(f"✗ Trial {trial_index} failed and was marked as FAILED")
```

## Detailed Examples

### Example 1: Simple workflow (workflow_test.ipynb style)

```python
import helper_functions as hf

# Initialize
ax_client = hf.optimizer_init()
ax_client.save_to_json_file('optimizer/optimizer_init.json')

optimizer_file_path = 'optimizer/optimizer_'

# Run optimization
for i in range(20):
    batch_size = 1
    parameterizations, optimization_complete = ax_client.get_next_trials(batch_size)
    
    for trial_index, parameterization in list(parameterizations.items()):
        # NEW: Use safe_complete_trial instead of manual handling
        success = hf.safe_complete_trial(
            ax_client=ax_client,
            trial_index=trial_index,
            parameterization=parameterization
        )
        
        # Save after each trial
        ax_client.save_to_json_file(optimizer_file_path + str(i) + '.json')
        
        if success:
            print(f"Trial {trial_index} completed.")
        else:
            print(f"Trial {trial_index} failed.")

# Get results (now includes trial status)
df = ax_client.get_trials_data_frame()
print(df[['trial_index', 'trial_status', 'complexity', 'cost', 'performance']])
```

### Example 2: With custom stock concentrations

```python
# If you're using non-default stock concentrations
for trial_index, parameterization in parameterizations.items():
    success = hf.safe_complete_trial(
        ax_client=ax_client,
        trial_index=trial_index,
        parameterization=parameterization,
        drug_stock_conc=100,      # Custom value
        drug_total_volume=0.2,    # Custom value
        surfactant_stock_conc=75, # Custom value
        surfactant_total_volume=1.5  # Custom value
    )
```

### Example 3: With additional logging/handling

```python
failed_trials = []
successful_trials = []

for trial_index, parameterization in parameterizations.items():
    print(f"\nTrying trial {trial_index} with params:")
    print(f"  surfactant_conc: {parameterization['surfactant_conc']}")
    print(f"  drug_conc: {parameterization['drug_conc']}")
    
    success = hf.safe_complete_trial(
        ax_client=ax_client,
        trial_index=trial_index,
        parameterization=parameterization
    )
    
    if success:
        successful_trials.append(trial_index)
        print(f"  ✓ Success")
    else:
        failed_trials.append((trial_index, parameterization))
        print(f"  ✗ Failed - parameters were infeasible")

print(f"\nSummary:")
print(f"  Successful: {len(successful_trials)}")
print(f"  Failed: {len(failed_trials)}")
```

## What Changed?

### In `helper_functions.py`:

1. **`conc_to_vol()` now validates volumes:**
   - Checks for negative volumes before returning
   - Raises `ValueError` if volumes are invalid

2. **New function `safe_complete_trial()`:**
   - Wraps the trial completion logic
   - Validates parameters before running experiment
   - Marks failed trials using `ax_client.mark_trial_failed()`
   - Returns `True`/`False` to indicate success

## Benefits of Migration

1. **Robustness**: Your workflow won't crash on invalid parameters
2. **Better optimization**: Ax learns to avoid problematic parameter regions
3. **Visibility**: Failed trials are clearly marked in the results
4. **Simplicity**: Less code to write - no manual parameter extraction needed

## Backward Compatibility

The old approach will still work, but won't benefit from automatic failure handling:

```python
# This still works but won't handle failures gracefully
results = hf.virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12)
ax_client.complete_trial(trial_index=trial_index, raw_data=results)
```

However, if you use `design_to_conc_to_vol()` separately with invalid parameters, it will now raise a `ValueError` instead of producing incorrect results.

## Troubleshooting

### "Trial X marked as FAILED" appearing frequently

This means the optimizer is suggesting parameters that are physically infeasible. Common causes:

1. **Parameter bounds too wide**: Consider narrowing the bounds on `surfactant_conc` or `drug_conc`
2. **Stock concentrations too low**: Increase `drug_stock_conc` or `surfactant_stock_conc`
3. **Total volumes too small**: Increase `drug_total_volume` or `surfactant_total_volume`

### Understanding which parameters caused failures

```python
# After optimization, check failed trials
df = ax_client.get_trials_data_frame()
failed_df = df[df['trial_status'] == 'FAILED']
print("Failed trial parameters:")
print(failed_df[['trial_index', 'surfactant_conc', 'drug_conc']])
```

### All trials failing

If ALL trials are failing, check your stock concentrations and volumes:

```python
# Example: verify your setup makes sense
drug_stock_conc = 50  # mg/mL
drug_total_volume = 0.12  # mL
max_drug_conc = 50  # mg/mL (from parameter bounds)

# Check if this is feasible
required_volume = (max_drug_conc * drug_total_volume) / drug_stock_conc
print(f"Max required volume: {required_volume:.4f} mL")
print(f"Available volume: {drug_total_volume:.4f} mL")
print(f"Feasible: {required_volume <= drug_total_volume}")
```

## See Also

- [FAILED_EXPERIMENT_HANDLING.md](FAILED_EXPERIMENT_HANDLING.md) - Detailed documentation
- [example_safe_trials.py](example_safe_trials.py) - Complete working example
