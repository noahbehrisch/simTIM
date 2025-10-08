"""
Detection Package

This package contains all detection engines for the TIM simulator:

1. LegacyDetectionEngine (legacy_detection.py):
   - Original simple detection implementation
   - Basic random-based detection
   - Backward compatibility

2. SimpleTIMDetectionEngine (simple_detection.py):
   - Minimal TIM paper compliance
   - Pure mathematical framework from TIM paper
   - Configurable ϱ(a, π̂(n)) and Fa(t) functions
   - No domain-specific knowledge

3. AdvancedTIMDetectionEngine (advanced_detection.py):
   - Full TIM compliance plus cybersecurity domain knowledge
   - Pre-configured detection factors
   - Multiple CDF patterns for different action types
   - Ready-to-use for realistic simulations

Usage:
    from src.detection import LegacyDetectionEngine, SimpleTIMDetectionEngine, AdvancedTIMDetectionEngine
    
    # Or import specific engines:
    from src.detection.simple_detection import SimpleTIMDetectionEngine
    from src.detection.advanced_detection import TIMDetectionEngine as AdvancedTIMDetectionEngine
    from src.detection.legacy_detection import SimpleDetectionEngine as LegacyDetectionEngine
"""

# Import all detection engines for easy access
from .legacy_detection import SimpleDetectionEngine as LegacyDetectionEngine
from .simple_detection import SimpleTIMDetectionEngine
from .advanced_detection import TIMDetectionEngine as AdvancedTIMDetectionEngine

# For backward compatibility
SimpleDetectionEngine = LegacyDetectionEngine
DetectionEngine = LegacyDetectionEngine
TIMDetectionEngine = AdvancedTIMDetectionEngine

__all__ = [
    'LegacyDetectionEngine',
    'SimpleTIMDetectionEngine', 
    'AdvancedTIMDetectionEngine',
    # Backward compatibility aliases
    'SimpleDetectionEngine',
    'DetectionEngine',
    'TIMDetectionEngine'
]

def get_detection_engine(engine_type: str = "legacy", **kwargs):
    """
    Factory function to create detection engines.
    
    Args:
        engine_type: "legacy", "simple_tim", or "advanced_tim"
        **kwargs: Additional arguments for engine initialization
        
    Returns:
        Configured detection engine instance
    """
    if engine_type == "legacy":
        return LegacyDetectionEngine(**kwargs)
    elif engine_type == "simple_tim":
        return SimpleTIMDetectionEngine(**kwargs)
    elif engine_type == "advanced_tim":
        return AdvancedTIMDetectionEngine(**kwargs)
    else:
        raise ValueError(f"Unknown detection engine type: {engine_type}")

def list_available_engines():
    """List all available detection engines."""
    return {
        'legacy': {
            'class': 'LegacyDetectionEngine',
            'description': 'Original simple detection with basic random-based approach',
            'tim_compliant': False
        },
        'simple_tim': {
            'class': 'SimpleTIMDetectionEngine', 
            'description': 'Minimal TIM paper compliance with pure mathematical framework',
            'tim_compliant': True
        },
        'advanced_tim': {
            'class': 'AdvancedTIMDetectionEngine',
            'description': 'Full TIM compliance plus cybersecurity domain knowledge',
            'tim_compliant': True
        }
    }
