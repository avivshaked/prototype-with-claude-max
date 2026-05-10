# Prototype with Claude Max

A small, **educational** repo showing how to prototype with the **Claude Agent SDK** in Python and TypeScript, billed against a Claude **Pro or Max** subscription via an OAuth token — instead of paying per-token API credits.

If you already pay for Claude Pro/Max and want to script against the same model from your own code, this is the cheapest way to start.

---

## What is the Agent SDK?

The Agent SDK is two libraries:

| Language    | Package                                                                                            |
| ----------- | -------------------------------------------------------------------------------------------------- |
| Python      | [`claude-agent-sdk`](https://pypi.org/project/claude-agent-sdk/)                                   |
| TypeScript  | [`@anthropic-ai/claude-agent-sdk`](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk)   |

Both wrap the **Claude Code CLI**. When you call `query(...)`, the SDK spawns the Claude Code binary as a subprocess and pipes events back to your code: assistant text, tool use, system events, partial-message deltas, etc.

That subprocess can authenticate two ways:

1. **`ANTHROPIC_API_KEY`** — a Console API key. Billed per-token against your API account.
2. **`CLAUDE_CODE_OAUTH_TOKEN`** — a 1-year OAuth token tied to a Pro/Max subscription. Billed against your **subscription quota**.

This repo is configured for **option 2**.

> **Why not the regular Anthropic SDK?**
> The plain [`anthropic`](https://pypi.org/project/anthropic/) / [`@anthropic-ai/sdk`](https://www.npmjs.com/package/@anthropic-ai/sdk) packages call `https://api.anthropic.com/v1/messages` directly. Pro/Max OAuth tokens are issued for use **through Claude Code** (and the Agent SDK on top of it). Using one against the raw Messages API works in principle but hits aggressive rate limits almost immediately. The Agent SDK route is the supported path.

---

## Prerequisites

- A **Claude Pro or Max** subscription (the OAuth token is tied to it)
- The **Claude Code CLI** installed:
  ```bash
  npm install -g @anthropic-ai/claude-code
  ```
- **Python 3.10+** (for the Python examples)
- **Node.js 18+** (for the TypeScript examples)

---

## Step 1 — Get your OAuth token

In a terminal:

```bash
claude setup-token
```

This launches a browser flow that creates a 1-year, **inference-scoped** OAuth token starting with `sk-ant-oat01-`. It's only valid for making model calls (it can't read your conversations or change account settings). Copy the token — you'll paste it into the per-language `.env` file in step 2.

---

## Step 2 — Pick a language

Each subfolder is **self-contained** and includes its own setup walkthrough:

- 🐍 **Python** → [`python/README.md`](python/README.md)
- 🟦 **TypeScript** → [`typescript/README.md`](typescript/README.md)

Both folders contain the same three examples, in increasing complexity:

| Example       | Demonstrates                                                                                          |
| ------------- | ----------------------------------------------------------------------------------------------------- |
| `hello`       | The smallest possible `query()` call. Confirms your auth works.                                       |
| `check_auth`  | Which credential the SDK will actually use, and why precedence matters.                               |
| `news`        | Built-in `WebSearch` tool + token-by-token streaming via partial-message events.                      |

---

## Auth precedence — the gotcha that costs people money

The Agent SDK / Claude Code resolves auth in this order:

1. **Cloud provider creds** (`CLAUDE_CODE_USE_BEDROCK`, `..._VERTEX`, `..._FOUNDRY`)
2. **`ANTHROPIC_AUTH_TOKEN`** (bearer, billed per token)
3. **`ANTHROPIC_API_KEY`** (Console API key, billed per token)
4. **`apiKeyHelper`** (a configured helper script, if any)
5. **`CLAUDE_CODE_OAUTH_TOKEN`** (Pro/Max subscription) ← **what we want**
6. **Interactive `/login` session** (fallback to whatever the CLI cached)

If you have an `ANTHROPIC_API_KEY` exported from another project, it will **silently** shadow your OAuth token and bill API credits instead. The `hello` example fails loudly when this happens, and the `check_auth` example diagnoses it.

```bash
unset ANTHROPIC_API_KEY   # the safest thing you can do before running these
```

---

## Monitoring your Pro/Max usage

Pro/Max usage is visible in the Claude Code CLI itself:

```bash
claude          # starts an interactive session
> /status       # account state, current model, auth method
> /usage        # current 5-hour and 7-day rolling windows
```

The Agent SDK shares the same quota — usage from your scripts shows up here too.

---

## Repo layout

```
agent-sdk-hello-world/
├── README.md                  # ← you are here
├── .gitignore                 # secrets, OS junk, build outputs
├── python/
│   ├── README.md              # Python-specific setup + walkthroughs
│   ├── hello.py
│   ├── check_auth.py
│   ├── news.py
│   ├── requirements.txt
│   ├── .env.example           # template — copy to .env and fill in
│   └── .env                   # gitignored — your real OAuth token
└── typescript/
    ├── README.md              # TypeScript-specific setup + walkthroughs
    ├── src/
    │   ├── hello.ts
    │   ├── check-auth.ts
    │   └── news.ts
    ├── package.json
    ├── tsconfig.json
    ├── .env.example           # template — copy to .env and fill in
    └── .env                   # gitignored — your real OAuth token
```

---

## A note for LLM readers

This repo is intentionally written to be readable by both humans and LLMs. Each example file leads with a docstring/JSDoc explaining **what it demonstrates**, and inline comments explain the **why** of every non-obvious step (auth precedence, streaming opt-in, tool allowlisting). The READMEs are the conceptual layer; the code is the worked example.

If you're an agent helping a user with this repo, the most common failure modes are:
1. `ANTHROPIC_API_KEY` shadowing the OAuth token (run `python check_auth.py` to diagnose)
2. Python venv on a < 3.10 interpreter (`claude-agent-sdk` requires 3.10+)
3. Confusing the Python SDK version (`0.1.x`) with the TypeScript SDK version (`0.2.x`) — they have **independent** version lines
4. Trying to use the OAuth token against the regular Messages API directly — it gets rate-limited
