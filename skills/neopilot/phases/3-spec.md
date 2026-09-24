# Phase 3 — Flightplan

**First move — `python3 .neopilot/sync.py --enter spec`, before any work below.** A stage entered after its work records zero minutes and reads on the dashboard as skipped.

Turn the manifest and the briefing answers into a specification. **This phase does not reopen the interview** — what is still unresolved becomes a `placeholder` row, not another round of questions.

One exception, and it is narrow: a genuine fork the briefing missed, where the two branches are different projects and a placeholder would only defer the same question to the build. Ask it, once, in one line, with a recommended answer. In **full** mode there is no exception — decide it and record the `ASSUMPTION`.

Write to `.neopilot/<dir>/spec.md`. What the user sees in the dialogue is a two-line summary; the file is the spec.

## Depth

**The brief is a silhouette.** The user describes what happens when everything goes right, at the level of "accepts requests and puts them in a spreadsheet". They do not describe what the third screen says when the network drops, what an empty list looks like, what happens on a double submit, or what the very first launch shows before any data exists. They are not withholding those answers — they do not have them, and they are not supposed to.

Working them out is the most valuable thing this phase can do. A spec that merely restates the brief in tidier words has produced nothing, and it guarantees the gaps get filled during implementation by whichever subagent hits them first, differently each time.

Where the adversarial pass ran in Phase 2, its craft findings land here — the ones nobody needed to be asked about. They arrive as `R##.n` stories like anything else; what makes them worth their own mention is that they are usually the ones the depth pass below would not have produced, because they came from asking where the idea breaks rather than where a requirement is thin.

**How far to take it is the user's setting, not yours.** Read it from the announced depth:

| Depth | The depth pass below | `A##` new capabilities |
|---|---|---|
| **strict** | not run. Only *Wrong input* and *Failure*, and only where the requirement plainly breaks without them | **forbidden** — cut them, do not write them |
| **normal** *(default)* | run by judgement — the dimensions that plainly matter for that requirement, skipping the ones that do not | allowed, with parent and proportion |
| **deep** | run in full — every dimension, every requirement, or an explicit "not applicable" | encouraged, same parent and proportion |

At **strict**, an idea you had that the brief did not ask for does not become a spec section and does not become a note. It is simply not written. The user chose this setting to get exactly what they asked for, and a spec that argues with that choice has ignored an instruction.

At **normal**, use judgement rather than a checklist. Elaborate where the gap would obviously cause a bad build; do not chase every edge of every requirement. Most briefs belong here.

At **deep**, the pass is mechanical and exhaustive — that is what was asked for.

### The depth pass

Run at **normal** and **deep** (see the table above for how completely). Every `R##` requirement goes through this list.

At **deep**, skipping a dimension because a requirement is "obvious anyway" is exactly the mistake this pass exists to prevent — write "not applicable" instead of skipping silently.

| Dimension | The question the brief never answered |
|---|---|
| **First run** | what does this look like before any data exists? |
| **Empty** | zero items, zero results, zero history — what is on screen, and what invites the next step? |
| **Wrong input** | what does the user see, in their language, and what survives of what they typed? |
| **Failure** | the network, the service, the disk — what breaks, what is said, what is retried, what is lost |
| **Interruption** | closed halfway, refreshed, sent twice — does it resume, restart, or duplicate? |
| **Growth** | ten items versus ten thousand — what has to change, and does it now or later? |
| **Boundaries** | who may do this, and what happens to someone who may not? |
| **Aftermath** | where does the result go, who learns about it, can it be undone? |

Each answer becomes an `R##.n` story with its own acceptance line. `R##.n` never counts against any limit — it is the requirement the user actually made, worked out properly.

**The number of stories is an output, not a target.** A requirement that genuinely has seven dimensions gets seven stories; one that has two gets two, and padding it to look thorough is the same defect as skipping it. What is always wrong is twelve requirements producing twelve stories — that is the brief copied out rather than worked through.

### Two roads for depth

**Propose it** — when the answer is genuinely the user's to give (which of two behaviours they want, what tone the messages take, whether something is worth its cost). That is a briefing question, and one of the best a briefing can spend itself on.

**Decide it** — when the answer is craft, not preference. Error text, retry policy, empty-state copy, sensible limits, sane defaults. Decide, write it into the spec, and say so plainly in the summary. Asking the user which HTTP status to return is a wasted question; asking whether a cancelled order should refund automatically is not.

In **full** mode both roads collapse into the second — decide everything, and list what you decided in the final report. At **strict** depth, the first road narrows too: a question exists to clarify what the user asked for, never to sell them something extra.

### Keeping depth attached

The one failure mode worth guarding: depth that **floats free of the brief** — a beautiful subsystem grows while a plain requirement from line 2 quietly never gets a section. So every story carries a mark saying where it came from.

| Mark | Origin | Rule |
|---|---|---|
| `R##` | straight from the brief | untouchable |
| `R##.n` | **deepening** a brief requirement | uncapped — this is the main work of the phase |
| `G##` | **the user's own words**, in the briefing or later | untouchable, like `R##` — a `G##` raised mid-flight is a change to the task, not an idea |
| `A##` | a **new capability** the brief never implied | must name a parent `R##` |
| `D##` | a constraint the **build** proved, added mid-flight | only from `phases/5-repair.md`, never from an idea |

Note the line between the last two, because it is the one that gets blurred: elaborating "accepts requests" into retry, resume and validation is `R01.n` — the same requirement, understood properly. Adding a loyalty programme is `A`. Depth is not scope creep, and treating it as if it were is how specs end up thin.

Three rules keep additions attached. They hold at **every** depth — `deep` relaxes none of them, and `strict` removes `A##` entirely:

- **Parenthood.** An `A##` story names the `R##` it serves. A free-floating invention gets cut — not because inventions are bad, but because one with no parent is a different project.
- **Proportion.** `A` stories may not outnumber `R` + `G` combined. `R##.n` never counts toward this — deepening what was ordered is unlimited by construction.
- **Precedence.** Recorded here, enforced in Phase 4: tickets closing `R` come before tickets closing only `A`. If time or patience runs out, what goes unfinished is your addition, never the user's request.

Every `A##` that survives into the build is listed in the final report under "what I added beyond the order", so the user learns about it from the report rather than from the code.

## Boundaries — decided here, not by whichever ticket reaches them first

Phase 5 runs several subagents in fresh contexts, each seeing one ticket and `interfaces.md`. What makes them build one project instead of several incompatible halves is that the **boundaries between modules were already decided** — the units, what each one owns, and the signatures they expose to each other.

Leave that undecided and it still gets decided: by ticket 01, which has seen an eighth of the task, in whatever shape made ticket 01 easy. Everything after it either obeys that shape or quietly builds a second version of it. Reinvention is the most expensive defect a parallel crew produces, and this is where it is actually prevented — `interfaces.md` only records the decision, it cannot make it.

So this phase names, for every unit the build will have:

- **What it owns** — the data, the rule, the surface. One unit, one reason to change.
- **What it exposes** — the public signatures other units call. Names and shapes, not implementations.
- **What it hides** — the part nobody else may reach into. If nothing is hidden, it is not a module, it is a folder.

Then the **test seams**, which are a subset of the above and not a separate exercise: behaviour is checked through those same public boundaries. Prefer seams that already exist in the repo. **The fewer the better — the ideal is one.** A seam is a promise to keep something stable, and every extra one is another thing that cannot move.

Three rules keep this from becoming architecture for its own sake:

- **Boundaries follow the depth pass, not the requirement list.** One requirement can live inside one module; three requirements that all read the same data belong behind one boundary, not three.
- **A boundary that no ticket crosses is not a boundary.** If the whole thing is built by one subagent, it needs no public signature — say so and move on. At tier T0 this section is two lines.
- **Deep modules over many shallow ones.** A narrow interface hiding real work beats a wide one hiding none. Every signature written here is something eight contexts have to agree about, and the cheapest agreement is the one there is least of.

In **manual** this is part of what the spec gate covers, and it is the part worth actually discussing — it is the only decision in the spec that is expensive to change later.

Phase 4 seeds `interfaces.md` from this section before the first ticket flies. Write it so that is a copy, not a re-derivation.

## The template

```markdown
# Specification: <name>

## Task

The user's problem in their own words — from the person who suffers it,
not from the code's point of view.

## Solution

What the user will have once everything is done. Again without technicalities.

## User stories

| # | Mark | Story | Acceptance |
|---|------|-------|------------|
| 1 | R01 | As a client, I file a request with the bot so I don't have to call | the bot accepted and confirmed |
| 2 | R01.1 | …and see a clear error if the connection drops | error text, not silence |
| 3 | A01 → R01 | …and get a request number to refer to | the number is in the confirmation |

Each story is "As <who>, I <what>, so that <why>" plus whatever
shows it is working.

## Implementation decisions

Stack, modules and their boundaries, data schema, API contracts, external services.
Each decision — with one line of "why this way".
No file paths and no code: they go stale before the spec does.

Exception: if a structure (schema, type, state machine) is expressed
more precisely in code than in prose — include just that, without boilerplate.

## Boundaries and seams

The units the project consists of. One line each:
what it owns, what it exposes, what it hides.

| Module | Owns | Exposes | Hides |
|---|---|---|---|
| `intake` | client requests | `createRequest({phone, address, problem}) -> {id, createdAt}` | phone normalisation, number generation |

Test seams — an explicitly named subset of these same boundaries:
behaviour is checked through them, Phase 5 tests only here.
Prefer existing seams to new ones. The fewer seams, the better; the ideal is one.

This is the only spec section Phase 4 copies into `interfaces.md`
verbatim. Write it so the copy needs no guesswork.

## Out of scope

What we consciously do NOT build. Each line names the manifest requirement
it defers, and says why.

| Requirement | Why not now |
|---|---|
| R06i — admin screen for requests | requests are visible in the spreadsheet; a separate screen is the next pass |

## Open places

Every `placeholder` from the manifest: what stands in as the stub, where exactly
in the code, and what is needed from the user to close it.

## Manifest coverage

| Requirement | Spec section |
|---|---|
| R01 | Stories 1–3, Decisions §2 |
| R02 | Stories 4–5, Decisions §4 |

Exactly as many rows as there are live requirements in the manifest. None missing.
```

## The vocabulary rule

If `CONTEXT.md` or `docs/adr/` exist, the spec speaks the project's language — the terms already defined there, not synonyms. A concept you need that the glossary lacks is a signal: either you are inventing language the project does not use, or there is a real gap worth noting. If a decision here contradicts a recorded one, say so out loud in the spec rather than overriding it silently.

## Gate G2 — before leaving this phase

This is the single most valuable check in the whole flight. Everything downstream trusts the spec; this is the last moment the spec is still cheap to compare against the words the user actually said. It has two halves, and the second is the one that works.

### 1. Your own pass — zero `open` rows

Update every manifest row: `open` → `in-spec` with its section, or → `deferred` with its Out of Scope line.

Then check: **zero `open` rows.** An `open` row means the spec does not cover something the user asked for. That is not a note for later — it is an incomplete spec. Go back and write the missing section.

### 2. The independent coverage check

The first half cannot catch its own blind spot. **You wrote the spec, so you cannot see what you did not write** — a requirement you misread as covered gets marked `in-spec` by the same reading that lost it, and every check from here to the end inherits that. The manifest makes the loss *findable*; it does not make you the one who can find it.

So spawn a subagent. It receives **exactly two files** — `<date>-brief.md` and `spec.md` — and nothing else.

**It must not receive:** `manifest.md`, the conversation, the briefing answers, or any summary of them. The manifest is your reading of the brief; hand it over and you have asked someone to check your reading against itself.

**And it must be told not to go looking.** Both files live in `.neopilot/`, next to the manifest, under a `README.md` that explains what the manifest is — so a checker curious about "how this is tracked" finds your reading in one step, without disobeying a word of the above. The first line of its brief is therefore a prohibition, not an instruction.

Its brief:

> Open exactly the two named files and nothing else — not `manifest.md`,
> not the rest of `.neopilot/`'s contents. Your value here is that you
> have not seen how the spec's author read the task.
>
> Read the two files. The first is the task as the customer stated it
> in their own words. The second is the specification written from that task.
>
> The brief may contain an "Additions" section — things the customer said later.
> That is part of the task on equal footing with the main text, and where they
> disagree the later one is right: nothing cancelled there needs to be
> demanded, everything added does.
>
> Find everything the customer asked for that the spec does not cover. For each:
> a quote from the brief and one line on what exactly is missing.
>
> Separately — what is half-covered: the requirement is named but described
> so loosely it cannot be built from. "Puts into a spreadsheet" without saying
> what exactly goes in — that is a half.
>
> And separately — what is in the spec but was never in the brief.
>
> Do not judge quality, do not suggest improvements, do not explain why
> something might be missing. Only the fact of the discrepancy. If there are
> none — say so.

Then act on it, before leaving the phase:

| Finding | What it means |
|---|---|
| missing | the spec is incomplete — **write the section**, then update the row |
| half-covered | the executor will guess — write what was missing |
| in the spec, not in the brief | an `A##` with no parent, or a `D##` written too early. Attach it or cut it |
| "no discrepancies" | pass |

Record the result in `state.js` under `coverage` — the count of findings and what was done with each — so the Phase 8 report can say whether this gate ever caught anything. A gate whose findings are never visible is a gate nobody will keep running.

**A finding here is the gate working, not a failure of the spec phase.** It costs a paragraph now. The same finding at G4 costs the build.

## Showing it

**full, semi and interview** — two lines in the chat: what will be built, and what deliberately will not. Then move on.

In **interview** that is easy to get wrong, because the user has just spent twenty answers on this and it feels like they are owed the document. They are not — they chose the mode that buys questions, not gates, and stopping here to wait for approval is the pause the mode was picked to avoid. Two lines, plus one saying where it is: "The spec is `.neopilot/<dir>/spec.md` if you want a look. Starting." Then start.

**manual** — the spec is a gate. Show it in full, stop, wait for an explicit "ok". Rewrite on every objection and ask again. Silence is not agreement, and neither is work already started.
