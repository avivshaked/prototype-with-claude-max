# Python — Agent SDK Hello World

Three small examples building on each other, all using the OAuth-token / Pro-Max-subscription flow.

> **New here?** Read the [top-level README](../README.md) first — it explains what the Agent SDK is, how the OAuth flow works, and the auth-precedence gotcha. This file just covers Python-specific setup and code walkthroughs.

---

## Setup

### 1. Make sure you have Python 3.10+

The Python Agent SDK requires Python ≥ 3.10. macOS ships with 3.9, so you'll likely want a newer one from [python.org](https://www.python.org/downloads/) or Homebrew:

```bash
brew install python@3.12
which python3.12   # /opt/homebrew/bin/python3.12 on Apple Silicon
```

Check what you have:

```bash
python3 --version
```

### 2. Create a virtualenv

From this `python/` directory:

```bash
# Use a 3.10+ interpreter explicitly — don't trust whatever `python3` resolves to
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:

- `claude-agent-sdk` — the Agent SDK itself (currently version `0.1.x`)
- `python-dotenv` — to load `CLAUDE_CODE_OAUTH_TOKEN` from `.env`

> **Versioning gotcha:** the Python `claude-agent-sdk` and TypeScript `@anthropic-ai/claude-agent-sdk` have **completely independent version lines**. Python is at `0.1.x`; TypeScript is at `0.2.x`. Don't try to "match" them.

### 4. Paste your OAuth token into `.env`

If you haven't already, generate a token:

```bash
claude setup-token
```

Then copy the template and fill it in:

```bash
cp .env.example .env
# open .env in your editor and replace the placeholder with the
# real `sk-ant-oat01-...` token you just generated
```

`.env` is gitignored (won't be committed). `.env.example` is committed — it's the template new contributors copy from.

### 5. Make sure `ANTHROPIC_API_KEY` isn't shadowing it

```bash
unset ANTHROPIC_API_KEY
```

This is the #1 source of "why is my prototype using API credits I didn't expect to spend." See the auth-precedence section in the [top-level README](../README.md) for the full order.

---

## The three examples

### Example 1 — `hello.py`

**The smallest possible Agent SDK call.** If this prints a greeting, your token works.

```bash
python hello.py
```

Expected output: a one-sentence greeting from Claude.

**Key concepts:**

- `from claude_agent_sdk import query` — the main async-generator entrypoint.
- `ClaudeAgentOptions(allowed_tools=[])` — disable all built-in tools so the model just answers in plain text. (By default the SDK enables a Claude-Code-like toolset including `Bash`, `Read`, `Write`, etc.)
- `async for message in query(...)` — the SDK spawns the Claude Code binary as a subprocess and streams `Message` objects back: assistant messages, tool use, system events.
- We filter for `AssistantMessage` and print only the `TextBlock` content.

### Example 2 — `check_auth.py`

**Diagnostic.** Doesn't call the SDK at all — it just inspects your env vars and tells you which credential the SDK *would* use.

```bash
python check_auth.py
```

Expected output:

```
Detected env vars:
  ANTHROPIC_API_KEY        = (unset)
  ANTHROPIC_AUTH_TOKEN     = (unset)
  CLAUDE_CODE_OAUTH_TOKEN  = sk-ant-oat…AOVx
  ...

Active method per docs precedence: CLAUDE_CODE_OAUTH_TOKEN (Pro/Max subscription)
```

If it says anything other than `CLAUDE_CODE_OAUTH_TOKEN (Pro/Max subscription)`, you're not actually using your subscription. Run `unset` on whatever's winning and try again.

### Example 3 — `news.py`

**Two new concepts.** Asks Claude to fetch today's top news headlines.

```bash
python news.py
```

You'll see headlines stream in **token by token** rather than appearing in chunks.

**What's new vs `hello.py`:**

1. **Built-in tools.** `allowed_tools=["WebSearch", "WebFetch"]` enables Claude Code's built-in web tools. They run **server-side** on Anthropic's infrastructure — you don't implement anything client-side.

2. **Token-level streaming.** By default the SDK yields complete `AssistantMessage` blocks (so a paragraph arrives all at once). Setting `include_partial_messages=True` makes it *also* yield `StreamEvent` objects that wrap the raw Anthropic API stream events (`content_block_delta`, `text_delta`, ...). Unwrap those and you get one token at a time.

   ```python
   if isinstance(message, StreamEvent):
       event = message.event
       if event.get("type") == "content_block_delta":
           delta = event.get("delta", {})
           if delta.get("type") == "text_delta":
               print(delta.get("text", ""), end="", flush=True)
   ```

3. **Explicit model selection.** `model="claude-opus-4-7"` pins the model. Without this you get whatever the Claude Code CLI default is.

---

## Where to go next

- **Custom tools** — define your own Python functions and let Claude call them. See the [Agent SDK docs](https://docs.claude.com/en/api/agent-sdk/python) for the `@tool` decorator pattern.
- **Multi-turn conversations** — `query()` is one-shot. For back-and-forth, use the `ClaudeSDKClient` class.
- **Permission callbacks** — intercept tool calls before they execute (approve/deny/modify).
- **MCP servers** — wire in external tools via the Model Context Protocol.

---

## Troubleshooting

| Symptom                                          | Likely cause                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: No module named 'dotenv'`  | venv not activated, or `pip install` failed silently                                  |
| `ERROR: No matching distribution found ...`      | Wrong Python version (need 3.10+) or wrong package version pinned in `requirements.txt` |
| Script hangs forever, no output                  | Claude Code CLI isn't installed (`npm install -g @anthropic-ai/claude-code`)          |
| 429 rate-limit errors                            | Almost always means you're using the OAuth token against the wrong endpoint, or you've actually exhausted your Max quota — check `claude /usage` |
| Token works in CLI but not from script          | `ANTHROPIC_API_KEY` is set in your shell — run `python check_auth.py` to confirm      |
