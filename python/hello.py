"""Example 1 — the smallest possible Claude Agent SDK call.

Goal: prove that your CLAUDE_CODE_OAUTH_TOKEN works end-to-end.
Run:  python hello.py

What this demonstrates:
  - Loading the OAuth token from .env
  - Guarding against the auth-precedence gotcha
  - Calling `query()` — the SDK's main async-iterator entrypoint
  - Filtering the message stream for assistant text

For the bigger picture (what the Agent SDK actually is, why we use
an OAuth token instead of an API key, how billing works), see the
top-level README.md.
"""

import asyncio
import os
import sys

# Step 1. Load .env into os.environ so CLAUDE_CODE_OAUTH_TOKEN
# becomes available. python-dotenv is a no-op in production
# environments where the env var is set some other way.
from dotenv import load_dotenv

load_dotenv()

# Step 2. Auth-precedence guards.
#
# The Agent SDK / Claude Code resolve auth in this order:
#   cloud creds > ANTHROPIC_AUTH_TOKEN > ANTHROPIC_API_KEY
#   > apiKeyHelper > CLAUDE_CODE_OAUTH_TOKEN > /login session
#
# Notice that ANTHROPIC_API_KEY beats CLAUDE_CODE_OAUTH_TOKEN. So if
# you have an API key exported from another project, it will silently
# shadow your OAuth token and bill API credits — not your Pro/Max
# subscription quota. Fail loudly here so the user catches it before
# spending money they didn't mean to spend.
if os.environ.get("ANTHROPIC_API_KEY"):
    sys.exit(
        "ANTHROPIC_API_KEY is set and would take precedence over the OAuth token.\n"
        "Run `unset ANTHROPIC_API_KEY` and try again."
    )

if not os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
    sys.exit("CLAUDE_CODE_OAUTH_TOKEN is missing. Paste the token into .env first.")

# Step 3. Import the SDK *after* the guards. The SDK reads env vars
# during import to configure its subprocess, so we want the guards
# to run before anything from claude_agent_sdk loads.
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock


async def main() -> None:
    # Step 4. Configure the call.
    #
    # `allowed_tools=[]` disables every built-in tool. By default the
    # Agent SDK enables a Claude-Code-like toolset (Bash, Read, Write,
    # Glob, Grep, ...). For a hello-world we just want plain text.
    options = ClaudeAgentOptions(allowed_tools=[])

    # Step 5. Run the query.
    #
    # `query(prompt, options)` returns an async iterator. Under the
    # hood the SDK spawns the Claude Code binary as a subprocess and
    # pipes its newline-delimited JSON output back to us as typed
    # Python objects: AssistantMessage, ToolUseBlock, SystemMessage,
    # ResultMessage, etc.
    #
    # For this example we only care about assistant text.
    async for message in query(prompt="Say hello in one short sentence.", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


if __name__ == "__main__":
    # asyncio.run is required because query() is async — there's
    # always a subprocess in the loop that we have to await.
    asyncio.run(main())
