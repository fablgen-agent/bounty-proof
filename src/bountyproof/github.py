from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request

from .core import (
    Evidence,
    SECURITY_PATTERN,
    count_attempts,
    has_submission_block,
)


ISSUE_URL = re.compile(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)/?")


class GitHubError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")

    def get(self, path: str):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "bounty-proof/0.2.3",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request("https://api.github.com" + path, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception as error:
            raise GitHubError(f"GitHub request failed for {path}: {error}") from error

    def inspect(
        self,
        issue_url: str,
        *,
        reward_usd: float | None = None,
        source: str | None = None,
    ) -> Evidence:
        match = ISSUE_URL.fullmatch(issue_url)
        if not match:
            raise GitHubError("expected URL like https://github.com/owner/repo/issues/123")
        owner, repository, number = match.groups()
        full_name = f"{owner}/{repository}"
        issue = self.get(f"/repos/{full_name}/issues/{number}")
        repo = self.get(f"/repos/{full_name}")
        comments = self.get(f"/repos/{full_name}/issues/{number}/comments?per_page=100")
        query = urllib.parse.quote(f'repo:{full_name} is:pr "#{number}"')
        search = self.get(f"/search/issues?per_page=100&q={query}")
        reference = re.compile(
            rf"(?i)(?:#|/issues/){re.escape(number)}\b|(?:fix(?:e[sd])?|close[sd]?|resolve[sd]?)\s+#?{re.escape(number)}\b"
        )
        related_prs = []
        for pull_request in search.get("items", []):
            text = f"{pull_request.get('title') or ''}\n{pull_request.get('body') or ''}"
            if pull_request.get("state") == "open" and reference.search(text):
                related_prs.append(pull_request["html_url"])
        title_and_body = f"{issue.get('title') or ''}\n{issue.get('body') or ''}"
        return Evidence(
            issue_url=issue_url,
            title=issue.get("title") or "",
            issue_state=issue.get("state") or "unknown",
            assignees=tuple(person["login"] for person in issue.get("assignees", [])),
            open_prs=tuple(related_prs),
            attempts=count_attempts([comment.get("body") or "" for comment in comments]),
            repo_archived=bool(repo.get("archived")),
            repo_stars=int(repo.get("stargazers_count") or 0),
            repo_created_at=repo.get("created_at"),
            repo_pushed_at=repo.get("pushed_at"),
            reward_usd=reward_usd,
            source=source,
            security_related=bool(SECURITY_PATTERN.search(title_and_body)),
            submissions_blocked=has_submission_block(
                title_and_body,
                [
                    (
                        "ISSUE_AUTHOR"
                        if comment.get("user", {}).get("login")
                        == issue.get("user", {}).get("login")
                        else comment.get("author_association") or "",
                        comment.get("body") or "",
                    )
                    for comment in comments
                ],
            ),
        )
