#!/usr/bin/env bash
# Re-render the local living doc from the ticket files and serve it at http://localhost:${PORT:-8765}/
set -euo pipefail
cd "$(dirname "$0")"
python3 -I .claude/living-doc/progress_page.py .scratch/<effort> .scratch/<effort>/living-doc.html
PORT="${PORT:-8765}"
(sleep 1 && open "http://localhost:$PORT/living-doc.html") &
exec python3 -m http.server "$PORT" --bind 127.0.0.1 --directory .scratch/<effort>
