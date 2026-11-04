#!/usr/bin/env bash
# Installs the AI Welcome Kit: three skills, two plugins, system-tui and the statusline.
# Safe to run twice - every step checks what's already there, and anything it
# replaces gets backed up to ~/.claude/backups/ai-welcome-kit-<timestamp>/ first.
#
# Usage: ./install.sh [--code-dir DIR] [--force-skills]
#   --force-skills   replace a skill you already have under ~/.claude/skills, after a
#                    backup. Without it, a skill that's a git repo or differs from ours is kept.
#   --code-dir DIR   where you keep your code, for system-tui's disk-by-project panel.
#                    Relative to $HOME or absolute under it. Also read from $CODE_DIR.
#                    Default: the last folder you picked, else the first of ~/code,
#                    ~/src, ~/Projects, ~/Developer, ~/dev that exists, else ~/code.
#                    Asked for when run from a terminal.
#   $SYSTEM_TUI_REPO overrides the system-tui git source (a fork, or a local path).
#   $ARENA_REPO      overrides the arena skill's git source, the same way.
set -euo pipefail

KIT="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
CARGO_BIN="${CARGO_HOME:-$HOME/.cargo}/bin"
REPO="${SYSTEM_TUI_REPO:-https://github.com/constdecimals9/system-tui.git}"
ARENA_REPO="${ARENA_REPO:-https://github.com/Jakeschincariol/arena-skill.git}"
TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$CLAUDE_DIR/backups/ai-welcome-kit-$TS"
CODE_DIR="${CODE_DIR:-}"
FAILS=0
FORCE_SKILLS=0
# On a fresh HOME, step 3's plugin install creates settings.json - that's ours, not the user's, so no backup
[ -e "$CLAUDE_DIR/settings.json" ] && HAD_SETTINGS=1 || HAD_SETTINGS=0

while [ $# -gt 0 ]; do
  case "$1" in
    --code-dir) CODE_DIR="${2:?--code-dir needs a folder}"; shift 2 ;;
    --force-skills) FORCE_SKILLS=1; shift ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
done

say()  { echo "==> $*"; }
warn() { echo "    ! $*"; }
fail() { echo "    x $*"; FAILS=$((FAILS + 1)); }

# Move something we're about to replace into the backup folder, keeping its path
# under ~/.claude - backups never sit inside ~/.claude/skills, or they'd load as skills.
backup() {
  local rel="${1#"$CLAUDE_DIR"/}"
  mkdir -p "$BACKUP/$(dirname "$rel")"
  cp -RL "$1" "$BACKUP/$rel"  # -L: back up what a symlink points at, not the link
  echo "    backed up $1 -> $BACKUP/$rel"
}

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export PATH="$CARGO_BIN:$PATH"  # rustup puts cargo here; a fresh shell may not have it yet

# ----------------------- 1. PREREQUISITES -----------------------
say "1/6 prerequisites"
missing=0
# Run each tool, don't just find it: on a Mac without the Command Line Tools,
# /usr/bin/python3 and /usr/bin/git exist but only pop an install dialog.
command -v claude >/dev/null 2>&1 || {
  echo "    x claude not found - install Claude Code: https://claude.com/claude-code"; missing=1; }
python3 -c 1 >/dev/null 2>&1 || {
  echo "    x python3 doesn't run - run: xcode-select --install"; missing=1; }
git --version >/dev/null 2>&1 || {
  echo "    x git doesn't run - run: xcode-select --install"; missing=1; }
[ "$missing" = 0 ] || { echo "Install what's missing above, then run this again."; exit 1; }

TUI=1
if [ "$(uname -s)" != "Darwin" ]; then
  warn "not macOS - skipping system-tui (it needs caffeinate and nettop)"; TUI=0
elif ! command -v cargo >/dev/null 2>&1; then
  warn "cargo not found - skipping system-tui. get Rust from https://rustup.rs, then run this again"; TUI=0
elif ! cargo --version >/dev/null 2>&1; then  # rustup with no default toolchain: cargo is there but won't run
  warn "cargo won't run - skipping system-tui. run: rustup default stable, then run this again"; TUI=0
fi

# ----------------------- 2. SKILLS -----------------------
say "2/6 skills -> $CLAUDE_DIR/skills"
mkdir -p "$CLAUDE_DIR/skills"
for name in living-doc ticket-runbook; do
  dest="$CLAUDE_DIR/skills/$name"
  if [ -d "$dest" ] && diff -rq -x __pycache__ "$KIT/skills/$name" "$dest" >/dev/null 2>&1; then
    echo "    $name already installed"; continue
  fi
  # Someone else's skill by the same name could be their own work - we never replace it silently
  if [ -e "$dest" ] && [ "$FORCE_SKILLS" != 1 ]; then
    if [ -e "$dest/.git" ]; then why="it's a git repo"; else why="it differs from the kit's copy"; fi
    echo "    [--] existing $name kept ($why). rerun with --force-skills to replace it, after a backup"
    continue
  fi
  if [ -e "$dest" ]; then backup "$dest"; rm -rf "$dest"; fi
  cp -R "$KIT/skills/$name" "$dest"
  echo "    installed $name"
done

# arena is Jake Schincariol's skill, from its own repo. Its SKILL.md sits in skills/arena/ of
# that repo, so we keep the clone beside the skills and link the skill folder in - a rerun is a pull.
ARENA_CLONE="$CLAUDE_DIR/ai-welcome-kit/arena-skill"
ARENA_SKILL="$ARENA_CLONE/skills/arena"
dest="$CLAUDE_DIR/skills/arena"
if [ -e "$dest" ] && [ "$(readlink "$dest")" != "$ARENA_SKILL" ] && [ "$FORCE_SKILLS" != 1 ]; then
  if [ -e "$dest/.git" ]; then why="it's a git repo"; else why="it isn't the kit's clone"; fi
  echo "    [--] existing arena kept ($why). rerun with --force-skills to replace it, after a backup"
else
  if [ "$(git -C "$ARENA_CLONE" remote get-url origin 2>/dev/null)" = "$ARENA_REPO" ]; then
    old="$(git -C "$ARENA_CLONE" rev-parse HEAD)"
    git -C "$ARENA_CLONE" pull -q --ff-only 2>/dev/null || warn "couldn't update arena - keeping the copy you have"
  else
    old=""
    rm -rf "$ARENA_CLONE"; mkdir -p "$(dirname "$ARENA_CLONE")"  # kit-owned, never the user's own work
    git clone -q "$ARENA_REPO" "$ARENA_CLONE" 2>/dev/null || fail "couldn't clone $ARENA_REPO - skipping arena"
  fi
  if [ ! -f "$ARENA_SKILL/SKILL.md" ]; then
    if [ -d "$ARENA_CLONE" ]; then fail "arena's repo has no skills/arena/SKILL.md - skipping it"; fi
  elif [ "$(readlink "$dest")" = "$ARENA_SKILL" ]; then
    if [ "$old" = "$(git -C "$ARENA_CLONE" rev-parse HEAD)" ]; then echo "    arena already installed"
    else echo "    updated arena"; fi
  else
    if [ -e "$dest" ]; then backup "$dest"; fi
    rm -rf "$dest"  # also clears a dangling link
    ln -s "$ARENA_SKILL" "$dest"
    echo "    installed arena ($ARENA_REPO)"
  fi
fi

# ----------------------- 3. PLUGINS -----------------------
say "3/6 plugins (mattpocock-skills, ponytail)"
has() {  # has <marketplace|plugin|enabled> <name or id> - reads the CLI's own JSON listing
  local list
  if [ "$1" = marketplace ]; then list="$(claude plugin marketplace list --json 2>/dev/null)" || return 1
  else list="$(claude plugin list --json 2>/dev/null)" || return 1; fi
  printf '%s' "$list" | python3 -c '
import json, sys
want, on = sys.argv[1], sys.argv[2] == "enabled"
try:
    rows = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
# "enabled": a plugin someone disabled is installed but never loads
sys.exit(0 if any(want in (r.get("name"), r.get("id")) and (not on or r.get("enabled", True))
                  for r in rows) else 1)' "$2" "$1"
}
for pair in "claude-plugins-official anthropics/claude-plugins-official" "ponytail DietrichGebert/ponytail"; do
  set -- $pair
  if has marketplace "$1"; then echo "    marketplace $1 already added"
  elif claude plugin marketplace add "$2" >/dev/null; then echo "    added marketplace $1 ($2)"
  else fail "couldn't add marketplace $2"; fi
done
for id in mattpocock-skills@claude-plugins-official ponytail@ponytail; do
  if has enabled "$id"; then echo "    $id already installed"
  elif has plugin "$id"; then
    if claude plugin enable "$id" >/dev/null; then echo "    $id was disabled - enabled it"
    else fail "couldn't enable $id - try: claude plugin enable $id"; fi
  elif claude plugin install "$id" --scope user >/dev/null; then echo "    installed $id"
  else fail "couldn't install $id - try: claude plugin install $id"; fi
done

# ----------------------- 4. STATUSLINE -----------------------
# The cheap steps go before the slow Rust build, so a killed build can't leave them undone.
say "4/6 statusline -> $CLAUDE_DIR/statusline/statusline.py"
SRC="$TMP/system-tui"
if ! git clone -q --depth 1 "$REPO" "$SRC" 2>/dev/null && ! git clone -q "$REPO" "$SRC"; then
  fail "couldn't clone $REPO - skipping the statusline and system-tui"; TUI=0; SRC=""
fi
SL="$CLAUDE_DIR/statusline/statusline.py"
if [ -n "$SRC" ]; then
  mkdir -p "$CLAUDE_DIR/statusline"
  if [ -f "$SL" ] && cmp -s "$SRC/statusline/statusline.py" "$SL"; then
    echo "    already installed"
  else
    [ -f "$SL" ] && backup "$SL"
    cp "$SRC/statusline/statusline.py" "$SL"
    echo "    installed"
  fi
  chmod +x "$SL"
fi

# ----------------------- 5. SETTINGS -----------------------
say "5/6 settings.json statusLine"
if [ -f "$SL" ]; then
  mkdir -p "$CLAUDE_DIR"
  # python3 prints "same", "changed" or "bad: <why>"; it never writes - we back up first, then it writes
  state="$(python3 - "$CLAUDE_DIR/settings.json" "$SL" <<'PY'
import json, os, sys
path, cmd = sys.argv[1], sys.argv[2]
try:
    text = open(path).read() if os.path.exists(path) else ""
    cur = json.loads(text) if text.strip() else {}  # an empty file has no keys to keep
except ValueError as e:
    sys.exit(print("bad: it isn't valid JSON (%s)" % e))
except OSError as e:
    sys.exit(print("bad: can't read it (%s)" % e.strerror))
if not isinstance(cur, dict):
    sys.exit(print("bad: it holds a JSON %s, not an object {...}" % type(cur).__name__))
want = {"type": "command", "command": cmd, "refreshInterval": 10}
print("same" if cur.get("statusLine") == want else "changed")
PY
)" || true
  case "$state" in
    same|changed) ;;
    *) fail "settings.json left alone - ${state#bad: }. Fix it, then run this again"; state=bad ;;
  esac
  if [ "$state" = same ]; then
    echo "    already wired"
  elif [ "$state" = changed ]; then
    [ "$HAD_SETTINGS" = 1 ] && backup "$CLAUDE_DIR/settings.json"
    python3 - "$CLAUDE_DIR/settings.json" "$SL" <<'PY'
import json, os, sys
path, cmd = os.path.realpath(sys.argv[1]), sys.argv[2]  # write through a symlink, never over it
text = open(path).read() if os.path.exists(path) else ""
cur = json.loads(text) if text.strip() else {}
old = cur.get("statusLine")
if old:
    print("    replaced the old statusLine (it's in the backup): " + json.dumps(old))
cur["statusLine"] = {"type": "command", "command": cmd, "refreshInterval": 10}
with open(path + ".tmp", "w") as fh:
    if os.path.exists(path):  # keep a private 0600 file private, before any data lands
        os.chmod(path + ".tmp", os.stat(path).st_mode & 0o7777)
    json.dump(cur, fh, indent=2)
    fh.write("\n")
os.replace(path + ".tmp", path)
PY
    echo "    merged statusLine, every other key kept"
  fi
else
  warn "no statusline installed, so settings.json was left alone"
fi

# ----------------------- 6. SYSTEM-TUI -----------------------
say "6/6 system-tui"
# Remembers the last build (line 1: code folder, line 2: commit), so a plain rerun
# keeps the folder you picked and skips a rebuild that would change nothing.
STAMP="$CLAUDE_DIR/ai-welcome-kit/system-tui"
SAVED_DIR="$(sed -n 1p "$STAMP" 2>/dev/null || true)"
SAVED_REV="$(sed -n 2p "$STAMP" 2>/dev/null || true)"
if [ "$TUI" = 1 ]; then
  guess="$SAVED_DIR"
  if [ -z "$guess" ]; then  # first run: the first common code folder that exists
    guess=code
    for f in code src Projects Developer dev; do [ -d "$HOME/$f" ] && { guess="$f"; break; }; done
  fi
  if [ -z "$CODE_DIR" ] && [ -t 0 ]; then
    read -r -p "    Where do you keep your code? (relative to ~, default: $guess) " CODE_DIR || true
  fi
  CODE_DIR="${CODE_DIR:-$guess}"
  # main.rs scans $HOME/<this>, so boil ~/x, $HOME/x and an absolute path under $HOME down to x
  d="${CODE_DIR%/}"; d="${d#\~/}"; d="${d#\$HOME/}"; d="${d#"$HOME"/}"
  case "$d" in "~"|'$HOME'|"$HOME") d="" ;; esac
  case "/$d/" in
    //|/\~*|*'$'*|//*|*/../*|*/./*|*'"'*|*\\*)
      # the panel only scans under $HOME; a bad answer shouldn't cost the whole dashboard
      warn "--code-dir must be a folder inside $HOME (got: $CODE_DIR) - using ~/$guess. rerun with --code-dir to change it"
      CODE_DIR="$guess" ;;
    *) CODE_DIR="$d" ;;
  esac
  [ -d "$HOME/$CODE_DIR" ] || warn "~/$CODE_DIR doesn't exist yet - the disk panel stays empty until it does. rerun with --code-dir to change it"
  REV="$(git -C "$SRC" rev-parse HEAD)"
  if [ "$CODE_DIR" = "$SAVED_DIR" ] && [ "$REV" = "$SAVED_REV" ] && [ -x "$CARGO_BIN/monitor" ]; then
    ln -sf "$CARGO_BIN/monitor" "$CARGO_BIN/system-tui"
    echo "    already built for ~/$CODE_DIR"
  else
    # main.rs hardcodes the scanned folder - we point it at the user's code in the temp clone only
    python3 - "$SRC/src/main.rs" "$CODE_DIR" <<'PY'
import re, sys
path, code = sys.argv[1], sys.argv[2]
s = open(path).read()
s, n = re.subn(r'const PROJECT_ROOT: &str = "[^"]*";', 'const PROJECT_ROOT: &str = "%s";' % code, s)
s = re.sub(r'DISK BY PROJECT  \(~/[^)]*\)', 'DISK BY PROJECT  (~/%s)' % code, s)
open(path, "w").write(s)
if n != 1:
    print("    ! PROJECT_ROOT not found in main.rs - the project panel keeps its default folder")
PY
    echo "    building from a fresh clone, project folder ~/$CODE_DIR (takes a few minutes)"
    if cargo install --quiet --locked --path "$SRC" >"$TMP/cargo.log" 2>&1; then
      ln -sf "$CARGO_BIN/monitor" "$CARGO_BIN/system-tui"
      mkdir -p "$(dirname "$STAMP")"; printf '%s\n%s\n' "$CODE_DIR" "$REV" >"$STAMP"
      echo "    installed $CARGO_BIN/system-tui -> monitor"
    else
      # the dashboard is optional, so a failed build is a skip, not a failure
      tail -n 20 "$TMP/cargo.log"; warn "cargo install failed (log above) - skipping system-tui. try: rustup default stable, then run this again"; TUI=0
    fi
  fi
fi
[ "$TUI" = 1 ] || echo "    skipped"

# A brand-new login shell is the honest test: does `system-tui` resolve there?
new_shell_finds() {
  env -i HOME="$HOME" USER="${USER:-}" TERM=dumb SHELL="${SHELL:-/bin/zsh}" \
    "${SHELL:-/bin/zsh}" -lic 'command -v system-tui' </dev/null 2>/dev/null | grep -q system-tui
}
# bash reads only the first of these that exists, so append to that one -
# creating ~/.bash_profile would hide an existing ~/.profile.
case "$(basename "${SHELL:-/bin/zsh}")" in
  zsh)  # zsh reads $ZDOTDIR/.zshrc when ~/.zshenv sets ZDOTDIR, not ~/.zshrc
        zd="$(env -i HOME="$HOME" zsh -c 'printf %s "${ZDOTDIR:-$HOME}"' 2>/dev/null || true)"
        RC="${zd:-$HOME}/.zshrc" ;;
  bash) RC="$HOME/.profile"
        for f in .bash_profile .bash_login .profile; do
          [ -f "$HOME/$f" ] && { RC="$HOME/$f"; break; }
        done ;;
  fish) RC="$HOME/.config/fish/config.fish" ;;
  *)    RC="" ;;  # a shell we don't know; we won't guess at its rc file
esac
if [ "$TUI" = 1 ] && ! new_shell_finds; then
  if [ -z "$RC" ]; then
    warn "don't know $(basename "${SHELL:-}")'s rc file - add $CARGO_BIN to your PATH yourself"
  elif ! grep -qs "ai-welcome-kit: cargo bin" "$RC"; then
    case "$RC" in
      *.fish) mkdir -p "$(dirname "$RC")"; line="set -gx PATH \"$CARGO_BIN\" \$PATH" ;;
      *)      line="export PATH=\"$CARGO_BIN:\$PATH\"" ;;
    esac
    printf '\n# ai-welcome-kit: cargo bin on PATH, for system-tui\n%s\n' "$line" >>"$RC"
    echo "    added $CARGO_BIN to PATH in $RC - open a new terminal to pick it up"
  fi
fi

# ----------------------- VERIFY -----------------------
echo
echo "Verify:"
check() { if eval "$2" >/dev/null 2>&1; then echo "  [ok] $1"; else echo "  [  ] $1"; FAILS=$((FAILS + 1)); fi; }
check "skill living-doc"           "[ -f '$CLAUDE_DIR/skills/living-doc/SKILL.md' ]"
check "skill ticket-runbook"       "[ -f '$CLAUDE_DIR/skills/ticket-runbook/SKILL.md' ]"
check "skill arena"                "[ -f '$CLAUDE_DIR/skills/arena/SKILL.md' ]"
check "plugin mattpocock-skills"   "has enabled mattpocock-skills@claude-plugins-official"
check "plugin ponytail"            "has enabled ponytail@ponytail"
check "statusline runs"            "echo '{}' | '$SL' | grep -q ."
check "settings.json statusLine"   "python3 -c 'import json,sys; s=json.load(open(sys.argv[1]))[\"statusLine\"]; assert s[\"command\"]==sys.argv[2] and s[\"refreshInterval\"]==10' '$CLAUDE_DIR/settings.json' '$SL'"
if [ "$TUI" = 1 ] && [ -z "$RC" ]; then
  check "system-tui built (add $CARGO_BIN to PATH yourself)" "[ -x '$CARGO_BIN/system-tui' ]"
elif [ "$TUI" = 1 ]; then
  check "system-tui in a new shell" "new_shell_finds"
else
  echo "  [--] system-tui skipped (see warnings above)"
fi
echo
if [ "$FAILS" = 0 ]; then
  echo "Done. Restart Claude Code so it loads the new skills, plugins and statusline."
else
  echo "Done with $FAILS problem(s) above. Fix them and run this again - it's safe to rerun."
  exit 1
fi
