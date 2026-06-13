from enum import Enum
from functools import total_ordering
from typing import Any


@total_ordering
class NodeAccessLevel(Enum):
    NONE = 0
    VISIBLE = 1
    USER = 2
    ADMIN = 3

    def __lt__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    @classmethod
    def from_string(cls, access_str: str) -> "NodeAccessLevel":
        if access_str is None:
            return cls.NONE
        access_upper = access_str.upper()
        mapping = {
            "NONE": cls.NONE,
            "VISIBLE": cls.VISIBLE,
            "USER": cls.USER,
            "ADMIN": cls.ADMIN,
        }
        return mapping.get(access_upper, cls.NONE)

    def to_string(self) -> str:
        return self.name


@total_ordering
class LinkAccessLevel(Enum):
    NONE = 0
    VISIBLE = 1

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    @classmethod
    def from_string(cls, access_str: str):
        if access_str is None:
            return cls.NONE
        access_upper = access_str.upper()
        mapping = {"NONE": cls.NONE, "VISIBLE": cls.VISIBLE}
        return mapping.get(access_upper, cls.NONE)

    def to_string(self) -> str:
        return self.name


def validate_node_access(access) -> NodeAccessLevel:
    if isinstance(access, NodeAccessLevel):
        return access
    elif isinstance(access, str):
        return NodeAccessLevel.from_string(access)
    elif access is None:
        return NodeAccessLevel.NONE
    else:
        raise TypeError(f"Invalid node access type: {type(access)}")


def validate_link_access(access) -> LinkAccessLevel:
    if isinstance(access, LinkAccessLevel):
        return access
    elif isinstance(access, str):
        return LinkAccessLevel.from_string(access)
    elif access is None:
        return LinkAccessLevel.NONE
    else:
        raise TypeError(f"Invalid link access type: {type(access)}")
