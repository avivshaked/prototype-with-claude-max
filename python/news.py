"""Example 3 — built-in tools + token-by-token streaming.

Goal: ask Claude to fetch today's top news headlines and watch the
      response appear one token at a time.
Run:  python news.py

Two new concepts vs `hello.py`:

  1. **Server-side built-in tools.** `WebSearch` and `WebFetch` are
     run by Anthropic on their own infrastructure. We just declare
     them in `allowed_tools` and Claude calls them on its own.

  2. **Token-level streaming.** By default the SDK yields whole
     `AssistantMessage` objects (a paragraph arrives all at once).
     Setting `include_partial_messages=True` makes it ALSO yield
     `StreamEvent` objects — these wrap the raw Anthropic API
     stream events (`content_block_delta`, `text_delta`, ...). We
     unwrap those events to print one token at a time.

This is a good template for any prototype that needs (a) the model
to look something up on the web and (b) responsive streaming output.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# Same auth-precedence guard as hello.py — if ANTHROPIC_API_KEY is
# set it would silently shadow the OAuth token. See hello.py for
# the full explanation.
if os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit("ANTHROPIC_API_KEY is set — run `unset ANTHROPIC_API_KEY` first.")

from claude_agent_sdk import query, ClaudeAgentOptions, StreamEvent


async def main() -> None:
    options = ClaudeAgentOptions(
        # Pin the model explicitly. Without this you get whatever
        # the Claude Code CLI default is (usually Sonnet). Using the
        # full model id (no date suffix) lets Anthropic auto-upgrade
        # within the major version.
        model="claude-opus-4-7",
        # Allow only the web tools. WebSearch and WebFetch run
        # server-side — Anthropic queries the web for us and feeds
        # the results back into the model's context. We don't have
        # to implement any client-side tool handler.
        allowed_tools=["WebSearch", "WebFetch"],
        # Opt into per-token streaming. With this off we'd only see
        # complete `AssistantMessage` objects (chunky output).
        include_partial_messages=True,
    )

    async for message in query(
        prompt=(
            "Search the web for today's top 5 news headlines. "
            "For each one give: the headline, the source, and a one-sentence summary. "
            "Format as a numbered list."
        ),
        options=options,
    ):
        # The SDK yields several message types: AssistantMessage,
        # ToolUseBlock, SystemMessage, ResultMessage, ... and (because
        # we opted in above) StreamEvent for every individual API
        # stream event. We only care about the last category here.
        if isinstance(message, StreamEvent):
            # `event` is a plain dict mirroring the raw Anthropic API
            # stream event shape:
            #   { "type": "content_block_delta",
            #     "index": 0,
            #     "delta": { "type": "text_delta", "text": "Hello" } }
            #
            # Other event types include `message_start`,
            # `content_block_start`, `input_json_delta` (for tool-use
            # arguments), `message_stop`, etc. We filter for the one
            # that carries actual model-generated text.
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if delta.get("type") == "text_delta":
                    # `flush=True` is important: without it Python
                    # buffers stdout until the next newline, which
                    # defeats the whole point of streaming.
                    print(delta.get("text", ""), end="", flush=True)
    print()  # final newline after the streamed output


if __name__ == "__main__":
    asyncio.run(main())
