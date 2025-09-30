# Failed Experiment Handling

This document describes the failed experiment handling feature added to the drug-surfactant optimization workflow.

## Problem

When using Bayesian optimization with Ax, some parameter combinations may be physically infeasible. For example:
- Concentrations that are too high for the available stock solutions
- Parameter combinations that result in negative volumes (e.g., requiring more solvent than the total volume)
- Experimental conditions that would fail in practice

Previously, these failures would cause the optimization loop to crash or produce incorrect results. The optimizer would not learn from these failures.

## Solution

The solution adds proper error handling using Ax's built-in trial failure mechanism:

### 1. Validation in `conc_to_vol` function

The `conc_to_vol` function now checks for negative volumes (which indicate infeasible experiments):

```python
# Check for invalid volumes (negative values indicate infeasible experiments)
if (df_vol['dmso'] < 0).any() or (df_vol['water'] < 0).any():
    raise ValueError("Invalid experimental parameters: negative volumes calculated. "
                    "This indicates concentrations are too high for the available stock solutions.")
```

### 2. New `safe_complete_trial` function

A new helper function `safe_complete_trial` wraps the trial completion logic with error handling:

```python
def safe_complete_trial(ax_client, trial_index, parameterization, 
                        drug_stock_conc=50, drug_total_volume=0.12, 
                        surfactant_stock_conc=50, surfactant_total_volume=1):
    """
    Safely complete a trial with error handling for failed experiments.
    
    If the experiment fails due to invalid parameters, the trial is marked 
    as failed instead of completed.
    
    Returns:
        True if trial completed successfully, False if trial failed
    """
```

The function:
1. Validates that the experimental parameters can produce valid volumes
2. Runs the virtual experiment
3. Completes the trial normally if valid
4. Marks the trial as FAILED using `ax_client.mark_trial_failed()` if invalid

## Usage

### Before (without error handling):

```python
for trial_index, parameterization in parameterizations.items():
    s1 = parameterization["s1"]
    s2 = parameterization["s2"]
    # ... extract all parameters ...
    
    results = hf.virtual_exp(s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12)
    ax_client.complete_trial(trial_index=trial_index, raw_data=results)
```

Problems:
- Crashes if parameters are invalid
- No way to handle failures
- Optimizer doesn't learn to avoid bad parameter regions

### After (with error handling):

```python
for trial_index, parameterization in parameterizations.items():
    success = hf.safe_complete_trial(
        ax_client=ax_client,
        trial_index=trial_index,
        parameterization=parameterization
    )
    
    if success:
        print(f"Trial {trial_index} completed successfully")
    else:
        print(f"Trial {trial_index} failed - marked as FAILED")
```

Benefits:
- Gracefully handles invalid parameters
- Failed trials are properly marked in Ax
- Optimizer learns to avoid problematic parameter regions
- Workflow continues even if some trials fail

## Example

See `example_safe_trials.py` for a complete working example.

## API Reference

### `safe_complete_trial`

```python
def safe_complete_trial(ax_client, trial_index, parameterization, 
                        drug_stock_conc=50, drug_total_volume=0.12, 
                        surfactant_stock_conc=50, surfactant_total_volume=1)
```

**Parameters:**
- `ax_client`: The Ax client instance
- `trial_index`: Index of the trial to complete
- `parameterization`: Dictionary of parameter values for the trial
- `drug_stock_conc`: Stock concentration of drug (mg/mL), default: 50
- `drug_total_volume`: Total volume for drug solution (mL), default: 0.12
- `surfactant_stock_conc`: Stock concentration of surfactant (mg/mL), default: 50
- `surfactant_total_volume`: Total volume for surfactant solution (mL), default: 1

**Returns:**
- `True` if trial completed successfully
- `False` if trial failed and was marked as FAILED

**Exceptions Caught:**
- `ValueError`: Invalid experimental parameters (e.g., negative volumes)
- `KeyError`: Missing required parameters
- `Exception`: Any other unexpected errors

## Trial Status

After using this feature, you can check trial statuses:

```python
df = ax_client.get_trials_data_frame()
print(df[['trial_index', 'trial_status']])
```

Trial statuses:
- `COMPLETED`: Trial succeeded and has valid metric values
- `FAILED`: Trial was marked as failed due to invalid parameters
- `ABANDONED`: Trial was manually abandoned (not used by this feature)

## Implementation Details

The validation works by:

1. Creating a temporary dataframe with the trial parameters
2. Attempting to convert concentrations to volumes using `design_to_conc_to_vol`
3. Checking for negative volumes (DMSO or water)
4. Raising a ValueError if any volumes are negative

Failed trials are marked using Ax's built-in `mark_trial_failed()` method, which:
- Sets the trial status to FAILED
- Excludes the trial from model training
- Allows the optimization to continue with new trials
- Can be analyzed later to understand which parameter regions are problematic

## References

- Ax documentation on trial lifecycle: https://ax.dev/docs/experiment.html
- GitHub issues on handling failed experiments: facebook/Ax#2574, facebook/Ax#999
