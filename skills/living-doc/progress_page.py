"""Render .scratch/<effort>/ (map.md + issues/*.md) into the rollout page (living doc).

Usage: python3 progress_page.py <effort_dir> <out.html> [YYYY-MM-DD]
Ticket fields read: Status, Size, Blocked by, Estimate (working days, unpadded),
Not in estimate, ## Brief, ## Rollout (- [ ] / - [x]), ## Log (- YYYY-MM-DD: text),
## Open questions (- [qN] text), ## Human steps. Answers live in the page db, collection "answers".
Also reads /to-tickets files: `# NN: Title`, `**Status:**`, `**Blocked by:**`, `**What to build:**`
(the Goal) and bare `- [ ]` criteria (the steps). map.md is optional, and its <placeholder> lines are skipped.
"""
import html, re, sys, math, json, datetime as dt, pathlib

effort, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
today = dt.date.fromisoformat(sys.argv[3]) if len(sys.argv) > 3 else dt.date.today()
PAD_LO, PAD_HI = 1.5, 2.0  # be 50-100% conservative on every estimate
HOLIDAYS = {dt.date(2026, 11, 26), dt.date(2026, 11, 27), dt.date(2026, 12, 24), dt.date(2026, 12, 25),
            dt.date(2026, 12, 31), dt.date(2027, 1, 1)}  # ponytail: hand list, extend past Jan 2027
_map = effort / "map.md"
# Unfilled template lines (`<scope…>`) never reach the page.
mapmd = "\n".join(l for l in (_map.read_text() if _map.exists() else "").splitlines() if not re.search(r"<[a-z][^>]*>", l))
e = html.escape

def md_inline(s):
    s = e(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", s)

def field(text, name):
    m = re.search(rf"^\**{name}:\**\s*(.+)$", text, re.M)  # `Status:` or /to-tickets' `**Status:**`
    return m.group(1).strip() if m else ""

def section(text, name):
    m = re.search(rf"^## {name}\n(.*?)(?=\n## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""

def is_workday(d): return d.weekday() < 5 and d not in HOLIDAYS

def add_workdays(start, days):
    d = start
    while not is_workday(d): d += dt.timedelta(days=1)
    for _ in range(math.ceil(days - 1e-9) - 1 if days > 0 else 0):
        d += dt.timedelta(days=1)
        while not is_workday(d): d += dt.timedelta(days=1)
    return d

def fmt(d): return d.strftime("%a %b ") + str(d.day)

STATUS = {"done": "resolved", "closed": "resolved"}  # words /to-tickets users write for resolved
tickets = {}
for p in sorted((effort / "issues").glob("*.md"), key=lambda p: int(p.name.split("-")[0])):
    t = p.read_text(); num = p.name.split("-")[0]
    # No ## Rollout (a /to-tickets file): its acceptance criteria are the steps.
    steps = re.findall(r"^- \[( |x|-)\] (.+)$", section(t, "Rollout") or t, re.M)
    brief = re.findall(r"^- \*\*(\w+):\*\*\s*(.+)$", section(t, "Brief"), re.M)
    if not brief and (wtb := field(t, "What to build") or section(t, "What to build")):
        brief = [("Goal", wtb.splitlines()[0])]
    tickets[num] = dict(
        num=num, title=re.sub(r"^\d+:\s*", "", t.splitlines()[0].lstrip("# ").strip()),
        status=STATUS.get(field(t, "Status"), field(t, "Status")) or "needs-triage", size=field(t, "Size"),
        blocked=re.findall(r"\d{2,}", field(t, "Blocked by") or section(t, "Blocked by")),
        est=float((field(t, "Estimate") or "1").rstrip("d") or 0), excl=field(t, "Not in estimate"),
        brief=brief,
        steps=[(c, s) for c, s in steps], human=section(t, "Human steps"),
        needs_human=field(t, "Needs human"), plan=field(t, "Plan"), workspace=field(t, "Workspace"),
        pr=field(t, "PR"), pr_opened=field(t, "PR opened"), hold=field(t, "Hold"),
        original="\n\n".join(m.strip() for m in re.findall(r"^## (?:Ticket|Slack thread) \(as pasted[^\n]*\n(.*?)(?=\n## |\Z)", t, re.S | re.M)),
        log=re.findall(r"^- (\d{4}-\d{2}-\d{2}(?: [0-9:–-]+(?: UTC| NY)?)?):\s*(.+)$", section(t, "Log"), re.M),
        questions=[(f"t{num}-{q}", s) for q, s in re.findall(r"^- \[(q\d+)\]\s*(.+)$", section(t, "Open questions"), re.M)])

# "Won't do" tickets stay in their files but off the page.
tickets = {n: t for n, t in tickets.items() if t["status"] != "wontfix"}

DONE = {"resolved", "wontfix"}
LABEL = {"needs-triage": "Needs triage", "needs-info": "Needs info", "ready-for-agent": "Ready for agent",
         "ready-for-human": "Needs a human", "claimed": "In progress", "resolved": "Done", "wontfix": "Won't do"}
def frac(t):
    """Share of applicable runbook steps done; n/a steps don't count either way."""
    if t["status"] in DONE: return 1.0
    app = [c for c, _ in t["steps"] if c != "-"]
    return sum(c == "x" for c in app) / len(app) if app else 0.0
def review_due(t):
    """(due, hard) for an open PR awaiting sign-off (runbook step 9), else None."""
    if not t["pr_opened"] or len(t["steps"]) < 9 or t["steps"][8][0] != " ": return None
    d = dt.date.fromisoformat(t["pr_opened"][:10])
    return add_workdays(d + dt.timedelta(days=1), 2), add_workdays(d + dt.timedelta(days=1), 3)
def unblocked(t): return all(tickets.get(b, {}).get("status") in DONE for b in t["blocked"])

waves = []
for line in section(mapmd, "Waves").splitlines():
    m = re.match(r"\d+\.\s+\*\*(.+?):\*\*\s*(.+)$", line.strip())
    if m: waves.append((m.group(1), [n for n in re.findall(r"\b(\d{2,})\b", m.group(2)) if n in tickets]))
# Rollout order = wave order, then any ticket not placed in a wave.
# Tickets no wave names (no map.md, or adopted /to-tickets files) still get a card.
unplaced = [n for n in tickets if n not in {x for _, ns in waves for x in ns}]
if unplaced: waves.append(("Not in a wave yet" if waves else "Tickets", unplaced))
seq = [n for _, ns in waves for n in ns]
order = [tickets[n] for n in dict.fromkeys(seq + list(tickets))]

# Sequential schedule in rollout order: remaining work, padded, stacked from today.
cum_lo = cum_hi = 0.0
for t in order:
    rem = t["est"] * (1 - frac(t))
    t["start"] = add_workdays(today, cum_hi + 1e-6) if rem else None
    cum_lo += rem * PAD_LO; cum_hi += rem * PAD_HI
    t["due"] = add_workdays(today, cum_hi) if rem else None
base_total = sum(t["est"] for t in tickets.values())
base_left = sum(t["est"] * (1 - frac(t)) for t in tickets.values())
eta_lo, eta_hi = add_workdays(today, cum_lo), add_workdays(today, cum_hi)
pct = round(100 * (1 - base_left / base_total)) if base_total else 0
done_n = sum(t["status"] in DONE for t in tickets.values())
frontier = next((t for t in order if t["status"] not in DONE and unblocked(t)), None)
fog = re.findall(r"^- (.+)$", section(mapmd, "Fog"), re.M)
decisions = re.findall(r"^- (.+)$", section(mapmd, "Decisions so far"), re.M)

def pill(s): return f'<span class="pill s-{e(s)}">{LABEL.get(s, e(s))}</span>'
def bar(f): return f'<div class="track" role="progressbar" aria-valuenow="{round(f*100)}" aria-valuemin="0" aria-valuemax="100"><i style="width:{round(f*100)}%"></i></div>'
def blocked_chip(t):
    if not t["blocked"]: return ""
    return f'<span class="chip block {"met" if unblocked(t) else "wait"}">after {", ".join(t["blocked"])}</span>'
def review_chip(t):
    r = review_due(t)
    if not r: return ""
    due, hard = r
    cls = "late" if today > hard else ("warn" if today >= due else "")
    return f'<span class="chip review {cls}">review due {fmt(due)}, hard stop {fmt(hard)}</span>'
def due_txt(t): return "Done" if not t["due"] else f'target {fmt(t["due"])}'

def card(t):
    nxt = " is-next" if frontier and frontier["num"] == t["num"] else ""
    goal = next((v for k, v in t["brief"] if k == "Goal"), "")
    return f'''<a class="card s-{e(t["status"])}{nxt}" href="#t{t["num"]}">
  <header><span class="num">{t["num"]}</span><h3>{e(t["title"])}</h3></header>
  <p class="goal">{md_inline(goal)}</p>
  <div class="meta">{pill(t["status"])}{blocked_chip(t)}<span class="chip">{due_txt(t)}</span>{'<span class="chip human">Needs a human</span>' if t["needs_human"] else ""}{review_chip(t)}</div>
  {bar(frac(t))}
</a>'''

wave_html = "".join(f'''<section class="wave">
  <div class="rail"><span class="wn">Wave {i}</span><h2>{e(name)}</h2>
  <span class="wc">{sum(tickets[n]["status"] in DONE for n in nums if n in tickets)} of {len(nums)} done</span></div>
  <div class="cards">{"".join(card(tickets[n]) for n in nums if n in tickets and tickets[n]["status"] not in DONE) or '<p class="goal">Every ticket in this wave is done.</p>'}</div>
</section>''' for i, (name, nums) in enumerate(waves, 1))

PLAN = re.findall(r"^- \*\*(.+?):\*\*\s*(.+)$", section(mapmd, "Approach"), re.M)
TITLE = re.search(r"^# (.+)$", mapmd, re.M)
TITLE = TITLE.group(1).strip() if TITLE else effort.resolve().name
EYEBROW = re.search(r"^Eyebrow:\s*(.+)$", mapmd, re.M)
EYEBROW = EYEBROW.group(1).strip() if EYEBROW else TITLE
OWNER = re.search(r"^Owner:\s*(.+)$", mapmd, re.M)
OWNER = OWNER.group(1).strip() if OWNER else "the page owner"
plan_html = ('<section class="plan"><h2>How we tackle it</h2><ol>' + "".join(f"<li><h4>{h}</h4><p>{md_inline(x)}</p></li>" for h, x in PLAN) + "</ol></section>") if PLAN else ""
# Collapsed to a red count by default; it opens to each ticket and its ask.
humans = [t for t in order if t["needs_human"] and t["status"] not in DONE]
human_html = (f'''<details class="humans"><summary><h2>Waiting on a human · {len(humans)}</h2></summary><ul>{"".join(
    f'<li><a href="#t{t["num"]}"><span class="num">{t["num"]}</span> {e(t["title"])}</a><span>{md_inline(t["needs_human"])}</span></li>' for t in humans)}</ul></details>'''
    if humans else "")
# PRs whose agent reviews are done and that wait on a human's approval (runbook step 8 done, step 9 open),
# as one block the owner can paste to reviewers. A `Hold:` line keeps a PR out of it.
prs = [(m, t) for t in order if t["status"] not in DONE and len(t["steps"]) >= 9
       and t["steps"][7][0] == "x" and t["steps"][8][0] == " " and (m := re.search(r"#(\d+)\s+(https://\S+)", t["pr"]))]
held = [(m, t) for m, t in prs if t["hold"]]
ready = [(m, t) for m, t in prs if not t["hold"]]
pr_html = (f'''<section class="prs"><div class="prs-head"><h2>PRs ready for review · {len(ready)}</h2><button type="button" class="copy-prs">Copy</button></div>
  <pre class="prlist">{e(chr(10).join(f"#{m[1]} {t['title']}: {m[2]}" for m, t in ready))}</pre>
  {"".join(f'<p class="hint">On hold: <a href="{e(m[2])}">#{m[1]}</a> ({t["num"]}): {md_inline(t["hold"])}</p>' for m, t in held)}</section>'''
    if prs else "")
RUNBOOK = re.findall(r"^\d+\.\s+(.+)$", section(mapmd, "Runbook"), re.M)
runbook_html = "" if not RUNBOOK else f'''<section class="runbook"><h2>Every ticket runs this playbook</h2><ol>{"".join(f"<li>{s}</li>" for s in RUNBOOK)}</ol></section>'''
intake_html = f'''<section class="intake"><h2>Add a ticket</h2>
  <p>New request? Paste it here. It gets ticketed and runs the same playbook.</p>
  <form class="ticket-form" hidden>
    <label for="nt-title">Title</label><input id="nt-title" maxlength="200" placeholder="e.g. Retry failed webhook deliveries">
    <label for="nt-body">Details</label><textarea id="nt-body" rows="4" maxlength="20000" placeholder="What's wrong, example ids or logs, and who needs it."></textarea>
    <button type="submit">Submit ticket</button><span class="form-msg" role="status"></span></form>
  <p class="hint intake-hint" hidden>Submitting needs Contributor access to this page. Or send it to {OWNER}.</p>
  <ul class="reqlist" aria-live="polite"></ul></section>'''
overview = f'''<section class="panel" id="overview" role="tabpanel" aria-labelledby="tab-overview">
  {pr_html}
  {human_html}
  {runbook_html}
  {plan_html}
  {wave_html}
  {intake_html}
  <section class="side">
    <div><h2>Still unknown</h2><ul>{"".join(f"<li>{md_inline(f)}</li>" for f in fog)}</ul></div>
    <div><h2>Decided so far</h2><ul>{"".join(f"<li>{md_inline(d)}</li>" for d in decisions)}</ul></div>
  </section>
</section>'''

def ticket_panel(t):
    f = frac(t); n_done = sum(c == "x" for c, _ in t["steps"]); n_app = sum(c != "-" for c, _ in t["steps"])
    def step_li(i, c, s):
        cls = {"x": "done", "-": "na"}.get(c, "")
        mark = {"x": "✓", "-": "–"}.get(c, "")
        label = {"x": " (done)", "-": " (not applicable)"}.get(c, " (to do)")
        return (f'<li class="{cls}"><span class="box" aria-hidden="true">{mark}</span><span class="sn">{i}</span><span>{md_inline(s)}</span>'
                f'<span class="sr">{label}</span></li>')
    steps = "".join(step_li(i, c, s) for i, (c, s) in enumerate(t["steps"], 1))
    banner = (f'<div class="banner" role="note"><b>Needs a human</b><span>{md_inline(t["needs_human"])}</span></div>' if t["needs_human"] else "")
    def link(v):
        m = re.search(r"https://\S+", v)
        return f'<a href="{e(m.group(0))}">{md_inline(v.replace(m.group(0), "").strip() or m.group(0))}</a>' if m else f"<code>{e(v)}</code>"
    where = "".join(f'<div><span class="lbl">{k}</span><b class="small">{link(v)}</b></div>' for k, v in
                    (("Plan", t["plan"]), ("Workspace", t["workspace"]), ("PR", t["pr"])) if v)
    brief = "".join(f'<div class="b"><dt>{e(k)}</dt><dd>{md_inline(v)}</dd></div>' for k, v in t["brief"])
    when = ("Finished" if not t["due"] else
            f'{fmt(t["start"])} to {fmt(t["due"])}')
    excl = f'<div class="note"><h4>Not in the estimate</h4><p>{md_inline(t["excl"])}</p></div>' if t["excl"] else ""
    human = f'<div class="note"><h4>Human step</h4><p>{md_inline(t["human"])}</p></div>' if t["human"] else ""
    log = "".join(f'<li><time datetime="{d[:10]}">{d}</time><span>{md_inline(s)}</span></li>' for d, s in reversed(t["log"]))
    qs = "".join(f'''<li class="q" data-qid="{qid}"><p class="qt">{md_inline(s)}</p>
      <ul class="answers" aria-live="polite"></ul>
      <form class="answer-form" hidden><label class="sr" for="a-{qid}">Your answer</label>
        <textarea id="a-{qid}" rows="2" maxlength="4000" placeholder="Know the answer? Write it here."></textarea>
        <button type="submit">Post answer</button><span class="form-msg" role="status"></span></form></li>''' for qid, s in t["questions"])
    qblock = (f'<div class="block"><h3 class="lbl">Open questions · anyone can answer</h3><ol class="qs">{qs}</ol>'
              '<p class="hint" hidden>Answering needs Contributor access to this page. Ask the owner, or add a comment instead.</p></div>') if t["questions"] else ""
    logblock = f'<div class="block"><h3 class="lbl">Log</h3><ol class="log">{log}</ol></div>' if log else ""
    return f'''<section class="panel tp" id="t{t["num"]}" role="tabpanel"{' data-done="1"' if t["status"] in DONE else f' aria-labelledby="tab-t{t["num"]}"'}>
  <div class="th"><span class="num big">{t["num"]}</span><div><h2>{e(t["title"])}</h2>
    <div class="meta">{pill(t["status"])}{f'<span class="chip">size {e(t["size"])}</span>' if t["size"] else ""}{blocked_chip(t)}</div></div></div>
  {banner}
  <div class="tgrid">
    <div class="col">
      <div class="block"><h3 class="lbl">Brief</h3><dl>{brief}</dl></div>
      <div class="block"><h3 class="lbl">Rollout</h3>
        <div class="prow"><span>{n_done} of {n_app} applicable steps done{f" · {len(t['steps']) - n_app} not applicable" if n_app < len(t["steps"]) else ""}</span><b>{round(f*100)}%</b></div>{bar(f)}
        <ol class="steps">{steps}</ol></div>
      {qblock}
      <div class="block"><h3 class="lbl">Add information</h3>
        <div class="notes" data-ticket="t{t["num"]}"><ul class="notelist" aria-live="polite"></ul>
        <form class="note-form" hidden><label class="sr" for="n-t{t["num"]}">Information for this ticket</label>
          <textarea id="n-t{t["num"]}" rows="2" maxlength="8000" placeholder="Data, links, context or a correction for this ticket."></textarea>
          <button type="submit">Add</button><span class="form-msg" role="status"></span></form></div>
        <button type="button" class="ghost comment-btn" hidden>Comment on this ticket</button></div>
      {logblock}
    </div>
    <aside class="col">
      <div class="stats">
        <div><span class="lbl">Estimate</span><b>{t["est"]:g} d</b><small>{t["est"]*PAD_LO:g} to {t["est"]*PAD_HI:g} d padded</small></div>
        <div><span class="lbl">Window</span><b>{when}</b><small>{"" if not t["due"] else "padded 2x, in rollout order"}</small></div>
        {where}
        {review_chip(t)}
      </div>
      {human}{excl}
      <div class="orig"><h3 class="lbl">Original ticket</h3><h4>{e(t["title"])}</h4>
        <div class="orig-body" tabindex="0" aria-label="Original ticket text">{e(t["original"]) or "<em>No text was pasted.</em>"}</div></div>
    </aside>
  </div>
</section>'''

done_list = [t for t in order if t["status"] in DONE]
open_list = [t for t in order if t["status"] not in DONE]
HM = '<span class="hm" title="Needs a human">!</span>'  # kept out of the f-string so Python 3.9 parses it
tabs = '<a role="tab" id="tab-overview" href="#overview" aria-controls="overview">Overview</a>' + "".join(
    f'<a role="tab" id="tab-t{t["num"]}" href="#t{t["num"]}" aria-controls="t{t["num"]}" class="s-{e(t["status"])}">'
    f'<span class="dot"></span>{t["num"]}{HM if t["needs_human"] else ""}</a>' for t in open_list)
if done_list:
    tabs += f'<a role="tab" id="tab-done" href="#done" aria-controls="done" class="done-tab">Done · {len(done_list)}</a>'
done_panel = (f'''<section class="panel" id="done" role="tabpanel" aria-labelledby="tab-done">
  <div><span class="eyebrow">Closed tickets</span><p class="goal">Shipped, or closed with nothing to ship. Open one to see its log.</p></div>
  <div class="cards">{"".join(card(t) for t in done_list)}</div></section>''' if done_list else "")
next_html = (f'<a class="next" href="#t{frontier["num"]}"><span>Next up</span><b>{frontier["num"]} · {e(frontier["title"])}</b></a>'
             if frontier else '<div class="next"><span>Next up</span><b>Nothing unblocked</b></div>')

page = f'''<title>{e(TITLE)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@400;500;700;800&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
/* Layout: ETA band on top, tab strip, then Overview (wave ledger) or one ticket's rollout panel. */
:root {{
  --bg:#f3f5f8; --surface:#ffffff; --fg:#141a24; --muted:#5b6574; --line:#d9dee6; --accent:#2747c9;
  --s-agent:#2747c9; --s-human:#b86a00; --s-late:#c2322b; --s-info:#7a3fc2; --s-triage:#6b7480; --s-claimed:#0b8a8a; --s-done:#1f8a4c;
  --tint:color-mix(in oklab, var(--accent) 8%, var(--surface));
  --display:"Schibsted Grotesk", ui-sans-serif, system-ui, sans-serif;
  --body:"Schibsted Grotesk", ui-sans-serif, system-ui, sans-serif;
  --mono:"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#0e1218; --surface:#161c25; --fg:#e7ebf1; --muted:#9aa4b2; --line:#2a3340; --accent:#7f9bff;
  --s-agent:#7f9bff; --s-human:#f0a64a; --s-late:#ff7b72; --s-info:#b88cf2; --s-triage:#9aa4b2; --s-claimed:#4cc9c9; --s-done:#5bd08d; color-scheme:dark }} }}
:root[data-theme="dark"] {{
  --bg:#0e1218; --surface:#161c25; --fg:#e7ebf1; --muted:#9aa4b2; --line:#2a3340; --accent:#7f9bff;
  --s-agent:#7f9bff; --s-human:#f0a64a; --s-late:#ff7b72; --s-info:#b88cf2; --s-triage:#9aa4b2; --s-claimed:#4cc9c9; --s-done:#5bd08d; color-scheme:dark }}
* {{ box-sizing:border-box }}
body {{ background:var(--bg); color:var(--fg); font:15px/1.55 var(--body);
  padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); padding-block:28px 64px }}
.wrap {{ max-width:1120px; margin:0 auto; display:grid; gap:28px }}
code {{ font:0.88em var(--mono); overflow-wrap:anywhere }}
.lbl, .eyebrow, .wn, .next span, .plan h2, .side h2 {{ font:600 12px var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 }}
.eta {{ background:var(--fg); color:var(--bg); border-radius:14px; padding:22px 24px; display:grid; grid-template-columns:1.3fr 1fr; gap:20px 32px }}
.eta .lbl {{ color:color-mix(in oklab, var(--bg) 70%, var(--fg)) }}
.eta .date {{ font:800 clamp(30px, 6vw, 52px)/1 var(--display); letter-spacing:-.02em; margin:6px 0 8px; font-variant-numeric:tabular-nums }}
.eta p {{ margin:0; color:color-mix(in oklab, var(--bg) 78%, var(--fg)); font-size:14px; max-width:52ch }}
.eta dl {{ margin:0; display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:14px; align-content:center }}
.eta dd {{ margin:2px 0 0; font:700 20px var(--display); font-variant-numeric:tabular-nums }}
.eta .track {{ background:color-mix(in oklab, var(--bg) 25%, var(--fg)); grid-column:1 / -1 }}
h1 {{ font:800 clamp(26px, 4vw, 34px)/1.1 var(--display); margin:4px 0 0; letter-spacing:-.015em; text-wrap:balance }}
.top {{ display:flex; flex-wrap:wrap; gap:16px; align-items:end; justify-content:space-between }}
.top > div {{ min-width:0 }}
.next {{ display:grid; gap:4px; padding:12px 16px; border-radius:10px; background:var(--tint);
  border:1px solid color-mix(in oklab, var(--accent) 35%, var(--line)); color:var(--fg); text-decoration:none; min-width:0; max-width:100% }}
.next span {{ color:var(--accent) }}
.next b {{ font:700 16px/1.3 var(--display) }}
a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px }}
.tabs-wrap {{ overflow-x:auto; position:sticky; top:env(safe-area-inset-top, 0px); z-index:5; background:var(--bg); padding-block:8px; border-bottom:1px solid var(--line) }}
body::before {{ content:""; position:fixed; inset:0 0 auto; height:env(safe-area-inset-top, 0px); z-index:10; background:var(--bg) }}
.tabs {{ display:flex; gap:4px; width:max-content }}
.tabs a {{ display:flex; align-items:center; gap:6px; padding:8px 12px; border-radius:8px; color:var(--muted); text-decoration:none;
  font:600 13px var(--mono); font-variant-numeric:tabular-nums; white-space:nowrap }}
.tabs a:hover {{ background:var(--surface); color:var(--fg) }}
.tabs a[aria-selected="true"] {{ background:var(--fg); color:var(--bg) }}
.dot {{ width:8px; height:8px; border-radius:50%; background:var(--sc) }}
.pill {{ display:inline-block; font:600 11px/1 var(--mono); letter-spacing:.04em; text-transform:uppercase; padding:5px 8px; border-radius:99px;
  color:var(--sc); background:color-mix(in oklab, var(--sc) 14%, transparent); white-space:nowrap }}
.s-ready-for-agent {{ --sc:var(--s-agent) }} .s-ready-for-human {{ --sc:var(--s-human) }} .s-needs-info {{ --sc:var(--s-info) }}
.s-needs-triage {{ --sc:var(--s-triage) }} .s-claimed {{ --sc:var(--s-claimed) }} .s-resolved {{ --sc:var(--s-done) }} .s-wontfix {{ --sc:var(--s-triage) }}
.chip {{ font:12px var(--mono); color:var(--muted); border:1px solid var(--line); padding:3px 7px; border-radius:6px; max-width:100%; overflow-wrap:anywhere }}
.chip.block.wait {{ color:var(--s-human); border-color:color-mix(in oklab, var(--s-human) 40%, var(--line)) }}
.chip.block.met {{ color:var(--s-done) }}
.track {{ height:6px; border-radius:99px; background:var(--line); overflow:hidden }}
.track i {{ display:block; height:100%; background:var(--s-done) }}
.panel {{ display:grid; gap:32px; scroll-margin-top:80px }}
.plan {{ display:grid; gap:14px }}
.plan ol {{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:12px; counter-reset:p }}
.plan li {{ counter-increment:p; border-top:2px solid var(--fg); padding-top:10px; min-width:0 }}
.plan h4 {{ margin:0 0 4px; font:700 16px/1.25 var(--display); text-wrap:balance }}
.plan h4::before {{ content:counter(p) " "; font:600 12px var(--mono); color:var(--accent); vertical-align:2px }}
.plan p {{ margin:0; color:var(--muted); font-size:14px }}
.wave {{ display:grid; grid-template-columns:190px 1fr; gap:20px; border-top:1px solid var(--line); padding-top:20px }}
.rail {{ display:grid; gap:4px; align-content:start }}
.wn {{ color:var(--accent) }}
.rail h2 {{ font:800 21px/1.15 var(--display); margin:0; text-wrap:balance }}
.wc {{ font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(min(100%, 290px), 1fr)); gap:12px; min-width:0 }}
.card {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:14px 16px; display:grid; grid-template-columns:minmax(0, 1fr); gap:10px; align-content:start;
  min-width:0; color:inherit; text-decoration:none; transition:border-color .15s }}
.card:hover {{ border-color:var(--accent) }}
.card.is-next {{ border-color:var(--accent); box-shadow:0 0 0 1px var(--accent) }}
.card.s-resolved, .card.s-wontfix {{ opacity:.7 }}
.card header, .th {{ display:flex; gap:10px; align-items:baseline }}
.num {{ font:600 13px var(--mono); color:var(--muted); font-variant-numeric:tabular-nums }}
.card h3 {{ margin:0; font:700 16px/1.3 var(--display); text-wrap:balance; overflow-wrap:anywhere }}
.goal {{ margin:0; font-size:14px; color:var(--muted) }}
.meta {{ display:flex; flex-wrap:wrap; gap:6px; align-items:center }}
.side {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; border-top:1px solid var(--line); padding-top:20px }}
.side ul {{ margin:8px 0 0; padding-left:18px; display:grid; gap:4px; color:var(--muted); font-size:14px }}
.side > div {{ min-width:0 }}
.tp .th {{ align-items:flex-start; gap:16px }}
.num.big {{ font:600 34px/1 var(--mono); color:var(--accent) }}
.tp h2 {{ margin:0 0 8px; font:800 clamp(22px, 3.4vw, 30px)/1.15 var(--display); text-wrap:balance; overflow-wrap:anywhere }}
.tgrid {{ display:grid; grid-template-columns:1.6fr 1fr; gap:24px }}
.col {{ display:grid; gap:20px; align-content:start; min-width:0 }}
.block {{ display:grid; gap:10px }}
dl {{ margin:0; display:grid; gap:8px }}
.b {{ display:grid; grid-template-columns:64px 1fr; gap:8px }}
dt {{ font:600 11px/1.9 var(--mono); text-transform:uppercase; letter-spacing:.06em; color:var(--muted) }}
dd {{ margin:0; min-width:0 }}
.prow {{ display:flex; justify-content:space-between; font-size:13px; color:var(--muted); font-variant-numeric:tabular-nums }}
.prow b {{ color:var(--fg) }}
.steps {{ list-style:none; margin:0; padding:0; display:grid; gap:2px; border:1px solid var(--line); border-radius:10px; background:var(--surface) }}
.steps li {{ display:flex; gap:12px; align-items:center; padding:10px 14px; border-top:1px solid var(--line) }}
.steps li:first-child {{ border-top:0 }}
.box {{ flex:none; width:18px; height:18px; border-radius:5px; border:1.5px solid var(--line); display:grid; place-items:center; font:700 12px var(--body) }}
.steps li.done .box {{ background:var(--s-done); border-color:var(--s-done); color:var(--surface) }}
.sr {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0) }}
.stats {{ display:grid; gap:12px; background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:16px }}
.stats > div {{ display:grid; gap:2px }}
.stats b {{ font:700 19px var(--display); font-variant-numeric:tabular-nums }}
.stats small {{ color:var(--muted); font-size:13px }}
.note h4 {{ margin:0 0 4px; font:600 12px var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--muted) }}
.note p {{ margin:0; font-size:14px }}
.banner {{ display:grid; gap:2px; border:1px solid color-mix(in oklab, var(--s-late) 45%, var(--line)); background:color-mix(in oklab, var(--s-late) 9%, var(--surface)); border-radius:10px; padding:12px 16px }}
.banner b {{ font:600 12px var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--s-late) }}
.chip.human {{ color:var(--s-late); border-color:color-mix(in oklab, var(--s-late) 45%, var(--line)) }}
.chip.review {{ color:var(--s-agent) }} .chip.review.warn {{ color:var(--s-human) }} .chip.review.late {{ color:var(--s-late); font-weight:600 }}
.hm {{ display:inline-grid; place-items:center; width:16px; height:16px; border-radius:50%; background:var(--s-late); color:var(--surface); font:700 11px var(--body) }}
.tabs a[aria-selected="true"] .hm {{ background:var(--bg); color:var(--s-late) }}
.humans {{ border:1px solid color-mix(in oklab, var(--s-late) 40%, var(--line)); border-radius:12px; background:color-mix(in oklab, var(--s-late) 5%, var(--surface)) }}
.humans summary {{ display:flex; align-items:center; gap:12px; padding:14px 16px; border-radius:12px; cursor:pointer; list-style:none }}
.humans summary::-webkit-details-marker {{ display:none }}
.humans summary::after {{ content:""; margin-left:auto; width:7px; height:7px; border:solid var(--s-late); border-width:0 2px 2px 0; transform:translateY(-2px) rotate(45deg); transition:transform .15s }}
.humans[open] summary::after {{ transform:translateY(2px) rotate(-135deg) }}
.humans summary:focus-visible {{ outline:2px solid var(--s-late); outline-offset:2px }}
.prs {{ border:1px solid var(--line); border-radius:12px; background:var(--surface); padding:14px 16px; display:grid; gap:10px }}
.prs-head {{ display:flex; align-items:center; gap:12px }} .prs h2 {{ font:600 12px var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 }}
.copy-prs {{ margin-left:auto; font:600 12px var(--body); color:var(--surface); background:var(--accent); border:0; border-radius:8px; padding:6px 12px; cursor:pointer }}
.prlist {{ margin:0; font:13px/1.6 var(--mono); white-space:pre-wrap; overflow-wrap:anywhere; user-select:all }}
.humans h2, .runbook h2, .intake h2 {{ font:600 12px var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:0 }}
.humans h2 {{ color:var(--s-late) }}
.humans ul {{ list-style:none; margin:0; padding:0 16px 16px; display:grid; gap:8px }}
.humans li {{ display:grid; grid-template-columns:minmax(0, 18em) 1fr; gap:4px 16px; font-size:14px }}
.humans li a {{ color:var(--fg); font-weight:600; text-decoration:none }} .humans li a:hover {{ text-decoration:underline }}
.humans li > span {{ color:var(--muted); min-width:0 }}
.runbook {{ display:grid; gap:10px }}
.runbook ol {{ margin:0; padding:0; list-style:none; counter-reset:r; display:grid; grid-template-columns:repeat(auto-fill, minmax(min(100%, 210px), 1fr)); gap:8px }}
.runbook li {{ counter-increment:r; display:flex; gap:10px; align-items:baseline; background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:8px 12px; font-size:14px; min-width:0 }}
.runbook li::before {{ content:counter(r); font:600 12px var(--mono); color:var(--accent); font-variant-numeric:tabular-nums; min-width:1.5em }}
.intake {{ display:grid; gap:10px; border-top:1px solid var(--line); padding-top:20px }}
.intake p {{ margin:0; color:var(--muted); font-size:14px }}
.ticket-form {{ display:grid; gap:6px; max-width:640px }}
.ticket-form label {{ font:600 12px var(--mono); color:var(--muted) }}
.ticket-form input, .ticket-form textarea, .note-form textarea {{ font:14px/1.4 var(--body); color:var(--fg); background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:8px 10px; min-width:0 }}
.ticket-form button, .note-form button {{ justify-self:start; font:600 13px var(--body); color:var(--surface); background:var(--accent); border:0; border-radius:8px; padding:9px 14px; cursor:pointer }}
.ticket-form :focus-visible, .note-form :focus-visible, .ghost:focus-visible {{ outline:2px solid var(--accent); outline-offset:1px }}
.reqlist, .notelist {{ list-style:none; margin:0; padding:0; display:grid; gap:6px }}
.reqlist li, .notelist li {{ border-left:2px solid var(--accent); padding:2px 0 2px 10px; font-size:14px; white-space:pre-wrap; overflow-wrap:anywhere }}
.reqlist .who, .notelist .who {{ display:block; font:12px var(--mono); color:var(--muted); white-space:normal }}
.note-form {{ display:grid; grid-template-columns:1fr auto; gap:8px; align-items:end }}
.ghost {{ justify-self:start; font:600 13px var(--body); color:var(--accent); background:transparent; border:1px solid var(--line); border-radius:8px; padding:8px 12px; cursor:pointer }}
.steps li.na > span:nth-child(3) {{ color:var(--muted) }}
.steps li.na .box {{ border-style:dashed; color:var(--muted) }}
.sn {{ font:600 12px var(--mono); color:var(--muted); min-width:1.6em; font-variant-numeric:tabular-nums }}
.small {{ font:600 14px/1.4 var(--body) !important; overflow-wrap:anywhere }}
.small a {{ color:var(--accent) }}
.steps li.done > span:nth-child(3) {{ color:var(--muted); text-decoration:line-through; text-decoration-color:var(--line) }}
.orig {{ display:grid; gap:6px; min-width:0 }}
.orig h4 {{ margin:0; font:700 15px/1.3 var(--display); overflow-wrap:anywhere }}
.orig-body {{ white-space:pre-wrap; overflow-wrap:anywhere; font:13px/1.5 var(--mono); color:var(--fg); background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:12px 14px; max-height:28rem; overflow:auto }}
.orig-body:focus-visible {{ outline:2px solid var(--accent); outline-offset:1px }}
.done-tab {{ margin-left:8px; border:1px dashed var(--line) }}
.qs {{ list-style:none; margin:0; padding:0; display:grid; gap:10px }}
.q {{ background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:12px 14px; display:grid; gap:8px }}
.qt {{ margin:0; font-weight:600 }}
.answers {{ list-style:none; margin:0; padding:0; display:grid; gap:6px }}
.answers li {{ border-left:2px solid var(--s-done); padding:2px 0 2px 10px; font-size:14px; white-space:pre-wrap; overflow-wrap:anywhere }}
.answers .who {{ display:block; font:12px var(--mono); color:var(--muted); white-space:normal }}
.answer-form {{ display:grid; grid-template-columns:1fr auto; gap:8px; align-items:end }}
.answer-form textarea {{ font:14px/1.4 var(--body); color:var(--fg); background:var(--bg); border:1px solid var(--line); border-radius:8px; padding:8px 10px; resize:vertical; min-width:0 }}
.answer-form textarea:focus-visible, .answer-form button:focus-visible {{ outline:2px solid var(--accent); outline-offset:1px }}
.answer-form button {{ font:600 13px var(--body); color:var(--surface); background:var(--accent); border:0; border-radius:8px; padding:9px 14px; cursor:pointer }}
.answer-form button:disabled {{ opacity:.6; cursor:default }}
.form-msg {{ grid-column:1 / -1; font-size:13px; color:var(--muted) }}
.form-msg:empty {{ display:none }}
.hint {{ margin:0; font-size:13px; color:var(--muted) }}
.log {{ list-style:none; margin:0; padding:0; display:grid; gap:0; border-left:2px solid var(--line); margin-left:6px }}
.log li {{ display:grid; grid-template-columns:96px 1fr; gap:10px; padding:6px 0 6px 14px; position:relative; font-size:14px }}
.log li::before {{ content:""; position:absolute; left:-6px; top:12px; width:10px; height:10px; border-radius:50%; background:var(--surface); border:2px solid var(--accent) }}
.log time {{ font:12px/1.9 var(--mono); color:var(--muted); font-variant-numeric:tabular-nums }}
.log span {{ min-width:0 }}
footer {{ color:var(--muted); font-size:13px }}
@media (max-width:760px) {{ .wave, .side, .tgrid, .eta, .humans li {{ grid-template-columns:1fr }} .answer-form, .note-form {{ grid-template-columns:1fr }} .log li {{ grid-template-columns:1fr; gap:0 }} }}
@media (prefers-reduced-motion: reduce) {{ .card, .humans summary::after {{ transition:none }} }}
</style>
<div class="wrap">
  <section class="eta" aria-label="Estimated completion">
    <div><span class="lbl">Estimated completion · padded 2x</span>
      <div class="date">{fmt(eta_hi)}, {eta_hi.year}</div>
      <p>Earliest likely is {fmt(eta_lo)} at 1.5x padding. Tickets ship one at a time, top wave first. The date moves as steps get ticked off, and slips if nothing moves.</p></div>
    <dl>
      <div><dt class="lbl">Tickets done</dt><dd>{done_n} / {len(tickets)}</dd></div>
      <div><dt class="lbl">Work done</dt><dd>{pct}%</dd></div>
      <div><dt class="lbl">Base estimate</dt><dd>{base_total:g} d</dd></div>
      <div><dt class="lbl">Left, padded</dt><dd>{base_left*PAD_LO:.1f} to {base_left*PAD_HI:.1f} d</dd></div>
      {bar(1 - base_left / base_total if base_total else 0)}
    </dl>
  </section>
  <div class="top">
    <div><span class="eyebrow">{e(EYEBROW)} · living doc · as of {today.isoformat()}</span>
      <h1>{e(TITLE)}</h1></div>
    {next_html}
  </div>
  <div class="tabs-wrap"><nav class="tabs" role="tablist" aria-label="Tickets">{tabs}</nav></div>
  {overview}
  {done_panel}
  {"".join(ticket_panel(t) for t in order)}
  <footer>Working days only, skipping weekends and US holidays. Estimates exclude the items each ticket lists as not in the estimate. Rendered from the ticket files on {today.isoformat()}.</footer>
</div>
<script>
(function () {{
  var cp = document.querySelector(".copy-prs"), pl = document.querySelector(".prlist");
  if (cp) cp.addEventListener("click", function () {{
    function sel() {{ var r = document.createRange(); r.selectNodeContents(pl); var s = getSelection(); s.removeAllRanges(); s.addRange(r); cp.textContent = "Press ⌘C"; }}
    try {{ navigator.clipboard.writeText(pl.textContent).then(function () {{ cp.textContent = "Copied"; }}, sel); }} catch (x) {{ sel(); }}
  }});
}})();
(function () {{
  var panels = Array.prototype.slice.call(document.querySelectorAll(".panel"));
  var tabs = Array.prototype.slice.call(document.querySelectorAll('[role="tab"]'));
  function show() {{
    var id = (location.hash || "#overview").slice(1);
    if (!document.getElementById(id) || !document.getElementById(id).classList.contains("panel")) id = "overview";
    panels.forEach(function (p) {{ p.hidden = p.id !== id; }});
    tabs.forEach(function (t) {{
      var p = document.getElementById(id);
      var on = t.getAttribute("aria-controls") === id || (t.id === "tab-done" && p && p.dataset.done === "1");
      t.setAttribute("aria-selected", on ? "true" : "false");
      if (on && t.scrollIntoView) t.scrollIntoView({{ block: "nearest", inline: "nearest" }});
    }});
  }}
  window.addEventListener("hashchange", function () {{
    show();
    // Coming from further down (a long Waiting-on-a-human list), land on the panel's top, under the sticky tabs.
    var w = document.querySelector(".tabs-wrap"), p = document.querySelector(".panel:not([hidden])");
    if (w && p && p.getBoundingClientRect().top < w.getBoundingClientRect().bottom) p.scrollIntoView();
  }});
  show();
}})();
(async function () {{
  if (!window.claude || !window.claude.use) return;
  var db = await window.claude.use("db"); var user = await window.claude.use("user");
  var comments = await window.claude.use("comments");
  if (comments) document.querySelectorAll(".comment-btn").forEach(function (b) {{
    b.hidden = false;
    b.addEventListener("click", function () {{ comments.openComposer({{ element: b.closest(".panel") }}).catch(function () {{}}); }});
  }});
  if (!db) return;
  var canWrite = user && user.can ? await user.can("data.write") : null;
  var me = user && user.id ? await user.id() : null;
  async function names(ids) {{ try {{ return (user && user.profiles && ids.length) ? await user.profiles(ids) : {{}}; }} catch (e) {{ return {{}}; }} }}
  function item(a, ps) {{
    var li = document.createElement("li"); li.textContent = a.title ? a.title + "\\n" + (a.text || "") : a.text;
    var who = document.createElement("span"); who.className = "who";
    who.textContent = ((ps[a.by] && ps[a.by].name) || (a.by && a.by === me ? "You" : "Someone")) + " · " + String(a.at || "").slice(0, 16).replace("T", " ") + " UTC";
    li.appendChild(who); return li;
  }}
  function wire(form, onSubmit) {{
    if (canWrite === false) return false;
    form.hidden = false;
    form.addEventListener("submit", async function (ev) {{
      ev.preventDefault();
      var btn = form.querySelector("button"), msg = form.querySelector(".form-msg");
      btn.disabled = true; msg.textContent = "Saving…";
      try {{ var ok = await onSubmit(); msg.textContent = ok === false ? "Write something first." : "Saved. Thanks!"; }}
      catch (e) {{ if (e && e.code === "invalid_argument") {{ form.hidden = true; msg.textContent = ""; }} else msg.textContent = "Couldn't save. Check your connection and try again."; }}
      finally {{ btn.disabled = false; }}
    }});
    return true;
  }}
  document.querySelectorAll(".notes").forEach(function (box) {{
    var form = box.querySelector(".note-form"), ta = form.querySelector("textarea");
    wire(form, async function () {{ var v = ta.value.trim(); if (!v) return false;
      await db.collection("notes").add({{ ticket: box.dataset.ticket, text: v, by: me, at: new Date().toISOString() }}); ta.value = ""; }});
  }});
  db.collection("notes").onSnapshot(async function (snap) {{
    var by = {{}}, ids = [];
    snap.docs.forEach(function (d) {{ var a = d.data(); if (!a || typeof a.ticket !== "string" || typeof a.text !== "string") return;
      (by[a.ticket] = by[a.ticket] || []).push(a); if (a.by && ids.indexOf(a.by) < 0) ids.push(a.by); }});
    var ps = await names(ids);
    document.querySelectorAll(".notes").forEach(function (box) {{
      var ul = box.querySelector(".notelist"); ul.textContent = "";
      (by[box.dataset.ticket] || []).sort(function (x, y) {{ return String(x.at).localeCompare(String(y.at)); }}).forEach(function (a) {{ ul.appendChild(item(a, ps)); }});
    }});
  }}, function () {{}});
  var tf = document.querySelector(".ticket-form");
  if (tf) {{
    var ti = tf.querySelector("#nt-title"), tb = tf.querySelector("#nt-body");
    if (!wire(tf, async function () {{ var a = ti.value.trim(), b = tb.value.trim(); if (!a) return false;
        await db.collection("requests").add({{ title: a, text: b, by: me, at: new Date().toISOString(), status: "new" }}); ti.value = ""; tb.value = ""; }}))
      document.querySelector(".intake-hint").hidden = false;
    db.collection("requests").onSnapshot(async function (snap) {{
      var rows = [], ids = [];
      snap.docs.forEach(function (d) {{ var a = d.data(); if (!a || typeof a.title !== "string" || a.status === "ticketed") return; rows.push(a); if (a.by && ids.indexOf(a.by) < 0) ids.push(a.by); }});
      var ps = await names(ids), ul = document.querySelector(".reqlist"); ul.textContent = "";
      rows.sort(function (x, y) {{ return String(x.at).localeCompare(String(y.at)); }}).forEach(function (a) {{ ul.appendChild(item(a, ps)); }});
    }}, function () {{}});
  }}
}})();
(async function () {{
  var qEls = document.querySelectorAll(".q");
  if (!qEls.length || !window.claude || !window.claude.use) return;
  var db = await window.claude.use("db"); var user = await window.claude.use("user");
  if (!db) return;
  var canWrite = user && user.can ? await user.can("data.write") : null;
  var me = user && user.id ? await user.id() : null;
  var forms = document.querySelectorAll(".answer-form");
  if (canWrite === false) {{ document.querySelectorAll(".hint").forEach(function (h) {{ h.hidden = false; }}); }}
  else forms.forEach(function (f) {{ f.hidden = false; }});
  var byQ = {{}};
  async function render() {{
    var ids = []; Object.keys(byQ).forEach(function (k) {{ byQ[k].forEach(function (a) {{ if (a.by && ids.indexOf(a.by) < 0) ids.push(a.by); }}); }});
    var ps = {{}}; try {{ if (user && user.profiles && ids.length) ps = await user.profiles(ids); }} catch (e) {{}}
    qEls.forEach(function (q) {{
      var ul = q.querySelector(".answers"); ul.textContent = "";
      (byQ[q.dataset.qid] || []).forEach(function (a) {{
        var li = document.createElement("li"); li.textContent = a.text;
        var who = document.createElement("span"); who.className = "who";
        var nm = (ps[a.by] && ps[a.by].name) || (a.by && a.by === me ? "You" : "Someone");
        who.textContent = nm + " · " + (a.at || "").slice(0, 16).replace("T", " ") + " UTC";
        li.appendChild(who); ul.appendChild(li);
      }});
    }});
  }}
  db.collection("answers").onSnapshot(function (snap) {{
    byQ = {{}};
    snap.docs.forEach(function (d) {{ var a = d.data(); if (!a || typeof a.qid !== "string" || typeof a.text !== "string") return;
      (byQ[a.qid] = byQ[a.qid] || []).push(a); }});
    Object.keys(byQ).forEach(function (k) {{ byQ[k].sort(function (x, y) {{ return String(x.at).localeCompare(String(y.at)); }}); }});
    render();
  }}, function () {{}});
  forms.forEach(function (f) {{
    f.addEventListener("submit", async function (ev) {{
      ev.preventDefault();
      var q = f.closest(".q"), ta = f.querySelector("textarea"), btn = f.querySelector("button"), msg = f.querySelector(".form-msg");
      var text = ta.value.trim(); if (!text) {{ msg.textContent = "Write an answer first."; return; }}
      btn.disabled = true; msg.textContent = "Posting…";
      try {{
        await db.collection("answers").add({{ qid: q.dataset.qid, text: text, by: me, at: new Date().toISOString() }});
        ta.value = ""; msg.textContent = "Posted. Thanks!";
      }} catch (e) {{
        if (e && e.code === "invalid_argument") {{ f.hidden = true; var h = q.closest(".block").querySelector(".hint"); if (h) h.hidden = false; }}
        else msg.textContent = "Couldn't post. Check your connection and try again.";
      }} finally {{ btn.disabled = false; }}
    }});
  }});
}})();
</script>
'''
out.write_text(page)
print(f"wrote {out}: {len(tickets)} tickets, base {base_total:g}d, ETA {eta_lo} (1.5x) .. {eta_hi} (2x), next {frontier['num'] if frontier else '-'}")
