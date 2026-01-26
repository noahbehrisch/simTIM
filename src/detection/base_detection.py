import logging
import random
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class BaseDetectionEngine(ABC):
    def __init__(self, default_detection_probability: float = 0.3):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.default_detection_probability = default_detection_probability

    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        try:
            probability = action.get_detection_probability(target, actor_access, actor or "unknown")
            return max(0.0, min(1.0, probability))
        except Exception as e:
            self.logger.warning(f"Action '{action.name}' detection failed: {e}, using default")
            return self.default_detection_probability

    @abstractmethod
    def get_cdf_function(self, action) -> Callable[[float], float]:
        pass

    @abstractmethod
    def sample_inverse_cdf(self, u: float) -> float:
        pass

    @abstractmethod
    def get_configuration_summary(self) -> dict[str, Any]:
        pass

    def calculate_detection_time(
        self, action, target, actor_access: str, actor, duration: float
    ) -> float | None:
        detection_prob = self.calculate_detection_probability(action, target, actor_access, actor)
        if random.random() >= detection_prob:
            self.logger.debug(f"{action.name} NOT detected (ϱ={detection_prob:.3f})")
            return None
        u = random.random()
        if u >= 0.9999:
            u = 0.9999
        t_normalized = self.sample_inverse_cdf(u)
        t_normalized = min(1.0, max(0.0, t_normalized))
        detection_time = t_normalized * duration
        self.logger.debug(
            f"{action.name} detected at t={detection_time:.2f}/{duration:.2f} (ϱ={detection_prob:.3f})"
        )
        return detection_time

    def validate_cdf(self, cdf_func: Callable[[float], float], tolerance: float = 0.02) -> bool:
        if abs(cdf_func(0.0)) > tolerance:
            self.logger.error(f"CDF constraint violated: Fa(0) = {cdf_func(0.0):.6f} ≠ 0")
            return False
        if abs(cdf_func(1.0) - 1.0) > tolerance:
            self.logger.warning(
                f"CDF constraint: Fa(1) = {cdf_func(1.0):.6f} (within {tolerance} tolerance of 1)"
            )
        prev_value = 0.0
        for t in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            current_value = cdf_func(t)
            if current_value < prev_value - tolerance:
                self.logger.error(
                    f"CDF not non-decreasing: Fa({t}) = {current_value:.6f} < previous value {prev_value:.6f}"
                )
                return False
            prev_value = current_value
        return True
