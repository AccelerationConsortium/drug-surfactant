# Drug-Surfactant Closed-Loop System

Automated optimization system for drug-surfactant formulations using Bayesian optimization and robotic liquid handling.

## Features

- **Bayesian Optimization**: Uses Ax platform for intelligent experiment design
- **Robotic Automation**: Integrates with Opentrons Flex for automated liquid handling
- **MQTT Communication**: Real-time messaging between orchestrator and robot
- **Closed-Loop Control**: Automated experiment execution and optimization

## MQTT Infrastructure

The system now includes comprehensive MQTT messaging infrastructure for real-time communication:

- **Broker**: HiveMQ Cloud for reliable message routing
- **Topics**: Structured messaging for commands, status, and data
- **Security**: TLS encryption and authentication
- **Testing**: Comprehensive test scripts and demo workflows

For detailed MQTT setup instructions, see [docs/mqtt_setup.md](docs/mqtt_setup.md).

### Quick MQTT Test

```bash
# Setup environment
cp .env.example .env
# Edit .env with your HiveMQ credentials

# Test connection
cd mqtt/scripts
python test_connection.py

# Run demo workflow
python demo_workflow.py --role both
```