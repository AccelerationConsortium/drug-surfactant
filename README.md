# Drug-Surfactant Nanoformulation Optimizer

An automated self-driving laboratory (SDL) for discovering surfactants that solubilize poorly water-soluble drugs using the minimum possible surfactant volume. A Bayesian optimization (BO) loop proposes formulations, an Opentrons Flex robot physically prepares them, and an Absorbance Reader Module measures drug solubilization — all without human intervention.

## Overview

Poorly water-soluble drugs often require surfactant excipients to form stable "solutions". This system searches for the optimal two-surfactant combination and their volumes that keeps a drug dissolved while minimizing total surfactant use. 
Case study drugs: **Ibuprofen (IBP)**, **Lovastatin (LOV)**, **Diclofenac (DCF)**, and **Griseofulvin (GLV)**.

Each iteration of the loop:
1. Uses prior results to fit a Gaussian process surrogate (via [Ax](https://ax.dev/) / [BoTorch](https://botorch.org/))
2. Proposes new candidate formulations and registers them as trials
3. Auto-generates an Opentrons Flex protocol and uploads it to the robot
4. Waits for the robot to prepare, mix, dissolve, and read absorbance
5. Downloads results, evaluates success, and updates the optimizer

## Documentation

| Document | Contents |
|---|---|
| This README | Installation, example workflows, parameters, data layout |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Software architecture, closed-loop data-flow diagram, optimisation problem definition, robot deck layout, file formats |
| [docs/API.md](docs/API.md) | Function-level API reference for every module, including all configuration variables |

## Installation

Tested on macOS with Python 3.10.16. The BO loop, smoke test, and data analysis also run on Linux and Windows. Only `Click_Me_to_Run.command` is macOS-specific.

```bash
git clone https://github.com/AccelerationConsortium/drug-surfactant.git
cd drug-surfactant

# Option A (recommended): conda
conda env create -f environment.yml
conda activate drug-surfactant

# Option B: pip / venv (Python 3.10)
python3.10 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

All dependency versions are pinned in [requirements.txt](requirements.txt). [environment.yml](environment.yml) wraps the same list and adds Python 3.10.16 and Tk (for the GUI). The `opentrons` package is **not** needed on the host, because generated protocols run on the robot itself.

Check the installation by running the smoke test ([Workflow 2](#workflow-2--run-the-closed-loop-without-a-robot-smoke-test)).

## Example Workflows

### Workflow 1 — Reproduce the published analysis and figures from the included data

No robot is needed. The raw data and the complete optimizer state for all four case studies are already in the repository.

```bash
conda activate drug-surfactant
cd data_analysis
# open data_analysis.ipynb in VS Code (Jupyter extension) or any Jupyter front end and "Run All"
# (for the classic browser UI: pip install notebook && jupyter notebook data_analysis.ipynb)
```

The notebook reloads the final Ax state of each case study (`<folder>/optimizer/optimizer_10_loaded.json`), rebuilds the per-trial tables, and regenerates every figure in `data_analysis/figures/`:
- `drug_properties.png`
- `<DRUG>_optimization_trace.png`
- `model_analysis_<DRUG>.png`

A full run takes a few minutes on a laptop. Most of the time is spent on GP refitting and SHAP.

### Workflow 2 — Run the closed loop without a robot (smoke test)

This runs the complete software pipeline with the robot calls mocked: candidate generation, GP fitting, acquisition, protocol generation, absorbance processing, and Ax updates.

- **GUI:** run `python governing_files/launcher_ui.py`, tick **Smoke Test**, and click **LAUNCH EXPERIMENT**.
- **Command line:** set the parameters as environment variables. Every parameter must be set; see [docs/API.md](docs/API.md#configuration-environment-variables).

```bash
SMOKE_TEST=1 NUM_ITERATIONS=3 TRIALS_PER_ITERATION=3 NUM_RANDOM_TRIALS=9 REPLICATES=2 \
ABSORBANCE_THRESHOLD=0.06 SURFACTANT_VOL_REDUCTION=10 DRUG_CHOICES=IBP \
PUNISHMENT_FACTOR=1 DELAY_TIME=60 GREEDY_HIGH=1 GREEDY_MEDIUM=1 GREEDY_LOW=1 \
python governing_files/drug_surfactant_bo.py
```

Output is written to `smoketest_output/`, using the same layout as a real experiment folder with a `_smoketest` suffix. Each BO iteration takes about 1 minute on a laptop.

> The repository ships a completed smoke-test run in `smoketest_output/`, and the script **resumes** from any existing state. To start a fresh smoke test, move or delete that folder first (for example `mv smoketest_output smoketest_output_old`).

### Workflow 3 — Run a real experiment on the Opentrons Flex

1. Set up the deck as listed in [docs/ARCHITECTURE.md §4](docs/ARCHITECTURE.md#4-robot-deck-layout-from-protocol_templatepy), with full tip racks, stock solutions, and empty plates.
2. Connect the host to the robot (Ethernet by default). Set `OPENTRONS_BASE_URL` if the address differs.
3. Create an experiment folder from the template, for example `cp -r experiments_template 2026-10-01`.
4. Start the GUI: `Click_Me_to_Run.command` on macOS, or `python governing_files/launcher_ui.py` elsewhere. Enter the folder name and parameters, then click **LAUNCH EXPERIMENT**. The settings used for the four case studies are saved in each case study's `experiment_parameters.csv`; see [Data Availability](#data-availability-and-experiment-folders).
5. After each iteration all state is saved, so an interrupted run can be resumed (see [Resuming a Run](#resuming-a-run)).

## Repository Structure

```
governing_files/         # Core scripts and labware definitions
    launcher_ui.py           # Tkinter GUI — configure and launch experiments
    drug_surfactant_bo.py    # Main BO orchestration loop
    helper_functions.py      # Volume calculations, absorbance processing, utilities
    protocol_template.py     # Opentrons Flex protocol template (filled per iteration)
    opentrons_http_client.py # Low-level Opentrons HTTP API client
    opentrons_http_otflex_iA_mwe.py  # Upload, run, and poll a protocol on the robot
    allenlab_8_wellplate_20000ul.json         # Custom 8-well stock plate labware
    corning_96_wellplate_360ul_flat_new.json  # Custom 96-well plate labware

Click_Me_to_Run.command  # macOS launcher (activates conda env, opens GUI)
environment.yml          # Conda environment (Python 3.10.16 + requirements.txt)
requirements.txt         # Pinned Python dependencies
docs/                    # Architecture and API documentation

experiments_template/    # Template folder structure for new experiment dates
smoketest_output/        # Output folder for smoke test (no-robot) runs
2026-02-19/ … 2026-02-26/  # Case-study experiments (see Data Availability below)
data_analysis/
    data_analysis.ipynb  # Notebook for post-hoc analysis and visualization
    data_analysis_helper.py # Helper functions for post-hoc analysis and visualization
    figures/             # Figures generated by the notebook
```

## Data Availability and Experiment Folders

| Folder | Drug | Content | Used in `data_analysis/` |
|---|---|---|---|
| `2026-02-19/` | Ibuprofen (IBP) | Case study: 9 random + 10 BO iterations × 3 trials | yes |
| `2026-02-20/` | Lovastatin (LOV) | Case study: same settings | yes |
| `2026-02-23/` | Diclofenac (DCF) | Case study: same settings | yes |
| `2026-02-26/` | Griseofulvin (GLV) | Case study: same settings | yes |
| `2026-03-20 (Random IBP)/` | IBP | Random-sampling baseline (39 random trials) + DLS results | no |
| `2026-09-17 (39_Random -2)/` | LOV | Random-sampling baseline (39 random trials) | no |
| `experiment_refine_testing/` | LOV | Hardware/protocol test run | no |
| `smoketest_output/` | IBP | Example smoke-test output (synthetic absorbance) | no |

The exact settings of each run are recorded in its `experiment_parameters.csv`. The `optimizer/optimizer_N_loaded.json` files contain the full Ax experiment, including all trials, parameters, and measured outcomes, and can be loaded with `AxClient.load_from_json_file(...)`.

Each dated experiment folder contains:

```
YYYY-MM-DD/
    experiment_parameters.csv   # Logged copy of all run configuration
    tip_positions.json          # Tip state (for resuming mid-experiment)
    well_positions.json         # Plate/deep-well state (for resuming)
    optimizer/
        design_iN.csv           # Proposed formulations for iteration N
        optimizer_N.json        # Ax state before iteration N
        optimizer_N_loaded.json # Ax state after completing iteration N
    protocols/
        otflex_iN.py            # Auto-generated robot protocol for iteration N
    raw_data/
        raw_absorbance_iN.csv   # 8×12 absorbance plate reading from robot
    results/
        viewer_results_iN_*.csv # Full per-trial results with volumes and outcomes
```

## Hardware Requirements

| Hardware | Purpose |
|---|---|
| Opentrons Flex robot | Liquid handling (pipetting, gripper for plate moves) |
| Flex 1-channel 1000 µL pipette | Dispensing surfactants and water (> 40 µL) |
| Flex 1-channel 50 µL pipette | Dispensing drugs and small volumes (≤ 40 µL) |
| Flex 96-filter tip racks (1000 µL ×2, 50 µL ×1) | Disposable tips |
| Heater-Shaker Module V1 | Mixing formulations in the deep-well plate |
| Absorbance Reader Module V1 | Measuring turbidity at 600 nm |
| 8-well plate (20 mL) ×2 | Stock solutions: 8 surfactants + 4 drugs |
| Agilent 1-well reservoir (290 mL) | Water |
| Corning 96-well flat plate (360 µL) ×2 | Experimental plate + deep-well plate on heater-shaker |
| Host computer (tested on macOS) | Running BO, GUI, and robot communication |

The host connects to the robot over **Ethernet** at `http://169.254.40.153:31950` (default) or WiFi at `http://192.168.0.5:31950`. Override via the `OPENTRONS_BASE_URL` environment variable.

## Software Requirements

See [Installation](#installation) for setup; exact versions are pinned in `requirements.txt`. Key packages:

| Package | Purpose |
|---|---|
| `ax-platform` | Bayesian optimization service layer |
| `botorch` | Gaussian process surrogate + acquisition functions |
| `torch` | Required by BoTorch |
| `pandas` | CSV handling for designs and results |
| `numpy` | Numerical computations |
| `requests` | HTTP communication with Opentrons Flex API |
| `tkinter` | GUI launcher (standard library) |
| `rdkit`, `shap`, `matplotlib` | Post-hoc analysis and figures (`data_analysis/`) |


## Usage

### GUI (recommended)

Double-click `Click_Me_to_Run.command` on macOS. This activates the `drug-surfactant` conda environment and opens the configuration GUI.

In the GUI:
- Set the experiment folder name (e.g., today's date)
- Configure starting tip and well positions (for resuming a run)
- Set all optimization parameters (see below)
- Click **LAUNCH EXPERIMENT**

Live console output is streamed directly in the GUI window.


## Key Parameters

| Parameter | Default | Description |
|---|---|---|
| `NUM_ITERATIONS` | 10 | Total BO iterations |
| `TRIALS_PER_ITERATION` | 3 | New formulations tested per iteration (iter 1+) |
| `NUM_RANDOM_TRIALS` | 9 | Random seed formulations in iteration 0 |
| `REPLICATES` | 2 | Replicate wells per formulation on the plate |
| `ABSORBANCE_THRESHOLD` | 0.06 | AU at 600 nm — below this = formulation is clear |
| `SURFACTANT_VOL_REDUCTION` | 10 | % reduction applied to best known volume each iteration |
| `DRUG_CHOICES` | IBP | Comma-separated drugs to study (IBP, LOV, DCF, GLV) |
| `PUNISHMENT_FACTOR` | 1 | Volume multiplier reported to Ax for failed (cloudy) trials |
| `DELAY_TIME` | 60 | Minutes to wait between mixing and absorbance reading |
| `GREEDY_HIGH` | 4 | First N iterations — high-diversity candidate selection |
| `GREEDY_MEDIUM` | 4 | Next N iterations — medium-diversity selection |
| `GREEDY_LOW` | 2 | Final N iterations — low-diversity (fully greedy) selection |

These are the environment-variable names read by `drug_surfactant_bo.py` (the GUI sets them for you). In `experiment_parameters.csv` the greedy settings are logged as `GREEDY_*_ITERS`. The full list, including tip/well start positions, is in [docs/API.md](docs/API.md#configuration-environment-variables).

## Smoke Test (No Robot)

Check **Smoke Test** in the GUI (or set `SMOKE_TEST=1`) to run a full dry-run without a physical robot. Robot calls are mocked and synthetic absorbance values are generated deterministically, enabling complete pipeline testing on any laptop.

Output is written to `smoketest_output/`. For a command-line example, see [Workflow 2](#workflow-2--run-the-closed-loop-without-a-robot-smoke-test).

## Resuming a Run

The system saves tip positions, well positions, and optimizer state after every iteration. To resume a partially completed experiment, set the experiment folder to the existing dated folder and specify the correct starting tip rack and plate positions in the GUI. The optimizer will automatically reload from the latest `optimizer_N_loaded.json` checkpoint.

## How the BO Loop Works

```
Iteration 0
  └── Random sampling: NUM_RANDOM_TRIALS candidates chosen at random
        └── Register trials → generate protocol → run robot → process absorbance → update Ax

Iteration 1+
  └── Fit GP surrogate on all completed trials
        └── Evaluate acquisition function over all feasible (s_i, s_j, volume) candidates
              └── Select TRIALS_PER_ITERATION diverse candidates (greedy diversity filter)
                    └── Tighten volume budget by SURFACTANT_VOL_REDUCTION% of best-so-far
                          └── Register trials → generate protocol → run robot → process absorbance → update Ax
```

The objective is to **minimize total surfactant volume** subject to the formulation being optically clear. Successful formulations report their actual volume; failed formulations are penalized by `PUNISHMENT_FACTOR`.

## License

See [LICENSE](LICENSE).
