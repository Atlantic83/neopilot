# Fix plan: sync.py must not spawn orphaned http.server processes

> Execution instructions. Diagnosis confirmed by reproduction on Windows
> (2026-09-18): three `sync.py` invocations → three live `python -m http.server`
> processes on ports 61189/61194/61489, with `serve.pid` aware only of the last one.

## Diagnosis

All process identification in `serve()` is built on `ps`:

- `ps -p <pid> -o command=` (`cmdline`, sync.py:91) — Git Bash/cygwin `ps`
  has no `-o` flag, and it cannot see native Windows processes at all → always `""`.
- `ps -Ao pid=,command=` (orphan cleanup, sync.py:136) — no `-A` flag →
  empty output → kills nothing. The call isn't wrapped in try/except: where
  `ps` isn't in PATH at all (cmd/PowerShell), sync.py crashes mid-run with
  `FileNotFoundError`.
- Net result on Windows: the "server is alive" early-return never fires
  (`is_ours("")` = False), cleanup is empty, the previous port is held by a
  live server → `free_port` silently picks a random one → `Popen` brings up
  yet another server. Every call = +1 orphan, and the link changes.
- The Phase 8 kill block (`phases/8-final.md`:249-257) uses the same
  `pgrep -f` / `ps -o command=` → final cleanup on Windows also finds no
  processes → orphans outlive the run forever.

## Fix idea

Prove "ours" without any process listing at all. The server serves directory
`A`, so over HTTP it serves this run's files. Introduce a journal
`serve.pids` (append-only, `"port pid"` lines — every server the run has ever
started). The process on port `P` is ours if and only if
`GET http://127.0.0.1:P/serve.pids` returns 200 and contains the line
`"P <pid>"`. A foreign process holding the port won't serve such a file; this
test finds an orphan more reliably than `ps`, and it works everywhere —
Windows, Unix, without a single external command.

## Changes — `skills/neopilot/tools/sync.py`

### 1. Constants (after line 37)

```python
PIDS = os.path.join(A, "serve.pids")   # journal of all servers started by the run
```

### 2. Delete `cmdline()` (89-94) and `is_ours()` (97-99)

Unused anywhere after the fix.

### 3. New helpers (in place of the deleted ones)

```python
def fetch(port, path):
    """Response body from the server on the port, or None. The only "ours" check."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=2) as r:
            return r.read().decode("utf-8", "replace") if r.status == 200 else None
    except (urllib.error.URLError, OSError, ValueError):
        return None


def serves_us(port, pid):
    """The port is served by this run's server: it serves serve.pids containing "port pid"."""
    body = fetch(port, "/serve.pids")
    return body is not None and ("%d %d" % (port, pid)) in body.splitlines()


def known():
    """All (port, pid) pairs the run has ever started."""
    try:
        for line in open(PIDS):
            parts = line.split()
            if len(parts) == 2:
                yield int(parts[0]), int(parts[1])
    except (OSError, ValueError):
        return


def kill_ours():
    """SIGTERM to every live server of this run. Returns the killed ports."""
    dead = []
    for port, pid in known():
        if serves_us(port, pid):
            try:
                os.kill(pid, 15)                     # on Windows — TerminateProcess
                dead.append(port)
            except OSError:
                pass
    return dead


def wait_down(ports, tries=20):
    """Wait until the killed ports are freed — otherwise the old port loses the race."""
    for _ in range(tries):
        if all(fetch(p, "/serve.pids") is None for p in ports):
            return
        time.sleep(0.1)
```

Keep `http_ok()` — it's used in the probe loop after `Popen` (where we need
exactly `/dashboard.html` and status 200). Add `import time`; `import re` —
already dead, don't touch (surgical).

### 4. `serve()` (124-166) — replace the middle

```python
    port, pid = recorded()
    if port and pid and serves_us(port, pid):
        return "server alive: http://localhost:%d/dashboard.html" % port

    wait_down(kill_ours())          # this run's orphans; no foreign ones here

    port = free_port(port)
    ...
    for _ in range(10):
        if http_ok(port):
            open(PIDS, "a").write("%d %d\n" % (port, srv.pid))   # journal before the pointer
            open(PIDF, "w").write("%d %d\n" % (port, srv.pid))
            return "server up: ..."
```

### 5. After `srv.terminate()` (line 165) — `srv.wait()`

Reaps the zombie that lingers until sync.py exits.

### 6. `main()` — `--kill` mode at the very top, before `read_state()`

```python
    if "--kill" in sys.argv:
        wait_down(kill_ours())
        for f in (PIDF, PIDS, LOG):
            try:
                os.remove(f)
            except OSError:
                pass
        print("server stopped")
        return
```

Doesn't require `state.js`, doesn't touch the snapshot. Replaces the Phase 8
bash block.

## Changes — `skills/neopilot/phases/8-final.md` (249-261)

Replace the bash block with:

```bash
A=$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)/.neopilot
( sleep 12; python3 "$A/sync.py" --kill ) >/dev/null 2>&1 &
```

Rewrite the prose after the block in the same spirit, dropping the
`pgrep`/`ps` rationale: the meaning stays — kill follows this run's
`serve.pids`, "ours" is proven by the process serving the journal containing
that line; a foreign process on the port won't serve such a file. Leave the
twelve-second paragraph untouched.

## Verification (Windows, all steps reproducible)

1. Fixture: `state.js` + `dashboard.html` with markers + `sync.py` → two
   launches → the second prints "server alive" on the **same port**;
   `netstat` — one LISTENING, `tasklist` — one python.
2. Orphan: manually start a second `http.server` on another port, append
   its `"port pid"` to `serve.pids` → `sync.py` → the orphan is dead, the
   previous port kept, link unchanged.
3. Foreign process on a recorded port: kill the server, start an
   `http.server` of a different directory on that port → `sync.py` → doesn't
   recognize it as its own, doesn't kill it, starts on a free port.
4. `sync.py --kill` → all of the run's servers dead, `serve.*` removed.
5. `finishedAt` in state.js → server doesn't start (already exists, regression).
6. Launch outside Git Bash (cmd/PowerShell) → not a single `ps` call, no
   crashes.
