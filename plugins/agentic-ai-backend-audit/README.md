<h1 align="center">🛡️ agentic-ai-backend-audit</h1>

<p align="center">
  <strong>The senior review your AI agent's backend never got.</strong><br>
  Run it after an agent finishes a feature — lint and tests pass, but the bugs AI ships don't show up there.
</p>

<p align="center">
  <a href="../../README.md">ghost-skills</a> •
  <a href="#install">Install</a> •
  <a href="skills/agentic-ai-backend-audit/SKILL.md">SKILL.md</a> •
  <a href="#the-18-lenses">Lenses</a>
</p>

<p align="center">
  <img alt="lenses" src="https://img.shields.io/badge/lenses-18-8b5cf6">
  <img alt="severity" src="https://img.shields.io/badge/severity-0%E2%80%934-d97757">
  <img alt="owasp" src="https://img.shields.io/badge/OWASP-LLM%20%2B%20API%20%2B%20Agentic-3fb950">
  <img alt="read-only" src="https://img.shields.io/badge/mode-read--only-2563eb">
</p>

---

## What is this?

A skill that runs a **principal engineer's adversarial review** of a backend change
**after an AI agent finishes it** — when `lint`, types, and unit tests are green but
nobody senior has looked. It's tuned for the failure classes AI-built and agentic
backends ship most: **missing authorization, data leakage, prompt-injection escape,
excessive agency, silent failures, and runaway cost.**

Every finding **names the issue, cites `file:line`, warns "⚠ this may cause …",
gives a one-line fix, and rates severity 0–4** — ending in a **Ship / Fix-then-ship /
Block** verdict. Read-only: it reports; you ask for fixes as a separate step.

## The 18 lenses

| # | Lens | # | Lens |
|---|------|---|------|
| **A. Security** | | **D. Reliability** | |
| 1 | Access control & authorization (BOLA/IDOR, tenancy, JWT) | 10 | Agent runtime resilience (retries, idempotency, budgets) |
| 2 | Injection & API security (OWASP API Top 10, SSRF) | 11 | Resource-exhaustion ordering |
| 3 | Secrets & supply chain (MCP trust, slopsquatting) | 12 | Silent failures (async/streaming) |
| **B. Prompt & agent safety** | | 13 | Schema / contract / state drift |
| 4 | Prompt injection & system-prompt leakage | 14 | Cost & token controls |
| 5 | Excessive agency & tool safety | **E. Observability & governance** | |
| 6 | Content filtering & output safety | 15 | Observability & tracing (OTel GenAI) |
| 7 | Memory & RAG integrity | 16 | Evals & non-determinism |
| **C. Data protection & leakage** | | 17 | Compliance & governance (EU AI Act, audit trails) |
| 8 | PII/PHI handling | **F. AI-authorship hygiene** | |
| 9 | Data-leakage vectors (×9: RAG, embeddings, logs, errors, output, cross-tenant, cache, prompt, egress) | 18 | AI code smells & artefact leakage |

Each lens carries concrete **detection checks (grep patterns + code smells)**, **impact
warnings**, **example findings**, **severity guidance**, and **false-positives to
suppress** — in the category reference files under `skills/agentic-ai-backend-audit/references/`.

## Install

```text
/plugin marketplace add CreatorGhost/ghost-skills
/plugin install agentic-ai-backend-audit@ghost-skills
```

…or copy `skills/agentic-ai-backend-audit` into `~/.claude/skills/`.

## Use

```text
/agentic-ai-backend-audit             # explicit
audit the change I just made          # natural
is this leaking any data?             # natural
is this safe to push?                 # natural
```

It runs from the project root, scopes to the staged diff (or `main..HEAD`), reads every
changed file in full, runs the lenses, and returns a severity-grouped report with a verdict.

## How it works

```text
1. Scope      — diff + platform shape (CRUD? LLM/agent? RAG? multi-tenant? PII?)
2. Read       — every changed file in full, plus key callers
3. Run lenses — category by category (or one subagent per category, in parallel)
4. Rate       — severity 0–4 + an impact warning on every finding
5. Triage     — pre-existing bugs go under "Out of scope"
6. Report     — grouped by severity → Ship / Fix-then-ship / Block
```

## Author

**Aditya Pratap Singh** — [@CreatorGhost](https://github.com/CreatorGhost)

## License

[MIT](../../LICENSE)
