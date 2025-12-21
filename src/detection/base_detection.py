from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable
import logging
logger = logging.getLogger(__name__)

class BaseDetectionEngine(ABC):

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        pass

    @abstractmethod
    def get_cdf_function(self, action) -> Callable[[float], float]:
        pass

    @abstractmethod
    def calculate_detection_time(self, action, target, actor_access: str, actor, duration: float) -> Optional[float]:
        pass

    @abstractmethod
    def get_configuration_summary(self) -> Dict[str, Any]:
        pass

    def validate_cdf(self, cdf_func: Callable[[float], float], tolerance: float=0.02) -> bool:
        if abs(cdf_func(0.0)) > tolerance:
            self.logger.error(f'CDF constraint violated: Fa(0) = {cdf_func(0.0):.6f} ≠ 0')
            return False
        if abs(cdf_func(1.0) - 1.0) > tolerance:
            self.logger.warning(f'CDF constraint: Fa(1) = {cdf_func(1.0):.6f} (within {tolerance} tolerance of 1)')
        prev_value = 0.0
        for t in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            current_value = cdf_func(t)
            if current_value < prev_value - tolerance:
                self.logger.error(f'CDF not non-decreasing: Fa({t}) = {current_value:.6f} < previous value {prev_value:.6f}')
                return False
            prev_value = current_value
        return True