# TypeScript — Agent SDK Hello World

> *Last updated: 2026-05-10. SDK versions move fast — check `package.json` against the latest on npm if something behaves unexpectedly.*

Three small examples building on each other, all using the OAuth-token / Pro-Max-subscription flow.

> **New here?** Read the [top-level README](../README.md) first — it explains what the Agent SDK is, how the OAuth flow works, and the auth-precedence gotcha. This file just covers TypeScript-specific setup and code walkthroughs.

> ⚠️ **Prototyping only.** The OAuth-token approach used here is for personal scripts and learning. Don't use it for production user-facing apps — every request bills against one person's subscription, which doesn't scale to multi-user traffic and may violate Anthropic's terms. For production, use the regular [`@anthropic-ai/sdk`](https://www.npmjs.com/package/@anthropic-ai/sdk) package with an `ANTHROPIC_API_KEY` from [console.anthropic.com](https://console.anthropic.com). See the [top-level README](../README.md#%EF%B8%8F-prototyping-only--do-not-use-for-production-user-facing-apps) for the full reasoning.

---

## Setup

### 1. Make sure you have Node.js 18+

```bash
node --version
```

Anything `v18.x` or newer works. The Agent SDK uses native `fetch` and async iteration, both of which require modern Node.

### 2. Install dependencies

From this `typescript/` directory:

```bash
npm install
```

This installs:

- `@anthropic-ai/claude-agent-sdk` — the Agent SDK (currently version `0.2.x`).
- `dotenv` — to load `CLAUDE_CODE_OAUTH_TOKEN` from `.env`.
- `tsx` — to run `.ts` files directly without a separate compile step.

> **Note on the bundled CLI.** The `@anthropic-ai/claude-agent-sdk` package depends on the Claude Code binary, which it ships as an optional npm dep. You usually don't need a separate global `claude` install for the SDK to work — but you *do* need one to run `claude setup-token` and the `/status` and `/usage` slash commands.

> **Versioning gotcha:** the TypeScript `@anthropic-ai/claude-agent-sdk` and Python `claude-agent-sdk` have **completely independent version lines**. TypeScript is at `0.2.x`; Python is at `0.1.x`. Don't try to "match" them.

### 3. Paste your OAuth token into `.env`

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

### 4. Make sure `ANTHROPIC_API_KEY` isn't shadowing it

```bash
unset ANTHROPIC_API_KEY
```

This is the #1 source of "why is my prototype using API credits I didn't expect to spend." See the auth-precedence section in the [top-level README](../README.md) for the full order.

---

## The three examples

Each example has a corresponding npm script defined in `package.json`:

| Example       | Run                  |
| ------------- | -------------------- |
| `hello.ts`    | `npm run hello`      |
| `check-auth.ts` | `npm run check-auth` |
| `news.ts`     | `npm run news`       |

Under the hood each script just runs `tsx src/<file>.ts`.

### Example 1 — `hello.ts`

**The smallest possible Agent SDK call.** If this prints a greeting, your token works.

```bash
npm run hello
```

Expected output: a one-sentence greeting from Claude.

**Key concepts:**

- `import { query } from "@anthropic-ai/claude-agent-sdk"` — the main async-iterable entrypoint.
- `options: { allowedTools: [] }` — disable all built-in tools so the model just answers in plain text. (By default the SDK enables a Claude-Code-like toolset including `Bash`, `Read`, `Write`, etc.)
- `for await (const message of query(...))` — the SDK spawns the Claude Code binary as a subprocess and streams `Message` objects back: assistant messages, tool use, system events.
- We filter `message.type === "assistant"` and print only `text`-type content blocks.

### Example 2 — `check-auth.ts`

**Diagnostic.** Doesn't call the SDK at all — it just inspects your env vars and tells you which credential the SDK *would* use.

```bash
npm run check-auth
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

### Example 3 — `news.ts`

**Two new concepts.** Asks Claude to fetch today's top news headlines.

```bash
npm run news
```

You'll see headlines stream in **token by token** rather than appearing in chunks.

**What's new vs `hello.ts`:**

1. **Built-in tools.** `allowedTools: ["WebSearch", "WebFetch"]` enables Claude Code's built-in web tools. They run **server-side** on Anthropic's infrastructure — you don't implement anything client-side.

2. **Token-level streaming.** By default the SDK yields whole assistant messages (so a paragraph arrives all at once). Setting `includePartialMessages: true` makes it *also* yield `stream_event` messages that wrap the raw Anthropic API stream events (`content_block_delta`, `text_delta`, ...). Match on those and you get one token at a time.

   ```typescript
   if (message.type === "stream_event") {
     const event = message.event;
     if (event.type === "content_block_delta" && event.delta.type === "text_delta") {
       process.stdout.write(event.delta.text);
     }
   }
   ```

3. **Explicit model selection.** `model: "claude-opus-4-7"` pins the model. Without this you get whatever the Claude Code CLI default is.

---

## Where to go next

- **Custom tools** — define your own TypeScript tools and let Claude call them. See the [Agent SDK docs](https://docs.claude.com/en/api/agent-sdk/typescript) for the `tool()` helper.
- **Multi-turn conversations** — `query()` is one-shot. For back-and-forth, use the `ClaudeSDKClient` class.
- **Permission callbacks** — intercept tool calls before they execute (approve/deny/modify).
- **MCP servers** — wire in external tools via the Model Context Protocol.

---

## Troubleshooting

| Symptom                                          | Likely cause                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `Cannot find module '@anthropic-ai/claude-agent-sdk'` | `npm install` didn't run, or you're in the wrong directory                       |
| Script hangs forever, no output                  | Claude Code CLI binary failed to spawn — check `node --version` (need 18+)            |
| 429 rate-limit errors                            | You're either using the OAuth token against the wrong endpoint, or you've actually exhausted your Max quota — check `claude /usage` |
| Token works in CLI but not from script          | `ANTHROPIC_API_KEY` is set in your shell — run `npm run check-auth` to confirm        |
| Top-level `await` errors                        | `tsconfig.json` needs `"target": "ESNext"` and `"module": "ESNext"` — check that yours matches the bundled one |
