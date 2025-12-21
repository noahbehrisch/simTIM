import random
from typing import Dict, Any, Callable, Optional
import logging
from .base_detection import BaseDetectionEngine
logger = logging.getLogger(__name__)

class UniformDetectionEngine(BaseDetectionEngine):

    def __init__(self, default_detection_probability: float=0.3):
        super().__init__()
        self.default_detection_probability = default_detection_probability
        logger.info(f'Initialized Uniform Detection Engine: Fa(t) = t (default ϱ={default_detection_probability})')

    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        try:
            probability = action.get_detection_probability(target, actor_access, actor or 'unknown')
            return max(0.0, min(1.0, probability))
        except Exception as e:
            logger.warning(f"Action '{action.name}' detection failed: {e}, using default")
            return self.default_detection_probability

    def get_cdf_function(self, action) -> Callable[[float], float]:
        return lambda t: t

    def calculate_detection_time(self, action, target, actor_access: str, actor, duration: float) -> Optional[float]:
        detection_prob = self.calculate_detection_probability(action, target, actor_access, actor)
        if random.random() >= detection_prob:
            logger.debug(f'[Uniform] {action.name} NOT detected (ϱ={detection_prob:.3f})')
            return None
        u = random.random()
        t_normalized = u
        detection_time = t_normalized * duration
        logger.debug(f'[Uniform] {action.name} detected at t={detection_time:.2f}/{duration:.2f} (ϱ={detection_prob:.3f}, Fa^(-1)({u:.3f})={t_normalized:.3f})')
        return detection_time

    def get_configuration_summary(self) -> Dict[str, Any]:
        return {'engine_type': 'UniformDetection', 'detection_strategy': 'Uniform CDF', 'cdf_formula': 'Fa(t) = t', 'cdf_inverse': 'Fa^(-1)(u) = u', 'description': 'Constant detection rate throughout action duration', 'paper_compliance': 'TIM Section 4.5 - Uniform distribution', 'complexity': 'O(1) - Direct sampling', 'default_detection_probability': self.default_detection_probability, 'characteristics': ['Linear cumulative detection probability', 'Equal detection likelihood at all times', 'Fast computation', 'Good baseline for comparison']}