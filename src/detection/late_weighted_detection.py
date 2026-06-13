import logging
import math
from collections.abc import Callable
from typing import Any

from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class LateWeightedDetectionEngine(BaseDetectionEngine):
    def __init__(self, exponent: float = 2.0, default_detection_probability: float = 0.35):
        super().__init__(default_detection_probability)
        if exponent < 1.0:
            logger.warning(f"Exponent {exponent} < 1 would give early bias, setting to 1.0")
            exponent = 1.0
        self.exponent = exponent
        logger.info(f"Initialized Late-Weighted Detection Engine: Fa(t) = t^{exponent}")

    def get_cdf_function(self, action) -> Callable[[float], float]:
        n = self.exponent
        return lambda t: math.pow(t, n)

    def sample_inverse_cdf(self, u: float) -> float:
        return math.pow(u, 1.0 / self.exponent)

    def get_configuration_summary(self) -> dict[str, Any]:
        return {
            "engine_type": "LateWeightedDetection",
            "cdf_formula": f"Fa(t) = t^{self.exponent}",
            "exponent": self.exponent,
            "default_detection_probability": self.default_detection_probability,
        }
