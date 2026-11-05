#!/usr/bin/env bash
# Removes what install.sh added. Keeps anything you had first, ~/.claude/backups, and your projects.
# Usage: bash uninstall.sh [--yes]
set -euo pipefail

KIT="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CARGO_BIN="${CARGO_HOME:-$HOME/.cargo}/bin"
STATE="$CLAUDE_DIR/ai-welcome-kit"
SL="$CLAUDE_DIR/statusline/statusline.py"
ARENA_SKILL="$STATE/arena-skill/skills/arena"

if [ "${1:-}" != --yes ]; then
  [ -t 0 ] || { echo "Run this with --yes, or from a terminal."; exit 2; }
  read -r -p "Remove the AI Welcome Kit from ~/.claude? [y/N] " answer
  case "$answer" in y|Y|yes) ;; *) echo "Nothing changed."; exit 0 ;; esac
fi

for name in kit-living-doc kit-ticket-runbook; do
  dest="$CLAUDE_DIR/skills/$name"
  [ -e "$dest" ] || continue
  if diff -rq -x __pycache__ "$KIT/skills/$name" "$dest" >/dev/null 2>&1; then rm -rf "$dest"; echo "removed $name"
  else echo "kept $name: it differs from the kit's copy"; fi
done
if [ "$(readlink "$CLAUDE_DIR/skills/arena" 2>/dev/null)" = "$ARENA_SKILL" ] || [ -f "$CLAUDE_DIR/skills/arena/.kit-copy" ]; then
  rm -rf "$CLAUDE_DIR/skills/arena"; echo "removed arena"
fi

# Only what install.sh added: a plugin you already had isn't in this list
if [ -f "$STATE/added" ]; then
  [ -e "$CLAUDE_DIR/settings.json" ] && { b="$CLAUDE_DIR/backups/ai-welcome-kit-uninstall-$(date +%Y%m%d-%H%M%S)"; mkdir -p "$b"; cp -L "$CLAUDE_DIR/settings.json" "$b/"; echo "backed up settings.json -> $b"; }
  grep '^plugin ' "$STATE/added" | while read -r _ id; do
    claude plugin uninstall "$id" >/dev/null && echo "removed $id" || echo "couldn't remove $id - try: claude plugin uninstall $id"
  done
  grep '^marketplace ' "$STATE/added" | while read -r _ name; do
    claude plugin marketplace remove "$name" >/dev/null && echo "removed marketplace $name" || echo "couldn't remove marketplace $name"
  done
fi

# Windows often has python or py, not python3
if ! python3 -c 1 >/dev/null 2>&1; then
  for p in python py; do
    if "$p" -c 1 >/dev/null 2>&1; then eval "python3() { $p \"\$@\"; }"; break; fi
  done
fi
python3 - "$CLAUDE_DIR/settings.json" "$SL" <<'PY'
import json, os, sys
path, cmd = os.path.realpath(sys.argv[1]), sys.argv[2]
if os.path.exists(path):
    try:
        cur = json.load(open(path))
    except ValueError:
        sys.exit(print("left settings.json alone: it isn't valid JSON"))
    old = cur.get("statusLine")
    if isinstance(old, dict) and old.get("command") == cmd:
        del cur["statusLine"]
        with open(path + ".tmp", "w") as fh:
            os.chmod(path + ".tmp", os.stat(path).st_mode & 0o7777)
            json.dump(cur, fh, indent=2)
            fh.write("\n")
        os.replace(path + ".tmp", path)
        print("removed statusLine from settings.json. If the kit replaced yours, it's in ~/.claude/backups")
PY
rm -f "$SL"; rmdir "$(dirname "$SL")" 2>/dev/null || true

if [ -f "$STATE/system-tui" ]; then
  rm -f "$CARGO_BIN/system-tui" "$CARGO_BIN/monitor"; echo "removed system-tui"
fi
rm -rf "$STATE"

rc="$(grep -ls 'ai-welcome-kit: cargo bin' "${ZDOTDIR:-$HOME}/.zshrc" "$HOME/.bash_profile" "$HOME/.bash_login" "$HOME/.profile" "$HOME/.config/fish/config.fish" || true)"
[ -z "$rc" ] || echo "left the PATH line in $rc: delete the two lines under 'ai-welcome-kit: cargo bin' if you don't use Rust"
echo
echo "Done. Restart Claude Code. Still here: ~/.claude/backups, ~/.config/ponytail if ponytail ran, and this folder ($KIT)."
