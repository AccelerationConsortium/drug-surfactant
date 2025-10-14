"""
MQTT Topics Schema
Defines the messaging topics for closed-loop communication between 
the Mac orchestrator and the Opentrons Flex robot.
"""

# Base topic prefix
BASE_TOPIC = "drug_surfactant"

class MQTTTopics:
    """Centralized MQTT topic definitions for the drug-surfactant system."""
    
    BASE_TOPIC = BASE_TOPIC
    
    # Command topics (Orchestrator -> Robot)
    class Commands:
        BASE = f"{BASE_TOPIC}/commands"
        
        # Protocol execution commands
        START_PROTOCOL = f"{BASE}/start_protocol"
        STOP_PROTOCOL = f"{BASE}/stop_protocol"
        PAUSE_PROTOCOL = f"{BASE}/pause_protocol"
        RESUME_PROTOCOL = f"{BASE}/resume_protocol"
        
        # Configuration commands
        UPDATE_CONFIG = f"{BASE}/update_config"
        CALIBRATE = f"{BASE}/calibrate"
        
        # Experiment design commands
        LOAD_EXPERIMENT = f"{BASE}/load_experiment"
        SET_PARAMETERS = f"{BASE}/set_parameters"
    
    # Status topics (Robot -> Orchestrator)
    class Status:
        BASE = f"{BASE_TOPIC}/status"
        
        # Robot status
        ROBOT_STATUS = f"{BASE}/robot"
        PROTOCOL_STATUS = f"{BASE}/protocol"
        
        # Hardware status
        PIPETTE_STATUS = f"{BASE}/pipette"
        MODULE_STATUS = f"{BASE}/modules"
        DECK_STATUS = f"{BASE}/deck"
        
        # Error reporting
        ERRORS = f"{BASE}/errors"
        WARNINGS = f"{BASE}/warnings"
    
    # Data topics (Robot -> Orchestrator)
    class Data:
        BASE = f"{BASE_TOPIC}/data"
        
        # Experimental data
        ABSORBANCE_DATA = f"{BASE}/absorbance"
        VOLUME_DATA = f"{BASE}/volumes"
        TEMPERATURE_DATA = f"{BASE}/temperature"
        
        # Protocol execution data
        STEP_COMPLETED = f"{BASE}/step_completed"
        EXPERIMENT_RESULTS = f"{BASE}/experiment_results"
        
        # Raw sensor data
        RAW_DATA = f"{BASE}/raw"
    
    # Heartbeat topics (Bidirectional)
    class Heartbeat:
        BASE = f"{BASE_TOPIC}/heartbeat"
        
        ORCHESTRATOR = f"{BASE}/orchestrator"
        ROBOT = f"{BASE}/robot"
    
    # Discovery topics (System discovery and capabilities)
    class Discovery:
        BASE = f"{BASE_TOPIC}/discovery"
        
        ANNOUNCE = f"{BASE}/announce"
        CAPABILITIES = f"{BASE}/capabilities"
        PING = f"{BASE}/ping"
        PONG = f"{BASE}/pong"
    
    @classmethod
    def get_all_topics(cls) -> list:
        """Get all defined topics as a list."""
        topics = []
        
        # Collect topics from all nested classes
        for class_attr in [cls.Commands, cls.Status, cls.Data, cls.Heartbeat, cls.Discovery]:
            for attr_name in dir(class_attr):
                if not attr_name.startswith('_') and attr_name != 'BASE':
                    attr_value = getattr(class_attr, attr_name)
                    if isinstance(attr_value, str) and attr_value.startswith(BASE_TOPIC):
                        topics.append(attr_value)
        
        return topics
    
    @classmethod
    def get_subscription_topics(cls, role: str) -> list:
        """Get topics to subscribe to based on role (orchestrator or robot)."""
        if role.lower() == 'orchestrator':
            return [
                cls.Status.ROBOT_STATUS,
                cls.Status.PROTOCOL_STATUS,
                cls.Status.PIPETTE_STATUS,
                cls.Status.MODULE_STATUS,
                cls.Status.DECK_STATUS,
                cls.Status.ERRORS,
                cls.Status.WARNINGS,
                cls.Data.ABSORBANCE_DATA,
                cls.Data.VOLUME_DATA,
                cls.Data.TEMPERATURE_DATA,
                cls.Data.STEP_COMPLETED,
                cls.Data.EXPERIMENT_RESULTS,
                cls.Heartbeat.ROBOT,
                cls.Discovery.ANNOUNCE,
                cls.Discovery.PONG
            ]
        
        elif role.lower() == 'robot':
            return [
                cls.Commands.START_PROTOCOL,
                cls.Commands.STOP_PROTOCOL,
                cls.Commands.PAUSE_PROTOCOL,
                cls.Commands.RESUME_PROTOCOL,
                cls.Commands.UPDATE_CONFIG,
                cls.Commands.CALIBRATE,
                cls.Commands.LOAD_EXPERIMENT,
                cls.Commands.SET_PARAMETERS,
                cls.Heartbeat.ORCHESTRATOR,
                cls.Discovery.PING
            ]
        
        else:
            raise ValueError(f"Unknown role: {role}. Must be 'orchestrator' or 'robot'")

# Create instance for easy import
mqtt_topics = MQTTTopics()