"""Tests for CLI entry points and commands."""

import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from git_changelog_craft.cli import main
from git_changelog_craft.parser import CommitParser


def test_cli_version(capsys):
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    captured = capsys.readouterr()
    assert "git-changelog-craft" in captured.out


def test_cli_parse_plain(capsys):
    code = main(["parse", "feat(cli): add new fancy feature"])
    assert code == 0
    captured = capsys.readouterr()
    assert "Conventional : True" in captured.out
    assert "Type         : feat" in captured.out
    assert "Scope        : cli" in captured.out


def test_cli_parse_json(capsys):
    code = main(["parse", "fix: resolve crash", "--json"])
    assert code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["type"] == "fix"
    assert data["is_conventional"] is True


def test_cli_init():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / ".changelog-craft.json"
        code = main(["init", "-o", str(out_path)])
        assert code == 0
        assert out_path.exists()

        # Re-running on existing file fails cleanly
        code_retry = main(["init", "-o", str(out_path)])
        assert code_retry == 1


def test_cli_bump_dry_run(capsys):
    commits = [
        CommitParser.parse("feat: add search"),
        CommitParser.parse("fix: minor issue"),
    ]
    with patch("git_changelog_craft.cli.GitRepo.get_commits", return_value=commits), \
         patch("git_changelog_craft.cli.GitRepo.get_latest_tag", return_value="v1.0.0"):
        code = main(["bump", "--dry-run"])
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "v1.1.0"


def test_cli_generate_markdown(capsys):
    commits = [
        CommitParser.parse("feat(ui): add dark theme", sha="1234567890"),
    ]
    with patch("git_changelog_craft.cli.GitRepo.get_commits", return_value=commits), \
         patch("git_changelog_craft.cli.GitRepo.get_latest_tag", return_value="v1.0.0"):
        code = main(["generate", "--version-name", "v1.1.0"])
        assert code == 0
        captured = capsys.readouterr()
        assert "## [v1.1.0]" in captured.out
        assert "### ✨ Features" in captured.out
        assert "**ui**: add dark theme" in captured.out
