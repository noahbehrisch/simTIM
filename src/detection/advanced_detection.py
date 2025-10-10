"""
Advanced TIM Detection Engine - Domain-Enhanced Implementation

This engine extends the TIM paper Section 4.5 model with cybersecurity domain knowledge.
It implements the same formal model as SimpleTIM but with pre-configured, realistic
detection probabilities and patterns based on real-world cybersecurity practices.

Base TIM paper model (Section 4.5):
1. ϱ(a, π̂(n)) - detection probability function: A(attack) × Π̂ → [0, 1]
2. Fa(t) - cumulative distribution function with Fa(0) = 0 and Fa(1) = 1
3. Detection timing: P(detected by time t) = Fa(t/da) · ϱ(a, π̂(n))

Enhancements:
- Pre-configured detection probabilities based on action types
- Node property factors (endpoint protection, monitoring, criticality)
- Action-specific CDF patterns based on detection characteristics
- Ready-to-use for realistic simulations

Reference: "Time is money: A temporal model of cybersecurity" by Zoltán Ádám Mann
"""

import math
from typing import Dict, Any, Callable, Set
import logging
from .base_detection import BaseDetectionEngine

logger = logging.getLogger(__name__)


class AdvancedTIMDetectionEngine(BaseDetectionEngine):
    """
    Advanced TIM detection engine with cybersecurity domain knowledge.
    
    Implements the same TIM paper model as SimpleTIM but with pre-configured,
    realistic detection probabilities and patterns.
    """
    
    # Define action categories for detection
    ACTION_CATEGORIES = {
        'reconnaissance': ['scan', 'probe', 'discover', 'enum', 'reconnaissance'],
        'exploitation': ['exploit', 'overflow', 'injection', 'cve'],
        'privilege_escalation': ['escalate', 'privilege', 'sudo', 'root'],
        'lateral_movement': ['lateral', 'ssh', 'rdp', 'psexec', 'wmi'],
        'persistence': ['backdoor', 'persistence', 'implant', 'rootkit'],
        'data_exfiltration': ['exfiltrate', 'download', 'steal', 'dump'],
        'defense_evasion': ['evasion', 'obfuscate', 'hide', 'disable'],
        'credential_access': ['credential', 'password', 'hash', 'mimikatz']
    }
    
    def __init__(self):
        """Initialize Advanced TIM detection engine with domain knowledge."""
        super().__init__()
        
        # Initialize detection probability mappings
        self._initialize_detection_probabilities()
        
        # Initialize CDF functions
        self._initialize_cdf_functions()
        
        # Initialize node property factors
        self._initialize_property_factors()
        
        logger.info("Initialized AdvancedTIM detection engine with domain knowledge")
    
    def _initialize_detection_probabilities(self):
        """
        Initialize base detection probabilities by action category.
        
        These are realistic values based on cybersecurity research and practice.
        """
        self.base_detection_probabilities = {
            'reconnaissance': 0.15,      # Often goes unnoticed
            'exploitation': 0.40,         # Moderate detection
            'privilege_escalation': 0.55, # High detection (suspicious privilege changes)
            'lateral_movement': 0.45,     # Moderate-high (unusual network activity)
            'persistence': 0.35,          # Moderate (can be subtle)
            'data_exfiltration': 0.70,    # High detection (large data transfers)
            'defense_evasion': 0.20,      # Low (designed to avoid detection)
            'credential_access': 0.50,    # Moderate-high (sensitive operations)
            'unknown': 0.30               # Default for uncategorized actions
        }
    
    def _initialize_cdf_functions(self):
        """
        Initialize CDF functions for different action categories.
        
        Different attack types have different detection time patterns.
        """
        # Reconnaissance: Often detected early (automated tools trigger alerts)
        self.cdf_early = lambda t: min(1.0, 1.5 * t * (1 - 0.3 * math.exp(-3 * t)))
        
        # Exploitation: Uniform detection throughout execution
        self.cdf_uniform = lambda t: t
        
        # Privilege escalation: Late detection (after suspicious activity accumulates)
        self.cdf_late = lambda t: t ** 2
        
        # Data exfiltration: Immediate detection (distinctive signature)
        self.cdf_immediate = lambda t: min(1.0, 1.5 * t)
        
        # Defense evasion: Very late detection (stealthy)
        self.cdf_very_late = lambda t: t ** 3
        
        # Exponential: For actions with increasing detection over time
        self.cdf_exponential = lambda t: min(1.0, t * (2 - 0.3 * math.exp(-2 * t)))
        
        # Map categories to CDF functions
        self.category_cdf_map = {
            'reconnaissance': self.cdf_early,
            'exploitation': self.cdf_uniform,
            'privilege_escalation': self.cdf_late,
            'lateral_movement': self.cdf_exponential,
            'persistence': self.cdf_late,
            'data_exfiltration': self.cdf_immediate,
            'defense_evasion': self.cdf_very_late,
            'credential_access': self.cdf_exponential,
            'unknown': self.cdf_uniform
        }
    
    def _initialize_property_factors(self):
        """
        Initialize detection probability modifiers based on node properties.
        
        These factors modify the base detection probability based on defensive measures.
        """
        self.property_factors = {
            # Endpoint protection software
            'endpoint_protection': {
                'CrowdStrike': 0.30,
                'Carbon Black': 0.28,
                'Sophos': 0.25,
                'McAfee': 0.20,
                'Symantec': 0.18,
                'Windows Defender': 0.15,
                'none': 0.0
            },
            
            # Network monitoring and IDS/IPS
            'network_monitoring': {
                'SIEM': 0.25,
                'IPS': 0.22,
                'IDS': 0.18,
                'NetFlow': 0.12,
                'basic_logging': 0.08,
                'none': 0.0
            },
            
            # System criticality (more monitoring on critical systems)
            'criticality': {
                'critical': 0.15,
                'high': 0.12,
                'medium': 0.08,
                'low': 0.03
            },
            
            # Logging level
            'logging_level': {
                'verbose': 0.10,
                'normal': 0.05,
                'minimal': 0.02,
                'none': 0.0
            },
            
            # Security team presence
            'security_monitoring': {
                '24/7_SOC': 0.20,
                'business_hours': 0.10,
                'automated_only': 0.05,
                'none': 0.0
            },
            
            # Internet exposure (external attacks more monitored)
            'exposure': {
                'internet_facing': 0.10,
                'dmz': 0.08,
                'internal': 0.0,
                'isolated': -0.05  # Negative because less monitoring
            }
        }
    
    def _categorize_action(self, action_name: str) -> str:
        """
        Categorize action based on its name.
        
        Args:
            action_name: Name of the action
            
        Returns:
            Action category string
        """
        action_name_lower = action_name.lower()
        
        for category, keywords in self.ACTION_CATEGORIES.items():
            for keyword in keywords:
                if keyword in action_name_lower:
                    return category
        
        return 'unknown'
    
    def calculate_detection_probability(self, action, target, actor_access: str, actor) -> float:
        """
        Calculate ϱ(a, π̂(n)) with domain knowledge enhancements.
        
        Implementation of TIM paper Section 4.5 plus realistic factors:
        - Base probability from action category
        - Modifiers from node properties (endpoint protection, monitoring, etc.)
        
        Args:
            action: The action 'a'
            target: The target node with properties π̂(n)
            actor_access: Actor's access level
            actor: The actor
            
        Returns:
            Detection probability ϱ(a, π̂(n)) ∈ [0, 1]
        """
        # Get base detection probability from action category
        category = self._categorize_action(action.name)
        base_prob = self.base_detection_probabilities.get(category, 0.30)
        
        logger.debug(f"Action '{action.name}' categorized as '{category}' with base ϱ={base_prob}")
        
        # Get node properties π̂(n)
        node_properties = getattr(target, 'properties', {})
        
        # Calculate modifiers from node properties
        total_modifier = 0.0
        
        # Endpoint protection modifier
        endpoint = node_properties.get('endpoint_protection', 'none')
        if isinstance(endpoint, str):
            modifier = self.property_factors['endpoint_protection'].get(endpoint, 0.0)
            total_modifier += modifier
            if modifier > 0:
                logger.debug(f"  + Endpoint protection '{endpoint}': +{modifier:.3f}")
        
        # Network monitoring modifier
        monitoring = node_properties.get('network_monitoring', 'none')
        if isinstance(monitoring, str):
            modifier = self.property_factors['network_monitoring'].get(monitoring, 0.0)
            total_modifier += modifier
            if modifier > 0:
                logger.debug(f"  + Network monitoring '{monitoring}': +{modifier:.3f}")
        
        # Criticality modifier
        if node_properties.get('critical', False) or node_properties.get('criticality') == 'critical':
            modifier = self.property_factors['criticality']['critical']
            total_modifier += modifier
            logger.debug(f"  + Critical system: +{modifier:.3f}")
        elif 'criticality' in node_properties:
            criticality = node_properties['criticality']
            modifier = self.property_factors['criticality'].get(criticality, 0.0)
            total_modifier += modifier
            if modifier > 0:
                logger.debug(f"  + Criticality '{criticality}': +{modifier:.3f}")
        
        # Logging level modifier
        logging_level = node_properties.get('logging_level', 'normal')
        if isinstance(logging_level, str):
            modifier = self.property_factors['logging_level'].get(logging_level, 0.0)
            total_modifier += modifier
            if modifier > 0:
                logger.debug(f"  + Logging '{logging_level}': +{modifier:.3f}")
        
        # Security monitoring modifier
        sec_monitoring = node_properties.get('security_monitoring', 'none')
        if isinstance(sec_monitoring, str):
            modifier = self.property_factors['security_monitoring'].get(sec_monitoring, 0.0)
            total_modifier += modifier
            if modifier > 0:
                logger.debug(f"  + Security monitoring '{sec_monitoring}': +{modifier:.3f}")
        
        # Exposure modifier
        if node_properties.get('exposed_to_internet', False):
            modifier = self.property_factors['exposure']['internet_facing']
            total_modifier += modifier
            logger.debug(f"  + Internet exposed: +{modifier:.3f}")
        elif 'exposure' in node_properties:
            exposure = node_properties['exposure']
            modifier = self.property_factors['exposure'].get(exposure, 0.0)
            total_modifier += modifier
            if modifier != 0:
                logger.debug(f"  + Exposure '{exposure}': {modifier:+.3f}")
        
        # Calculate final detection probability
        detection_probability = max(0.0, min(1.0, base_prob + total_modifier))
        
        logger.debug(f"Final ϱ({action.name}, π̂) = {detection_probability:.3f}")
        
        return detection_probability
    
    def get_cdf_function(self, action) -> Callable[[float], float]:
        """
        Get Fa(t) based on action category.
        
        Implementation of TIM paper Section 4.5:
        Different action categories have different detection time patterns.
        
        Args:
            action: The action 'a'
            
        Returns:
            CDF function Fa: [0, 1] → [0, 1]
        """
        category = self._categorize_action(action.name)
        cdf_func = self.category_cdf_map.get(category, self.cdf_uniform)
        
        logger.debug(f"Action '{action.name}' (category '{category}') using CDF pattern")
        
        return cdf_func
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get summary of current configuration."""
        return {
            'engine_type': 'AdvancedTIM',
            'paper_section': '4.5 + Domain Knowledge',
            'compliance': 'TIM paper + cybersecurity domain knowledge',
            'action_categories': len(self.ACTION_CATEGORIES),
            'base_detection_probabilities': self.base_detection_probabilities,
            'property_factors': {
                factor_name: len(values)
                for factor_name, values in self.property_factors.items()
            },
            'cdf_patterns': len(self.category_cdf_map),
            'features': [
                'ϱ(a, π̂(n)) detection probability function',
                'Fa(t) cumulative distribution function',
                'Fa(t/da) · ϱ(a, π̂(n)) temporal detection',
                'Action categorization',
                'Endpoint protection awareness',
                'Network monitoring awareness',
                'System criticality factors',
                'Logging and SOC awareness',
                'Pre-configured realistic values',
                'Category-specific CDF patterns'
            ]
        }
    
    def get_action_category_info(self, action_name: str) -> Dict[str, Any]:
        """
        Get detailed information about how an action would be detected.
        
        Useful for understanding and debugging detection behavior.
        
        Args:
            action_name: Name of the action
            
        Returns:
            Dictionary with category, base probability, and CDF type
        """
        category = self._categorize_action(action_name)
        base_prob = self.base_detection_probabilities.get(category, 0.30)
        
        # Identify CDF type
        cdf_func = self.category_cdf_map.get(category, self.cdf_uniform)
        cdf_name = 'unknown'
        if cdf_func == self.cdf_early:
            cdf_name = 'early'
        elif cdf_func == self.cdf_uniform:
            cdf_name = 'uniform'
        elif cdf_func == self.cdf_late:
            cdf_name = 'late'
        elif cdf_func == self.cdf_immediate:
            cdf_name = 'immediate'
        elif cdf_func == self.cdf_very_late:
            cdf_name = 'very_late'
        elif cdf_func == self.cdf_exponential:
            cdf_name = 'exponential'
        
        return {
            'action_name': action_name,
            'category': category,
            'base_detection_probability': base_prob,
            'cdf_pattern': cdf_name,
            'description': self._get_category_description(category)
        }
    
    def _get_category_description(self, category: str) -> str:
        """Get human-readable description of category detection characteristics."""
        descriptions = {
            'reconnaissance': 'Low base detection, early CDF (automated scanners often trigger alerts)',
            'exploitation': 'Moderate detection, uniform CDF (depends on exploit sophistication)',
            'privilege_escalation': 'High detection, late CDF (suspicious privilege changes accumulate)',
            'lateral_movement': 'Moderate-high detection, exponential CDF (unusual network patterns)',
            'persistence': 'Moderate detection, late CDF (changes may go unnoticed initially)',
            'data_exfiltration': 'High detection, immediate CDF (large transfers are distinctive)',
            'defense_evasion': 'Low detection, very late CDF (designed to be stealthy)',
            'credential_access': 'Moderate-high detection, exponential CDF (sensitive operations)',
            'unknown': 'Default detection behavior'
        }
        return descriptions.get(category, 'No description available')
