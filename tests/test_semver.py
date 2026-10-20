"""Tests for semantic versioning module."""

import pytest
from git_changelog_craft.semver import BumpLevel, SemVer


def test_semver_parse_valid():
    v1 = SemVer.parse("1.2.3")
    assert v1.major == 1
    assert v1.minor == 2
    assert v1.patch == 3
    assert v1.prefix == ""
    assert str(v1) == "1.2.3"

    v2 = SemVer.parse("v2.0.1")
    assert v2.major == 2
    assert v2.minor == 0
    assert v2.patch == 1
    assert v2.prefix == "v"
    assert str(v2) == "v2.0.1"


def test_semver_parse_with_prerelease():
    v = SemVer.parse("v1.0.0-alpha.1+build.123")
    assert v.major == 1
    assert v.minor == 0
    assert v.patch == 0
    assert v.prerelease == "alpha.1"
    assert v.build == "build.123"
    assert str(v) == "v1.0.0-alpha.1+build.123"


def test_semver_parse_invalid():
    with pytest.raises(ValueError):
        SemVer.parse("invalid-version")
    with pytest.raises(ValueError):
        SemVer.parse("1.2")


def test_semver_bump():
    v = SemVer.parse("v1.2.3")

    bumped_patch = v.bump(BumpLevel.PATCH)
    assert str(bumped_patch) == "v1.2.4"

    bumped_minor = v.bump(BumpLevel.MINOR)
    assert str(bumped_minor) == "v1.3.0"

    bumped_major = v.bump(BumpLevel.MAJOR)
    assert str(bumped_major) == "v2.0.0"

    bumped_none = v.bump(BumpLevel.NONE)
    assert str(bumped_none) == "v1.2.3"


def test_semver_comparisons():
    v1 = SemVer.parse("1.0.0")
    v2 = SemVer.parse("1.1.0")
    v3 = SemVer.parse("2.0.0")
    v_alpha = SemVer.parse("1.0.0-alpha")

    assert v1 < v2
    assert v2 < v3
    assert v1 <= v1
    assert v2 > v1
    assert v3 >= v2
    assert v1 == SemVer.parse("1.0.0")
    assert v1 != v2
    assert v_alpha < v1


def test_bumplevel_comparisons():
    assert BumpLevel.MAJOR > BumpLevel.MINOR
    assert BumpLevel.MINOR > BumpLevel.PATCH
    assert BumpLevel.PATCH > BumpLevel.NONE
    assert BumpLevel.MAJOR >= BumpLevel.MAJOR
