"""Example 2 — diagnostic. Which credential will the Agent SDK actually use?

Goal: tell you, before you make any API calls, which auth method
      will win precedence — and warn loudly if your OAuth token is
      being silently shadowed by something else.
Run:  python check_auth.py

This script doesn't call the SDK at all. It just inspects environment
variables and applies the documented precedence rules. Run it any
time something feels off (rate-limit errors, unexpected billing,
"why does it work in the CLI but not from my script", ...).

Reference: https://docs.claude.com/en/docs/claude-code/iam
"""

import os

from dotenv import load_dotenv

# Load .env first so CLAUDE_CODE_OAUTH_TOKEN shows up below if it's
# only set in .env (not the shell).
load_dotenv()


def mask(value: str) -> str:
    """Show enough of a token to recognize it without leaking the secret part.

    `sk-ant-oat01-XYZ...ABC` becomes `sk-ant-oat…XYZA` — useful for
    confirming "yes that's the right token" without copy-paste risk.
    """
    if len(value) <= 12:
        return "***"
    return f"{value[:10]}…{value[-4:]}"


def main() -> None:
    # Snapshot every auth-relevant env var the Agent SDK / Claude Code
    # might consult. The full list and order is documented in the
    # Claude Code IAM docs (linked at the top).
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    oauth = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    bedrock = os.environ.get("CLAUDE_CODE_USE_BEDROCK")
    vertex = os.environ.get("CLAUDE_CODE_USE_VERTEX")
    foundry = os.environ.get("CLAUDE_CODE_USE_FOUNDRY")

    print("Detected env vars:")
    print(f"  ANTHROPIC_API_KEY        = {mask(api_key) if api_key else '(unset)'}")
    print(f"  ANTHROPIC_AUTH_TOKEN     = {mask(auth_token) if auth_token else '(unset)'}")
    print(f"  CLAUDE_CODE_OAUTH_TOKEN  = {mask(oauth) if oauth else '(unset)'}")
    print(f"  CLAUDE_CODE_USE_BEDROCK  = {bedrock or '(unset)'}")
    print(f"  CLAUDE_CODE_USE_VERTEX   = {vertex or '(unset)'}")
    print(f"  CLAUDE_CODE_USE_FOUNDRY  = {foundry or '(unset)'}")

    # Apply the documented precedence rules to figure out which
    # method "wins". Order matters — first match decides.
    #
    # 1. Cloud providers (Bedrock / Vertex / Foundry) — for enterprise
    #    deployments where Claude is hosted on a hyperscaler.
    # 2. ANTHROPIC_AUTH_TOKEN — bearer token, billed per token.
    # 3. ANTHROPIC_API_KEY    — Console API key, billed per token.
    # 4. apiKeyHelper         — a configured helper script. Can't be
    #                           detected from env vars alone, so we
    #                           skip it here.
    # 5. CLAUDE_CODE_OAUTH_TOKEN — Pro/Max subscription. ← what we want.
    # 6. Interactive /login session — falls back to whatever the CLI
    #                                 cached during a prior `claude` run.
    if bedrock or vertex or foundry:
        winner = "Cloud provider credentials"
    elif auth_token:
        winner = "ANTHROPIC_AUTH_TOKEN (bearer, billed per-token)"
    elif api_key:
        winner = "ANTHROPIC_API_KEY (Console key, billed per-token)"
    elif oauth:
        winner = "CLAUDE_CODE_OAUTH_TOKEN (Pro/Max subscription)"
    else:
        winner = "interactive /login session, if any (else unauthenticated)"

    print(f"\nActive method per docs precedence: {winner}")

    # The most common failure mode: someone has both ANTHROPIC_API_KEY
    # and CLAUDE_CODE_OAUTH_TOKEN set, expects the OAuth token to win,
    # and is surprised when their API account gets billed.
    if api_key and oauth:
        print("⚠ ANTHROPIC_API_KEY is shadowing your OAuth token. Run `unset ANTHROPIC_API_KEY`.")


if __name__ == "__main__":
    main()
