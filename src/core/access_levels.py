from enum import Enum, auto


class NodeAccessLevel(Enum):
    """
    Node access levels as specified in TIM paper Section 4.2.
    
    Hierarchy: NONE < VISIBLE < USER < ADMIN
    
    - NONE: Actor is not aware of the node
    - VISIBLE: Actor knows basic information (e.g., IP address), can send ping requests
    - USER: Actor has user-level access to the node
    - ADMIN: Actor has administrator-level access to the node
    """
    NONE = 0
    VISIBLE = 1
    USER = 2
    ADMIN = 3
    
    def __lt__(self, other):
        """Support comparison operators for access level hierarchy"""
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    
    @classmethod
    def from_string(cls, access_str: str):
        """Convert string representation to enum (backward compatibility)"""
        if access_str is None:
            return cls.NONE
        
        # Handle both uppercase and lowercase
        access_upper = access_str.upper()
        
        mapping = {
            'NONE': cls.NONE,
            'VISIBLE': cls.VISIBLE,
            'USER': cls.USER,
            'ADMIN': cls.ADMIN
        }
        
        return mapping.get(access_upper, cls.NONE)
    
    def to_string(self) -> str:
        """Convert enum to string representation"""
        return self.name


class LinkAccessLevel(Enum):
    """
    Link access levels as specified in TIM paper Section 4.2.
    
    Hierarchy: NONE < VISIBLE
    
    - NONE: Actor is unaware of the link
    - VISIBLE: Actor is aware of the link
    """
    NONE = 0
    VISIBLE = 1
    
    def __lt__(self, other):
        """Support comparison operators for access level hierarchy"""
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    
    @classmethod
    def from_string(cls, access_str: str):
        """Convert string representation to enum (backward compatibility)"""
        if access_str is None:
            return cls.NONE
        
        access_upper = access_str.upper()
        
        mapping = {
            'NONE': cls.NONE,
            'VISIBLE': cls.VISIBLE
        }
        
        return mapping.get(access_upper, cls.NONE)
    
    def to_string(self) -> str:
        """Convert enum to string representation"""
        return self.name


# Backward compatibility: String constants
NODE_ACCESS_NONE = "NONE"
NODE_ACCESS_VISIBLE = "VISIBLE"
NODE_ACCESS_USER = "USER"
NODE_ACCESS_ADMIN = "ADMIN"

LINK_ACCESS_NONE = "NONE"
LINK_ACCESS_VISIBLE = "VISIBLE"


def validate_node_access(access) -> NodeAccessLevel:
    """
    Validate and convert access to NodeAccessLevel enum.
    
    Args:
        access: Can be NodeAccessLevel enum, string, or None
        
    Returns:
        NodeAccessLevel enum
    """
    if isinstance(access, NodeAccessLevel):
        return access
    elif isinstance(access, str):
        return NodeAccessLevel.from_string(access)
    elif access is None:
        return NodeAccessLevel.NONE
    else:
        raise TypeError(f"Invalid node access type: {type(access)}")


def validate_link_access(access) -> LinkAccessLevel:
    """
    Validate and convert access to LinkAccessLevel enum.
    
    Args:
        access: Can be LinkAccessLevel enum, string, or None
        
    Returns:
        LinkAccessLevel enum
    """
    if isinstance(access, LinkAccessLevel):
        return access
    elif isinstance(access, str):
        return LinkAccessLevel.from_string(access)
    elif access is None:
        return LinkAccessLevel.NONE
    else:
        raise TypeError(f"Invalid link access type: {type(access)}")


# For backward compatibility with existing code that uses string comparison
def get_access_level_value(access) -> int:
    """
    Get numeric value for access level (for comparisons).
    Supports both enum and string inputs.
    """
    if isinstance(access, (NodeAccessLevel, LinkAccessLevel)):
        return access.value
    elif isinstance(access, str):
        # Try node access first
        try:
            return NodeAccessLevel.from_string(access).value
        except:
            # Fall back to link access
            return LinkAccessLevel.from_string(access).value
    return 0


def compare_access_levels(access1, access2) -> int:
    """
    Compare two access levels.
    
    Returns:
        -1 if access1 < access2
        0 if access1 == access2
        1 if access1 > access2
    """
    val1 = get_access_level_value(access1)
    val2 = get_access_level_value(access2)
    
    if val1 < val2:
        return -1
    elif val1 > val2:
        return 1
    else:
        return 0
