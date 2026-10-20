"""Tests for conventional commits parser."""

from git_changelog_craft.parser import CommitParser


def test_parse_simple_feat():
    msg = "feat: add user login endpoint"
    commit = CommitParser.parse(msg, sha="a1b2c3d4e5f6")
    assert commit.is_conventional is True
    assert commit.type == "feat"
    assert commit.scope is None
    assert commit.description == "add user login endpoint"
    assert commit.is_breaking is False
    assert commit.short_sha == "a1b2c3d"


def test_parse_scope_and_breaking_exclamation():
    msg = "feat(auth)!: replace sessions with JWT tokens"
    commit = CommitParser.parse(msg)
    assert commit.is_conventional is True
    assert commit.type == "feat"
    assert commit.scope == "auth"
    assert commit.description == "replace sessions with JWT tokens"
    assert commit.is_breaking is True
    assert commit.breaking_description == "replace sessions with JWT tokens"


def test_parse_breaking_change_footer():
    msg = (
        "fix(api): change payload parameter name\n\n"
        "BREAKING CHANGE: The `user_name` field has been renamed to `username`."
    )
    commit = CommitParser.parse(msg)
    assert commit.is_conventional is True
    assert commit.type == "fix"
    assert commit.scope == "api"
    assert commit.is_breaking is True
    assert commit.breaking_description == "The `user_name` field has been renamed to `username`."


def test_parse_issue_references():
    msg = "fix: resolve memory leak on shutdown (fixes #104, #105)"
    commit = CommitParser.parse(msg)
    assert "#104" in commit.references
    assert "#105" in commit.references


def test_parse_footers():
    msg = (
        "refactor(core): streamline config loading\n\n"
        "Detailed explanation here.\n\n"
        "Signed-off-by: Jane Doe <jane@example.com>\n"
        "Co-authored-by: Bob Smith <bob@example.com>"
    )
    commit = CommitParser.parse(msg)
    assert commit.is_conventional is True
    assert commit.footers.get("Signed-off-by") == "Jane Doe <jane@example.com>"
    assert commit.footers.get("Co-authored-by") == "Bob Smith <bob@example.com>"
    assert "Detailed explanation here." in (commit.body or "")


def test_parse_unconventional_commit():
    msg = "just updated the readme instructions"
    commit = CommitParser.parse(msg)
    assert commit.is_conventional is False
    assert commit.type is None
    assert commit.description == "just updated the readme instructions"
    assert commit.is_breaking is False


def test_parse_empty_message():
    commit = CommitParser.parse("")
    assert commit.is_conventional is False
    assert commit.description == ""
