/**
 * Example 2 — diagnostic. Which credential will the Agent SDK actually use?
 *
 * Goal: tell you, before you make any API calls, which auth method
 *       will win precedence — and warn loudly if your OAuth token is
 *       being silently shadowed by something else.
 * Run:  npm run check-auth
 *
 * This script doesn't call the SDK at all. It just inspects environment
 * variables and applies the documented precedence rules. Run it any
 * time something feels off (rate-limit errors, unexpected billing,
 * "why does it work in the CLI but not from my script", ...).
 *
 * Reference: https://docs.claude.com/en/docs/claude-code/iam
 */

import "dotenv/config";

/**
 * Show enough of a token to recognize it without leaking the secret part.
 * `sk-ant-oat01-XYZ...ABC` becomes `sk-ant-oat…XYZA` — useful for
 * confirming "yes that's the right token" without copy-paste risk.
 */
function mask(value: string | undefined): string {
  if (!value) return "(unset)";
  if (value.length <= 12) return "***";
  return `${value.slice(0, 10)}…${value.slice(-4)}`;
}

// Snapshot every auth-relevant env var the Agent SDK / Claude Code
// might consult. The full list and order is documented in the
// Claude Code IAM docs (linked at the top).
const apiKey = process.env.ANTHROPIC_API_KEY;
const authToken = process.env.ANTHROPIC_AUTH_TOKEN;
const oauth = process.env.CLAUDE_CODE_OAUTH_TOKEN;
const bedrock = process.env.CLAUDE_CODE_USE_BEDROCK;
const vertex = process.env.CLAUDE_CODE_USE_VERTEX;
const foundry = process.env.CLAUDE_CODE_USE_FOUNDRY;

console.log("Detected env vars:");
console.log(`  ANTHROPIC_API_KEY        = ${mask(apiKey)}`);
console.log(`  ANTHROPIC_AUTH_TOKEN     = ${mask(authToken)}`);
console.log(`  CLAUDE_CODE_OAUTH_TOKEN  = ${mask(oauth)}`);
console.log(`  CLAUDE_CODE_USE_BEDROCK  = ${bedrock ?? "(unset)"}`);
console.log(`  CLAUDE_CODE_USE_VERTEX   = ${vertex ?? "(unset)"}`);
console.log(`  CLAUDE_CODE_USE_FOUNDRY  = ${foundry ?? "(unset)"}`);

// Apply the documented precedence rules to figure out which method
// "wins". Order matters — first match decides.
//
// 1. Cloud providers (Bedrock / Vertex / Foundry) — for enterprise
//    deployments where Claude is hosted on a hyperscaler.
// 2. ANTHROPIC_AUTH_TOKEN — bearer token, billed per token.
// 3. ANTHROPIC_API_KEY    — Console API key, billed per token.
// 4. apiKeyHelper         — a configured helper script. Can't be
//                           detected from env vars alone, so we
//                           skip it here.
// 5. CLAUDE_CODE_OAUTH_TOKEN — Pro/Max subscription. ← what we want.
// 6. Interactive /login session — falls back to whatever the CLI
//                                 cached during a prior `claude` run.
let winner: string;
if (bedrock || vertex || foundry) winner = "Cloud provider credentials";
else if (authToken) winner = "ANTHROPIC_AUTH_TOKEN (bearer, billed per-token)";
else if (apiKey) winner = "ANTHROPIC_API_KEY (Console key, billed per-token)";
else if (oauth) winner = "CLAUDE_CODE_OAUTH_TOKEN (Pro/Max subscription)";
else winner = "interactive /login session, if any (else unauthenticated)";

console.log(`\nActive method per docs precedence: ${winner}`);

// The most common failure mode: someone has both ANTHROPIC_API_KEY
// and CLAUDE_CODE_OAUTH_TOKEN set, expects the OAuth token to win,
// and is surprised when their API account gets billed.
if (apiKey && oauth) {
  console.log("⚠ ANTHROPIC_API_KEY is shadowing your OAuth token. Run `unset ANTHROPIC_API_KEY`.");
}
