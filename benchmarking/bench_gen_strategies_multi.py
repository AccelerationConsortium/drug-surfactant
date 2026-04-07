import utils
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.modelbridge.factory import Generators
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
from botorch.acquisition import ExpectedImprovement

from ax.service.utils.best_point import get_trace

import matplotlib.pyplot as plt

import time

seed_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
obj1_name = 'f1'
obj2_name = 'f2'
obj3_name = 'f3'

models_list = [Generators.SAASBO, Generators.BO_MIXED, Generators.BOTORCH_MODULAR]

total_trials = 7

sobol_count = 5
trial_num = total_trials - sobol_count

trial_parameters = [
    {"name": "x1", "type": "range", "bounds": [-np.pi, np.pi], "value_type": "float"},
    {"name": "x2", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"},
    {"name": "x3", "type": "range", "bounds": [-np.pi, np.pi], "value_type": "float"},
    {"name": "x4", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"},
    {"name": "x5", "type": "range", "bounds": [-np.pi, np.pi], "value_type": "float"},
    {"name": "x6", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"},
    {"name": "x7", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"},
    {"name": "x8", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"},
    {"name": "x9", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"},
    {"name": "x10", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"},
    {"name": "x11", "type": "range", "bounds": [-np.pi, np.pi], "value_type": "float"},
    {"name": "x12", "type": "range", "bounds": [-np.pi, np.pi], "value_type": "float"},
    {"name": "x13", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"},
    {"name": "x14", "type": "range", "bounds": [-3.0, 3.0], "value_type": "float"}
]

trial_objectives = {
    obj1_name: ObjectiveProperties(minimize=True),
    obj2_name: ObjectiveProperties(minimize=True),
    obj3_name: ObjectiveProperties(minimize=True),
}

traces = []
for model in models_list:
    traces.append(np.zeros((len(seed_list), total_trials)))

times = []
for model in models_list:
    times.append(np.zeros((len(seed_list), total_trials)))

for j, seed in enumerate(seed_list):
    utils.set_seeds(seed)  # setting the random seed for reproducibility

    # generate same sobol trials for all models
    sobol_trials = []
    sobol_client = AxClient(
        generation_strategy=GenerationStrategy(
            steps=[
                GenerationStep(
                    model=Generators.SOBOL,
                    num_trials=sobol_count,
                    min_trials_observed=3,
                    max_parallelism=5,
                    model_kwargs={"seed": seed},
                    model_gen_kwargs={},
                ),
            ]
        ),
        verbose_logging=False,
        random_seed=seed)
    
    sobol_client.create_experiment(
        parameters=trial_parameters,
        objectives=trial_objectives,
    )

    for a in range(sobol_count):
        start_time = time.time()
        parameterization, trial_index = sobol_client.get_next_trial()
        time_taken = time.time() - start_time
        
        for mod_time in times:
            mod_time[j, a] = time_taken

        x = np.array([parameterization[f"x{i+1}"] for i in range(14)])

        results = utils.polynomial_14d(x)
        sobol_trials.append([results, parameterization])
        sobol_client.complete_trial(trial_index=trial_index, raw_data=results)

    for i, model in enumerate(models_list):
        gs = GenerationStrategy(
            steps=[
                #GenerationStep(
                #    model=Generators.SOBOL,
                #    num_trials=sobol_count,
                #    min_trials_observed=3,
                #    max_parallelism=5,
                #    model_kwargs={"seed": seed},
                #    model_gen_kwargs={},
                #),
                GenerationStep(
                    model=model,
                    num_trials=-1,
                    max_parallelism=3,
                    model_kwargs={"botorch_acqf_class": ExpectedImprovement} if model == Generators.BOTORCH_MODULAR else {},
                ),
            ]
        )

        ax_client = AxClient(generation_strategy=gs,
                                verbose_logging=False,
                                random_seed=seed)

        ax_client.create_experiment(
            parameters=trial_parameters,
            objectives=trial_objectives,
        )

        for a, (result, parameterization) in enumerate(sobol_trials):
            ax_client.attach_trial(parameters=parameterization)
            ax_client.complete_trial(trial_index=a, raw_data=result)
        traces[i][j, :sobol_count] = get_trace(ax_client._experiment)[:sobol_count]

        for a in range(trial_num):
            start_time = time.time()
            parameterization, trial_index = ax_client.get_next_trial()
            times[i][j, sobol_count + a] = time.time() - start_time

            x = np.array([parameterization[f"x{i+1}"] for i in range(14)])

            results = utils.mixed_14d(x)
            ax_client.complete_trial(trial_index=trial_index, raw_data=results)

        traces[i][j, :] = get_trace(ax_client._experiment)#[sobol_count:]
        print(traces[i][j, :], "for model:", i, "seed:", seed)
        print(times[i][j, :], "for model:", i, "seed:", seed)
    
    # plot for each seed
    objective = '14D Mixed Function Hypervolume'
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 8), dpi=150)

    for trace, duration, name in zip(traces, times, ["SAASBO", "BO_MIXED", "BOTORCH_MODULAR"]):

        color = '#0033FF' if name == "SAASBO" else '#FF3300'
        color = '#00FF33' if name == "BOTORCH_MODULAR" else color

        ax1.plot(trace[j], color=color, label=f"{name} Trace")
        print(seed, trace[j])

        ax2.plot(duration[j], color=color, label=f"{name} Duration")
        print(seed, duration[j])

    for ax in [ax1, ax2]:
        ax.axvline(sobol_count - 1, color='black', linestyle='--') # mark end of SOBOL trials
        ax.set_xlabel("Trial Number")
        ax.legend()

    ax1.set_ylabel(objective)

    ax2.set_ylabel("Time (seconds)")

    plt.tight_layout()
    plt.show()
    #plt.savefig("benchmarking/14_parameter_benches/mixed_multi/gen_strategy_bench_mixed14D_seed{}.png".format(seed), dpi=150)


# plot everything together
objective = '14D Mixed Function Hypervolume'

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 8), dpi=150)

for trace, duration, name in zip(traces, times, ["SAASBO", "BO_MIXED", "BOTORCH_MODULAR"]):

    trace_mean = np.mean(trace, axis=0)
    trace_std = np.std(trace, axis=0)

    duration_mean = np.mean(duration, axis=0)
    duration_std = np.std(duration, axis=0)

    color = '#0033FF' if name == "SAASBO" else '#FF3300'
    color = '#00FF33' if name == "BOTORCH_MODULAR" else color

    ax1.plot(trace_mean, color=color, label=f"{name} Mean")
    ax1.fill_between(
        range(len(trace_mean)), trace_mean - trace_std, trace_mean + trace_std,
        color=color, alpha=0.3, label=f"{name} Std Dev"
    )

    ax2.plot(duration_mean, color=color, label=f"{name} Duration Mean")
    ax2.fill_between(
        range(len(duration_mean)), duration_mean - duration_std, duration_mean + duration_std,
        color=color, alpha=0.3, label=f"{name} Duration Std Dev"
    )

for ax in [ax1, ax2]:
    ax.axvline(sobol_count - 1, color='black', linestyle='--') # mark end of SOBOL trials
    ax.set_xlabel("Trial Number")
    ax.legend()

ax1.set_ylabel(objective)

ax2.set_ylabel("Time (seconds)")
plt.show()
#plt.savefig("benchmarking/14_parameter_benches/mixed_multi/gen_strategy_bench_mixed14D_mean_and_std.png", dpi=150)