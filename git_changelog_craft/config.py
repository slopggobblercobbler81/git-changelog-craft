"""Configuration loader and settings management."""

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_SECTIONS: Dict[str, str] = {
    "feat": "✨ Features",
    "fix": "🐛 Bug Fixes",
    "perf": "⚡ Performance Improvements",
    "refactor": "♻️ Code Refactoring",
    "docs": "📚 Documentation",
    "test": "🧪 Tests",
    "build": "📦 Build System",
    "ci": "👷 Continuous Integration",
    "chore": "🔧 Chores",
    "revert": "⏪ Reverts",
}

DEFAULT_TYPE_PRIORITY: Dict[str, int] = {
    "feat": 10,
    "fix": 20,
    "perf": 30,
    "refactor": 40,
    "docs": 50,
    "test": 60,
    "build": 70,
    "ci": 80,
    "chore": 90,
    "revert": 100,
}


@dataclass
class Config:
    repo_url: Optional[str] = None
    commit_url_template: str = "{repo_url}/commit/{sha}"
    issue_url_template: str = "{repo_url}/issues/{issue}"
    sections: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_SECTIONS))
    breaking_section_title: str = "💥 Breaking Changes"
    other_section_title: str = "📌 Other Changes"
    include_other_commits: bool = True
    include_authors: bool = True
    default_version: str = "0.1.0"
    unreleased_title: str = "Unreleased"

    @classmethod
    def load(cls, config_path: Optional[str] = None, search_dir: Optional[str] = None) -> "Config":
        target = None
        if config_path:
            target = Path(config_path)
        else:
            base = Path(search_dir or os.getcwd())
            candidates = [
                base / ".changelog-craft.json",
                base / ".changelogcraft.json",
            ]
            for c in candidates:
                if c.is_file():
                    target = c
                    break

        if target and target.is_file():
            try:
                with open(target, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return cls.from_dict(data)
            except Exception:
                return cls()
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        sections = data.get("sections") or DEFAULT_SECTIONS
        return cls(
            repo_url=data.get("repo_url"),
            commit_url_template=data.get("commit_url_template", "{repo_url}/commit/{sha}"),
            issue_url_template=data.get("issue_url_template", "{repo_url}/issues/{issue}"),
            sections=sections,
            breaking_section_title=data.get("breaking_section_title", "💥 Breaking Changes"),
            other_section_title=data.get("other_section_title", "📌 Other Changes"),
            include_other_commits=data.get("include_other_commits", True),
            include_authors=data.get("include_authors", True),
            default_version=data.get("default_version", "0.1.0"),
            unreleased_title=data.get("unreleased_title", "Unreleased"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def format_commit_url(self, sha: str) -> Optional[str]:
        if not self.repo_url or not sha:
            return None
        repo = self.repo_url.rstrip("/")
        return self.commit_url_template.format(repo_url=repo, sha=sha)

    def format_issue_url(self, issue: str) -> Optional[str]:
        if not self.repo_url or not issue:
            return None
        issue_num = issue.lstrip("#")
        repo = self.repo_url.rstrip("/")
        return self.issue_url_template.format(repo_url=repo, issue=issue_num)
