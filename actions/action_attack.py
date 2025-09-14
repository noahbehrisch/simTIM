from actions.action import Action
from simulator.graph import Node, Link
from enum import Enum, auto
from packaging.version import Version # useful module for version comparisons, which is used qite a lot here

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
        node.get_software('Endpoint protection') == 'sophos' # maybe not the best idea to put it in the precondition? TODO: ask
    )

def compromise_tapestry_post(node: Node, actor_access: str, actor_id: str) -> None:
    node.access[actor_id] = AccessNode.ADMIN.name

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

def zero():
    return 0.0

# Definitely not the best way to do this TODO: rework
def tapestry_detection_probability(node: Node, actor_access: str, actor_id: str) -> float:
    endpoint = node.get_software('Endpoint protection')
    if endpoint and endpoint.lower() == 'sophos':
        return 0.8
    return 0.2

# Example attack actions
compromise_tapestry = Action(
    name="Tapestry attack",
    precondition=compromise_tapestry_pre,
    postcondition=compromise_tapestry_post,
    cost=300,
    duration=1.0,
    success_probability=0.2,
    action_type="node",
    detection_probability=zero,
    one_off_damage=zero,
    one_off_gain=zero,
    time_damage=zero,
    time_gain=zero,
)

port_scan = Action(
    name="Port scan",
    precondition=port_scan_pre,
    postcondition=port_scan_post,
    cost=0,
    duration=2,
    success_probability=0.9,
    action_type="node",
    detection_probability=zero,
    one_off_damage=zero,
    one_off_gain=zero,
    time_damage=zero,
    time_gain=zero,
)

compromise_mysql = Action(
    name="Remote attack on MySQL",
    precondition=compromise_mysql_pre,
    postcondition=compromise_mysql_post,
    cost=800,
    duration=1.0,
    success_probability=0.8,
    action_type="link",
    detection_probability=zero,
    one_off_damage=zero,
    one_off_gain=zero,
    time_damage=zero,
    time_gain=zero,
)

def simple_user_attack_pre(node: Node, actor_access: str, actor_id: str) -> bool:
    return actor_access == AccessNode.USER.name

def simple_user_attack_post(node: Node, actor_access: str, actor_id: str) -> None:
    node.compromised = True

simple_user_attack = Action(
    name="Simple User Attack",
    precondition=simple_user_attack_pre,
    postcondition=simple_user_attack_post,
    cost=10,
    duration=1.0,
    success_probability=1.0,
    action_type="node",
    detection_probability=zero,
    one_off_damage=zero,
    one_off_gain=lambda node, access, actor_id: 100,
    time_damage=zero,
    time_gain=zero,
)

node_attack_actions = [compromise_tapestry, port_scan, simple_user_attack]
link_attack_actions = [compromise_mysql]
all_attack_actions = node_attack_actions + link_attack_actions
