import math
import random
from typing import Dict, Any, Callable, Optional
import logging
from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class ExponentialDetectionEngine(BaseDetectionEngine):
    """
    Exponential Detection Engine - Fa(t) = 1 - e^(-λt)
    
    Detection Time Strategy: Exponential CDF (Early Detection Bias)
    ================================================================
    Implements exponential CDF favoring early detection:
    - Fa(t) = 1 - e^(-λt) where λ is chosen so Fa(1) = 1
    - λ ≈ 5 gives good properties: Fa(1) ≈ 0.9933
    - High detection probability in early phases
    - Models "signature-based" detection systems
    
    From TIM Paper Section 4.5:
    "If the execution of the action is detected, the detection time follows 
    a random distribution with cumulative distribution function Fa"
    
    With Fa(t) = 1 - e^(-5t):
    - At t=0: 0% cumulative detection probability
    - At t=0.2: ~63% cumulative detection probability
    - At t=0.5: ~92% cumulative detection probability
    - At t=1: ~99% cumulative detection probability
    
    Characteristics:
    - Strong bias toward early detection
    - Realistic for known attack patterns
    - O(log n) computation - binary search for inverse CDF
    - Models IDS with signature databases
    
    Use Case: Environments with good signature-based detection (IDS/IPS),
             well-known attack patterns, strong monitoring
    """
    
    def __init__(self, lambda_param: float = 4.605, default_detection_probability: float = 0.4):
        """
        Initialize Exponential Detection Engine.
        
        Args:
            lambda_param: Rate parameter λ for exponential distribution (higher = earlier detection)
                         Default 4.605 ensures Fa(1) = 1 - e^(-4.605) ≈ 0.99 (close to 1)
            default_detection_probability: Fallback ϱ(a, π̂(n))
        """
        super().__init__()
        self.lambda_param = lambda_param
        self.default_detection_probability = default_detection_probability
        
        # Note: For exponential CDF, Fa(1) = 1 - e^(-λ)
        # With λ=4.605, Fa(1) ≈ 0.99, which is acceptable for TIM paper constraints
        
        logger.info(
            f"Initialized Exponential Detection Engine: Fa(t) = 1 - e^(-{lambda_param:.2f}t) "
            f"(Fa(1)≈{1-math.exp(-lambda_param):.4f}, default ϱ={default_detection_probability})"
        )
    
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) - base detection probability.
        
        For exponential engine, this might be higher due to early detection capability.
        """
        try:
            probability = action.get_detection_probability(target, actor_access, actor or "unknown")
            return max(0.0, min(1.0, probability))
        except Exception as e:
            logger.warning(f"Action '{action.name}' detection failed: {e}, using default")
            return self.default_detection_probability
    
    def get_cdf_function(self, action) -> Callable[[float], float]:
        """
        Return exponential CDF: Fa(t) = 1 - e^(-λt)
        
        Normalized so Fa(1) ≈ 1:
        - With λ=5: Fa(1) = 1 - e^(-5) ≈ 0.9933
        - Close enough to 1 for practical purposes
        
        Properties:
        - Fa(0) = 1 - e^0 = 0 ✓
        - Fa(1) ≈ 1 ✓
        - Monotonically increasing ✓
        """
        lambda_val = self.lambda_param
        return lambda t: 1.0 - math.exp(-lambda_val * t)
    
    def calculate_detection_time(self, action, target, actor_access: str, actor, 
                                duration: float) -> Optional[float]:
        """
        Calculate detection time using exponential CDF.
        
        Algorithm (TIM paper Section 4.5):
        1. Calculate ϱ(a, π̂(n))
        2. Determine if detection occurs (probability ϱ)
        3. If detected, sample timing using inverse CDF:
           - Generate u ~ U[0,1]
           - Solve Fa(t) = u for t
           - For Fa(t) = 1 - e^(-λt), inverse is: t = -ln(1-u)/λ
        4. Return detection_time = t * duration
        
        Returns:
            Detection time in [0, duration] if detected, None otherwise
        """
        # Step 1: Get detection probability
        detection_prob = self.calculate_detection_probability(action, target, actor_access, actor)
        
        # Step 2: Determine if detection occurs
        if random.random() >= detection_prob:
            logger.debug(
                f"[Exponential] {action.name} NOT detected "
                f"(ϱ={detection_prob:.3f})"
            )
            return None
        
        # Step 3: Sample detection timing using inverse CDF
        # For Fa(t) = 1 - e^(-λt), solve for t:
        # u = 1 - e^(-λt)
        # e^(-λt) = 1 - u
        # -λt = ln(1 - u)
        # t = -ln(1 - u) / λ
        
        u = random.random()
        
        # Handle edge case where u = 1 (would cause ln(0))
        if u >= 0.9999:
            u = 0.9999
        
        t_normalized = -math.log(1.0 - u) / self.lambda_param
        
        # Ensure t is in [0, 1]
        t_normalized = min(1.0, max(0.0, t_normalized))
        
        # Step 4: Convert to actual time
        detection_time = t_normalized * duration
        
        logger.debug(
            f"[Exponential] {action.name} detected at t={detection_time:.2f}/{duration:.2f} "
            f"(ϱ={detection_prob:.3f}, λ={self.lambda_param}, "
            f"Fa^(-1)({u:.3f})={t_normalized:.3f})"
        )
        
        return detection_time
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Return configuration summary for this engine."""
        return {
            'engine_type': 'ExponentialDetection',
            'detection_strategy': 'Exponential CDF (Early Detection)',
            'cdf_formula': f'Fa(t) = 1 - e^(-{self.lambda_param}t)',
            'cdf_inverse': f'Fa^(-1)(u) = -ln(1-u)/{self.lambda_param}',
            'lambda_parameter': self.lambda_param,
            'description': 'High probability of early detection, models signature-based IDS',
            'paper_compliance': 'TIM Section 4.5 - Exponential distribution',
            'complexity': 'O(1) - Direct inverse formula',
            'default_detection_probability': self.default_detection_probability,
            'characteristics': [
                'Strongly biased toward early detection',
                f'{int((1-math.exp(-self.lambda_param*0.2))*100)}% detected by 20% of duration',
                f'{int((1-math.exp(-self.lambda_param*0.5))*100)}% detected by 50% of duration',
                'Realistic for known attack signatures',
                'Good for well-monitored environments'
            ]
        }
