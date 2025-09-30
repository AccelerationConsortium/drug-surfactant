# Issue Resolution: Batch Conditioning in update_results.ipynb

## Problem Statement

The current implementation in `experiments/20250917_closed_loop/update_results.ipynb` (from the `fully_automated_workflow` branch) manually updates trials with fantasy data using `update_trial_data()`. This approach was used to handle batch conditioning for Bayesian optimization.

## Analysis of Current Implementation

Looking at the code in `update_results.ipynb`:

```python
def update_data_to_optimizer(ax_client, list_of_new_failures, list_of_new_success):
    # ...
    for trial_index in list_of_new_failures:
        new_failure = {
            "obj_surf_conc": hf.surfactant_stock_conc,  # Fantasy failure value
        }
        ax_client.update_trial_data(trial_index=trial_index, raw_data=new_failure)
    
    for trial_index in list_of_new_success:
        surf_conc_success = ...  # Calculate success value
        new_success = {
            "obj_surf_conc": surf_conc_success,
        }
        ax_client.update_trial_data(trial_index=trial_index, raw_data=new_success)
```

This approach manually updates completed trials to reflect corrected outcomes after the fact.

## Recommended Solution

### Understanding the Two Use Cases

After analyzing the code, there are actually **two different scenarios** that need different solutions:

#### Scenario 1: Real-Time Batch Conditioning (During Trial Generation)

If you want to generate multiple trials in parallel and have the model condition on pending trials:

**Use `get_next_trials()`** - No fantasy updates needed!

```python
# Generate batch of trials
trials_dict, _ = ax_client.get_next_trials(max_trials=batch_size)

# Trials are automatically in RUNNING state and treated as pending
# The model will condition on these when generating subsequent trials

# Complete trials when data is available
for trial_idx, params in trials_dict.items():
    results = run_experiment(**params)
    ax_client.complete_trial(trial_index=trial_idx, raw_data=results)
```

#### Scenario 2: Post-Hoc Data Correction (Current update_results.ipynb Use Case)

The `update_results.ipynb` notebook appears to be correcting trial outcomes **after** trials were completed. This is a different use case than typical batch conditioning.

**For post-hoc updates, `update_trial_data()` is actually the correct approach!**

```python
# This is appropriate when you need to fix/update completed trials
ax_client.update_trial_data(
    trial_index=trial_index,
    raw_data=corrected_data
)
```

## Key Insights

### 1. `update_trial_data()` is NOT for Fantasy Modeling

The `update_trial_data()` method is designed for:
- ✅ Correcting data in completed trials
- ✅ Adding additional metrics to completed trials
- ❌ NOT for batch conditioning during trial generation

### 2. Batch Conditioning is Automatic with Proper Workflow

For batch conditioning during optimization:
- Use `get_next_trials()` for batch generation
- Trials in RUNNING/STAGED status are automatically treated as pending
- No manual updates needed

### 3. The update_results.ipynb Use Case is Special

The notebook appears to handle a specific workflow where:
1. Trials are run and completed
2. Later, outcomes are re-evaluated (e.g., success/failure determination)
3. Data needs to be corrected retroactively

For this workflow, **`update_trial_data()` is appropriate**.

## Recommendations

### If Your Goal is Batch Conditioning During Optimization:

**Don't use `update_results.ipynb` pattern**. Instead:

```python
# Option 1: Batch generation (recommended)
trials_dict, _ = ax_client.get_next_trials(max_trials=3)
for trial_idx, params in trials_dict.items():
    # Run experiments in parallel
    results = run_experiment(**params)
    ax_client.complete_trial(trial_index=trial_idx, raw_data=results)

# Option 2: Sequential with automatic conditioning
for i in range(3):
    params, trial_idx = ax_client.get_next_trial()
    # This trial is automatically pending for subsequent calls
    results = run_experiment(**params)
    ax_client.complete_trial(trial_index=trial_idx, raw_data=results)
```

### If You Need Post-Hoc Data Correction:

**Keep using the current approach** with `update_trial_data()`:

```python
# This is correct for fixing completed trials
ax_client.update_trial_data(
    trial_index=trial_index,
    raw_data=corrected_data
)
```

However, consider whether your workflow can be improved to:
1. Determine success/failure before completing trials
2. Use `log_trial_failure()` for failed trials instead of completing them with bad data

## Migration Strategy

### Current Workflow Analysis

If `update_results.ipynb` is being used as part of the main optimization loop:

1. **Assess why data correction is needed**
   - Is it because trials are completed before results are known?
   - Is it because success criteria change after completion?

2. **Consider workflow improvements**
   - Complete trials only when final results are available
   - Use trial status (RUNNING) to represent in-flight experiments
   - Use `log_trial_failure()` for failed trials

3. **Migrate to batch generation if appropriate**
   - If you're generating trials in batches, use `get_next_trials()`
   - If you're running experiments in parallel, let Ax track pending trials automatically

### Example Migration

**Before (if using update_results for batch conditioning):**
```python
# Generate trials
for i in range(batch_size):
    params, trial_idx = ax_client.get_next_trial()
    # Update with fantasy data
    ax_client.update_trial_data(trial_idx, fantasy_data)

# Later, update with real data
for trial_idx in batch_indices:
    ax_client.update_trial_data(trial_idx, real_data)
```

**After (proper batch conditioning):**
```python
# Generate batch - trials are automatically pending
trials_dict, _ = ax_client.get_next_trials(max_trials=batch_size)

# Run experiments
for trial_idx, params in trials_dict.items():
    results = run_experiment(**params)
    ax_client.complete_trial(trial_index=trial_idx, raw_data=results)
```

## Conclusion

The key question to answer is: **What is the purpose of `update_results.ipynb` in your workflow?**

1. **If it's for batch conditioning during optimization:**
   - Migrate to `get_next_trials()` 
   - Remove manual fantasy updates
   - See `batch_conditioning_example.ipynb` for full example

2. **If it's for correcting data post-hoc:**
   - Current approach with `update_trial_data()` is correct
   - Consider if workflow can be improved to avoid corrections
   - Document why corrections are needed

## Additional Resources

- [BATCH_CONDITIONING_GUIDE.md](BATCH_CONDITIONING_GUIDE.md) - Comprehensive batch conditioning guide
- [batch_conditioning_example.ipynb](batch_conditioning_example.ipynb) - Working example
- [Ax Documentation on Batch Trials](https://ax.dev/tutorials/gpei_hartmann_service.html)
- [Ax GitHub - get_next_trials source](https://github.com/facebook/Ax/blob/main/ax/service/ax_client.py)
