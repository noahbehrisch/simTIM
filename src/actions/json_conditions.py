from typing import Dict, Any, List, Union, Callable
from src.actions.version import Version
from src.core.graph import Node, Link
from src.core.access_levels import get_access_level_value, compare_access_levels

class ConditionEvaluator:
    def __init__(self):
        self.variable_scope = {}

    def evaluate_condition(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        condition_type = condition.get('type')
        if condition_type == 'compound':
            return self._evaluate_compound(condition, node, actor_access, actor_id, network_context)
        elif condition_type == 'implication':
            return self._evaluate_implication(condition, node, actor_access, actor_id, network_context)
        elif condition_type == 'negation':
            return self._evaluate_negation(condition, node, actor_access, actor_id, network_context)
        elif condition_type == 'exists':
            return self._evaluate_exists(condition, node, actor_access, actor_id, network_context)
        elif condition_type == 'forall':
            return self._evaluate_forall(condition, node, actor_access, actor_id, network_context)
        elif condition_type == 'software_check':
            return self._evaluate_software_check(condition, node)
        elif condition_type == 'service_check':
            return self._evaluate_service_check(condition, node)
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
        elif condition_type == 'variable_ref':
            return self._evaluate_variable_ref(condition, node, actor_access, actor_id)
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")

    def _evaluate_compound(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        operator = condition.get('operator', 'AND')
        conditions = condition.get('conditions', [])
        if operator == 'AND':
            return all(self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions)
        elif operator == 'OR':
            return any(self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions)
        elif operator == 'XOR':
            results = [self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions]
            return sum(results) == 1
        elif operator == 'NAND':
            return not all(self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions)
        elif operator == 'NOR':
            return not any(self.evaluate_condition(cond, node, actor_access, actor_id, network_context) for cond in conditions)
        else:
            raise ValueError(f"Unknown compound operator: {operator}")

    def _evaluate_implication(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        premise = condition.get('premise')
        conclusion = condition.get('conclusion')
        if not premise or not conclusion:
            raise ValueError("Implication requires both 'premise' and 'conclusion'")
        premise_result = self.evaluate_condition(premise, node, actor_access, actor_id, network_context)
        conclusion_result = self.evaluate_condition(conclusion, node, actor_access, actor_id, network_context)
        return not premise_result or conclusion_result

    def _evaluate_negation(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        inner_condition = condition.get('condition')
        if not inner_condition:
            raise ValueError("Negation requires 'condition' field")
        return not self.evaluate_condition(inner_condition, node, actor_access, actor_id, network_context)

    def _evaluate_exists(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        variable = condition.get('variable')
        domain = condition.get('domain')
        formula = condition.get('formula')
        if not all([variable, domain, formula]):
            raise ValueError("Exists quantifier requires 'variable', 'domain', and 'formula'")
        domain_elements = self._get_domain_elements(domain, node, network_context)
        for element in domain_elements:
            old_value = self.variable_scope.get(variable)
            self.variable_scope[variable] = element
            try:
                if self.evaluate_condition(formula, element if isinstance(element, Node) else node, actor_access, actor_id, network_context):
                    return True
            finally:
                if old_value is not None:
                    self.variable_scope[variable] = old_value
                else:
                    self.variable_scope.pop(variable, None)
        return False

    def _evaluate_forall(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str, network_context: Dict = None) -> bool:
        variable = condition.get('variable')
        domain = condition.get('domain')
        formula = condition.get('formula')
        if not all([variable, domain, formula]):
            raise ValueError("Forall quantifier requires 'variable', 'domain', and 'formula'")
        domain_elements = self._get_domain_elements(domain, node, network_context)
        for element in domain_elements:
            old_value = self.variable_scope.get(variable)
            self.variable_scope[variable] = element
            try:
                if not self.evaluate_condition(formula, element if isinstance(element, Node) else node, actor_access, actor_id, network_context):
                    return False
            finally:
                if old_value is not None:
                    self.variable_scope[variable] = old_value
                else:
                    self.variable_scope.pop(variable, None)
        return True

    def _get_domain_elements(self, domain: Dict[str, Any], node: Node, network_context: Dict = None) -> List[Any]:
        domain_type = domain.get('type')
        if domain_type == 'neighbors':
            return [link.get_other_node(node) for link in node.links if link.get_other_node(node)]
        elif domain_type == 'network_nodes':
            if network_context and 'nodes' in network_context:
                return list(network_context['nodes'].values())
            return []
        elif domain_type == 'vulnerabilities':
            return getattr(node, 'vulnerabilities', [])
        elif domain_type == 'assets':
            return getattr(node, 'assets', [])
        elif domain_type == 'software':
            return list(getattr(node, 'software', {}).keys())
        elif domain_type == 'range':
            start = domain.get('start', 0)
            end = domain.get('end', 0)
            return list(range(start, end + 1))
        else:
            raise ValueError(f"Unknown domain type: {domain_type}")

    def _evaluate_variable_ref(self, condition: Dict[str, Any], node: Node, actor_access: str, actor_id: str) -> bool:
        variable = condition.get('variable')
        property_name = condition.get('property')
        operator = condition.get('operator', 'equals')
        value = condition.get('value')
        if variable not in self.variable_scope:
            raise ValueError(f"Unbound variable: {variable}")
        element = self.variable_scope[variable]
        if isinstance(element, Node):
            actual_value = getattr(element, property_name, None)
        elif isinstance(element, str):
            actual_value = element
        else:
            actual_value = element
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

    def _evaluate_service_check(self, condition: Dict[str, Any], node: Node) -> bool:
        service = condition['service']
        status = condition.get('status', 'running')
        
        # Check if node has services attribute
        if not hasattr(node, 'services'):
            node.services = {}
        
        # Get service status (default to 'stopped' if not found)
        service_status = node.services.get(service, 'stopped')
        
        # Check against expected status
        if status == 'running':
            return service_status == 'running'
        elif status == 'stopped':
            return service_status == 'stopped'
        elif status == 'exists':
            return service in node.services
        else:
            return service_status == status

    def _evaluate_version_check(self, condition: Dict[str, Any], node: Node) -> bool:
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
            current_level = get_access_level_value(actor_access)
            required_level = get_access_level_value(condition['value'])
            return current_level > required_level
        elif operator == 'greater_equal':
            current_level = get_access_level_value(actor_access)
            required_level = get_access_level_value(condition['value'])
            return current_level >= required_level
        else:
            raise ValueError(f"Unknown access check operator: {operator}")

    def _evaluate_property_check(self, condition: Dict[str, Any], node: Node) -> bool:
        property_name = condition['property']
        operator = condition['operator']
        expected_value = condition['value']
        
        # First try to get from properties dictionary, then fall back to direct attribute
        if hasattr(node, 'properties') and property_name in node.properties:
            actual_value = node.properties[property_name]
        else:
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
            target_id = condition.get('target_id')
            if not network_context or not target_id:
                return False
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
    def __init__(self):
        self._simulator = None

    def set_simulator(self, simulator):
        self._simulator = simulator

    def execute_postcondition(self, postcondition: Dict[str, Any], node: Node, actor_access: str, actor_id: str) -> None:
        action_type = postcondition.get('type')
        if action_type == 'compound':
            self._execute_compound(postcondition, node, actor_access, actor_id)
        elif action_type == 'set_access':
            self._execute_set_access(postcondition, node, actor_id)
        elif action_type == 'set_property':
            self._execute_set_property(postcondition, node)
        elif action_type == 'modify_property':
            self._execute_modify_property(postcondition, node)
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
        actions = postcondition.get('actions', [])
        for action in actions:
            self.execute_postcondition(action, node, actor_access, actor_id)

    def _execute_set_access(self, action: Dict[str, Any], node: Node, actor_id: str) -> None:
        access_level = action['value']
        if not hasattr(node, 'access'):
            node.access = {}
        old_access = node.access.get(actor_id, "NONE")
        node.access[actor_id] = access_level
        
        # Set compromised flag when attacker gains USER or higher access
        if access_level in ["USER", "ADMIN", "ROOT"] and old_access in ["NONE", "VISIBLE"]:
            node.compromised = True
            # Also update the actor's compromised nodes set if it's an attacker
            if hasattr(self, '_simulator') and self._simulator:
                for actor in self._simulator.get_all_actors():
                    if actor.id == actor_id and hasattr(actor, 'compromised_nodes'):
                        # Ensure we're working with a Node object that has an id attribute
                        if hasattr(node, 'id'):
                            actor.compromised_nodes.add(node.id)
        
        # Notify about node discovery when going from NONE to VISIBLE
        if old_access == "NONE" and access_level == "VISIBLE":
            if hasattr(self, '_simulator') and self._simulator:
                # Only notify for actual Node objects, not Link objects
                if hasattr(node, 'id'):
                    self._simulator.notify_nodes_discovered(actor_id, [node])
        
        if hasattr(self, '_simulator') and self._simulator:
            self._simulator.record_access_change(node, actor_id, old_access, access_level)

    def _execute_set_property(self, action: Dict[str, Any], node: Node) -> None:
        property_name = action['property']
        value = action['value']
        
        # Ensure node has properties dictionary
        if not hasattr(node, 'properties'):
            node.properties = {}
        
        # Set property in the properties dictionary
        node.properties[property_name] = value

    def _execute_modify_property(self, action: Dict[str, Any], node: Node) -> None:
        property_name = action['property']
        operation = action.get('operation', 'set')
        value = action['value']
        
        if not hasattr(node, property_name):
            if operation in ['add', 'subtract']:
                setattr(node, property_name, 0)
            else:
                setattr(node, property_name, None)
        
        current_value = getattr(node, property_name)
        
        if operation == 'add':
            if isinstance(current_value, (int, float)):
                setattr(node, property_name, current_value + value)
            elif isinstance(current_value, list):
                # For lists, add means append
                if not isinstance(value, list):
                    value = [value]
                setattr(node, property_name, current_value + value)
        elif operation == 'subtract':
            if isinstance(current_value, (int, float)):
                setattr(node, property_name, max(0, current_value - value))
            elif isinstance(current_value, list):
                # For lists, subtract means remove first N items
                new_list = current_value[:]
                items_to_remove = min(value, len(new_list))
                setattr(node, property_name, new_list[items_to_remove:])
        elif operation == 'multiply':
            if isinstance(current_value, (int, float)):
                setattr(node, property_name, current_value * value)
        else:  # Default to set
            setattr(node, property_name, value)

    def _execute_set_software(self, action: Dict[str, Any], node: Node) -> None:
        software_key = action['software_key']
        value = action['value']
        if not hasattr(node, 'software'):
            node.software = {}
        node.software[software_key] = value

    def _execute_add_vulnerability(self, action: Dict[str, Any], node: Node) -> None:
        vulnerability = action['vulnerability']
        if not hasattr(node, 'vulnerabilities'):
            node.vulnerabilities = []
        node.vulnerabilities.append(vulnerability)

    def _execute_remove_vulnerability(self, action: Dict[str, Any], node: Node) -> None:
        if not hasattr(node, 'vulnerabilities'):
            node.vulnerabilities = []
            return
        if 'cve' in action:
            cve_id = action['cve']
            if cve_id in node.vulnerabilities:
                node.vulnerabilities.remove(cve_id)
            return
        if 'vulnerability' in action:
            vuln_id = action['vulnerability']
            if vuln_id in node.vulnerabilities:
                node.vulnerabilities.remove(vuln_id)
            return
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
        counter_name = action['counter']
        increment = action.get('increment', 1)
        current_value = getattr(node, counter_name, 0)
        setattr(node, counter_name, current_value + increment)

    def _execute_set_links_access(self, action: Dict[str, Any], node: Node, actor_id: str) -> None:
        # Ensure we're working with a Node object that has links
        if not hasattr(node, 'links'):
            return  # Skip if not a Node object
            
        access_value = action['access_value']
        discovered_nodes = []
        
        for link in node.links:
            if not hasattr(link, 'access'):
                link.access = {}
            old_access = link.access.get(actor_id, "NONE")
            link.access[actor_id] = access_value
            
            # If this is a new discovery (from NONE to VISIBLE), track the discovered node
            if old_access == "NONE" and access_value == "VISIBLE":
                discovered_nodes.append(link)
        
        # Notify the simulator about newly discovered nodes so it can update actor visibility
        if discovered_nodes and hasattr(self, '_simulator') and self._simulator:
            self._simulator.notify_nodes_discovered(actor_id, discovered_nodes)

    def _execute_clear_assets(self, action: Dict[str, Any], node: Node) -> None:
        if hasattr(node, 'assets'):
            node.assets.clear()

    def _execute_add_capability(self, action: Dict[str, Any], node: Node) -> None:
        capability = action['capability']
        if not hasattr(node, 'capabilities'):
            node.capabilities = []
        if capability not in node.capabilities:
            node.capabilities.append(capability)

    def _execute_remove_capability(self, action: Dict[str, Any], node: Node) -> None:
        capability = action['capability']
        if hasattr(node, 'capabilities') and capability in node.capabilities:
            node.capabilities.remove(capability)
condition_evaluator = ConditionEvaluator()
action_executor = ActionExecutor()