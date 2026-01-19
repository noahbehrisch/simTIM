import re
from typing import Union


class Version:

    def __init__(self, version_string: str):
        self.version_string = version_string.strip()
        self._parse_version()

    def _parse_version(self):
        version = self.version_string.lower()
        self.is_prerelease = False
        self.prerelease_type = None
        self.prerelease_number = 0
        prerelease_pattern = "(a|alpha|b|beta|rc|dev)(\\d*)"
        prerelease_match = re.search(prerelease_pattern, version)
        if prerelease_match:
            self.is_prerelease = True
            self.prerelease_type = prerelease_match.group(1)
            self.prerelease_number = (
                int(prerelease_match.group(2)) if prerelease_match.group(2) else 0
            )
            version = re.sub(prerelease_pattern, "", version)
        clean_version = re.sub("[^0-9.]", "", version)
        parts = clean_version.split(".")
        while len(parts) < 3:
            parts.append("0")
        try:
            self.major = int(parts[0]) if parts[0] else 0
            self.minor = int(parts[1]) if parts[1] else 0
            self.patch = int(parts[2]) if parts[2] else 0
            self.additional = [int(p) for p in parts[3:] if p.isdigit()]
        except ValueError:
            self.major = self.minor = self.patch = 0
            self.additional = []

    def _get_prerelease_priority(self) -> int:
        if not self.is_prerelease:
            return 1000
        priorities = {"dev": 0, "a": 10, "alpha": 10, "b": 20, "beta": 20, "rc": 30}
        return priorities.get(self.prerelease_type, 5)

    def _compare_to(self, other: "Version") -> int:
        if not isinstance(other, Version):
            other = Version(str(other))
        for self_part, other_part in zip(
            [self.major, self.minor, self.patch] + self.additional,
            [other.major, other.minor, other.patch] + other.additional,
        ):
            if self_part < other_part:
                return -1
            elif self_part > other_part:
                return 1
        self_prerelease_priority = self._get_prerelease_priority()
        other_prerelease_priority = other._get_prerelease_priority()
        if self_prerelease_priority < other_prerelease_priority:
            return -1
        elif self_prerelease_priority > other_prerelease_priority:
            return 1
        if self.is_prerelease and other.is_prerelease:
            if self.prerelease_number < other.prerelease_number:
                return -1
            elif self.prerelease_number > other.prerelease_number:
                return 1
        return 0

    def __lt__(self, other) -> bool:
        return self._compare_to(other) < 0

    def __le__(self, other) -> bool:
        return self._compare_to(other) <= 0

    def __gt__(self, other) -> bool:
        return self._compare_to(other) > 0

    def __ge__(self, other) -> bool:
        return self._compare_to(other) >= 0

    def __eq__(self, other) -> bool:
        return self._compare_to(other) == 0

    def __ne__(self, other) -> bool:
        return self._compare_to(other) != 0

    def __str__(self) -> str:
        return self.version_string

    def __repr__(self) -> str:
        return f"Version('{self.version_string}')"
