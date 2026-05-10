/**
 * Example 1 — the smallest possible Claude Agent SDK call.
 *
 * Goal: prove that your CLAUDE_CODE_OAUTH_TOKEN works end-to-end.
 * Run:  npm run hello
 *
 * What this demonstrates:
 *   - Loading the OAuth token from .env
 *   - Guarding against the auth-precedence gotcha
 *   - Calling `query()` — the SDK's main async-iterable entrypoint
 *   - Filtering the message stream for assistant text
 *
 * For the bigger picture (what the Agent SDK actually is, why we use
 * an OAuth token instead of an API key, how billing works), see the
 * top-level README.md.
 */

// `dotenv/config` loads .env into process.env as a side effect. Doing
// it via the import keeps the side-effect at the top of the module
// where it belongs.
import "dotenv/config";
import { query } from "@anthropic-ai/claude-agent-sdk";

// Auth-precedence guards.
//
// The Agent SDK / Claude Code resolve auth in this order:
//   cloud creds > ANTHROPIC_AUTH_TOKEN > ANTHROPIC_API_KEY
//   > apiKeyHelper > CLAUDE_CODE_OAUTH_TOKEN > /login session
//
// Notice that ANTHROPIC_API_KEY beats CLAUDE_CODE_OAUTH_TOKEN. So if
// you have an API key exported from another project, it will silently
// shadow your OAuth token and bill API credits — not your Pro/Max
// subscription quota. Fail loudly so the user catches it before
// spending money they didn't mean to spend.
if (process.env.ANTHROPIC_API_KEY) {
  console.error(
    "ANTHROPIC_API_KEY is set and would take precedence over the OAuth token.\n" +
      "Run `unset ANTHROPIC_API_KEY` and try again.",
  );
  process.exit(1);
}

if (!process.env.CLAUDE_CODE_OAUTH_TOKEN) {
  console.error("CLAUDE_CODE_OAUTH_TOKEN is missing. Paste the token into .env first.");
  process.exit(1);
}

// `query(input)` returns an async iterable. Under the hood the SDK
// spawns the Claude Code binary as a subprocess and streams typed
// SDK*Message objects back to us: assistant text, tool calls,
// system events, results, etc.
//
// `allowedTools: []` disables every built-in tool. By default the
// Agent SDK enables a Claude-Code-like toolset (Bash, Read, Write,
// Glob, Grep, ...). For a hello-world we just want plain text.
for await (const message of query({
  prompt: "Say hello in one short sentence.",
  options: { allowedTools: [] },
})) {
  // For this example we only care about assistant text. Each
  // assistant message has a `.message.content` array of typed
  // content blocks (text, thinking, tool_use, ...).
  if (message.type === "assistant") {
    for (const block of message.message.content) {
      if (block.type === "text") {
        console.log(block.text);
      }
    }
  }
}
