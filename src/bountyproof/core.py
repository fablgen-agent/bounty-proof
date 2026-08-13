from __future__ import annotations

import dataclasses
import datetime as dt
import re


ATTEMPT_PATTERN = re.compile(
    r"(?im)^\s*/(?:opire\s+)?try(?:\s|$)|^\s*/attempt(?:\s|$)"
)
SECURITY_PATTERN = re.compile(
    r"(?i)\b(?:security|vulnerability|exploit|penetration[ -]?test|red[ -]?team|audit)\b"
)


@dataclasses.dataclass(frozen=True)
class Evidence:
    issue_url: str
    title: str
    issue_state: str
    assignees: tuple[str, ...] = ()
    open_prs: tuple[str, ...] = ()
    attempts: int = 0
    repo_archived: bool = False
    repo_stars: int = 0
    repo_created_at: str | None = None
    repo_pushed_at: str | None = None
    reward_usd: float | None = None
    source: str | None = None
    security_related: bool = False


@dataclasses.dataclass(frozen=True)
class Assessment:
    verdict: str
    score: int
    reasons: tuple[str, ...]


def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def count_attempts(comments: list[str]) -> int:
    return sum(len(ATTEMPT_PATTERN.findall(comment)) for comment in comments)


def assess(evidence: Evidence, now: dt.datetime | None = None) -> Assessment:
    now = now or dt.datetime.now(dt.timezone.utc)
    score = 100
    reasons: list[str] = []

    if evidence.security_related:
        return Assessment("SKIP", 0, ("security-related work is out of scope",))
    if evidence.issue_state != "open":
        return Assessment("SKIP", 0, (f"issue is {evidence.issue_state}",))
    if evidence.repo_archived:
        return Assessment("SKIP", 0, ("repository is archived",))

    if evidence.assignees:
        score -= 45
        reasons.append("issue already has assignee(s): " + ", ".join(evidence.assignees))
    if evidence.open_prs:
        score -= 45
        reasons.append(f"{len(evidence.open_prs)} related open pull request(s)")
    if evidence.attempts:
        penalty = min(36, evidence.attempts * 4)
        score -= penalty
        reasons.append(f"{evidence.attempts} public attempt command(s)")

    pushed_at = parse_time(evidence.repo_pushed_at)
    if pushed_at and (now - pushed_at).days > 180:
        score -= 35
        reasons.append("repository has not been pushed in over 180 days")

    created_at = parse_time(evidence.repo_created_at)
    if created_at and (now - created_at).days < 90 and evidence.repo_stars < 10:
        score -= 35
        reasons.append("new low-signal repository")

    if evidence.reward_usd is None:
        score -= 25
        reasons.append("cash reward was not independently supplied or verified")
    elif evidence.reward_usd < 20:
        score -= 10
        reasons.append("reward is below $20")
    elif evidence.reward_usd >= 100:
        score += 5
        reasons.append(f"verified reward supplied: ${evidence.reward_usd:g}")

    score = max(0, min(100, score))
    verdict = "WORK" if score >= 75 else "WATCH" if score >= 50 else "SKIP"
    if not reasons:
        reasons.append("open, unassigned, active, and no related PR or attempt found")
    return Assessment(verdict, score, tuple(reasons))
