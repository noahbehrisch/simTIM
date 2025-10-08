# Detection Package Documentation

This folder contains all detection engines for the TIM simulator, organized for easy maintenance and expansion.

## 📁 File Structure

```
src/detection/
├── __init__.py                # Package initialization and exports
├── legacy_detection.py        # Original simple detection engine
├── simple_detection.py        # Minimal TIM paper-compliant detection
└── advanced_detection.py      # TIM + cybersecurity domain knowledge
```

## 🎯 Detection Engines

### 1. Legacy Detection Engine (`legacy_detection.py`)
- **Class**: `SimpleDetectionEngine` (aliased as `LegacyDetectionEngine`)
- **Purpose**: Original simple detection implementation
- **Features**:
  - Basic random-based detection
  - Simple probability calculations
  - Backward compatibility with existing code
- **TIM Compliant**: ❌ No
- **Use Case**: Legacy systems, basic simulations

### 2. Simple TIM Detection Engine (`simple_detection.py`)
- **Class**: `SimpleTIMDetectionEngine`
- **Purpose**: Minimal TIM paper compliance
- **Features**:
  - Pure mathematical framework from TIM paper
  - Configurable ϱ(a, π̂(n)) detection probabilities
  - Configurable Fa(t) CDF functions with mathematical constraints
  - Exact TIM formula: Fa(t/da) · ϱ(a, π̂(n))
  - No hardcoded domain knowledge
- **TIM Compliant**: ✅ Yes (minimal)
- **Use Case**: Research, custom configurations, pure TIM implementation

### 3. Advanced TIM Detection Engine (`advanced_detection.py`)
- **Class**: `TIMDetectionEngine` (aliased as `AdvancedTIMDetectionEngine`)
- **Purpose**: Full TIM compliance + cybersecurity expertise
- **Features**:
  - Complete TIM mathematical framework
  - Pre-configured detection factors (endpoint protection, monitoring, etc.)
  - Multiple action-specific CDF patterns
  - Ready-to-use cybersecurity mappings
  - Extensive domain knowledge
- **TIM Compliant**: ✅ Yes (full)
- **Use Case**: Realistic simulations, production use, cybersecurity research

## 🚀 Usage Examples

### Import Detection Engines
```python
# Import all engines
from src.detection import LegacyDetectionEngine, SimpleTIMDetectionEngine, AdvancedTIMDetectionEngine

# Or use factory function
from src.detection import get_detection_engine
engine = get_detection_engine("simple_tim", default_detection_probability=0.3)

# List available engines
from src.detection import list_available_engines
print(list_available_engines())
```

### Use with Simulator
```python
from src.core.simulator import Simulator

# Legacy detection
sim1 = Simulator(network, detection_engine_type="legacy")

# Simple TIM detection
sim2 = Simulator(network, detection_engine_type="simple_tim")

# Advanced TIM detection  
sim3 = Simulator(network, detection_engine_type="advanced_tim")
```

### Configure Simple TIM Engine
```python
from src.detection import SimpleTIMDetectionEngine

engine = SimpleTIMDetectionEngine(default_detection_probability=0.2)

# Configure specific detection probabilities
node_props = {'security_level': 'high', 'monitoring': 'advanced'}
engine.configure_detection_probability("privilege_escalation", node_props, 0.8)

# Configure custom CDF function
def custom_cdf(t):
    return t ** 0.5  # Square root function (satisfies Fa(0)=0, Fa(1)=1)

engine.configure_cdf_function("privilege_escalation", custom_cdf)
```

## 🔧 Adding New Detection Engines

To add a new detection engine:

1. **Create new file**: `src/detection/my_new_detection.py`
2. **Implement interface**: Follow the pattern of existing engines
3. **Update __init__.py**: Add imports and aliases
4. **Update simulator**: Add support in simulator.py if needed
5. **Add tests**: Create tests in test files

### Required Methods
All detection engines should implement:
```python
def calculate_detection_probability(self, action, target, actor_access, actor) -> float:
    """Calculate detection probability for action on target"""
    
def sample_detection_time(self, action, duration, detection_probability) -> Optional[float]:
    """Sample detection time or return None if not detected"""
```

### TIM-Compliant Engines
TIM-compliant engines should also implement:
```python
def calculate_cumulative_detection_probability(self, action, target, actor_access, 
                                             time_elapsed, total_duration) -> float:
    """Calculate Fa(t/da) · ϱ(a, π̂(n))"""
    
def get_cdf_function(self, action) -> Callable[[float], float]:
    """Get CDF function Fa(t) with Fa(0)=0, Fa(1)=1"""
```

## 📊 TIM Paper Compliance

| Feature | Legacy | Simple TIM | Advanced TIM |
|---------|--------|------------|--------------|
| ϱ(a, π̂(n)) function | ❌ Basic | ✅ Configurable | ✅ Pre-configured |
| Fa(t) CDF with constraints | ❌ No CDF | ✅ Enforced | ✅ Multiple patterns |
| Fa(t/da) · ϱ(a, π̂(n)) formula | ❌ Heuristic | ✅ Exact | ✅ Exact |
| Domain knowledge | ❌ Minimal | ❌ None (pure) | ✅ Extensive |
| Ready for production | ✅ Simple | ⚠️ Needs config | ✅ Yes |

## 🧪 Testing

Run detection engine tests:
```bash
python test_all_detection_engines.py
python test_tim_compliance.py
```

All engines are tested for:
- Basic functionality
- TIM compliance (where applicable)
- Configuration capabilities
- Integration with simulator

## 📝 Maintenance Notes

- **Backward compatibility**: Legacy aliases maintained in `__init__.py`
- **Import structure**: All engines accessible via `src.detection` package
- **Factory pattern**: Use `get_detection_engine()` for dynamic creation
- **Documentation**: Keep this README updated when adding new engines
