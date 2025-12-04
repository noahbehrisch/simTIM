"""
Utility functions for standardized access to node and actor properties.

This module provides type-safe interfaces for accessing node/actor data,
using enums as the primary interface for full type safety.
"""
from typing import Optional, Any, Dict, Union
from src.core.access_levels import NodeAccessLevel, LinkAccessLevel, validate_node_access, validate_link_access


def get_node_access(node, actor_id: str, default: NodeAccessLevel = None) -> NodeAccessLevel:
    """
    Get actor's access level to a node (returns enum for type safety).
    
    Args:
        node: Node object
        actor_id: Actor's ID
        default: Default access level if not set (default: NodeAccessLevel.NONE)
        
    Returns:
        NodeAccessLevel enum (NONE, VISIBLE, USER, or ADMIN)
        
    Example:
        access = get_node_access(node, attacker.id)
        if access >= NodeAccessLevel.ADMIN:
            # Can perform admin actions
            
    Type Safety:
        - Returns enum, preventing string typos
        - Supports comparison operators (>=, <, etc.)
        - IDE auto-completion support
    """
    if default is None:
        default = NodeAccessLevel.NONE
    
    if not hasattr(node, 'access'):
        node.access = {}
    
    access = node.access.get(actor_id, default)
    
    # Handle legacy string values - convert to enum
    if isinstance(access, str):
        access = NodeAccessLevel.from_string(access)
        node.access[actor_id] = access  # Upgrade storage to enum
    
    return access if isinstance(access, NodeAccessLevel) else default


def get_node_access_string(node, actor_id: str, default: str = "NONE") -> str:
    """
    Get actor's access level as a string (for JSON serialization).
    
    Args:
        node: Node object
        actor_id: Actor's ID
        default: Default access level string
        
    Returns:
        Access level as string ("NONE", "VISIBLE", "USER", or "ADMIN")
        
    Note:
        Prefer get_node_access() which returns type-safe enum.
        Use this only for JSON serialization or legacy code.
    """
    access = get_node_access(node, actor_id)
    return access.to_string()


def set_node_access(node, actor_id: str, access_level: Union[NodeAccessLevel, str]):
    """
    Set actor's access level to a node.
    
    Args:
        node: Node object
        actor_id: Actor's ID
        access_level: NodeAccessLevel enum or string (string will be converted to enum)
        
    Example:
        set_node_access(node, attacker.id, NodeAccessLevel.ADMIN)
        set_node_access(node, defender.id, "ADMIN")  # Also works, converted to enum
        
    Type Safety:
        - Stores as enum internally for type safety
        - Accepts strings for convenience, converts to enum
        - Validates access level is valid
    """
    if not hasattr(node, 'access'):
        node.access = {}
    
    # Convert to enum if string provided
    if isinstance(access_level, str):
        access_level = NodeAccessLevel.from_string(access_level)
    elif not isinstance(access_level, NodeAccessLevel):
        raise TypeError(f"Expected NodeAccessLevel or str, got {type(access_level)}")
    
    # Store as enum for type safety
    node.access[actor_id] = access_level


def get_node_property(node, property_name: str, default: Any = None) -> Any:
    """
    Get a node property with consistent access pattern.
    
    Args:
        node: Node object
        property_name: Property name
        default: Default value if property doesn't exist
        
    Returns:
        Property value or default
        
    Example:
        sensitivity = get_node_property(node, "data_sensitivity", "low")
    """
    if not hasattr(node, 'properties'):
        return default
    return node.properties.get(property_name, default)


def set_node_property(node, property_name: str, value: Any):
    """
    Set a node property.
    
    Args:
        node: Node object
        property_name: Property name
        value: Property value
        
    Example:
        set_node_property(node, "compromised", True)
    """
    if not hasattr(node, 'properties'):
        node.properties = {}
    node.properties[property_name] = value


def get_node_software(node, software_key: str, default: Any = None) -> Any:
    """
    Get node software information.
    
    Args:
        node: Node object
        software_key: Software property key
        default: Default value if not found
        
    Returns:
        Software property value or default
        
    Example:
        dbms = get_node_software(node, "DBMS name")
    """
    if not hasattr(node, 'software'):
        return default
    return node.software.get(software_key, default)


def has_vulnerability(node, vuln_id: str) -> bool:
    """
    Check if node has a specific vulnerability.
    
    Args:
        node: Node object
        vuln_id: Vulnerability ID (e.g., CVE number)
        
    Returns:
        True if node has the vulnerability
        
    Example:
        if has_vulnerability(node, "CVE-2021-27850"):
            # Node is vulnerable
    """
    if not hasattr(node, 'vulnerabilities'):
        return False
    return vuln_id in node.vulnerabilities


def get_node_vulnerabilities(node) -> list:
    """
    Get all vulnerabilities for a node.
    
    Args:
        node: Node object
        
    Returns:
        List of vulnerability IDs
        
    Example:
        vulns = get_node_vulnerabilities(node)
        if len(vulns) > 0:
            # Node has vulnerabilities
    """
    if not hasattr(node, 'vulnerabilities'):
        return []
    return list(node.vulnerabilities) if node.vulnerabilities else []


def get_node_assets(node) -> list:
    """
    Get all assets stored on a node.
    
    Args:
        node: Node object
        
    Returns:
        List of assets
        
    Example:
        assets = get_node_assets(node)
        if "customer_data" in assets:
            # Node contains customer data
    """
    if not hasattr(node, 'assets'):
        return []
    return list(node.assets) if node.assets else []


def validate_actor(actor) -> Dict[str, Any]:
    """
    Validate that an actor has required attributes.
    
    Args:
        actor: Actor object to validate
        
    Returns:
        Dict with validation results
        
    Raises:
        ValueError: If actor is missing required attributes
        
    Example:
        result = validate_actor(attacker)
        if not result['valid']:
            print(result['errors'])
    """
    errors = []
    
    if not hasattr(actor, 'id') or not actor.id:
        errors.append("Actor missing required 'id' attribute")
    
    if not hasattr(actor, 'role'):
        errors.append("Actor missing required 'role' attribute")
    
    if not hasattr(actor, 'capacity'):
        errors.append("Actor missing 'capacity' attribute")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_node(node) -> Dict[str, Any]:
    """
    Validate that a node has required attributes.
    
    Args:
        node: Node object to validate
        
    Returns:
        Dict with validation results
        
    Example:
        result = validate_node(node)
        if not result['valid']:
            raise ValueError(f"Invalid node: {result['errors']}")
    """
    errors = []
    
    if not hasattr(node, 'id') or not node.id:
        errors.append("Node missing required 'id' attribute")
    
    # Ensure required dictionaries exist
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
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': []
    }


# ============================================================================
# Link Access Utilities
# ============================================================================

def get_link_access(link, actor_id: str, default: LinkAccessLevel = None) -> LinkAccessLevel:
    """
    Get actor's access level to a link (returns enum for type safety).
    
    Args:
        link: Link object
        actor_id: Actor's ID
        default: Default access level if not set (default: LinkAccessLevel.NONE)
        
    Returns:
        LinkAccessLevel enum (NONE or VISIBLE)
        
    Example:
        access = get_link_access(link, attacker.id)
        if access >= LinkAccessLevel.VISIBLE:
            # Can see the link
            
    Type Safety:
        - Returns enum, preventing string typos
        - Supports comparison operators
        - IDE auto-completion support
    """
    if default is None:
        default = LinkAccessLevel.NONE
    
    if not hasattr(link, 'access'):
        link.access = {}
    
    access = link.access.get(actor_id, default)
    
    # Handle legacy string values - convert to enum
    if isinstance(access, str):
        access = LinkAccessLevel.from_string(access)
        link.access[actor_id] = access  # Upgrade storage to enum
    
    return access if isinstance(access, LinkAccessLevel) else default


def get_link_access_string(link, actor_id: str, default: str = "NONE") -> str:
    """
    Get actor's access level to a link as a string (for JSON serialization).
    
    Args:
        link: Link object
        actor_id: Actor's ID
        default: Default access level string
        
    Returns:
        Access level as string ("NONE" or "VISIBLE")
        
    Note:
        Prefer get_link_access() which returns type-safe enum.
        Use this only for JSON serialization or legacy code.
    """
    access = get_link_access(link, actor_id)
    return access.to_string()


def set_link_access(link, actor_id: str, access_level: Union[LinkAccessLevel, str]):
    """
    Set actor's access level to a link.
    
    Args:
        link: Link object
        actor_id: Actor's ID
        access_level: LinkAccessLevel enum or string (string will be converted to enum)
        
    Example:
        set_link_access(link, attacker.id, LinkAccessLevel.VISIBLE)
        set_link_access(link, defender.id, "VISIBLE")  # Also works
        
    Type Safety:
        - Stores as enum internally for type safety
        - Accepts strings for convenience, converts to enum
        - Validates access level is valid
    """
    if not hasattr(link, 'access'):
        link.access = {}
    
    # Convert to enum if string provided
    if isinstance(access_level, str):
        access_level = LinkAccessLevel.from_string(access_level)
    elif not isinstance(access_level, LinkAccessLevel):
        raise TypeError(f"Expected LinkAccessLevel or str, got {type(access_level)}")
    
    # Store as enum for type safety
    link.access[actor_id] = access_level

