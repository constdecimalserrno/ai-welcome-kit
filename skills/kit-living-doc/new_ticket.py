"""Add a ticket to the rollout: issue file + work folder + Inbox wave entry.

Usage: python3 -I new_ticket.py <effort_dir> "<title>" [estimate_days] < pasted_ticket.txt
Prints the new ticket's path. Fill Brief, Findings and Plan during runbook step 1.
"""
import pathlib, re, sys, datetime

effort, title = pathlib.Path(sys.argv[1]), sys.argv[2].strip()
est = sys.argv[3] if len(sys.argv) > 3 else "1.0"
pasted = sys.stdin.read().strip()
issues = effort / "issues"
num = f"{max((int(p.name.split('-')[0]) for p in issues.glob('[0-9]*-*.md')), default=0) + 1:02d}"
slug = f"{num}-" + "-".join(re.findall(r"[a-z0-9]+", title.lower()))[:48].rstrip("-")
today = datetime.date.today().isoformat()
DEFAULT_STEPS = ["Research done, plan.md written", "Workspace ready", "Fix implemented with /implement, TDD and code review",
         "Tested: fixes the issue, breaks nothing else", "/ponytail-review applied", "Re-tested after the review",
         "PR open, referencing the ticket", "Agent reviews done", "Human sign-off", "Merged",
         "Deployed alone, inside the deploy window", "Monitored: service healthy", "Closed, requester told"]
m = effort / "map.md"
if not m.exists():  # adopting /to-tickets files: start a bare map, filled in later from templates/map.md
    m.write_text(f"# {effort.resolve().name}\n\n## Waves\n\n1. **Inbox, not yet placed:**\n")
_ms = re.search(r"^## Rollout steps\n(.*?)(?=\n## |\Z)", m.read_text(), re.S | re.M)
STEPS = re.findall(r"^\d+\.\s+(.+)$", _ms.group(1), re.M) if _ms else DEFAULT_STEPS
(issues / f"{slug}.md").write_text(f"""# {title}

Status: needs-triage
Type: task
Size: ?
Blocked by: none
Estimate: {est}d
Plan: {effort}/work/{slug}/plan.md

## Brief

- **Goal:** {title}.
- **Open:** Root cause and smallest fix, which runbook step 1 finds.

## Findings

None yet.

## Plan

Runbook step 1: research and write the plan.

## Rollout

""" + "".join(f"- [ ] {s}\n" for s in STEPS) + f"""
## Log

- {today}: Ticketed.

## Open questions

## Human steps

TBD at step 1.

## Ticket (as pasted)

{pasted}
""")
w = effort / "work" / slug; w.mkdir(parents=True, exist_ok=True)
(w / "plan.md").write_text(f"# Plan: {title}\n\nTicket: `{effort}/issues/{slug}.md`\nStatus: draft, research in progress (runbook step 1 not done)\n\n"
                           "## Problem\n\n## Cause\n\n## Smallest fix\n\n## Blast radius\n\n## Test plan\n\n- Fixes the issue:\n- Breaks nothing else:\n\n"
                           "## Release and monitoring\n\nDeploy alone, inside the deploy window (CLAUDE.md).\n\n## Open questions\n")
s = m.read_text()
inbox = re.search(r"^(\d+)\.\s+\*\*Inbox, not yet placed:\*\*(.*)$", s, re.M)
if inbox:
    s = s.replace(inbox.group(0), inbox.group(0).rstrip() + (", " if inbox.group(2).strip() else " ") + f"{num} {title}")
else:
    waves = re.search(r"## Waves\n\n((?:\d+\..*\n)+)", s)
    n = len(waves.group(1).strip().splitlines()) + 1
    s = s.replace(waves.group(1), waves.group(1) + f"{n}. **Inbox, not yet placed:** {num} {title}\n")
m.write_text(s)
print(issues / f"{slug}.md")
