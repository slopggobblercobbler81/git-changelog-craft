"""Semantic versioning parsing and comparison module."""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional, Union


class BumpLevel(str, Enum):
    NONE = "none"
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"

    @property
    def priority(self) -> int:
        levels = {
            BumpLevel.NONE: 0,
            BumpLevel.PATCH: 1,
            BumpLevel.MINOR: 2,
            BumpLevel.MAJOR: 3,
        }
        return levels[self]

    def __ge__(self, other: "BumpLevel") -> bool:
        if not isinstance(other, BumpLevel):
            return NotImplemented
        return self.priority >= other.priority

    def __gt__(self, other: "BumpLevel") -> bool:
        if not isinstance(other, BumpLevel):
            return NotImplemented
        return self.priority > other.priority

    def __le__(self, other: "BumpLevel") -> bool:
        if not isinstance(other, BumpLevel):
            return NotImplemented
        return self.priority <= other.priority

    def __lt__(self, other: "BumpLevel") -> bool:
        if not isinstance(other, BumpLevel):
            return NotImplemented
        return self.priority < other.priority


SEMVER_REGEX = re.compile(
    r"^(?P<prefix>[vV])?"
    r"(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>[0-9a-zA-Z.-]+))?"
    r"(?:\+(?P<build>[0-9a-zA-Z.-]+))?$"
)


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None
    prefix: str = ""

    @classmethod
    def parse(cls, version_str: str) -> "SemVer":
        version_str = version_str.strip()
        match = SEMVER_REGEX.match(version_str)
        if not match:
            raise ValueError(f"Invalid semantic version string: '{version_str}'")

        gd = match.groupdict()
        return cls(
            major=int(gd["major"]),
            minor=int(gd["minor"]),
            patch=int(gd["patch"]),
            prerelease=gd.get("prerelease"),
            build=gd.get("build"),
            prefix=gd.get("prefix") or "",
        )

    def bump(self, level: Union[BumpLevel, str]) -> "SemVer":
        if isinstance(level, str):
            level = BumpLevel(level.lower())

        if level == BumpLevel.MAJOR:
            return SemVer(
                major=self.major + 1,
                minor=0,
                patch=0,
                prefix=self.prefix,
            )
        elif level == BumpLevel.MINOR:
            return SemVer(
                major=self.major,
                minor=self.minor + 1,
                patch=0,
                prefix=self.prefix,
            )
        elif level == BumpLevel.PATCH:
            return SemVer(
                major=self.major,
                minor=self.minor,
                patch=self.patch + 1,
                prefix=self.prefix,
            )
        elif level == BumpLevel.NONE:
            return self
        else:
            raise ValueError(f"Unsupported bump level: {level}")

    def format(self, include_prefix: bool = True) -> str:
        pfx = self.prefix if include_prefix else ""
        ver = f"{pfx}{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            ver += f"-{self.prerelease}"
        if self.build:
            ver += f"+{self.build}"
        return ver

    def __str__(self) -> str:
        return self.format(include_prefix=bool(self.prefix))

    def tuple_key(self):
        # Prerelease logic: None is greater than any prerelease string
        prerelease_key = (1, "") if self.prerelease is None else (0, self.prerelease)
        return (self.major, self.minor, self.patch, prerelease_key)

    def __lt__(self, other: "SemVer") -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self.tuple_key() < other.tuple_key()

    def __le__(self, other: "SemVer") -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self.tuple_key() <= other.tuple_key()

    def __gt__(self, other: "SemVer") -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self.tuple_key() > other.tuple_key()

    def __ge__(self, other: "SemVer") -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return self.tuple_key() >= other.tuple_key()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return False
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
            and self.prerelease == other.prerelease
        )
