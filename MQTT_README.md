# MQTT Device-Orchestrator Pattern Implementation

This directory contains an MQTT device-orchestrator pattern for self-driving laboratories with OT-Flex integration, based on the [ACC-HelloWorld microcourses](https://github.com/AccelerationConsortium/ac-microcourses) and [AC dev lab OT2mqtt.py](https://github.com/AccelerationConsortium/ac-dev-lab/blob/main/src/ac_training_lab/ot-2/_scripts/OT2mqtt.py).

## Overview

The implementation provides MQTT-based control of OT-Flex robots with protocol simulation using opentrons.simulate:
- **Device**: Uses `opentrons.simulate.get_protocol_api()` to validate protocols and simulate absorbance reading
- **Orchestrator**: Sends experiment commands and receives results via MQTT

## Files

- `mqtt_otflex_simulate_device.py` - MQTT device using opentrons.simulate for protocol validation
- `test_mqtt_simulate_orchestrator.py` - Test orchestrator demonstrating absorbance reading commands


## Setup

### Prerequisites
```bash
pip install paho-mqtt>=2.1.0 opentrons>=7.0.0
```

### Environment Variables
Set the following environment variables for HiveMQ connection:
```bash
export HIVEMQ_HOST="your-broker-host"
export HIVEMQ_USERNAME="your-username"
export HIVEMQ_PASSWORD="your-password"
```

## Usage

### Running the Device and Orchestrator

1. Start the device in one terminal:
```bash
python mqtt_otflex_simulate_device.py
```

2. Run the orchestrator in another terminal:
```bash
python test_mqtt_simulate_orchestrator.py
```

The orchestrator demonstrates:
- Single wavelength absorbance reading (600nm) for all 96 wells
- Multi-wavelength reading (450-650nm) for specific wells
- Single well reading

Results are printed to console and saved to `simulate_absorbance_results.json`.


## MQTT Topics

- Request topic: `sdl/otflex/{device_id}/experiment/request`
- Results topic: `sdl/otflex/{device_id}/experiment/results`

## Message Format

### Absorbance Reading Request
```json
{
  "experiment_id": "0433597597317b4f",
  "operation": "read_absorbance",
  "params": {
    "wavelengths": [450, 500, 550, 600, 650],
    "wells": ["A1", "A2", "B1", "B2"]
  }
}
```

### Absorbance Reading Response
```json
{
  "experiment_id": "0433597597317b4f",
  "operation": "read_absorbance",
  "absorbance_spectra": {
    "A1": {
      "450": 0.3797,
      "500": 0.3227,
      "550": 0.3141,
      "600": 0.4454,
      "650": 0.3705
    },
    "A2": {...}
  },
  "wavelengths": [450, 500, 550, 600, 650],
  "num_wells": 4,
  "status": "completed",
  "timestamp": 1760484800.123,
  "device_id": "otflex_001"
}
```

## Key Features

- ✅ Secure TLS/SSL connection to HiveMQ Cloud
- ✅ MQTT v5 protocol support
- ✅ JSON message serialization
- ✅ Experiment ID tracking for request-response matching
- ✅ Queue-based message handling with timeouts
- ✅ Protocol validation with opentrons.simulate
- ✅ Multi-wavelength absorbance reading
- ✅ Flexible well selection (all wells, specific wells, single well)
- ✅ Mock absorbance reader for simulation testing

## Implementation Notes

The device uses `opentrons.simulate.get_protocol_api()` to directly call opentrons functions following the [AC dev lab OT2mqtt.py pattern](https://github.com/AccelerationConsortium/ac-dev-lab/blob/main/src/ac_training_lab/ot-2/_scripts/OT2mqtt.py). The absorbance reader is mocked during simulation because opentrons.simulate cannot load the actual module.

## References

- [ACC-HelloWorld Microcourses](https://ac-microcourses.readthedocs.io/en/latest/courses/hello-world/)
- [AC Dev Lab OT2mqtt.py](https://github.com/AccelerationConsortium/ac-dev-lab/blob/main/src/ac_training_lab/ot-2/_scripts/OT2mqtt.py)
- [Opentrons Python API Documentation](https://docs.opentrons.com/v2/)
- [HiveMQ MQTT Broker](https://www.hivemq.com/)

