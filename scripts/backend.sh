#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec uv run langgraph dev --host 127.0.0.1 --port 2024 --no-browser --allow-blocking
