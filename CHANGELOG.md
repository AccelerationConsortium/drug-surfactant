# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Device MQTT Listener** (`device.py`) - MQTT listener for Opentrons Flex that subscribes to experiment messages, generates protocol scripts, and executes them [2025-01-14]
- **MQTT Dependencies** - Added paho-mqtt and opentrons packages to requirements.txt [2025-01-14]
- **Environment Mode Control** - Added OPENTRONS_MODE environment variable for simulate vs execute modes [2025-01-14]
- **Protocol Generation** - Template-based protocol generation from experiment MQTT payloads [2025-01-14]
- **Result Publishing** - Automatic result publishing via MQTT after protocol execution [2025-01-14]
- **Comprehensive Documentation** - Updated README.md with system architecture, usage instructions, and MQTT message formats [2025-01-14]
- **Test Suite** (`test_device.py`) - Validation tests for device functionality without external dependencies [2025-01-14]
- **Usage Examples** (`example_usage.py`) - Demonstration scripts showing configuration and message formats [2025-01-14]

### Features
- Subscribes to `lab/experiments/new` topic for incoming experiment requests
- Generates temporary protocol files based on the existing template system
- Executes protocols using Opentrons Flex API with simulate/execute mode support
- Publishes execution results to `lab/experiments/result` topic
- Automatic cleanup of temporary protocol files
- Comprehensive error handling and logging
- Support for both simulation and hardware execution modes

### Topics
- **Input**: `lab/experiments/new` - Receives experiment configurations
- **Output**: `lab/experiments/result` - Publishes execution results and status