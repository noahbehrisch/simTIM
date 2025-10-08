"""
TIM Paper-Compliant Detection Engine

This module implements the detection mechanism exactly as specified in the TIM paper:
- Detection probability function ϱ(a, π̂(n)) for each action-node combination
- Cumulative distribution function Fa(t) for detection timing
- Proper temporal detection modeling

Reference: Section 4.5 "Detection of malicious activities" in TIM paper
"""

import random
import math
from typing import Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class TIMDetectionEngine:
    """
    Detection engine implementing the TIM paper specification:
    
    For an attacker action a applied to node n:
    - ϱ(a, π̂(n)) = probability that defender detects the action during execution
    - If detected, detection time follows CDF Fa(t) where t ∈ [0, da]
    - Detection probability at time t: Fa(t/da) · ϱ(a, π̂(n))
    """
    
    def __init__(self):
        self.base_detection_probabilities = {}  # ϱ(a, π̂(n)) values
        self.cumulative_distribution_functions = {}  # Fa functions per action
        self.actions_loaded = False
        
        # Initialize default detection probabilities based on node properties
        self._initialize_default_detection_probabilities()
        self._initialize_cumulative_distribution_functions()
    
    def _initialize_default_detection_probabilities(self):
        """
        Initialize detection probability function ϱ(a, π̂(n))
        Based on node properties (endpoint protection, monitoring, etc.)
        """
        # Detection probabilities depend on both action type and node properties
        self.detection_factors = {
            # Endpoint protection software increases detection
            'endpoint_protection': {
                'Sophos': 0.4,
                'McAfee': 0.35,
                'Symantec': 0.3,
                'Windows Defender': 0.25,
                'CrowdStrike': 0.5,
                'none': 0.0
            },
            
            # Network monitoring affects detection
            'network_monitoring': {
                'IDS': 0.3,
                'IPS': 0.4,
                'SIEM': 0.45,
                'basic_logging': 0.15,
                'none': 0.0
            },
            
            # System criticality affects monitoring intensity
            'criticality': {
                'high': 0.2,
                'medium': 0.1,
                'low': 0.05
            },
            
            # Internet exposure increases detection likelihood
            'exposure': {
                'internet_exposed': 0.15,
                'internal_only': -0.05
            }
        }
        
        # Base detection probabilities per action type
        self.base_action_detection = {
            'reconnaissance': 0.1,
            'network_scan': 0.2,
            'vulnerability_scan': 0.25,
            'exploit': 0.4,
            'privilege_escalation': 0.5,
            'lateral_movement': 0.35,
            'data_exfiltration': 0.6,
            'persistence': 0.3,
            'defense_evasion': 0.15
        }
    
    def _initialize_cumulative_distribution_functions(self):
        """
        Initialize cumulative distribution functions Fa(t) for different action types
        
        From TIM paper: "detection time follows a random distribution with cumulative 
        distribution function Fa with Fa(0) = 0 and Fa(1) = 1"
        """
        
        # Different detection timing patterns for different action types
        self.cdf_functions = {
            # Quick actions detected early or not at all
            'reconnaissance': self._early_detection_cdf,
            'network_scan': self._early_detection_cdf,
            
            # Exploitation often detected during execution
            'exploit': self._uniform_detection_cdf,
            'vulnerability_scan': self._uniform_detection_cdf,
            
            # Privilege escalation detected later in process
            'privilege_escalation': self._late_detection_cdf,
            'persistence': self._late_detection_cdf,
            
            # Data exfiltration has distinctive signature - often detected
            'data_exfiltration': self._immediate_detection_cdf,
            
            # Lateral movement detected throughout
            'lateral_movement': self._uniform_detection_cdf,
            
            # Defense evasion specifically designed to avoid detection
            'defense_evasion': self._very_late_detection_cdf
        }
    
    def _early_detection_cdf(self, t_normalized: float) -> float:
        """CDF for actions likely to be detected early (e.g., scans)"""
        # Exponential growth: most detection happens early
        return 1 - math.exp(-3 * t_normalized)
    
    def _uniform_detection_cdf(self, t_normalized: float) -> float:
        """CDF for uniform detection probability throughout execution"""
        # Linear growth: uniform detection probability
        return t_normalized
    
    def _late_detection_cdf(self, t_normalized: float) -> float:
        """CDF for actions detected late in execution"""
        # Power function: detection probability increases toward end
        return t_normalized ** 2
    
    def _immediate_detection_cdf(self, t_normalized: float) -> float:
        """CDF for actions with high immediate detection (e.g., data exfiltration)"""
        # Very early detection for obvious malicious activity
        return min(1.0, 2 * t_normalized)
    
    def _very_late_detection_cdf(self, t_normalized: float) -> float:
        """CDF for evasive actions"""
        # Cubic function: very low detection until very end
        return t_normalized ** 3
    
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) - the probability that action a on node n is detected
        
        Args:
            action: The action being performed
            target: The target node
            actor_access: Actor's access level to the target
            actor: The actor performing the action
            
        Returns:
            Detection probability ϱ(a, π̂(n)) ∈ [0, 1]
        """
        # Get base detection probability for this action type
        action_name = action.name.lower()
        base_prob = 0.2  # Default
        
        for action_type, prob in self.base_action_detection.items():
            if action_type in action_name:
                base_prob = prob
                break
        
        # Modify based on node properties π̂(n)
        node_properties = getattr(target, 'properties', {})
        detection_modifier = 0.0
        
        # Check endpoint protection
        endpoint_protection = node_properties.get('endpoint_protection', 'none')
        if isinstance(endpoint_protection, str):
            detection_modifier += self.detection_factors['endpoint_protection'].get(endpoint_protection, 0.0)
        
        # Check network monitoring
        monitoring = node_properties.get('network_monitoring', 'none')
        if isinstance(monitoring, str):
            detection_modifier += self.detection_factors['network_monitoring'].get(monitoring, 0.0)
        
        # Check system criticality
        criticality = node_properties.get('critical', False)
        if criticality:
            detection_modifier += self.detection_factors['criticality']['high']
        else:
            detection_modifier += self.detection_factors['criticality']['low']
        
        # Check internet exposure
        if node_properties.get('exposed_to_internet', False):
            detection_modifier += self.detection_factors['exposure']['internet_exposed']
        else:
            detection_modifier += self.detection_factors['exposure']['internal_only']
        
        # Final detection probability ϱ(a, π̂(n))
        detection_probability = max(0.0, min(1.0, base_prob + detection_modifier))
        
        logger.debug(f"Detection probability for {action.name} on {target.id}: {detection_probability:.3f}")
        return detection_probability
    
    def sample_detection_time(self, action, duration: float, detection_probability: float) -> Optional[float]:
        """
        Sample detection time using the TIM paper's CDF approach
        
        Args:
            action: The action being performed
            duration: Action duration da
            detection_probability: ϱ(a, π̂(n))
            
        Returns:
            Detection time relative to action start, or None if not detected
        """
        # First, determine if detection occurs at all
        if random.random() >= detection_probability:
            return None
        
        # If detection occurs, sample the timing using CDF
        action_name = action.name.lower()
        
        # Select appropriate CDF function
        cdf_func = self.cdf_functions.get('uniform_detection_cdf', self._uniform_detection_cdf)
        for action_type, func in self.cdf_functions.items():
            if action_type in action_name:
                cdf_func = func
                break
        
        # Sample from the CDF using inverse transform sampling
        # Generate random value and find corresponding time
        random_value = random.random()
        
        # Binary search to find t such that Fa(t) ≈ random_value
        t_normalized = self._inverse_cdf_sampling(cdf_func, random_value)
        
        # Convert to actual time
        detection_time = t_normalized * duration
        
        logger.debug(f"Sampled detection time for {action.name}: {detection_time:.2f} / {duration:.2f}")
        return detection_time
    
    def _inverse_cdf_sampling(self, cdf_func: Callable, target_value: float, tolerance: float = 0.001) -> float:
        """
        Use binary search to find t such that CDF(t) ≈ target_value
        """
        low, high = 0.0, 1.0
        
        while high - low > tolerance:
            mid = (low + high) / 2
            cdf_value = cdf_func(mid)
            
            if cdf_value < target_value:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2
    
    def calculate_cumulative_detection_probability(self, action, target, actor_access: str, 
                                                 time_elapsed: float, total_duration: float) -> float:
        """
        Calculate the cumulative detection probability at time t during action execution
        
        From TIM paper: "the probability that the execution of the action is detected 
        by tstart + t is Fa(t/da) · ϱ(a, π̂(n))"
        
        Args:
            action: The action being performed
            target: The target node
            actor_access: Actor's access level
            time_elapsed: Time elapsed since action start
            total_duration: Total action duration da
            
        Returns:
            Cumulative detection probability at time t
        """
        # Get base detection probability ϱ(a, π̂(n))
        base_detection_prob = self.calculate_detection_probability(action, target, actor_access, None)
        
        # Get normalized time t/da
        t_normalized = min(1.0, time_elapsed / total_duration)
        
        # Get appropriate CDF function Fa
        action_name = action.name.lower()
        cdf_func = self.cdf_functions.get('uniform_detection_cdf', self._uniform_detection_cdf)
        for action_type, func in self.cdf_functions.items():
            if action_type in action_name:
                cdf_func = func
                break
        
        # Calculate Fa(t/da) · ϱ(a, π̂(n))
        cdf_value = cdf_func(t_normalized)
        cumulative_prob = cdf_value * base_detection_prob
        
        return cumulative_prob
    
    def should_detect_action_at_time(self, action, target, actor_access: str, 
                                   time_elapsed: float, total_duration: float) -> bool:
        """
        Determine if action should be detected at specific time during execution
        
        This implements the TIM paper's detection model where detection can occur
        at any time during the interval [tstart, tstart + da)
        """
        cumulative_prob = self.calculate_cumulative_detection_probability(
            action, target, actor_access, time_elapsed, total_duration
        )
        
        # Sample whether detection occurs at this specific moment
        # This is an approximation of the continuous detection process
        return random.random() < cumulative_prob
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of detection configuration"""
        return {
            'detection_engine': 'TIM Paper Compliant',
            'base_action_types': len(self.base_action_detection),
            'cdf_functions': len(self.cdf_functions),
            'detection_factors': {
                'endpoint_protection': len(self.detection_factors['endpoint_protection']),
                'network_monitoring': len(self.detection_factors['network_monitoring']),
                'criticality_levels': len(self.detection_factors['criticality']),
                'exposure_types': len(self.detection_factors['exposure'])
            }
        }

# Example usage for testing
if __name__ == "__main__":
    # Test the detection engine
    engine = TIMDetectionEngine()
    
    # Mock objects for testing
    class MockAction:
        def __init__(self, name):
            self.name = name
            self.duration = 2.0
    
    class MockTarget:
        def __init__(self):
            self.id = "test_node"
            self.properties = {
                'endpoint_protection': 'Sophos',
                'network_monitoring': 'SIEM',
                'critical': True,
                'exposed_to_internet': True
            }
    
    action = MockAction("vulnerability_scan")
    target = MockTarget()
    
    detection_prob = engine.calculate_detection_probability(action, target, "VISIBLE", None)
    print(f"Detection probability: {detection_prob:.3f}")
    
    detection_time = engine.sample_detection_time(action, action.duration, detection_prob)
    print(f"Detection time: {detection_time}")
    
    print("Detection summary:", engine.get_detection_summary())
