---
name: ticket-runbook
description: Ticket runbook: the 13 steps every ticket runs (the living doc's playbook), from research and plan through PR, human sign-off and a solo deploy to monitoring and close, under the golden rules for code. Use whenever you work a ticket.
---

# Ticket runbook

Every ticket runs these 13 steps, in order. The ticket's `## Rollout` in its living doc tracks them: tick a step `- [x]` once its done-line holds, and mark one that can't apply `- [-] … (n/a: why)`, such as no deploy for a docs-only change, instead of skipping it silently. Every step also gets a dated line in the ticket's `## Log`, questions go in `## Open questions` so anyone can answer them, and the living doc is synced. A ticket with no `## Rollout`, like a `/to-tickets` file, gets one first: append `## Rollout` with the 13 steps below as `- [ ]` lines.

**Test seams come from the spec.** When the ticket's spec has Testing Decisions (`/to-spec` writes them), those are the seams `/tdd` would agree with the user, so a subagent doesn't stop to ask.

**Already a subagent?** You can't spawn another, so run your skills inline, through the Skill tool or by reading their SKILL.md and doing what it says. A skill that says to spawn sub-agents runs inline too, one part after another: `mattpocock-skills:code-review`'s parallel Standards and Spec reviews become two reviews you do yourself, in turn. A builder runs steps 1 to 7 (`/implement`, `/tdd`, `/ponytail-review`), commits, and reports back. It never runs step 8 on its own work - a self-review finds nothing. A reviewer runs step 8 on the builder's diff. Either way, update the ticket file and leave the living-doc sync to the main chat.

**The main chat runs the tickets.** For each one it spawns a builder subagent (opus, effort medium, or low only for a tiny, clear fix) for steps 1 to 7. Once the builder reports, it spawns a separate reviewer subagent (opus, effort medium) for step 8, on the builder's diff. The reviewer saves its findings and can bounce the ticket: then a builder fixes them and the reviewer looks again. The main chat ticks steps 8, 10 and 13, closes the ticket and syncs the living doc.

**Project settings** are in the project's CLAUDE.md, under "Ticket runbook": the service, deploy window, freeze, shared code that needs extra care, and outages confirmed as expected. If that section is missing, settle it with the user and add it before step 11. A project that never deploys needs none: mark steps 11 and 12 `- [-] … (n/a: no deploy)`.

**Branches**, in a repo with a remote, are `<prefix>/<NN-slug>`, where `<prefix>` is the user's branch prefix from their global CLAUDE.md. If it names none, ask once.

**No remote, or local by choice?** A local-only repo (`git remote` prints nothing), or one whose CLAUDE.md says tickets land on local `main`, has no PR to open and nothing to deploy. Skip steps 2, 7, 9, 11 and 12, and mark each `- [-] … (n/a: no remote)`. Work on local `main`, so `/implement`'s "commit to the current branch" lands there; tickets that run in parallel must touch separate files. Step 8's correctness and spec reviews still run; its live-data review is n/a with no prod data or live state, so mark it `n/a: no prod data` in its review file (step 4 already wrote up the blast radius). Step 10 is done once the commits are on local `main`, and step 13 closes the ticket once its tests pass, it's reviewed and it's merged to local `main`. No branch prefix or project settings needed. Any other repo runs every step.

## Steps

1. **Research and plan.** Set the ticket's `Status: claimed`. Research the issue: read the code and the data, and find the root cause with evidence. Write `.scratch/<effort>/work/<NN-slug>/plan.md` covering the problem, the proven cause, what is still inferred, the smallest fix, the blast radius, the test plan, the release and monitoring plan, and open questions. Research notes go beside it in the same folder. Done when every section of plan.md is filled, with the cause proven by evidence or marked inferred. For new code there's no bug: the cause is the design, what you'll build and why it's shaped that way.
2. **Workspace.** Make a fresh worktree on `<prefix>/<NN-slug>` off `origin/main` of the repo the fix lands in. With the repo cloned under `context/<repo>`, that's (from the project folder) `git -C context/<repo> fetch origin && git -C context/<repo> worktree add "$PWD/worktrees/<NN-slug>" -b <prefix>/<NN-slug> origin/main`. When the project folder is the repo, drop the `-C context/<repo>`. Done when the ticket's `Workspace:` line names the new worktree.
3. **Implement.** The builder subagent does this itself. From the main chat, that means briefing a builder on model opus at effort medium, or low only for a tiny, clear fix. It must use all three skills:
   - **`/implement`** (`mattpocock-skills:implement`) to implement the plan. If it can't be invoked, copy its SKILL.md verbatim from `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/<version>/skills/engineering/implement/SKILL.md` into the brief.
   - **`/tdd`** (`mattpocock-skills:tdd`) to work test-first: a regression test that fails on `main` and passes with the fix. For new code, that's red first: the test fails before the code exists.
   - **`mattpocock-skills:code-review`** on the diff before calling it done. That's the "code-review" `/implement` means, not the built-in `/code-review`.

   It follows the golden rules. Done when the regression test passes and every review finding is fixed or answered.
4. **Test.** Prove both things:
   - **It fixes the issue.** The regression test passes, and it fails with the fix reverted, which proves it tests the bug. To revert safely, with the fix still uncommitted: `git stash push -u -- <fix files>`, run the test and watch it fail, then `git stash pop`. Only pop if the stash printed `Saved`. Never move or copy files into `/tmp`. For new code, it failed before the code existed. A revert that can loop forever hangs `node --test` and the like, so give that run a hard limit, like `perl -e 'alarm 60; exec @ARGV' node --test`. Where possible, also check against real prod data or a real fixture.
   - **It breaks nothing else.** The full test suite and the linter, if the project has one (`cargo clippy` for Rust), pass for every crate or package touched, and the blast-radius check from golden rule 3 is written up.
5. **Ponytail review.** Run `/ponytail-review` on the diff and apply its findings. Done when every finding is applied or has a one-line reason in the ticket's log.
6. **Re-test.** Repeat step 4 on the reviewed diff. If it doesn't fix the problem, or it breaks anything, go back to step 3. Done when both checks pass.
7. **PR.** Push `<prefix>/<NN-slug>` and open a PR against `main`. Write the body with `mattpocock-skills:pr`, and reference the ticket. The body covers what the issue is, what the fix is, how it was tested, the blast radius, the release and monitoring plan, and any other notes. Done when the ticket's `PR:` line links it.
8. **Agent reviews.** A reviewer that didn't build the ticket (opus, effort medium) runs three independent agent reviews, one after another, and saves each to `work/<NN-slug>/reviews/`. Post none of them to GitHub.
   - Correctness: `/code-review`.
   - Spec and standards: `mattpocock-skills:code-review` against the ticket and plan.
   - Live data and blast radius: does the fix hold against prod data and live state, and what else does it touch? n/a with no prod data, as **No remote** says.

   Done when every finding is fixed or answered, with steps 4 to 6 re-run if code changed.
9. **Human sign-off.** Set `Needs human:` on the ticket and record `PR opened: YYYY-MM-DD`, so the living doc shows when the review is due or overdue. A human approves and merges the PR; agents never merge. The review is due within 2 working days and never past 3. Chase the reviewer on day 2. Done when a human has approved.
10. **Merged.** Done when the PR is on `main`.
11. **Deployed.** It deploys alone, inside the deploy window, under golden rules 4 and 5. Note the rollback target first. Done when the deploy has finished.
12. **Monitored.** Watch logs, restarts and the ticket's own check under golden rule 6. Done when the service is verified healthy with the change in it.
13. **Closed.** Tell the requester, then set `Status: resolved`. For new code, the requester is whoever asked for it: the report back to the main chat tells them. In a repo with a remote, a ticket closes only after its PR is in, it's deployed (if the project deploys), and the service is confirmed healthy. A local one closes as **No remote** says.

## Every step

- **Scratch files are per ticket, inside the project.** Every agent briefed on a ticket keeps its scripts and data under the ticket's `work/<NN-slug>/research/`, or a gitignored `tmp/<NN-slug>/` in the project, and never in `/tmp` or a shared scratch root. Agents running in parallel otherwise overwrite each other's files. Never overwrite, move or delete a file your ticket doesn't own, and never `mv` onto a path that already exists. Name the scratch folder in every brief.
- **Research before asking a human.** Before setting `Needs human:` or adding an open question, try to answer it yourself from the code, data, docs and earlier logs. Allow up to three research rounds. Log each round in the ticket. Flag a human only if it's still unanswered after three rounds, or if it's inherently human: approvals, merges, deploys, prod writes, spend, or a requester's intent that no data shows. Otherwise use your best judgment, log the call and its evidence, and move on.
- **Whenever a step needs a human**, set `Needs human: <what, in plain words>` near the top of the ticket, and the living doc is synced. It flags the ticket in red on its tab and in the overview. Clear the line once it's handled.

## Golden rules for code

Every ticket ships under these rules. No exceptions without the user's say-so.

1. **One ticket, one fix.** A fix changes only what its ticket needs. No drive-by refactors, renames, formatting sweeps or bundled tickets. If you find a second problem, note it in the current ticket's log and Findings, and open a ticket only on the user's go-ahead.
2. **Smallest possible fix.** Before a PR opens, run `/ponytail-review` on the diff. Every finding is fixed or answered in the ticket's log.
3. **Prove it breaks nothing.** Before release, also check the blast radius: grep every caller of each function you touched, and run the tests plus the linter for every crate or package you touched. Write down what else could change, such as other services, integrations or stored rows, and why it won't. A change to the shared code the project settings name gets extra care.
4. **Release one at a time.** One ticket per deploy. Don't start the next deploy until the last one is verified healthy.
5. **Deploy inside the window.** Prod deploys run only inside the project's deploy window and stay clear of its freeze. No deploys late on Fridays.
6. **Monitor after every release.** A finished dispatch doesn't mean healthy. Watch logs, restarts and the ticket's own check, such as the rows it should write, until it's verified. Then tick runbook step 12. Note the rollback target, the previous release, before deploying.
   - **Every deploy ends with every system running, as well as before or better.** No systems down, ever: that includes problems that predate the deploy. Before dispatching, snapshot a baseline: service state, throughput against the same hours the day before, one busy record spot-checked against its source, and upstream dependencies. After the deploy, compare against it. Anything below baseline or down blocks step 12. Restore it (restart, rollback or fix) before the deploy counts as done. Never wave something off as pre-existing: only the outages the project settings list as confirmed expected are exempt.
7. **Prod writes and merges are human-approved.** Agents commit and push only their own `<prefix>/<NN-slug>` branch, and never merge. The one exception is a repo with no remote, where tickets land on local `main`. DB writes are dry-run in `BEGIN … ROLLBACK` first and need the user's yes. The same goes for prod config, deploys and prod one-off jobs.
