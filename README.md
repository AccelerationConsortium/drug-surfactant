# Drug-Surfactant Closed-Loop Optimization

This repository contains a closed-loop Bayesian optimization system for drug-surfactant experiments using the Opentrons Flex robot.

## Orchestrator Usage

The `orchestrator.py` script provides automated experiment orchestration via MQTT communication between the Mac (this system) and the Opentrons Flex robot.

### Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure MQTT Connection**
   
   Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your MQTT broker credentials (from issue #30):
   ```
   MQTT_HOST=your-hivemq-instance.hivemq.cloud
   MQTT_PORT=8883
   MQTT_USERNAME=your_username
   MQTT_PASSWORD=your_password
   ```

3. **Initialize Optimizer State**
   
   Ensure you have the initial optimizer file from the closed-loop experiments:
   ```
   experiments/20250917_closed_loop/optimizer/optimizer_00.json
   ```

### Running the Orchestrator

#### Basic Usage
```bash
# Run full optimization loop for 5 iterations
python orchestrator.py --iterations 5

# Run single test iteration
python orchestrator.py --test

# Specify custom drugs to test
python orchestrator.py --drugs IBP LOV --iterations 3

# Use custom configuration
python orchestrator.py --config config/orchestrator_config.json
```

#### Command Line Options
- `--config`: Path to JSON configuration file
- `--iterations`: Number of optimization iterations to run (default: 5)  
- `--test`: Run single test iteration instead of full loop
- `--drugs`: List of drugs to optimize (default: IBP LOV DCF GLV)

### MQTT Communication

The orchestrator communicates via two MQTT topics:

- **Publish experiments**: `lab/experiments/new`
  - Sends experiment configurations for the robot to execute
  - Payload includes protocol data, experiment ID, and session information

- **Subscribe to results**: `lab/experiments/result`  
  - Receives experimental results from the robot
  - Processes absorbance data and updates optimization model

### Workflow

1. **Generate Experiments**: Uses existing Bayesian optimization from `helper_functions.py`
2. **Publish to MQTT**: Sends experiment configurations to the robot
3. **Wait for Results**: Listens for experimental results via MQTT
4. **Update Model**: Feeds results back into the optimization algorithm
5. **Iterate**: Generates next batch based on updated model

### Output

- **Logs**: `orchestrator.log` contains detailed execution logs
- **Results**: `orchestrator_results/` directory contains:
  - `iteration_N_results.json`: Raw experimental results
  - `iteration_N_results.csv`: Results in tabular format
- **Optimizer State**: Updated in `experiments/20250917_closed_loop/optimizer/`

### Troubleshooting

1. **MQTT Connection Issues**
   - Verify credentials in `.env` file
   - Check network connectivity to HiveMQ broker
   - Ensure robot is connected and listening

2. **Import Errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check that `experiments/20250917_closed_loop/` contains required files

3. **Optimization Errors**  
   - Ensure initial optimizer file exists
   - Verify drug configurations in helper_functions.py

### Testing

Use the minimal test version for MQTT connectivity testing:
```bash
python orchestrator_minimal.py --test-mqtt
```

This validates MQTT connection without requiring the full BO stack.