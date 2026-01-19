import math
from typing import Dict, Any, Callable
import logging
from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class ExponentialDetectionEngine(BaseDetectionEngine):

    def __init__(
        self, lambda_param: float = 4.605, default_detection_probability: float = 0.4
    ):
        super().__init__(default_detection_probability)
        self.lambda_param = lambda_param
        logger.info(f"Initialized Exponential Detection Engine: λ={lambda_param:.2f}")

    def get_cdf_function(self, action) -> Callable[[float], float]:
        lambda_val = self.lambda_param
        return lambda t: 1.0 - math.exp(-lambda_val * t)

    def sample_inverse_cdf(self, u: float) -> float:
        return -math.log(1.0 - u) / self.lambda_param

    def get_configuration_summary(self) -> Dict[str, Any]:
        return {
            "engine_type": "ExponentialDetection",
            "cdf_formula": f"Fa(t) = 1 - e^(-{self.lambda_param}t)",
            "lambda_parameter": self.lambda_param,
            "default_detection_probability": self.default_detection_probability,
        }
