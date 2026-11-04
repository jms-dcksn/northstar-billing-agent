#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv sync
if [[ ! -f .env ]]; then cp .env.example .env; fi
npm --prefix ui ci --ignore-scripts
echo "Setup complete. Add ANTHROPIC_API_KEY to .env, then run ./scripts/backend.sh and ./scripts/ui.sh."
