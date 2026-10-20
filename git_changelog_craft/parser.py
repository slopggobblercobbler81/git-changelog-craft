"""Conventional Commits parser and data structures."""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional


CONVENTIONAL_HEADER_REGEX = re.compile(
    r"^(?P<type>[a-zA-Z]+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*"
    r"(?P<description>.+)$"
)

BREAKING_CHANGE_FOOTER_REGEX = re.compile(
    r"^(?:BREAKING\s+CHANGE|BREAKING-CHANGE):\s*(?P<desc>[\s\S]+)$",
    re.MULTILINE,
)

ISSUE_REF_REGEX = re.compile(
    r"(?:(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+)?(#\d+|gh-\d+)",
    re.IGNORECASE,
)

FOOTER_LINE_REGEX = re.compile(
    r"^(?P<token>[a-zA-Z0-9-]+|BREAKING CHANGE|BREAKING-CHANGE)(?::\s*|\s+#)(?P<value>.+)$"
)


@dataclass
class ConventionalCommit:
    sha: str = ""
    short_sha: str = ""
    author_name: str = ""
    author_email: str = ""
    date: str = ""
    raw_message: str = ""
    is_conventional: bool = False
    type: Optional[str] = None
    scope: Optional[str] = None
    description: str = ""
    body: Optional[str] = None
    is_breaking: bool = False
    breaking_description: Optional[str] = None
    references: List[str] = field(default_factory=list)
    footers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "sha": self.sha,
            "short_sha": self.short_sha,
            "author_name": self.author_name,
            "author_email": self.author_email,
            "date": self.date,
            "raw_message": self.raw_message,
            "is_conventional": self.is_conventional,
            "type": self.type,
            "scope": self.scope,
            "description": self.description,
            "body": self.body,
            "is_breaking": self.is_breaking,
            "breaking_description": self.breaking_description,
            "references": self.references,
            "footers": self.footers,
        }


class CommitParser:
    """Parses raw git commits into ConventionalCommit objects."""

    @classmethod
    def parse(
        cls,
        raw_message: str,
        sha: str = "",
        short_sha: str = "",
        author_name: str = "",
        author_email: str = "",
        date: str = "",
    ) -> ConventionalCommit:
        message = raw_message.strip()
        if not message:
            return ConventionalCommit(
                sha=sha,
                short_sha=short_sha,
                author_name=author_name,
                author_email=author_email,
                date=date,
                raw_message=raw_message,
                is_conventional=False,
                description="",
            )

        lines = message.splitlines()
        first_line = lines[0].strip()
        match = CONVENTIONAL_HEADER_REGEX.match(first_line)

        is_conventional = bool(match)
        commit_type = None
        scope = None
        breaking_flag = False
        description = first_line

        if match:
            gd = match.groupdict()
            commit_type = gd["type"].lower()
            scope = gd.get("scope")
            breaking_flag = bool(gd.get("breaking"))
            description = gd["description"].strip()

        # Parse body and footers
        body_lines: List[str] = []
        footers: Dict[str, str] = {}
        breaking_description: Optional[str] = None

        if len(lines) > 1:
            rest_of_message = "\n".join(lines[1:]).strip()
            # Check for breaking change footer in the rest of message
            bc_match = BREAKING_CHANGE_FOOTER_REGEX.search(rest_of_message)
            if bc_match:
                breaking_flag = True
                breaking_description = bc_match.group("desc").strip()

            paragraphs = rest_of_message.split("\n\n")
            body_paragraphs = []
            for para in paragraphs:
                para_lines = para.strip().splitlines()
                # Check if paragraph is footers
                is_footer_block = True
                para_footers: Dict[str, str] = {}
                for line in para_lines:
                    f_match = FOOTER_LINE_REGEX.match(line.strip())
                    if f_match:
                        token = f_match.group("token")
                        val = f_match.group("value")
                        para_footers[token] = val
                    else:
                        is_footer_block = False
                        break

                if is_footer_block and para_footers:
                    footers.update(para_footers)
                else:
                    body_paragraphs.append(para.strip())

            if body_paragraphs:
                body_lines.append("\n\n".join(body_paragraphs))

        body = "\n\n".join(body_lines).strip() if body_lines else None

        # Extract references (#123, gh-456)
        raw_refs = ISSUE_REF_REGEX.findall(raw_message)
        # Deduplicate while preserving order
        references: List[str] = []
        for ref in raw_refs:
            ref_clean = ref.strip()
            if ref_clean and ref_clean not in references:
                references.append(ref_clean)

        if breaking_flag and not breaking_description:
            # If `feat!: some breaking feature`, fallback breaking description to description
            breaking_description = description

        if not short_sha and sha:
            short_sha = sha[:7]

        return ConventionalCommit(
            sha=sha,
            short_sha=short_sha,
            author_name=author_name,
            author_email=author_email,
            date=date,
            raw_message=raw_message,
            is_conventional=is_conventional,
            type=commit_type,
            scope=scope,
            description=description,
            body=body,
            is_breaking=breaking_flag,
            breaking_description=breaking_description,
            references=references,
            footers=footers,
        )
