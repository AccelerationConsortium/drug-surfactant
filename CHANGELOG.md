# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- 2025-10-20: Replaced `ExpectedImprovement` with `LogExpectedImprovement` in benchmarking scripts to fix known numerical issues

### Added
- 2025-10-14: HiveMQ integration test script (`test_hivemq_connection.py`) to verify MQTT broker connectivity
- 2025-10-14: `paho-mqtt` dependency for MQTT client functionality
