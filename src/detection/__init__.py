"""
Detection Package for simTIM

TIM paper-compliant detection engines implementing Section 4.5.
"""

from .base_detection import BaseDetectionEngine
from .simple_detection import SimpleTIMDetectionEngine
from .advanced_detection import AdvancedTIMDetectionEngine

TIMDetectionEngine = AdvancedTIMDetectionEngine
DetectionEngine = AdvancedTIMDetectionEngine

__all__ = [
    'BaseDetectionEngine',
    'SimpleTIMDetectionEngine',
    'AdvancedTIMDetectionEngine',
    'TIMDetectionEngine',
    'DetectionEngine'
]
