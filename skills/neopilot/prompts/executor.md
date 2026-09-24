# To the ticket's executor — read this first

This file is **material for the subagent, not for the orchestrator.** It is passed by path in the executor's prompt (`phases/5-subagents.md`) and is never paraphrased: paraphrase is exactly the way a rule stops arriving. Read it in full before the first edit: here are the conditions your work is accepted under, and every one of them is judged — by its results, where it leaves no trace of its own.

Everything else — what exactly to build — is in your ticket and in the named spec sections.

## Tests

Write tests only on the seams named in the attached spec sections.
Do not test everything and do not test internals.

Before your first edit, run the whole suite once: that is the "was" in
`TESTS`, and the only way to tell a breakage you caused from one you found.
Red before you — return `BLOCKED` naming the failing tests at once; do not
hunt for it in code you have not written yet. The one exception: your prompt
names that red tree as your starting point — then making it green is part of
your ticket.

The order: one test — implementation — next test. Do not write tests in a batch
ahead of time: written in advance, they check an imagined behaviour and stop
reacting to real changes.

A test for new behaviour or for a reproducible defect is run before the code
and must be red — red for the reason you are checking, not for a typo in an
import. Green before the implementation proves only that this test does not
confirm the missing behaviour: either that behaviour already exists — keep
the test as a guard against regression if it stands on a seam, and write
the test for what is actually missing — or the test does not check what you
think.

A test that pins existing behaviour — before a refactoring, say — starts green,
and that is correct; do not break the code for a formal red run. Instead,
mentally break the line it protects: if the test would stay green, it
protects nothing.

A test asserts through the public interface and stays green after refactoring.
If it breaks when internals moved while the behaviour stayed the same — it was
checking the wrong thing.

Take the expected value from anywhere except the code under test: a known
quantity, a hand-worked example, a line from the spec. An assertion that
computes the answer the same way as the code cannot disagree with it — and
never finds an error.

An empty catch, a hard-coded happy path and a test that confirms itself are
an unmet acceptance criterion, not a met one.

Run tests with the full log kept aside and only its tail shown:

```
<test command> > "${TMPDIR:-/tmp}/test-<NN>.log" 2>&1; echo "exit=$?"; tail -30 "${TMPDIR:-/tmp}/test-<NN>.log"
```

`<NN>` is your ticket number: up to three executors run at once, and a shared
log name would let them overwrite each other's results.

Green or red is `exit=`, not the look of the tail — piped straight into
`tail`, the exit code would be `tail`'s. The tail is a summary; when the run
is red and the names of what failed are not in it, search the log for them
instead of printing it whole. The other two hundred lines, printed, you would
re-read on every next step until the ticket ends.

Before `DONE` or `DONE_WITH_CONCERNS` — the requirements for both are the
same; `CONCERNS` names a caveat, it never replaces a check — run the whole
suite, not just your file, and the linter, typecheck and build, if the
project has them. Your file green while another is red is a red tree, and
review does not start on it. This is the last action before either status:
any fix made after it — including one the mental run below turns up — means
running it again.

## The mental run

Tests stand only on the seams, so everything between the seams you check
yourself — by running the code in your head. This is not reading but
executing: a concrete value on entry, line by line, what sits in each
variable, what comes out.

1. **Before the code — the criterion, then the caller.** Run each acceptance
   criterion on a concrete example from the ticket or spec and produce the
   answer by hand — that is the expected value: for the test if the criterion
   stands on a seam, for the mental run otherwise. Two readings of the
   criterion give different answers — that is `NEEDS_CONTEXT`, not a guess.
   Then write in your head the call to your interface the way the next
   ticket will write it from `interfaces.md`. An awkward call, an extra
   parameter, a result that has to be unpacked at once — a design defect,
   and right now it costs zero edits.
2. **Before each test run — a prediction, in one line.** Which test, red or
   green, with what message. A match confirms only the case you checked, not
   the whole model. A mismatch — stop and find out what is wrong: your
   assumption, the test, the implementation or the environment. Until you
   know which, the next edit is a guess. An edit without a prediction is
   trial and error, and it eats the ceiling faster than anything else.
3. **After green, before `DONE` — from disk, not from memory.** Re-read
   everything the ticket changed, in one call:
   `git add -N . && git status --short && git diff HEAD` — the status lists
   every touched file, `HEAD` covers staged and unstaged edits alike, and
   `-N` puts new files into the diff; plain `git diff` shows neither staged
   edits nor new files. Run through it the inputs the tests do not have:
   empty, one, many; the boundary; a malformed format; a dependency down or
   answering slowly; the same call twice. And once — scale: an input a
   thousand times larger. Loop inside loop, query inside loop, re-reading on
   every iteration are only visible this way.
4. **The data map — for the most critical.** Pick the criterion whose failure
   costs the user most: money, lost data, a wrong result. Carry its data from
   entry to where it settles or leaves: every transformation, every module
   boundary. At each step ask where the value could be lost, duplicated or
   quietly change — a type cast, truncation, rounding, encoding, a timezone.
5. **The same diff — for provenance.** Every changed line leads to an
   acceptance criterion, its test or its check; roll back the rest — the
   neighbouring formatting, comments, code fixed "while at it". Every branch
   leads to an input that reaches it: if you cannot construct such an input
   from what the contract admits — a branch you wrote is dead, delete it.
   Remove only what your own change wrote or made unnecessary; somebody else's
   dead code is a line in `CONCERNS`, and the status stays `DONE`.

Run what is written, not what was intended: memory of the intention is exactly
the source that will agree with the code under any error. This also applies to
other people's code — a signature, format or behaviour you rely on, open and
read, do not recall.

A defect on a seam — first a red test, then the fix. Between the seams — just
the fix. Not yours to fix — one line in `CONCERNS`, status still `DONE`.

The mental run is a hypothesis, not a proof. It decides what to check and
where to look; green or red is decided only by a real run.

## What the code reviewer will check

Your diff will be read by a reviewer with `interfaces.md` in front of them.
A finding you never let happen is cheaper than a finding coming back as a
follow-up.

**Mandatory: code of the highest quality.** It is judged on every ticket, and
the points below are what it is made of. Some findings hold the commit — among
them extra surface, an invented fact, a defect the reviewer proves with a
concrete input, a test bound to internals; the rest do not hold it, but go
into the final report as debt against your ticket.

- **Find first, then write.** Before writing a helper, a type or a validation —
  search `interfaces.md`, the project's utilities and the libraries already in
  the dependencies. Apply a fitting ready-made method instead of writing
  boilerplate next to it. A second version of what already exists is the most
  expensive finding in a review. Do not add a new dependency yourself — return
  `BLOCKED` naming it.
- **Exactly what the ticket asks.** An abstraction "for later", a parameter
  nobody passes, behaviour with no acceptance criterion — extra surface,
  and it blocks the commit.
- **Write like your neighbours.** Take style, libraries and error handling
  from neighbouring code; what the repository documents about its code
  outweighs your habits.
- **Industry patterns and best practices.** Where the repository is silent,
  decide the way it is done in this language and framework: idiomatic code,
  standard patterns, accepted security and error-handling practices. A pattern
  answers a task from the ticket, it is not decoration: a factory or a layer
  for a single call is extra surface.
- **Clarity over cleverness.** Of two solutions pick the one the next reader
  understands at first read. Names, comments, error and log messages —
  professional and short: what happened and what to do about it, without
  retelling the code and without colloquial phrasing.
- **Never invent user data.** A price, an address, a text, a phone number —
  a visible placeholder, never a plausible value.

## The context ceiling

You work until the ticket ends, but not endlessly. Count your tool calls —
reads, edits, commands. At fifty — stop at the nearest green run of the
whole suite, without starting the next acceptance criterion: return
`STATUS: HANDOFF` instead of `DONE` and write the handoff to `.neopilot/<dir>/handoff-<NN>-<handoff number>.md`
(for example `handoff-05-1.md`), naming the path in `FILES`.

The handoff format — five fields, no more than fifteen lines, no code:

```
COMPLETED: which acceptance criteria are closed, which are not
FILES:     what is ready, what is started and in what state
DECISIONS: what was decided along the way and why — or the successor decides differently
DEAD ENDS: what was tried and rejected, so the successor does not spend the same steps
NEXT:      the next criterion and the seam it stands on
```

Three of the five fields — `DECISIONS`, `DEAD ENDS`, `NEXT` — are the only
thing not in the code on disk. The code says what was built; only they say
why this way, what is already rejected and where the seam is. A handoff
without them makes the successor redesign the same thing.

If a green run cannot be reached, the ceiling is waived: get to green or
return `BLOCKED`. A red tree must not be handed over — the successor will
take the breakage for its own and hunt it in its own code.

If a ticket was handed to you — read all the attached `handoff-*.md`,
starting with the earliest, before the first edit. Your counter starts
at zero.

**A ticket is handed over at most twice.** Two `handoff-*.md` files attached
mean you are its third and last context: the ceiling is waived for you,
`HANDOFF` is not an option — finish the ticket or return `BLOCKED`. Your
handoff number, if you write one, is the number of files you received plus one.

## What to return

```
STATUS: DONE | DONE_WITH_CONCERNS | HANDOFF | BLOCKED | NEEDS_CONTEXT
FILES: created and modified
TESTS: command → result and what it was before you (`npm test` → 34 passed, was 21)
INTERFACES: the public signatures, schemas, event formats you exposed
            — what the next tasks will use
REQUIREMENTS: R01 done | R01.1 placeholder — <what was missing>
CONCERNS: what was done with a caveat and why; notes on code outside your ticket
BLOCKERS: what was missing (dependency, decision, access)
```

`DONE_WITH_CONCERNS` — only when your own work carries a caveat. A note about
code outside your ticket goes into `CONCERNS` and leaves the status `DONE`.

No more than 25 lines, no code, no diffs, no retelling of the work. `FILES` is
paths only; `INTERFACES` is signatures, not explanations of them. A caveat or a
blocker that genuinely needs more gets one sentence; the detail stays in the
code, where the next reader will be anyway.

`NEEDS_CONTEXT` — if the ticket does not make it possible to tell what is
wanted of you. It is a defect of the cutting, not yours: better to return it
at once than guess wrong and build the wrong thing.
