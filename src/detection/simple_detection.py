"""
Simple TIM Paper-Compliant Detection Engine

This module implements ONLY what the TIM paper actually specifies:
1. Detection probability function ϱ(a, π̂(n)) → [0, 1]
2. Cumulative distribution function Fa with Fa(0) = 0 and Fa(1) = 1
3. Detection timing formula: Fa(t/da) · ϱ(a, π̂(n))

No additional domain knowledge or specific mappings are included.
This is the pure mathematical framework from the TIM paper.

Reference: Section 4.5 "Detection of malicious activities" in TIM paper
"""

import random
import logging
from typing import Dict, Any, Callable, Optional

logger = logging.getLogger(__name__)

class SimpleTIMDetectionEngine:
    """
    Minimal TIM paper-compliant detection engine.
    
    Implements only what the paper specifies:
    - ϱ(a, π̂(n)): Detection probability function
    - Fa(t): Cumulative distribution function with Fa(0)=0, Fa(1)=1  
    - Fa(t/da) · ϱ(a, π̂(n)): Detection timing formula
    
    All specific mappings are configurable parameters.
    """
    
    def __init__(self, default_detection_probability: float = 0.2, 
                 default_cdf_function: str = "linear"):
        """
        Initialize with configurable defaults.
        
        Args:
            default_detection_probability: Default ϱ(a, π̂(n)) value
            default_cdf_function: Default CDF type ("linear", "exponential", "power")
        """
        self.default_detection_probability = default_detection_probability
        self.default_cdf_function = default_cdf_function
        
        # Configurable detection probabilities per action-node combination
        # Format: {(action_name, node_property_hash): probability}
        self.detection_probability_map = {}
        
        # Configurable CDF functions per action
        # Format: {action_name: cdf_function}
        self.cdf_function_map = {}
        
        logger.info(f"Initialized SimpleTIMDetectionEngine with default probability {default_detection_probability}")
    
    def configure_detection_probability(self, action_name: str, node_properties: Dict[str, Any], 
                                      probability: float):
        """
        Configure detection probability ϱ(a, π̂(n)) for specific action-node combination.
        
        Args:
            action_name: Name of the action 'a'
            node_properties: Node properties π̂(n) 
            probability: Detection probability ϱ(a, π̂(n)) ∈ [0, 1]
        """
        if not (0 <= probability <= 1):
            raise ValueError(f"Detection probability must be in [0, 1], got {probability}")
        
        # Create a simple hash of node properties for lookup
        property_hash = hash(frozenset(node_properties.items()))
        key = (action_name, property_hash)
        
        self.detection_probability_map[key] = probability
        logger.debug(f"Configured ϱ({action_name}, π̂(n)) = {probability}")
    
    def configure_cdf_function(self, action_name: str, cdf_function: Callable[[float], float]):
        """
        Configure CDF function Fa(t) for specific action.
        
        Args:
            action_name: Name of the action
            cdf_function: Function Fa(t) with Fa(0)=0, Fa(1)=1
        """
        # Validate CDF constraints
        if abs(cdf_function(0.0)) > 1e-6:
            raise ValueError(f"CDF function must satisfy Fa(0) = 0, got Fa(0) = {cdf_function(0.0)}")
        if abs(cdf_function(1.0) - 1.0) > 1e-6:
            raise ValueError(f"CDF function must satisfy Fa(1) = 1, got Fa(1) = {cdf_function(1.0)}")
        
        self.cdf_function_map[action_name] = cdf_function
        logger.debug(f"Configured CDF function for action {action_name}")
    
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) - detection probability for action a on node with properties π̂(n).
        
        This is the core TIM paper function: ϱ : A(attack) × Π̂ → [0, 1]
        
        Args:
            action: The action 'a'
            target: The target node with properties π̂(n)
            actor_access: Actor's access level (not used in basic TIM model)
            actor: The actor (not used in basic TIM model)
            
        Returns:
            Detection probability ϱ(a, π̂(n)) ∈ [0, 1]
        """
        action_name = action.name
        
        # Get node properties π̂(n)
        if hasattr(target, 'properties'):
            node_properties = target.properties
        else:
            node_properties = {}
        
        # Look up configured detection probability
        property_hash = hash(frozenset(node_properties.items()))
        key = (action_name, property_hash)
        
        if key in self.detection_probability_map:
            probability = self.detection_probability_map[key]
            logger.debug(f"Found configured ϱ({action_name}, π̂(n)) = {probability}")
            return probability
        else:
            # Use default probability
            logger.debug(f"Using default ϱ({action_name}, π̂(n)) = {self.default_detection_probability}")
            return self.default_detection_probability
    
    def get_cdf_function(self, action) -> Callable[[float], float]:
        """
        Get cumulative distribution function Fa(t) for action a.
        
        Returns function Fa with constraints:
        - Fa(0) = 0
        - Fa(1) = 1
        - Fa is non-decreasing
        
        Args:
            action: The action 'a'
            
        Returns:
            CDF function Fa(t) : [0, 1] → [0, 1]
        """
        action_name = action.name
        
        if action_name in self.cdf_function_map:
            return self.cdf_function_map[action_name]
        else:
            # Return default CDF function
            return self._get_default_cdf_function()
    
    def _get_default_cdf_function(self) -> Callable[[float], float]:
        """Get default CDF function based on configuration."""
        if self.default_cdf_function == "linear":
            return lambda t: t  # Linear: Fa(t) = t
        elif self.default_cdf_function == "exponential":
            import math
            return lambda t: 1 - math.exp(-2 * t)  # Exponential growth
        elif self.default_cdf_function == "power":
            return lambda t: t ** 2  # Power function: Fa(t) = t²
        else:
            # Default to linear
            return lambda t: t
    
    def calculate_cumulative_detection_probability(self, action, target, actor_access: str,
                                                 time_elapsed: float, total_duration: float) -> float:
        """
        Calculate cumulative detection probability at time t.
        
        This implements the core TIM paper formula:
        P(detected by time t) = Fa(t/da) · ϱ(a, π̂(n))
        
        Args:
            action: The action 'a'
            target: The target node with properties π̂(n)
            actor_access: Actor's access level (not used in basic model)
            time_elapsed: Time elapsed since action start
            total_duration: Total action duration da
            
        Returns:
            Cumulative detection probability Fa(t/da) · ϱ(a, π̂(n))
        """
        # Get detection probability ϱ(a, π̂(n))
        detection_prob = self.calculate_detection_probability(action, target, actor_access, None)
        
        # Get normalized time t/da
        if total_duration <= 0:
            return 0.0
        t_normalized = min(1.0, max(0.0, time_elapsed / total_duration))
        
        # Get CDF function Fa
        cdf_function = self.get_cdf_function(action)
        
        # Calculate Fa(t/da)
        cdf_value = cdf_function(t_normalized)
        
        # Return TIM paper formula: Fa(t/da) · ϱ(a, π̂(n))
        cumulative_prob = cdf_value * detection_prob
        
        logger.debug(f"Cumulative detection: Fa({t_normalized:.3f}) · ϱ = {cdf_value:.3f} · {detection_prob:.3f} = {cumulative_prob:.3f}")
        return cumulative_prob
    
    def sample_detection_time(self, action, duration: float, detection_probability: float) -> Optional[float]:
        """
        Sample detection time using the TIM paper's approach.
        
        Args:
            action: The action being performed
            duration: Action duration da
            detection_probability: ϱ(a, π̂(n))
            
        Returns:
            Detection time relative to action start, or None if not detected
        """
        # First determine if detection occurs at all
        if random.random() >= detection_probability:
            return None
        
        # If detection occurs, sample timing using inverse CDF sampling
        cdf_function = self.get_cdf_function(action)
        
        # Generate random value for inverse transform sampling
        random_value = random.random()
        
        # Find t such that Fa(t) ≈ random_value using binary search
        t_normalized = self._inverse_cdf_sampling(cdf_function, random_value)
        
        # Convert to actual time
        detection_time = t_normalized * duration
        
        logger.debug(f"Sampled detection time: {detection_time:.3f} / {duration:.3f}")
        return detection_time
    
    def _inverse_cdf_sampling(self, cdf_func: Callable[[float], float], 
                            target_value: float, tolerance: float = 0.001) -> float:
        """
        Use binary search to find t such that CDF(t) ≈ target_value.
        
        This implements inverse transform sampling for the CDF.
        """
        low, high = 0.0, 1.0
        
        # Binary search for inverse CDF
        while high - low > tolerance:
            mid = (low + high) / 2
            cdf_value = cdf_func(mid)
            
            if cdf_value < target_value:
                low = mid
            else:
                high = mid
        
        return (low + high) / 2
    
    def should_detect_action_at_time(self, action, target, actor_access: str,
                                   time_elapsed: float, total_duration: float) -> bool:
        """
        Determine if action should be detected at specific time during execution.
        
        Uses the TIM paper's cumulative detection probability.
        """
        cumulative_prob = self.calculate_cumulative_detection_probability(
            action, target, actor_access, time_elapsed, total_duration
        )
        
        return random.random() < cumulative_prob
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        return {
            'detection_engine': 'Simple TIM Paper Compliant',
            'default_detection_probability': self.default_detection_probability,
            'default_cdf_function': self.default_cdf_function,
            'configured_detection_probabilities': len(self.detection_probability_map),
            'configured_cdf_functions': len(self.cdf_function_map),
            'paper_compliance': 'Minimal - Only TIM paper requirements'
        }

# Example usage demonstrating TIM paper compliance
if __name__ == "__main__":
    # Test the minimal TIM detection engine
    engine = SimpleTIMDetectionEngine(default_detection_probability=0.3, 
                                    default_cdf_function="linear")
    
    # Mock objects for testing
    class MockAction:
        def __init__(self, name):
            self.name = name
            self.duration = 2.0
    
    class MockTarget:
        def __init__(self, properties):
            self.id = "test_node"
            self.properties = properties
    
    # Test basic functionality
    action = MockAction("test_attack")
    target = MockTarget({'critical': True, 'monitoring': 'basic'})
    
    # Test detection probability calculation
    detection_prob = engine.calculate_detection_probability(action, target, "VISIBLE", None)
    print(f"Default detection probability: {detection_prob}")
    
    # Configure specific detection probability
    engine.configure_detection_probability("test_attack", target.properties, 0.7)
    configured_prob = engine.calculate_detection_probability(action, target, "VISIBLE", None)
    print(f"Configured detection probability: {configured_prob}")
    
    # Test cumulative detection probability (TIM paper formula)
    cumulative_prob = engine.calculate_cumulative_detection_probability(
        action, target, "VISIBLE", 1.0, 2.0
    )
    print(f"Cumulative detection probability at t=1.0/2.0: {cumulative_prob}")
    
    # Test detection time sampling
    detection_time = engine.sample_detection_time(action, action.duration, configured_prob)
    print(f"Sampled detection time: {detection_time}")
    
    print("\nConfiguration summary:")
    print(engine.get_configuration_summary())
