import random
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SimpleDetectionEngine:
    
    def __init__(self, default_detection_rate: float = 0.1):
        self.default_detection_rate = default_detection_rate
        self.action_detection_rates = {}
        self.actions_loaded = False
    
    def load_action_detection_rates(self):
        if self.actions_loaded:
            return
            
        try:
            from src.actions.action_manager import get_attack_actions, get_defense_actions
            
            attack_actions = get_attack_actions()
            for action in attack_actions:
                dummy_node = type('DummyNode', (), {'id': 'dummy', 'assets': 1, 'vulnerabilities': 1})()
                detection_prob = action.detection_probability(dummy_node, 'VISIBLE', None)
                self.action_detection_rates[action.name] = detection_prob
                logger.debug(f"Loaded detection rate for {action.name}: {detection_prob}")
            
            defense_actions = get_defense_actions()
            for action in defense_actions:
                dummy_node = type('DummyNode', (), {'id': 'dummy', 'assets': 1, 'vulnerabilities': 1})()
                detection_prob = action.detection_probability(dummy_node, 'ADMIN', None)
                self.action_detection_rates[action.name] = detection_prob
                logger.debug(f"Loaded detection rate for {action.name}: {detection_prob}")
            
            self.actions_loaded = True
            logger.info(f"Loaded detection rates for {len(self.action_detection_rates)} actions")
            
        except Exception as e:
            logger.warning(f"Failed to load action detection rates: {e}")
            logger.warning("Using default detection rates")
    
    def calculate_detection_probability(self, action, target_node, actor_access: str = None, actor = None) -> float:
        self.load_action_detection_rates()
        
        action_name = action.name if hasattr(action, 'name') else str(action)
        base_rate = self.action_detection_rates.get(action_name, self.default_detection_rate)
        security_multiplier = 1.0
        
        node_properties = target_node if isinstance(target_node, dict) else {}
        if hasattr(target_node, '__dict__'):
            node_properties = target_node.__dict__
        
        if isinstance(node_properties, dict):
            if node_properties.get('security_level') == 'high':
                security_multiplier = 2.0
            elif node_properties.get('security_level') == 'low':
                security_multiplier = 0.5
            
            if node_properties.get('monitoring', False):
                security_multiplier *= 1.5
        
        return min(0.95, base_rate * security_multiplier)
    
    def should_detect_action(self, action_name: str, node_properties: Dict[str, Any], actor_access: str = None, actor = None) -> bool:
        detection_prob = self.calculate_detection_probability(action_name, node_properties)
        return random.random() < detection_prob
    
    def sample_detection_time(self, action_name: str, action_duration: float) -> float:
        return random.uniform(0, action_duration)
    
    def update_time(self, current_time: float):
        pass

DetectionEngine = SimpleDetectionEngine