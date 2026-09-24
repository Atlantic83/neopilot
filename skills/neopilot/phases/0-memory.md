# Phase 0 — Raising the project memory

Two things happen here and nothing else: **pick the file, write the skeleton.** What may be appended during the build, the full description written from the finished code, and the ADRs all live in `phases/9-memory.md` and are read when they happen — the second inside Phase 5, the last two in Phase 8. None of it applies until the build is over.

## Which file

The repo needs a file that tells the **next** session what this project is — `CLAUDE.md` or `AGENTS.md`. Decided by detection, in this order. Stop at the first match.

| Check | File |
|---|---|
| `CLAUDE.md` already exists | `CLAUDE.md` |
| `AGENTS.md` already exists | `AGENTS.md` |
| both exist | the one that already holds the project description; if neither does, `AGENTS.md` — and **leave the other file alone** |
| `.claude/` directory, or `$CLAUDECODE` / `$CLAUDE_CODE_ENTRYPOINT` is set | `CLAUDE.md` |
| `.cursor/` directory | `AGENTS.md` |
| `.codex/` directory, or `.github/copilot-instructions.md` | `AGENTS.md` |
| nothing matched | `AGENTS.md` as the real file **+ `CLAUDE.md` containing one line: `See @AGENTS.md`** |

- **An existing file always wins over detection.** The repo has already answered the question; asking it again is how you end up with two half-filled memory files.
- **The pointer file is written only in the fallback case.** When the agent was identified, one file is enough — a second file is a second thing to keep in sync, and it will not be kept in sync.
- **Never duplicate the text into both files.** Two copies of a project description drift within one run.
- Record the choice in `state.js` as `memoryFile`, so a resume does not re-derive it.

**This is never a question for the user** — in any mode, including manual. It is a process decision, like where ticket files live, and Phase 0 answers those itself. It is not, however, a *secret* decision: one line in the opening block, together with the mode.

> Project memory — `AGENTS.md` (+ `CLAUDE.md` with a link). Tell me if you need a different one.

Say it and move on. **Do not wait for an answer** — if the user names a different file later, switch and move the block; renaming a markdown file costs nothing, which is exactly why this never earned a gate.

## The skeleton

Cheap, written before anything is built, and it is what survives an interrupted run. Only what is already known — everything NeoPilot writes sits between the two markers, in every case, including a file it created itself:

```markdown
<!-- neopilot:start -->
# <Project name>

<One line: what this is and who it's for.>

## Commands

| Command | What it does |
|---------|--------------|
| `<install>` | Install dependencies |
| `<run>` | Run locally |
| `<tests>` | Run tests |

## How NeoPilot works here

The build is driven by the `/neopilot` skill. Requirements, specification and
tasks — in `.neopilot/`. Progress — `.neopilot/dashboard.html`. The rule: a
requirement from `manifest.md` can only be dropped by the user.

If work is resuming — say "resume neopilot": the state is picked up from
`.neopilot/state.js`, nothing needs to be re-asked.
<!-- neopilot:end -->
```

Commands that are not known yet are simply absent. **An invented command is worse than a missing one** — the next session runs it, it fails, and now the whole file is suspect.

**Anything the user wrote outside the markers is untouchable.** A brownfield repo whose `CLAUDE.md` carries a team's hard-won rules must come out of an NeoPilot run with those rules intact. If the markers are missing on a later run but NeoPilot's sections are recognisably there, wrap them — do not append a second copy. The reasoning is in `phases/9-memory.md`.

In the third Phase 0 case — a configured repo starting a new feature — the memory file already exists: **top it up, do not rewrite it.** The skeleton is written once, in the run that created the repo.
