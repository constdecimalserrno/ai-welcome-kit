# <Title>

Eyebrow: <project folder · effort>
Owner: <who requesters contact>

## Approach

- **Cheapest wins first:** <one or two sentences>
- **Humans hold the keys:** With a remote, deploys, production writes and merges stay with the team, and each ticket names its human step. Without one, tickets land on local main.

## Runbook

1. Research the issue and write plan.md
2. Create the ticket's workspace (remote only)
3. Implement with /implement, TDD and code review
4. Test: fixes the issue, breaks nothing else
5. Run /ponytail-review and apply it
6. Test again, and loop until both checks pass
7. Open a PR that references the ticket (remote only)
8. Agent reviews, by an agent that didn't build it (live data is n/a locally)
9. Human sign-off within 2 days, never past 3 (remote only)
10. Merge (no remote: commit to local main)
11. Deploy alone, inside the deploy window (if it deploys)
12. Monitor until the service is healthy (if it deploys)
13. Close and tell the requester

## Rollout steps

1. Research done, plan.md written
2. Workspace ready
3. Fix implemented with /implement, TDD and code review
4. Tested: fixes the issue, breaks nothing else
5. /ponytail-review applied
6. Re-tested after the review
7. PR open, referencing the ticket
8. Agent reviews done
9. Human sign-off
10. Merged
11. Deployed alone, inside the deploy window
12. Monitored: service healthy
13. Closed, requester told

## Notes

- <scope, repos, shared mechanics every ticket leans on>

## Waves

1. **<Wave name>:** <NN title>, <NN title>

## Decisions so far

## Fog

- <unknowns worth chasing>
