"""Command Line Interface for git-changelog-craft."""

import argparse
import json
import os
import sys
from typing import List, Optional

from git_changelog_craft import __version__
from git_changelog_craft.config import Config, DEFAULT_SECTIONS
from git_changelog_craft.generator import ChangelogGenerator
from git_changelog_craft.git import GitRepo
from git_changelog_craft.parser import CommitParser
from git_changelog_craft.semver import SemVer


def safe_print(text: str) -> None:
    """Safely print unicode strings even in legacy Windows console encodings."""
    try:
        print(text)
    except UnicodeEncodeError:
        enc = sys.stdout.encoding or "utf-8"
        print(text.encode(enc, errors="replace").decode(enc))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-changelog-craft",
        description="A fast, flexible CLI to generate changelogs, release notes, and version bumps from conventional commits.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # generate subcommand
    gen_p = subparsers.add_parser("generate", help="Generate changelog or release notes")
    gen_p.add_argument(
        "--all",
        action="store_true",
        help="Include all commits from repository root up to to-ref.",
    )
    gen_p.add_argument(
        "--from-ref",
        dest="from_ref",
        help="Starting git ref (tag/commit). Defaults to previous tag.",
    )
    gen_p.add_argument(
        "--to-ref",
        dest="to_ref",
        default="HEAD",
        help="Ending git ref. Defaults to HEAD.",
    )
    gen_p.add_argument(
        "--version-name",
        dest="version_name",
        help="Version title for generated section (e.g. 1.0.0). Defaults to automatic bump.",
    )
    gen_p.add_argument(
        "--repo-dir",
        dest="repo_dir",
        default=".",
        help="Path to git repository directory.",
    )
    gen_p.add_argument(
        "-f",
        "--format",
        choices=["markdown", "release-notes", "json"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    gen_p.add_argument(
        "-o",
        "--output",
        dest="output",
        help="File path to write output. If omitted, prints to stdout.",
    )
    gen_p.add_argument(
        "--update-file",
        action="store_true",
        help="Prepend/insert section into existing changelog file instead of overwriting.",
    )
    gen_p.add_argument(
        "--remote-url",
        dest="remote_url",
        help="Override repository web URL for commit/issue hyperlinks.",
    )
    gen_p.add_argument(
        "-c",
        "--config",
        dest="config_path",
        help="Path to custom config JSON file.",
    )

    # bump subcommand
    bump_p = subparsers.add_parser(
        "bump", help="Analyze commits and calculate the next semantic version"
    )
    bump_p.add_argument(
        "--all",
        action="store_true",
        help="Include all commits from repository root up to to-ref.",
    )
    bump_p.add_argument(
        "--from-ref",
        dest="from_ref",
        help="Starting git ref (tag/commit). Defaults to latest tag.",
    )
    bump_p.add_argument(
        "--to-ref",
        dest="to_ref",
        default="HEAD",
        help="Ending git ref. Defaults to HEAD.",
    )
    bump_p.add_argument(
        "--repo-dir",
        dest="repo_dir",
        default=".",
        help="Path to git repository directory.",
    )
    bump_p.add_argument(
        "--current-version",
        dest="current_version",
        help="Current version to bump from (e.g. 1.2.3). Defaults to latest tag or 0.1.0.",
    )
    bump_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Output the calculated next version string only.",
    )

    # parse subcommand
    parse_p = subparsers.add_parser(
        "parse", help="Parse a single commit message into conventional components"
    )
    parse_p.add_argument("message", help="Commit message string to parse")
    parse_p.add_argument(
        "--json",
        action="store_true",
        help="Output parsed commit details as JSON",
    )

    # init subcommand
    init_p = subparsers.add_parser(
        "init", help="Initialize a .changelog-craft.json configuration file"
    )
    init_p.add_argument(
        "-o",
        "--output",
        default=".changelog-craft.json",
        help="Target config file path (default: .changelog-craft.json)",
    )

    return parser


def handle_init(args: argparse.Namespace) -> int:
    config_dict = {
        "repo_url": None,
        "commit_url_template": "{repo_url}/commit/{sha}",
        "issue_url_template": "{repo_url}/issues/{issue}",
        "sections": DEFAULT_SECTIONS,
        "breaking_section_title": "💥 Breaking Changes",
        "other_section_title": "📌 Other Changes",
        "include_other_commits": True,
        "include_authors": True,
        "default_version": "0.1.0",
        "unreleased_title": "Unreleased",
    }
    target_path = args.output
    if os.path.exists(target_path):
        print(f"Error: configuration file '{target_path}' already exists.", file=sys.stderr)
        return 1

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)

    safe_print(f"Initialized configuration file at '{target_path}'")
    return 0


def handle_parse(args: argparse.Namespace) -> int:
    commit = CommitParser.parse(args.message)
    if args.json:
        safe_print(json.dumps(commit.to_dict(), indent=2))
    else:
        safe_print(f"Conventional : {commit.is_conventional}")
        safe_print(f"Type         : {commit.type or 'None'}")
        safe_print(f"Scope        : {commit.scope or 'None'}")
        safe_print(f"Description  : {commit.description}")
        safe_print(f"Breaking     : {commit.is_breaking}")
        if commit.breaking_description:
            safe_print(f"Breaking Desc: {commit.breaking_description}")
        if commit.references:
            safe_print(f"References   : {', '.join(commit.references)}")
        if commit.footers:
            safe_print("Footers      :")
            for k, v in commit.footers.items():
                safe_print(f"  {k}: {v}")
    return 0


def handle_bump(args: argparse.Namespace) -> int:
    repo = GitRepo(args.repo_dir)
    cfg = Config.load(search_dir=args.repo_dir)

    latest_tag = repo.get_latest_tag()
    from_ref = None if args.all else (args.from_ref or latest_tag)

    current_ver_str = args.current_version or latest_tag or cfg.default_version
    try:
        current_semver = SemVer.parse(current_ver_str)
    except ValueError:
        current_semver = SemVer.parse("0.1.0")

    commits = repo.get_commits(from_ref=from_ref, to_ref=args.to_ref)
    generator = ChangelogGenerator(cfg)
    bump_level = generator.determine_bump_level(commits)
    next_ver = current_semver.bump(bump_level)

    if args.dry_run:
        safe_print(str(next_ver))
    else:
        safe_print(f"Current version: {current_semver}")
        safe_print(f"Analyzed {len(commits)} commit(s) from '{from_ref or 'root'}' to '{args.to_ref}'")
        safe_print(f"Determined bump: {bump_level.value.upper()}")
        safe_print(f"Next version   : {next_ver}")
    return 0


def handle_generate(args: argparse.Namespace) -> int:
    repo = GitRepo(args.repo_dir)
    cfg = Config.load(config_path=args.config_path, search_dir=args.repo_dir)

    if args.remote_url:
        cfg.repo_url = args.remote_url
    elif not cfg.repo_url:
        cfg.repo_url = repo.get_remote_url()

    latest_tag = repo.get_latest_tag()
    from_ref = None if args.all else (args.from_ref or latest_tag)
    commits = repo.get_commits(from_ref=from_ref, to_ref=args.to_ref)

    generator = ChangelogGenerator(cfg)

    # Determine version name
    if args.version_name:
        version_name = args.version_name
    else:
        cur_str = latest_tag or cfg.default_version
        try:
            cur_sv = SemVer.parse(cur_str)
            bump_level = generator.determine_bump_level(commits)
            version_name = str(cur_sv.bump(bump_level))
        except ValueError:
            version_name = cfg.unreleased_title

    # Formatting
    if args.format == "json":
        data = generator.generate_json(version=version_name, commits=commits)
        output_text = json.dumps(data, indent=2)
    elif args.format == "release-notes":
        output_text = generator.generate_section(
            version=version_name, commits=commits, is_release_notes=True
        )
    else:
        # Markdown
        if args.update_file and args.output:
            generator.update_changelog_file(
                filepath=args.output,
                version=version_name,
                commits=commits,
            )
            safe_print(f"Updated changelog at '{args.output}' for version {version_name}")
            return 0
        else:
            output_text = generator.generate_section(
                version=version_name, commits=commits, is_release_notes=False
            )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_text + "\n")
        safe_print(f"Written output to '{args.output}'")
    else:
        safe_print(output_text)

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    # Try reconfiguring stdout to utf-8 if supported
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "init":
        return handle_init(args)
    elif args.command == "parse":
        return handle_parse(args)
    elif args.command == "bump":
        return handle_bump(args)
    elif args.command == "generate":
        return handle_generate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
