"""
TIM Detection System Implementation
Implements Section 4.5 of the TIM paper: Detection probability ρ(a, π̂(n)) and timing distribution F_a
"""

import random
import math
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class DetectionDistribution(ABC):
    """Abstract base class for detection time distributions F_a"""
    
    @abstractmethod
    def sample_detection_time(self, duration: float) -> float:
        """Sample detection time given action duration"""
        pass
    
    @abstractmethod
    def cumulative_probability(self, t: float, duration: float) -> float:
        """F_a(t/d_a) - cumulative probability of detection by time t"""
        pass

class UniformDetection(DetectionDistribution):
    """Uniform distribution for detection timing"""
    
    def sample_detection_time(self, duration: float) -> float:
        return random.uniform(0, duration)
    
    def cumulative_probability(self, t: float, duration: float) -> float:
        if t <= 0:
            return 0.0
        if t >= duration:
            return 1.0
        return t / duration

class ExponentialDetection(DetectionDistribution):
    """Exponential distribution for detection timing (early detection more likely)"""
    
    def __init__(self, rate_factor: float = 2.0):
        self.rate_factor = rate_factor
    
    def sample_detection_time(self, duration: float) -> float:
        rate = self.rate_factor / duration
        sample = random.expovariate(rate)
        return min(sample, duration)  # Cap at action duration
    
    def cumulative_probability(self, t: float, duration: float) -> float:
        if t <= 0:
            return 0.0
        if t >= duration:
            return 1.0
        rate = self.rate_factor / duration
        return 1 - math.exp(-rate * t)

class DetectionEngine:
    """Implements TIM Section 4.5 detection mechanism"""
    
    def __init__(self):
        self.detection_functions: Dict[str, Callable] = {}
        self.distribution_functions: Dict[str, DetectionDistribution] = {}
        
        # Default distributions
        self.distribution_functions['uniform'] = UniformDetection()
        self.distribution_functions['exponential'] = ExponentialDetection()
        
        # Initialize default detection functions
        self._setup_default_detection_functions()
    
    def _setup_default_detection_functions(self):
        """Setup default detection functions"""
        self.register_detection_function('apache_tapestry_exploit', endpoint_protection_detection)
        self.register_detection_function('mysql_exploit', endpoint_protection_detection)
        self.register_detection_function('network_scan', network_monitoring_detection)
        self.register_detection_function('database_attack', database_monitoring_detection)
    
    def register_detection_function(self, action_type: str, 
                                  detection_func: Callable[[Dict[str, Any]], float]):
        """Register ρ(a, π̂(n)) function for specific action type"""
        self.detection_functions[action_type] = detection_func
    
    def register_distribution(self, action_type: str, distribution: DetectionDistribution):
        """Register F_a distribution for specific action type"""
        self.distribution_functions[action_type] = distribution
    
    def calculate_detection_probability(self, action_type: str, 
                                      node_properties: Dict[str, Any]) -> float:
        """Calculate ρ(a, π̂(n)) - probability of detecting action on node"""
        if action_type not in self.detection_functions:
            return 0.0  # No detection capability for this action
        
        return self.detection_functions[action_type](node_properties)
    
    def should_detect_action(self, action_type: str, 
                           node_properties: Dict[str, Any]) -> bool:
        """Determine if action should be detected based on ρ(a, π̂(n))"""
        detection_prob = self.calculate_detection_probability(action_type, node_properties)
        return random.random() < detection_prob
    
    def sample_detection_time(self, action_type: str, action_duration: float) -> float:
        """Sample detection time using F_a distribution"""
        distribution = self.distribution_functions.get(
            action_type, 
            self.distribution_functions['uniform']
        )
        return distribution.sample_detection_time(action_duration)
    
    def get_cumulative_detection_probability(self, action_type: str, 
                                           time: float, duration: float) -> float:
        """Get F_a(t/d_a) cumulative probability"""
        distribution = self.distribution_functions.get(
            action_type,
            self.distribution_functions['uniform']
        )
        return distribution.cumulative_probability(time, duration)

# Default detection functions for common scenarios
def endpoint_protection_detection(properties: Dict[str, Any]) -> float:
    """Detection function for systems with endpoint protection"""
    endpoint_protection = properties.get('endpoint_protection', 'none')
    
    detection_rates = {
        'none': 0.0,
        'basic': 0.3,
        'sophos': 0.8,  # As per paper example
        'advanced': 0.9,
        'enterprise': 0.95
    }
    
    return detection_rates.get(endpoint_protection.lower(), 0.0)

def network_monitoring_detection(properties: Dict[str, Any]) -> float:
    """Detection function for network-based attacks"""
    network_monitoring = properties.get('network_monitoring', 'none')
    
    detection_rates = {
        'none': 0.0,
        'basic': 0.2,
        'ids': 0.6,
        'advanced_ids': 0.8,
        'enterprise_siem': 0.9
    }
    
    return detection_rates.get(network_monitoring.lower(), 0.0)

def database_monitoring_detection(properties: Dict[str, Any]) -> float:
    """Detection function for database attacks"""
    db_monitoring = properties.get('database_monitoring', 'none')
    
    detection_rates = {
        'none': 0.1,  # Some basic logging
        'basic_logging': 0.3,
        'advanced_logging': 0.7,
        'database_firewall': 0.9
    }
    
    return detection_rates.get(db_monitoring.lower(), 0.1)
