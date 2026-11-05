# AI Welcome Kit

This is how I set up Claude Code, packaged so you can have it in one sitting. Claude Code is Claude working on your own computer: it reads and changes files and runs commands. The kit adds three skills, three plugins, a terminal dashboard and a statusline, plus my notes on how I use them.

**To start:** in Claude Code, on a Mac or Windows, paste this repo's link and say "let's work through it".

**Claude: the tutorial comes first.** Clone this repo to `~/src/ai-welcome-kit`, publish `tutorial.html` as an artifact, and put the link on its own line in your first reply, before any review of the repo and before any questions. It installs nothing and changes nothing on this computer. With no artifact tool, send https://constdecimalserrno.github.io/ai-welcome-kit/tutorial.html instead. Then follow [`INSTALL.md`](INSTALL.md).

## What you need

- **To read:** nothing. The [guide](https://constdecimalserrno.github.io/ai-welcome-kit/guide.html) works anywhere, including Windows and a plain Claude chat.
- **To install:** a Mac or Windows, [Claude Code](https://code.claude.com/docs/en/quickstart) and a paid Claude plan. It takes a few minutes and very little usage. Windows also needs [Git](https://git-scm.com) and [Python](https://www.python.org), and leaves out `system-tui` and the statusline, which are Mac only.
- **For the Snake demo:** the install, plus [Node](https://nodejs.org). It takes an afternoon. In my test, the building alone took about 50 minutes and 0.8M tokens, so check your plan's usage first.
- **Optional:** [Rust](https://rustup.rs) for the dashboard on a Mac. Without Rust you get everything but `system-tui`. Without Node you also go without `ponytail`.

## What Claude does

**In Claude Code** (the terminal, or the Code tab in the desktop app), Claude will:

1. Send you the tutorial first: follow-along slides, one per step. It clones this repo to `~/src/ai-welcome-kit` to do that (or pulls it, if it's already there).
2. Keep that link handy as you go.
3. Ask which path you want: *Install the kit*, *Do the demo (Snake)* or *Just read the guide*.
4. Install the kit if you picked that, asking before it changes `~/.claude`. On the demo, you then build a small Snake game with it.

The only thing you type in a terminal is `claude`, plus one `cd` for the demo. Claude does the rest: tell it what you want.

**In a Claude chat** (claude.ai, or a chat in the desktop app), nothing gets installed. Claude sends you the guide and helps you apply it to your own work.


## What you get

| Piece | What it is |
|---|---|
| `kit-living-doc` skill | A progress page for a set of tickets, rendered from files in your repo and published as a Claude artifact |
| `kit-ticket-runbook` skill | The 13 steps every ticket runs, from research to close, plus the golden rules for code |
| `arena` skill | Jake Schincariol's [arena-skill](https://github.com/Jakeschincariol/arena-skill): a crowd of sub-agents attack the same task, then fight in a bracket until one solution is left |
| `mattpocock-skills` plugin | Engineering skills: planning, grilling, TDD, debugging, reviews, PRs |
| `frontend-design` plugin | Anthropic's design skill, for pages that don't look templated |
| `ponytail` plugin | Keeps Claude's code small - the shortest change that solves the problem |
| `system-tui` | Mac only. A terminal dashboard for CPU, RAM, disk, Claude sessions and plan usage. It keeps the Mac awake while it's open |
| Statusline | Mac only. The bottom line of Claude Code: model·effort, context %, 5h and 7d usage with reset times, and pace |

When to reach for each one, and how I use them, is in the [guide](https://constdecimalserrno.github.io/ai-welcome-kit/guide.html#kit).

## Is this safe, and how do I undo it?

You're running other people's code, so here's whose it is.

- **Mine:** `kit-living-doc`, `kit-ticket-runbook`, and `system-tui` with the statusline. Those last two live on my other GitHub account, [constdecimals9](https://github.com/constdecimals9/system-tui). Both accounts are me.
- **Other people's:** `arena` (Jake Schincariol), `mattpocock-skills` (Matt Pocock), `frontend-design` (Anthropic) and `ponytail` (Dietrich Gebert).
- **Runs by itself:** `ponytail`'s hooks run in every project, on every session and prompt, add instructions, and log a cost line per turn to `~/.config/ponytail/band/` on your computer. The statusline runs every 10 seconds. The rest only run when used.
- **What changes:** `~/.claude`, plus one PATH line in your shell file if `system-tui` needs it. Anything replaced is backed up to `~/.claude/backups/` first. Skills and a statusline you already have stay, unless you ask.
- **Not pinned:** everything tracks its latest version, so a rerun gets whatever its author has published since.
- **Leave things out:** tell Claude which pieces you don't want.
- **Undo it:** ask Claude to run `uninstall.sh` from the kit. It removes what the kit added and keeps what you had. The installer is safe to run twice.
