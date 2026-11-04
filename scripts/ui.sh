#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../ui"
exec npm run dev -- --hostname 127.0.0.1 --port 3000
