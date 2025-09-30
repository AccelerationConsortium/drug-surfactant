# drug-surfactant

## Batch Conditioning / Pending Observations

For information on properly implementing batch conditioning (also known as pending observations or fantasy modeling) in Ax, see:

- **[Batch Conditioning Guide](BATCH_CONDITIONING_GUIDE.md)** - Comprehensive guide on batch conditioning best practices
- **[batch_conditioning_example.ipynb](batch_conditioning_example.ipynb)** - Working example showing how to use `get_next_trials` with automatic batch conditioning

### Quick Summary

Instead of manually updating trials with fantasy data, use Ax's built-in batch conditioning:

```python
# Recommended approach
trials_dict, optimization_complete = ax_client.get_next_trials(max_trials=batch_size)

# Trials are automatically in RUNNING state and treated as pending observations
# Complete trials when data is available
for trial_idx, params in trials_dict.items():
    results = run_experiment(**params)
    ax_client.complete_trial(trial_index=trial_idx, raw_data=results)
```

See the guide for more details and migration instructions from manual fantasy point updates.