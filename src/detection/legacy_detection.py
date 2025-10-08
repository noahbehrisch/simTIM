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
    
    def calculate_detection_probability(self, action, target, actor_access, actor):
        base_rate = self.action_detection_rates.get(action.name, 0.2)
        return min(base_rate, 0.95)
    
    def should_detect_action(self, action_name: str, node_properties: Dict[str, Any], actor_access: str = None, actor = None) -> bool:
        # Create a mock action object for detection probability calculation
        mock_action = type('MockAction', (), {'name': action_name})()
        mock_target = type('MockTarget', (), {'properties': node_properties})()
        detection_prob = self.calculate_detection_probability(mock_action, mock_target, actor_access, actor)
        return random.random() < detection_prob
    
    def sample_detection_time(self, action_name: str, action_duration: float) -> float:
        return random.uniform(0, action_duration)
    
    def update_time(self, current_time: float):
        pass

DetectionEngine = SimpleDetectionEngine