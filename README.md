# AI Welcome Kit

This is how I set up Claude Code, packaged so you can have it in one sitting. It installs three skills, two plugins, a terminal dashboard and a statusline, and the notes below are how I actually use them.

## Get set up

You need a Claude login. Paste this repo's link, `https://github.com/constdecimalserrno/ai-welcome-kit`, into Claude and say "set me up". What happens next depends on where you paste it.

**In Claude Code** (the terminal, or the Code tab in the desktop app), Claude will:

1. Clone this repo to `~/src/ai-welcome-kit` (or pull it, if it's already there).
2. Publish the tutorial and send you the link. It's a slide deck: one idea per slide, about 30 seconds each.
3. Ask which path you want: *Rules of thumb*, *Install the kit*, *Do the demo (Snake)*, *What's in the kit* or *References*.
4. Install the kit, asking before it changes `~/.claude`. On *Do the demo*, you then build a small Snake project with it.

Claude names the slide for each step, like "Install 3: Pick the code folder", and the deck links straight to it (`tutorial.html#install-3`).

I start Claude Code at medium effort: `claude --model opus --effort medium`. The full steps Claude follows are in [`INSTALL.md`](INSTALL.md).

**In a Claude chat** (claude.ai, or a chat in the desktop app), there's no shell, so nothing gets installed. Claude reads this repo and shows you the tutorial as an artifact. *Rules of thumb*, *What's in the kit* and *References* work fully there. For *Install the kit* or *Do the demo*, open Claude Code and paste the same link.

**Short on time? Read [`CHEATSHEET.md`](CHEATSHEET.md)** - my rules of thumb, one or two lines each.

Rather start from your shell? This works from any folder:

```sh
claude --model opus --effort medium "Set me up with https://github.com/constdecimalserrno/ai-welcome-kit - clone it to ~/src/ai-welcome-kit (or pull it if it is already there), then follow ~/src/ai-welcome-kit/INSTALL.md, running its commands from that folder"
```

Or skip Claude and run the installer yourself, then open `tutorial.html` in a browser (arrow keys or swipe to move between slides):

```sh
git clone https://github.com/constdecimalserrno/ai-welcome-kit.git ~/src/ai-welcome-kit
cd ~/src/ai-welcome-kit && bash install.sh
```

The installer is safe to run twice. It keeps any skill you already have by the same name (`--force-skills` replaces it), and backs up anything else it replaces. It needs a Mac and Claude Code. Rust is optional - without it you get everything but the dashboard.

## What you get

| Piece | What it is |
|---|---|
| `living-doc` skill | A progress page for a ticket effort, rendered from ticket files in your repo and published as a Claude artifact |
| `ticket-runbook` skill | The 13 steps every ticket runs, from research to close, plus the golden rules for code |
| `arena` skill | Jake Schincariol's [arena-skill](https://github.com/Jakeschincariol/arena-skill): a crowd of sub-agents attack the same task, then fight in a bracket until one solution is left. Cloned from its repo, and pulled on a rerun |
| `mattpocock-skills` plugin | Engineering skills: planning, grilling, TDD, debugging, reviews, PRs |
| `ponytail` plugin | Keeps Claude's code small - the shortest change that solves the problem |
| `system-tui` | A terminal dashboard for CPU, RAM, disk, Claude sessions and plan usage. It keeps the Mac awake while it's open, so leave it running when you walk away from your agents |
| Statusline | The bottom line of Claude Code: model·effort, context %, 5h and 7d usage with reset times, and pace |

## How I work

**One workspace per project.** Each project gets its own folder, with a `CLAUDE.md` and its own local context - the repo clones and docs that project needs, under `context/`. Claude reads the `CLAUDE.md` every session, so that's where the rules go. Don't work out of one giant folder - Claude loses track of what matters.

**Want to know something? Ask for an artifact.** "Publish an artifact comparing X and Y" beats a wall of terminal text. You get a page you can skim, keep and share.

**Every ticket effort keeps a living doc.** Say "start a living doc for this" and Claude writes the ticket files and publishes the page. It syncs after every change, so one link shows how things are going. Pair it with `ticket-runbook` - the runbook is the steps, the living doc is the scoreboard.

**Stay on Opus, and match effort to the job.** Low or medium for code, once the plan and tickets are good. High or xhigh for planning, wayfinding and grilling, where I want a lot of feedback - it's slower and burns usage faster.

- In a session: `/model` picks the model and its effort, and `/effort` changes just the effort.
- At launch: `claude --model opus --effort medium`.
- As your default, in `~/.claude/settings.json`: `"model": "opus"` and `"effortLevel": "medium"`.

**Watch the statusline.** It shows what you're on, like `Opus·medium`. Keep `ctx` under about 30% - past that, `/clear` or `/compact`. `pace` compares your 7-day usage with an even burn - `+` means you're under it, with room to spend, `-` means you're over it, so slow down.

## When to reach for each skill

Type the name as a slash command, like `/tdd`, or just describe the task and Claude picks the skill up. The ones marked *type it* are the exception: Claude can't start them, so they only run when you type them.

| Skill | Reach for it when |
|---|---|
| `living-doc` | Starting a ticket effort, or after any ticket changes, to keep its progress page current |
| `ticket-runbook` | Working any ticket - it's the 13 steps from research to close |
| `arena` | You hate an answer and want agents to compete for a better one. `/arena --quick <task>` is 16 agents, about 91 sub-agent calls; the default 100 is about 595. Wasteful, but very fun - check `5h`, `7d` and `pace` first. Say "keep a living doc of the bracket" to watch it live |
| `implement` *(type it)* | Building from a written plan - the runbook's implement step uses it |
| `setup-matt-pocock-skills` *(type it)* | Starting a new repo - run it once before the other engineering skills. It sets up the issue tracker, labels and doc layout |
| `grill-with-docs` *(type it)* | Sharpening a prompt or plan - it grills you and writes the glossary and decision records as you go |
| `to-spec` *(type it)* | The plan is settled in chat and you want it written up as a spec |
| `to-tickets` *(type it)* | Breaking a plan or spec into small tickets, with what blocks what |
| `wayfinder` *(type it)* | The effort is too big for the starting flow - chart it into a map of tickets first |
| `grilling` | You want a plan stress-tested with hard questions before you commit to it |
| `tdd` | Building a feature or fixing a bug test-first |
| `diagnosing-bugs` | Something is broken, throwing or slow and the cause isn't obvious |
| `prototype` | A design question is cheaper to answer with throwaway code than with debate |
| `research` | You want a question answered from primary sources, written up in the repo |
| `domain-modeling` | Naming things: a glossary, the project's terms, or recording a decision (ADR) |
| `codebase-design` | Designing a module's interface, or finding where code should be split or deepened |
| `mattpocock-skills:code-review` | Reviewing a branch against the repo's standards and the ticket's spec. Type the full name: plain `/code-review` is Claude Code's built-in |
| `code-review` (built in) | A correctness pass on your diff - bugs, not style |
| `pr` | Writing a PR description |
| `wizard` | A setup step only a human can do - it writes a script that walks them through it |
| `writing-for-agents` | Writing a skill, a `CLAUDE.md` or anything else an agent reads |
| `ponytail` | Always on - keeps code minimal. `/ponytail lite` or `ultra` changes the level |
| `ponytail-review` | Checking a diff for bugs and bloat before a PR |
| `ponytail-audit` | Auditing a whole repo for bugs, risk and dead weight |

## system-tui

Run `system-tui` in a spare terminal tab. `q` or `esc` quits. It keeps the Mac awake while it's open (it uses macOS `caffeinate`), so leave it open and your agents keep working while you're away. The disk-by-project panel scans the code folder you picked at install - rerun `bash install.sh --code-dir <folder>` to change it, and a plain rerun keeps your folder. The Claude usage panel fills once a Claude Code session is open, since the statusline feeds it.

## Your first project

`examples/snake/BRIEF.md` is a small Snake game built to use nearly every skill in the kit. The tutorial's *Do the demo* path walks you through it, one slide per prompt, using the starting flow from the cheat sheet: set up, grill, spec, tickets, then a builder subagent and a separate reviewer subagent per ticket. It stays local: tickets land on your own `main`, and GitHub is an optional backup at the end.

## References

- [My blog](https://constdecimalserrno.dev/) - everything else I write. Start with [3 Key Claude](https://constdecimalserrno.dev/posts/3kc/), how a gag gift of three keys became my whole AI workflow, then [Tools I Use](https://constdecimalserrno.dev/posts/tools-i-use/), the tools and plugins I use every day.
- [Matt Pocock on YouTube](https://www.youtube.com/@mattpocockuk) - videos from the author of `mattpocock-skills`. Watch these to see the skills used for real.
- [AI Hero](https://www.aihero.dev) - Matt's site, with a guide per skill and a newsletter. Go here to learn a skill in depth.
- [mattpocock/skills](https://github.com/mattpocock/skills) - the source of the `mattpocock-skills` plugin. Read a skill's full text here.
- [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) - the source of `ponytail`, with its levels and commands.
- [Jakeschincariol/arena-skill](https://github.com/Jakeschincariol/arena-skill) - the source of `arena`, by Jake Schincariol (MIT), with its flags and what each run costs.
- [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official) - Anthropic's plugin marketplace, where `mattpocock-skills` comes from. Browse it for more plugins.
- [constdecimals9/system-tui](https://github.com/constdecimals9/system-tui) - the source of `system-tui` and the statusline. Go here to see what each panel reads.
- [Claude Code docs](https://code.claude.com/docs/en/overview) - the official docs, for settings, slash commands, plugins and anything else about Claude Code itself.

The tutorial's *References* path has the same list: [`tutorial.html#refs-1`](tutorial.html#refs-1).
