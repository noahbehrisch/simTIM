import math
import random
from typing import Dict, Any, Callable, Optional
import logging
from .base_detection import BaseDetectionEngine
logger = logging.getLogger(__name__)

class ExponentialDetectionEngine(BaseDetectionEngine):

    def __init__(self, lambda_param: float=4.605, default_detection_probability: float=0.4):
        super().__init__()
        self.lambda_param = lambda_param
        self.default_detection_probability = default_detection_probability
        logger.info(f'Initialized Exponential Detection Engine: Fa(t) = 1 - e^(-{lambda_param:.2f}t) (Fa(1)≈{1 - math.exp(-lambda_param):.4f}, default ϱ={default_detection_probability})')

    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        try:
            probability = action.get_detection_probability(target, actor_access, actor or 'unknown')
            return max(0.0, min(1.0, probability))
        except Exception as e:
            logger.warning(f"Action '{action.name}' detection failed: {e}, using default")
            return self.default_detection_probability

    def get_cdf_function(self, action) -> Callable[[float], float]:
        lambda_val = self.lambda_param
        return lambda t: 1.0 - math.exp(-lambda_val * t)

    def calculate_detection_time(self, action, target, actor_access: str, actor, duration: float) -> Optional[float]:
        detection_prob = self.calculate_detection_probability(action, target, actor_access, actor)
        if random.random() >= detection_prob:
            logger.debug(f'[Exponential] {action.name} NOT detected (ϱ={detection_prob:.3f})')
            return None
        u = random.random()
        if u >= 0.9999:
            u = 0.9999
        t_normalized = -math.log(1.0 - u) / self.lambda_param
        t_normalized = min(1.0, max(0.0, t_normalized))
        detection_time = t_normalized * duration
        logger.debug(f'[Exponential] {action.name} detected at t={detection_time:.2f}/{duration:.2f} (ϱ={detection_prob:.3f}, λ={self.lambda_param}, Fa^(-1)({u:.3f})={t_normalized:.3f})')
        return detection_time

    def get_configuration_summary(self) -> Dict[str, Any]:
        return {'engine_type': 'ExponentialDetection', 'detection_strategy': 'Exponential CDF (Early Detection)', 'cdf_formula': f'Fa(t) = 1 - e^(-{self.lambda_param}t)', 'cdf_inverse': f'Fa^(-1)(u) = -ln(1-u)/{self.lambda_param}', 'lambda_parameter': self.lambda_param, 'description': 'High probability of early detection, models signature-based IDS', 'paper_compliance': 'TIM Section 4.5 - Exponential distribution', 'complexity': 'O(1) - Direct inverse formula', 'default_detection_probability': self.default_detection_probability, 'characteristics': ['Strongly biased toward early detection', f'{int((1 - math.exp(-self.lambda_param * 0.2)) * 100)}% detected by 20% of duration', f'{int((1 - math.exp(-self.lambda_param * 0.5)) * 100)}% detected by 50% of duration', 'Realistic for known attack signatures', 'Good for well-monitored environments']}