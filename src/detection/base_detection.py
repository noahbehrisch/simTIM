from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class BaseDetectionEngine(ABC):
    """
    Abstract base class for TIM paper-compliant detection engines.
    
    All detection engines must implement the TIM paper's detection model (Section 4.5):
    1. ϱ(a, π̂(n)) - detection probability function
    2. Fa(t) - cumulative distribution function with Fa(0)=0, Fa(1)=1
    3. Detection timing calculation implementing: Fa(t/da) · ϱ(a, π̂(n))
    
    Each engine defines a different CDF function Fa(t), resulting in different
    detection time distributions (uniform, early bias, late bias, etc.)
    """
    
    def __init__(self):
        """Initialize the detection engine with logging."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) - the probability that action a on node n is detected.
        
        From TIM paper Section 4.5:
        "Let ϱ : A(attack) × Π̂ → [0, 1] denote the detection probability function."
        
        This is the base probability that detection occurs SOMETIME during the
        action execution. The actual timing is then determined by the CDF.
        
        Args:
            action: The action 'a' being performed
            target: The target node with properties π̂(n)
            actor_access: Actor's current access level to the target
            actor: The actor performing the action
            
        Returns:
            Detection probability ϱ(a, π̂(n)) ∈ [0, 1]
        """
        pass
    
    @abstractmethod
    def get_cdf_function(self, action) -> Callable[[float], float]:
        """
        Get cumulative distribution function Fa(t) for action a.
        
        From TIM paper Section 4.5:
        "detection time follows a random distribution with cumulative distribution
        function Fa with Fa(0) = 0 and Fa(1) = 1"
        
        The CDF determines the timing distribution of detection within the action duration.
        Different engines implement different CDFs:
        - Uniform: Fa(t) = t
        - Exponential: Fa(t) = 1 - e^(-λt) 
        - Polynomial: Fa(t) = t^n
        
        Args:
            action: The action 'a' (may be used for action-specific CDFs)
            
        Returns:
            CDF function Fa: [0, 1] → [0, 1] with Fa(0) = 0, Fa(1) = 1
        """
        pass
    
    @abstractmethod
    def calculate_detection_time(self, action, target, actor_access: str, actor, 
                                duration: float) -> Optional[float]:
        """
        Calculate when (if at all) an attack action will be detected.
        
        This is the core method that each detection engine must implement.
        It combines detection probability ϱ and timing distribution Fa to determine
        if and when an attack is detected.
        
        From TIM paper Section 4.5:
        "Let x ∈ X(att) be an attacker that starts an action a ∈ A(x) at time tstart...
        ϱ(a, π̂(n)) is the probability that the defender detects sometime between 
        tstart and tstart + da that a is being executed."
        
        "for any 0 ≤ t ≤ da, the probability that the execution of the action is 
        detected by tstart + t is Fa(t/da) · ϱ(a, π̂(n))"
        
        Args:
            action: The action being performed
            target: The target node with properties π̂(n)
            actor_access: Actor's access level to the target
            actor: The actor performing the action
            duration: Action duration da
            
        Returns:
            Detection time in [0, duration] if detected, None otherwise
        """
        pass
    
    @abstractmethod
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get summary of detection engine configuration.
        
        Should include at minimum:
        - engine_type: Name of the engine
        - detection_strategy: Brief description
        - cdf_formula: Mathematical formula for Fa(t)
        
        Returns:
            Dictionary with configuration details
        """
        pass
    
    def validate_cdf(self, cdf_func: Callable[[float], float], tolerance: float = 0.02) -> bool:
        """
        Validate that a CDF function satisfies TIM paper constraints.
        
        TIM paper Section 4.5 requires:
        - Fa(0) = 0
        - Fa(1) = 1
        - Fa is non-decreasing
        
        Args:
            cdf_func: The CDF function to validate
            tolerance: Numerical tolerance for equality checks (default 0.02 for practical CDFs)
            
        Returns:
            True if valid, False otherwise
        """
        # Check Fa(0) = 0
        if abs(cdf_func(0.0)) > tolerance:
            self.logger.error(f"CDF constraint violated: Fa(0) = {cdf_func(0.0):.6f} ≠ 0")
            return False
        
        # Check Fa(1) ≈ 1 (allow small tolerance for numerical approximations)
        if abs(cdf_func(1.0) - 1.0) > tolerance:
            self.logger.warning(
                f"CDF constraint: Fa(1) = {cdf_func(1.0):.6f} "
                f"(within {tolerance} tolerance of 1)"
            )
        
        # Check non-decreasing (sample at several points)
        prev_value = 0.0
        for t in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            current_value = cdf_func(t)
            if current_value < prev_value - tolerance:
                self.logger.error(
                    f"CDF not non-decreasing: Fa({t}) = {current_value:.6f} < "
                    f"previous value {prev_value:.6f}"
                )
                return False
            prev_value = current_value
        
        return True
