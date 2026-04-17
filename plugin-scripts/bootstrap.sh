#!/usr/bin/env bash
# Graph of Skills — bootstrap helper.
# Walks a user through first-time setup: dependencies, env, workspace.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$PLUGIN_ROOT"

echo "==> Graph of Skills bootstrap"
echo "Plugin root: $PLUGIN_ROOT"
echo

# 1. uv
if ! command -v uv >/dev/null 2>&1; then
  echo "[✗] uv not found. Install from https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi
echo "[✓] uv: $(uv --version)"

# 2. Python deps
if ! uv run python -c "import gos" >/dev/null 2>&1; then
  echo "[…] Installing graph-skills package via uv sync"
  uv sync
fi
echo "[✓] graph-skills package importable"

# 3. .env
if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    echo "[…] Copying .env.example to .env"
    cp .env.example .env
    echo "[!] .env created. Edit it and set GEMINI_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY."
  else
    echo "[✗] No .env.example found — cannot bootstrap."
    exit 1
  fi
else
  echo "[✓] .env present"
fi

# 4. Check API keys
if ! grep -qE '^(GEMINI_API_KEY|OPENAI_API_KEY|OPENROUTER_API_KEY)=.+' .env; then
  echo "[!] No embedding API key set in .env. Edit .env and set one before indexing or querying."
fi

# 5. Workspace
workspace=$(grep -oE '"--workspace",[[:space:]]*"[^"]+"' .mcp.json 2>/dev/null | head -n1 | sed -E 's/.*"([^"]+)"$/\1/' || true)
workspace="${workspace:-./gos_workspace}"

if [[ -d "$workspace" ]] && compgen -G "$workspace/*" > /dev/null; then
  echo "[✓] workspace present at $workspace"
else
  echo "[!] workspace at $workspace is empty or missing."
  echo "    Options:"
  echo "      - Download prebuilt: ./scripts/download_data.sh --workspace"
  echo "      - Build from source: uv run gos index <skill-library-path> --workspace $workspace --clear"
fi

echo
echo "==> Bootstrap complete. Next: run /gos-status from Claude Code to verify."
