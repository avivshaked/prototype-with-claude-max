/**
 * Example 3 — built-in tools + token-by-token streaming.
 *
 * Goal: ask Claude to fetch today's top news headlines and watch the
 *       response appear one token at a time.
 * Run:  npm run news
 *
 * Two new concepts vs `hello.ts`:
 *
 *   1. **Server-side built-in tools.** `WebSearch` and `WebFetch` are
 *      run by Anthropic on their own infrastructure. We just declare
 *      them in `allowedTools` and Claude calls them on its own.
 *
 *   2. **Token-level streaming.** By default the SDK yields whole
 *      assistant messages (a paragraph arrives all at once).
 *      Setting `includePartialMessages: true` makes it ALSO yield
 *      `stream_event` messages — these wrap the raw Anthropic API
 *      stream events (`content_block_delta`, `text_delta`, ...). We
 *      unwrap those events to print one token at a time.
 *
 * This is a good template for any prototype that needs (a) the model
 * to look something up on the web and (b) responsive streaming output.
 */

import "dotenv/config";
import { query } from "@anthropic-ai/claude-agent-sdk";

// Same auth-precedence guard as hello.ts — if ANTHROPIC_API_KEY is
// set it would silently shadow the OAuth token. See hello.ts for
// the full explanation.
if (process.env.ANTHROPIC_API_KEY) {
  console.error("ANTHROPIC_API_KEY is set — run `unset ANTHROPIC_API_KEY` first.");
  process.exit(1);
}

for await (const message of query({
  prompt:
    "Search the web for today's top 5 news headlines. " +
    "For each one give: the headline, the source, and a one-sentence summary. " +
    "Format as a numbered list.",
  options: {
    // Pin the model explicitly. Without this you get whatever the
    // Claude Code CLI default is (usually Sonnet). Using the full
    // model id (no date suffix) lets Anthropic auto-upgrade within
    // the major version.
    model: "claude-opus-4-7",
    // Allow only the web tools. WebSearch and WebFetch run
    // server-side — Anthropic queries the web for us and feeds the
    // results back into the model's context. We don't have to
    // implement any client-side tool handler.
    allowedTools: ["WebSearch", "WebFetch"],
    // Opt into per-token streaming. With this off we'd only see
    // complete assistant messages (chunky output).
    includePartialMessages: true,
  },
})) {
  // The SDK yields several message types: assistant, user, result,
  // system, ... and (because we opted in above) `stream_event` for
  // every individual API stream event. We only care about the last
  // category here.
  if (message.type === "stream_event") {
    // `event` mirrors the raw Anthropic API stream event shape:
    //   { type: "content_block_delta",
    //     index: 0,
    //     delta: { type: "text_delta", text: "Hello" } }
    //
    // Other event types include `message_start`,
    // `content_block_start`, `input_json_delta` (for tool-use
    // arguments), `message_stop`, etc. We filter for the one that
    // carries actual model-generated text.
    const event = message.event;
    if (event.type === "content_block_delta" && event.delta.type === "text_delta") {
      // process.stdout.write avoids the trailing newline that
      // console.log adds — important when each chunk is a few tokens.
      process.stdout.write(event.delta.text);
    }
  }
}
console.log(); // final newline after the streamed output
