# Phase 8 — Touchdown

**First move — `python3 .neopilot/sync.py --enter final`, before any work below.** A stage entered after its work records zero minutes and reads on the dashboard as skipped.

Landing. Two things happen here, and the first one is the reason this framework exists. A third — the polish loop — happens between them, and only when the `polish` parameter is on.

## 1. Blind acceptance — gate G4

Every check so far has measured the build against the **spec**. But the spec is your own paraphrase of the brief, written several phases ago. If a requirement was lost on the way into it, everything downstream has been faithfully confirming that loss.

So the last check does not use the spec.

**Spawn a subagent that receives:**

- `.neopilot/<dir>/<date>-brief.md` — the user's own words (the directory is `dir` in `state.js`, the filename `briefFile`). **The whole file, `## Additions` included** — what they said at ticket four is as much the task as what they said at the start, and this file is the only place the checker can learn it
- the repository as it now stands
- how to run the project and its tests

**It must not receive:** `spec.md`, `manifest.md`, the tickets, or any summary of them. A checker given the spec inherits the spec's blind spots and will confirm them. Independence is the entire mechanism — take it away and this phase is theatre.

**Not sending them is no longer enough — say it in the prompt.** `.neopilot/` is committed and sits in the repository you just handed over, with a `README.md` explaining what each file is; a checker that opens `spec.md` "to understand the context" has broken the gate without disobeying anything you wrote. One line closes it: **"do not open `.neopilot/` — not the spec, not the manifest, not the tickets; check only against the brief and what actually works"**. The same line belongs in the G2 coverage check (`phases/3-spec.md`) and in the memory agent's prompt below, for the same reason.

Its brief:

> Read the attached brief file — it is the task as the customer stated it. Then examine
> the repository and determine what of it is actually implemented.
>
> If the brief has an "Additions" section — that is what the customer said while
> the work was already running, and it is part of the task on equal footing with the
> main text. Where they disagree the later one is right: nothing cancelled there is
> required, everything added is.
>
> **Run the project** — the commands are in the attached description — and walk the
> main scenario the way the customer would. Reading code shows intention; running
> shows the result. If the project does not start or the scenario breaks off — that
> is the check's main finding, put it first. If it cannot be run at all (it needs an
> account, a key, an external service) — say plainly what exactly blocked it, and do
> not pass code reading off as a functionality check.
>
> For each requirement from the brief: implemented / partial / no — and one line
> on where exactly that is visible (what you saw on launch, or where it is in the
> code, or why you concluded it is not there).
>
> On a separate line return **the commands you used to bring the project up, and
> their result** — verbatim. They are not for you: an agent writing the project's
> memory works alongside you, and without them it will install the same `install`
> a second time.
>
> Do not judge code quality. Do not suggest improvements. Do not look for excuses
> for what is absent — just record the fact. If a requirement is formally met but
> does not actually work (data is saved but never shown to the user) — that is
> "partial", not "implemented".

**Then compare its verdict with `manifest.md`:**

| Manifest says | Blind says | Meaning |
|---|---|---|
| `done` | implemented | agreed |
| `done` | **partial / no** | 🔴 **drift** — the manifest is wrong. Report it; the fix is a ticket or a line in the report, never an edit of your own (§1a) |
| `placeholder` | partial | expected — confirm the placeholder is visible, not an invented fact |
| `dropped` / `deferred` | no | expected — must appear in the report as not built |
| — | implemented, but not from the brief | scope that grew without a parent; report it. With the brief kept current (`phases/2-briefing.md`), a `G##` never lands here — anything that still does is genuinely unordered |

Every 🔴 goes in the report **and** in `state.js` under `blind`. A drift found here is not a failure of the run — it is the run working. Hiding it is the failure.

If there are no tickets (tier T0), this check still runs. Small builds drift too, and it is one subagent.

**A build that was never run is a build nobody has seen work.** The tests were written by the same process that wrote the code, so they agree with it by construction; the first time this project meets a user must not be the first time it is launched. If it genuinely cannot be run here — no credentials, a service that needs an account, a platform this machine is not — that goes in the report as an open item under "what we need from you", not silently into the accepted column.

## 1a. The deferred findings — triaged once, here

Through the build, every Craft finding that was not blocking went into `state.js` under `concerns` instead of into a follow-up (`phases/6-review.md`). **This is where that list gets its one reader.** A deferred-findings list nobody opens is not a deferral, it is a silent discard — and the whole loosening that produced it was justified on the promise that this pass happens.

Read the list — it is `concerns`, in `state.js`, on disk, not from memory — and sort it in one pass:

| Verdict | What it means | What happens |
|---|---|---|
| **Fix now** | it will cost more to leave than to close, and the fix is bounded | a ticket, cut and flown and reviewed like any other — `phases/5-subagents.md` |
| **Report** | real, but not worth holding delivery for | one line in "what didn't go to plan", in the user's language |
| **Drop** | it was a matter of taste, or the code it pointed at no longer exists | struck, with the reason kept in `concerns` |

Two rules keep this honest. **Never fix one yourself** — a concern repaired by the orchestrator skips review and puts a diff into the one context that cannot afford it; it is a ticket or it is a line in the report. And **anything repeated across three or more tickets is promoted to "fix now" regardless of how small it looked** — the same judgement call landing that often is not a judgement call, it is a convention the project never settled, and the next session will meet it on its first day.

At tier T0 there was one context and no tickets, so `concerns` is short and this pass takes a minute. It still runs: the list exists either way.

## 2. What outlives the run — memory and decisions

**Launch these at the same time as the blind acceptance.** Up to three subagents in one slot, no contact between them, each answering a different question:

| Agent | Question | Receives | Never receives |
|---|---|---|---|
| blind checker | what of the brief was built | the brief, the repo | `spec.md`, `manifest.md`, tickets |
| memory | how to use this tomorrow | the repo, `interfaces.md`, the memory file, the tier | `spec.md`, tickets |
| ADR *(tier T2+)* | why it was done exactly this way | `spec.md`, `manifest.md` | the repo — it documents decisions, not code |

The memory agent writes the full description of the project into `CLAUDE.md` or `AGENTS.md` — architecture, key files, conventions, environment, tests, gotchas — scaled to the tier, folding in what `interfaces.md` accumulated. Like the blind checker, **it does not receive `spec.md` or the tickets**: a memory written from the plan documents intentions, and the next session has no way to tell the difference.

The ADR agent is the mirror image and that is why it cannot be the same one. **`spec.md` dies with the run**, and with it every "why this way" in it — the reason for the data model, what the build proved wrong at ticket four, which word the project uses for which thing. Six months later the next session reads working code and no reason for any of it, and re-opens decisions that were settled here. At tier T2+ that is worth three files in `docs/adr/`; below it, the memory file carries what little there is.

Everything about all of this — which memory file, the markers, the sections per tier, what an ADR contains, and the verification pass over the commands — is in `phases/9-memory.md`. Read it before spawning.

This is the artifact that decides what the *next* run costs. A project whose second session begins by re-reading the whole codebase paid for that in the first session and got nothing.

## 2a. Polish — only with `polish` on

If the run has the `polish` parameter, the loop goes **here**: after the blind acceptance has said what is and is not built, and before the report describes the result. Both halves of that matter. The blind verdict is the baseline the regression rule compares against, and a report written before the loop describes a build that no longer exists.

Read `phases/polish.md` now — and only now. On a run without the parameter, skip this section entirely and do not read the file.

Without `polish`, nothing changes: the blind checker's findings go into the report as open items, exactly as below.

## 2b. The `--wip` comes off

The flight has landed, so the directory stops saying it has not. `.neopilot/<YYYY-MM-DD>-<slug>--wip/` loses its suffix and becomes the canonical name it keeps forever (`phases/0-preflight.md` step 1):

```bash
A=$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)/.neopilot
D=2026-08-07-telegram-repair-bot--wip          # `dir` from state.js, verbatim
git -C "$A" mv "$D" "${D%--wip}"
```

**`git mv`, not `mv`.** The directory is committed — a plain rename shows up as a wholesale deletion plus an untracked twin, and the run's record loses its history in the one commit that was supposed to seal it.

**Here, and not after the report.** The report names paths inside that directory (`## Where things live`), and a path that stops existing a minute after the user reads it is a broken path. The rename also has to be inside the final commit, so it goes before the memory file is committed, not after.

Then two writes, both small:

- `dir` in `state.js` → the new name. It is the field every path is built from, and the next session — a polish pass, a "finish this up" a month later — resolves nothing without it.
- the run's row in `.neopilot/README.md` → status "delivered", and the `Outcome` cell filled with **one line of what it delivered**, in the user's language. Not a stage count, not "done": what now exists that did not before. Once the dashboard moves on to the next flight, that row is the only place this run says what it was.

**If the rename fails, the run is not undone by it.** A name already taken by an earlier flight of the same slug, or a dirty index inside the directory — say it in one line, leave the directory as it is, and make `dir` in `state.js` match whatever it is actually called. A landed run wearing a `--wip` is a cosmetic defect; a `dir` pointing at a directory that does not exist breaks every path the next session builds.

## 3. The final report

Run the full test suite once more first — truncated the same way as after every ticket, with the exit code read from `exit=` and not from the tail (`phases/5-subagents.md`, step 5) — and wait for both subagents. Then write in the user's language, plain, no jargon.

**"Wait" is not "wait forever".** A gate agent that dies or never returns gets one respawn — its inputs are all on disk, so a fresh context loses nothing. A second failure is not a reason to hold the landing: the run lands, and the missing check goes into the report as an open item under "what we need from you" — a `blind` that never ran is exactly what the audit's "final stage done, but the blind acceptance is not recorded" flag exists to show.

### Where every line of it comes from

**Re-read the files. Do not write this from memory.**

By this phase your context is the most polluted it has been all run, and most of it has been compacted at least once. The report is the one artifact the user actually reads, and writing it from memory is how a `deferred` requirement gets reported as done, a placeholder disappears, and an `A##` nobody ordered turns up in the summary as though they had asked for it.

So build each section from its source, opened now:

| Section | Read from |
|---|---|
| Decisions made for you | `manifest.md` — every `ASSUMPTION` in Basis |
| Done | the blind checker's return, not the manifest's `done` rows |
| Polish *(only with `polish`)* | `state.js` → `polish`, and `reference.md` for what was compared against |
| What we need from you | `manifest.md` `placeholder` rows + `state.js` → `debt` |
| What didn't make it | `manifest.md` `deferred` and `dropped` rows, with their quotes |
| What I added beyond the order | `state.js` → `additions`, cross-checked against `A##` in the spec |
| What didn't go to plan | every `D##` row in `manifest.md`, plus any ticket whose `handoffs` reached 2 — that is the plan reporting its own coarse cut, and it is the only place the counter is ever read |
| Open questions | `state.js` → `blind`, plus anything in `coverage` that ended up not built |
| Run it / Where things live | `state.js` → `memoryFile`, `briefFile`, and the commands the memory agent verified |

Two of these are worth naming, because memory gets them wrong in a specific direction. **"Done" comes from the blind checker, not from your own bookkeeping** — the manifest says what you believe was delivered, and the whole point of the previous section is that those two can disagree. And **"What didn't make it" comes from the rows, not from recollection**: a requirement dropped in the first ten minutes of a three-hour run is exactly the one you will not remember, and it is quoted in the file.

Order matters — the user reads the top and skims the rest.

**In full mode, the report opens with "Decisions made for you"** — every `ASSUMPTION` from the self-briefing, in plain language, each with the one-line reason. They never asked for these; they have the right to see all of them in one place, first.

```markdown
## Done

<What now works — 3–6 lines of plain language, from the user's point of view.>

**Run it:**
```
npm install && npm run dev
```
Open http://localhost:3000

## What we need from you

1. Fill in `.env` — `TELEGRAM_BOT_TOKEN`, `GOOGLE_SHEETS_ID`.
   The `.env.example` file is already beside it, copy and fill it.
2. Replace the placeholders: prices in `src/data/prices.ts`, email copy
   in `src/emails/`. They currently carry visible `[FILL IN]` marks, not invented values.

## What didn't make it

| What | Why |
|---|---|
| SMS notifications | you said "no SMS, Telegram only" |
| Admin screen for requests | deferred: requests are visible in the spreadsheet, a separate screen is the next pass |

## What I added beyond the order

<Every `A##` story that reached the code — in plain language, with the
requirement it was added for. The section is dropped only if there were
no additions (at `strict` depth — always). The user must learn about
them here, not by stumbling on them in the code.>

| What I added | What for |
|---|---|
| Request number in the confirmation | so the client can refer to it — R01 |

## What didn't go to plan

<Every `D##` row from the manifest — in plain language: what was intended,
what blocked it, and how it was done instead. The section is dropped only if
there were no `D##` rows. The requirement is unchanged — the approach changed,
not the order.>

| What didn't work | How it was done |
|---|---|
| One request per address — half the clients have two | Addresses moved to a list, the form accepts several |

## Open questions

<Discrepancies from the blind acceptance, if any. Directly, without softening:
"The requirement 'client sees status' was counted done; the independent check
showed the status is saved but displayed nowhere. Fixed / needs its own ticket."

Here also goes whatever the spec coverage check found that ended up NOT
built. Anything found and built is not mentioned here: the gate did its job
and there is nothing for the user to do with it.>

## Where things live

- Project description for next time — `AGENTS.md` in the root
- Why it was done this way — `docs/adr/` (if the project is large)
- Progress and numbers — `.neopilot/dashboard.html`
- Your original task — `.neopilot/<date>-<project>/<date>-brief.md`
- Requirements and their fate — `.neopilot/<date>-<project>/manifest.md`
- Specification — `.neopilot/<date>-<project>/spec.md`
- List of all this project's builds — `.neopilot/README.md`
```

## Rules for the report

- **Placeholders and empty variables are a mandatory section**, even when there are none (then one line: "everything filled in"). That is what separates "works" from "works for you".
- **Secrets by name only.** Never values, including ones the user sent themselves.
- **"What didn't make it" is always written**, even when everything made it. An empty section with one line is more honest than a missing one: it shows the question was asked.
- **No embellishment.** A failed test, an unfinished ticket, a discovered discrepancy — named plainly, with what exactly is broken and what fixing needs. A report that hides a defect costs more than the defect.
- **No diffs, no code file names, no test names** — they are in the instruments, for whoever needs them.

## Closing the instruments

The memory file goes in with the final commit, before this. Then, in `state.js` and nowhere else: set `finishedAt`, write the `blind` block, refresh the counts, close every stage — `final` to `done`, and anything still `active` or `pending` to `done`, `skipped` (with a note) or `failed`, whichever is true. A run whose dashboard says "in progress" a day after it landed is lying to the person who trusted it.

The `blind` block is written whole — the acceptance card reads it verbatim:

```json
"blind": { "ranAt": "2026-08-07T18:12:40+03:00", "checked": 23, "matched": 21,
           "mismatches": ["R11 — brief said 'and by SMS', build has Telegram only"] }
```

`checked` is how many brief requirements the checker reached, `matched` how many of them agreed with the manifest, `mismatches` the 🔴 rows one line each (`[]` when clean). A block without the counts renders the card as a bare "/" — the audit flags it, but flagging is not writing.

The open page picks this up by itself within ten seconds — this is the picture the user is left with, and it arrives without you doing anything more.

`finishedAt` also stops the clocks and the ten-second polling: the page freezes on the final numbers instead of counting time nobody is spending. Leave it `null` on a finished run and the user's total keeps growing overnight.

**Sync once more right after writing it** — `python3 .neopilot/sync.py`. This is the write that decides what a landed run looks like six months later: the snapshot inside `dashboard.html` freezes on the final numbers, so the page opens from the archive with the whole flight intact, long after the server is gone. `sync.py` sees `finishedAt` and raises no server for a run that has landed — instead it marks `serve.final` and detaches a `--kill`, so even this section skipped whole cannot orphan the server.

**Then put out the server** — the one Phase 0 started for the pane (`phases/0-instruments.md`). It goes at all because a run that ends leaving an HTTP server on the user's machine has left something running that nobody will ever think to stop.

```bash
A=$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)/.neopilot
( python3 "$A/sync.py" --kill ) >/dev/null 2>&1 &
```

**`--kill` on a landed run waits for the page's fetch, not on a timer.** Every poll the page makes is a `GET /state.js` line in `serve.log`, and `serve.final` marks where the log stood when the last state was written — a fetch past that mark provably carried the final picture. The timer this replaced could prove nothing: the page polls every ten seconds but a throttled background tab polls once a minute, so `sleep 12` still cut the server before the last fetch — and the final `sync.py` used to kill it outright the moment `finishedAt` landed, which is how a pane could freeze on "in progress" with the acceptance card never drawn. The wait is bounded — about 75 seconds — for the pane that will never ask (closed, or `data:`-origin); the snapshot inside `dashboard.html` tells the truth for it. Keep the call in a background subshell: the wait is real time, and run synchronously it would hold the turn while the page is still deciding to ask.

**The kill is `sync.py --kill`, one call — process enumeration has no portable shape.** The shell loop it replaces found servers through `pgrep`/`ps`, and cygwin `ps` cannot see native Windows processes while outside a Unix shell `ps` may not exist at all — which is how a landed run could leave every server standing while looking correct. `sync.py` keeps `.neopilot/serve.pids`, an append-only log addressed from the git root (`phases/0-instruments.md` §3), of every server this run ever raised — a restart or a lost `serve.pid` cannot orphan what it lists, and a shared machine-wide name is still how one run's ending takes down another run's dashboard. **The proof is not ceremony.** A pid file says nothing about the process alive under that number today; an entry is killed only when the process on that port serves `serve.pids` back with its own `port pid` line in it — which no foreign process can produce, on any platform. The npm `http-server` that the old `-m http\.server` pattern existed to protect (measured 2026-08-19, with a user's dev server as the casualty) is safe for a stronger reason than the pattern ever gave.

The pane keeps the final picture on screen — it is already rendered and no longer polling. Nothing is lost with the port: `dashboard.html` carries the final state inside itself, so a double-click reopens it with every number intact — in a real browser, in a pane, on another machine, with no server and no `state.js` anywhere near it. Say nothing about any of this; the shutdown is not news. If polish is running (`phases/polish.md`), the run is not over — the server stays up until the polish closes too.
