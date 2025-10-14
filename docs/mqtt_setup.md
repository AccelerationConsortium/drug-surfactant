# MQTT Infrastructure Setup

This document describes the MQTT messaging infrastructure for the drug-surfactant closed-loop system, enabling communication between the Mac orchestrator and the Opentrons Flex robot.

## Overview

The system uses MQTT (Message Queuing Telemetry Transport) as the messaging backbone for real-time communication between:
- **Mac Orchestrator**: Runs optimization algorithms and experiment design
- **Opentrons Flex Robot**: Executes protocols and collects experimental data

## Architecture

### Components
1. **HiveMQ Cloud Broker**: Managed MQTT broker for reliable message routing
2. **MQTT Client Library**: Python-based client using paho-mqtt
3. **Topic Schema**: Structured topics for different message types
4. **Configuration Management**: Environment-based configuration

### Message Flow
```
Mac Orchestrator  ←--MQTT Topics--→  Opentrons Flex
     ↓                                    ↑
Commands/Data        HiveMQ Cloud        Status/Results
```

## HiveMQ Cloud Setup

### 1. Create HiveMQ Cloud Instance

1. Visit [HiveMQ Cloud](https://www.hivemq.com/mqtt-cloud-broker/)
2. Sign up for a free account
3. Create a new cluster:
   - **Cluster Name**: `drug-surfactant-cluster`
   - **Provider**: Choose your preferred cloud provider
   - **Region**: Select closest to your location
   - **Plan**: Start with free tier (100 connections, 10GB data transfer/month)

### 2. Configure Access Credentials

1. In the HiveMQ Cloud Console, go to **Access Management**
2. Create new credentials:
   - **Username**: `drug_surfactant_user`
   - **Password**: Generate strong password
   - **Permissions**: Full access (for development)

### 3. Get Connection Details

Record the following from your cluster overview:
- **Host**: `your-cluster.hivemq.cloud`
- **Port**: `8883` (TLS/SSL)
- **Username**: Your created username
- **Password**: Your created password

## Local Configuration

### 1. Environment Setup

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your HiveMQ credentials:
```env
MQTT_BROKER_HOST=your_cluster.hivemq.cloud
MQTT_BROKER_PORT=8883
MQTT_USERNAME=drug_surfactant_user
MQTT_PASSWORD=your_generated_password
MQTT_CLIENT_ID_PREFIX=drug_surfactant_system
MQTT_USE_TLS=true

ORCHESTRATOR_ID=mac_orchestrator
ROBOT_ID=opentrons_flex
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `paho-mqtt>=1.6.0`: MQTT client library
- `python-dotenv>=1.0.0`: Environment variable management

## Topic Schema

### Command Topics (Orchestrator → Robot)
- `drug_surfactant/commands/start_protocol` - Start protocol execution
- `drug_surfactant/commands/stop_protocol` - Stop protocol execution  
- `drug_surfactant/commands/pause_protocol` - Pause protocol execution
- `drug_surfactant/commands/resume_protocol` - Resume protocol execution
- `drug_surfactant/commands/update_config` - Update robot configuration
- `drug_surfactant/commands/calibrate` - Initiate calibration
- `drug_surfactant/commands/load_experiment` - Load experiment design
- `drug_surfactant/commands/set_parameters` - Set experiment parameters

### Status Topics (Robot → Orchestrator)
- `drug_surfactant/status/robot` - General robot status
- `drug_surfactant/status/protocol` - Protocol execution status
- `drug_surfactant/status/pipette` - Pipette status
- `drug_surfactant/status/modules` - Hardware module status
- `drug_surfactant/status/deck` - Deck configuration status
- `drug_surfactant/status/errors` - Error messages
- `drug_surfactant/status/warnings` - Warning messages

### Data Topics (Robot → Orchestrator)
- `drug_surfactant/data/absorbance` - Absorbance measurements
- `drug_surfactant/data/volumes` - Volume measurements
- `drug_surfactant/data/temperature` - Temperature readings
- `drug_surfactant/data/step_completed` - Protocol step completion
- `drug_surfactant/data/experiment_results` - Final experiment results
- `drug_surfactant/data/raw` - Raw sensor data

### Heartbeat Topics (Bidirectional)
- `drug_surfactant/heartbeat/orchestrator` - Orchestrator heartbeat
- `drug_surfactant/heartbeat/robot` - Robot heartbeat

### Discovery Topics (Bidirectional)
- `drug_surfactant/discovery/announce` - Device announcements
- `drug_surfactant/discovery/capabilities` - Device capabilities
- `drug_surfactant/discovery/ping` - Connectivity ping
- `drug_surfactant/discovery/pong` - Connectivity pong response

## Message Format

All messages use JSON format with the following structure:

### Command Messages
```json
{
  "command": "start_protocol",
  "protocol_id": "protocol_001",
  "parameters": {
    "drug": "IBP",
    "concentration": 180.0,
    "surfactants": ["s1", "s4"],
    "volumes": [100, 200]
  },
  "timestamp": "2024-10-14T05:26:03.043Z",
  "client_id": "drug_surfactant_system_orchestrator_1728885963"
}
```

### Status Messages
```json
{
  "status": "running",
  "protocol_id": "protocol_001",
  "progress": 0.75,
  "current_step": "absorbance_reading",
  "timestamp": "2024-10-14T05:26:03.043Z",
  "client_id": "drug_surfactant_system_robot_1728885963"
}
```

### Data Messages
```json
{
  "experiment_id": "exp_001",
  "measurement_type": "absorbance",
  "data": {
    "wavelength": 595,
    "values": [0.125, 0.234, 0.156, 0.289],
    "well_positions": ["A1", "A2", "A3", "A4"]
  },
  "timestamp": "2024-10-14T05:26:03.043Z",
  "client_id": "drug_surfactant_system_robot_1728885963"
}
```

## Testing Scripts

### 1. Comprehensive Connection Test
```bash
cd mqtt/scripts
python test_connection.py
```

This script tests:
- Configuration validation
- Broker connectivity
- Message publishing
- Message subscription
- Bidirectional communication

### 2. Publisher Test
```bash
cd mqtt/scripts
python test_publisher.py
```

Tests message publishing capabilities with various message types.

### 3. Subscriber Test
```bash
cd mqtt/scripts
python test_subscriber.py --duration 30
```

Tests message subscription and handling for 30 seconds.

## Usage Examples

### Basic Publisher (Orchestrator)
```python
from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics

class Orchestrator(MQTTClientBase):
    def __init__(self):
        super().__init__(client_id="orchestrator", role="orchestrator")
    
    def start_experiment(self, protocol_data):
        if self.connect():
            self.publish_message(
                mqtt_topics.Commands.START_PROTOCOL, 
                protocol_data
            )

# Usage
orchestrator = Orchestrator()
protocol_data = {"protocol_id": "test_001", "drug": "IBP"}
orchestrator.start_experiment(protocol_data)
```

### Basic Subscriber (Robot)
```python
from mqtt.mqtt_client import MQTTClientBase
from mqtt.config.topics import mqtt_topics

class Robot(MQTTClientBase):
    def __init__(self):
        super().__init__(client_id="robot", role="robot")
        self.register_message_handler(
            mqtt_topics.Commands.START_PROTOCOL,
            self.handle_start_protocol
        )
    
    def handle_start_protocol(self, topic, data):
        print(f"Starting protocol: {data['protocol_id']}")
        # Execute protocol...
        
        # Send status update
        status = {"status": "started", "protocol_id": data["protocol_id"]}
        self.publish_message(mqtt_topics.Status.PROTOCOL_STATUS, status)

# Usage
robot = Robot()
robot.connect()
```

## Security Considerations

1. **TLS Encryption**: All connections use TLS 1.2+ encryption
2. **Authentication**: Username/password authentication required
3. **Access Control**: Topic-based permissions (implement in production)
4. **Credential Management**: Store credentials in environment variables, not in code
5. **Network Security**: Use VPN or private networks in production environments

## Troubleshooting

### Connection Issues
1. **Check credentials**: Verify username/password in .env file
2. **Network connectivity**: Ensure internet access and DNS resolution
3. **Port access**: Ensure port 8883 is not blocked by firewall
4. **TLS certificates**: Check system certificate store

### Message Issues
1. **Topic permissions**: Verify client has publish/subscribe rights
2. **Message size**: Check broker message size limits
3. **QoS settings**: Adjust Quality of Service levels if needed
4. **Client ID conflicts**: Ensure unique client IDs

### Performance Issues
1. **Connection limits**: Monitor concurrent connection count
2. **Message rate**: Check broker rate limiting
3. **Bandwidth**: Monitor data transfer usage
4. **Latency**: Test message round-trip times

## Monitoring and Logging

The MQTT client includes comprehensive logging:
- Connection events
- Message publishing/receiving
- Error conditions
- Performance metrics

Configure logging level in your application:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Next Steps

1. **Production Setup**: Move to dedicated HiveMQ instance
2. **Security Hardening**: Implement certificate-based authentication
3. **Monitoring**: Add metrics collection and alerting
4. **Scaling**: Plan for multiple robot instances
5. **Integration**: Connect with existing laboratory systems

## Support

For issues with:
- **MQTT Infrastructure**: Check this documentation and test scripts
- **HiveMQ Cloud**: Consult [HiveMQ Documentation](https://docs.hivemq.com/)
- **paho-mqtt**: See [Paho MQTT Documentation](https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)