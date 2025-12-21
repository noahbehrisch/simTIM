from typing import Optional, Any, Dict, Union
from src.core.access_levels import NodeAccessLevel, LinkAccessLevel, validate_node_access, validate_link_access

def get_node_access(node, actor_id: str, default: NodeAccessLevel=None) -> NodeAccessLevel:
    if default is None:
        default = NodeAccessLevel.NONE
    if not hasattr(node, 'access'):
        node.access = {}
    access = node.access.get(actor_id, default)
    if isinstance(access, str):
        access = NodeAccessLevel.from_string(access)
        node.access[actor_id] = access
    return access if isinstance(access, NodeAccessLevel) else default

def get_node_access_string(node, actor_id: str, default: str='NONE') -> str:
    access = get_node_access(node, actor_id)
    return access.to_string()

def set_node_access(node, actor_id: str, access_level: Union[NodeAccessLevel, str]):
    if not hasattr(node, 'access'):
        node.access = {}
    if isinstance(access_level, str):
        access_level = NodeAccessLevel.from_string(access_level)
    elif not isinstance(access_level, NodeAccessLevel):
        raise TypeError(f'Expected NodeAccessLevel or str, got {type(access_level)}')
    node.access[actor_id] = access_level

def get_node_property(node, property_name: str, default: Any=None) -> Any:
    if not hasattr(node, 'properties'):
        return default
    return node.properties.get(property_name, default)

def set_node_property(node, property_name: str, value: Any):
    if not hasattr(node, 'properties'):
        node.properties = {}
    node.properties[property_name] = value

def get_node_software(node, software_key: str, default: Any=None) -> Any:
    if not hasattr(node, 'software'):
        return default
    return node.software.get(software_key, default)

def has_vulnerability(node, vuln_id: str) -> bool:
    if not hasattr(node, 'vulnerabilities'):
        return False
    return vuln_id in node.vulnerabilities

def get_node_vulnerabilities(node) -> list:
    if not hasattr(node, 'vulnerabilities'):
        return []
    return list(node.vulnerabilities) if node.vulnerabilities else []

def get_node_assets(node) -> list:
    if not hasattr(node, 'assets'):
        return []
    return list(node.assets) if node.assets else []

def validate_actor(actor) -> Dict[str, Any]:
    errors = []
    if not hasattr(actor, 'id') or not actor.id:
        errors.append("Actor missing required 'id' attribute")
    if not hasattr(actor, 'role'):
        errors.append("Actor missing required 'role' attribute")
    if not hasattr(actor, 'capacity'):
        errors.append("Actor missing 'capacity' attribute")
    return {'valid': len(errors) == 0, 'errors': errors}

def validate_node(node) -> Dict[str, Any]:
    errors = []
    if not hasattr(node, 'id') or not node.id:
        errors.append("Node missing required 'id' attribute")
    if not hasattr(node, 'access'):
        node.access = {}
    if not hasattr(node, 'properties'):
        node.properties = {}
    if not hasattr(node, 'software'):
        node.software = {}
    if not hasattr(node, 'vulnerabilities'):
        node.vulnerabilities = []
    if not hasattr(node, 'assets'):
        node.assets = []
    return {'valid': len(errors) == 0, 'errors': errors, 'warnings': []}

def get_link_access(link, actor_id: str, default: LinkAccessLevel=None) -> LinkAccessLevel:
    if default is None:
        default = LinkAccessLevel.NONE
    if not hasattr(link, 'access'):
        link.access = {}
    access = link.access.get(actor_id, default)
    if isinstance(access, str):
        access = LinkAccessLevel.from_string(access)
        link.access[actor_id] = access
    return access if isinstance(access, LinkAccessLevel) else default

def get_link_access_string(link, actor_id: str, default: str='NONE') -> str:
    access = get_link_access(link, actor_id)
    return access.to_string()

def set_link_access(link, actor_id: str, access_level: Union[LinkAccessLevel, str]):
    if not hasattr(link, 'access'):
        link.access = {}
    if isinstance(access_level, str):
        access_level = LinkAccessLevel.from_string(access_level)
    elif not isinstance(access_level, LinkAccessLevel):
        raise TypeError(f'Expected LinkAccessLevel or str, got {type(access_level)}')
    link.access[actor_id] = access_level