"""Tests for changelog generator."""

from pathlib import Path
import tempfile
from git_changelog_craft.config import Config
from git_changelog_craft.generator import ChangelogGenerator
from git_changelog_craft.parser import CommitParser
from git_changelog_craft.semver import BumpLevel


def test_determine_bump_level():
    gen = ChangelogGenerator()

    # Major if breaking
    c1 = CommitParser.parse("feat!: big breaking change")
    assert gen.determine_bump_level([c1]) == BumpLevel.MAJOR

    # Minor if feature
    c2 = CommitParser.parse("feat: add search filter")
    c3 = CommitParser.parse("fix: fix typo")
    assert gen.determine_bump_level([c2, c3]) == BumpLevel.MINOR

    # Patch if only fix
    assert gen.determine_bump_level([c3]) == BumpLevel.PATCH

    # None if empty
    assert gen.determine_bump_level([]) == BumpLevel.NONE


def test_generate_section_markdown():
    config = Config(
        repo_url="https://github.com/slopggobblercobbler81/git-changelog-craft",
        include_authors=True,
    )
    gen = ChangelogGenerator(config)

    c1 = CommitParser.parse(
        "feat(cli): add bump command (#12)",
        sha="11111112222222",
        author_name="Alice",
    )
    c2 = CommitParser.parse(
        "fix(core): handle empty tags",
        sha="33333334444444",
        author_name="Bob",
    )
    c3 = CommitParser.parse(
        "feat(api)!: remove v1 endpoints",
        sha="55555556666666",
        author_name="Alice",
    )

    md = gen.generate_section("v1.0.0", [c1, c2, c3], release_date="2026-10-20")

    assert "## [v1.0.0] - 2026-10-20" in md
    assert "### 💥 Breaking Changes" in md
    assert "**api**: remove v1 endpoints" in md
    assert "### ✨ Features" in md
    assert "**cli**: add bump command (#12)" in md
    assert "https://github.com/slopggobblercobbler81/git-changelog-craft/commit/11111112222222" in md
    assert "https://github.com/slopggobblercobbler81/git-changelog-craft/issues/12" in md
    assert "### 🐛 Bug Fixes" in md
    assert "**core**: handle empty tags" in md


def test_generate_release_notes():
    gen = ChangelogGenerator()
    c = CommitParser.parse("feat: shiny new feature")
    notes = gen.generate_section("v2.0.0", [c], is_release_notes=True)
    assert "## Release v2.0.0" in notes
    assert "### ✨ Features" in notes


def test_generate_json():
    gen = ChangelogGenerator()
    c1 = CommitParser.parse("feat: one")
    c2 = CommitParser.parse("fix: two")
    data = gen.generate_json("1.2.0", [c1, c2], release_date="2026-10-20")

    assert data["version"] == "1.2.0"
    assert data["total_commits"] == 2
    assert data["features_count"] == 1
    assert data["fixes_count"] == 1
    assert data["suggested_bump"] == "minor"
    assert "feat" in data["categories"]


def test_update_changelog_file_new_and_existing():
    gen = ChangelogGenerator()
    c = CommitParser.parse("feat: initial release")

    with tempfile.TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"

        # 1. Create fresh
        gen.update_changelog_file(str(changelog_path), "0.1.0", [c], release_date="2026-10-20")
        content = changelog_path.read_text(encoding="utf-8")
        assert "# Changelog" in content
        assert "## [0.1.0] - 2026-10-20" in content

        # 2. Prepend a newer version
        c2 = CommitParser.parse("fix: patch bug")
        gen.update_changelog_file(str(changelog_path), "0.1.1", [c2], release_date="2026-10-21")
        updated = changelog_path.read_text(encoding="utf-8")
        assert updated.index("## [0.1.1]") < updated.index("## [0.1.0]")
