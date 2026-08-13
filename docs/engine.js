export const attemptPattern = /^\s*\/(?:opire\s+)?try(?:\s|$)|^\s*\/attempt(?:\s|$)/gim;
export const securityPattern = /\b(?:security|vulnerability|exploit|penetration[ -]?test|red[ -]?team|audit)\b/i;
export const submissionBlockPattern = /\b(?:(?:please\s+)?refrain\s+from\s+submitting\s+(?:any\s+)?(?:additional|new)\s+(?:pull requests?|prs?|submissions?)|(?:please\s+)?do\s+not\s+submit\s+(?:any\s+)?(?:additional|new)\s+(?:pull requests?|prs?|submissions?)|(?:not|no\s+longer)\s+accepting\s+(?:any\s+)?(?:new\s+)?(?:pull requests?|prs?|submissions?|contributions?)|(?:bounty|submissions?)\s+(?:is|are)\s+(?:paused|closed|on\s+hold))\b/i;
export const maintainerAssociations = new Set(["OWNER", "MEMBER", "COLLABORATOR"]);

export function hasSubmissionBlock(issueText, comments) {
  if (submissionBlockPattern.test(issueText)) return true;
  return comments.some((comment) =>
    maintainerAssociations.has((comment.author_association || "").toUpperCase())
      && submissionBlockPattern.test(comment.body || ""),
  );
}

export function parseIssueUrl(value) {
  const match = value.trim().match(/^https:\/\/github\.com\/([^/]+)\/([^/]+)\/issues\/(\d+)\/?$/);
  if (!match) throw new Error("Enter a public GitHub issue URL.");
  return { owner: match[1], repository: match[2], number: match[3] };
}

export function countAttempts(comments) {
  return comments.reduce((total, comment) => {
    const matches = (comment.body || "").match(attemptPattern);
    return total + (matches ? matches.length : 0);
  }, 0);
}

export function findRelatedPullRequests(items, issueNumber) {
  const reference = new RegExp(
    `(?:#|/issues/)${issueNumber}\\b|(?:fix(?:e[sd])?|close[sd]?|resolve[sd]?)\\s+#?${issueNumber}\\b`,
    "i",
  );
  return items.filter((item) => item.state === "open" && reference.test(`${item.title || ""}\n${item.body || ""}`));
}

function daysSince(timestamp, now) {
  return timestamp ? (now - new Date(timestamp)) / 86_400_000 : 0;
}

export function scoreEvidence(evidence, now = new Date()) {
  if (evidence.securityRelated) return { verdict: "SKIP", score: 0, reasons: ["Security-related work is out of scope."] };
  if (evidence.issueState !== "open") return { verdict: "SKIP", score: 0, reasons: [`Issue is ${evidence.issueState}.`] };
  if (evidence.repoArchived) return { verdict: "SKIP", score: 0, reasons: ["Repository is archived."] };
  if (evidence.submissionsBlocked) return { verdict: "SKIP", score: 0, reasons: ["Maintainer text pauses or rejects new submissions."] };

  let score = 100;
  const reasons = [];
  if (evidence.assignees.length) {
    score -= 45;
    reasons.push(`Already assigned to ${evidence.assignees.join(", ")}.`);
  }
  if (evidence.openPullRequests.length) {
    score -= 45;
    reasons.push(`${evidence.openPullRequests.length} related open pull request(s).`);
  }
  if (evidence.attempts) {
    score -= Math.min(36, evidence.attempts * 4);
    reasons.push(`${evidence.attempts} public attempt command(s).`);
  }
  if (daysSince(evidence.repoPushedAt, now) > 180) {
    score -= 35;
    reasons.push("Repository has not been pushed in over 180 days.");
  }
  if (daysSince(evidence.repoCreatedAt, now) < 90 && evidence.repoStars < 10) {
    score -= 35;
    reasons.push("New low-signal repository.");
  }
  if (evidence.rewardUsd == null) {
    score -= 25;
    reasons.push("Reward amount was not independently supplied.");
  } else if (evidence.rewardUsd < 20) {
    score -= 10;
    reasons.push("Reward is below $20.");
  } else if (evidence.rewardUsd >= 100) {
    score += 5;
    reasons.push(`User-supplied reward: $${evidence.rewardUsd}.`);
  }
  score = Math.max(0, Math.min(100, score));
  if (!reasons.length) reasons.push("Open, unassigned, active, and no related PR or attempt found.");
  return { verdict: score >= 75 ? "WORK" : score >= 50 ? "WATCH" : "SKIP", score, reasons };
}
