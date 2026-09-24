# Rationalizations and Red Flags — the catalogue

**Read this file at three moments, and not otherwise:** when a gate fails (G1–G4), when you catch yourself building an argument for skipping something, and once before writing the final report. It is a checklist, not an instruction — nothing here tells you how to do a phase, and everything here tells you how a phase goes wrong.

The five rules that never lose are in `SKILL.md` and stay there. This is the long tail.

## Rationalizations — the ones that cost the user the product

Phase-specific mechanics are not here; they live in the phase that owns them. What follows is the short list of excuses that end with the user getting something other than what they asked for.

| Excuse | Reality |
|--------|---------|
| "The user said not to ask questions" | They said not to ask UNNECESSARY ones. Deciding questions are part of the work, not a discussion of process. |
| "KISS — just build it" | A simple result comes from process, not from skipping stages. Without a spec, every fix becomes "I meant something else". |
| "The brief is all in the dialogue, why copy it to a file" | The dialogue gets compacted, and the brief in it is the oldest part. Three phases later you'll be synthesizing from a retelling of a retelling. |
| "The requirement is unimportant" / "they haven't mentioned it since — so it's cancelled" | Importance is the user's call, and silence doesn't cancel. You may propose `deferred`; striking it out — only them, in their own words, quoted into the manifest. |
| "They changed their mind mid-run — I'll fix the manifest, the brief mustn't be touched" | What was said can't be rewritten, but what was said later MUST be appended: `## Additions`, verbatim, dated. The manifest is your reading, and neither independent check sees it. A change that reached the manifest but not the brief does not exist for G2 and G4. |
| "A new wish mid-build — the briefing is over, I'll file it as `D##`" | `D##` is what the build proved. The user's words are always `G##`, in any phase, plus a line in "Additions" and out loud: taking it as a task, deferring it, or putting it in the report. Accepted silently is a deadline they never agreed to. |
| "I'll put a stub, they'll clarify later" | Blocking unknowns (payment, hosting, accounts) are resolved in the briefing — in full auto, in self-briefing — but always before the build. |
| "Let them send the key, I'll paste it" / "the key is already in context — so I can write it down" | Keys are pasted by the user and only into `.env`; you work with the variable name. A key that ended up in context is grounds to redact and warn, not a permission. |
| "Fastest to do it all in one context" | Fastest in the first hour. After that the model walks in circles and breaks what worked. |
| "The executor couldn't — I'll finish it myself, I'm in context anyway" / "it's a two-line fix, spinning up a subagent costs more" | More expensive for this task — paid by every next one. Your context is spent once and never returns: a hand-made edit sits in it until the end of the build. Couldn't do it — a follow-up to it or a fresh context, but not your keyboard. |
| "A short brief means a short spec" | The brief is a silhouette: the user described the happy path and described no empty states, no errors, no interruptions. At normal and maximum depth, thinking them through is your job. |
| "That's obvious, won't write it down" | What's obvious to you is not recorded, and every subagent will guess it differently: three executors — three different "obvious" answers. The manifest and the spec are the only points of reference. |
| "Thought of a useful feature, adding it" | Deepening what was ordered (`R##.n`) — yes. A new capability (`A`) — only with a parent requirement, within proportion, and into the report. On `strict` — not at all. |
| "Full auto — so I can deploy too" | Automation removes questions about the product, not the right to do the irreversible. Deploy, payment, mailout, deletion — a gate in every mode. |
| "In full auto I can decide everything for the user" | Decisions — yes, and all into ASSUMPTIONS. Facts about the user (prices, copy, accounts) — no: a placeholder and a line in the report. |
| "I'll write 'launching in 60 seconds'" | You can't wait — the promised pause won't happen. The honest wording: "starting now, say stop". |
| "In manual I'll also just start and wait for objections" | In manual, approval means an explicit "ok". Silence is not one, started work even less so. |
| "I'll check against the spec, that's enough" / "I'll check coverage myself — I wrote it" | The one who wrote it can't see what wasn't written, and the spec may already have lost a requirement. At G2 and G4 a subagent reads — against the brief, without the spec and without the manifest — otherwise the check confirms its own error. |
| "The test rule is written in the phase — so it's in force" | Only what made it into the executor's prompt is in force. The phase file is read by the orchestrator, and the orchestrator doesn't write the code. |
| "Interfaces will settle along the way — the first task sets them" | Then they're set by the agent that saw one eighth of the task. Module boundaries are decided before the cut, otherwise eight contexts negotiate retroactively. |
| "I'll write the report from memory — I did all of it" | By phase eight your context is the dirtiest of the whole run. The report is assembled from `manifest.md` and `state.js`, re-read from disk. |
| "Decision rationales stay in the spec" | The spec dies with the run. What must outlive it goes into an ADR — otherwise the next session re-opens the same decisions. |
| "The user said 'grill me' — I'll show the spec too" | Interview mode buys questions, not gates. Gates are "manual mode", and that's a separate word they didn't say. |
| "Tasks and spec are visible in chat — why files" | The file in `.neopilot/` IS the artifact; chat is only its retelling. The dialogue will die, the files remain. |
| "The user didn't ask about modes — won't burden them" | They won't ask either: there's no `--help` in a chat. The five lines at the start are the only place they ever learn the build has controls. |
| "They asked for polish — the critic will figure out what to compare against" | It won't: it will invent a benchmark and drive the build toward it. No benchmark from the user — polish doesn't run, and that's an answer, not a refusal. |
| "A polish round found a small thing — I'll fix it myself, it's not a task" | Then the fix ships without review, without a green run, and without a rollback point. Polish is more tasks, not a license to take the keyboard. |
| "The critic is still unhappy — too early to stop" | It will always be unhappy: that's what it's paid for. Stopping is no new findings, the round ceiling, or the user's word. |
| "Project built, tests green — so it works" | The tests were written by the same process as the code. Until somebody launched the project, "works" is a hypothesis — and the first to launch it is the user. |
| "The task is big, but I'll pull it through in one context" | You'll pull it through — and pay quadratically for it: the ceiling in `phases/5-subagents.md` exists precisely because "a little more" costs more than a relay. |

## Red Flags — start the phase over

Every line here means something the user asked for is at risk. Phase mechanics — instruments, timestamps, wave bookkeeping, memory-file detection — are checked in the phase files that own them, not here.

- Writing code before the spec exists.
- The brief was never written to its file — the run is anchored to nothing.
- A requirement left the manifest without a status, or was marked `dropped` without a quote of the user saying so.
- Past gate G3: a ticket that traces to no requirement, or a requirement that traces to no ticket.
- Spec or tickets that exist only in the dialogue — nothing written under `.neopilot/`.
- Instruments that disagree with the chat: a stage still `active` after you moved on, a ticket running while the dashboard calls it `pending`, a ticket carrying the run's `startedAt` instead of its own, timestamps filled in afterwards from memory. The user believes the screen over your sentences, which is the whole reason it exists.
- The announced depth and the actual spec diverge: a bare restatement of the brief at normal or deep, or an invented capability — any `A##` — at strict.
- G2 or G4 judged by you instead of by a subagent: your own reading of your own spec, or a final acceptance measured against the spec rather than blind against the brief.
- A blind checker, coverage checker or memory subagent handed `spec.md`, the manifest or the tickets — or left free to open `.neopilot/` for itself. Independence is the entire mechanism; without it each confirms the plan instead of the thing.
- The final report composed from memory instead of from `manifest.md`, `state.js` and the two subagents' returns, re-read from disk.
- A T2+ run that ended with no ADR: every `D##` and every load-bearing implementation decision left to die with `.neopilot/`.
- The finished project was never actually run — accepted on green tests and a reading of the code.
- Starting without announcing mode and depth, or announcing one and behaving as another: questions in full, a spec put up for approval in interview, a start-and-see instead of "ok" in manual.
- With `polish` on: a polish round run against no reference, its findings applied outside the ticket path, a fourth round, or a round that broke something and was patched instead of reverted.
- A comparable in `reference.md` that the user never named — your taste entered as though it were theirs, and everything downstream now judges the build against it.
- The adversarial pass skipped in `interview` because the brief "looked well thought out" — or used to argue the user out of a requirement instead of into a decision.
- A blocking unknown — payment, hosting, an account, where the data lives — left unasked in semi, interview or manual because the brief "looked clear". Asking nothing is legitimate only when nothing is open; a manufactured question and a skipped blocking one are both defects, in opposite directions.
- Promising the user a wait — a countdown, "in a minute", "if you don't reply within N seconds" — that you have no way to honour.
- In full: an invented fact about the user standing where an ASSUMPTION, a stub, or a PLACEHOLDER belongs.
- Asking the user a process question — which tracker, which doc file, which memory file, ticket granularity, code review — outside manual, where spec and tickets are gates by design.
- A requirement quietly narrowed to whatever happened to work, or the spec amended mid-build with no `D##` row recording why.
- Two tickets in one subagent context, or two tickets in one commit.
- The orchestrator editing a file outside `.neopilot/`: a "two-line" fix, a red test, a review finding applied by hand instead of sent down. One such edit is the whole failure — the diff stays in its context for the rest of the run.
- A ticket's diff, or the raw output of a full test run, read into the orchestrator's context. It needs a verdict and the names of what failed, not the material.
- A repair started from an empty context when the ticket's own executor was still reachable — or the mirror failure, a third follow-up into an executor that has already failed to do it twice.
- Parallel subagents editing the same files — or the mirror failure, independent tickets flown one at a time with the plan's parallelism thrown away in the delivery.
- A subagent launched without `interfaces.md`, or finishing without returning the contract block.
- The first wave launched with `interfaces.md` still empty — module boundaries left for whichever ticket happens to reach them first.
- A subagent prompt with no testing rules or no context ceiling in it: the discipline written in the phase file the orchestrator reads, and absent from the handoff to the one who writes the code.
- A ticket relayed to a fresh context on a red suite, or a relay whose handoff file has no `DECISIONS` / `DEAD ENDS` / `NEXT` — the successor then rebuilds what was already ruled out.
- A resume that reset a ticket with `handoffs > 0` to `pending`, throwing away the written seam and re-running the longest ticket of the flight from zero.
- Payment, hosting, or accounts first mentioned at the finish line.
- A secret value asked for, repeated back, or written into any file, prompt, commit, or report.
- Installing a package or fetching remote code without the user asking for it.
- Text outside the `neopilot` markers edited, moved or dropped, or the run ending with no project memory file at all.
