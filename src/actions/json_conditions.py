#!/usr/bin/env python3
"""
Enhanced JSON-based condition evaluator for actions
Supports SMT-like formulas with quantifiers, implications, and variable binding
Based on TIM paper requirements for preconditions φₐ as SMT formulas
"""

from typing import Dict, Any, List, Union, Callable
from src.actions.version import Version
from src.core.graph import Node, Link


class ConditionEvaluator:
    """
    Enhanced evaluator for SMT-like conditions in JSON format
    Supports TIM paper requirements: preconditions φₐ as SMT formulas over node properties
    """
    
    def __init__(self):
        self.variable_scope = {}  # For variable binding in quantified formulas
    
    def evaluate_condition(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        """
        Evaluate an SMT-like condition against a node and actor state
        
        Args:
            condition: JSON condition definition (SMT-like formula)
            node: Target node
            actor_access: Actor's access level
            actor_id: Actor identifier
            network_context: Optional network context for quantified formulas
            
        Returns:
            bool: True if condition is satisfied (φₐ evaluates to true)
        """
        condition_type = condition.get('type')
        
        # Core logical operators
        if condition_type == 'compound':
            return self._evaluate_compound(condition, node, actor_access, actor_id, network_context)
        elif condition_type == 'implication':
            return self._evaluate_implication(condition, node, actor_access, actor_id, network_context)
        elif condition_type == 'negation':
            return self._evaluate_negation(condition, node, actor_access, actor_id, network_context)
            
        # Quantified formulas (SMT-like)
        elif condition_type == 'exists':
            return self._evaluate_exists(condition, node, actor_access, actor_id, network_context)
        elif condition_type == 'forall':
            return self._evaluate_forall(condition, node, actor_access, actor_id, network_context)
            
        # Property checks with variable binding
        elif condition_type == 'software_check':
            return self._evaluate_software_check(condition, node)
        elif condition_type == 'version_check':
            return self._evaluate_version_check(condition, node)
        elif condition_type == 'access_check':
            return self._evaluate_access_check(condition, actor_access, actor_id)
        elif condition_type == 'property_check':
            return self._evaluate_property_check(condition, node)
        elif condition_type == 'vulnerability_check':
            return self._evaluate_vulnerability_check(condition, node)
        elif condition_type == 'assets_check':
            return self._evaluate_assets_check(condition, node)
        elif condition_type == 'network_check':
            return self._evaluate_network_check(condition, node, network_context)
            
        # Variable references for quantified formulas
        elif condition_type == 'variable_ref':
            return self._evaluate_variable_ref(condition, node, actor_access, actor_id)
            
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")
    
    def _evaluate_compound(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        """Evaluate compound logical operations (∧, ∨, ⊕)"""
        operator = condition.get('operator', 'AND')
        conditions = condition.get('conditions', [])
        
        if operator == 'AND':  # ∧
            return all(self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions)
        elif operator == 'OR':   # ∨
            return any(self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions)
        elif operator == 'XOR':  # ⊕ (exclusive or)
            results = [self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions]
            return sum(results) == 1  # Exactly one condition true
        elif operator == 'NAND': # ¬(A ∧ B)
            return not all(self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions)
        elif operator == 'NOR':  # ¬(A ∨ B) 
            return not any(self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions)
        else:
            raise ValueError(f"Unknown compound operator: {operator}")
    
    def _evaluate_implication(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        """Evaluate implication: premise → conclusion (¬premise ∨ conclusion)"""
        premise = condition.get('premise')
        conclusion = condition.get('conclusion')
        
        if not premise or not conclusion:
            raise ValueError("Implication requires both 'premise' and 'conclusion'")
        
        premise_result = self.evaluate_condition(premise, node, actor_access, actor_id, network_context)
        conclusion_result = self.evaluate_condition(conclusion, node, actor_access, actor_id, network_context)
        
        # A → B is equivalent to ¬A ∨ B
        return not premise_result or conclusion_result
    
    def _evaluate_negation(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        """Evaluate logical negation: ¬φ"""
        inner_condition = condition.get('condition')
        if not inner_condition:
            raise ValueError("Negation requires 'condition' field")
        
        return not self.evaluate_condition(inner_condition, node, actor_access, actor_id, network_context)
    
    def _evaluate_exists(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        """
        Evaluate existential quantification: ∃x ∈ Domain : φ(x)
        Example: ∃n ∈ neighbors : compromised(n) = true
        """
        variable = condition.get('variable')  # x
        domain = condition.get('domain')      # Domain to quantify over
        formula = condition.get('formula')    # φ(x)
        
        if not all([variable, domain, formula]):
            raise ValueError("Exists quantifier requires 'variable', 'domain', and 'formula'")
        
        domain_elements = self._get_domain_elements(domain, node, network_context)
        
        # Check if ∃x : φ(x) is true for any x in domain
        for element in domain_elements:
            # Bind variable to current element
            old_value = self.variable_scope.get(variable)
            self.variable_scope[variable] = element
            
            try:
                if self.evaluate_condition(formula, element if isinstance(element, Node) else node, actor_access, actor_id, network_context):
                    return True  # Found an element that satisfies φ
            finally:
                # Restore variable scope
                if old_value is not None:
                    self.variable_scope[variable] = old_value
                else:
                    self.variable_scope.pop(variable, None)
        
        return False  # No element satisfies φ
    
    def _evaluate_forall(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        """
        Evaluate universal quantification: ∀x ∈ Domain : φ(x)
        Example: ∀n ∈ neighbors : patched(n) = true
        """
        variable = condition.get('variable')  # x
        domain = condition.get('domain')      # Domain to quantify over
        formula = condition.get('formula')    # φ(x)
        
        if not all([variable, domain, formula]):
            raise ValueError("Forall quantifier requires 'variable', 'domain', and 'formula'")
        
        domain_elements = self._get_domain_elements(domain, node, network_context)
        
        # Check if ∀x : φ(x) is true for all x in domain
        for element in domain_elements:
            # Bind variable to current element
            old_value = self.variable_scope.get(variable)
            self.variable_scope[variable] = element
            
            try:
                if not self.evaluate_condition(formula, element if isinstance(element, Node) else node, actor_access, actor_id, network_context):
                    return False  # Found an element that violates φ
            finally:
                # Restore variable scope
                if old_value is not None:
                    self.variable_scope[variable] = old_value
                else:
                    self.variable_scope.pop(variable, None)
        
        return True  # All elements satisfy φ
    
    def _get_domain_elements(self, domain: Dict[str, Any], node: Node, network_context: Dict = None) -> List[Any]:
        """Get elements for quantification domain"""
        domain_type = domain.get('type')
        
        if domain_type == 'neighbors':
            # Get neighboring nodes
            return [link.get_other_node(node) for link in node.links if link.get_other_node(node)]
        elif domain_type == 'network_nodes':
            # Get all nodes in network
            if network_context and 'nodes' in network_context:
                return list(network_context['nodes'].values())
            return []
        elif domain_type == 'vulnerabilities':
            # Get node vulnerabilities
            return getattr(node, 'vulnerabilities', [])
        elif domain_type == 'assets':
            # Get node assets  
            return getattr(node, 'assets', [])
        elif domain_type == 'software':
            # Get software packages
            return list(getattr(node, 'software', {}).keys())
        elif domain_type == 'range':
            # Numeric range [start, end]
            start = domain.get('start', 0)
            end = domain.get('end', 0)
            return list(range(start, end + 1))
        else:
            raise ValueError(f"Unknown domain type: {domain_type}")
    
    def _evaluate_variable_ref(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str) -> bool:
        """Evaluate variable reference in quantified formula"""
        variable = condition.get('variable')
        property_name = condition.get('property')
        operator = condition.get('operator', 'equals')
        value = condition.get('value')
        
        if variable not in self.variable_scope:
            raise ValueError(f"Unbound variable: {variable}")
        
        element = self.variable_scope[variable]
        
        # Get property value from bound element
        if isinstance(element, Node):
            actual_value = getattr(element, property_name, None)
        elif isinstance(element, str):
            actual_value = element  # String elements
        else:
            actual_value = element
        
        # Apply operator
        if operator == 'equals':
            return actual_value == value
        elif operator == 'not_equals':
            return actual_value != value
        elif operator == 'greater_than':
            return actual_value > value
        elif operator == 'less_than':
            return actual_value < value
        elif operator == 'contains':
            return value in actual_value if actual_value else False
        else:
            raise ValueError(f"Unknown variable operator: {operator}")
    
    def _evaluate_software_check(self, condition: Dict[str, Any], node: Node) -> bool:
        """Check software properties"""
        software_key = condition['software_key']
        operator = condition['operator']
        
        actual_value = node.get_software(software_key)
        
        if operator == 'equals':
            return actual_value == condition['value']
        elif operator == 'not_equals':
            return actual_value != condition['value']
        elif operator == 'in':
            return actual_value in condition['values']
        elif operator == 'not_in':
            return actual_value not in condition['values']
        elif operator == 'exists':
            return actual_value is not None and actual_value != ""
        elif operator == 'not_exists':
            return actual_value is None or actual_value == ""
        else:
            raise ValueError(f"Unknown software check operator: {operator}")
    
    def _evaluate_version_check(self, condition: Dict[str, Any], node: Node) -> bool:
        """Check software version comparisons"""
        software_key = condition['software_key']
        operator = condition['operator']
        expected_version = Version(condition['value'])
        
        actual_version_str = node.get_software(software_key)
        if not actual_version_str:
            return False
            
        actual_version = Version(actual_version_str)
        
        if operator == 'less_than':
            return actual_version < expected_version
        elif operator == 'less_equal':
            return actual_version <= expected_version
        elif operator == 'greater_than':
            return actual_version > expected_version
        elif operator == 'greater_equal':
            return actual_version >= expected_version
        elif operator == 'equals':
            return actual_version == expected_version
        elif operator == 'not_equals':
            return actual_version != expected_version
        elif operator == 'between':
            min_version = Version(condition['min_value'])
            max_version = Version(condition['max_value'])
            return min_version <= actual_version <= max_version
        else:
            raise ValueError(f"Unknown version check operator: {operator}")
    
    def _evaluate_access_check(self, condition: Dict[str, Any], actor_access: str, actor_id: str) -> bool:
        """Check actor access level with enhanced operators"""
        operator = condition['operator']
        
        if operator == 'equals':
            expected_access = condition['value']
            return actor_access == expected_access
        elif operator == 'not_equals':
            expected_access = condition['value']
            return actor_access != expected_access
        elif operator == 'in':
            return actor_access in condition['values']
        elif operator == 'greater_than':
            # Access hierarchy: NONE < VISIBLE < USER < ADMIN
            access_levels = {'NONE': 0, 'VISIBLE': 1, 'USER': 2, 'ADMIN': 3}
            current_level = access_levels.get(actor_access, 0)
            required_level = access_levels.get(condition['value'], 0)
            return current_level > required_level
        elif operator == 'greater_equal':
            access_levels = {'NONE': 0, 'VISIBLE': 1, 'USER': 2, 'ADMIN': 3}
            current_level = access_levels.get(actor_access, 0)
            required_level = access_levels.get(condition['value'], 0)
            return current_level >= required_level
        else:
            raise ValueError(f"Unknown access check operator: {operator}")
    
    def _evaluate_property_check(self, condition: Dict[str, Any], node: Node) -> bool:
        """Check node properties"""
        property_name = condition['property']
        operator = condition['operator']
        expected_value = condition['value']
        
        actual_value = getattr(node, property_name, None)
        
        if operator == 'equals':
            return actual_value == expected_value
        elif operator == 'not_equals':
            return actual_value != expected_value
        elif operator == 'exists':
            return actual_value is not None
        elif operator == 'not_exists':
            return actual_value is None
        else:
            raise ValueError(f"Unknown property check operator: {operator}")
    
    def _evaluate_vulnerability_check(self, condition: Dict[str, Any], node: Node) -> bool:
        """Check vulnerability-related conditions"""
        # Check for specific CVE presence
        if 'cve' in condition:
            cve_id = condition['cve']
            status = condition.get('status', 'present')
            node_vulns = getattr(node, 'vulnerabilities', [])
            
            if status == 'present':
                return cve_id in node_vulns
            elif status == 'absent':
                return cve_id not in node_vulns
            else:
                raise ValueError(f"Unknown CVE status: {status}")
        
        # Legacy vulnerability count checking
        check_type = condition.get('check_type', 'count')
        operator = condition['operator']
        
        if check_type == 'count':
            vuln_count = len(getattr(node, 'vulnerabilities', []))
            expected_count = condition['value']
            
            if operator == 'greater_than':
                return vuln_count > expected_count
            elif operator == 'less_than':
                return vuln_count < expected_count
            elif operator == 'equals':
                return vuln_count == expected_count
            else:
                raise ValueError(f"Unknown vulnerability count operator: {operator}")
        
        raise ValueError(f"Unknown vulnerability check type: {check_type}")
    
    def _evaluate_assets_check(self, condition: Dict[str, Any], node: Node) -> bool:
        """Check asset-related conditions"""
        check_type = condition.get('check_type', 'count')
        operator = condition['operator']
        
        if check_type == 'count':
            assets_count = len(getattr(node, 'assets', []))
            expected_count = condition['value']
            
            if operator == 'greater_than':
                return assets_count > expected_count
            elif operator == 'less_than':
                return assets_count < expected_count
            elif operator == 'equals':
                return assets_count == expected_count
            else:
                raise ValueError(f"Unknown assets count operator: {operator}")
        
        raise ValueError(f"Unknown assets check type: {check_type}")
        
    def _evaluate_network_check(self, condition: Dict[str, Any], node: Node, network_context: Dict = None) -> bool:
        """Check network conditions with topology awareness"""
        check_type = condition.get('check_type', 'port_access')
        
        if check_type == 'port_access':
            ports = condition.get('ports', [])
            accessible = condition.get('accessible', True)
            
            node_exposed_services = getattr(node, 'exposed_services', [])
            
            if accessible:
                return any(port in node_exposed_services for port in ports)
            else:
                return not any(port in node_exposed_services for port in ports)
        
        elif check_type == 'neighbor_count':
            operator = condition.get('operator', 'equals')
            value = condition.get('value', 0)
            neighbor_count = len(node.links)
            
            if operator == 'equals':
                return neighbor_count == value
            elif operator == 'greater_than':
                return neighbor_count > value
            elif operator == 'less_than':
                return neighbor_count < value
            else:
                raise ValueError(f"Unknown neighbor_count operator: {operator}")
        
        elif check_type == 'path_exists':
            # Check if path exists to target node
            target_id = condition.get('target_id')
            if not network_context or not target_id:
                return False
            
            # Simple BFS to check connectivity
            visited = set()
            queue = [node]
            
            while queue:
                current = queue.pop(0)
                if current.id == target_id:
                    return True
                
                if current.id in visited:
                    continue
                visited.add(current.id)
                
                for link in current.links:
                    neighbor = link.get_other_node(current)
                    if neighbor and neighbor.id not in visited:
                        queue.append(neighbor)
            
            return False
        
        else:
            raise ValueError(f"Unknown network check type: {check_type}")


class ActionExecutor:
    """Executes JSON-defined postconditions"""
    
    def __init__(self):
        self._simulator = None
    
    def set_simulator(self, simulator):
        """Set simulator reference for economic tracking"""
        self._simulator = simulator
    
    def execute_postcondition(self, postcondition: Dict[str, Any], node: Node, actor_access: str, actor_id: str) -> None:
        """
        Execute a postcondition action on a node
        
        Args:
            postcondition: JSON postcondition definition
            node: Target node
            actor_access: Actor's access level
            actor_id: Actor identifier
        """
        action_type = postcondition.get('type')
        
        if action_type == 'compound':
            self._execute_compound(postcondition, node, actor_access, actor_id)
        elif action_type == 'set_access':
            self._execute_set_access(postcondition, node, actor_id)
        elif action_type == 'set_property':
            self._execute_set_property(postcondition, node)
        elif action_type == 'set_software':
            self._execute_set_software(postcondition, node)
        elif action_type == 'add_vulnerability':
            self._execute_add_vulnerability(postcondition, node)
        elif action_type == 'remove_vulnerability':
            self._execute_remove_vulnerability(postcondition, node)
        elif action_type == 'increment_counter':
            self._execute_increment_counter(postcondition, node)
        elif action_type == 'set_links_access':
            self._execute_set_links_access(postcondition, node, actor_id)
        elif action_type == 'clear_assets':
            self._execute_clear_assets(postcondition, node)
        elif action_type == 'add_capability':
            self._execute_add_capability(postcondition, node)
        elif action_type == 'remove_capability':
            self._execute_remove_capability(postcondition, node)
        else:
            raise ValueError(f"Unknown postcondition type: {action_type}")
    
    def _execute_compound(self, postcondition: Dict[str, Any], node: Node, actor_access: str, actor_id: str) -> None:
        """Execute multiple actions"""
        actions = postcondition.get('actions', [])
        for action in actions:
            self.execute_postcondition(action, node, actor_access, actor_id)
    
    def _execute_set_access(self, action: Dict[str, Any], node: Node, actor_id: str) -> None:
        """Set actor access level on node"""
        access_level = action['value']
        if not hasattr(node, 'access'):
            node.access = {}
        
        # Record old access for economic model
        old_access = node.access.get(actor_id, "NONE")
        node.access[actor_id] = access_level
        
        # Notify economic model of access change if simulator is available
        if hasattr(self, '_simulator') and self._simulator:
            self._simulator.record_access_change(node, actor_id, old_access, access_level)
    
    def _execute_set_property(self, action: Dict[str, Any], node: Node) -> None:
        """Set a node property"""
        property_name = action['property']
        value = action['value']
        setattr(node, property_name, value)
    
    def _execute_set_software(self, action: Dict[str, Any], node: Node) -> None:
        """Update software information"""
        software_key = action['software_key']
        value = action['value']
        if not hasattr(node, 'software'):
            node.software = {}
        node.software[software_key] = value
    
    def _execute_add_vulnerability(self, action: Dict[str, Any], node: Node) -> None:
        """Add a vulnerability"""
        vulnerability = action['vulnerability']
        if not hasattr(node, 'vulnerabilities'):
            node.vulnerabilities = []
        node.vulnerabilities.append(vulnerability)
    
    def _execute_remove_vulnerability(self, action: Dict[str, Any], node: Node) -> None:
        """Remove vulnerability(ies)"""
        if not hasattr(node, 'vulnerabilities'):
            node.vulnerabilities = []
            return
            
        # Check for specific CVE removal
        if 'cve' in action:
            cve_id = action['cve']
            if cve_id in node.vulnerabilities:
                node.vulnerabilities.remove(cve_id)
            return
            
        # Check for vulnerability field (new format)
        if 'vulnerability' in action:
            vuln_id = action['vulnerability']
            if vuln_id in node.vulnerabilities:
                node.vulnerabilities.remove(vuln_id)
            return
            
        # Legacy vulnerability removal methods
        method = action.get('method', 'pop')
        
        if method == 'pop' and len(node.vulnerabilities) > 0:
            node.vulnerabilities.pop()
        elif method == 'multiple':
            count = action.get('count', 1)
            for _ in range(min(count, len(node.vulnerabilities))):
                if node.vulnerabilities:
                    node.vulnerabilities.pop()
        elif method == 'specific':
            vulnerability = action['vulnerability']
            if vulnerability in node.vulnerabilities:
                node.vulnerabilities.remove(vulnerability)
        elif method == 'all':
            node.vulnerabilities.clear()
    
    def _execute_increment_counter(self, action: Dict[str, Any], node: Node) -> None:
        """Increment a counter property"""
        counter_name = action['counter']
        increment = action.get('increment', 1)
        
        current_value = getattr(node, counter_name, 0)
        setattr(node, counter_name, current_value + increment)
    
    def _execute_set_links_access(self, action: Dict[str, Any], node: Node, actor_id: str) -> None:
        """Set actor access level on all links from this node"""
        access_value = action['access_value']
        for link in node.links:
            if not hasattr(link, 'access'):
                link.access = {}
            link.access[actor_id] = access_value
    
    def _execute_clear_assets(self, action: Dict[str, Any], node: Node) -> None:
        """Clear all assets from a node"""
        if hasattr(node, 'assets'):
            node.assets.clear()
            
    def _execute_add_capability(self, action: Dict[str, Any], node: Node) -> None:
        """Add a capability to a node"""
        capability = action['capability']
        if not hasattr(node, 'capabilities'):
            node.capabilities = []
        if capability not in node.capabilities:
            node.capabilities.append(capability)
            
    def _execute_remove_capability(self, action: Dict[str, Any], node: Node) -> None:
        """Remove a capability from a node"""
        capability = action['capability']
        if hasattr(node, 'capabilities') and capability in node.capabilities:
            node.capabilities.remove(capability)


# Global instances
condition_evaluator = ConditionEvaluator()
action_executor = ActionExecutor()
