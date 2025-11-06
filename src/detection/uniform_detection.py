import random
from typing import Dict, Any, Callable, Optional
import logging
from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class UniformDetectionEngine(BaseDetectionEngine):

    def __init__(self, default_detection_probability: float = 0.3):
        """
        Initialize Uniform Detection Engine.
        
        Args:
            default_detection_probability: Fallback ϱ(a, π̂(n)) when action doesn't specify
        """
        super().__init__()
        self.default_detection_probability = default_detection_probability
        
        logger.info(
            f"Initialized Uniform Detection Engine: Fa(t) = t "
            f"(default ϱ={default_detection_probability})"
        )
    
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) - base detection probability.
        
        This is the probability that detection occurs sometime during action execution.
        """
        try:
            probability = action.get_detection_probability(target, actor_access, actor or "unknown")
            return max(0.0, min(1.0, probability))
        except Exception as e:
            logger.warning(f"Action '{action.name}' detection failed: {e}, using default")
            return self.default_detection_probability
    
    def get_cdf_function(self, action) -> Callable[[float], float]:
        """
        Return uniform CDF: Fa(t) = t
        
        Satisfies TIM paper constraints:
        - Fa(0) = 0
        - Fa(1) = 1
        - Fa is monotonically increasing
        """
        return lambda t: t
    
    def calculate_detection_time(self, action, target, actor_access: str, actor, 
                                duration: float) -> Optional[float]:
        """
        Calculate detection time using uniform CDF.
        
        Algorithm (TIM paper compliant):
        1. Calculate ϱ(a, π̂(n)) = base detection probability
        2. Determine if detection occurs: sample U[0,1], check if < ϱ
        3. If detected, sample timing using inverse CDF:
           - Generate u ~ U[0,1]
           - Find t where Fa(t) = u
           - For Fa(t) = t, inverse is simply t = u
        4. Return detection_time = t * duration
        
        Returns:
            Detection time in [0, duration] if detected, None otherwise
        """
        # Step 1: Get detection probability ϱ(a, π̂(n))
        detection_prob = self.calculate_detection_probability(action, target, actor_access, actor)
        
        # Step 2: Determine if detection occurs at all
        if random.random() >= detection_prob:
            logger.debug(
                f"[Uniform] {action.name} NOT detected "
                f"(ϱ={detection_prob:.3f})"
            )
            return None
        
        # Step 3: Sample detection timing using inverse CDF
        # For Fa(t) = t, the inverse is Fa^(-1)(u) = u
        u = random.random()  # Random value in [0,1]
        t_normalized = u     # For uniform CDF, inverse is identity function
        
        # Step 4: Convert normalized time to actual time
        detection_time = t_normalized * duration
        
        logger.debug(
            f"[Uniform] {action.name} detected at t={detection_time:.2f}/{duration:.2f} "
            f"(ϱ={detection_prob:.3f}, Fa^(-1)({u:.3f})={t_normalized:.3f})"
        )
        
        return detection_time
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Return configuration summary for this engine."""
        return {
            'engine_type': 'UniformDetection',
            'detection_strategy': 'Uniform CDF',
            'cdf_formula': 'Fa(t) = t',
            'cdf_inverse': 'Fa^(-1)(u) = u',
            'description': 'Constant detection rate throughout action duration',
            'paper_compliance': 'TIM Section 4.5 - Uniform distribution',
            'complexity': 'O(1) - Direct sampling',
            'default_detection_probability': self.default_detection_probability,
            'characteristics': [
                'Linear cumulative detection probability',
                'Equal detection likelihood at all times',
                'Fast computation',
                'Good baseline for comparison'
            ]
        }
