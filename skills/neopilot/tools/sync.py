#!/usr/bin/env python3
"""Mirrors state.js into the dashboard page itself and keeps the server alive.

Run after every edit of .neopilot/state.js — one line, no arguments:

    python3 .neopilot/sync.py

Does exactly three things, in this order:

  1. Checks that state.js parses. A broken file goes no further: the snapshot
     on the page stays as it was rather than being overwritten with garbage.
  2. Writes the state into dashboard.html between the markers — atomically,
     through a temp file beside it. If it dies halfway, the intact old page
     is what remains. That is how the dashboard shows data even when opened
     as a file, from a pane via data:, with a dead server, or a month after
     the run.
  3. Checks whether this run's static server is alive and raises it on the
     same port if not; along the way it kills this run's orphaned servers.
     "Ours" is proven without a process list or ps: the process on the port
     serves serve.pids containing its own "port pid" line, which a foreign
     process cannot serve. The same port — so the link the user already
     copied keeps working.

Flags: --no-serve — snapshot only, do not touch the server; --kill — stop all
of the run's servers and remove serve.*; on a landed run it first waits for
the page to fetch the final state.js — the request is visible in serve.log
(Phase 8 calls it after the final report, and the sync at landing calls it
as a detached process, so no orphan lives forever);
--enter <stage> — a transition: marks the stage active+startedAt and moves
the pulse; called before the new phase's first edit — a mark placed after
the work gifts its minutes to the stage still active. Fields are written the
same way — by command, not by hand-editing JSON: --set <path> <value>
(tickets.04.status, now — the current timestamp), --add appends to a list,
--inc bumps a counter by 1.

Prints nothing to the chat on its own: one line on stdout, read by the agent.
"""

import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone

A = os.path.dirname(os.path.abspath(__file__))          # this run's .neopilot
STATE = os.path.join(A, "state.js")
PAGE = os.path.join(A, "dashboard.html")
PIDF = os.path.join(A, "serve.pid")
PIDS = os.path.join(A, "serve.pids")                    # every server the run ever raised
LOG = os.path.join(A, "serve.log")
FMARK = os.path.join(A, "serve.final")              # serve.log offset at landing
BEGIN, END = "/*STATE-BEGIN*/", "/*STATE-END*/"


def fail(msg):
    print(msg)
    sys.exit(1)


def read_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        fail("no state.js yet — snapshot not written, server untouched")
    head = raw.split("\n", 1)[0]
    body = raw.split("=", 1)[1] if head.startswith("window.STATE") else raw
    try:
        return json.loads(body.strip().rstrip(";")), raw
    except json.JSONDecodeError as e:
        # This was the "file got mangled" failure mode: before, it was only
        # visible as a blank page; now it is a line with the line number,
        # right after the write.
        fail("state.js does not parse (line %d: %s) — snapshot left as it was" % (e.lineno, e.msg))


INDEX = os.path.join(A, "index.html")
INDEX_SHIM = ('<!doctype html><meta charset="utf-8">'
              '<meta http-equiv="refresh" content="0; url=dashboard.html">'
              '<script>location.replace("dashboard.html")</script>\n')


def ensure_index():
    """The server's root is index.html. We keep it a permanent redirect to
    dashboard.html: a copy of the page under that name is never updated by
    anything, and "/" would open a stale copy. The shim contains no
    snapshot — it has nothing to go stale."""
    if os.path.islink(INDEX):
        return                                            # a real symlink — serves the live page
    try:
        cur = open(INDEX, encoding="utf-8").read(400)
    except OSError:
        cur = ""
    if BEGIN not in cur and "dashboard.html" in cur:
        return                                            # already a shim or our redirect
    try:
        tmp = INDEX + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(INDEX_SHIM)
        os.replace(tmp, INDEX)
    except OSError:
        pass                                              # the root serves a listing — not fatal


def write_snapshot(state):
    """The snapshot into the page. Returns text for the report."""
    ensure_index()
    try:
        page = open(PAGE, encoding="utf-8").read()
    except FileNotFoundError:
        return "no dashboard.html — re-copy it from the skill"
    i, j = page.find(BEGIN), page.find(END)
    if i < 0 or j <= i:
        return "the page has no snapshot markers — re-copy dashboard.html from the skill"
    # </ inside <script> would close the tag and tear the page; < is safe in JSON.
    payload = "window.STATE=" + json.dumps(state, ensure_ascii=False).replace("</", "<\\/") + ";"
    new = page[: i + len(BEGIN)] + payload + page[j:]
    if new == page:
        return "snapshot already matched"
    tmp = PAGE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(new)
        os.replace(tmp, PAGE)                            # atomic: a broken page cannot happen
    except OSError as e:                                 # page locked by a reader, the disk
        try:
            os.remove(tmp)
        except OSError:
            pass
        return "snapshot not written (%s)" % e
    return "snapshot written"


def _done(buf):
    """The response is fully assembled: headers arrived and the body is no
    shorter than Content-Length."""
    head, sep, body = buf.partition(b"\r\n\r\n")
    if not sep:
        return False
    m = re.search(br"(?im)^content-length:[ \t]*(\d+)", head)
    return m is not None and len(body) >= int(m.group(1))


def fetch(port, path):
    """The body of the server's response on the port, or None.

    A raw socket, not urllib: there the timeout was per single read, and a
    listener dripping one byte at a time would hold the probe forever while
    r.read() accumulates the body in memory. Here the deadline is shared —
    two seconds for everything — plus a size cap: all we need is the
    "port pid" lines from small files.
    """
    deadline = time.monotonic() + 2
    buf = b""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2) as s:
            s.sendall(b"GET %s HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n" % path.encode())
            while len(buf) < 65536 and not _done(buf):
                left = deadline - time.monotonic()
                if left <= 0:
                    return "hung"                        # answers, but too slowly — alive
                s.settimeout(left)
                chunk = s.recv(8192)
                if not chunk:
                    break
                buf += chunk
    except ConnectionRefusedError:
        return None                                      # no port — provably dead
    except (TimeoutError, ConnectionError):
        return "hung"                                    # listening, but silent/resetting
    except OSError:
        return None
    head, sep, body = buf.partition(b"\r\n\r\n")
    status = head.split(b"\r\n", 1)[0].split()
    if not sep or len(status) < 2 or status[1] != b"200":
        return None
    return body.decode("utf-8", "replace")


def serves_us(port, pid):
    """True — the port is provably ours; "hung" — listening but not answering;
    False — not ours.

    The proof needs no process list: ps under cygwin cannot see native
    processes, outside a Unix shell it may not exist at all, and a foreign
    process on the port cannot serve our journal — serve.pids lives only
    in A. "hung" is neither "not ours" nor "ours": never kill on it, and
    never clean the journal on it.
    """
    line = "%d %d" % (port, pid)
    hung = False
    for path in ("/serve.pids", "/serve.pid"):
        body = fetch(port, path)
        if body == "hung":
            hung = True
            continue
        if body is not None and line in body.splitlines():
            return True
    return "hung" if hung else False


def pid_alive(pid):
    """The process exists — without a process list.

    The dead/slow distinction via socket is unavailable where RST is
    filtered: on such a Windows machine an empty port raises TimeoutError
    just like a hung one. The discriminator is the process itself: journal
    entries are ours, OpenProcess on them always has rights. EPERM also
    means "exists". On Windows os.kill(pid, 0) is CTRL_C_EVENT, not a probe,
    hence ctypes.
    """
    if sys.platform == "win32":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)   # QUERY_LIMITED_INFORMATION
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
        return bool(h)
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def known():
    """All (port, pid) pairs the run has ever raised."""
    try:
        with open(PIDS) as f:
            lines = f.readlines()
    except OSError:
        return
    for line in lines:
        parts = line.split()
        if len(parts) == 2:
            try:
                yield int(parts[0]), int(parts[1])
            except ValueError:
                continue


def kill_ours(spare=None):
    """SIGTERM to every live server of this run except spare. Returns ports.

    Dead entries are struck from the journal: a "port pid" pair will not
    come back to life, and a file that only grows would stretch every next
    pass. Before replacing it the journal is re-read: a line appended by a
    parallel launch in mid-run must not be lost — without it that server
    would become an unregistered orphan.
    """
    dead, live, dropped = [], [], False
    entries = list(known())
    for port, pid in entries:
        if (port, pid) == spare:
            live.append((port, pid))
            continue
        if not pid_alive(pid):
            dropped = True                           # no process — provably dead
            continue
        live.append((port, pid))                     # alive — the entry stays,
        if serves_us(port, pid) is not True:         # but without proof
            continue                                 # it is never killed
        try:
            os.kill(pid, 15)                         # on Windows — TerminateProcess
            dead.append((port, pid))
        except OSError:
            pass
    if dropped:
        seen = set(entries)
        try:
            with open(PIDS + ".tmp", "w") as f:
                for port, pid in live:
                    f.write("%d %d\n" % (port, pid))
                for port, pid in known():              # keep what was appended mid-run
                    if (port, pid) not in seen:
                        f.write("%d %d\n" % (port, pid))
            os.replace(PIDS + ".tmp", PIDS)
        except OSError:
            pass
    return dead


def wait_down(killed, tries=20):
    """Wait for the killed (port, pid) to die — or the old port loses the race.

    By pid, not by port: a process death is a precise, instant fact, while
    a socket on a machine with RST filtering would keep "answering" with a
    timeout for two more seconds.
    """
    for _ in range(tries):
        if all(not pid_alive(pid) for _, pid in killed):
            return
        time.sleep(0.1)


def _landed():
    """Is the run landed? A mangled or missing state.js means "no": --kill
    must still stop servers with a broken state; it only waits on an honest
    finish."""
    try:
        with open(STATE, encoding="utf-8") as f:
            raw = f.read()
        head = raw.split("\n", 1)[0]
        body = raw.split("=", 1)[1] if head.startswith("window.STATE") else raw
        st = json.loads(body.strip().rstrip(";"))
    except (OSError, ValueError, IndexError):
        return False
    return isinstance(st, dict) and bool(st.get("finishedAt"))


def wait_page_saw(cap=75):
    """Wait for the open page to fetch the final state.js.

    A timer could never beat the poll here: a background tab asks once a
    minute, and any "wait N seconds" cut the server before the last render.
    http.server writes every request to stderr → serve.log, and the final
    sync marked in serve.final where the log stood at landing: a
    GET /state.js past that mark already carried the final state — the file
    does not change after it. No mark (the finish was written without
    sync) — we watch from the end of the log as it is now: a page that has
    not seen the finish keeps polling and will ask; one that has stays
    silent forever — we leave by the cap. The cap also covers the pane that
    will never ask — a closed one or a data:-origin; for it the snapshot
    inside the page tells the truth.
    """
    if not any(pid_alive(pid) for _, pid in known()):
        return False                                        # nobody to wait for
    try:
        with open(FMARK) as f:
            base = int(f.read())
    except (OSError, ValueError):
        try:
            base = os.path.getsize(LOG)
        except OSError:
            return False                                    # no log — no requests visible
    end = time.time() + cap
    while time.time() < end:
        try:
            with open(LOG, encoding="utf-8", errors="replace") as f:
                f.seek(base)
                if '"GET /state.js' in f.read():
                    return True
        except OSError:
            return False                                    # log gone — nothing to wait on
        time.sleep(0.5)
    return False


def recorded():
    try:
        with open(PIDF) as f:
            port, pid = f.read().split()
        return int(port), int(pid)
    except (OSError, ValueError):
        return None, None


def write_pointer(port, pid):
    """serve.pid — atomically, like everything in this file.

    A mangled pointer is worse than a missing one: recorded() returns None,
    the live server from the journal gets killed as an orphan, and the
    address moves to a random port — the pane is left on a dead one.
    """
    try:
        with open(PIDF + ".tmp", "w") as f:
            f.write("%d %d\n" % (port, pid))
        os.replace(PIDF + ".tmp", PIDF)
    except OSError:
        pass


def detached():
    """How to detach the server from its parent.

    start_new_session is POSIX-only: on Windows it is silently ignored, and
    without DETACHED_PROCESS the server inherits the console and dies with
    it.
    """
    if sys.platform == "win32":
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP
                                 | subprocess.DETACHED_PROCESS}
    return {"start_new_session": True}


def free_port(prefer):
    """The old port if free, else any. A stable address beats a random one."""
    for p in ([prefer] if prefer else []) + [0]:
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            return s.getsockname()[1]
        except OSError:
            continue
        finally:
            s.close()
    return None


def serve(state):
    if state.get("finishedAt"):
        # The page needs the server for one more fetch — the final state.js.
        # Killing it here and now would leave the pane on "in progress"
        # forever — which is exactly what a landed run used to look like.
        # The detached --kill waits for the fetch in serve.log and stops
        # everything itself; if Phase 8 never got to it, it gets done here —
        # either way there is no orphan.
        try:
            subprocess.Popen([sys.executable, os.path.abspath(__file__), "--kill"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             **detached())
        except OSError:
            wait_down(kill_ours())
        return "run landed — the server waits for the final fetch and then stops"
    if os.environ.get("SSH_CONNECTION") or os.environ.get("CI"):
        return "remote session — no server"

    port, pid = recorded()
    alive = port and pid and serves_us(port, pid)
    if alive == "hung":
        # A timeout is neither a foreign port nor a dead server: where RST is
        # filtered an empty port looks the same. A dead pid decides instantly;
        # a live one gets re-asked, or a single lag would move the link to a
        # new port.
        if not pid_alive(pid):
            alive = False
        else:
            for _ in range(3):
                time.sleep(0.3)
                alive = serves_us(port, pid)
                if alive != "hung":
                    break
    alive = alive is True
    journal = list(known())
    if not alive:
        # The pointer is dead or lost, but the journal may hold a server the
        # pane is already open on — kill_ours below would kill it as an
        # orphan and the address would move to a random port. Search from the
        # end: that is the last announced one. What we find becomes the
        # pointer — the address stays the same.
        for p, i in reversed(journal):
            if (p, i) == (port, pid):
                continue                             # just checked
            if pid_alive(i) and serves_us(p, i) is True:
                port, pid, alive = p, i, True
                write_pointer(port, pid)             # pointer restored
                break
    # This run's orphans — on every call, not only before a raise: next to a
    # live server an orphan serves nobody either, and nothing else kills it.
    wait_down(kill_ours(spare=(port, pid) if alive else None))
    if alive:
        return "server alive: http://localhost:%d/dashboard.html" % port

    old = port or (journal[-1][0] if journal else None)
    port = free_port(old)
    if not port:
        return "no port found — the dashboard opens as a file: %s" % PAGE
    moved = (" · previous port %d taken — link moved: re-point the pane"
             % old if old and port != old else "")
    try:
        if os.path.getsize(LOG) > 1 << 20:              # the log needs a ceiling too
            os.replace(LOG, LOG + ".1")                  # one generation back
    except OSError:
        pass                                             # no file, or it is busy
    try:
        log = open(LOG, "a")
        try:
            srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port),
                                    "--bind", "127.0.0.1", "--directory", A],
                                   stdout=subprocess.DEVNULL, stderr=log,
                                   **detached())               # outlives the agent session
        finally:
            log.close()                                  # the child has its own descriptor copy
    except OSError as e:
        return "server failed to start (%s) — the dashboard opens as a file: %s" % (e, PAGE)
    with open(PIDS, "a") as f:                         # journal before probe and pointer
        f.write("%d %d\n" % (port, srv.pid))
    for _ in range(10):
        # Not http_ok but proof: a "200 on dashboard" could also come from
        # another run's server that won the bind race — its journal does not
        # contain our line.
        if serves_us(port, srv.pid) is True:
            write_pointer(port, srv.pid)
            return "server up: http://localhost:%d/dashboard.html%s" % (port, moved)
        try:
            srv.wait(timeout=0.5)
            break
        except subprocess.TimeoutExpired:
            continue
    srv.terminate()
    try:
        srv.wait(timeout=5)                          # not forever: the child could hang
    except subprocess.TimeoutExpired:
        srv.kill()
        srv.wait()
    return "server did not respond — the dashboard opens as a file: %s" % PAGE


ORDER = ["preflight", "manifest", "briefing", "spec", "plan", "build", "review", "final"]


def close_passed(state):
    """Closes the stages the run has already passed. Returns the closed ones.

    An invariant, not an event: nothing earlier than the active stage may
    also be active. So the agent only opens the next one — the previous is
    closed here, at the opening time of the new one, the very timestamp it
    would have been given by hand. Half the ritual stopped being the
    agent's work, and with it a class of errors where a transition was
    half-recorded (2026-08-19: spec stood active for two and a half hours
    beside a finished plan and a running build).

    One exception, and it is in the model of the work itself: review runs
    per ticket inside the build, so review does not close build. Anything
    later than review closes both.

    Touches nothing but active: skipped and failed are deliberate states,
    and turning them into done would erase what was said about the run.
    """
    rank = {v: i for i, v in enumerate(ORDER)}
    stages = state.get("stages") or []
    live = [s for s in stages if s.get("status") == "active" and s.get("id") in rank]
    if len(live) < 2:
        return []
    closed = []
    for s in live:
        # What comes next. Review does not count as "next" for the build: it
        # lives inside it, so it neither closes it nor gives it a close time.
        later = [o for o in live if rank[o["id"]] > rank[s["id"]]
                 and not (s["id"] == "build" and o["id"] == "review")]
        if not later:
            continue
        # We close at the moment the run moved on — the opening of the
        # nearest next stage, not the furthest: otherwise the spec would get
        # review's opening time and an hour of somebody else's work on its
        # bill.
        marks = sorted(o["startedAt"] for o in later if isinstance(o.get("startedAt"), str))
        when = marks[0] if marks else state.get("updatedAt")
        if not when:
            continue
        s["status"] = "done"
        s["finishedAt"] = when
        note = "%s closed automatically (%s)" % (s["id"], str(when)[11:19])
        # Opened and closed by one mark — meaning --enter came after the
        # work, not before it: on the dashboard the stage reads as skipped
        # (2026-09-22). Caught here, not in audit(): the record cannot be
        # fixed, but at the moment of transition the phase can still be run
        # for real.
        if s.get("startedAt") == when:
            note += " — ! zero duration: --enter after the work = the phase was skipped"
        closed.append(note)
    return closed


def save(state, before):
    """Writes state.js only if nobody touched it since our read."""
    with open(STATE, encoding="utf-8") as f:
        raw = f.read()
    if raw != before:
        return False                               # a foreign edit — do not overwrite
    head = (raw.split("=", 1)[0] if raw.split("\n", 1)[0].startswith("window.STATE")
            else "window.STATE ")
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(head + "=\n" + json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    os.replace(tmp, STATE)
    return True


def enter_stage(state, stage):
    """--enter <id>: opening a stage — the transition itself, not a note of it.

    Called before the new phase's first edit: close_passed closes the stage
    that was left at the entry mark, and work begun without the call goes
    to the neighbour. Idempotent: a stage already active keeps its
    startedAt. The pulse always moves: a transition is an edit too.
    Returns a line to print, or None.
    """
    if not stage or stage.startswith("--"):
        fail("--enter <stage id> — order: %s" % ", ".join(ORDER))
    if stage not in ORDER:
        fail("no stage %r — order: %s" % (stage, ", ".join(ORDER)))
    if state.get("finishedAt"):
        fail("the run is closed — no transitions open")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    st = next((s for s in state.get("stages") or [] if s.get("id") == stage), None)
    if st is None:
        st = {"id": stage, "status": "pending"}
        state.setdefault("stages", []).append(st)
    line = None
    if st.get("status") != "active":
        st["status"] = "active"
        st["startedAt"] = now
        st.pop("finishedAt", None)                       # re-entry — a new interval
        line = "stage %s opened (%s)" % (stage, now[11:19])
    elif not st.get("startedAt"):
        st["startedAt"] = now                            # active with no mark — the same hole
        line = "stage %s — startedAt filled" % stage
    if stage == "build":
        # Entering the build is the most frequent place a task is launched
        # unmarked: suggest the exact command before the launch happens.
        ts = state.get("tickets") or []
        first = next((t for t in ts if t.get("status") == "pending"), None)
        flying = any(t.get("status") in ("in-progress", "review", "repair")
                     for t in ts)
        if first and not flying:
            line = (line or "build stage already active") + \
                " · first task not marked — before launching: " \
                "--set tickets.%s.status in-progress" % first.get("id")
    if stage == "review":
        # Sending to review is the same hole as launching: the task went to
        # a reviewer while its status stayed in-progress. No task has been
        # through review yet — suggest the command before the send happens.
        ts = state.get("tickets") or []
        sent = any(t.get("status") in ("review", "repair", "done", "failed")
                   for t in ts)
        if not sent:
            cand = next((t for t in ts if t.get("status") == "in-progress"),
                        None) or next(iter(ts), None)
            if cand:
                line = (line or "review stage already active") + \
                    " · no task sent yet — when sending: " \
                    "--set tickets.%s.status review" % cand.get("id")
    if stage == "final":
        # Landing with live tasks — the last moment an unwritten status can
        # still be called by name rather than guessed from traces.
        open_t = [str(t.get("id")) for t in state.get("tickets") or []
                  if t.get("status") not in ("done", "failed")]
        if open_t:
            line = (line or "final stage already active") + \
                " · ! tasks not closed: %s — is their status true?" % ", ".join(open_t)
    state["updatedAt"] = now
    return line


def apply_edit(state, op, path, raw):
    """--set/--add/--inc: a point edit of state.js without hand-editing.

    The path is keys joined by dots; lists (stages, tickets) are addressed
    by element id (tickets.04.status), not by position. A --set value: the
    word now — the current ISO mark; JSON where it parses (a number,
    true/false/null, an array, an object, "a string"); otherwise the string
    as is. --add appends the value to the end of a list, --inc adds 1 to a
    number.
    A status transition stamps the interval's own edges: starting work —
    startedAt, done/failed — finishedAt; repair also bumps the repairs
    counter — a half-written transition is impossible because the edit is
    one.
    """
    keys = [k for k in path.split(".") if k != ""]
    if not keys or keys[0] not in state:
        fail("no field %r in state.js" % (keys[0] if keys else path))
    node = state
    for k in keys[:-1]:
        if isinstance(node, list):
            node = next((x for x in node if str(x.get("id")) == k), None)
            if node is None:
                fail("no %r in the list — path %r" % (k, path))
        elif isinstance(node, dict):
            nxt = node.get(k)
            if nxt is None:
                nxt = node[k] = {}                   # a null field becomes an empty object
            if not isinstance(nxt, (dict, list)):
                fail("path %r runs into a value" % path)
            node = nxt
        else:
            fail("path %r runs into a value" % path)
    last = keys[-1]
    if not isinstance(node, (dict, list)):
        fail("path %r runs into a value" % path)
    if op == "inc":
        if not isinstance(node, dict):
            fail("--inc works on a field, not a list — path %r" % path)
        cur = node.get(last)
        if cur is not None and not isinstance(cur, (int, float)):
            fail("--inc works on numbers — field %r is now %r" % (path, cur))
        node[last] = (cur or 0) + 1
        return "%s = %s" % (path, node[last])
    v = raw
    if raw == "now":
        v = datetime.now(timezone.utc).isoformat(timespec="seconds")
    else:
        try:
            v = json.loads(raw)
        except ValueError:
            v = raw
    if op == "add":
        if not isinstance(node, dict):
            fail("--add works on a list field — path %r" % path)
        lst = node.setdefault(last, [])
        if not isinstance(lst, list):
            fail("field %r is not a list" % path)
        lst.append(v)
        return "%s += %s" % (path, raw)
    if isinstance(node, list):                       # --set a whole list element
        idx = next((i for i, x in enumerate(node) if str(x.get("id")) == last), None)
        if idx is None:
            fail("no %r in the list — path %r" % (last, path))
        node[idx] = v
        return "%s = %s" % (path, raw)
    node[last] = v
    extra = ""
    if last == "status":                             # transition marks — on their own
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if v in ("active", "in-progress", "review", "repair") \
                and not node.get("startedAt"):
            node["startedAt"] = now
            extra += " · startedAt"
        if v in ("done", "failed") and not node.get("finishedAt"):
            node["finishedAt"] = now
            extra += " · finishedAt"
        if v == "repair":
            node["repairs"] = (node.get("repairs") or 0) + 1
            extra += " · repairs+1"
        if v == "in-progress" and isinstance(node, dict):
            # Launching a dependent with a live blocker: either the blocker
            # is not finished (it must not launch) or its done was never
            # recorded — the same output reminds while the launch has not
            # happened.
            byid = {str(x.get("id")): x for x in state.get("tickets") or []}
            open_b = [str(b) for b in (node.get("blockedBy") or [])
                      if byid.get(str(b), {}).get("status") not in ("done", "failed")]
            if open_b:
                extra += " · ! blockers not closed: %s — is their done recorded?" % ", ".join(open_b)
        if v in ("review", "repair") and isinstance(node, dict):
            # The task goes to a reviewer while the receiving side is not
            # set up: the stage is not open or the handles are not
            # recorded — "in review" with no reviewers, and the dashboard
            # will show it as it is.
            rst = next((s for s in state.get("stages") or []
                        if s.get("id") == "review"), None)
            if not rst or rst.get("status") == "pending":
                extra += " · ! review stage not open — --enter review first"
            revs = state.get("reviewers") or {}
            if not any(revs.values()):
                extra += " · ! reviewers not recorded — --set reviewers.<axis> <handle>"
    return "%s = %s%s" % (path, raw, extra)


def recount_reqs(state):
    """The requirements block is counted from manifest.md — the file is the
    truth, the counter a copy.

    A requirement row is a table row whose first cell is an ID like
    R03 / R19i / A01 / G02 / D04; the status is the third column. No file or
    no table — None, and the block is untouched. Hand-editing the counts is
    no longer needed: the Requirements card cannot drift from the file.
    """
    d = state.get("dir")
    if not d:
        return None
    try:
        text = open(os.path.join(A, d, "manifest.md"), encoding="utf-8").read()
    except OSError:
        return None
    count = {"done": 0, "in-ticket": 0, "in-spec": 0,
             "placeholder": 0, "deferred": 0, "dropped": 0}
    n = 0
    for line in text.splitlines():
        m = re.match(r"^\s*\|\s*([RAGD]\d+(?:\.\d+)?i?)\s*\|(.+)", line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split("|")]
        if len(cells) < 2:
            continue
        n += 1
        st = cells[1].lower()
        if st in count:
            count[st] += 1
    if not n:
        return None
    return {"total": n, "done": count["done"], "inTicket": count["in-ticket"],
            "inSpec": count["in-spec"], "placeholder": count["placeholder"],
            "deferred": count["deferred"], "dropped": count["dropped"]}


def audit(state):
    """Silent while the state agrees with itself. Does not fix: names.

    Catches one class of error — a transition recorded halfway. A stage
    left active while the run moved on; a task launched without startedAt;
    closed without finishedAt. Each lives until a person sees it: on
    2026-08-19 spec stood active for two and a half hours beside a finished
    plan and a running build, and it was the user who noticed, not the run.
    """
    out = []
    stages = state.get("stages") or []
    rank = {v: i for i, v in enumerate(ORDER)}
    live = [s["id"] for s in stages if s.get("status") == "active" and s.get("id") in rank]
    # A stage the run walked past but never marked passed or skipped:
    # close_passed does not touch it — "skipped" needs a reason and only the
    # agent knows it. On screen it otherwise reads as "the build is stuck".
    if live:
        edge = max(rank[i] for i in live)
        for s in stages:
            if s.get("status") == "pending" and rank.get(s.get("id"), 99) < edge:
                out.append("stage %s stayed pending while the run moved on — close it done or skipped with a reason" % s.get("id"))
    for s in stages:
        if s.get("status") == "active" and not s.get("startedAt"):
            out.append("stage %s active without startedAt — its clock runs off the neighbour" % s.get("id"))
        if s.get("status") == "done" and not s.get("finishedAt"):
            out.append("stage %s closed without finishedAt" % s.get("id"))
        # skipped is a deliberate "produced nothing", and the reason is part
        # of the status: without a note the screen shows a bare "skipped".
        if s.get("status") == "skipped" and not s.get("note"):
            out.append("stage %s skipped without a reason — note is required" % s.get("id"))
    for t in state.get("tickets") or []:
        if t.get("status") in ("in-progress", "review", "repair") and not t.get("startedAt"):
            out.append("task %s in work without startedAt" % t.get("id"))
        if t.get("status") in ("done", "failed") and not t.get("finishedAt"):
            out.append("task %s closed without finishedAt" % t.get("id"))
        # The rule ceiling is two: beyond that, failed or a re-cut of the
        # ticket. A counter above the ceiling means the rule was broken or
        # the status was never recorded.
        for k in ("repairs", "retries", "handoffs"):
            if (t.get(k) or 0) > 2:
                out.append("task %s %s=%s — ceiling is 2, beyond that failed or a re-cut"
                           % (t.get("id"), k, t.get(k)))
        # pending with marks — the task worked and its status was never
        # switched: on the dashboard it is "not started" though its clock
        # already ran.
        if t.get("status") == "pending" and any(
                t.get(k) for k in ("startedAt", "finishedAt", "commit", "tests",
                                   "retries", "repairs", "handoffs",
                                   "repairFindings")):
            out.append("task %s — pending, but its marks say it worked: status never switched" % t.get("id"))
        # The subagent returned, the work landed, and done was never
        # recorded: a commit or an end mark under a live status.
        if t.get("commit") and t.get("status") != "done":
            out.append("task %s committed (%s), but status is %s — done not recorded"
                       % (t.get("id"), t.get("commit"), t.get("status")))
        if t.get("finishedAt") and t.get("status") not in ("done", "failed"):
            out.append("task %s has finishedAt, but status is %s"
                       % (t.get("id"), t.get("status")))
    # The dependent stepped past its blocker — the blocker worked and has no
    # mark: by contract a dependent cannot start before its blocker.
    byid = {}
    dup = set()
    for t in state.get("tickets") or []:
        tid = str(t.get("id"))
        if tid in byid and tid not in dup:
            dup.add(tid)
            out.append("duplicate task id %s — --set by id edits the first match" % tid)
        byid.setdefault(tid, t)
    for t in state.get("tickets") or []:
        tst = t.get("status")
        for b in t.get("blockedBy") or []:
            if str(b) == str(t.get("id")):
                out.append("task %s blocks itself — eternal pending" % t.get("id"))
                continue
            bt = byid.get(str(b))
            if not bt:
                out.append("task %s waits on blocker %s — no such task"
                           % (t.get("id"), b))
                continue
            bst = bt.get("status")
            if bst == "pending" and tst in ("in-progress", "review", "repair",
                                          "done", "failed"):
                out.append("task %s is %s, but its blocker %s is still pending — blocker status not recorded"
                           % (t.get("id"), tst, b))
            elif bst in ("in-progress", "review", "repair") and tst == "done":
                out.append("task %s closed, but its blocker %s is still %s — blocker done not recorded"
                           % (t.get("id"), b, bst))
    # The review side: a task sent to a reviewer while the intake is not set
    # up — the stage is not open or there are no handles; or the stage
    # closed with tasks still under review.
    rev = next((s for s in stages if s.get("id") == "review"), None)
    revs = state.get("reviewers") or {}
    rev_live = any(revs.values())
    for t in state.get("tickets") or []:
        if t.get("status") in ("review", "repair"):
            if not rev or rev.get("status") == "pending":
                out.append("task %s in review, but the review stage is not open — --enter review" % t.get("id"))
            if not rev_live:
                out.append("task %s in review, but reviewer handles are not recorded" % t.get("id"))
        # done = reviewed + green + committed: no commit means the
        # transition is half-recorded and the task has no rollback point.
        if t.get("status") == "done" and not t.get("commit"):
            out.append("task %s done without a commit — rollback point not recorded" % t.get("id"))
    if rev and rev.get("status") in ("done", "skipped"):
        hanging = [t.get("id") for t in state.get("tickets") or []
                   if t.get("status") in ("review", "repair")]
        if hanging:
            out.append("review stage %s, but tasks %s are still under review"
                       % (rev.get("status"), ", ".join(hanging)))
    # A blockedBy cycle is a deadlock in pure form: each waits on another,
    # none can start. The self-block is named above; here only chains of
    # length 2+.
    def _reaches(start):
        stack, seen = [start], set()
        while stack:
            cur = stack.pop()
            for b in cur.get("blockedBy") or []:
                if cur is start and str(b) == str(start.get("id")):
                    continue
                bt = byid.get(str(b))
                if bt is None or id(bt) in seen:
                    continue
                if bt is start:
                    return True
                seen.add(id(bt))
                stack.append(bt)
        return False
    cyc = [str(t.get("id")) for t in state.get("tickets") or [] if _reaches(t)]
    if cyc:
        out.append("blockedBy cycle: %s — eternal pending" % ", ".join(cyc))
    # Marks against the clock: an end before a start — hand-edited, or a
    # startedAt overwritten on re-entry.
    sp = state.get("singlePass") or {}
    pairs = [("run", state.get("startedAt"), state.get("finishedAt")),
             ("singlePass", sp.get("startedAt"), sp.get("finishedAt"))]
    for s in stages:
        pairs.append(("stage %s" % s.get("id"), s.get("startedAt"), s.get("finishedAt")))
    for t in state.get("tickets") or []:
        pairs.append(("task %s" % t.get("id"), t.get("startedAt"), t.get("finishedAt")))
    for name, a, b in pairs:
        da, db = _iso(a), _iso(b)
        if da and db and db < da:
            out.append("%s: finishedAt earlier than startedAt — marks swapped" % name)
    # Edits after landing: any mark later than the run's finishedAt means
    # work continued past the close, or finishedAt was backdated.
    fin = _iso(state.get("finishedAt"))
    if fin is not None:
        for name, a, b in pairs:
            if any(_iso(m) and _iso(m) > fin for m in (a, b)):
                out.append("%s: mark later than the run's finishedAt — work after landing" % name)
    # A stage is closed but its artifact is missing — "passed" without
    # producing anything.
    stmap = {s.get("id"): s for s in stages}
    d = state.get("dir")
    def _miss(name):
        return bool(d) and not os.path.exists(os.path.join(A, d, name))
    if stmap.get("manifest", {}).get("status") == "done":
        if _miss("manifest.md"):
            out.append("manifest stage done, but manifest.md is missing — passed without an artifact")
        bf = state.get("briefFile")
        if not bf:
            out.append("manifest stage done, but briefFile is not recorded — the brief is lost")
        elif _miss(bf):
            out.append("manifest stage done, but the brief file %s is missing" % bf)
    if stmap.get("spec", {}).get("status") == "done":
        if _miss("spec.md"):
            out.append("spec stage done, but spec.md is missing — passed without an artifact")
        if state.get("coverage") is None:
            out.append("spec stage done, but coverage is not recorded — gate G2 skipped")
    if stmap.get("plan", {}).get("status") == "done":
        if _miss("interfaces.md"):
            out.append("plan stage done, but interfaces.md is missing — seeding is required")
        if str(state.get("tier")).upper() != "T0" and not (state.get("tickets") or []):
            out.append("plan stage done at tier %s, but there are no tasks — the breakdown is not recorded"
                       % state.get("tier"))
    bst = stmap.get("build") or {}
    if bst.get("status") in ("done", "skipped"):
        hang = [t.get("id") for t in state.get("tickets") or []
                if t.get("status") != "done" and t.get("status") != "failed"]
        if hang:
            out.append("build stage %s, but tasks %s are not closed"
                       % (bst.get("status"), ", ".join(hang)))
    elif bst.get("status") in (None, "pending"):
        fly = [t.get("id") for t in state.get("tickets") or []
               if t.get("status") in ("in-progress", "review", "repair")]
        if fly:
            out.append("tasks %s in work, but the build stage is not open — --enter build"
                       % ", ".join(fly))
    fst = stmap.get("final") or {}
    if fst.get("status") == "done":
        if not state.get("finishedAt"):
            out.append("final stage done, but the run's finishedAt is not recorded — the clock is ticking")
        bl = state.get("blind")
        if bl is None:
            out.append("final stage done, but the blind acceptance is not recorded")
        elif not isinstance(bl, dict) or not all(
                isinstance(bl.get(k), (int, float)) for k in ("checked", "matched")):
            out.append("blind recorded without the checked/matched counts — the acceptance card is empty")
    # The pulse fell behind: a mark newer than updatedAt means an edit was
    # recorded without moving it.
    upd = _iso(state.get("updatedAt"))
    if upd is not None:
        sp = state.get("singlePass") or {}
        marks = [state.get("finishedAt"), (state.get("blind") or {}).get("ranAt"),
                 sp.get("startedAt"), sp.get("finishedAt")]
        for s in stages:
            marks += [s.get("startedAt"), s.get("finishedAt")]
        for t in state.get("tickets") or []:
            marks += [t.get("startedAt"), t.get("finishedAt")]
        if any(m and m > upd for m in (_iso(x) for x in marks)):
            out.append("a mark is newer than updatedAt — the pulse moves on every state.js edit")
    # A half-written finish: finishedAt is set while a stage or task is
    # still alive.
    if state.get("finishedAt"):
        for s in stages:
            if s.get("status") in ("active", "pending"):
                out.append("the run is closed, but stage %s is still %s — mark it done or skipped" % (s.get("id"), s.get("status")))
        for t in state.get("tickets") or []:
            if t.get("status") in ("in-progress", "review", "repair"):
                out.append("the run is closed, but task %s is still %s" % (t.get("id"), t.get("status")))
    return out


def _iso(v):
    """ISO mark → aware datetime, or None if not a string or not parseable."""
    if not isinstance(v, str):
        return None
    try:
        d = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d.replace(tzinfo=d.tzinfo or timezone.utc)


def main():
    # The Windows console is not UTF-8 by default — output must not depend
    # on the console's codepage.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    if "--kill" in sys.argv:
        # On a landed run the server stops only after the page has fetched
        # the final state.js — otherwise the pane stays on "in progress"
        # forever.
        saw = wait_page_saw() if _landed() else None
        dead = kill_ours()
        wait_down(dead)
        for f in (PIDF, PIDS, LOG, LOG + ".1", FMARK):  # .1 — the serve.log rotation generation
            try:
                os.remove(f)
            except OSError:
                pass
        if not dead:
            print("no servers were running")
        elif saw is False:
            print("server stopped · the page never fetched the final state — the snapshot inside it is truthful")
        else:
            print("server stopped")
        return
    state, before = read_state()
    lines = []
    rq = recount_reqs(state)
    if rq is not None and rq != state.get("requirements"):
        state["requirements"] = rq
        lines.append("requirements ← manifest.md: total %d" % rq["total"])
    enter = "--enter" in sys.argv
    if enter:
        i = sys.argv.index("--enter")
        line = enter_stage(state, sys.argv[i + 1] if i + 1 < len(sys.argv) else "")
        if line:
            lines.append(line)
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        op = args[i]
        if op in ("--set", "--add"):
            if i + 2 >= len(args) or args[i + 2].startswith("--"):
                fail("%s <path> <value>" % op)
            lines.append(apply_edit(state, op[2:], args[i + 1], args[i + 2]))
            i += 3
        elif op == "--inc":
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                fail("--inc <path>")
            lines.append(apply_edit(state, "inc", args[i + 1], None))
            i += 2
        else:
            i += 1
    lines += close_passed(state)
    # Without --enter/--set updatedAt stays — it is the agent's pulse. With
    # them save is mandatory: the edit moves the pulse itself, or the
    # snapshot would show a mark the file does not have.
    if lines or enter:
        state["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    saved = save(state, before) if lines or enter else True
    if not saved:
        state, _ = read_state()                      # the disk has newer truth — continue with it
        lines = []
    snap = write_snapshot(state)
    if state.get("finishedAt"):
        # The mark in the request log: a GET /state.js past it already
        # carried the final state. Without it --kill could not tell "the
        # page already fetched" from "will never ask" — the second is
        # silent either way.
        try:
            size = os.path.getsize(LOG)
        except OSError:
            size = 0
        try:
            with open(FMARK, "w") as f:
                f.write(str(size))
        except OSError:
            pass
    srv = "server not checked" if "--no-serve" in sys.argv else serve(state)
    print("%s · %s · updated %s" % (snap, srv, str(state.get("updatedAt") or "?")[11:19]))
    if saved:
        for line in lines:
            print("  · " + line)
    else:
        print("  ! state.js was rewritten under us — stage auto-close not saved")
    for line in audit(state)[:5]:
        print("  ! " + line)


if __name__ == "__main__":
    main()
