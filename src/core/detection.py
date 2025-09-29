import random
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimpleDetectionEngine:
    
    def __init__(self, default_detection_rate: float = 0.1):
        self.default_detection_rate = default_detection_rate
        self.action_detection_rates = {
            'network_scan': 0.3,
            'port_scan': 0.4,
            'vulnerability_scan': 0.5,
            'apache_tapestry_exploit': 0.2,
            'mysql_exploit': 0.15,
            'database_attack': 0.25,
            'privilege_escalation': 0.1,
            'lateral_movement': 0.05,
            'data_exfiltration': 0.08,
        }
    
    def calculate_detection_probability(self, action_type: str, node_properties: Dict[str, Any]) -> float:
        base_rate = self.action_detection_rates.get(action_type, self.default_detection_rate)
        security_multiplier = 1.0
        
        if isinstance(node_properties, dict):
            if node_properties.get('security_level') == 'high':
                security_multiplier = 2.0
            elif node_properties.get('security_level') == 'low':
                security_multiplier = 0.5
            
            if node_properties.get('monitoring', False):
                security_multiplier *= 1.5
        
        return min(0.95, base_rate * security_multiplier)
    
    def should_detect_action(self, action_type: str, node_properties: Dict[str, Any]) -> bool:
        detection_prob = self.calculate_detection_probability(action_type, node_properties)
        return random.random() < detection_prob
    
    def sample_detection_time(self, action_type: str, action_duration: float) -> float:
        return random.uniform(0, action_duration)

DetectionEngine = SimpleDetectionEngine