# git-changelog-craft 🛠️✨

[![CI](https://github.com/slopggobblercobbler81/git-changelog-craft/actions/workflows/ci.yml/badge.svg)](https://github.com/slopggobblercobbler81/git-changelog-craft/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)

**git-changelog-craft** is a lightning-fast CLI tool that analyzes conventional git commits, tags, and PR references to generate changelogs, release notes, automated semantic version bumps, and commit validation.

---

## 🚀 Features

- **Conventional Commit Engine**: Parses types (`feat`, `fix`, `perf`, `refactor`, `docs`, etc.), scopes, breaking indicators (`!`), and footer notes (`BREAKING CHANGE: ...`).
- **Semantic Version Bumps**: Calculates the next version (`major`, `minor`, `patch`) automatically based on commit history.
- **Commit History Validator**: Enforces Conventional Commits compliance in pull requests and CI pipelines (`validate`).
- **Multiple Output Formats**:
  - `markdown`: Keep a Changelog compliant markdown.
  - `release-notes`: Clean notes ready for GitHub Releases or Slack announcements.
  - `json`: Machine-readable output for release pipelines and automated workflows.
- **Smart Changelog Updates**: Safely prepends or inserts new release notes into existing `CHANGELOG.md` files without overwriting history.
- **Issue & PR Linking**: Automatically parses `#123` / `gh-123` and turns them into clickable hyperlinks using your GitHub repository URL.
- **Zero Heavy Dependencies**: Pure Python standard library implementation with zero external runtime requirements.

---

## 📦 Installation

```bash
pip install git-changelog-craft
```

Or install locally in editable mode:

```bash
git clone https://github.com/slopggobblercobbler81/git-changelog-craft.git
cd git-changelog-craft
pip install -e .
```

---

## ⚡ Quick Start

### 1. Generate Changelog for Current Changes

```bash
# Print changelog markdown since the last tag to stdout
git-changelog-craft generate

# Prepend changes directly into CHANGELOG.md
git-changelog-craft generate -o CHANGELOG.md --update-file
```

### 2. Validate Git Commits in CI / Pull Requests

```bash
# Validate commits on current branch against main
git-changelog-craft validate --from-ref origin/main --strict
```

### 3. Compute the Next Semantic Version

```bash
# Preview the next version bump
git-changelog-craft bump

# Output just the next version string (ideal for scripting)
NEXT_VER=$(git-changelog-craft bump --dry-run)
echo "Next release: $NEXT_VER"
```

### 4. Output Formats

```bash
# Generate GitHub Release Notes
git-changelog-craft generate --format release-notes

# Generate JSON for CI pipelines
git-changelog-craft generate --format json
```

### 5. Parse a Single Commit Message

```bash
git-changelog-craft parse "feat(auth)!: add OAuth2 PKCE login flow (#42)"
```

Output:
```
Conventional : True
Type         : feat
Scope        : auth
Description  : add OAuth2 PKCE login flow (#42)
Breaking     : True
Breaking Desc: add OAuth2 PKCE login flow (#42)
References   : #42
```

### 6. Initialize Configuration File

```bash
git-changelog-craft init
```

This creates `.changelog-craft.json` with customizable categories and templates.

---

## ⚙️ Configuration (`.changelog-craft.json`)

```json
{
  "repo_url": "https://github.com/slopggobblercobbler81/git-changelog-craft",
  "commit_url_template": "{repo_url}/commit/{sha}",
  "issue_url_template": "{repo_url}/issues/{issue}",
  "sections": {
    "feat": "✨ Features",
    "fix": "🐛 Bug Fixes",
    "perf": "⚡ Performance Improvements",
    "refactor": "♻️ Code Refactoring",
    "docs": "📚 Documentation",
    "test": "🧪 Tests",
    "build": "📦 Build System",
    "ci": "👷 Continuous Integration",
    "chore": "🔧 Chores",
    "revert": "⏪ Reverts"
  },
  "breaking_section_title": "💥 Breaking Changes",
  "other_section_title": "📌 Other Changes",
  "include_other_commits": true,
  "include_authors": true,
  "default_version": "0.1.0"
}
```

---

## 🤖 GitHub Actions Workflow Example

Automate your release process and commit validation with GitHub Actions:

```yaml
name: Release & Validate

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install git-changelog-craft
        run: pip install git-changelog-craft
      - name: Validate Commits
        if: github.event_name == 'pull_request'
        run: git-changelog-craft validate --from-ref origin/main --strict

  release:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install git-changelog-craft
        run: pip install git-changelog-craft
      - name: Calculate Next Version
        id: bump
        run: |
          NEXT_VER=$(git-changelog-craft bump --dry-run)
          echo "version=$NEXT_VER" >> $GITHUB_OUTPUT
      - name: Generate Release Notes
        run: |
          git-changelog-craft generate --format release-notes --output release_notes.md
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.bump.outputs.version }}
          body_path: release_notes.md
```

---

## 🧪 Testing

Run unit tests locally with `pytest`:

```bash
python -m pytest -v
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
