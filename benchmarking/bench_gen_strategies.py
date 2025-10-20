import utils
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.modelbridge.factory import Generators
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
from botorch.acquisition import LogExpectedImprovement

from ax.service.utils.best_point import get_trace

import matplotlib.pyplot as plt

utils.set_seeds(0)  # setting the random seed for reproducibility

seed_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
obj1_name = 'ackley'

models_list = [Generators.SAASBO, Generators.BO_MIXED, Generators.BOTORCH_MODULAR] # BO_MIXED is new name for GPEI in Ax 1.0.0

traces = []
for model in models_list:
    traces.append(np.zeros((len(seed_list), 20)))

for j, seed in enumerate(seed_list):
    for i, model in enumerate(models_list):
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
                    model_kwargs={"botorch_acqf_class": LogExpectedImprovement} if model == Generators.BOTORCH_MODULAR else {},
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

            results = utils.ackley(x1, x2)
            ax_client.complete_trial(trial_index=trial_index, raw_data=results)

        traces[i][seed, :] = get_trace(ax_client._experiment)
        print(traces[i][seed, :], "for model:", i, "seed:", seed)
    
    # plot for each seed
    objective = 'ackley'
    
    fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

    for trace, name in zip([trace for trace in traces], ["SAASBO", "GPEI", "BOTORCH_MODULAR"]):

        color = '#0033FF' if name == "SAASBO" else '#FF3300'
        color = '#00FF33' if name == "BOTORCH_MODULAR" else color

        ax.plot(trace[j], color=color, label=f"{name} Trace")
        print(j, trace[j])
        print(seed, trace[seed])

    ax.axvline(3, color='black', linestyle='--') # mark end of SOBOL trials

    ax.set_xlabel("Trial Number")
    ax.set_ylabel(objective)
    ax.legend()
    plt.savefig("benchmarking/gen_strategy_bench_seed{}.png".format(seed), dpi=150)


# plot everything together
objective = 'ackley'

fig, ax = plt.subplots(figsize=(6, 4), dpi=150)

for trace, name in zip([trace for trace in traces], ["SAASBO", "GPEI", "BOTORCH_MODULAR"]):

    mean = np.mean(trace, axis=0)
    std = np.std(trace, axis=0)

    color = '#0033FF' if name == "SAASBO" else '#FF3300'
    color = '#00FF33' if name == "BOTORCH_MODULAR" else color

    ax.plot(mean, color=color, label=f"{name} Mean")
    ax.fill_between(
        range(len(mean)), mean - std, mean + std,
        color=color, alpha=0.3, label=f"{name} Std Dev"
    )

ax.axvline(3, color='black', linestyle='--') # mark end of SOBOL trials

ax.set_xlabel("Trial Number")
ax.set_ylabel(objective)
ax.legend()
plt.savefig("benchmarking/gen_strategy_bench_mean_and_std.png", dpi=150)