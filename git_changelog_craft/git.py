"""Git repository operations and commit extraction."""

from dataclasses import dataclass
import os
import re
import subprocess
from typing import List, Optional

from git_changelog_craft.parser import CommitParser, ConventionalCommit
from git_changelog_craft.semver import SemVer


RECORD_SEPARATOR = "\x1e"
UNIT_SEPARATOR = "\x1f"


@dataclass
class GitTag:
    name: str
    semver: Optional[SemVer] = None


class GitRepo:
    """Helper for executing git operations in a local repository."""

    def __init__(self, repo_dir: str = "."):
        self.repo_dir = repo_dir

    def _run_git(self, args: List[str]) -> str:
        if not os.path.isdir(self.repo_dir):
            return ""
        cmd = ["git"] + args
        try:
            res = subprocess.run(
                cmd,
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
            if res.returncode != 0:
                return ""
            return res.stdout.strip()
        except OSError:
            return ""

    def is_git_repository(self) -> bool:
        res = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return res.strip() == "true"

    def get_remote_url(self) -> Optional[str]:
        raw = self._run_git(["config", "--get", "remote.origin.url"])
        if not raw:
            raw = self._run_git(["remote", "get-url", "origin"])
        if not raw:
            return None

        # Convert SSH/Git format to HTTPS
        # git@github.com:owner/repo.git -> https://github.com/owner/repo
        ssh_match = re.match(r"^git@([^:]+):([^/]+)/(.+?)(?:\.git)?$", raw)
        if ssh_match:
            host, owner, repo = ssh_match.groups()
            return f"https://{host}/{owner}/{repo}"

        # https://github.com/owner/repo.git -> https://github.com/owner/repo
        if raw.endswith(".git"):
            raw = raw[:-4]
        return raw

    def get_tags(self) -> List[GitTag]:
        output = self._run_git(["tag", "-l"])
        if not output:
            return []

        raw_tags = [t.strip() for t in output.splitlines() if t.strip()]
        tags: List[GitTag] = []
        for t in raw_tags:
            semver = None
            try:
                semver = SemVer.parse(t)
            except ValueError:
                pass
            tags.append(GitTag(name=t, semver=semver))

        # Sort tags by semver descending if available, else by name
        def sort_key(gt: GitTag):
            if gt.semver:
                return (1, gt.semver.tuple_key())
            return (0, (gt.name,))

        tags.sort(key=sort_key, reverse=True)
        return tags

    def get_latest_tag(self) -> Optional[str]:
        tags = self.get_tags()
        if not tags:
            return None
        return tags[0].name

    def get_commits(
        self,
        from_ref: Optional[str] = None,
        to_ref: str = "HEAD",
    ) -> List[ConventionalCommit]:
        """Fetch commits in the range from_ref..to_ref."""
        if not self.is_git_repository():
            return []

        # Check if HEAD exists
        head_check = self._run_git(["rev-parse", "--verify", to_ref])
        if not head_check:
            return []

        git_args = [
            "log",
            f"--pretty=format:%H{UNIT_SEPARATOR}%h{UNIT_SEPARATOR}%an{UNIT_SEPARATOR}%ae{UNIT_SEPARATOR}%aI{UNIT_SEPARATOR}%B{RECORD_SEPARATOR}",
        ]

        if from_ref:
            git_args.append(f"{from_ref}..{to_ref}")
        else:
            git_args.append(to_ref)

        output = self._run_git(git_args)
        if not output:
            return []

        records = output.split(RECORD_SEPARATOR)
        commits: List[ConventionalCommit] = []

        for record in records:
            record = record.strip()
            if not record:
                continue

            parts = record.split(UNIT_SEPARATOR)
            if len(parts) >= 6:
                sha = parts[0].strip()
                short_sha = parts[1].strip()
                author_name = parts[2].strip()
                author_email = parts[3].strip()
                date = parts[4].strip()
                raw_message = parts[5].strip()

                commit = CommitParser.parse(
                    raw_message=raw_message,
                    sha=sha,
                    short_sha=short_sha,
                    author_name=author_name,
                    author_email=author_email,
                    date=date,
                )
                commits.append(commit)

        return commits
