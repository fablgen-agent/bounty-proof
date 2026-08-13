import { countAttempts, findRelatedPullRequests, parseIssueUrl, scoreEvidence, securityPattern, submissionBlockPattern } from "./engine.js";

const form = document.querySelector("#preflight-form");
const button = form.querySelector("button");
const output = document.querySelector("#result");

async function github(path) {
  const response = await fetch(`https://api.github.com${path}`, {
    headers: { Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" },
  });
  if (!response.ok) {
    const remaining = response.headers.get("x-ratelimit-remaining");
    throw new Error(response.status === 403 && remaining === "0" ? "GitHub's anonymous API limit was reached. Try later or use the CLI with a token." : `GitHub returned ${response.status}.`);
  }
  return response.json();
}

function render(result, evidence) {
  output.hidden = false;
  output.className = `result ${result.verdict.toLowerCase()}`;
  output.replaceChildren();
  const heading = document.createElement("h3");
  heading.textContent = `${result.verdict} · ${result.score}/100`;
  const title = document.createElement("p");
  title.className = "result-title";
  title.textContent = evidence.title;
  const list = document.createElement("ul");
  for (const reason of result.reasons) {
    const item = document.createElement("li");
    item.textContent = reason;
    list.append(item);
  }
  const facts = document.createElement("p");
  facts.className = "facts";
  facts.textContent = `${evidence.repoStars.toLocaleString()} stars · ${evidence.attempts} attempts · ${evidence.openPullRequests.length} related open PRs`;
  output.append(heading, title, list, facts);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  button.textContent = "Checking live GitHub state…";
  output.hidden = true;
  try {
    const issueUrl = new FormData(form).get("issue-url");
    const rewardValue = new FormData(form).get("reward");
    const { owner, repository, number } = parseIssueUrl(issueUrl);
    const fullName = `${owner}/${repository}`;
    const query = encodeURIComponent(`repo:${fullName} is:pr "#${number}"`);
    const [issue, repo, comments, search] = await Promise.all([
      github(`/repos/${fullName}/issues/${number}`),
      github(`/repos/${fullName}`),
      github(`/repos/${fullName}/issues/${number}/comments?per_page=100`),
      github(`/search/issues?per_page=100&q=${query}`),
    ]);
    const openPullRequests = findRelatedPullRequests(search.items || [], number);
    const evidence = {
      title: issue.title || "",
      issueState: issue.state || "unknown",
      assignees: (issue.assignees || []).map((person) => person.login),
      openPullRequests,
      attempts: countAttempts(comments),
      repoArchived: Boolean(repo.archived),
      repoStars: Number(repo.stargazers_count || 0),
      repoCreatedAt: repo.created_at,
      repoPushedAt: repo.pushed_at,
      rewardUsd: rewardValue === "" ? null : Number(rewardValue),
      securityRelated: securityPattern.test(`${issue.title || ""}\n${issue.body || ""}`),
      submissionsBlocked: submissionBlockPattern.test(`${issue.title || ""}\n${issue.body || ""}`),
    };
    render(scoreEvidence(evidence), evidence);
  } catch (error) {
    output.hidden = false;
    output.className = "result error";
    output.textContent = error.message;
  } finally {
    button.disabled = false;
    button.textContent = "Run live preflight";
  }
});
