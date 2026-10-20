"""Tests for configuration loader."""

import json
from pathlib import Path
import tempfile
from git_changelog_craft.config import Config


def test_config_defaults():
    cfg = Config()
    assert cfg.default_version == "0.1.0"
    assert "feat" in cfg.sections
    assert cfg.include_authors is True


def test_config_url_formatting():
    cfg = Config(repo_url="https://github.com/myorg/myproject")
    commit_url = cfg.format_commit_url("abcdef123456")
    assert commit_url == "https://github.com/myorg/myproject/commit/abcdef123456"

    issue_url = cfg.format_issue_url("#99")
    assert issue_url == "https://github.com/myorg/myproject/issues/99"


def test_config_load_from_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".changelog-craft.json"
        data = {
            "repo_url": "https://github.com/test/repo",
            "breaking_section_title": "Custom Breaking",
            "default_version": "1.0.0",
        }
        config_file.write_text(json.dumps(data), encoding="utf-8")

        loaded = Config.load(config_path=str(config_file))
        assert loaded.repo_url == "https://github.com/test/repo"
        assert loaded.breaking_section_title == "Custom Breaking"
        assert loaded.default_version == "1.0.0"
