# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 2025-10-15: MQTT device-orchestrator pattern for OT-Flex integration
  - `mqtt_otflex_simulate_device.py`: MQTT device using opentrons.simulate following AC dev lab OT2mqtt.py pattern
    - Uses `opentrons.simulate.get_protocol_api()` for direct opentrons function calls
    - Queue-based MQTT command processing
    - Mock absorbance reader (opentrons.simulate cannot load real module)
    - Easy toggle to real hardware with commented line showing actual module loading
    - Multi-wavelength absorbance reading support
    - Flexible well selection (all wells, specific wells, single well)
    - **Independent absorbance measurements** without requiring mixing experiments
    - **Independent mixing experiments using complete deep plate workflow**
      - **Step 1: Mix in deep plate** - Components transferred to deep well plate on heater-shaker
        - Deep plates prevent spillage (larger volume, more headspace)
        - Improves compositional accuracy (minimal volume loss)
        - Enables efficient mixing (accommodates magnetic/vortex mixing)
        - Pipette selection based on volume (50µL for ≤40µL, 1000µL for >40µL)
        - Well clearances: aspirate 2mm, dispense 25mm (deep plate optimized)
        - Air gap handling (55µL for 1000µL pipette, 10µL for 50µL pipette)
        - Initial heater-shaker mixing (1000 rpm, 1 minute)
      - **Step 2: Dispense replicates** - `make_exp()` function transfers from deep plate to standard 96-well plate
        - Creates 3 replicates per formulation (270µL each)
        - Well clearances: aspirate 2mm, dispense 13mm (standard plate optimized)
        - Standard plate is what goes to plate reader (optimized for optical measurements)
      - **Step 3: Final mixing** - Standard plate on heater-shaker for final mixing
        - `plate_on_hs_to_reader()` function enables streamlined heater-shaker-to-reader workflow
        - Final mixing (1000 rpm, 5 minutes)
      - **Step 4: Absorbance reading** - Standard plate moved to plate reader
        - Gripper operations with `protocol.move_labware()` and proper offsets (`pick_up_offset={'x': 0, 'y': 0, 'z':-2}`)
        - Optional `read_after_mixing` parameter to measure absorbance after mixing
        - `wells_to_read` parameter to specify which wells to measure
        - Supports reading all occupied wells on a single plate
        - Enables retroactive failure detection (e.g., t=1hr looked good but t=12hr shows failure)
        - Can read new experiment and previously successful experiments simultaneously
        - Helps track formulation stability over time and update model with failure data
      - Based on real protocol patterns from experiments/20250917_closed_loop/drug_surfactant_otflex_template.py
      - All gripper transfers implemented (deep plate ↔ heater-shaker, standard plate ↔ heater-shaker, standard plate ↔ reader)
    - Both operations can be triggered independently via MQTT commands
    - **Response payloads include input_message for traceability**
    - **Supports measuring absorbance of both new and previously successful experiments**
  - `test_mqtt_simulate_orchestrator.py`: Test orchestrator demonstrating both independent operations
    - Absorbance commands (all wells, specific wells, single well, multi-wavelength)
    - Mixing experiment commands with real Opentrons operations
    - Demonstrates independence of absorbance and mixing operations
  - `MQTT_README.md`: Documentation for MQTT communication pattern
  - `requirements.txt`: Added paho-mqtt>=2.1.0 and opentrons>=7.0.0
- 2025-10-14: HiveMQ integration test script (`test_hivemq_connection.py`) to verify MQTT broker connectivity

### Implementation Details
- Natural error handling with proper exceptions (ValueError, ConnectionError)
- Errors bubble up naturally without try/except wrappers
- Top-level scripts without `if __name__ == "__main__"` wrappers
- Secure TLS/SSL connection to HiveMQ Cloud (MQTT v5)
- JSON message serialization with experiment ID tracking
- Queue-based message handling with timeouts
