import datetime as dt
import unittest

from bountyproof.core import (
    SUBMISSION_BLOCK_PATTERN,
    Evidence,
    assess,
    count_attempts,
    has_submission_block,
)


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

    def test_maintainer_submission_pause_is_always_skip(self):
        result = assess(evidence(submissions_blocked=True), NOW)
        self.assertEqual((result.verdict, result.score), ("SKIP", 0))
        self.assertIn("rejects new submissions", result.reasons[0])

    def test_activepieces_pause_wording_is_detected(self):
        body = (
            "Kindly refrain from submitting additional PRs for this bounty "
            "while we wait for the review to complete."
        )
        self.assertIsNotNone(SUBMISSION_BLOCK_PATTERN.search(body))
        self.assertIsNone(
            SUBMISSION_BLOCK_PATTERN.search("Please review existing PRs before submitting.")
        )

    def test_only_authoritative_comments_can_block_submissions(self):
        message = "I'm not accepting any contributions from new contributors for this feature."
        self.assertTrue(has_submission_block("Open bounty", [("OWNER", message)]))
        self.assertTrue(has_submission_block("Open bounty", [("MEMBER", message)]))
        self.assertFalse(has_submission_block("Open bounty", [("CONTRIBUTOR", message)]))

    def test_issue_author_can_put_bounty_on_halt(self):
        message = "This is on halt until we have some public testing."
        self.assertTrue(has_submission_block("Open bounty", [("ISSUE_AUTHOR", message)]))
        self.assertFalse(has_submission_block("Open bounty", [("NONE", message)]))

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
