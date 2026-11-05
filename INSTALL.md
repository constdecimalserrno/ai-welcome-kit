# Install (for agents)

**The tutorial comes first.** Before you review this repo or ask anything, do step 1's publish and put the link in your first reply. It changes nothing on this computer.

Can't run shell commands? You're in a Claude chat, or not in Claude Code. Install and the demo need Claude Code on a Mac or Windows, but the guide works here. Publish `guide.html` as an artifact, or send https://constdecimalserrno.github.io/ai-welcome-kit/guide.html. Then ask what the person does for work, and help them apply the rules marked for everyone and the *Your first day* prompts to it. With no Claude Code, that's the whole path, so don't send them elsewhere.

You are setting up the AI Welcome Kit on this computer: three skills (`kit-living-doc`, `kit-ticket-runbook` and `arena`), three plugins, and on a Mac `system-tui` and a statusline. `install.sh` does every step and is safe to rerun. On Windows your Bash tool is Git Bash, so every command below runs as written, and the installer leaves out `system-tui` and the statusline.

## How to run this

- The kit lives in `~/src/ai-welcome-kit`. If that folder doesn't exist, clone it: `git clone https://github.com/constdecimalserrno/ai-welcome-kit.git ~/src/ai-welcome-kit`. If it does, run `git -C ~/src/ai-welcome-kit pull -q --ff-only`. Run every command below from that folder.
- `tutorial.html` is a slide deck. Each step below is one slide, with the same name, at `#install-<n>`: step 3 is `#install-3`, "Pick the code folder". A hosted artifact may not pass the `#` on to the deck, so don't rely on the link: name the slide in chat, like "Setup 3 of 6: Pick the code folder", the same as the deck's progress label.
- For each step: say what's next in one line, run it, then report the result in a line or two.
- Don't ask the user to make choices beyond the ones below. Every other choice has a default.
- Ask before anything that changes `~/.claude`. Only step 4 does that. If they say no, nothing has changed: send the guide and go to step 8.
- Already installed? Still start at step 1. On *Do the demo (Snake)*, rerun the installer anyway - it's safe, and every line says "already" - then go on to step 7.

## 1. Open the tutorial and pick a path

Slide `#install-1`. Do this first, every time, even if the kit is already installed. It only reads, and it doesn't need `install.sh`, so it works in plan mode or a cautious session too.

Publish `tutorial.html` with your Artifact tool and give the user the link, on its own line. Give it again whenever they change sessions. If that fails or you have no Artifact tool, send https://constdecimalserrno.github.io/ai-welcome-kit/tutorial.html. Say that the slides are follow-along only: they do everything by talking to you here.

Before the question, say in two lines what this needs: a Mac or Windows, Claude Code and a paid plan; the install takes minutes, and the demo takes an afternoon, needs Node and uses a lot of usage.

Then ask which path they want: "Which path? *Install the kit*, *Do the demo (Snake)* or *Just read the guide*." Always ask, even when their first message was "set me up": that's how they got here, not a path. Wait for the answer. A free-text answer maps to the closest one: "the tutorial", "the demo" or "all of it" is *Do the demo (Snake)*, "install" or "just the kit" is *Install the kit*, and "the rules", "the cheat sheet" or "what's in it" is *Just read the guide*. Still unsure? Ask once more, with the list.

- **Install the kit:** run steps 2 to 6 one at a time, reporting each and naming its slide. Then step 8.
- **Do the demo (Snake):** run steps 2 to 6 one at a time, reporting each, then step 7.
- **Just read the guide:** publish `guide.html` as a second artifact, or send https://constdecimalserrno.github.io/ai-welcome-kit/guide.html. Install nothing and don't offer to. Then step 8.

## 2. Check prerequisites

Slide `#install-2`.

```sh
uname -s; command -v claude; python3 -c 'print("python ok")' || python -c 'print("python ok")' || py -c 'print("python ok")'; git --version; node --version; cargo --version
```

- A path for `claude`, `python ok` and a git version are all required. `Darwin` is a Mac; `MINGW` or `MSYS` is Windows. On Windows, if Python is missing, tell the user it's at https://www.python.org, then stop. On a Mac without the Command Line Tools, `python3` and `git` exist but fail to run. If either fails, tell the user to run `xcode-select --install`, then stop. No `claude` means they're running you some other way: point them to https://code.claude.com/docs/en/quickstart, and say it needs a paid Claude plan.
- `node` is needed for `ponytail` and the demo. If it's missing, tell the user it's at https://nodejs.org. On the demo path, stop until they have it. Otherwise carry on: the installer skips `ponytail`.
- `cargo` is optional, and only used on a Mac. If it's missing (`command not found`), the install skips `system-tui` with a warning and does everything else. Don't install Rust yourself - tell the user it's at https://rustup.rs. If `cargo` is there but errors with "rustup could not choose a version", tell them to run `rustup default stable`.

## 3. Pick the code folder

Slide `#install-3`. `system-tui` shows disk use for each project under one folder. If the user already told you where they keep their code, pass it with `--code-dir`. Otherwise leave the flag off: the installer reuses the folder from its last run, or else picks the first of `~/code`, `~/src`, `~/Projects`, `~/Developer` and `~/dev` that holds something besides this kit. Don't stop to ask. If it warns that the folder doesn't exist, tell the user, and that they can rerun with `--code-dir <folder>`.

## 4. Run the installer

Slide `#install-4`. This is the step that writes to `~/.claude`. Tell the user, in plain words first: "This adds Claude skills, plugins and a status bar to your Claude Code setup, and you can undo it with one command." Then what it will do:

- Copy two skills into `~/.claude/skills`.
- Clone the `arena` skill from https://github.com/Jakeschincariol/arena-skill into `~/.claude/ai-welcome-kit/arena-skill`, and link it in as `~/.claude/skills/arena`. A rerun pulls it.
- Install three plugins: `mattpocock-skills`, `frontend-design` and `ponytail`. `ponytail`'s hooks then run in every project, and it logs a cost line per turn to `~/.config/ponytail/band/`, on this computer.
- On a Mac: clone https://github.com/constdecimals9/system-tui (the kit author's other account), add its statusline, and set `statusLine` in `~/.claude/settings.json`, unless they already have one.
- On a Mac: build `system-tui` if Rust is installed, which can add `~/.cargo/bin` to PATH in their shell rc file.

Anything it replaces is backed up first. Whose code each piece is, and how to undo it, is in the README's safety section and at https://constdecimalserrno.github.io/ai-welcome-kit/guide.html#safe: point them there if they ask. Ask "OK to run it?" and wait. If they want less, add `--skip <pieces>` (see `bash install.sh --help`).

```sh
bash install.sh                       # or: bash install.sh --code-dir <folder> --skip arena,system-tui
```

`<folder>` is a folder inside `~`, like `code` or `Documents/work`. Anything outside `~` (or `~` itself, or a path with `..`) gets a warning and falls back to the default. The Rust build runs last and takes a few minutes on the first run, so give the command a 10-minute timeout. If it gets cut off anyway, just rerun it: everything before the build is already done. It prints one `==>` line per step and ends with a `Verify:` checklist.

- Exit 0 and every line `[ok]` or `[--]`: go to step 5. A skipped `system-tui` isn't a failure, even when the build itself failed: pass on the fix it printed, like `rustup default stable`, and don't rerun for it.
- A `[--] existing <name> kept` line means the user already had a skill by that name - a git repo, or a different version. For `arena`, it means `~/.claude/skills/arena` isn't the kit's link, like a copy they installed themselves. That's not a failure. Tell the user, and that `bash install.sh --force-skills` replaces it after a backup. Only run that if they say yes.
- A `[--] existing statusLine kept` line means they have their own. Tell them `system-tui`'s usage panel stays empty without the kit's, and that `--force-statusline` replaces theirs after a backup. Only run that if they say yes.
- Exit 1: each problem is printed with an `x` and how to fix it. Fix what you can, rerun the same command, and report the rest to the user.

## 5. Verify

Slide `#install-5`. Each of these should succeed:

```sh
for s in kit-living-doc kit-ticket-runbook arena; do test -f ~/.claude/skills/$s/SKILL.md || echo "missing $s"; done
claude plugin list --json | python3 -c 'import json,sys; on={p["id"] for p in json.load(sys.stdin) if p.get("enabled")}; miss={"mattpocock-skills@claude-plugins-official","frontend-design@claude-plugins-official","ponytail@ponytail"} - on; print(sorted(miss) or "all enabled"); sys.exit(bool(miss))'   # all installed and enabled
python3 -c 'import json,os; print(json.load(open(os.path.expanduser("~/.claude/settings.json")))["statusLine"])'
echo '{}' | ~/.claude/statusline/statusline.py
env -i HOME="$HOME" TERM=dumb "$SHELL" -lic 'command -v system-tui'   # a clean login shell; skip if system-tui was skipped or the installer said to add PATH yourself
```

Skip the check for anything skipped or kept in step 4. The first line prints nothing. The `statusLine` printed should be `{'type': 'command', 'command': '<home>/.claude/statusline/statusline.py', 'refreshInterval': 10}`.

## 6. Restart and wrap up

Slide `#install-6`. Tell the user:

- What installed, and anything skipped or failed, with the fix.
- Anything replaced is backed up under `~/.claude/backups/ai-welcome-kit-<timestamp>/`. If the installer replaced an existing `statusLine`, say so.
- If it added `~/.cargo/bin` to their shell rc (`~/.zshrc`, a bash profile, or fish's `config.fish`), say which file, and that new terminals pick it up. For any other shell it only warns: tell them to add `~/.cargo/bin` to PATH themselves.
- **Restart Claude Code** to load the skills, plugins and statusline. On *Do the demo (Snake)*, that restart is step 7's new session: `/exit`, then run slide `#demo-2`. Don't restart twice.
- `/exit` only closes this session. Nothing is lost, the tutorial link keeps working, and a local copy is at `~/src/ai-welcome-kit/tutorial.html`. The next session starts fresh: on the demo the slides carry them, and otherwise it's enough to say "I just installed the AI Welcome Kit".
- Unless it was skipped, run `system-tui` in a spare terminal tab; `q` quits.
- Point them to the checklist slide, `#install-done` ("You're done when").

## 7. Start the Snake project

Only on the *Do the demo (Snake)* path. The project is a very simple web Snake game, scripted and played from fixed seeds, then analyzed to find the fastest strategy. It uses nearly every skill in the kit, and follows the starting flow: set up, grill, spec, tickets, then one subagent per ticket. The demo slides, `#demo-1` to `#demo-19`, give each step its skill, its effort and the exact prompt to type.

Say this in the same message as step 6, since `/exit` ends this session. Then they run slide `#demo-2`, "Make the workspace", in their terminal (Git Bash on Windows). It makes `~/src/snake`, copies in `examples/snake/BRIEF.md`, and starts their next session there, at high effort. That session is the restart. Don't build the game yourself - they build it, in that session.

## 8. A first thing to do

On every path but the demo, before you finish. Ask what they do for work, then give them two or three concrete things to try tomorrow, in their own terms. The *Your first day* prompts at https://constdecimalserrno.github.io/ai-welcome-kit/guide.html#first-day are the starting point. None of it should need tickets.
