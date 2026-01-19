from typing import Dict, Any, Callable
import logging
from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class UniformDetectionEngine(BaseDetectionEngine):

    def __init__(self, default_detection_probability: float = 0.3):
        super().__init__(default_detection_probability)
        logger.info(f"Initialized Uniform Detection Engine: Fa(t) = t")

    def get_cdf_function(self, action) -> Callable[[float], float]:
        return lambda t: t

    def sample_inverse_cdf(self, u: float) -> float:
        return u

    def get_configuration_summary(self) -> Dict[str, Any]:
        return {
            "engine_type": "UniformDetection",
            "cdf_formula": "Fa(t) = t",
            "default_detection_probability": self.default_detection_probability,
        }
