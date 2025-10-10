"""
Simple TIM Detection Engine - Pure Paper Implementation

This engine is a 1:1 implementation of Section 4.5 from the TIM paper.
It implements ONLY what the paper specifies, with no additional domain knowledge.

From TIM paper Section 4.5 "Detection of malicious activities":
1. ϱ(a, π̂(n)) - detection probability function: A(attack) × Π̂ → [0, 1]
2. Fa(t) - cumulative distribution function with Fa(0) = 0 and Fa(1) = 1
3. Detection timing: P(detected by time t) = Fa(t/da) · ϱ(a, π̂(n))

Reference: "Time is money: A temporal model of cybersecurity" by Zoltán Ádám Mann
"""

import math
from typing import Dict, Any, Callable
import logging
from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class SimpleTIMDetectionEngine(BaseDetectionEngine):
    """
    Pure implementation of TIM paper Section 4.5 detection model.
    
    Provides sensible defaults for ϱ(a, π̂(n)) and Fa(t) but can be fully configured.
    No cybersecurity domain knowledge - just the mathematical framework.
    """
    
    def __init__(self, 
                 default_detection_probability: float = 0.3,
                 default_cdf_type: str = "uniform"):
        """
        Initialize SimpleTIM detection engine.
        
        Args:
            default_detection_probability: Default ϱ(a, π̂(n)) for unconfigured actions
            default_cdf_type: Default CDF pattern ("uniform", "early", "late", "exponential")
        """
        super().__init__()
        
        self.default_detection_probability = default_detection_probability
        self.default_cdf_type = default_cdf_type
        
        # Storage for configured detection probabilities
        self.detection_probability_map: Dict[tuple, float] = {}
        
        # Storage for configured CDF functions
        self.cdf_function_map: Dict[str, Callable[[float], float]] = {}
        
        # Pre-defined CDF patterns (TIM paper compliant)
        self._initialize_cdf_patterns()
        
        logger.info(
            f"Initialized SimpleTIM detection engine "
            f"(default ϱ={default_detection_probability}, CDF={default_cdf_type})"
        )
    
    def _initialize_cdf_patterns(self):
        """Initialize standard CDF patterns that satisfy Fa(0)=0, Fa(1)=1."""
        self.cdf_patterns = {
            "uniform": lambda t: t,
            "early": lambda t: min(1.0, 1 - math.exp(-3 * t) * (1 - t)),  # Ensure Fa(1) = 1
            "late": lambda t: t ** 2,
            "very_late": lambda t: t ** 3,
            "exponential": lambda t: min(1.0, t * (2 - math.exp(-2 * t))),  # Ensure Fa(1) = 1
        }
        
        # Validate all patterns
        for pattern_name, cdf_func in self.cdf_patterns.items():
            if not self.validate_cdf(cdf_func):
                logger.error(f"CDF pattern '{pattern_name}' failed validation!")
    
    def configure_detection_probability(self, 
                                       action_name: str, 
                                       node_properties: Dict[str, Any],
                                       probability: float):
        """Configure ϱ(a, π̂(n)) for specific action-node combination."""
        if not (0 <= probability <= 1):
            raise ValueError(f"Detection probability must be in [0, 1], got {probability}")
        
        property_sig = self._create_property_signature(node_properties)
        key = (action_name, property_sig)
        
        self.detection_probability_map[key] = probability
        logger.debug(f"Configured ϱ({action_name}, π̂) = {probability}")
    
    def configure_cdf_pattern(self, action_name: str, pattern_name: str):
        """Configure action to use a pre-defined CDF pattern."""
        if pattern_name not in self.cdf_patterns:
            raise ValueError(
                f"Unknown CDF pattern '{pattern_name}'. "
                f"Available: {list(self.cdf_patterns.keys())}"
            )
        
        self.cdf_function_map[action_name] = self.cdf_patterns[pattern_name]
        logger.debug(f"Configured action {action_name} to use CDF pattern '{pattern_name}'")
    
    def _create_property_signature(self, properties: Dict[str, Any]) -> str:
        """Create a stable signature from node properties."""
        if not properties:
            return ""
        
        sorted_items = sorted(properties.items())
        signature_parts = []
        for key, value in sorted_items:
            if isinstance(value, (list, dict)):
                signature_parts.append(f"{key}={str(value)}")
            else:
                signature_parts.append(f"{key}={value}")
        
        return "|".join(signature_parts)
    
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) - detection probability function.
        
        Implementation of TIM paper Section 4.5:
        "Let ϱ : A(attack) × Π̂ → [0, 1] denote the detection probability function."
        """
        action_name = action.name
        node_properties = getattr(target, 'properties', {})
        
        # Create property signature
        property_sig = self._create_property_signature(node_properties)
        key = (action_name, property_sig)
        
        # Look up configured detection probability
        if key in self.detection_probability_map:
            probability = self.detection_probability_map[key]
            logger.debug(f"Found configured ϱ({action_name}, π̂) = {probability}")
            return probability
        
        # Use default probability
        logger.debug(f"Using default ϱ({action_name}, π̂) = {self.default_detection_probability}")
        return self.default_detection_probability
    
    def get_cdf_function(self, action) -> Callable[[float], float]:
        """
        Get Fa(t) cumulative distribution function for action.
        
        Implementation of TIM paper Section 4.5:
        "detection time follows a random distribution with cumulative distribution
        function Fa with Fa(0) = 0 and Fa(1) = 1"
        """
        action_name = action.name
        
        # Check for configured CDF
        if action_name in self.cdf_function_map:
            return self.cdf_function_map[action_name]
        
        # Use default pattern
        if self.default_cdf_type in self.cdf_patterns:
            return self.cdf_patterns[self.default_cdf_type]
        
        # Fallback to uniform
        logger.warning(f"Unknown default CDF type '{self.default_cdf_type}', using uniform")
        return self.cdf_patterns["uniform"]
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        return {
            'engine_type': 'SimpleTIM',
            'paper_section': '4.5',
            'compliance': 'Pure TIM paper implementation',
            'default_detection_probability': self.default_detection_probability,
            'default_cdf_type': self.default_cdf_type,
            'configured_detection_probabilities': len(self.detection_probability_map),
            'configured_cdf_functions': len(self.cdf_function_map),
            'available_cdf_patterns': list(self.cdf_patterns.keys()),
            'features': [
                'ϱ(a, π̂(n)) detection probability function',
                'Fa(t) cumulative distribution function',
                'Fa(t/da) · ϱ(a, π̂(n)) temporal detection',
                'Configurable detection probabilities',
                'Multiple CDF patterns',
                'No domain-specific knowledge'
            ]
        }
