# drug-surfactant

A closed-loop drug-surfactant optimization system using Bayesian optimization and Opentrons Flex automation.

## Overview

This repository contains the implementation of an automated drug-surfactant formulation optimization system that uses:

- **Bayesian Optimization**: For intelligent experiment design using Ax platform
- **MQTT Communication**: For orchestration between Mac controller and Opentrons Flex
- **Opentrons Flex**: For automated liquid handling and experiment execution
- **Closed-loop Feedback**: Automated result collection and optimization iteration

## System Architecture

```
┌─────────────────┐    MQTT     ┌─────────────────┐
│   Mac Controller│ ◄────────► │ Opentrons Flex  │
│   (Orchestrator)│             │   (Device)      │
└─────────────────┘             └─────────────────┘
         │                               │
         ▼                               ▼
   Bayesian Opt.                 Protocol Execution
   & Exp. Design                 & Result Collection
```

## Components

### 1. Device Listener (`device.py`)

The MQTT listener that runs on the Opentrons Flex robot. It:
- Subscribes to `lab/experiments/new` for new experiments
- Generates protocol scripts from experiment data
- Executes protocols using the Flex API
- Publishes results to `lab/experiments/result`

#### Configuration

Set these environment variables:

```bash
# Execution mode
export OPENTRONS_MODE=simulate  # or 'execute'

# MQTT Broker settings
export MQTT_HOST=your-broker.hivemq.cloud
export MQTT_PORT=8883
export MQTT_USERNAME=your-username
export MQTT_PASSWORD=your-password

# Device identification
export DEVICE_ID=flex-lab-001
```

#### Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run the device listener
python device.py
```

### 2. Experiment Templates

Located in `experiments/20250917_closed_loop/`:
- `drug_surfactant_otflex_template.py`: Base protocol template
- `helper_functions.py`: Protocol generation utilities
- `iteration_*/protocol/`: Generated protocol files

### 3. MQTT Message Format

#### Experiment Message (`lab/experiments/new`)
```json
{
  "experiment_id": "exp_20250101_001",
  "session_id": "session_001", 
  "timestamp": 1704067200.0,
  "data": [
    {
      "trial_index": "0",
      "drug": "IBP",
      "s1": "30.0",
      "s2": "20.0", 
      "water": "280.0",
      "IBP": "180.0"
    }
  ]
}
```

#### Result Message (`lab/experiments/result`)
```json
{
  "experiment_id": "exp_20250101_001",
  "device_id": "flex-lab-001",
  "status": "completed",
  "execution_mode": "execute", 
  "timestamp": 1704067800.0,
  "result_files": ["raw_absorbance_exp_20250101_001.csv"]
}
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AccelerationConsortium/drug-surfactant.git
cd drug-surfactant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables (see Configuration section above)

## Testing

Run the test suite to validate functionality:

```bash
# Test core device functionality
python test_device.py

# View usage examples
python example_usage.py
```

## Development

### Protocol Generation

The system uses template-based protocol generation:
1. Base template: `drug_surfactant_otflex_template.py`
2. Experiment data injection via JSON replacement
3. Dynamic file naming for result tracking
4. Temporary protocol file creation and cleanup

### Adding New Experiments

1. Define experiment parameters in the data structure
2. Update the template if new liquid handling is needed
3. Test with `OPENTRONS_MODE=simulate` first
4. Deploy to Flex for execution

## Related Issues

- [Issue #30](https://github.com/AccelerationConsortium/drug-surfactant/issues/30): MQTT Infrastructure Setup
- [Issue #32](https://github.com/AccelerationConsortium/drug-surfactant/issues/32): Mac Orchestrator Implementation  
- [Issue #34](https://github.com/AccelerationConsortium/drug-surfactant/issues/34): Flex Device Implementation (this)

## License

This project is licensed under the MIT License.