import math
import random
from typing import Dict, Any, Callable, Optional
import logging
from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class LinearDetectionEngine(BaseDetectionEngine):
    """
    Linear Detection Engine - uses polynomial CDF with n=2 for linear detection rate increase.
    
    CDF: Fa(t) = t^n
    PDF: fa(t) = n·t^(n-1)  [detection rate at time t]
    
    With n=2 (default):
    - CDF: Fa(t) = t²
    - PDF: fa(t) = 2t (LINEAR increase in detection rate)
    
    Characteristics:
    - Detection rate increases linearly over time (late detection bias)
    - Longer the action runs, higher the probability of detection per moment
    - Good for: Behavioral analysis, anomaly detection, UEBA
    
    Real-world analogy:
    - Behavioral analysis systems that need time to establish baseline
    - Anomaly detection requiring data accumulation  
    - Statistical methods that detect deviations as they become significant
    
    Detection timing distribution with n=2:
    - Early (0-20%): ~4% of detections
    - Middle (20-60%): ~32% of detections
    - Late (60-100%): ~64% of detections
    """

    def __init__(self, exponent: float = 2.0, default_detection_probability: float = 0.35):
        """
        Initialize Linear Detection Engine (polynomial CDF).
        
        Args:
            exponent: Polynomial exponent n (default 2.0 for linear detection rate)
                     - n=1: Uniform (constant detection rate)
                     - n=2: Linear increase in detection rate [DEFAULT]
                     - n>2: Accelerating detection rate (stronger late bias)
            default_detection_probability: Fallback ϱ(a, π̂(n))
        """
        super().__init__()
        
        if exponent < 1.0:
            logger.warning(f"Exponent {exponent} < 1 would give early bias, setting to 1.0")
            exponent = 1.0
        
        self.exponent = exponent
        self.default_detection_probability = default_detection_probability
        
        # Verify CDF constraints
        test_cdf = self.get_cdf_function(None)
        if not self.validate_cdf(test_cdf):
            logger.error(f"Polynomial CDF with n={exponent} failed validation!")
        
        bias_type = "linear" if exponent == 2.0 else ("late" if exponent > 1 else "uniform")
        logger.info(
            f"Initialized Linear Detection Engine: Fa(t) = t^{exponent} "
            f"(detection rate: {bias_type}, default ϱ={default_detection_probability})"
        )
    
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) - base detection probability.
        
        For linear detection (polynomial CDF), overall detection probability might be
        lower since behavioral analysis takes time and may miss quick attacks.
        """
        try:
            probability = action.get_detection_probability(target, actor_access, actor or "unknown")
            return max(0.0, min(1.0, probability))
        except Exception as e:
            logger.warning(f"Action '{action.name}' detection failed: {e}, using default")
            return self.default_detection_probability
    
    def get_cdf_function(self, action) -> Callable[[float], float]:
        """
        Return polynomial CDF: Fa(t) = t^n
        
        With n=2 (default):
        - CDF: Fa(t) = t²
        - PDF: fa(t) = 2t (linear increase)
        
        Properties:
        - Fa(0) = 0^n = 0 ✓
        - Fa(1) = 1^n = 1 ✓
        - For n > 0, monotonically increasing on [0,1] ✓
        - For n = 2, detection rate increases linearly over time
        - For n > 2, detection rate accelerates (stronger late bias)
        - For n = 1, constant detection rate (uniform)
        """
        n = self.exponent
        return lambda t: math.pow(t, n)
    
    def calculate_detection_time(self, action, target, actor_access: str, actor, 
                                duration: float) -> Optional[float]:
        """
        Calculate detection time using polynomial CDF (linear detection rate).
        
        Algorithm (TIM paper Section 4.5):
        1. Calculate ϱ(a, π̂(n))
        2. Determine if detection occurs (probability ϱ)
        3. If detected, sample timing using inverse CDF:
           - Generate u ~ U[0,1]
           - Solve Fa(t) = u for t
           - For Fa(t) = t^n, inverse is: t = u^(1/n)
        4. Scale to actual duration
        4. Return detection_time = t * duration
        
        Returns:
            Detection time in [0, duration] if detected, None otherwise
        """
        # Step 1: Get detection probability
        detection_prob = self.calculate_detection_probability(action, target, actor_access, actor)
        
        # Step 2: Determine if detection occurs
        if random.random() >= detection_prob:
            logger.debug(
                f"[Polynomial] {action.name} NOT detected "
                f"(ϱ={detection_prob:.3f})"
            )
            return None
        
        # Step 3: Sample detection timing using inverse CDF
        # For Fa(t) = t^n, solve for t:
        # u = t^n
        # t = u^(1/n)
        
        u = random.random()
        t_normalized = math.pow(u, 1.0 / self.exponent)
        
        # Ensure t is in [0, 1] (should be guaranteed by math, but be safe)
        t_normalized = min(1.0, max(0.0, t_normalized))
        
        # Step 4: Convert to actual time
        detection_time = t_normalized * duration
        
        logger.debug(
            f"[Polynomial] {action.name} detected at t={detection_time:.2f}/{duration:.2f} "
            f"(ϱ={detection_prob:.3f}, n={self.exponent}, "
            f"Fa^(-1)({u:.3f})={t_normalized:.3f})"
        )
        
        return detection_time
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Return configuration summary for this engine."""
        # Calculate some key percentiles for information
        cdf = self.get_cdf_function(None)
        
        # Find time at which 50% cumulative detection occurs
        # For t^n = 0.5, t = 0.5^(1/n)
        t_50_pct = math.pow(0.5, 1.0 / self.exponent)
        
        return {
            'engine_type': 'LinearDetection',
            'detection_strategy': 'Linear Detection Rate Increase',
            'cdf_formula': f'Fa(t) = t^{self.exponent}',
            'pdf_formula': f'fa(t) = {self.exponent}·t^{self.exponent-1}',
            'cdf_inverse': f'Fa^(-1)(u) = u^(1/{self.exponent})',
            'exponent': self.exponent,
            'description': 'Detection rate increases linearly over time - models behavioral analysis',
            'paper_compliance': 'TIM Section 4.5 - Polynomial distribution with n=2 for linear rate',
            'complexity': 'O(1) - Direct power and root operations',
            'default_detection_probability': self.default_detection_probability,
            'median_detection_time': f'{t_50_pct:.1%} of duration',
            'characteristics': [
                'Detection rate increases linearly (fa(t) = 2t for n=2)',
                f'{int(cdf(0.25)*100)}% detected by 25% of duration',
                f'{int(cdf(0.5)*100)}% detected by 50% of duration',
                f'{int(cdf(0.75)*100)}% detected by 75% of duration',
                'Realistic for behavioral/anomaly detection',
                'Models systems that need time to learn patterns'
            ]
        }
