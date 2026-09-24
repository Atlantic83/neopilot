# Phase 6 — Checklist

**First move — `python3 .neopilot/sync.py --enter review`, before any work below.** A stage entered after its work records zero minutes and reads on the dashboard as skipped. (Review runs inside the build per ticket, so `build` stays active alongside it — that is by design, not a skipped mark.) The order is enforced, not just advised: `--set tickets.NN.status review` while the stage is still pending prints `! stage review not open`, and the audit flags a ticket sitting on review with the stage never entered.

Review of each ticket's diff along three axes. Not sequential — it runs inside Phase 5, after every ticket.

Three axes, because a change can pass one and fail another:

| Axis | Question | Fails when |
|---|---|---|
| **Manifest** | does the diff deliver what the user asked for, in their words? | a requirement quietly shrank |
| **Spec** | does it implement what the spec decided? | the executor improvised |
| **Craft** | is the code fit to build on? | it works today and blocks tomorrow |

Report them **separately**. Merging or ranking findings across axes lets one mask another — clean code implementing the wrong thing looks fine until you read the axes apart.

## Which axis a finding belongs to

One question decides it: **could the executor have known?**

It saw its ticket, the spec sections that ticket named, and `interfaces.md`. Nothing else.

- **Yes, it could have known** → axis Spec or Craft. This is a defect of the code, and it is fixed in this ticket.
- **No, it could not have known** → axis Manifest. The requirement was lost on the way down, and the defect is in the spec or in the cut — **not in the executor**. It still gets fixed, but do not re-run the subagent against words it was never given: repair the ticket first, or the spec, then run it.

This is the same line the whole framework runs on, seen from close up. Between the gates everything measures against the spec, because the spec is the contract the crew actually received; only at G2 and G4 does anything measure against the brief, and there the subject is the plan, not the code. **The manifest is what lets axis 1 exist at all** — without it the brief is prose and cannot be checked one ticket at a time.

## Scale to the ticket

Delegated from the first ticket. A review that costs more than the ticket is its own kind of waste — and so is a review that quietly spends the one context the run cannot replace.

| Where the run is | How |
|---|---|
| tier T0 — no tickets at all | all three axes yourself, inline: there is nobody to delegate to, and the run ends before it matters |
| every ticket, from the first | Manifest+Spec in one subagent, Craft in another, in parallel |
| the final whole-project pass at the end | separate subagents, per `phases/8-final.md` |

**Inline review is T0 only.** Once there are tickets, you do not read diffs at all (`phases/5-subagents.md`, «Your hands») — and inline review is how the one never-refreshed context fills, one ticket at a time, until ticket 08 is judged by a reader who has been awake since the brief. Ticket 01 is no exception: the shell and the schema are what every later ticket builds on, the worst place for the weakest review.

## The reviewer outlives the ticket

**Do not spawn a new reviewer per ticket.** Keep one for Manifest+Spec and one for Craft, and send each subsequent ticket to the same pair by message. The setup — `interfaces.md`, the spec sections, the manifest rows, the repo's conventions — is most of what a review costs and almost none of what it produces. Paid once per crew, it is cheap. Paid once per ticket, it is the reason reviewing everything felt unaffordable in the first place.

The second gain is the one that is hard to buy any other way. A reviewer that saw ticket 02 can see that ticket 05 quietly contradicts it — a whole class of defect that no per-ticket reviewer can reach, because nothing in its inputs mentions ticket 02 at all. **This is the panoramic view the orchestrator used to have and can no longer afford**, relocated to the one context where accumulation is safe: a reviewer writes nothing, so a tired reviewer misses findings but cannot break the build, and unlike you it can be replaced.

- **Write both handles into `state.js` under `reviewers` when you first spawn them**, and read them from there rather than from memory. This rule is worth exactly as much as your ability to reach the reviewer you kept alive, and that is the one thing a compaction takes away silently: what follows is a fresh reviewer per ticket, working correctly, while the cross-ticket findings quietly stop happening. A missing handle is loud on disk too — sending a ticket to `review`/`repair` while `reviewers` is empty prints `! reviewers not recorded` at `--set` time, and the audit flags the same shape.
- **Refresh it at wave boundaries, or whenever its judgement starts drifting** — repeating findings, hedging, reviewing the previous ticket instead of this one. A fresh reviewer rebuilds everything it needs from `interfaces.md`; the only thing lost is the cross-ticket memory, and that is exactly what has already gone stale.
- **Each reviewer keeps its own axes for the whole run.** Swapping which one holds Manifest halfway through gives you two reviewers with half a picture each.
- **The Craft reviewer is the one worth keeping longest.** Reinvention and divergent change are visible only to someone who remembers what the earlier tickets built.
- **If continuing a subagent is not available in the harness**, fall back to a fresh reviewer per ticket. It works; it just costs what this section exists to avoid, and the cross-ticket findings do not happen at all.
- **A reviewer that cannot be reached — dead context, lost handle, a call that ends without a verdict — is replaced, not waited on.** Spawn a fresh one, write the new handle into `state.js`, and it rebuilds from `interfaces.md` the same way the resume path does (`phases/0-preflight.md`). The cross-ticket memory is lost either way; a ticket parked at `review` forever is the worse outcome.

## What a reviewer gets

A reviewer knows nothing you do not hand it — the same rule as for an executor, and it bites harder here, because **axis Manifest is built entirely out of words the subagent has never seen.** A reviewer sent off with just the diff will quietly review two axes and report three.

| | Manifest + Spec | Craft |
|---|---|---|
| the diff — as a command, not its output: `git add -A` first, so new files are in it, then the reviewer runs `git diff --cached`; plain `git diff` shows neither new files nor staged edits | ✓ | ✓ |
| **the manifest rows the ticket names, with the verbatim brief quotes** | ✓ | — |
| the spec sections the ticket named — the same ones the executor got | ✓ | — |
| `interfaces.md` | ✓ | ✓ — the only way Reinvention is visible |
| the ticket body and its acceptance criteria | ✓ | ✓ |
| whatever the repo documents about how code is written | — | ✓ |
| **`prompts/craft-review.md`, by path** — the smells, the efficiency and robustness misses, the assertion-level testing check with mental mutation, the mental run of the diff with a data-flow map of the most critical criterion, the security pass, the return format. The path is `skillDir` in `state.js` | — | ✓ |
| what it must not do: repair nothing, refactor nothing, open no source code outside the diff to "understand it better" — the material handed over is read in full, and reading what a specific check needs as evidence (a called function, a contract, an existing test, a name lookup for *Reinvention*) is not that | ✓ | ✓ |

**Give each one only its own axes.** A reviewer handed material for an axis it was not asked to judge will judge it anyway, badly and without saying so — and two overlapping half-reviews are what the separation of axes exists to prevent.

**That table is the first ticket only.** A reviewer you are keeping (above) already holds the standing material; from the second ticket onward each gets only what is new to it, and the axes stay separate:

- **Manifest+Spec** — the diff, the ticket body, this ticket's manifest rows, the spec sections this ticket names that it has not seen yet, any section amended since it read it (`phases/5-repair.md`), and whatever `interfaces.md` has grown since.
- **Craft** — the diff, the ticket body, and whatever `interfaces.md` has grown since. Never manifest rows, never spec sections, on any ticket.

Nothing else. Resending what it already has is not harmless: it reads as new material, and a reviewer re-reading yesterday's interfaces as though they arrived today is how a ticket gets judged against the wrong contract.

**Give the Craft reviewer the path, and require it to read the file before the first diff.** A path is not a delivery: what makes the check exist is the reviewer having read it, so say so as a requirement and expect the return format from that file. If the harness gives you no way to have a subagent read a file, paste the contents once, into the first ticket's prompt only — the reviewer keeps them for the run.

### What a reviewer returns

```
AXIS: manifest | spec | craft
VERDICT: clean | findings
FINDINGS: <axis> · <file:line> · what's wrong · what condition must hold
          — one sentence per finding, as a condition, not a wish
BLOCKING: only a requirement not delivered, a spec decision missing or
          implemented differently without an amendment, extra surface from the
          spec, an invented fact about the user, silent narrowing of an
          acceptance criterion, a red run, a defect proven by a trace, a
          secret's value in the diff, or a test bound to what the next task
          has the right to rewrite — and nothing else.
          Nothing to block — write `none`, that's a normal and frequent answer.
```

**No more than 20 lines, no code fragments and no diff.** A finding phrased as a condition can be forwarded to the executor as a follow-up unchanged; a finding phrased as "should have been more careful" has to be rewritten by you before it can go anywhere, and rewriting it means reading the diff — which is the whole thing this arrangement exists to avoid.

**Tell the reviewer what `BLOCKING` costs, in its prompt.** It is not a severity rating for its own use: everything it lists there becomes a follow-up plus a re-review, and everything it leaves out still reaches the user in the report. A reviewer that does not know this hedges upward — listing anything it feels strongly about — and the run pays a repair cycle per feeling.

## Axis 1 — Manifest

The axis that does not exist in ordinary code review, and the one this framework is built around.

Take the ticket's `Requirements` line, pull those rows from `manifest.md`, and read the **verbatim brief quotes** — not the spec's version, not the ticket's summary. Then, for each:

- Is it delivered end to end, or only the easy half?
- Was it narrowed on the way down? A requirement that entered as "the client sees the status" and left as a status stored in the database but shown nowhere is a shrunk requirement, not a done one.
- Does a `placeholder` sit exactly where a user fact belongs — and is it visibly a placeholder, not a plausible invention?

Verdict per requirement: `done` / `partial` / `missing`, and `partial` or `missing` means the ticket is not finished.

## Axis 2 — Spec

Against the spec sections the ticket named:

- **Missing** — a decision the spec made that the diff does not implement.
- **Extra** — behaviour in the diff that no one asked for. Scope creep is not a bonus; it is untested surface with no requirement behind it and nobody to maintain it.
- **Wrong** — implemented, but not the way the spec decided. Especially: a second version of something `interfaces.md` already provides.

A diff that departs from the spec because the spec turned out to be wrong is **not** a finding on this axis — but it is only legitimate once the spec has been amended and a `D##` row exists. An undocumented departure is `Wrong`, however good the reason: see `phases/5-subagents.md`.

Quote the spec line for every finding.

## Axis 3 — Craft

**The whole of what this reviewer judges by is `prompts/craft-review.md`, and it goes down as a path, not as your retelling of it.** The list of smells, the assertion-level testing check and the return format live there because they are the subagent's material, not yours: an orchestrator that reads them keeps them until the end of the run and gains nothing, and an orchestrator that paraphrases them ships a weaker version of the check than the one that was written.

What stays here is the part you decide:

- Whatever the repo documents about how code is written **wins over that file** — hand the reviewer the repo's conventions too, and say which wins.
- Every smell in it is a **judgement call** — "possible Feature Envy", never a hard violation — and anything tooling already enforces is out of scope: a linter finding is not a review finding. **A defect proven by a trace is not a judgement call**: `input → returns → should`, on an input the contract permits, is a fact the executor can check in a minute.
- Four of its entries exist because subagents cause them — *Reinvention*, *Silent narrowing*, *Invented fact*, *Drive-by edit* — and the first is the reason the Craft reviewer gets `interfaces.md`. Without it that whole class of finding is invisible.
- The testing check in it is the line most often lost on the way down, because a pass count looks like it already answered the question. Handing over the file is what makes it arrive; nothing about it is checkable from the count.

## What to do with findings

**Every "fix" below happens in the ticket, not in the orchestrator and not in the reviewer.** A finding goes back to the executor that wrote the code, as a **follow-up** stating the condition — `phases/5-repair.md`. The reviewer judged and is done; a reviewer that also repairs is a check that has stopped being one. Two follow-ups is the ceiling, after which the finding becomes a failed ticket and takes that path instead.

### `BLOCKING` decides, and it is a short list

**Only findings the reviewer put in `BLOCKING` hold up the commit.** That line exists in the return format for this and nothing else; a run that treats every finding as blocking has turned a three-line verdict into a repair queue, and it pays for that queue twice — once in the follow-up, once in the re-review that follows it.

What is always blocking, no judgement involved:

- **Manifest `partial` or `missing`** — a requirement the user asked for is not delivered. This is the one category no weakening ever touches: the whole framework exists to catch it, and "we'll fix it later" is how it stops being caught.
- **Craft *invented fact*** — a plausible-looking price, address or text standing where the user's own fact belongs. It ships as truth if it ships at all.
- **Craft *proven defect*** — a trace from the reviewer's mental run: an input the contract permits, what the code returns, what it should. Between the seams nothing else would catch it.
- **Craft test bound to internals** — a test tied to what the next ticket is entitled to rewrite. This ticket does not pay for it; the next one does, when the suite goes red on a correct change.
- **A secret's value in the diff** — rule 2 of `SKILL.md`; also reported to the user at once, per the Secrets section.
- **Spec *missing* or *wrong*** — the spec is the contract the executor was given, so a decision it made and the diff skipped or replaced blocks until the code follows it or the spec is amended with a `D##` row (`phases/5-repair.md`). A different library, a crossed module boundary — the code working is not the test.
- **Spec *extra*** that adds surface nobody asked for — removed, unless the rest genuinely needs it, and then one line in the commit message says so.
- **Craft *silent narrowing*** of an acceptance criterion — an empty `catch`, a hard-coded happy path, a self-confirming test. The executor's contract already calls this an unmet criterion.
- **A red suite.** Nothing is committed on red, ever.

Everything else — Craft judgement calls, style, structure, a test set that is bigger than its seams — goes to `state.js` under `concerns` with its file and line, and travels to the final report. **It is not a follow-up and does not delay the commit.**

**This is a deliberate loosening, and here is what it costs.** Deferred findings accumulate, and a list nobody reads is a silent discard — so the list has one reader by construction: the whole-project pass in `phases/8-final.md` triages it, and what it decides is worth fixing becomes a ticket like any other, reviewed and committed the same way. What is not fixed is named in the report. The alternative — repairing every judgement call inside the ticket that surfaced it — was measured at thirteen repairs across nine tickets, each adding roughly forty percent to its ticket's clock, for findings that were mostly not what the run was at risk from.

**Structural findings were already exempt** («if it is structural, note it in `concerns`») — this rule keeps that exemption and stops relying on «small and local», which is the phrase that quietly pulled everything back into the loop.

### The re-review is scoped to the fix

When a follow-up comes back, **review the fix, not the ticket again.** Send the reviewer the diff of the repair alone and the list of findings it was supposed to close; it verdicts each one addressed or not, and flags new breakage inside the fix only. Re-reading the whole ticket costs what the first review cost and re-derives a verdict you already have — and it is how a two-round ceiling turns into an evening.

Refactoring belongs here, not inside the red-green loop. Cleaning up while chasing a failing test is how both jobs get done badly.

## Reporting

To yourself, structured, per axis. **To the user, nothing** — unless something is being carried to the final report as a concern. The user gets one plain line per ticket from Phase 5, not a review.
