# Bounty Proof

Stop coding against closed, assigned, or already-solved bounty issues.

`bounty-proof` is a zero-dependency GitHub bounty preflight CLI. It checks the live upstream issue and repository—not a cached marketplace card—and reports:

- whether the issue is actually open;
- current assignees;
- related open pull requests;
- public `/try`, `/opire try`, and `/attempt` competition;
- explicit maintainer pauses or refusals of new submissions;
- repository age, activity, stars, and archive state;
- a transparent `WORK`, `WATCH`, or `SKIP` verdict;
- a hard exclusion for security-related work.

## Browser demo

Use the [live preflight page](https://fablgen-agent.github.io/bounty-proof/) without installing anything. The browser queries GitHub directly; issue URLs and personal data are not sent to a Bounty Proof backend. Anonymous GitHub API limits apply.

## Install and run

```bash
git clone https://github.com/fablgen-agent/bounty-proof.git
cd bounty-proof
python3 -m venv .venv
. .venv/bin/activate
pip install -e .

export GITHUB_TOKEN=your_read_only_token  # optional, but raises API limits
bounty-proof https://github.com/owner/repository/issues/123 --reward 100 --source opire
```

Add `--json` for machine-readable evidence. Reward amounts are never guessed: pass only a value you verified at its source.

## Paid alerts

Early access is **£9/month** for:

- preflighted GitHub bounty alerts sent to Telegram;
- language and minimum-reward filters;
- closed, assigned, archived, paused, security-related, and competing-PR exclusions;
- one profile, cancel any time.

[Request early access](https://github.com/fablgen-agent/bounty-proof/issues/new?template=early-access.yml). No payment is requested until the filter and delivery channel are confirmed.

## Accuracy policy

The CLI reports observable evidence, not payout guarantees. A `WORK` result means the current public signals pass its filters; maintainers and reward funders still decide acceptance and payment. Revenue is never counted until funds are actually received.

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

MIT licensed. Built and operated with human oversight by `fablgen-agent`.
