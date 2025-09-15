from actions.action import Action
from simulator.graph import Node, Link
from enum import Enum, auto
from packaging.version import Version

class AccessNode(Enum):
    NONE = auto()
    VISIBLE = auto()
    USER = auto()
    ADMIN = auto()

class AccessLink(Enum):
    NONE = auto()
    VISIBLE = auto()


def compromise_tapestry_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return (
        node.get_software('WebApp framework name') == 'Apache Tapestry' and
        node.get_software('WebApp framework version') in {'5.4.5','5.5.0','5.6.2','5.7.0'} and
        actor_access != AccessNode.NONE.name and
        node.get_software('Endpoint protection') == 'sophos'
    )

def compromise_tapestry_post(node: Node, actor_access: str, actor_id: str) -> None:
    node.access[actor_id] = AccessNode.ADMIN.name
    node.compromised = True

def port_scan_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == AccessNode.ADMIN.name

def port_scan_post(node: Node, actor_access: str, actor_id: str) -> None:
    for link in node.links:
        if hasattr(link, 'access'):
            link.access[actor_id] = AccessLink.VISIBLE.name

def compromise_mysql_pre(link: Link, actor_access: str, actor_id: str) -> bool:
    node = link.node2
    return (
        node.get_software('DBMS name') == 'MySQL' and
        Version('8.0.0') <= Version(node.get_software('DBMS version')) <= Version('8.0.28') and
        actor_access == AccessLink.VISIBLE.name
    )

def compromise_mysql_post(link: Link, actor_access: str, actor_id: str) -> None:
    link.node2.access[actor_id] = AccessNode.ADMIN.name
    link.node2.compromised = True

def zero():
    return 0.0

def tapestry_detection_probability(node: Node, actor_access: str, actor_id: str) -> float:
    endpoint = node.get_software('Endpoint protection')
    if endpoint and endpoint.lower() == 'sophos':
        return 0.8
    return 0.2


def simple_user_attack_pre(node: Node, actor_access: str, actor_id: str) -> bool:
   return actor_access == AccessNode.USER.name

def simple_user_attack_post(node: Node, actor_access: str, actor_id: str) -> None:
   node.compromised = True

def reconnaissance_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access != AccessNode.NONE.name

def reconnaissance_post(node: Node, actor_access: str, actor_id: str) -> None:
    node.access[actor_id] = AccessNode.VISIBLE.name

def privilege_escalation_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == AccessNode.USER.name

def privilege_escalation_post(node: Node, actor_access: str, actor_id: str) -> None:
    node.access[actor_id] = AccessNode.ADMIN.name
    node.compromised = True

def data_exfiltration_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == AccessNode.ADMIN.name and len(node.assets) > 0

def data_exfiltration_post(node: Node, actor_access: str, actor_id: str) -> None:
    node.assets.clear()

compromise_tapestry = Action(
    name="Tapestry attack",
    precondition=compromise_tapestry_pre,
    postcondition=compromise_tapestry_post,
    cost=300,
    duration=1.5,
    success_probability=0.6,
    action_type="node",
    detection_probability=tapestry_detection_probability,
    one_off_damage=lambda node, access, actor: 50.0,
    one_off_gain=lambda node, access, actor: 30.0,
    time_damage=lambda node, access, actor: 10.0,
    time_gain=lambda node, access, actor: 5.0,
)

port_scan = Action(
    name="Port scan",
    precondition=port_scan_pre,
    postcondition=port_scan_post,
    cost=50,
    duration=1.0,
    success_probability=0.95,
    action_type="node",
    detection_probability=lambda node, access, actor: 0.15,
    one_off_damage=lambda node, access, actor: 0.0,
    one_off_gain=lambda node, access, actor: 20.0,
    time_damage=lambda node, access, actor: 0.0,
    time_gain=lambda node, access, actor: 0.0,
)

simple_user_attack = Action(
   name="Simple User Attack",
   precondition=simple_user_attack_pre,
   postcondition=simple_user_attack_post,
   cost=20,
   duration=0.5,
   success_probability=0.7,
   action_type="node",
   detection_probability=lambda node, access, actor: 0.1,
   one_off_damage=lambda node, access, actor: 10.0,
   one_off_gain=lambda node, access, actor: 50.0,
   time_damage=lambda node, access, actor: 0.0,
   time_gain=lambda node, access, actor: 0.0,
)

reconnaissance = Action(
    name="Reconnaissance",
    precondition=reconnaissance_pre,
    postcondition=reconnaissance_post,
    cost=50,
    duration=0.5,
    success_probability=0.9,
    action_type="node",
    detection_probability=lambda node, access, actor: 0.1,
    one_off_damage=lambda node, access, actor: 0.0,
    one_off_gain=lambda node, access, actor: 10.0,
    time_damage=lambda node, access, actor: 0.0,
    time_gain=lambda node, access, actor: 0.0,
)

privilege_escalation = Action(
    name="Privilege Escalation",
    precondition=privilege_escalation_pre,
    postcondition=privilege_escalation_post,
    cost=100,
    duration=1.0,
    success_probability=0.8,
    action_type="node",
    detection_probability=lambda node, access, actor: 0.2,
    one_off_damage=lambda node, access, actor: 0.0,
    one_off_gain=lambda node, access, actor: 20.0,
    time_damage=lambda node, access, actor: 0.0,
    time_gain=lambda node, access, actor: 0.0,
)

data_exfiltration = Action(
    name="Data Exfiltration",
    precondition=data_exfiltration_pre,
    postcondition=data_exfiltration_post,
    cost=200,
    duration=2.0,
    success_probability=0.7,
    action_type="node",
    detection_probability=lambda node, access, actor: 0.3,
    one_off_damage=lambda node, access, actor: 50.0,
    one_off_gain=lambda node, access, actor: 100.0,
    time_damage=lambda node, access, actor: 0.0,
    time_gain=lambda node, access, actor: 0.0,
)

compromise_mysql = Action(
    name="Remote attack on MySQL",
    precondition=compromise_mysql_pre,
    postcondition=compromise_mysql_post,
    cost=800,
    duration=2.0,
    success_probability=0.7,
    action_type="link",
    detection_probability=lambda node, access, actor: 0.25,
    one_off_damage=lambda node, access, actor: 100.0,
    one_off_gain=lambda node, access, actor: 80.0,
    time_damage=lambda node, access, actor: 20.0,
    time_gain=lambda node, access, actor: 10.0,
)

node_attack_actions = [
    compromise_tapestry,
    port_scan,
    simple_user_attack,
    reconnaissance,
    privilege_escalation,
    data_exfiltration
]

link_attack_actions = [
    compromise_mysql
]

all_attack_actions = node_attack_actions + link_attack_actions

def get_all_attack_actions_from_json():
    from actions.action_loader import get_attack_actions
    return get_attack_actions()

