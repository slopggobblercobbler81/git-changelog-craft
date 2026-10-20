"""Tests for git repository interactions."""

from unittest.mock import patch
from git_changelog_craft.git import GitRepo, RECORD_SEPARATOR, UNIT_SEPARATOR
from git_changelog_craft.semver import SemVer


def test_git_repo_non_existent():
    repo = GitRepo("/non/existent/path/123456")
    assert repo.is_git_repository() is False
    assert repo.get_tags() == []
    assert repo.get_latest_tag() is None
    assert repo.get_commits() == []


def test_git_get_remote_url_ssh_and_https():
    repo = GitRepo(".")
    with patch.object(repo, "_run_git", return_value="git@github.com:foo/bar.git"):
        url = repo.get_remote_url()
        assert url == "https://github.com/foo/bar"

    with patch.object(repo, "_run_git", return_value="https://github.com/foo/bar.git"):
        url = repo.get_remote_url()
        assert url == "https://github.com/foo/bar"


def test_git_get_tags_sorting():
    repo = GitRepo(".")
    mock_tags = "v1.0.0\nv1.2.0\nv1.1.0\nv2.0.0-beta.1\ncustom-tag"
    with patch.object(repo, "_run_git", return_value=mock_tags):
        tags = repo.get_tags()
        tag_names = [t.name for t in tags]
        # SemVer tags come first in descending order
        assert tag_names[0] == "v2.0.0-beta.1" or tag_names[0] == "v1.2.0"
        assert "custom-tag" in tag_names
        assert repo.get_latest_tag() == tag_names[0]


def test_git_get_commits_parsing():
    repo = GitRepo(".")
    sample_log = (
        f"1111111111{UNIT_SEPARATOR}1111111{UNIT_SEPARATOR}Author One{UNIT_SEPARATOR}one@test.com{UNIT_SEPARATOR}2026-10-20{UNIT_SEPARATOR}feat(core): initial core{RECORD_SEPARATOR}"
        f"2222222222{UNIT_SEPARATOR}2222222{UNIT_SEPARATOR}Author Two{UNIT_SEPARATOR}two@test.com{UNIT_SEPARATOR}2026-10-20{UNIT_SEPARATOR}fix(parser): bug fix{RECORD_SEPARATOR}"
    )

    with patch.object(repo, "is_git_repository", return_value=True), \
         patch.object(repo, "_run_git") as mock_run:
        # First call is head check, second call is git log
        mock_run.side_effect = ["true", sample_log]
        commits = repo.get_commits()

        assert len(commits) == 2
        assert commits[0].type == "feat"
        assert commits[0].scope == "core"
        assert commits[0].author_name == "Author One"
        assert commits[1].type == "fix"
        assert commits[1].scope == "parser"
