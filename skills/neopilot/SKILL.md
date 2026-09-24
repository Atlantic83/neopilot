---
name: neopilot
description: Use when the user dictates an app, site, bot, or feature to build end-to-end and expects a finished result without reviewing specs, tickets, or code — vibecoding sessions, non-technical users, "build it turnkey", "build it for me", "don't ask unnecessary questions" requests. Also use when the user invokes /neopilot, or asks for a build in a named mode, depth or finish — "full auto", "interview mode", "grill me", "manual mode", "strict to the brief", "think it through deeply", "polish to a benchmark".
argument-hint: "[full|semi|interview|manual] [strict|deep] [polish] what to build or path to brief.md"
license: MIT
---

# NeoPilot

## Overview

NeoPilot flies a dictated idea from words to a working project **in one dialogue**, without making the user approve each stage. It is self-contained: every rule it needs lives in `phases/`. No other skill has to be installed.

Two ideas carry the whole design.

**The order is the product.** Code is written in the second-to-last phase. Everything before it exists to decide *what* to build, and everything after it exists to prove the right thing got built.

**The brief is the contract, not the design.** Two obligations follow from it, and they pull in opposite directions on purpose.

*Nothing may quietly vanish.* The user's original words become a numbered manifest before anything else happens, and every phase is gated on it. What breaks naive vibecoding is not bad code — it is a requirement that stopped existing somewhere around the third rewrite.

*The brief is not the design.* It is a silhouette: it describes the happy path and nothing underneath — no empty states, no failures, no interruptions, no limits. Working those out is legitimate work, not scope creep, and it is where much of the value of this process comes from. **How far to take it is the user's dial**, set by the [depth](#depth) parameter. What is never allowed at any setting is depth that **detaches** from the brief.

## Reading this skill

This file is the orchestrator: modes, phase order, gates. The rules for each phase live in `phases/` and are **read at the moment that phase starts, not before** — that is what keeps the working context small.

**One file at a time, and never ahead.** Breaking this does not feel like breaking it: the next files are small, the flight is planned, opening them while you are already reading seems tidy. What it does is put Phase 5's rules into the context Phase 1 is thinking in, and leave them there for the rest of the run. The unit of loading is the file, not the section — a read pulls in the whole thing, which is why anything one phase needs and another does not is its own file.

**Twice only where the table says twice** — `7-instruments.md` in Phase 4, `9-memory.md` in Phases 5 and 8, legitimate there because the run has usually been compacted in between. Everywhere else, re-reading because «details have faded» buys a copy of what is still in the context.

**After a compaction, re-read the state, not the phases.** `state.js` (it holds `skillDir`, the reviewers and the tickets), `manifest.md`, `interfaces.md`, and the file of the phase you are actually in — those four and nothing else. The pull is to reopen `5-subagents.md` to recover the thread; that spends eight thousand tokens re-reading rules you are already executing, and the thread was never in them.

| Phase | Read | Produces |
|---|---|---|
| 0 Preflight | `phases/0-modes.md`, `phases/0-preflight.md`, then `0-instruments.md` and `0-memory.md` | mode announced, repo configured, `.neopilot/` created |
| 1 Manifest | `phases/1-manifest.md` | `brief.md`, `manifest.md` |
| 2 Briefing | `phases/2-briefing.md` | answers recorded into the manifest |
| 3 Spec | `phases/3-spec.md` | `spec.md` |
| 4 Plan | `phases/4-plan.md` | `tickets/NN-*.md` (or none — see tiers), `interfaces.md` seeded |
| 5 Subagents | `phases/5-subagents.md` | code, commits, `interfaces.md` grown |
| 6 Review | `phases/6-review.md` | per-ticket review |
| 7 Instruments | `phases/7-instruments.md` — **in Phase 4**, when the tickets are cut | `state.js`, `dashboard.html` + `index.html` (opened for the user) |
| 8 Final | `phases/8-final.md` | blind acceptance, final report |
| 9 Memory | `phases/9-memory.md` — **in Phase 5 and Phase 8** | `CLAUDE.md` / `AGENTS.md`, `docs/adr/` — the project as the next session will find it |
| — | `phases/5-repair.md` — when a ticket comes back anything other than `DONE` | the repair path, retries, spec amendments |
| — | `phases/rationalizations.md` — on a failed gate, on catching yourself excusing something, once before the report | nothing; it is a checklist |
| — | `phases/polish.md` — only with the `polish` parameter | polish rounds |

## The words the user sees

The phases have English names in this file and the user never sees them. In the chat, on the dashboard and in the final report there is **exactly one word per stage**, and it is this one. Two vocabularies for one process is how a person reads the README and then cannot find any of it on the screen.

| Phase | `stages[].id` | User-facing |
|---|---|---|
| 0 Preflight | `preflight` | Preparation |
| 1 Manifest | `manifest` | Requirements |
| 2 Briefing | `briefing` | Briefing |
| 3 Spec | `spec` | Specification |
| 4 Plan | `plan` | Plan |
| 5 Subagents | `build` | Development |
| 6 Review | `review` | Code review |
| 8 Final | `final` | Acceptance |

Two rules hold this together:

- **"Build" is the whole run, not one stage.** "The build is running", "the build was interrupted", "resume the build" — all about the process as a whole. That is why stage five is called "Development": otherwise one word means both the part and the whole. And "build" in the `npm run build` sense — not that either.
- **The unit of work is a "task".** Not "todo", not "ticket", not "issue". The "task" is also what the user set (the brief); one word for two different things breaks both the report and the dashboard.

Phases 7 and 9 are not sequential, and each is split in two along the line where it is read. The instruments are raised in Phase 0 from `phases/0-instruments.md` — template, starting state, the update ritual — and `phases/7-instruments.md` is opened only when the tickets are cut. The project memory is raised in Phase 0 from `phases/0-memory.md` — which file, and the skeleton — and `phases/9-memory.md` is opened when the build discovers something and again in Phase 8, where a subagent writes the full description from the finished code.

## The three dials

Everything typed after `/neopilot` splits into four parts: **the mode** (`full`, `semi`, `interview`, `manual` — default `semi`), **the depth** (`strict`, `deep` — default normal), **the finish** (`polish` — off by default), and **the brief** (everything else). Bare words, no dashes; anything unrecognised is brief.

**The rules for all three are in `phases/0-modes.md`, read in Phase 0 with `phases/0-preflight.md`** — the triggers in both languages, the opening block that announces the resolved settings, what each depth permits, and what happens when the user switches mid-run. They are decided once, before Phase 1, and every phase after that only applies them; carrying the argument for why there are four modes instead of three through nine phases is what that file exists to prevent.

What stays here is the consequence: the table in `The flight` below, which says exactly which cells each mode changes. Two things about the dials never move, and they are repeated there because they are not calibration — **no mode removes the manifest gates, and no mode removes the safety gates.**

## When to Use

- User dictates what to build and expects the finished thing, not a collaboration on process.
- User is non-technical: will not read specs, judge ticket granularity, or review code.
- "Build it turnkey", "just build it", "don't ask unnecessary questions".
- User wants the idea taken apart with them question by question, and the build done without them — that is **interview** mode, still NeoPilot.
- User wants to approve the spec and the tickets but not to run the pipeline by hand — that is **manual** mode, still NeoPilot.

**When NOT to use:** the user wants to co-author the code itself line by line (work with them directly); the task is a small single-file change (just do it); the idea is bigger than one project and its destination is unclear (settle the destination first, then return here).

## The flight

| Phase | full | semi (default) | interview | manual |
|---|---|---|---|---|
| 0 Preflight | auto | auto | auto | auto |
| 1 Manifest | auto | auto | auto | auto |
| 2 Briefing | no interview — self-briefing, stage `done` | only what the brief leaves open — sometimes none | the adversarial pass, then every fork it opens | the same |
| 3 Spec | auto | auto | auto | show → wait for explicit "ok" |
| 4 Plan | auto, notify only | auto, stoppable | auto, stoppable | discuss → wait for explicit "ok" |
| 5 Subagents | auto | auto | auto | auto |
| 6 Review | auto | auto | auto | auto |
| 8 Final | report + Assumptions | report | report | report |

**`polish` adds a step inside Phase 8, in every mode** — the polish loop, between the blind acceptance and the report. It changes no cell above: it asks the user nothing, and it approves nothing with them.

**`interview` and `manual` differ in exactly two cells** — the spec gate and the plan gate. If you find yourself treating them differently anywhere else, one of them is wrong.

**The manifest gates run in every mode.** They are checks against the user's own words, not requests for the user's time — no mode buys the right to skip them.

| Gate | After phase | Condition to pass |
|---|---|---|
| **G1** | 2 Briefing | every requirement has a status; none left `open` without a reason recorded |
| **G2** | 3 Spec | every live requirement is `in-spec`, `deferred`, or `dropped`, zero `open` — **and an independent reader given only the brief and the spec finds nothing missing** |
| **G3** | 4 Plan | every `in-spec` maps to ≥1 ticket, **and every ticket traces back to ≥1 requirement** |
| **G4** | 8 Final | blind acceptance run against the brief, spec withheld; every disagreement with the manifest reported |

**G2 and G4 are the same check at the two ends of the flight, and both are needed.** They measure the build against the user's own words, with your paraphrase of them taken away — G2 while the answer is a paragraph of spec, G4 when it is the last chance to know. Everything in between measures against the spec, because that is the contract the executors were actually given; judging a subagent by words it never saw produces findings nobody can act on.

A failed gate is not a warning. It sends the phase back to be redone — see `phases/1-manifest.md`.

**The plan may be corrected; the brief may not.** When the build proves the plan wrong — a data model that does not hold, an assumed interface that cannot exist — the spec is amended and a `D##` row records what the code demonstrated and when. That is the one thing allowed into the manifest after the briefing, it never retires a requirement, and it is never a route for an idea you had. Rules in `phases/5-repair.md`.

## Secrets

Credentials are the user's to hold, not the agent's to handle. This section binds every phase; the phases do not restate it.

- **Never request one.** No key, token, password, connection string, or card number is ever a question. *Which* provider is a question. *Whether* an account exists is a question. The credential is not.
- **Redact at ingest, before anything is written.** The brief, every user answer, and every pasted fragment pass the redaction gate in `phases/1-manifest.md` *before* they reach a file. A detected secret becomes `[REDACTED:<VAR_NAME>]` — the variable name survives, the value does not.
- **"Verbatim" always means "verbatim after redaction."** Wherever this skill asks for the user's exact words, it asks for them redacted. The two rules are one rule.
- **Refer to it by name.** `STRIPE_SECRET_KEY`, not the value. The user puts the value in `.env` themselves; `.env` is in `.gitignore` before the first commit; the final report lists which names are still empty.
- **A leaked secret is a stop condition.** A secret that reached a file or a commit is reported immediately, in plain language, with the advice to rotate it. Before the first commit, run the redaction gate over the whole of `.neopilot/`.

## Files this skill owns

```
.neopilot/
├── <YYYY-MM-DD>-<feature-slug>--wip/   one run; the date is the day it started,
│   │                    the suffix means it has not landed yet and goes in Phase 8
│   ├── <YYYY-MM-DD>-brief.md   the user's original words, redacted; later changes appended
│   ├── manifest.md      R01…Rnn — requirements and their status
│   ├── reference.md     what the result should be like — the user's comparables, never yours
│   ├── spec.md          the specification
│   ├── interfaces.md    the boundaries from the spec, then what finished tickets built
│   ├── handoff-NN-1.md  only when a ticket outgrew one context — what the successor needs
│   └── tickets/NN-<slug>.md
├── README.md            how to read this folder, and the register of runs — for the human:
│                        written in Phase 0, one row added per run and closed in Phase 8
├── state.js             the run state, and the only file you edit: stages, tickets, timings, debt
├── dashboard.html       the human view — copied in Phase 0; carries a snapshot of the state inside it
├── sync.py              one call after each update: snapshot into the page, server back up if it died
└── index.html           a symlink onto dashboard.html, so the pane's `/` is the dashboard

CLAUDE.md | AGENTS.md   the project memory — what the next session reads first
docs/adr/               decisions worth outliving the run — written in Phase 9, tier T2+
```

The brief is dated in its filename because a run directory outlives one sitting — the directory's date is the day the run started, the brief's is the day that brief was dictated. The dashboard is opened for the user, not described to them: it shows the eight stages of the cycle, where the run is now, and a live clock on the run, the current stage and the current ticket.

`.neopilot/` is the record of **this** run; the memory file at the root is the project as it stands, for whoever opens the repo next; `docs/adr/` is why it stands that way. NeoPilot's content in the memory file lives between `<!-- neopilot:start -->` markers — everything the user wrote outside them is untouchable. See `phases/9-memory.md`.

The three are not interchangeable, and the split is what keeps the spec throwaway. `spec.md` is worth nothing the day the work ships; the reasoning inside it — why this data model, what the build proved wrong, which word means which thing — is worth something for years, and it dies with `.neopilot/` unless something routes it out. That is what the ADRs are for.

`.neopilot/` is committed, not ignored — it is the user's record of what was promised and what was delivered. A run that leaves nothing under `.neopilot/` did not happen.

## Judgement

This skill describes a process, not the product. Its numbers — tiers, question counts, story counts, wave widths — are **calibration for a first guess, never targets to hit.** A spec written to reach a story count, or a plan cut to land inside a tier, has optimised for the rule instead of for the person who asked.

The rules below are the same kind of thing. Each one is here because it was paid for, and each is an argument — arguments can lose. Where following one would make the result worse for the user, break it deliberately, say so in one line, and carry on. That is a decision, and decisions get recorded. What is never acceptable is breaking one quietly, or keeping one because it is written down.

**Five rules are not calibration and do not lose.** They hold in every mode, at every depth, at every tier:

1. **A requirement is removed only by the user**, in their own words, quoted into the manifest — and appended to the brief, where the independent gates can see it. The same holds for one they add mid-flight.
2. **A secret is never requested, echoed, or written** — not into a file, a prompt, a commit, or a report.
3. **A fact about the user is never invented.** Prices, texts, addresses, accounts stay visible placeholders until they supply them.
4. **An irreversible or outward-facing action is a question** — deploy, publish, pay, message a third party, delete data, rewrite history.
5. **The orchestrator does not write the project's code.** Its keyboard reaches `.neopilot/`, the memory file and git. Everything else — a fix worth two lines, a red test, a review finding — travels down to a subagent. Rules in `phases/5-subagents.md`.

Everything else is argument.

## When it starts going wrong

Two catalogues live in `phases/rationalizations.md` — the excuses that end with the user getting something other than what they asked for, and the red flags that mean a phase has to be started over. **Read that file at three moments: when a gate fails, when you notice yourself assembling an argument for skipping something, and once before the final report.**

They are checks, not instructions: nothing in them tells you how to run a phase, and every phase's own mechanics are checked in its own file. Keeping fifteen thousand characters of failure modes resident from the first turn — in the one context that is never refreshed — means paying for them on every step of the run to answer questions that arrive at three of them. The five rules above are the ones that must be in your head without a lookup; the rest is a catalogue, and a catalogue is opened.
