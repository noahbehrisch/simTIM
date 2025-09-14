from actions.action import Action
from simulator.network import Node
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

# Example defense actions

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