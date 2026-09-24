# Phase 1 — Manifest

**First move — `python3 .neopilot/sync.py --enter manifest`, before any work below.** A stage entered after its work records zero minutes and reads on the dashboard as skipped.

The brief is the only thing in this whole process the user actually authored. Everything downstream is your paraphrase of it. This phase turns it into an artifact that survives every later rewrite, so that nothing can quietly stop existing.

Runs **before** the briefing questions. The questions are themselves a re-encoding of the brief — the anchor has to be dropped first.

## 1. Redaction gate — runs before anything is written

Every piece of user text — the brief, every answer, every pasted fragment — passes this gate on its way to a file, a prompt, or the dashboard. Nothing bypasses it.

Scan for:

| Kind | Shape |
|---|---|
| Stripe / OpenAI-style | `sk-…`, `sk_live_…`, `sk_test_…`, `rk_live_…`, `pk_live_…` |
| GitHub | `ghp_…`, `gho_…`, `ghs_…`, `github_pat_…` |
| AWS | `AKIA…`, `ASIA…` |
| Google | `AIza…`, `ya29.…` |
| Slack | `xoxb-…`, `xoxp-…`, `xoxa-…` |
| Telegram bot | 8–10 digits, colon, 35 chars of `[A-Za-z0-9_-]` |
| JWT | `eyJ…` followed by a dot and more base64 |
| Connection string | `<scheme>://<user>:<something>@<host>` |
| Private key | `-----BEGIN … PRIVATE KEY-----` |
| Generic | ≥32 chars of hex or base64 sitting next to `key`, `token`, `secret`, `password`, `access` |

On a hit:

1. Replace the value with `[REDACTED:<VAR_NAME>]`, inventing the conventional variable name for that provider (`STRIPE_SECRET_KEY`, `TELEGRAM_BOT_TOKEN`, `DATABASE_URL`). The name is what the build needs; the value never was.
2. Add the name to `.env.example` with an empty value.
3. Tell the user immediately, in one line, in plain language: "You sent a Stripe key — I didn't save it. Enter it into `.env` yourself, and it's better to revoke this one and issue a new one: it's already been through correspondence."
4. Carry on. A redacted secret does not block the flight.

**Never echo the value back**, not even to confirm what you found. Naming the provider is enough.

Before the first commit, run this gate over everything under `.neopilot/`. A secret that got in through some path nobody predicted still must not reach git history.

## 2. Write the brief file

The redacted brief, **word for word**, into `.neopilot/<dir>/<YYYY-MM-DD>-brief.md` — today's date, then `-brief.md`: `2026-08-07-brief.md`. The date is part of the name because a slug directory outlives one sitting; a month later "finish this too" arrives, and the files have to say which brief came when. Record the chosen name in `state.js` as `briefFile`, so nothing downstream has to guess it.

```markdown
# Original task

> Recorded <date>. The task text is never edited — it is the benchmark the
> finished result is checked against. Everything said later is appended
> in "Additions" below.

<all of the user's text, verbatim, after secret redaction>

## Additions

- <date> — "no SMS, Telegram only"
- <date> — "and make it possible to cancel a request within an hour"
```

Rules that make this file worth having:

- **No paraphrase, no cleanup, no reordering.** Bad grammar, contradictions, half-sentences and duplicated thoughts all stay. A tidied brief is already a spec, and a spec is the thing you cannot check against.
- **Everything counts as brief** — the idea, the asides, the constraints, the "and it'd be nice if", the stack preference, the deadline mentioned in passing.
- **The text above is never edited — but the file goes on growing.** Everything the user says after it, for as long as the run lasts, is appended under `## Additions`: dated, word for word, never merged into the text above. A cancellation, an addition, a decision reversed at ticket four — all of it, not only the afterthoughts of the first sitting.

  This is the rule the rest of the framework leans on, and the easiest one to skip, because the manifest row does get updated and that feels like enough. It is not. **The manifest is your reading of the task, and both independent gates are forbidden to read it** — G2 gets the brief and the spec, G4 gets the brief and the repository, and neither is allowed anything else (`phases/3-spec.md`, `phases/8-final.md`). A change that reaches the manifest and not this file is a change the two checks capable of catching a loss will never hear about: the cancelled requirement comes back as a false "not implemented", and the thing the user asked for at ticket four is either reported as scope you invented or — if it never got built — noticed by nobody at all.

  A brief dictated on a **later day** is a new file with that day's date — appending it to an older one erases the fact that the project was asked for twice.

## 3. Atomise into requirements

Split the brief into the smallest units that can independently be true or false about the finished product. Write `.neopilot/<dir>/manifest.md`.

Every requirement is a row, and every row carries the **exact words it came from**. The quote is the point — a paraphrased requirement drifts exactly like a paraphrased brief.

```markdown
# Requirements manifest

Source: `<date>-brief.md`. A row in this list can be dropped **only by the user**.

| ID | From the brief (verbatim) | Status | Basis | Where |
|----|---------------------------|--------|-------|-------|
| R01 | "accepts repair service requests" | in-ticket | — | spec §2 → T02 |
| R02 | "saves them into a Google Sheet" | in-ticket | — | spec §4 → T05 |
| R03 | "so the client can see the status" | in-spec | — | spec §6 |
| R04 | "and also send via SMS" | dropped | user: "no SMS, Telegram only" | — |
| R05 | "the studio's brand colours" | placeholder | colours not provided | report |
| R06i | *(implied)* someone has to read the requests | deferred | Out of Scope §9: no admin panel in the brief | report |
```

### Statuses

| Status | Meaning | Who may set it |
|---|---|---|
| `open` | not yet resolved anywhere | initial state |
| `in-spec` | landed in the spec, section noted | you |
| `in-ticket` | a ticket exists that delivers it | you |
| `done` | built and reviewed, commit noted | you |
| `placeholder` | in the build, but with a stub where a user fact belongs | you |
| `deferred` | consciously postponed, listed in the spec's Out of Scope with a reason | you |
| `dropped` | **cancelled by the user** | **the user, never you** |

Three rules bind these, and they are the reason this file exists:

- **`dropped` requires a quote.** The Basis column holds the user's own words cancelling it. No quote, no drop. You may *propose* dropping something — that is a briefing question, not a status change.
- **`deferred` is not `dropped`.** Postponing is yours to decide; cancelling is not. Every `deferred` row appears in the final report under "what didn't make it in", so the user learns about it while the project is still fresh.
- **Silence never cancels anything.** A requirement the user stopped mentioning is still live. Forgetting and deciding must not look alike.

The dashboard's "Requirements" card counts this table itself — `sync.py` recounts `requirements` from the status column on every call, so keeping the column true is the whole job; there are no numbers to write by hand and nothing to forget.

### Implicit requirements

Mark with a trailing `i` (`R06i`) anything the brief clearly *implies* but never says — "accepts requests" implies somewhere to read them; "online store" implies a way to pay.

These are the most dangerous items in the whole flight: too obvious to state, too big to skip. Route them to the briefing as questions rather than inventing or ignoring them. In **full** mode they become explicit `ASSUMPTION` decisions and appear in the report.

### Discovered constraints

Mark with `D` (`D01`, `D02`) anything the **build** proved that the plan did not know — a data model that does not hold, an assumed interface that cannot exist, two requirements that collide in practice. Its Basis is the finding itself, and it names the requirement it serves.

After the briefing, a `D##` row is the only thing **you** may add to the manifest, and only from `phases/5-repair.md` — the one other way it can grow is a `G##` the user themselves asked for, per `phases/2-briefing.md`. A `D##` is not a requirement the user made and it never replaces one: a requirement the code proves impossible is a question for the user, not a `D##` that quietly retires it. An idea you had while building is not a discovery either — that is an `A##`, and it lives in the spec under the usual parent-and-proportion rules.

### How fine to cut

One requirement = one thing that can be independently true or false.

- "a Telegram bot that accepts requests and saves them into a spreadsheet" → **two** requirements. One can work while the other doesn't.
- "a beautiful modern design" → **one**, and it is inherently untestable — mark it and let the briefing turn it into something checkable, or let it stay a stated matter of taste.
- A 2000-word brief usually yields 25–50 rows. Under 10 from a long brief means you summarised instead of atomising — redo it.

## 4. Report the manifest in one line

"Broke the task down into 23 requirements — keeping them under control to the very end." No table in the chat. The file is the artifact; the chat is a mention of it.

## The gates

Recorded here because they all read this file. A failed gate is not a warning — the phase is redone.

**G1 — after the briefing.** Every requirement has a status. Anything still `open` must have a recorded reason (unreachable user, question deferred). In **full** mode nothing may be `open`: the self-briefing answers everything or marks it `placeholder`.

**G2 — after the spec.** Two halves, both mandatory, per `phases/3-spec.md`.

- *Your own pass* — zero `open`. Every live requirement is `in-spec`, `deferred`, or `dropped`, with its spec section noted. **An `open` row means the spec is incomplete** — rewrite the spec, do not proceed.
- *The independent pass* — a subagent given the brief and the spec, and **not** this file, reports what the spec fails to cover. You wrote the spec, so you cannot see what you did not write; this file makes the loss findable, not you the one who finds it.

This is the gate that would have caught every drift you have ever seen, and the second half is why.

**G3 — after the plan.** Two directions, both mandatory:

- *Forward* — every `in-spec` requirement maps to at least one ticket. A requirement with no ticket will not get built.
- *Backward* — every ticket traces to at least one requirement or to a spec decision that traces to one. **A ticket tracing to nothing is work nobody ordered** — cut it or attach it to the requirement it actually serves.

**G4 — at the final phase.** Blind acceptance, per `phases/8-final.md`. Every disagreement between the manifest and the blind verdict goes in the report.

## Keeping it current

The manifest is updated at exactly six moments, never continuously:

| When | What changes |
|---|---|
| after each briefing answer | `open` → `dropped` / clarified / confirmed |
| after the spec is written | `open` → `in-spec` / `deferred`, section noted |
| after tickets are cut | `in-spec` → `in-ticket`, ticket number noted |
| after each ticket lands | `in-ticket` → `done` / `placeholder`, commit noted |
| when the build contradicts the plan | a new `D##` row, and the affected rows re-pointed at the amended spec section |
| when the user changes something mid-flight | the affected row moves — `dropped` with the quote, or a new `G##` — **and the same words go into the brief's `## Additions`** |

The last row is the only one that touches a second file, and that is the point: it is the moment when this table and the brief would otherwise start describing different projects. The procedure for it — all three steps, in order — is in `phases/2-briefing.md`.

Each update is an edit of the affected rows, never a rewrite of the table. The table is short-lived context and long-lived truth; treat it as data, not prose.
