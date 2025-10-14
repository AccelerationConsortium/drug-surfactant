"""
MQTT Configuration Module
Handles loading and validation of MQTT broker settings from environment variables.
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

class MQTTConfig:
    """Configuration class for MQTT broker connection settings."""
    
    def __init__(self):
        self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.broker_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        self.username = os.getenv('MQTT_USERNAME')
        self.password = os.getenv('MQTT_PASSWORD')
        self.client_id_prefix = os.getenv('MQTT_CLIENT_ID_PREFIX', 'drug_surfactant')
        
        # TLS Configuration
        self.use_tls = os.getenv('MQTT_USE_TLS', 'false').lower() == 'true'
        self.ca_cert_path = os.getenv('MQTT_CA_CERT_PATH')
        self.cert_file = os.getenv('MQTT_CERT_FILE')
        self.key_file = os.getenv('MQTT_KEY_FILE')
        
        # System IDs
        self.orchestrator_id = os.getenv('ORCHESTRATOR_ID', 'mac_orchestrator')
        self.robot_id = os.getenv('ROBOT_ID', 'opentrons_flex')
        
        # Connection settings
        self.keepalive = 60
        self.qos = 1  # At least once delivery
        
    def validate(self) -> bool:
        """Validate that required configuration is present."""
        required_fields = [self.broker_host]
        if self.use_tls and self.broker_port == 8883:
            required_fields.extend([self.username, self.password])
        
        return all(field is not None and field != '' for field in required_fields)
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters as a dictionary."""
        return {
            'host': self.broker_host,
            'port': self.broker_port,
            'keepalive': self.keepalive
        }
    
    def get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters."""
        auth = {}
        if self.username:
            auth['username'] = self.username
        if self.password:
            auth['password'] = self.password
        return auth

# Global configuration instance
mqtt_config = MQTTConfig()