import datetime as dt
import unittest

from bountyproof.core import Evidence, assess, count_attempts


NOW = dt.datetime(2026, 8, 13, tzinfo=dt.timezone.utc)


def evidence(**overrides):
    values = {
        "issue_url": "https://github.com/example/project/issues/1",
        "title": "Add CSV export",
        "issue_state": "open",
        "repo_stars": 500,
        "repo_created_at": "2020-01-01T00:00:00Z",
        "repo_pushed_at": "2026-08-12T00:00:00Z",
        "reward_usd": 100,
    }
    values.update(overrides)
    return Evidence(**values)


class AssessmentTests(unittest.TestCase):
    def test_clean_funded_issue_is_work(self):
        result = assess(evidence(), NOW)
        self.assertEqual(result.verdict, "WORK")
        self.assertEqual(result.score, 100)

    def test_closed_issue_is_always_skip(self):
        result = assess(evidence(issue_state="closed"), NOW)
        self.assertEqual((result.verdict, result.score), ("SKIP", 0))

    def test_security_work_is_always_skip(self):
        result = assess(evidence(security_related=True), NOW)
        self.assertEqual((result.verdict, result.score), ("SKIP", 0))

    def test_competing_pr_and_attempts_are_skip(self):
        result = assess(
            evidence(open_prs=("https://github.com/example/project/pull/2",), attempts=4),
            NOW,
        )
        self.assertEqual(result.verdict, "SKIP")

    def test_new_low_signal_repo_is_penalized(self):
        result = assess(
            evidence(repo_stars=1, repo_created_at="2026-08-01T00:00:00Z"), NOW
        )
        self.assertEqual(result.verdict, "WATCH")

    def test_attempt_commands_are_counted_without_generic_comments(self):
        comments = ["/try", "/opire try\nstarting", "/attempt #1", "I will try this"]
        self.assertEqual(count_attempts(comments), 3)


if __name__ == "__main__":
    unittest.main()
