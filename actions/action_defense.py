from actions.action import Action
from simulator.graph import Node
from enum import Enum
from packaging.version import Version

def upgrade_mysql_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    dbms_name = node.get_software('DBMS name')
    dbms_version = node.get_software('DBMS version')
    return (
        dbms_name == 'MySQL' and
        Version(dbms_version) < Version('9.0.1') and
        actor_access == 'ADMIN'
    )

def upgrade_mysql_post(node: Node, actor_access: str, actor_id: str) -> None:
    node.software['DBMS version'] = '9.0.1'

def zero():
    return 0.0

def system_patch_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == 'ADMIN' and len(node.vulnerabilities) > 0

def system_patch_post(node: Node, actor_access: str, actor_id: str) -> None:
    if len(node.vulnerabilities) > 0:
        node.vulnerabilities.pop()
        if not hasattr(node, 'security_patches'):
            node.security_patches = 0
        node.security_patches += 1

def firewall_update_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == 'ADMIN'

def firewall_update_post(node: Node, actor_access: str, actor_id: str) -> None:
    if not hasattr(node, 'firewall_rules'):
        node.firewall_rules = 0
    node.firewall_rules += 1

def ids_deploy_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == 'ADMIN'

def ids_deploy_post(node: Node, actor_access: str, actor_id: str) -> None:
    if not hasattr(node, 'ids_deployed'):
        node.ids_deployed = True
        node.detection_capability = 0.3

def incident_response_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == 'ADMIN' and node.compromised

def incident_response_post(node: Node, actor_access: str, actor_id: str) -> None:
    node.compromised = False
    if not hasattr(node, 'incident_responses'):
        node.incident_responses = 0
    node.incident_responses += 1

def security_monitoring_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == 'ADMIN'

def security_monitoring_post(node: Node, actor_access: str, actor_id: str) -> None:
    if not hasattr(node, 'monitoring_enabled'):
        node.monitoring_enabled = True
        node.alert_capability = 0.2

def vuln_remediation_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == 'ADMIN' and len(node.vulnerabilities) > 1

def vuln_remediation_post(node: Node, actor_access: str, actor_id: str) -> None:
    original_vulns = len(node.vulnerabilities)

    for _ in range(min(2, len(node.vulnerabilities))):
        if node.vulnerabilities:
            node.vulnerabilities.pop()
    if not hasattr(node, 'hardening_level'):
        node.hardening_level = 0
    node.hardening_level += 1

upgrade_mysql = Action(
    name="Upgrading MySQL to new version",
    precondition=upgrade_mysql_pre,
    postcondition=upgrade_mysql_post,
    cost=500,
    duration=1.0,
    success_probability=0.9,
    action_type="node",
    detection_probability=zero,
    one_off_damage=zero,
    one_off_gain=zero,
    time_damage=zero,
    time_gain=zero,
)

node_defense_actions = [upgrade_mysql]
link_defense_actions = []
all_defense_actions = node_defense_actions + link_defense_actions

def get_all_defense_actions_from_json():
    from actions.action_loader import get_defense_actions
    return get_defense_actions()