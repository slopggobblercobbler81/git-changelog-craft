"""Changelog and release notes markdown / JSON generation."""

from collections import defaultdict
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from git_changelog_craft.config import Config, DEFAULT_TYPE_PRIORITY
from git_changelog_craft.parser import ConventionalCommit
from git_changelog_craft.semver import BumpLevel, SemVer


class ChangelogGenerator:
    """Formats conventional commits into changelog sections and release notes."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def determine_bump_level(self, commits: List[ConventionalCommit]) -> BumpLevel:
        if not commits:
            return BumpLevel.NONE

        has_breaking = any(c.is_breaking for c in commits)
        if has_breaking:
            return BumpLevel.MAJOR

        has_feature = any(c.type == "feat" for c in commits)
        if has_feature:
            return BumpLevel.MINOR

        has_patch = any(
            c.type in ("fix", "perf", "refactor", "build", "revert")
            for c in commits
        )
        if has_patch:
            return BumpLevel.PATCH

        # If only docs/chore/tests/ci or non-conventional commits exist
        return BumpLevel.PATCH if commits else BumpLevel.NONE

    def format_commit_entry(self, commit: ConventionalCommit) -> str:
        parts: List[str] = []

        if commit.scope:
            parts.append(f"**{commit.scope}**: {commit.description}")
        else:
            parts.append(commit.description)

        extras: List[str] = []

        # Commit hash link
        if commit.short_sha:
            commit_url = self.config.format_commit_url(commit.sha)
            if commit_url:
                extras.append(f"[{commit.short_sha}]({commit_url})")
            else:
                extras.append(f"`{commit.short_sha}`")

        # Issue/PR references
        for ref in commit.references:
            issue_url = self.config.format_issue_url(ref)
            if issue_url:
                extras.append(f"[{ref}]({issue_url})")
            else:
                extras.append(ref)

        if extras:
            parts.append(f"({', '.join(extras)})")

        if self.config.include_authors and commit.author_name:
            parts.append(f"by {commit.author_name}")

        return "- " + " ".join(parts)

    def group_commits(
        self, commits: List[ConventionalCommit]
    ) -> Dict[str, List[ConventionalCommit]]:
        grouped: Dict[str, List[ConventionalCommit]] = defaultdict(list)

        for commit in commits:
            if commit.is_breaking:
                grouped["breaking"].append(commit)
            elif commit.type and commit.type in self.config.sections:
                grouped[commit.type].append(commit)
            else:
                if self.config.include_other_commits:
                    grouped["other"].append(commit)

        return grouped

    def generate_section(
        self,
        version: str,
        commits: List[ConventionalCommit],
        release_date: Optional[str] = None,
        is_release_notes: bool = False,
    ) -> str:
        """Generate markdown for a single release section."""
        date_str = release_date or datetime.now().strftime("%Y-%m-%d")
        lines: List[str] = []

        if is_release_notes:
            lines.append(f"## Release {version}")
        else:
            lines.append(f"## [{version}] - {date_str}")

        if not commits:
            lines.append("\n*No significant changes.*")
            return "\n".join(lines)

        grouped = self.group_commits(commits)

        # 1. Breaking changes
        if grouped.get("breaking"):
            lines.append(f"\n### {self.config.breaking_section_title}")
            for commit in grouped["breaking"]:
                # Use breaking description if available
                desc = commit.breaking_description or commit.description
                scope_prefix = f"**{commit.scope}**: " if commit.scope else ""
                hash_part = f" (`{commit.short_sha}`)" if commit.short_sha else ""
                lines.append(f"- {scope_prefix}{desc}{hash_part}")

        # 2. Configured commit types ordered by priority
        sorted_types = sorted(
            [t for t in grouped.keys() if t not in ("breaking", "other")],
            key=lambda t: DEFAULT_TYPE_PRIORITY.get(t, 999),
        )

        for c_type in sorted_types:
            section_title = self.config.sections.get(c_type, c_type.capitalize())
            lines.append(f"\n### {section_title}")
            for commit in grouped[c_type]:
                lines.append(self.format_commit_entry(commit))

        # 3. Other commits
        if grouped.get("other"):
            lines.append(f"\n### {self.config.other_section_title}")
            for commit in grouped["other"]:
                lines.append(self.format_commit_entry(commit))

        return "\n".join(lines)

    def generate_json(
        self,
        version: str,
        commits: List[ConventionalCommit],
        release_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        date_str = release_date or datetime.now().strftime("%Y-%m-%d")
        grouped = self.group_commits(commits)

        categories: Dict[str, Any] = {}
        for cat, cat_commits in grouped.items():
            categories[cat] = [c.to_dict() for c in cat_commits]

        return {
            "version": version,
            "date": date_str,
            "total_commits": len(commits),
            "breaking_count": len(grouped.get("breaking", [])),
            "features_count": len(grouped.get("feat", [])),
            "fixes_count": len(grouped.get("fix", [])),
            "suggested_bump": self.determine_bump_level(commits).value,
            "categories": categories,
        }

    def update_changelog_file(
        self,
        filepath: str,
        version: str,
        commits: List[ConventionalCommit],
        release_date: Optional[str] = None,
    ) -> str:
        """Insert or prepend the release section into an existing CHANGELOG.md file."""
        new_section = self.generate_section(
            version=version,
            commits=commits,
            release_date=release_date,
            is_release_notes=False,
        )

        path = Path(filepath)
        header = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"

        if not path.exists():
            content = header + new_section + "\n"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return content

        existing = path.read_text(encoding="utf-8")

        # Check if this version heading already exists
        version_header = f"## [{version}]"
        if version_header in existing:
            # We don't overwrite if already there
            return existing

        # Locate where to insert (after initial top-level header)
        if existing.startswith("# Changelog"):
            lines = existing.splitlines(keepends=True)
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith("## "):
                    insert_idx = i
                    break
            if insert_idx > 0:
                updated = (
                    "".join(lines[:insert_idx])
                    + new_section
                    + "\n\n"
                    + "".join(lines[insert_idx:])
                )
            else:
                updated = existing.strip() + "\n\n" + new_section + "\n"
        else:
            updated = header + new_section + "\n\n" + existing

        path.write_text(updated, encoding="utf-8")
        return updated
