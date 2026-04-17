#!/usr/bin/env bash
# Graph of Skills — session start workspace health check.
# Runs non-blocking: prints a short status line to stderr so Claude can see it
# without blocking the session if anything goes sideways.

set -u

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

# Output JSON to stdout so SessionStart can pass it through as additional context.
# The JSON body is purely informational — Claude Code treats it as a system notice.

status_line=""

# Check .env exists
if [[ ! -f "$PLUGIN_ROOT/.env" ]]; then
  status_line="GoS plugin: .env missing — copy .env.example to .env and set an embedding API key, or run /gos-bootstrap"
else
  # Check at least one embedding provider key looks plausible
  if grep -qE '^(GEMINI_API_KEY|OPENAI_API_KEY|OPENROUTER_API_KEY)=.+' "$PLUGIN_ROOT/.env" 2>/dev/null; then
    # Try to find the configured workspace
    workspace_dir=$(grep -E '^GOS_WORKING_DIR=' "$PLUGIN_ROOT/.env" 2>/dev/null | tail -n1 | cut -d= -f2-)
    workspace_dir="${workspace_dir:-./gos_workspace}"

    # Check .mcp.json for the workspace the MCP server will actually use.
    # Parse with python3 to handle the JSON properly and substitute ${CLAUDE_PLUGIN_ROOT:-.} manually.
    mcp_workspace=""
    if [[ -f "$PLUGIN_ROOT/.mcp.json" ]]; then
      mcp_workspace=$(python3 -c '
import json, re, sys
try:
    with open(sys.argv[1]) as f:
        cfg = json.load(f)
    args = cfg.get("mcpServers", {}).get("graph-of-skills", {}).get("args", [])
    for i, a in enumerate(args):
        if a == "--workspace" and i + 1 < len(args):
            ws = args[i + 1]
            ws = ws.replace("${CLAUDE_PLUGIN_ROOT:-.}", sys.argv[2]).replace("${CLAUDE_PLUGIN_ROOT}", sys.argv[2])
            print(ws)
            break
except Exception:
    pass
' "$PLUGIN_ROOT/.mcp.json" "$PLUGIN_ROOT" 2>/dev/null)
    fi

    effective="${mcp_workspace:-$workspace_dir}"
    # Resolve relative to plugin root
    if [[ "$effective" != /* ]]; then
      effective="$PLUGIN_ROOT/$effective"
    fi

    if [[ -d "$effective" ]] && compgen -G "$effective/*" > /dev/null; then
      status_line="GoS plugin: ready. Workspace=$effective. Use /gos-status to verify skill/edge counts."
    else
      status_line="GoS plugin: workspace empty or missing at $effective. Run ./scripts/download_data.sh --workspace or /gos-index <path>."
    fi
  else
    status_line="GoS plugin: no embedding API key detected in .env. Set GEMINI_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY."
  fi
fi

# Emit as SessionStart JSON — sets additionalContext so Claude sees the notice.
python3 -c "import json,sys; print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': sys.argv[1]}}))" "$status_line"
