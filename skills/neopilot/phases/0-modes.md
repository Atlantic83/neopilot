# Phase 0 — Modes, depth and finish

**Read this in Phase 0, together with `phases/0-preflight.md`, before anything is announced to the user.** Everything here is decided once, at the start, and never again: the parameters come out of what the user typed, the resolved settings are announced in one block, and the rest of the run only ever *applies* them. That is why it is not in `SKILL.md` — nine phases would otherwise carry the argument for why there are four modes instead of three.

`SKILL.md` keeps the one-line map of which cell each mode changes (`The flight`); the rules for filling those cells are here.

## Modes

Everything typed after `/neopilot` splits into four parts: **the mode** (optional bare word — `full`, `semi`, `interview`, `manual`), **the depth** (optional bare word — `strict`, `deep`), **the finish** (optional bare word — `polish`), and **the brief** (everything else). No dashes on any parameter. Text that is not a recognised parameter is always brief.

`/neopilot full deep ceramics online store` — full mode, deep elaboration. Order does not matter; all three parameters are optional and independent.

| Mode | Triggers | Human gates |
|---|---|---|
| **full** — full auto | `/neopilot full`, "full auto", "do it all yourself", "don't ask me anything", "fully automatic" | none |
| **semi** — semi-auto **(default)** | `/neopilot semi`, "semi-auto", nothing specified | questions, on genuine forks only |
| **interview** — interview mode | `/neopilot interview`, "interview mode", "grill me", "interview me", "ask me everything", "take the task apart with me" | questions, all of them |
| **manual** — manual | `/neopilot manual`, "manual mode", "approve every step" | the same questions + spec + tickets |

A mode decides two separate things — how much the user is asked about the *product*, and how much of the *process* they approve — and wanting one without the other is the ordinary case. `interview` is that case; `manual` is `interview` plus the two artifact gates, and nothing else.

- **Announce the resolved mode and offer the others, once, before Phase 1.** The user must never discover the mode by noticing questions that did or did not arrive — and they cannot ask for a mode they do not know exists. In a chat client there is no `--help` to read: this block is the only place the dials are ever named, so it is not optional.

  ```
  Mode: semi-auto · depth: normal — I'll only ask what the task leaves undefined, then build it myself.
  Dashboard opened — it refreshes itself: http://localhost:PORT/dashboard.html
  Project memory — AGENTS.md (+ CLAUDE.md with a link). Tell me if you need a different one.

  You can switch at any time, just say:
  • "full auto" — I won't ask anything at all
  • "grill me" — I'll take the task apart with questions to the end, then build it myself
  • "manual mode" — the same plus you approve the specification and the task list
  • "strict to the brief" / "think it through deeply" — less or more elaboration beyond what was said
  • "polish it" — at the end I'll compare against the benchmark and finish it off; longer and more expensive
  ```

  With `polish` on, the first line names it and its ceiling: "Mode: semi-auto · depth: normal · polish: up to three rounds".

  **The dashboard line carries the address whenever there is one** (`phases/0-instruments.md` §3, Path A). Depending on the client the page may open beside the chat or arrive as a card with an "Open" button, and in the second case this line is the only way to the dashboard that does not depend on finding the button. Without a server (Path B) the line names the file instead: "Dashboard opened — `.neopilot/dashboard.html`, it refreshes itself."

  One short block, once, at the start. **It is a hint, not a question** — say it and go straight into Phase 1; waiting for a reply to it is exactly the pause this skill exists to remove. Do not repeat it later, do not restate it after a mid-run switch (one line is enough there: "Got it, manual mode from here").
- **Ambiguity resolves to semi.** A mode word contradicting the rest of the sentence ("manual mode, but don't ask") → the explicit mode word wins; two mode words → ask which one, in one line.
- **The mode can be switched mid-run** ("switch to manual") — it applies from the next phase onward. Phases already passed are not replayed.
- **Extra instructions in the brief** (stack, language, budget, "no database", deadline) are manifest requirements like any other. They constrain the build; they never replace a phase.
- **No mode removes the manifest gates or the safety gates.** Irreversible or outward-facing actions — deploy, publish, pay, send messages to third parties, delete data, rewrite git history — stay a question in **all four** modes, including full.

## Depth

How far past the brief's own words the spec is allowed to go. The mode decides *how much the user is asked*; depth decides *how much is worked out for them*. They are independent.

| Depth | Triggers | Deepening a requirement (`R##.n`) | New capabilities (`A##`) |
|---|---|---|---|
| **strict** | `/neopilot strict`, "strict to the brief", "only what I said", "don't add anything", "strictly as written", "nothing extra" | only what the requirement cannot work without | **not allowed** |
| **normal** **(default)** | nothing specified | freely, by judgement — as much as the feature warrants | allowed, with a parent, within proportion |
| **deep** | `/neopilot deep`, "think it through deeply", "maximum depth", "think for me", "go deep", "think it through" | the full depth pass, every dimension, every requirement | actively encouraged, same two limits |

- **Default is normal, and normal means permitted.** The agent elaborates where elaboration obviously helps and does not chase every edge of every requirement. This is the setting most briefs should run on.
- **`strict` does not mean careless.** Errors and empty states are still handled — a build that crashes on bad input does not satisfy the requirement it was written for. What `strict` removes is anything the user did not ask for: no extra capabilities, no anticipating needs, no "while I'm here, let me add".
- **`deep` does not lift the attachment rules.** Every `A##` still names its parent requirement; the proportion limit still holds. `deep` buys thoroughness, never a different project.
- **`deep` also turns on the adversarial pass** — the premortem over the brief in `phases/2-briefing.md`, which asks where the idea itself comes apart rather than where a requirement is underspecified. It runs at `deep` in **every** mode, and in `interview` and `manual` at every depth, because taking the task apart is what those modes are for. The mode then decides what happens to what it finds: a question, or an `ASSUMPTION` decided for the user.
- **Depth is announced with the mode**, in the same opening block: "Mode: semi-auto · depth: maximum".
- **Depth can be changed mid-run** ("less invention", "think deeper") — applies from the next phase. Already-written spec sections are not retroactively trimmed unless the user asks.

The rules for each level live in `phases/3-spec.md`.

## Polish

**Off by default.** One bare word turns it on, and it is the only parameter that costs the user real money and real time rather than just attention.

| | Triggers | What it adds |
|---|---|---|
| **polish** | `/neopilot polish`, "polish it", "make it perfect", "compare against the benchmark", "don't stop until it's right", "budget doesn't matter, the result does" | after the blind acceptance, up to three rounds of comparing the running build against the user's own reference and fixing the differences |

It is a separate dial because depth decides how much is worked out *before* the code exists and polish how much is corrected *after*: a `strict` brief can deserve a flawless finish, and a `deep` spec can be right the first time.

Two things are decided here; everything else — the critic's prompt, the filter, the stop conditions, the bookkeeping — is in `phases/polish.md`, **read only when the parameter is on.**

- **It measures against a reference, never against taste.** No `reference.md` with something comparable in it → the loop says so in one line and does not run. A critic with nothing to compare against invents a standard, and the run then pays for chasing it.
- **Its findings become tickets**, cut and flown and reviewed and committed like any others. Nothing about polish bypasses Phase 6 or the green suite; it is more work of the same kind, not a different kind of work.

Announced with the mode and depth in the opening block, ceiling named: "polish: up to three rounds".
