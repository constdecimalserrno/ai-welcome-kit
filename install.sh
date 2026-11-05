#!/usr/bin/env bash
# Installs the AI Welcome Kit: three skills, three plugins, system-tui and the statusline.
# Safe to run twice - every step checks what's already there, and anything it
# replaces gets backed up to ~/.claude/backups/ai-welcome-kit-<timestamp>/ first.
#
# Mac, or Windows in Git Bash, where system-tui and the statusline are left out. To undo it: bash uninstall.sh
#
# Usage: bash install.sh [--code-dir DIR] [--skip LIST] [--force-skills] [--force-statusline]
#   --skip LIST      leave pieces out, comma separated: kit-living-doc, kit-ticket-runbook,
#                    arena, mattpocock-skills, frontend-design, ponytail, statusline,
#                    system-tui.
#   --force-skills   replace a skill you already have under ~/.claude/skills, after a
#                    backup. Without it, a skill that's a git repo or differs from ours is kept.
#   --force-statusline  replace a statusLine you already have, after a backup. Without it, yours stays.
#   --code-dir DIR   where you keep your code, for system-tui's disk-by-project panel.
#                    Relative to $HOME or absolute under it. Also read from $CODE_DIR.
#                    Default: the last folder you picked, else the first of ~/code,
#                    ~/src, ~/Projects, ~/Developer, ~/dev that holds more than this kit,
#                    else ~/code.
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
FORCE_STATUSLINE=0
SKIP=""
ADDED="$CLAUDE_DIR/ai-welcome-kit/added"  # what we added, so uninstall.sh leaves what you already had
# On a fresh HOME, step 3's plugin install creates settings.json - that's ours, not the user's, so no backup
[ -e "$CLAUDE_DIR/settings.json" ] && HAD_SETTINGS=1 || HAD_SETTINGS=0

while [ $# -gt 0 ]; do
  case "$1" in
    --code-dir) CODE_DIR="${2:?--code-dir needs a folder}"; shift 2 ;;
    --force-skills) FORCE_SKILLS=1; shift ;;
    --force-statusline) FORCE_STATUSLINE=1; shift ;;
    --skip) SKIP="${2:?--skip needs a list}"; shift 2 ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
done

for piece in $(echo "$SKIP" | tr ',' ' '); do
  case "$piece" in
    kit-living-doc|kit-ticket-runbook|arena|mattpocock-skills|frontend-design|ponytail|statusline|system-tui) ;;
    *) echo "unknown piece for --skip: $piece (try --help)" >&2; exit 2 ;;
  esac
done
skip() { case ",$SKIP," in *",$1,"*) return 0 ;; esac; return 1; }

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

# settings.json gets its one backup right before the first thing that changes it
snapshot_settings() {
  [ "$HAD_SETTINGS" = 1 ] || return 0
  HAD_SETTINGS=0
  backup "$CLAUDE_DIR/settings.json"
}
added() { mkdir -p "$(dirname "$ADDED")"; echo "$1" >>"$ADDED"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export PATH="$CARGO_BIN:$PATH"  # rustup puts cargo here; a fresh shell may not have it yet

# ----------------------- 1. PREREQUISITES -----------------------
say "1/6 prerequisites"
if [ "$(uname -s)" = Darwin ]; then FIX="run: xcode-select --install"
else
  FIX="get it from https://git-scm.com or https://www.python.org"
  SKIP="$SKIP,statusline,system-tui"
  warn "not a Mac - leaving out the statusline and system-tui, which are Mac only"
fi
# Windows often has python or py, not python3
if ! python3 -c 1 >/dev/null 2>&1; then
  for p in python py; do
    if "$p" -c 1 >/dev/null 2>&1; then eval "python3() { $p \"\$@\"; }"; break; fi
  done
fi
missing=0
# Run each tool, don't just find it: on a Mac without the Command Line Tools,
# /usr/bin/python3 and /usr/bin/git exist but only pop an install dialog.
command -v claude >/dev/null 2>&1 || {
  echo "    x claude not found - install Claude Code: https://claude.com/claude-code"; missing=1; }
python3 -c 1 >/dev/null 2>&1 || {
  echo "    x python doesn't run - $FIX"; missing=1; }
git --version >/dev/null 2>&1 || {
  echo "    x git doesn't run - $FIX"; missing=1; }
[ "$missing" = 0 ] || { echo "Install what's missing above, then run this again."; exit 1; }

# ponytail's hooks all run node. Without it they error on every prompt, so we don't install it.
NODE=1
if ! skip ponytail && ! node --version >/dev/null 2>&1; then
  warn "node not found - skipping ponytail, whose hooks need it. The Snake demo needs it too. get Node from https://nodejs.org, then run this again"; NODE=0
fi

TUI=1
if skip system-tui; then TUI=0
elif ! command -v cargo >/dev/null 2>&1; then
  warn "cargo not found - skipping system-tui. get Rust from https://rustup.rs, then run this again"; TUI=0
elif ! cargo --version >/dev/null 2>&1; then  # rustup with no default toolchain: cargo is there but won't run
  warn "cargo won't run - skipping system-tui. run: rustup default stable, then run this again"; TUI=0
fi

# ----------------------- 2. SKILLS -----------------------
say "2/6 skills -> $CLAUDE_DIR/skills"
mkdir -p "$CLAUDE_DIR/skills"
for name in kit-living-doc kit-ticket-runbook; do
  dest="$CLAUDE_DIR/skills/$name"
  if skip "$name"; then echo "    $name skipped"; continue; fi
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
if skip arena; then echo "    arena skipped"
elif [ -e "$dest" ] && [ "$(readlink "$dest")" != "$ARENA_SKILL" ] && [ ! -f "$dest/.kit-copy" ] && [ "$FORCE_SKILLS" != 1 ]; then
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
  elif [ -f "$dest/.kit-copy" ]; then  # a copy can't follow the clone, so refresh it
    rm -rf "$dest"; cp -R "$ARENA_SKILL" "$dest"; touch "$dest/.kit-copy"
    echo "    arena already installed"
  else
    if [ -e "$dest" ]; then backup "$dest"; fi
    rm -rf "$dest"  # also clears a dangling link
    ln -s "$ARENA_SKILL" "$dest" 2>/dev/null || cp -R "$ARENA_SKILL" "$dest"
    [ -L "$dest" ] || touch "$dest/.kit-copy"  # Git Bash copies instead of linking
    echo "    installed arena ($ARENA_REPO)"
  fi
fi

# ----------------------- 3. PLUGINS -----------------------
say "3/6 plugins (mattpocock-skills, frontend-design, ponytail)"
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
wanted() {  # wanted <plugin>: not skipped, and for ponytail, Node is here
  skip "$1" && return 1
  [ "$1" != ponytail ] || [ "$NODE" = 1 ]
}
for row in "mattpocock-skills claude-plugins-official anthropics/claude-plugins-official" "frontend-design claude-plugins-official anthropics/claude-plugins-official" "ponytail ponytail DietrichGebert/ponytail"; do
  set -- $row
  wanted "$1" || continue
  if has marketplace "$2"; then case "${seen:-}" in *" $2 "*) ;; *) echo "    marketplace $2 already added" ;; esac; continue; fi
  seen="${seen:-} $2 "
  snapshot_settings
  if claude plugin marketplace add "$3" >/dev/null; then echo "    added marketplace $2 ($3)"; added "marketplace $2"
  else fail "couldn't add marketplace $3"; fi
done
for id in mattpocock-skills@claude-plugins-official frontend-design@claude-plugins-official ponytail@ponytail; do
  if ! wanted "${id%@*}"; then echo "    ${id%@*} skipped"; continue; fi
  if has enabled "$id"; then echo "    $id already installed"; continue; fi
  snapshot_settings
  if has plugin "$id"; then
    if claude plugin enable "$id" >/dev/null; then echo "    $id was disabled - enabled it"
    else fail "couldn't enable $id - try: claude plugin enable $id"; fi
  elif claude plugin install "$id" --scope user >/dev/null; then echo "    installed $id"; added "plugin $id"
  else fail "couldn't install $id - try: claude plugin install $id"; fi
done

# ----------------------- 4. STATUSLINE -----------------------
# The cheap steps go before the slow Rust build, so a killed build can't leave them undone.
say "4/6 statusline -> $CLAUDE_DIR/statusline/statusline.py"
SRC="$TMP/system-tui"
if skip statusline && [ "$TUI" = 0 ]; then SRC=""
elif ! git clone -q --depth 1 "$REPO" "$SRC" 2>/dev/null && ! git clone -q "$REPO" "$SRC"; then
  fail "couldn't clone $REPO - skipping the statusline and system-tui"; TUI=0; SRC=""
fi
SL="$CLAUDE_DIR/statusline/statusline.py"
if skip statusline; then echo "    skipped"
elif [ -n "$SRC" ]; then
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
STATUS_KEPT=0
if skip statusline; then echo "    skipped"
elif [ -f "$SL" ]; then
  mkdir -p "$CLAUDE_DIR"
  # python3 prints "same", "changed", "theirs" or "bad: <why>"; it never writes - we back up first, then it writes
  state="$(python3 - "$CLAUDE_DIR/settings.json" "$SL" "$FORCE_STATUSLINE" <<'PY'
import json, os, sys
path, cmd, force = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
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
old = cur.get("statusLine")
if old == want:
    print("same")
elif old and not force and not (isinstance(old, dict) and old.get("command") == cmd):
    print("theirs")
else:
    print("changed")
PY
)" || true
  case "$state" in
    same|changed|theirs) ;;
    *) fail "settings.json left alone - ${state#bad: }. Fix it, then run this again"; state=bad ;;
  esac
  if [ "$state" = same ]; then
    echo "    already wired"
  elif [ "$state" = theirs ]; then
    STATUS_KEPT=1
    echo "    [--] existing statusLine kept. system-tui's usage panel needs ours: rerun with --force-statusline to replace yours, after a backup"
  elif [ "$state" = changed ]; then
    snapshot_settings
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
    # the kit's own clone creates ~/src, so a folder holding only the kit doesn't count
    for f in code src Projects Developer dev; do
      if [ -d "$HOME/$f" ] && [ "$(ls -A "$HOME/$f" | grep -vx .DS_Store)" != ai-welcome-kit ]; then guess="$f"; break; fi
    done
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
dash() { echo "  [--] $1"; }
# A skill you kept isn't the kit's, so it doesn't earn an [ok]
check_skill() {  # check_skill <name> <is it the kit's?>
  if skip "$1"; then dash "skill $1 skipped"
  elif [ -e "$CLAUDE_DIR/skills/$1" ] && ! eval "$2" >/dev/null 2>&1; then dash "skill $1 is yours, not the kit's"
  else check "skill $1" "$2"; fi
}
check_skill kit-living-doc     "diff -rq -x __pycache__ '$KIT/skills/kit-living-doc' '$CLAUDE_DIR/skills/kit-living-doc'"
check_skill kit-ticket-runbook "diff -rq -x __pycache__ '$KIT/skills/kit-ticket-runbook' '$CLAUDE_DIR/skills/kit-ticket-runbook'"
check_skill arena              "{ [ \"\$(readlink '$CLAUDE_DIR/skills/arena')\" = '$ARENA_SKILL' ] || [ -f '$CLAUDE_DIR/skills/arena/.kit-copy' ]; } && [ -f '$ARENA_SKILL/SKILL.md' ]"
if skip mattpocock-skills; then dash "plugin mattpocock-skills skipped"
else check "plugin mattpocock-skills" "has enabled mattpocock-skills@claude-plugins-official"; fi
if skip frontend-design; then dash "plugin frontend-design skipped"
else check "plugin frontend-design" "has enabled frontend-design@claude-plugins-official"; fi
if skip ponytail; then dash "plugin ponytail skipped"
elif [ "$NODE" = 0 ]; then dash "plugin ponytail skipped: needs Node"
else check "plugin ponytail" "has enabled ponytail@ponytail"; fi
if skip statusline; then dash "statusline skipped"
else
  check "statusline runs" "echo '{}' | '$SL' | grep -q ."
  if [ "$STATUS_KEPT" = 1 ]; then dash "settings.json statusLine is yours, not the kit's"
  else check "settings.json statusLine" "python3 -c 'import json,sys; s=json.load(open(sys.argv[1]))[\"statusLine\"]; assert s[\"command\"]==sys.argv[2] and s[\"refreshInterval\"]==10' '$CLAUDE_DIR/settings.json' '$SL'"; fi
fi
if [ "$TUI" = 1 ] && [ -z "$RC" ]; then
  check "system-tui built (add $CARGO_BIN to PATH yourself)" "[ -x '$CARGO_BIN/system-tui' ]"
elif [ "$TUI" = 1 ]; then
  check "system-tui in a new shell" "new_shell_finds"
else
  dash "system-tui skipped"
fi
echo
if [ "$FAILS" = 0 ]; then
  echo "Done. Restart Claude Code so it loads what was installed."
else
  echo "Done with $FAILS problem(s) above. Fix them and run this again - it's safe to rerun."
  exit 1
fi
