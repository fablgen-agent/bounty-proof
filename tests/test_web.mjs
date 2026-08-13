import assert from "node:assert/strict";
import test from "node:test";
import { countAttempts, findRelatedPullRequests, parseIssueUrl, scoreEvidence } from "../docs/engine.js";

const now = new Date("2026-08-13T00:00:00Z");
const clean = {
  issueState: "open", assignees: [], openPullRequests: [], attempts: 0,
  repoArchived: false, repoStars: 500, repoCreatedAt: "2020-01-01T00:00:00Z",
  repoPushedAt: "2026-08-12T00:00:00Z", rewardUsd: 100, securityRelated: false,
};

test("parses only GitHub issue URLs", () => {
  assert.deepEqual(parseIssueUrl("https://github.com/acme/tool/issues/42"), { owner: "acme", repository: "tool", number: "42" });
  assert.throws(() => parseIssueUrl("https://example.com/issues/42"));
});

test("counts explicit attempt commands", () => {
  assert.equal(countAttempts([{ body: "/try" }, { body: "/opire try\nplan" }, { body: "I will try" }]), 2);
});

test("finds only open pull requests that reference the issue", () => {
  const items = [
    { state: "open", title: "Fixes #42", body: "" },
    { state: "closed", title: "Fixes #42", body: "" },
    { state: "open", title: "Unrelated", body: "" },
  ];
  assert.equal(findRelatedPullRequests(items, "42").length, 1);
});

test("scores clean work and rejects closed or security work", () => {
  assert.equal(scoreEvidence(clean, now).verdict, "WORK");
  assert.deepEqual(scoreEvidence({ ...clean, issueState: "closed" }, now), { verdict: "SKIP", score: 0, reasons: ["Issue is closed."] });
  assert.equal(scoreEvidence({ ...clean, securityRelated: true }, now).score, 0);
});
