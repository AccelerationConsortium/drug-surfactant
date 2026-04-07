import utils
import numpy as np
from ax.service.ax_client import AxClient, ObjectiveProperties
from ax.modelbridge.factory import Generators
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
from botorch.acquisition import ExpectedImprovement

from ax.service.utils.best_point import get_trace

import matplotlib.pyplot as plt

import time

from api_keys import get_hf_token
from gradio_client import Client

client = Client.duplicate("AccelerationConsortium/crabnet-hyperparameter", hf_token=get_hf_token())

def ret_y(x, whichY):
    params = {f"param_{i + 5}": x[i] for i in range(15)}

    results = client.predict(
        **params,
        api_name="/predict"
    )

    return float(results['data'][0][whichY - 1])

seed_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
obj1_name = "y1"
obj2_name = "y2"
obj3_name = "y3"

models_list = [Generators.SAASBO, Generators.BO_MIXED, Generators.BOTORCH_MODULAR]

total_trials = 20

sobol_count = 5
trial_num = total_trials - sobol_count

trial_parameters = [
    {"name": f"x{i}", "type": "range", "bounds": [0.0, 1.0], "value_type": "float"}
    for i in range(6, 21) # 15 parameters so we can test with the constraints
]


trial_objectives = {
    obj1_name: ObjectiveProperties(minimize=True),
    obj2_name: ObjectiveProperties(minimize=True),
    obj3_name: ObjectiveProperties(minimize=True),
}

trial_constraints = [
    "x19 - x20 <= -0.01", # ran into ax api issues with 0.0, so using a small value
    "x6 + x15 <= 0.99", # limit less than 1.0 due to running into api issues
]

traces = []
for model in models_list:
    to_append = []
    for _ in range(len(trial_objectives)):
        to_append.append(np.zeros((len(seed_list), total_trials)))
    traces.append(to_append)

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
        parameter_constraints=trial_constraints,
    )

    for a in range(sobol_count):
        start_time = time.time()
        parameterization, trial_index = sobol_client.get_next_trial()
        time_taken = time.time() - start_time
        
        for mod_time in times:
            mod_time[j, a] = time_taken

        x = [parameterization[f"x{i}"] for i in range(6, 21)]

        results = {
            obj1_name: ret_y(x, 1),
            obj2_name: ret_y(x, 2),
            obj3_name: ret_y(x, 3)
        }

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
            parameter_constraints=trial_constraints,
        )

        for a, (result, parameterization) in enumerate(sobol_trials):
            ax_client.attach_trial(parameters=parameterization)
            ax_client.complete_trial(trial_index=a, raw_data=result)
            for b, result in enumerate(result.values()):
                traces[i][b][j][a] = result[0]
        #traces[i][j, :sobol_count] = get_trace(ax_client._experiment)[:sobol_count] may need uncomment

        for a in range(trial_num):
            start_time = time.time()
            parameterization, trial_index = ax_client.get_next_trial()
            times[i][j, sobol_count + a] = time.time() - start_time

            x = [parameterization[f"x{i}"] for i in range(6, 21)]

            results = {
                obj1_name: ret_y(x, 1),
                obj2_name: ret_y(x, 2),
                obj3_name: ret_y(x, 3)
            }
            print(results)

            ax_client.complete_trial(trial_index=trial_index, raw_data=results)
            for b, result in enumerate(results.values()):
                traces[i][b][j][sobol_count + a] = result[0]
    
    # plot for each seed
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 8), dpi=150)

    for trace, duration, name in zip(traces, times, models_list):

        color = '#0033FF' if name == Generators.BO_MIXED else "#8CFF00"
        color = '#FF0000' if name == Generators.BOTORCH_MODULAR else color

        ax1.plot(np.minimum.accumulate(trace[0][j]), color=color, label=f"{name} y1")

        ax2.plot(np.minimum.accumulate(trace[1][j]), color=color, label=f"{name} y2")

        ax3.plot(np.minimum.accumulate(trace[2][j]), color=color, label=f"{name} y3")

        print(seed, trace[0][j])

    for ax in [ax1, ax2, ax3]:
        ax.axvline(sobol_count - 1, color='black', linestyle='--') # mark end of SOBOL trials
        ax.set_xlabel("Trial Number")
        ax.legend()

    ax1.set_ylabel(obj1_name)

    ax2.set_ylabel(obj2_name)

    ax3.set_ylabel(obj3_name)

    plt.tight_layout()
    #plt.show()
    plt.savefig("benchmarking/14_parameter_benches/crabnet_3obj/crabnet14D_seed{}.png".format(seed), dpi=150)


# plot everything together

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 8), dpi=150)

for trace, duration, name in zip(traces, times, models_list):

    color = '#0033FF' if name == Generators.BO_MIXED else "#8CFF00"
    color = '#FF0000' if name == Generators.BOTORCH_MODULAR else color

    y1_mean = np.mean(np.minimum.accumulate(trace[0]), axis=1)
    y1_std = np.std(np.minimum.accumulate(trace[0]), axis=1)
    y2_mean = np.mean(np.minimum.accumulate(trace[1]), axis=1)
    y2_std = np.std(np.minimum.accumulate(trace[1]), axis=1)
    y3_mean = np.mean(np.minimum.accumulate(trace[2]), axis=1)
    y3_std = np.std(np.minimum.accumulate(trace[2]), axis=1)

    ax1.plot(y1_mean, color=color, label=f"{name} y1")
    ax1.fill_between(
        range(len(y1_mean)),
        y1_mean - y1_std,
        y1_mean + y1_std,
        color=color, alpha=0.3
    )

    ax2.plot(y2_mean, color=color, label=f"{name} y2")
    ax2.fill_between(
        range(len(y2_mean)),
        y2_mean - y2_std,
        y2_mean + y2_std,
        color=color, alpha=0.3
    )

    ax3.plot(y3_mean, color=color, label=f"{name} y3")
    ax3.fill_between(
        range(len(y3_mean)),
        y3_mean - y3_std,
        y3_mean + y3_std,
        color=color, alpha=0.3
    )

for ax in [ax1, ax2, ax3]:
    ax.axvline(sobol_count - 1, color='black', linestyle='--') # mark end of SOBOL trials
    ax.set_xlabel("Trial Number")
    ax.legend()

ax1.set_ylabel(obj1_name)

ax2.set_ylabel(obj2_name)

ax3.set_ylabel(obj3_name)

#plt.show()
plt.savefig("benchmarking/14_parameter_benches/crabnet_3obj/crabnet14D_mean_and_std.png", dpi=150)