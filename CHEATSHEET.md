# Rules of thumb

How I get the most out of Claude Code.

1. **Almost always run in auto mode.** The faster you trust Claude, the faster you get your work done. Press `Shift+Tab` to cycle permission modes until it says auto, or start with `claude --permission-mode auto`.
2. **Use Opus 5.5.** Low or medium effort for actual code implementation. High or xhigh for planning, wayfinding and grilling. `/model` and `/effort` change it mid-session.
3. **Effort doesn't mean good or bad output.** It only means how much Claude thinks and checks its own work. If you planned and ticketed well, code needs low or medium. When you're planning and don't quite know yet, higher effort is OK.
4. **Use artifacts to understand what's going on.** Ask for a page instead of reading a wall of terminal text.
5. **Play with multimedia.** Claude isn't just text. It reads PDFs and images, and can transcribe what's in them. It works with your files, and draws things: diagrams, SVGs, charts, whole pages. If it can't do something natively, like generating an image or transcribing audio, it can find or write the right tool for it. So feel free to play.
6. **Make Claude write in your voice.** I train my agent on my blog. Write a voice guide from your own writing and point your global `CLAUDE.md` at it.
7. **Think like an automator.** If you're ever doing data entry, ask "can I have Claude do this?" For anything you're doing, ask yourself: can Claude do this, or can we make a skill for it?
8. **Anything you do more than once, make it a skill.** Have Claude write it, using Matt Pocock's `writing-for-agents` skill.
9. **Keep your global `~/.claude/CLAUDE.md` short.** It's context for every session you run.
10. **Don't let Claude read sensitive info directly.** Have it write a script that reads the secret and puts it where it needs to go, so Claude never sees it.
11. **Context is everything.** Every new problem gets a fresh workspace with only the context it needs. Be as verbose as you like with that context, just don't confuse it - if you're studying bananas, don't mention oranges.
12. **Treat Claude like a junior dev.** Give it the exact plan, so it can't fuck up. The more leniency you give it, the more it takes.
13. **Claude is a reflection of you and what you know.** It will be sycophantic, so tell it what to do. You're still the driver.
14. **Have agents argue.** Have them test things against each other: one builds, another attacks it. `/arena` is the extreme version - a whole bracket of them.
15. **Trust and verify.** Use test-driven development (`/tdd`), so the agent can prove the output is correct, not just claim it. Have Claude run your tests, or audit the code with `/ponytail-audit`. Matt Pocock's closest is `/improve-codebase-architecture`.
16. **The ticket runbook does most of this for you.** Every ticket works test-first with `/tdd`, runs the full test suite and gets a ponytail review. Then a separate agent reviews it for bugs, spec and live data. Live data is n/a locally. The one thing it doesn't do is an audit. Run `/ponytail-audit` yourself every so often.
17. **Don't know what you don't know? Ask Claude.** Keep asking until you get to the bottom of it. That's how you learn to use this. You no longer have to be a programmer to program.
18. **Watch your context.** The statusline's `ctx` is how much of the window this session is using. Keep it under about 30%. Past that, `/clear` or `/compact` to stay out of the dumb zone.
19. **Budget with the statusline.** `5h`, `7d` and `pace` tell you how much effort and how many parallel sessions you can throw at a problem. Don't be afraid to work in parallel - just make sure agents working in the same codebase know about each other.
20. **Leave `system-tui` open.** It doubles as caffeine. It keeps your Mac awake while it runs, so you can walk away and leave your agents working. It uses macOS `caffeinate`, and only holds the Mac awake while it's open.
21. **Name your sessions.** `/rename <name>`, or start with `claude -n <name>`, so you can tell which one is doing what. I name them after their folder or their problem.
22. **The starting flow for a small problem.** Claude can set up the workspace for you, and always look for ways to speed this up:
    1. A new workspace.
    2. `/setup-matt-pocock-skills`
    3. `/grill-with-docs` with your prompt or plan.
    4. `/to-spec`
    5. `/to-tickets`
    6. One subagent per ticket.

    Type the skills as slash commands - Claude can't start them for you. The main chat never implements. All implementation is done by a subagent at medium effort, or low only for a tiny, clear fix, and every piece of implementation is a ticket, local or on GitHub. For anything bigger, chart it with `/wayfinder` first. Matt Pocock's skills and videos go deeper - see the References in the README.
23. **GitHub is your friend.** Use it to store your work. Claude knows how to organize itself there.
24. **Code is cheap.** Don't be afraid to refactor or rebuild something if it's not working. It's often faster to rebuild a system or a script than to fix an old one.
25. **Dictate with [Wispr Flow](https://wisprflow.ai).** Download it and talk to Claude instead of typing. It makes your life so much easier.
26. **Get excited about working out how to use Claude best.** Treat it as a thought experiment. Being able to take on any problem is fun.
