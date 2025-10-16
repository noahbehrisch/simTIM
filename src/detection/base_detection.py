from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class BaseDetectionEngine(ABC):
    """
    Abstract base class for TIM paper-compliant detection engines.
    
    All detection engines must implement the TIM paper's detection model:
    1. ϱ(a, π̂(n)) - detection probability function
    2. Fa(t) - cumulative distribution function
    3. Detection timing using Fa(t/da) · ϱ(a, π̂(n))
    """
    
    def __init__(self):
        """Initialize the detection engine."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) - the probability that action a on node n is detected.
        
        From TIM paper Section 4.5:
        "Let ϱ : A(attack) × Π̂ → [0, 1] denote the detection probability function."
        
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
        
        Args:
            action: The action 'a'
            
        Returns:
            CDF function Fa: [0, 1] → [0, 1] with Fa(0) = 0, Fa(1) = 1
        """
        pass
    
    def calculate_cumulative_detection_probability(self, action, target, actor_access: str,
                                                   time_elapsed: float, total_duration: float) -> float:
        """
        Calculate cumulative detection probability at time t during action execution.
        
        From TIM paper Section 4.5:
        "for any 0 ≤ t ≤ da, the probability that the execution of the action is 
        detected by tstart + t is Fa(t/da) · ϱ(a, π̂(n))"
        
        This is the core TIM paper formula for temporal detection.
        
        Args:
            action: The action 'a'
            target: The target node with properties π̂(n)
            actor_access: Actor's access level
            time_elapsed: Time elapsed since action start (t)
            total_duration: Total action duration (da)
            
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
        
        self.logger.debug(
            f"Cumulative detection at t={time_elapsed:.2f}/{total_duration:.2f}: "
            f"Fa({t_normalized:.3f}) · ϱ = {cdf_value:.3f} · {detection_prob:.3f} = {cumulative_prob:.3f}"
        )
        
        return cumulative_prob
    
    def sample_detection_time(self, action, duration: float, detection_probability: float) -> Optional[float]:
        """
        Sample detection time using the TIM paper's CDF-based approach.
        
        First determines if detection occurs (with probability ϱ), then samples
        the timing using inverse transform sampling on Fa(t).
        
        Args:
            action: The action being performed
            duration: Action duration da
            detection_probability: ϱ(a, π̂(n))
            
        Returns:
            Detection time relative to action start, or None if not detected
        """
        import random
        
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
        
        self.logger.debug(
            f"Sampled detection time for {action.name}: "
            f"{detection_time:.2f} / {duration:.2f} (t_norm={t_normalized:.3f})"
        )
        
        return detection_time
    
    def _inverse_cdf_sampling(self, cdf_func: Callable[[float], float],
                            target_value: float, tolerance: float = 0.001) -> float:
        """
        Use binary search to find t such that CDF(t) ≈ target_value.
        
        This implements inverse transform sampling for the CDF.
        
        Args:
            cdf_func: The CDF function Fa(t)
            target_value: Target CDF value (random sample)
            tolerance: Convergence tolerance
            
        Returns:
            Time t such that Fa(t) ≈ target_value
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
        
        Uses the TIM paper's cumulative detection probability formula.
        
        Args:
            action: The action being performed
            target: The target node
            actor_access: Actor's access level
            time_elapsed: Time elapsed since action start
            total_duration: Total action duration
            
        Returns:
            True if action should be detected at this time
        """
        import random
        
        cumulative_prob = self.calculate_cumulative_detection_probability(
            action, target, actor_access, time_elapsed, total_duration
        )
        
        return random.random() < cumulative_prob
    
    @abstractmethod
    def get_configuration_summary(self) -> Dict[str, Any]:
        """
        Get summary of detection engine configuration.
        
        Returns:
            Dictionary with configuration details
        """
        pass
    
    def validate_cdf(self, cdf_func: Callable[[float], float], tolerance: float = 1e-6) -> bool:
        """
        Validate that a CDF function satisfies TIM paper constraints:
        - Fa(0) = 0
        - Fa(1) = 1
        - Fa is non-decreasing
        
        Args:
            cdf_func: The CDF function to validate
            tolerance: Numerical tolerance for equality checks
            
        Returns:
            True if valid, False otherwise
        """
        # Check Fa(0) = 0
        if abs(cdf_func(0.0)) > tolerance:
            self.logger.error(f"CDF constraint violated: Fa(0) = {cdf_func(0.0)} ≠ 0")
            return False
        
        # Check Fa(1) = 1
        if abs(cdf_func(1.0) - 1.0) > tolerance:
            self.logger.error(f"CDF constraint violated: Fa(1) = {cdf_func(1.0)} ≠ 1")
            return False
        
        # Check non-decreasing (sample at several points)
        prev_value = 0.0
        for t in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            current_value = cdf_func(t)
            if current_value < prev_value - tolerance:
                self.logger.error(
                    f"CDF not non-decreasing: Fa({t}) = {current_value} < previous value {prev_value}"
                )
                return False
            prev_value = current_value
        
        return True
