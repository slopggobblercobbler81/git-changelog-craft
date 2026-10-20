"""git-changelog-craft: Fast CLI for changelogs, release notes, and version bumps."""

from git_changelog_craft.config import Config
from git_changelog_craft.generator import ChangelogGenerator
from git_changelog_craft.git import GitRepo, GitTag
from git_changelog_craft.parser import CommitParser, ConventionalCommit
from git_changelog_craft.semver import BumpLevel, SemVer

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "BumpLevel",
    "ChangelogGenerator",
    "CommitParser",
    "Config",
    "ConventionalCommit",
    "GitRepo",
    "GitTag",
    "SemVer",
]
