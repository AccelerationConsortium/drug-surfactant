# Batch Conditioning in Ax: Best Practices Guide

## Overview

Batch conditioning (also known as "pending observations" or "fantasy modeling") refers to the practice of informing the Bayesian optimization model about trials that have been generated but not yet completed. This allows the model to account for in-flight experiments when generating new candidates, preventing redundant suggestions.

## Current Implementation Issues

The current implementation in `experiments/20250917_closed_loop/update_results.ipynb` (from the `fully_automated_workflow` branch) manually updates trial data using `update_trial_data` to add fantasy points. While this works, it's not the recommended approach in Ax v1.

### Problems with Manual Fantasy Point Updates:
1. **Manual tracking required**: You need to manually track which trials need fantasy data
2. **Error-prone**: Easy to forget updating fantasy data or to update it incorrectly
3. **Not idiomatic**: Ax has built-in mechanisms for handling this automatically

## Recommended Approaches in Ax v1

### Approach 1: Use `get_next_trials` (Recommended for Batch Generation)

The `get_next_trials` method is the **recommended approach** for batch Bayesian optimization. It automatically handles batch conditioning through pending observations.

#### How it Works:
- Ax internally tracks trials with status `RUNNING` or `STAGED`
- When generating new candidates, Ax automatically treats these as "pending observations"
- The model conditions on these pending points to avoid redundant suggestions

#### Example Implementation:

```python
from ax.service.ax_client import AxClient, ObjectiveProperties

# Create and configure AxClient
ax_client = AxClient()
ax_client.create_experiment(
    parameters=[...],
    objectives={...}
)

# Generate a batch of trials
batch_size = 3
trials_dict, optimization_complete = ax_client.get_next_trials(max_trials=batch_size)

# trials_dict is a dictionary: {trial_index: parameterization}
for trial_index, parameterization in trials_dict.items():
    # At this point, the trial is already created with status RUNNING
    # and will be automatically considered as a pending observation
    # for subsequent calls to get_next_trials
    
    # Run your experiment with the parameterization
    results = run_experiment(**parameterization)
    
    # Complete the trial when results are available
    ax_client.complete_trial(trial_index=trial_index, raw_data=results)
```

#### Key Advantages:
- ✅ Automatic batch conditioning - no manual intervention needed
- ✅ Handles parallelism limits from GenerationStrategy
- ✅ Returns optimization status
- ✅ Clean, idiomatic Ax code

### Approach 2: Use `get_next_trial` with Automatic Pending Observations

If you prefer to generate trials one at a time (e.g., for sequential workflows with some parallelism), `get_next_trial` also automatically handles pending observations.

#### Example Implementation:

```python
# Generate first trial
params_1, trial_idx_1 = ax_client.get_next_trial()
# Trial is now RUNNING, will be treated as pending observation

# Generate second trial - automatically conditions on trial_idx_1 being pending
params_2, trial_idx_2 = ax_client.get_next_trial()

# Generate third trial - automatically conditions on both previous trials being pending  
params_3, trial_idx_3 = ax_client.get_next_trial()

# Complete trials as results become available (can be in any order)
ax_client.complete_trial(trial_index=trial_idx_1, raw_data=results_1)
ax_client.complete_trial(trial_index=trial_idx_2, raw_data=results_2)
ax_client.complete_trial(trial_index=trial_idx_3, raw_data=results_3)
```

#### Key Advantages:
- ✅ Automatic batch conditioning
- ✅ More flexible for sequential workflows
- ✅ Can complete trials in any order

## Migration Guide

### Migrating from Manual Fantasy Point Updates

If you're currently using a workflow similar to `update_results.ipynb` that manually updates trial data:

**Old Approach (Not Recommended):**
```python
# Manually create trials and update with fantasy data
for i in range(batch_size):
    params, trial_idx = ax_client.get_next_trial()
    # Mark trial as having some fantasy outcome
    ax_client.update_trial_data(
        trial_index=trial_idx,
        raw_data={"metric": fantasy_value}
    )
```

**New Approach (Recommended):**
```python
# Simply generate trials - they're automatically pending
trials_dict, _ = ax_client.get_next_trials(max_trials=batch_size)

# Trials are now in RUNNING state and treated as pending observations
# No need to manually update with fantasy data!

# Complete trials when real data is available
for trial_idx, params in trials_dict.items():
    results = run_experiment(**params)
    ax_client.complete_trial(trial_index=trial_idx, raw_data=results)
```

## Understanding Trial States

Ax automatically considers trials as "pending observations" based on their status:

- **CANDIDATE**: Trial created but not yet deployed
- **RUNNING**: Trial is running (automatically treated as pending)
- **STAGED**: Trial is staged for execution (automatically treated as pending)  
- **COMPLETED**: Trial has finished with data
- **FAILED**: Trial failed
- **ABANDONED**: Trial was abandoned

The method `get_pending_observation_features_based_on_trial_status` (used internally) extracts pending points based on trial status.

## GenerationStrategy Considerations

### Parallelism Limits

The `GenerationStrategy` can specify parallelism limits for each generation step:

```python
from ax.modelbridge.generation_strategy import GenerationStrategy, GenerationStep
from ax.modelbridge.factory import Generators

gs = GenerationStrategy(
    steps=[
        GenerationStep(
            model=Generators.SOBOL,
            num_trials=5,
            max_parallelism=3,  # Run up to 3 Sobol trials in parallel
        ),
        GenerationStep(
            model=Generators.BOTORCH_MODULAR,
            num_trials=-1,
            max_parallelism=2,  # Run up to 2 BO trials in parallel
        ),
    ]
)

ax_client = AxClient(generation_strategy=gs)
```

When using `get_next_trials`, Ax respects these limits automatically.

### Checking Generation Limits

You can check how many trials can currently be generated:

```python
num_trials, is_complete = ax_client.get_current_trial_generation_limit()

if is_complete:
    print("Optimization is complete!")
elif num_trials == -1:
    print("Can generate unlimited trials")
else:
    print(f"Can generate {num_trials} more trials")
```

## Best Practices Summary

1. **Use `get_next_trials` for batch generation** - This is the idiomatic Ax way
2. **Let Ax manage trial states** - Don't manually update trial data unless you have actual results
3. **Complete trials when data is available** - Use `complete_trial` to add real experimental data
4. **Configure parallelism in GenerationStrategy** - Set appropriate limits for your use case
5. **Check generation limits** - Use `get_current_trial_generation_limit` to understand optimization status

## References

- [Ax Service API Documentation](https://ax.dev/api/service.html#ax.service.ax_client.AxClient)
- [Generation Strategy Documentation](https://ax.dev/tutorials/generation_strategy.html)
- [Batch Trial Example](https://ax.dev/tutorials/gpei_hartmann_service.html)

## Questions?

If you have questions about batch conditioning or need help migrating your code, please:
1. Check the [Ax documentation](https://ax.dev/docs/bayesopt.html)
2. Look at [Ax tutorials](https://ax.dev/tutorials/)
3. Open an issue on the [Ax GitHub repo](https://github.com/facebook/Ax)
