# MQTT Communication Package

This package provides MQTT messaging infrastructure for the drug-surfactant closed-loop system.

## Quick Start

1. **Setup Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your HiveMQ Cloud credentials
   ```

2. **Test Connection**:
   ```bash
   cd mqtt/scripts
   python test_connection.py
   ```

3. **Run Demo Workflow**:
   ```bash
   cd mqtt/scripts
   python demo_workflow.py --role both
   ```

## Package Structure

```
mqtt/
├── __init__.py              # Package initialization
├── mqtt_client.py           # Base MQTT client class
├── config/
│   ├── __init__.py
│   ├── mqtt_config.py       # Configuration management
│   └── topics.py            # Topic definitions
└── scripts/
    ├── test_connection.py   # Comprehensive connection test
    ├── test_publisher.py    # Publisher test
    ├── test_subscriber.py   # Subscriber test
    └── demo_workflow.py     # Complete workflow demo
```

## Usage Examples

### Basic Publisher (Orchestrator)
```python
from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics

orchestrator = MQTTClientBase("orchestrator", "orchestrator")
orchestrator.connect()
orchestrator.publish_message(
    mqtt_topics.Commands.START_PROTOCOL, 
    {"protocol_id": "test_001"}
)
```

### Basic Subscriber (Robot)
```python
from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics

def handle_command(topic, data):
    print(f"Received: {data}")

robot = MQTTClientBase("robot", "robot")
robot.register_message_handler(mqtt_topics.Commands.START_PROTOCOL, handle_command)
robot.connect()
```

For detailed documentation, see [docs/mqtt_setup.md](../docs/mqtt_setup.md)