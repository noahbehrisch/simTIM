import math
from typing import Dict, Any, Callable
import logging
from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class SimpleTIMDetectionEngine(BaseDetectionEngine):
    """
    Pure implementation of TIM paper Section 4.5 detection model.
    """
    
    def __init__(self, 
                 default_detection_probability: float = 0.3,
                 default_cdf_type: str = "uniform"):

        super().__init__()
        
        self.default_detection_probability = default_detection_probability
        self.default_cdf_type = default_cdf_type
        
        self.cdf_function_map: Dict[str, Callable[[float], float]] = {}
        
        self._initialize_cdf_patterns()
        
        logger.info(
            f"Initialized SimpleTIM detection engine "
            f"(fallback ϱ={default_detection_probability}, CDF={default_cdf_type})"
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
    
    def configure_cdf_pattern(self, action_name: str, pattern_name: str):
        """Configure action to use a pre-defined CDF pattern."""
        if pattern_name not in self.cdf_patterns:
            raise ValueError(
                f"Unknown CDF pattern '{pattern_name}'. "
                f"Available: {list(self.cdf_patterns.keys())}"
            )
        
        self.cdf_function_map[action_name] = self.cdf_patterns[pattern_name]
        logger.debug(f"Configured action {action_name} to use CDF pattern '{pattern_name}'")
    
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n))
        """
        try:
            probability = action.get_detection_probability(target, actor_access, actor or "unknown")
            logger.debug(f"Action '{action.name}' provided ϱ(a, π̂(n)) = {probability}")
            return max(0.0, min(1.0, probability))  # Ensure [0,1] range
        except Exception as e:
            logger.warning(f"Action '{action.name}' detection function failed: {e}")
            logger.debug(f"Falling back to default ϱ = {self.default_detection_probability}")
            return self.default_detection_probability
    
    def get_cdf_function(self, action) -> Callable[[float], float]:
        """
        Get Fa(t) cumulative distribution function for action.
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
        return {
            'engine_type': 'SimpleTIM',
            'paper_section': '4.5',
            'compliance': 'Pure TIM paper implementation using action-defined detection',
            'detection_source': 'action.detection_probability() functions',
            'fallback_detection_probability': self.default_detection_probability,
            'default_cdf_type': self.default_cdf_type,
            'configured_cdf_functions': len(self.cdf_function_map),
            'available_cdf_patterns': list(self.cdf_patterns.keys()),
        }
