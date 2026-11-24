# API Reference

This page gives a function-level reference for every module in the repository. For how the modules interact, see [ARCHITECTURE.md](ARCHITECTURE.md). Volumes are in µL unless stated otherwise, and wells use the plate notation `A1`…`H12`.

- [`governing_files/drug_surfactant_bo.py`](#governing_filesdrug_surfactant_bopy): main BO loop (script)
- [`governing_files/helper_functions.py`](#governing_fileshelper_functionspy): volumes, absorbance, wells
- [`governing_files/protocol_template.py`](#governing_filesprotocol_templatepy): robot protocol template
- [`governing_files/opentrons_http_client.py`](#governing_filesopentrons_http_clientpy): Opentrons HTTP API wrappers
- [`governing_files/opentrons_http_otflex_iA_mwe.py`](#governing_filesopentrons_http_otflex_ia_mwepy): run a protocol end-to-end
- [`governing_files/launcher_ui.py`](#governing_fileslauncher_uipy): GUI
- [`data_analysis/data_analysis_helper.py`](#data_analysisdata_analysis_helperpy): post-hoc analysis and figures

---

## `governing_files/drug_surfactant_bo.py`

This is an executable script, not an importable library. It runs `NUM_ITERATIONS` closed-loop iterations, starting from the first iteration without raw data in the selected experiment folder.

```bash
python governing_files/drug_surfactant_bo.py
```

### Configuration (environment variables)

The launcher GUI sets these automatically. When running from the command line, every variable marked *required* must be set, because the script does not provide defaults for them.

| Variable | Required | GUI default | Meaning |
|---|---|---|---|
| `SMOKE_TEST` | no | `0` | `1`/`true` mocks the robot and writes to `smoketest_output/` |
| `EXP_FOLDER_NAME` | real runs | — | Experiment folder name, relative to the repo root. The script prompts for it if unset. |
| `OPENTRONS_BASE_URL` | no | `http://169.254.40.153:31950` | Robot HTTP address |
| `NUM_ITERATIONS` | yes | `10` | Iterations to run in this call |
| `TRIALS_PER_ITERATION` | yes | `3` | Trials selected per BO iteration (n ≥ 1) |
| `NUM_RANDOM_TRIALS` | yes | `9` | Random trials in iteration 0 |
| `REPLICATES` | yes | `2` | Replicate wells per trial |
| `ABSORBANCE_THRESHOLD` | yes | `0.06` | A600 at or below this value counts as a clear formulation (success) |
| `SURFACTANT_VOL_REDUCTION` | yes | `10` | % by which the best-so-far volume is reduced to set the next budget |
| `DRUG_CHOICES` | yes | `IBP` | Comma-separated list, cycled over iterations (`IBP`, `LOV`, `DCF`, `GLV`) |
| `PUNISHMENT_FACTOR` | yes | `1` | Multiplier on total volume reported for failed trials |
| `DELAY_TIME` | yes | `60` | Minutes between mixing and absorbance reading (in the robot protocol) |
| `GREEDY_HIGH` / `GREEDY_MEDIUM` / `GREEDY_LOW` | yes | `4` / `4` / `2` | Number of iterations using the high / medium / low diversity selection rule |
| `START_PLATE_WELL`, `START_DEEP_WELL` | real runs | last saved | First free well on the read-out / mixing plate. The script prompts for it if unset; an empty value keeps the saved position. |
| `TIP_RACK_ID`, `TIP_WELL_1000`, `TIP_WELL_50` | real runs | `0`, `A1`, `A1` | First unused tips. The script prompts for them if unset; an empty value keeps the saved position. |

### Internal functions

| Function | Description |
|---|---|
| `determine_current_iteration()` → `int` | Returns the number of existing `raw_data/raw_absorbance_i*.csv` files, i.e. the index of the next iteration. |
| `run_otflex_iA`, `get_run_details`, `download_data_file` | Robot I/O. In smoke-test mode they are replaced by local mocks; the mock absorbance is a deterministic function of the surfactant volumes. |

---

## `governing_files/helper_functions.py`

### Module constants

| Name | Value | Meaning |
|---|---|---|
| `drug_stock_conc` | `25` | Drug stock concentration |
| `surfactant_stock_conc` | `100` | Nominal surfactant stock concentration |
| `actual_surfactant_stock_conc` | `50` | Surfactant stock concentration used in practice |
| `drug_total_volume` | `0.18` (mL) | Drug + DMSO volume per formulation (180 µL) |
| `surfactant_total_volume` | `1.2` (mL) | Surfactant + water volume per formulation (1200 µL); upper bound of the search space |
| `number_of_surfactants` | `8` | Number of surfactant stocks `s1`…`s8` |
| `normalize_drug_properties_dict` | dict | Drug abbreviation → `{full_name, normalized_properties, drug_stock_conc}`. `normalized_properties` is empty, so drug descriptors are **not** used as model inputs. |

### Functions

**`design_to_vol(iteration, design_file_path, drug_stock_conc=25, drug_total_volume=0.18, surfactant_stock_conc=100, surfactant_total_volume=1.2)`** → `(df_design, df_vol)`

Reads `f"{design_file_path}i{iteration}.csv"` and converts it into per-trial pipetting volumes. `df_vol` has columns `trial_index, drug_name, s1…s8, IBP, LOV, DCF, GLV, dmso, water`:
- The selected drug gets 180 µL.
- `dmso = 180 − drug`.
- `water = 1200 − Σ s_i`.

Returns `(None, None)` if the CSV cannot be parsed, and raises `FileNotFoundError` if it does not exist.

**`process_absorbance(raw_data_file_path, trials_data, replicates=3, threshold=0.06)`** → `DataFrame`

Parses the 8 × 12 absorbance CSV exported by the Absorbance Reader. `trials_data` is a list of dicts, each with a `well_slot` key (the first replicate well). For each trial it reads `replicates` consecutive wells. It returns the columns `well_slot`, `absorbance` (mean of the replicates) and `success` (`1` only if every replicate is below `threshold`). A missing well counts as `0.0` and triggers a warning.

**`build_results(iteration, df_absorbance, design_file_path)`** → `DataFrame`

Merges `design_iN.csv` with the output of `process_absorbance` on `well_slot`. It adds `vol_actual` and `vol_with_penalty` (the actual volume if successful, 1200 µL otherwise).

**`add_drug_names(df)`** → `DataFrame`

If `df` has a `drug` column, adds the columns `drug_name` (the abbreviation) and `drug_full` (the full name).

**`get_next_well(starting_well, offset=1)`** → `str`

Returns the well `offset` positions after `starting_well` in row-major order (A1, A2, …, A12, B1, …). Raises `ValueError` if the input is malformed or the plate is exhausted (past H12).

**`ax_trial_status_dataframe(ax_client)`** → `DataFrame`

Returns one row per Ax trial, with the columns `trial_index`, `status` and `plate_num`.

---

## `governing_files/protocol_template.py`

This is an Opentrons Python API (apiLevel 2.27, robotType Flex) protocol written as a Python `str.format` template. Literal braces are doubled (`{{ }}`). The BO script fills the following placeholders:

| Placeholder | Filled with |
|---|---|
| `{ITERATION}` | iteration index `n` |
| `{DATA_JSON}` | JSON list of per-trial volume dicts (the `df_vol` rows plus `next_plate_well`, `next_deepplate_well`, `replicates`) |
| `{RACK_ID_1000}`, `{WELL_1000}`, `{WELL_50}` | starting tips |
| `{START_PLATE_WELL}`, `{START_DEEP_WELL}` | starting wells |
| `{REPLICATES}` | replicate wells per trial |
| `{DELAY_TIME}` | minutes to wait before reading |
| `{WATER_WELL}` | water source well (rotated every 4 iterations) |

The rendered protocol runs in five phases:

1. For each trial, dispense the surfactant(s) and water into one deep well, and the drug into the next deep well. Volumes of 40 µL or less use the 50 µL pipette; larger volumes use the 1000 µL pipette.
2. Shake the deep-well plate (1000 rpm, 1 min).
3. For each replicate, transfer 270 µL of the surfactant mix and 30 µL of the drug solution to the read-out plate.
4. Shake the read-out plate and wait `DELAY_TIME` minutes.
5. Read A600 with the Absorbance Reader. The reading is exported as `raw_absorbance_i{ITERATION}`.

The helper functions inside `run()` are:
- `next_well`
- `pipette_selection(vol)`
- `plate_on_hs`, `plate_on_hs_to_reader`, `plate_on_pr`: labware moves, shaking and reading
- `make_drug_or_surfactant`
- `make_exp`

---

## `governing_files/opentrons_http_client.py`

Every function takes `base_url` (for example `http://169.254.40.153:31950`) and sends the header `opentrons-version: 4`. HTTP errors raise `requests.HTTPError`. Functions return the parsed JSON response unless noted otherwise.

| Function | HTTP call | Notes |
|---|---|---|
| `get_health(base_url)` | `GET /health` | Connectivity check |
| `upload_protocol(base_url, protocol_file_path, labware_paths=None)` | `POST /protocols` | Uploads the protocol together with custom labware JSON files |
| `get_protocol(base_url, protocol_id)` | `GET /protocols/{id}` | |
| `get_protocol_analyses(base_url, protocol_id)` | `GET /protocols/{id}/analyses` | |
| `get_protocol_analysis_document(base_url, protocol_id, analysis_id)` | `GET …/analyses/{id}/asDocument` | Returns JSON if possible, otherwise text |
| `wait_for_analysis_completion(base_url, protocol_id, analysis_id, poll_interval=5)` | polling | Returns the analysis dict; raises `ValueError` if the analysis fails |
| `create_run(base_url, protocol_id, run_time_parameters)` | `POST /runs` | Raises `ValueError` on failure |
| `start_run(base_url, run_id)` | `POST /runs/{id}/actions` (`play`) | |
| `get_runs(base_url)` / `get_run_details(base_url, run_id)` | `GET /runs`, `GET /runs/{id}` | `get_run_details(...)["data"]["outputFileIds"]` lists the absorbance files |
| `get_run_commands(base_url, run_id)` | `GET /runs/{id}/commands` | |
| `wait_for_run_completion(base_url, run_id, poll_interval=5)` | polling | Streams commands to stdout; returns the final status (`succeeded` / `failed` / `stopped`) |
| `get_data_files(base_url)` / `get_data_file_info(base_url, data_file_id)` | `GET /dataFiles[/{id}]` | |
| `download_data_file(base_url, data_file_id, save_path)` | `GET /dataFiles/{id}/download` | Writes the file to `save_path` and returns the path |
| `get_log(base_url, log_identifier)` | `GET /logs/{id}` | Returns text |
| `run_protocol(base_url, protocol_path, run_time_parameters, labware_paths=None)` | combined | Generic upload → analyse → run helper (not used by the BO loop) |

## `governing_files/opentrons_http_otflex_iA_mwe.py`

**`run_otflex_iA(protocol_file_path)`** → `run_id: str`

Uploads the protocol together with the two custom labware definitions in `governing_files/`. It then waits for the protocol analysis, creates and starts a run, blocks until the run finishes, and returns the run ID. The robot address comes from `OPENTRONS_BASE_URL`.

## `governing_files/launcher_ui.py`

`python governing_files/launcher_ui.py` opens a Tkinter window with the following fields:
- smoke-test toggle
- experiment folder name
- start wells and tips
- all run parameters listed [above](#configuration-environment-variables)

**LAUNCH EXPERIMENT** exports the fields as environment variables and runs `drug_surfactant_bo.py` in a subprocess, streaming its output into the window.

---

## `data_analysis/data_analysis_helper.py`

Import this module from inside `data_analysis/`, because it loads data through relative paths (`../<experiment folder>/…`). Figures are written to `data_analysis/figures/`.

### Module data

| Name | Meaning |
|---|---|
| `exp_dict` | Drug → `{experiment_folder, iteration}`: which experiment folder and which final `optimizer_<iteration>_loaded.json` are analysed (the case studies `2026-02-19`, `2026-02-20`, `2026-02-23` and `2026-02-26`) |
| `drug_dict` | Drug → full name, CAS number, SMILES |
| `surfactant_dict` | `s1`…`s8` → abbreviation and full name (SDS, NaC, CHAPS, DTAB, TTAB, P188, P407, SB3-12) |
| `factor` | `270 / 1200`: rescales the optimiser volumes, which refer to the 1200 µL deep-well mixture, to the 270 µL of that mixture transferred into each read-out well |

### Public functions

| Function | Output |
|---|---|
| `data_summary()` → `dict` | Loads each case study's Ax state and `experiment_parameters.csv`. For each drug it stores `results` (a trial `DataFrame` with `iteration`, `success`, surfactant-named columns and rescaled volumes), `exp_params` and `ax_client` in `exp_dict`, then returns `exp_dict`. |
| `drug_visualization(drug_dict)` | Parallel-coordinate plot of RDKit descriptors (MW, logP, HBD, HBA, TPSA, rotatable bonds) → `figures/drug_properties.png` |
| `plot_surfactant_combined(df, drug, success_only=False, transparent=False)` | Optimisation trace: surfactant composition per iteration, best-so-far volume, surfactant usage bubbles → `figures/<DRUG>_optimization_trace.png` |
| `plot_drug(drug, feat_x=None, feat_y=None)` | Refits the GP on the absorbance outcome. Produces a SHAP beeswarm and a 2-D GP response surface for the two most important surfactants (or `feat_x`/`feat_y`) → `figures/model_analysis_<DRUG>.png` |
| `plot_shap(drug)` → `ndarray` | SHAP panel only → `figures/shap_<DRUG>.png` |
| `plot_response_surface(drug, feat_x=None, feat_y=None)` | Response-surface panel only → `figures/response_surface_<DRUG>.png` |
| `add_iteration_number(df, trials_per_iteration, num_random_trials)`, `add_success_column(df, threshold)`, `replace_surfacant_names(df)` | `DataFrame` utilities used by `data_summary()` |

Functions whose names start with `_` (for example `_build_gp` and `_get_X_y`) are private helpers.
