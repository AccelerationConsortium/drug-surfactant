# drug-surfactant

Bayesian optimization workflow for drug-surfactant formulation using Ax.

## Features

- Multi-objective optimization (complexity, cost, performance)
- Robust error handling for failed experiments
- Automatic detection of infeasible parameter combinations
- Integration with Opentrons liquid handling robots

## New: Failed Experiment Handling

When Ax suggests parameter combinations that are physically infeasible (e.g., concentrations too high for available stock solutions), the workflow now gracefully handles these failures:

```python
import helper_functions as hf

# Initialize optimizer
ax_client = hf.optimizer_init()

# Run optimization with automatic failure handling
for trial_index, parameterization in parameterizations.items():
    success = hf.safe_complete_trial(
        ax_client=ax_client,
        trial_index=trial_index,
        parameterization=parameterization
    )
```

**Benefits:**
- No crashes on invalid parameters
- Failed trials are properly marked in Ax
- Optimizer learns to avoid problematic regions
- Workflow continues despite failures

See [FAILED_EXPERIMENT_HANDLING.md](FAILED_EXPERIMENT_HANDLING.md) for detailed documentation and [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for updating existing workflows.

**Quick Demo:** Run `python demo_failed_trials.py` to see the feature in action.

## Installation

```bash
pip install ax-platform
```

## Usage

See [example_safe_trials.py](example_safe_trials.py) for a complete example.