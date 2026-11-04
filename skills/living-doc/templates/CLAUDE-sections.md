<!-- Append to the project's CLAUDE.md, then fill every <placeholder>. The examples show the shape: change them to fit. No service or deploys (a plain or local project)? Drop the "Ticket runbook" section. -->
## Ticket runbook

Every ticket runs the `ticket-runbook` skill, with these settings:

- **Service:** <service>
- **Deploy window:** <window, e.g. weekdays 10:00 to 16:00 local time>
- **Freeze:** <freeze, e.g. no restarts 15:30 to 16:30 during the daily report>
- **Shared code that needs extra care:** <shared modules>
- **Outages confirmed as expected, and who confirmed them:** none yet

## Living doc

Our living doc: <artifact URL>. Its ticket files live in `.scratch/<effort>/` and render to the local mirror `.scratch/<effort>/living-doc.html`; both stay in this repo, current after every change.

After every ticket change, and for every new ticket (pasted, or from the page's form), use the `living-doc` skill. It syncs the local mirror and the artifact, and respins the artifact when this link is unreachable after a Claude account switch.
