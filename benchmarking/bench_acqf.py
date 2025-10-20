from utils import set_seeds, ackley
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.modelbridge.factory import Generators
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
from botorch.acquisition import UpperConfidenceBound, LogExpectedImprovement

from ax.service.utils.best_point import get_trace

set_seeds(0)  # setting the random seed for reproducibility

seed_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
obj1_name = 'ackley'

model = Generators.SAASBO

acqf_list = [LogExpectedImprovement, UpperConfidenceBound]

traces = []
for acqf in acqf_list:
    traces.append(np.zeros((len(seed_list), 20)))

for i, acqf in enumerate(acqf_list):
    for seed in seed_list:

        gs = GenerationStrategy(
            steps=[
                GenerationStep(
                    model=Generators.SOBOL,
                    num_trials=5,
                    min_trials_observed=3,
                    max_parallelism=5,
                    model_kwargs={"seed": seed},
                    model_gen_kwargs={},
                ),
                GenerationStep(
                    model=model,
                    num_trials=-1,
                    max_parallelism=3,
                    model_kwargs={"botorch_acqf_class": acqf},
                ),
            ]
        )

        ax_client = AxClient(generation_strategy=gs,
                                verbose_logging=False,
                                random_seed=seed)

        ax_client.create_experiment(
            parameters=[
                {"name": "x1", "type": "range", "bounds": [-32.768, 32.768]},
                {"name": "x2", "type": "range", "bounds": [-32.768, 32.768]},
                ],
            objectives={
                obj1_name: ObjectiveProperties(minimize=True),
            },
        )

        for _ in range(20):
            parameterization, trial_index = ax_client.get_next_trial()

            x1 = parameterization["x1"]
            x2 = parameterization["x2"]

            results = ackley(x1, x2)
            ax_client.complete_trial(trial_index=trial_index, raw_data=results)

        traces[i][seed, :] = get_trace(ax_client._experiment)
        print(traces[i][seed, :])
    print(traces)

import matplotlib.pyplot as plt

objective = 'ackley'

fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

for acqf, name in zip([trace for trace in traces], ["LEI", "UCB"]):

    mean = np.mean(acqf, axis=0)
    std = np.std(acqf, axis=0)

    color = '#00FF33' if name == "LEI" else '#FF3300'  # green for LEI, red for UCB

    ax.plot(mean, color=color, label=f"{name} Mean")
    ax.fill_between(
        range(len(mean)), mean - std, mean + std,
        color=color, alpha=0.3, label=f"{name} Std Dev"
    )

ax.axvline(3, color='black', linestyle='--') # mark end of SOBOL trials

ax.set_xlabel("Trial Number")
ax.set_ylabel(objective)
ax.legend()
plt.savefig("benchmarking/aqcf_bench_saasbo.png", dpi=150)