"""
MQTT Client Base Class
Provides a foundation for MQTT communication in the drug-surfactant system.
"""

import json
import logging
import ssl
import time
from datetime import datetime
from typing import Callable, Dict, Any, Optional
import paho.mqtt.client as mqtt

from mqtt.config.mqtt_config import mqtt_config
from mqtt.config.topics import mqtt_topics

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTClientBase:
    """Base MQTT client for the drug-surfactant system."""
    
    def __init__(self, client_id: str, role: str):
        """
        Initialize MQTT client.
        
        Args:
            client_id: Unique identifier for this client
            role: Either 'orchestrator' or 'robot'
        """
        self.client_id = f"{mqtt_config.client_id_prefix}_{client_id}_{int(time.time())}"
        self.role = role.lower()
        self.connected = False
        self.message_handlers = {}
        
        # Initialize MQTT client
        self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.client.on_publish = self._on_publish
        
        # Configure authentication
        auth_params = mqtt_config.get_auth_params()
        if auth_params:
            self.client.username_pw_set(**auth_params)
        
        # Configure TLS if enabled
        if mqtt_config.use_tls:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.client.tls_set_context(context)
            
            if mqtt_config.ca_cert_path:
                self.client.tls_set(ca_certs=mqtt_config.ca_cert_path,
                                  certfile=mqtt_config.cert_file,
                                  keyfile=mqtt_config.key_file)
        
        logger.info(f"Initialized MQTT client: {self.client_id} (role: {self.role})")
    
    def connect(self) -> bool:
        """Connect to the MQTT broker."""
        try:
            if not mqtt_config.validate():
                logger.error("Invalid MQTT configuration")
                return False
            
            connection_params = mqtt_config.get_connection_params()
            logger.info(f"Connecting to MQTT broker at {connection_params['host']}:{connection_params['port']}")
            
            self.client.connect(**connection_params)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10  # seconds
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("Successfully connected to MQTT broker")
                self._subscribe_to_topics()
                return True
            else:
                logger.error("Failed to connect to MQTT broker within timeout")
                return False
                
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for successful connection."""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker with result code {rc}")
        else:
            self.connected = False
            logger.error(f"Failed to connect to MQTT broker with result code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for disconnection."""
        self.connected = False
        logger.info(f"Disconnected from MQTT broker with result code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"Received message on topic '{topic}': {payload}")
            
            # Try to parse as JSON
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
            
            # Call registered handlers
            if topic in self.message_handlers:
                self.message_handlers[topic](topic, data)
            else:
                logger.warning(f"No handler registered for topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for successful subscription."""
        logger.debug(f"Subscribed with QoS: {granted_qos}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for successful publish."""
        logger.debug(f"Message published with mid: {mid}")
    
    def _subscribe_to_topics(self):
        """Subscribe to relevant topics based on role."""
        try:
            topics = mqtt_topics.get_subscription_topics(self.role)
            for topic in topics:
                self.client.subscribe(topic, qos=mqtt_config.qos)
                logger.info(f"Subscribed to topic: {topic}")
        except Exception as e:
            logger.error(f"Error subscribing to topics: {e}")
    
    def register_message_handler(self, topic: str, handler: Callable[[str, Any], None]):
        """Register a message handler for a specific topic."""
        self.message_handlers[topic] = handler
        logger.info(f"Registered handler for topic: {topic}")
    
    def publish_message(self, topic: str, data: Any, retain: bool = False) -> bool:
        """
        Publish a message to a topic.
        
        Args:
            topic: MQTT topic to publish to
            data: Data to publish (will be JSON encoded if dict/list)
            retain: Whether to retain the message
            
        Returns:
            True if message was queued for sending, False otherwise
        """
        try:
            if not self.connected:
                logger.error("Cannot publish: not connected to broker")
                return False
            
            # Prepare payload
            if isinstance(data, (dict, list)):
                payload = json.dumps(data, default=str)
            else:
                payload = str(data)
            
            # Add timestamp if data is a dict
            if isinstance(data, dict):
                data_with_timestamp = data.copy()
                data_with_timestamp['timestamp'] = datetime.now().isoformat()
                data_with_timestamp['client_id'] = self.client_id
                payload = json.dumps(data_with_timestamp, default=str)
            
            # Publish message
            result = self.client.publish(topic, payload, qos=mqtt_config.qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published message to '{topic}': {payload}")
                return True
            else:
                logger.error(f"Failed to publish message to '{topic}': {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
    
    def send_heartbeat(self):
        """Send a heartbeat message."""
        heartbeat_topic = (mqtt_topics.Heartbeat.ORCHESTRATOR if self.role == 'orchestrator' 
                          else mqtt_topics.Heartbeat.ROBOT)
        
        heartbeat_data = {
            'status': 'alive',
            'role': self.role,
            'client_id': self.client_id
        }
        
        return self.publish_message(heartbeat_topic, heartbeat_data)