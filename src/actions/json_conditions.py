from __future__ import annotations

import logging
from typing import Any

from src.core.access_levels import (
    LinkAccessLevel,
    NodeAccessLevel,
    validate_link_access,
    validate_node_access,
)
from src.core.access_utils import (
    get_link_access,
    get_node_access,
    set_link_access,
    set_node_access,
)
from src.core.graph import Link, Node
from src.utils.version import Version

# Import directly from modules to avoid circular imports through src.core.__init__

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    def __init__(self):
        self.variable_scope = {}
        self._simulator = None

    def set_simulator(self, simulator):
        """Set simulator reference for time-based condition checks."""
        self._simulator = simulator

    def evaluate_condition(
        self,
        condition: dict[str, Any],
        node: Node,
        actor_access: str,
        actor_id: str,
        network_context: dict | None = None,
    ) -> bool:
        condition_type = condition.get("type")
        if condition_type == "compound":
            return self._evaluate_compound(condition, node, actor_access, actor_id, network_context)
        elif condition_type == "implication":
            return self._evaluate_implication(
                condition, node, actor_access, actor_id, network_context
            )
        elif condition_type == "negation":
            return self._evaluate_negation(condition, node, actor_access, actor_id, network_context)
        elif condition_type == "exists":
            return self._evaluate_exists(condition, node, actor_access, actor_id, network_context)
        elif condition_type == "forall":
            return self._evaluate_forall(condition, node, actor_access, actor_id, network_context)
        elif condition_type == "software_check":
            return self._evaluate_software_check(condition, node)
        elif condition_type == "service_check":
            return self._evaluate_service_check(condition, node)
        elif condition_type == "version_check":
            return self._evaluate_version_check(condition, node)
        elif condition_type == "access_check":
            return self._evaluate_access_check(condition, actor_access, actor_id)
        elif condition_type == "property_check":
            return self._evaluate_property_check(condition, node)
        elif condition_type == "vulnerability_check":
            return self._evaluate_vulnerability_check(condition, node)
        elif condition_type == "assets_check":
            return self._evaluate_assets_check(condition, node)
        elif condition_type == "network_check":
            return self._evaluate_network_check(condition, node, network_context)
        elif condition_type == "variable_ref":
            return self._evaluate_variable_ref(condition, node, actor_access, actor_id)
        # Link action condition types (for actions with action_type: "link")
        elif condition_type == "start_node_access_check":
            return self._evaluate_start_node_access_check(condition, node, actor_id)
        elif condition_type == "end_node_access_check":
            return self._evaluate_end_node_access_check(condition, node, actor_id)
        elif condition_type == "start_node_property_check":
            return self._evaluate_start_node_property_check(condition, node)
        elif condition_type == "end_node_property_check":
            return self._evaluate_end_node_property_check(condition, node)
        elif condition_type == "link_property_check":
            return self._evaluate_link_property_check(condition, node)
        elif condition_type == "time_check":
            return self._evaluate_time_check(condition, node)
        else:
            raise ValueError(f"Unknown condition type: {condition_type}")

    def _evaluate_compound(
        self,
        condition: dict[str, Any],
        node: Node,
        actor_access: str,
        actor_id: str,
        network_context: dict | None = None,
    ) -> bool:
        operator = condition.get("operator", "AND")
        conditions = condition.get("conditions", [])
        if operator == "AND":
            return all(
                self.evaluate_condition(cond, node, actor_access, actor_id, network_context)
                for cond in conditions
            )
        elif operator == "OR":
            return any(
                self.evaluate_condition(cond, node, actor_access, actor_id, network_context)
                for cond in conditions
            )
        elif operator == "XOR":
            results = [
                self.evaluate_condition(cond, node, actor_access, actor_id, network_context)
                for cond in conditions
            ]
            return sum(results) == 1
        elif operator == "NAND":
            return not all(
                self.evaluate_condition(cond, node, actor_access, actor_id, network_context)
                for cond in conditions
            )
        elif operator == "NOR":
            return not any(
                self.evaluate_condition(cond, node, actor_access, actor_id, network_context)
                for cond in conditions
            )
        else:
            raise ValueError(f"Unknown compound operator: {operator}")

    def _evaluate_implication(
        self,
        condition: dict[str, Any],
        node: Node,
        actor_access: str,
        actor_id: str,
        network_context: dict | None = None,
    ) -> bool:
        premise = condition.get("premise")
        conclusion = condition.get("conclusion")
        if not premise or not conclusion:
            raise ValueError("Implication requires both 'premise' and 'conclusion'")
        premise_result = self.evaluate_condition(
            premise, node, actor_access, actor_id, network_context
        )
        conclusion_result = self.evaluate_condition(
            conclusion, node, actor_access, actor_id, network_context
        )
        return not premise_result or conclusion_result

    def _evaluate_negation(
        self,
        condition: dict[str, Any],
        node: Node,
        actor_access: str,
        actor_id: str,
        network_context: dict | None = None,
    ) -> bool:
        inner_condition = condition.get("condition")
        if not inner_condition:
            raise ValueError("Negation requires 'condition' field")
        return not self.evaluate_condition(
            inner_condition, node, actor_access, actor_id, network_context
        )

    def _evaluate_exists(
        self,
        condition: dict[str, Any],
        node: Node,
        actor_access: str,
        actor_id: str,
        network_context: dict | None = None,
    ) -> bool:
        variable = condition.get("variable")
        domain = condition.get("domain")
        formula = condition.get("formula")
        if not all([variable, domain, formula]):
            raise ValueError("Exists quantifier requires 'variable', 'domain', and 'formula'")
        assert domain is not None and formula is not None  # Type narrowing
        domain_elements = self._get_domain_elements(domain, node, network_context)
        for element in domain_elements:
            old_value = self.variable_scope.get(variable)
            self.variable_scope[variable] = element
            try:
                if self.evaluate_condition(
                    formula,
                    element if isinstance(element, Node) else node,
                    actor_access,
                    actor_id,
                    network_context,
                ):
                    return True
            finally:
                if old_value is not None:
                    self.variable_scope[variable] = old_value
                else:
                    self.variable_scope.pop(variable, None)
        return False

    def _evaluate_forall(
        self,
        condition: dict[str, Any],
        node: Node,
        actor_access: str,
        actor_id: str,
        network_context: dict | None = None,
    ) -> bool:
        variable = condition.get("variable")
        domain = condition.get("domain")
        formula = condition.get("formula")
        if not all([variable, domain, formula]):
            raise ValueError("Forall quantifier requires 'variable', 'domain', and 'formula'")
        assert domain is not None and formula is not None  # Type narrowing
        domain_elements = self._get_domain_elements(domain, node, network_context)
        for element in domain_elements:
            old_value = self.variable_scope.get(variable)
            self.variable_scope[variable] = element
            try:
                if not self.evaluate_condition(
                    formula,
                    element if isinstance(element, Node) else node,
                    actor_access,
                    actor_id,
                    network_context,
                ):
                    return False
            finally:
                if old_value is not None:
                    self.variable_scope[variable] = old_value
                else:
                    self.variable_scope.pop(variable, None)
        return True

    def _get_domain_elements(
        self, domain: dict[str, Any], node: Node, network_context: dict | None = None
    ) -> list[Any]:
        domain_type = domain.get("type")
        if domain_type == "neighbors":
            return [link.get_other_node(node) for link in node.links if link.get_other_node(node)]
        elif domain_type == "network_nodes":
            if network_context and "nodes" in network_context:
                return list(network_context["nodes"].values())
            return []
        elif domain_type == "vulnerabilities":
            return getattr(node, "vulnerabilities", [])
        elif domain_type == "assets":
            return getattr(node, "assets", [])
        elif domain_type == "software":
            return list(getattr(node, "software", {}).keys())
        elif domain_type == "range":
            start = domain.get("start", 0)
            end = domain.get("end", 0)
            return list(range(start, end + 1))
        else:
            raise ValueError(f"Unknown domain type: {domain_type}")

    def _evaluate_variable_ref(
        self, condition: dict[str, Any], node: Node, actor_access: str, actor_id: str
    ) -> bool:
        variable = condition.get("variable")
        property_name = condition.get("property")
        operator = condition.get("operator", "equals")
        value = condition.get("value")
        if variable not in self.variable_scope:
            raise ValueError(f"Unbound variable: {variable}")
        element = self.variable_scope[variable]
        actual_value: Any
        if isinstance(element, Node):
            actual_value = getattr(element, property_name or "", None)
        elif isinstance(element, str):
            actual_value = element
        else:
            actual_value = element
        if operator == "equals":
            return actual_value == value
        elif operator == "not_equals":
            return actual_value != value
        elif operator == "greater_than":
            return actual_value is not None and value is not None and actual_value > value
        elif operator == "less_than":
            return actual_value is not None and value is not None and actual_value < value
        elif operator == "contains":
            return value in actual_value if actual_value else False
        else:
            raise ValueError(f"Unknown variable operator: {operator}")

    def _evaluate_software_check(self, condition: dict[str, Any], node: Node) -> bool:
        software_key = condition["software_key"]
        operator = condition["operator"]
        actual_value = node.get_software(software_key)
        if operator == "equals":
            return actual_value == condition["value"]
        elif operator == "not_equals":
            return actual_value != condition["value"]
        elif operator == "in":
            return actual_value in condition["values"]
        elif operator == "not_in":
            return actual_value not in condition["values"]
        elif operator == "exists":
            return actual_value is not None and actual_value != ""
        elif operator == "not_exists":
            return actual_value is None or actual_value == ""
        else:
            raise ValueError(f"Unknown software check operator: {operator}")

    def _evaluate_service_check(self, condition: dict[str, Any], node: Node) -> bool:
        service = condition["service"]
        status = condition.get("status", "running")
        if not hasattr(node, "services"):
            node.services = {}
        service_status = node.services.get(service, "stopped")
        if status == "running":
            return service_status == "running"
        elif status == "stopped":
            return service_status == "stopped"
        elif status == "exists":
            return service in node.services
        else:
            return service_status == status

    def _evaluate_version_check(self, condition: dict[str, Any], node: Node) -> bool:
        software_key = condition["software_key"]
        operator = condition["operator"]
        expected_version = Version(condition["value"])
        actual_version_str = node.get_software(software_key)
        if not actual_version_str:
            return False
        actual_version = Version(actual_version_str)
        if operator == "less_than":
            return actual_version < expected_version
        elif operator == "less_equal":
            return actual_version <= expected_version
        elif operator == "greater_than":
            return actual_version > expected_version
        elif operator == "greater_equal":
            return actual_version >= expected_version
        elif operator == "equals":
            return actual_version == expected_version
        elif operator == "not_equals":
            return actual_version != expected_version
        elif operator == "between":
            min_version = Version(condition["min_value"])
            max_version = Version(condition["max_value"])
            return min_version <= actual_version <= max_version
        else:
            raise ValueError(f"Unknown version check operator: {operator}")

    def _evaluate_access_check(
        self, condition: dict[str, Any], actor_access, actor_id: str
    ) -> bool:
        if isinstance(actor_access, str):
            actor_access = validate_node_access(actor_access)
        elif not isinstance(actor_access, NodeAccessLevel):
            actor_access = validate_node_access(actor_access)
        operator = condition["operator"]
        if operator == "equals":
            expected_access = validate_node_access(condition["value"])
            return actor_access == expected_access
        elif operator == "not_equals":
            expected_access = validate_node_access(condition["value"])
            return actor_access != expected_access
        elif operator == "in":
            expected_levels = [validate_node_access(v) for v in condition["values"]]
            return actor_access in expected_levels
        elif operator == "greater_than":
            required_level = validate_node_access(condition["value"])
            return actor_access > required_level
        elif operator == "greater_equal":
            required_level = validate_node_access(condition["value"])
            return actor_access >= required_level
        elif operator == "less_than":
            required_level = validate_node_access(condition["value"])
            return actor_access < required_level
        elif operator == "less_equal":
            required_level = validate_node_access(condition["value"])
            return actor_access <= required_level
        else:
            raise ValueError(f"Unknown access check operator: {operator}")

    def _evaluate_property_check(self, condition: dict[str, Any], node: Node | Link) -> bool:
        property_name = condition["property"]
        operator = condition["operator"]
        expected_value = condition["value"]
        if hasattr(node, "properties") and property_name in node.properties:  # type: ignore[union-attr]
            actual_value = node.properties[property_name]  # type: ignore[union-attr]
        else:
            actual_value = getattr(node, property_name, None)
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "exists":
            return actual_value is not None
        elif operator == "not_exists":
            return actual_value is None
        else:
            raise ValueError(f"Unknown property check operator: {operator}")

    def _evaluate_vulnerability_check(self, condition: dict[str, Any], node: Node) -> bool:
        if "cve" in condition:
            cve_id = condition["cve"]
            status = condition.get("status", "present")
            node_vulns = getattr(node, "vulnerabilities", [])
            if status == "present":
                return cve_id in node_vulns
            elif status == "absent":
                return cve_id not in node_vulns
            else:
                raise ValueError(f"Unknown CVE status: {status}")
        check_type = condition.get("check_type", "count")
        operator = condition["operator"]
        if check_type == "count":
            vuln_count = len(getattr(node, "vulnerabilities", []))
            expected_count = condition["value"]
            if operator == "greater_than":
                return vuln_count > expected_count
            elif operator == "less_than":
                return vuln_count < expected_count
            elif operator == "equals":
                return vuln_count == expected_count
            else:
                raise ValueError(f"Unknown vulnerability count operator: {operator}")
        raise ValueError(f"Unknown vulnerability check type: {check_type}")

    def _evaluate_assets_check(self, condition: dict[str, Any], node: Node) -> bool:
        check_type = condition.get("check_type", "count")
        operator = condition["operator"]
        if check_type == "count":
            assets_count = len(getattr(node, "assets", []))
            expected_count = condition["value"]
            if operator == "greater_than":
                return assets_count > expected_count
            elif operator == "less_than":
                return assets_count < expected_count
            elif operator == "equals":
                return assets_count == expected_count
            else:
                raise ValueError(f"Unknown assets count operator: {operator}")
        raise ValueError(f"Unknown assets check type: {check_type}")

    def _evaluate_network_check(
        self, condition: dict[str, Any], node: Node, network_context: dict | None = None
    ) -> bool:
        check_type = condition.get("check_type", "port_access")
        if check_type == "port_access":
            ports = condition.get("ports", [])
            accessible = condition.get("accessible", True)
            node_exposed_services = getattr(node, "exposed_services", [])
            if accessible:
                return any(port in node_exposed_services for port in ports)
            else:
                return not any(port in node_exposed_services for port in ports)
        elif check_type == "neighbor_count":
            operator = condition.get("operator", "equals")
            value = condition.get("value", 0)
            neighbor_count = len(node.links)
            if operator == "equals":
                return neighbor_count == value
            elif operator == "greater_than":
                return neighbor_count > value
            elif operator == "less_than":
                return neighbor_count < value
            else:
                raise ValueError(f"Unknown neighbor_count operator: {operator}")
        elif check_type == "path_exists":
            target_id = condition.get("target_id")
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

    # =========================================================================
    # Link Action Condition Types
    # =========================================================================
    # These extract the appropriate node from a Link and delegate to existing
    # condition evaluators. Per TIM paper Section 4.3:
    # "For a link action, Vφa contains the properties of the start and end node
    # of the link and the actor's access to the start and end node of the link."
    # =========================================================================

    def _evaluate_start_node_access_check(
        self, condition: dict[str, Any], target, actor_id: str
    ) -> bool:
        """Check actor's access to start node of a link. Delegates to _evaluate_access_check."""
        node = target.node1 if isinstance(target, Link) else target
        actor_access = get_node_access(node, actor_id)
        return self._evaluate_access_check(condition, actor_access, actor_id)

    def _evaluate_end_node_access_check(
        self, condition: dict[str, Any], target, actor_id: str
    ) -> bool:
        """Check actor's access to end node of a link. Delegates to _evaluate_access_check."""
        if not isinstance(target, Link):
            return True
        actor_access = get_node_access(target.node2, actor_id)
        return self._evaluate_access_check(condition, actor_access, actor_id)

    def _evaluate_start_node_property_check(self, condition: dict[str, Any], target) -> bool:
        """Check property on start node of a link. Delegates to _evaluate_property_check."""
        node = target.node1 if isinstance(target, Link) else target
        return self._evaluate_property_check(condition, node)

    def _evaluate_end_node_property_check(self, condition: dict[str, Any], target) -> bool:
        """Check property on end node of a link. Delegates to _evaluate_property_check."""
        if not isinstance(target, Link):
            return True
        return self._evaluate_property_check(condition, target.node2)

    def _evaluate_link_property_check(self, condition: dict[str, Any], target) -> bool:
        """Check property on the link itself. Reuses _evaluate_property_check logic."""
        if not isinstance(target, Link):
            return True
        # Treat link as a node-like object for property checking
        return self._evaluate_property_check(condition, target)

    def _evaluate_time_check(self, condition: dict[str, Any], node: Node) -> bool:
        """Check time-based conditions (cooldowns). Extends property_check with time math."""
        property_name = condition["property"]
        last_time = node.properties.get(property_name) if hasattr(node, "properties") else None
        if last_time is None:
            return True  # Never done before = condition satisfied

        current_time = self._simulator.current_time if self._simulator else 0.0
        time_since = current_time - last_time

        op = condition["operator"]
        threshold = condition["value"]
        if op == "time_since_greater_than":
            return time_since > threshold
        elif op == "time_since_less_than":
            return time_since < threshold
        raise ValueError(f"Unknown time check operator: {op}")


class ActionExecutor:
    def __init__(self):
        self._simulator = None

    def set_simulator(self, simulator):
        self._simulator = simulator

    def execute_postcondition(
        self,
        postcondition: dict[str, Any],
        node: Node,
        actor_access: str,
        actor_id: str,
    ) -> None:
        action_type = postcondition.get("type")
        if action_type == "compound":
            self._execute_compound(postcondition, node, actor_access, actor_id)
        elif action_type == "set_access":
            self._execute_set_access(postcondition, node, actor_id)
        elif action_type == "set_access_if_none":
            self._execute_set_access_if_none(postcondition, node, actor_id)
        elif action_type == "set_property":
            self._execute_set_property(postcondition, node)
        elif action_type == "modify_property":
            self._execute_modify_property(postcondition, node)
        elif action_type == "set_software":
            self._execute_set_software(postcondition, node)
        elif action_type == "add_vulnerability":
            self._execute_add_vulnerability(postcondition, node)
        elif action_type == "remove_vulnerability":
            self._execute_remove_vulnerability(postcondition, node)
        elif action_type == "increment_counter":
            self._execute_increment_counter(postcondition, node)
        elif action_type == "set_links_access":
            self._execute_set_links_access(postcondition, node, actor_id)
        elif action_type == "set_access_neighbors":
            self._execute_set_access_neighbors(postcondition, node, actor_id)
        elif action_type == "clear_assets":
            self._execute_clear_assets(postcondition, node)
        elif action_type == "add_capability":
            self._execute_add_capability(postcondition, node)
        elif action_type == "remove_capability":
            self._execute_remove_capability(postcondition, node)
        else:
            raise ValueError(f"Unknown postcondition type: {action_type}")

    def _execute_compound(
        self,
        postcondition: dict[str, Any],
        node: Node,
        actor_access: str,
        actor_id: str,
    ) -> None:
        actions = postcondition.get("actions", [])
        for action in actions:
            self.execute_postcondition(action, node, actor_access, actor_id)

    def _execute_set_access(self, action: dict[str, Any], node: Node, actor_id: str) -> None:
        access_level = action.get("access_value", action.get("value"))
        if access_level is None:
            return
        old_access = get_node_access(node, actor_id)
        set_node_access(node, actor_id, access_level)
        if isinstance(access_level, str):
            access_level = validate_node_access(access_level)
        if access_level >= NodeAccessLevel.USER and old_access < NodeAccessLevel.USER:
            node.compromised = True
            if hasattr(self, "_simulator") and self._simulator:
                for actor in self._simulator.get_all_actors():
                    if actor.id == actor_id and hasattr(actor, "compromised_nodes"):
                        if hasattr(node, "id"):
                            actor.compromised_nodes.add(node.id)
        if old_access == NodeAccessLevel.NONE and access_level == NodeAccessLevel.VISIBLE:
            if hasattr(self, "_simulator") and self._simulator:
                if hasattr(node, "id"):
                    self._simulator.notify_nodes_discovered(actor_id, [node])
        if hasattr(self, "_simulator") and self._simulator:
            self._simulator.record_access_change(node, actor_id, old_access, access_level)

    def _execute_set_access_if_none(
        self, action: dict[str, Any], node: Node, actor_id: str
    ) -> None:
        """Set access only if current access is NONE. Used for discovery actions."""
        current_access = get_node_access(node, actor_id)
        if current_access == NodeAccessLevel.NONE:
            self._execute_set_access(action, node, actor_id)

    def _execute_set_property(self, action: dict[str, Any], node: Node) -> None:
        property_name = action["property"]
        value = action["value"]

        # Handle special value placeholders
        if isinstance(value, str) and value.startswith("@"):
            value = self._resolve_special_value(value, node)

        if not hasattr(node, "properties"):
            node.properties = {}
        node.properties[property_name] = value

    def _execute_modify_property(self, action: dict[str, Any], node: Node) -> None:
        property_name = action["property"]
        operation = action.get("operation", "set")
        value = action["value"]
        if not hasattr(node, property_name):
            if operation in ["add", "subtract"]:
                setattr(node, property_name, 0)
            else:
                setattr(node, property_name, None)
        current_value = getattr(node, property_name)
        if operation == "add":
            if isinstance(current_value, int | float):
                setattr(node, property_name, current_value + value)
            elif isinstance(current_value, list):
                if not isinstance(value, list):
                    value = [value]
                setattr(node, property_name, current_value + value)
        elif operation == "subtract":
            if isinstance(current_value, int | float):
                setattr(node, property_name, max(0, current_value - value))
            elif isinstance(current_value, list):
                new_list = current_value[:]
                items_to_remove = min(value, len(new_list))
                setattr(node, property_name, new_list[items_to_remove:])
        elif operation == "multiply":
            if isinstance(current_value, int | float):
                setattr(node, property_name, current_value * value)
        else:
            setattr(node, property_name, value)

    def _execute_set_software(self, action: dict[str, Any], node: Node) -> None:
        software_key = action["software_key"]
        value = action["value"]
        if not hasattr(node, "software"):
            node.software = {}
        node.software[software_key] = value

    def _execute_add_vulnerability(self, action: dict[str, Any], node: Node) -> None:
        vulnerability = action["vulnerability"]
        if not hasattr(node, "vulnerabilities"):
            node.vulnerabilities = []
        node.vulnerabilities.append(vulnerability)

    def _execute_remove_vulnerability(self, action: dict[str, Any], node: Node) -> None:
        if not hasattr(node, "vulnerabilities"):
            node.vulnerabilities = []
            return
        if "cve" in action:
            cve_id = action["cve"]
            if cve_id in node.vulnerabilities:
                node.vulnerabilities.remove(cve_id)
            return
        if "vulnerability" in action:
            vuln_id = action["vulnerability"]
            if vuln_id in node.vulnerabilities:
                node.vulnerabilities.remove(vuln_id)
            return
        method = action.get("method", "pop")
        if method == "pop" and len(node.vulnerabilities) > 0:
            node.vulnerabilities.pop()
        elif method == "multiple":
            count = action.get("count", 1)
            for _ in range(min(count, len(node.vulnerabilities))):
                if node.vulnerabilities:
                    node.vulnerabilities.pop()
        elif method == "specific":
            vulnerability = action["vulnerability"]
            if vulnerability in node.vulnerabilities:
                node.vulnerabilities.remove(vulnerability)
        elif method == "all":
            node.vulnerabilities.clear()

    def _execute_increment_counter(self, action: dict[str, Any], node: Node) -> None:
        counter_name = action["counter"]
        increment = action.get("increment", 1)
        current_value = getattr(node, counter_name, 0)
        setattr(node, counter_name, current_value + increment)

    def _execute_set_links_access(self, action: dict[str, Any], node: Node, actor_id: str) -> None:
        if not hasattr(node, "links"):
            logger.debug(
                f"set_links_access: Node {getattr(node, 'id', '?')} has no links attribute"
            )
            return
        logger.debug(f"set_links_access on node {node.id} by {actor_id}")
        logger.debug(f"  Node has {len(node.links)} links")
        access_value = action["access_value"]
        discovered_nodes = []
        discovered_links = []
        for link in node.links:
            old_access = get_link_access(link, actor_id)
            set_link_access(link, actor_id, access_value)
            logger.debug(f"  Link access: {old_access} → {access_value}")
            if (
                old_access == LinkAccessLevel.NONE
                and validate_link_access(access_value) == LinkAccessLevel.VISIBLE
            ):
                discovered_links.append(link)
                other_node = link.get_other_node(node)
                if other_node and other_node not in discovered_nodes:
                    discovered_nodes.append(other_node)
                    logger.debug(f"  Discovered node: {other_node.id}")
        logger.debug(
            f"  Total discovered: {len(discovered_nodes)} nodes, {len(discovered_links)} links"
        )
        if discovered_nodes and hasattr(self, "_simulator") and self._simulator:
            logger.debug(f"  Notifying simulator about {len(discovered_nodes)} discovered nodes")
            self._simulator.notify_nodes_discovered(actor_id, discovered_nodes)
        if discovered_links and hasattr(self, "_simulator") and self._simulator:
            logger.debug(f"  Notifying simulator about {len(discovered_links)} discovered links")
            self._simulator.notify_links_discovered(actor_id, discovered_links)

    def _execute_set_access_neighbors(
        self, action: dict[str, Any], node: Node, actor_id: str
    ) -> None:
        if not hasattr(node, "links"):
            return
        access_value = action["access_value"]
        compromised_neighbors = []
        for link in node.links:
            other_node = link.get_other_node(node)
            if other_node and (not other_node.compromised):
                if not hasattr(other_node, "access"):
                    other_node.access = {}
                other_node.access[actor_id] = access_value
                other_node.compromised = True
                compromised_neighbors.append(other_node)
                if not hasattr(link, "access"):
                    link.access = {}
                link.access[actor_id] = "VISIBLE"
        if compromised_neighbors and hasattr(self, "_simulator") and self._simulator:
            self._simulator.notify_nodes_discovered(actor_id, compromised_neighbors)
            for actor in self._simulator.get_all_actors():
                if actor.id == actor_id and hasattr(actor, "compromised_nodes"):
                    for neighbor in compromised_neighbors:
                        if hasattr(neighbor, "id"):
                            actor.compromised_nodes.add(neighbor.id)

    def _execute_clear_assets(self, action: dict[str, Any], node: Node) -> None:
        if hasattr(node, "assets"):
            node.assets.clear()

    def _execute_add_capability(self, action: dict[str, Any], node: Node) -> None:
        capability = action["capability"]
        if not hasattr(node, "capabilities"):
            node.capabilities = []
        if capability not in node.capabilities:
            node.capabilities.append(capability)

    def _execute_remove_capability(self, action: dict[str, Any], node: Node) -> None:
        capability = action["capability"]
        if hasattr(node, "capabilities") and capability in node.capabilities:
            node.capabilities.remove(capability)

    def _resolve_special_value(self, value: str, node: Node) -> Any:
        """
        Resolve special value placeholders like @current_time, @node_id, etc.

        Supported placeholders:
        - @current_time: Current simulation time
        - @node_id: ID of the current node
        - @start_node_id: ID of start node (for link actions)
        - @end_node_id: ID of end node (for link actions)
        """
        if value == "@current_time":
            if hasattr(self, "_simulator") and self._simulator:
                return self._simulator.current_time
            return 0.0
        elif value == "@node_id":
            return getattr(node, "id", str(node))
        elif value == "@start_node_id":
            if isinstance(node, Link):
                return getattr(node.node1, "id", str(node.node1))
            return getattr(node, "id", str(node))
        elif value == "@end_node_id":
            if isinstance(node, Link):
                return getattr(node.node2, "id", str(node.node2))
            return getattr(node, "id", str(node))
        else:
            # Unknown placeholder, return as-is
            return value


condition_evaluator = ConditionEvaluator()
action_executor = ActionExecutor()
