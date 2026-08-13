from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from .core import assess
from .github import GitHubClient, GitHubError


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        prog="bounty-proof",
        description="Verify a GitHub bounty against current upstream state.",
    )
    command.add_argument("issue_url")
    command.add_argument("--reward", type=float, help="Verified reward amount in USD")
    command.add_argument("--source", help="Reward platform or source")
    command.add_argument("--json", action="store_true", dest="as_json")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        evidence = GitHubClient().inspect(
            args.issue_url, reward_usd=args.reward, source=args.source
        )
    except GitHubError as error:
        print(str(error), file=sys.stderr)
        return 1
    result = assess(evidence)
    output = {
        "verdict": result.verdict,
        "score": result.score,
        "reasons": list(result.reasons),
        "evidence": dataclasses.asdict(evidence),
    }
    if args.as_json:
        print(json.dumps(output, indent=2))
    else:
        print(f"{result.verdict} {result.score}/100 — {evidence.title}")
        for reason in result.reasons:
            print(f"- {reason}")
        print(f"- {evidence.issue_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
