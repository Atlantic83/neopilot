#!/usr/bin/env python3
"""Edge cases of sync.py: transitions, the audit, parity with the dashboard audit.

Sandbox: sync.py is copied into a temp directory — there it IS the run's
".neopilot" (A = dirname of the script). state.js and artifact files are
written beside it; sync is invoked as a subprocess with --no-serve — no
network, no servers.

Run:     python tests/test_sync.py            (from the skill root or anywhere)
         python -m unittest tests.test_sync -v
"""

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC = os.path.join(ROOT, "tools", "sync.py")
TEMPLATE = os.path.join(ROOT, "phases", "dashboard-template.html")

TS = "2026-09-23T10:%02d:00+00:00"                    # fixture marks — a single day
STAGE_IDS = ["preflight", "manifest", "briefing", "spec",
             "plan", "build", "review", "final"]


def stage(i, status="pending", **kw):
    s = {"id": i, "status": status}
    s.update(kw)
    return s


def ticket(i, status="pending", **kw):
    t = {"id": i, "title": "t%s" % i, "status": status, "blockedBy": [],
         "requirements": [], "retries": 0, "repairs": 0, "handoffs": 0}
    t.update(kw)
    return t


def base_state(**kw):
    """A clean state: every mark in place, a fresh updatedAt — the audit must stay silent."""
    st = {
        "slug": "t", "dir": "run", "title": "t", "tier": "T2",
        "briefFile": "2026-09-23-brief.md",
        "startedAt": TS % 0, "updatedAt": "2026-09-23T12:00:00+00:00",
        "finishedAt": None,
        "reviewers": {"manifestSpec": "r1", "craft": "r2"},
        "coverage": {"checkedAt": TS % 4},
        "requirements": {"total": 0},
        "stages": [
            stage("preflight", "done", startedAt=TS % 0, finishedAt=TS % 1),
            stage("manifest", "done", startedAt=TS % 1, finishedAt=TS % 2),
            stage("briefing", "done", startedAt=TS % 2, finishedAt=TS % 3),
            stage("spec", "done", startedAt=TS % 3, finishedAt=TS % 4),
            stage("plan", "done", startedAt=TS % 4, finishedAt=TS % 5),
            stage("build", "active", startedAt=TS % 5),
            stage("review"),
            stage("final"),
        ],
        "tickets": [
            ticket("01", "done", startedAt=TS % 6, finishedAt=TS % 20,
                   commit="abc1234"),
            ticket("02", "in-progress", startedAt=TS % 21, blockedBy=["01"]),
        ],
    }
    st.update(kw)
    return st


class SyncCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="apt-test-")
        self.sync = os.path.join(self.dir, "sync.py")
        shutil.copy(SYNC, self.sync)
        self.rundir = os.path.join(self.dir, "run")
        os.mkdir(self.rundir)
        # artifacts of the "passed" stages — so the clean state is truly clean
        for f in ("manifest.md", "spec.md", "interfaces.md",
                  "2026-09-23-brief.md"):
            with open(os.path.join(self.rundir, f), "w") as fh:
                fh.write("# x\n")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, st):
        with open(os.path.join(self.dir, "state.js"), "w", encoding="utf-8") as f:
            f.write("window.STATE=\n" + json.dumps(st, ensure_ascii=False) + "\n")

    def call(self, *args):
        r = subprocess.run([sys.executable, self.sync, *args, "--no-serve"],
                           capture_output=True, text=True, timeout=30)
        return r.stdout + r.stderr

    def state(self):
        with open(os.path.join(self.dir, "state.js"), encoding="utf-8") as f:
            return json.loads(f.read().split("=", 1)[1])

    def mod(self):
        """The sandbox copy as a module — unit access to save/serve/audit without the CLI."""
        spec = importlib.util.spec_from_file_location("syncmod", self.sync)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def dashboard(self, markers=True):
        """A minimal page with snapshot markers (or without)."""
        body = ("<html><script>/*STATE-BEGIN*/window.STATE=null;/*STATE-END*/"
                "</script></html>" if markers else "<html>no markers</html>")
        with open(os.path.join(self.dir, "dashboard.html"), "w",
                  encoding="utf-8") as f:
            f.write(body)

    def manifest(self, text):
        with open(os.path.join(self.rundir, "manifest.md"), "w",
                  encoding="utf-8") as f:
            f.write(text)

    def flags(self, out):
        return [l.strip() for l in out.splitlines() if l.strip().startswith("!")]

    def flag(self, out, frag):
        """Inline warnings live on ·-lines (· ! text), audit flags on
        !-lines. Look for the fragment in any output."""
        for l in out.splitlines():
            if frag in l:
                return l
        self.fail("flag %r not in output:\n%s" % (frag, out))

    def no_flags(self, out):
        self.assertEqual(self.flags(out), [], "false flags:\n" + out)


# ——— clean states: the guard against false positives ————————————————

class TestClean(SyncCase):
    def test_clean_t2(self):
        self.write(base_state())
        self.no_flags(self.call())

    def test_clean_t0(self):
        st = base_state(tickets=[], tier="T0",
                        singlePass={"startedAt": TS % 6, "finishedAt": TS % 20,
                                    "files": ["a.py"], "commit": "abc",
                                    "tests": {"passed": 3, "failed": 0}})
        self.write(st)
        self.no_flags(self.call())

    def test_clean_finished(self):
        st = base_state(finishedAt=TS % 40,
                        blind={"ranAt": TS % 39, "matched": 2, "checked": 2},
                        tickets=[ticket("01", "done", startedAt=TS % 6,
                                        finishedAt=TS % 20, commit="abc")])
        for s in st["stages"]:
            s["status"] = "done"
            s.setdefault("finishedAt", TS % 30)
        st["stages"][7]["startedAt"] = TS % 29
        self.write(st)
        self.no_flags(self.call())


# ——— --enter: transitions and reminders —————————————————————————————

class TestEnter(SyncCase):
    def test_enter_build_hints_first_pending(self):
        st = base_state()
        st["tickets"][1]["status"] = "pending"
        st["tickets"][1].pop("startedAt")
        self.write(st)
        self.flag(self.call("--enter", "build"),
                  "--set tickets.02.status in-progress")

    def test_enter_build_silent_when_flying(self):
        self.write(base_state())
        out = self.call("--enter", "build")
        self.assertNotIn("not marked", out)

    def test_enter_review_hints_first_unsent(self):
        st = base_state()
        # A done task has already been through review — "nothing sent" is
        # true only when not a single task has ever been to review.
        st["tickets"] = [ticket("01", "in-progress", startedAt=TS % 6),
                         ticket("02", "pending", blockedBy=["01"])]
        self.write(st)
        self.flag(self.call("--enter", "review"),
                  "--set tickets.01.status review")

    def test_enter_review_silent_after_first_send(self):
        st = base_state()
        st["tickets"][0]["status"] = "review"
        self.write(st)
        out = self.call("--enter", "review")
        self.assertNotIn("not sent", out)

    def test_enter_final_warns_open_tickets(self):
        self.write(base_state())
        self.flag(self.call("--enter", "final"), "tasks not closed: 02")

    def test_enter_bad_stage_fails(self):
        self.write(base_state())
        self.assertIn("no stage", self.call("--enter", "nope"))

    def test_enter_after_landing_fails(self):
        st = base_state(finishedAt=TS % 40)
        self.write(st)
        self.assertIn("the run is closed", self.call("--enter", "build"))

    def test_enter_idempotent_keeps_startedAt(self):
        st = base_state()
        self.write(st)
        self.call("--enter", "review")
        first = self.state()
        self.call("--enter", "review")
        second = self.state()
        rev = lambda s: next(x for x in s["stages"] if x["id"] == "review")
        self.assertEqual(rev(first)["startedAt"], rev(second)["startedAt"])

    def test_review_does_not_close_build(self):
        self.write(base_state())
        self.call("--enter", "review")
        st = self.state()
        b = next(s for s in st["stages"] if s["id"] == "build")
        self.assertEqual(b["status"], "active")

    def test_final_closes_build_and_review(self):
        st = base_state()
        st["stages"][6] = stage("review", "active", startedAt=TS % 10)
        self.write(st)
        self.call("--enter", "final")
        st = self.state()
        for i in ("build", "review"):
            s = next(x for x in st["stages"] if x["id"] == i)
            self.assertEqual(s["status"], "done", i)


# ——— --set: transition marks and warnings ———————————————————————————

class TestSet(SyncCase):
    def test_in_progress_stamps_startedAt(self):
        self.write(base_state())
        self.call("--set", "tickets.02.status", "review")
        t = self.state()["tickets"][1]
        self.assertEqual(t["status"], "review")
        self.assertTrue(t.get("startedAt"))

    def test_done_stamps_finishedAt(self):
        self.write(base_state())
        self.call("--set", "tickets.02.status", "done")
        t = self.state()["tickets"][1]
        self.assertTrue(t.get("finishedAt"))

    def test_repair_counts_and_stays_open(self):
        self.write(base_state())
        self.call("--set", "tickets.02.status", "repair")
        t = self.state()["tickets"][1]
        self.assertEqual(t["repairs"], 1)
        self.assertIsNone(t.get("finishedAt"))

    def test_repair_second_time_counts_again(self):
        st = base_state()
        st["tickets"][1]["status"] = "repair"
        st["tickets"][1]["repairs"] = 1
        self.write(st)
        self.call("--set", "tickets.02.status", "repair")
        self.assertEqual(self.state()["tickets"][1]["repairs"], 2)

    def test_startedAt_not_reset_on_second_transition(self):
        st = base_state()
        self.write(st)
        self.call("--set", "tickets.02.status", "review")
        t = self.state()["tickets"][1]
        self.assertEqual(t["startedAt"], TS % 21)   # not overwritten

    def test_in_progress_open_blocker_warns(self):
        st = base_state()
        st["tickets"][0]["status"] = "in-progress"
        st["tickets"][0].pop("commit")
        st["tickets"][0].pop("finishedAt")
        self.write(st)
        self.flag(self.call("--set", "tickets.02.status", "in-progress"),
                  "blockers not closed: 01")

    def test_review_without_stage_warns(self):
        st = base_state()
        st["stages"][6] = stage("review")           # pending
        self.write(st)
        self.flag(self.call("--set", "tickets.02.status", "review"),
                  "review stage not open")

    def test_review_without_reviewers_warns(self):
        st = base_state(reviewers={"manifestSpec": None, "craft": None})
        st["stages"][6] = stage("review", "active", startedAt=TS % 10)
        self.write(st)
        self.flag(self.call("--set", "tickets.02.status", "review"),
                  "reviewers not recorded")

    def test_review_clean_is_silent(self):
        st = base_state()
        st["stages"][6] = stage("review", "active", startedAt=TS % 10)
        self.write(st)
        out = self.call("--set", "tickets.02.status", "review")
        self.assertNotIn("!", out)

    def test_set_unknown_path_fails(self):
        self.write(base_state())
        self.assertIn("no field", self.call("--set", "nope.x", "1"))

    def test_inc_and_add(self):
        self.write(base_state())
        self.call("--inc", "tickets.02.retries",
                 "--add", "tickets.02.repairFindings", "condition")
        t = self.state()["tickets"][1]
        self.assertEqual(t["retries"], 1)
        self.assertEqual(t["repairFindings"], ["condition"])


# ——— the audit: one case per rule ———————————————————————————————————

class TestAudit(SyncCase):
    def audit(self, st):
        self.write(st)
        return self.call()

    def test_pending_stage_behind_edge(self):
        st = base_state()
        st["stages"][2] = stage("briefing")
        self.flag(self.audit(st), "stage briefing stayed pending")

    def test_active_stage_without_startedAt(self):
        st = base_state()
        st["stages"][5].pop("startedAt")
        self.flag(self.audit(st), "stage build active without startedAt")

    def test_done_stage_without_finishedAt(self):
        st = base_state()
        st["stages"][1].pop("finishedAt")
        self.flag(self.audit(st), "stage manifest closed without finishedAt")

    def test_skipped_without_note(self):
        st = base_state()
        st["stages"][2] = stage("briefing", "skipped")
        self.flag(self.audit(st), "stage briefing skipped without a reason")

    def test_skipped_with_note_is_clean(self):
        st = base_state()
        st["stages"][2] = stage("briefing", "skipped",
                                note="no questions were needed")
        self.no_flags(self.audit(st))

    def test_ticket_active_without_startedAt(self):
        st = base_state()
        st["tickets"][1].pop("startedAt")
        self.flag(self.audit(st), "task 02 in work without startedAt")

    def test_ticket_failed_without_finishedAt(self):
        st = base_state()
        st["tickets"][1]["status"] = "failed"
        self.flag(self.audit(st), "task 02 closed without finishedAt")

    def test_repairs_over_ceiling(self):
        st = base_state()
        st["tickets"][1]["repairs"] = 3
        self.flag(self.audit(st), "task 02 repairs=3")

    def test_handoffs_over_ceiling(self):
        st = base_state()
        st["tickets"][1]["handoffs"] = 3
        self.flag(self.audit(st), "task 02 handoffs=3")

    def test_retries_over_ceiling(self):
        st = base_state()
        st["tickets"][1]["retries"] = 3
        self.flag(self.audit(st), "task 02 retries=3")

    def test_pending_with_work_marks(self):
        st = base_state()
        st["tickets"][1]["status"] = "pending"
        st["tickets"][1].pop("blockedBy")
        self.flag(self.audit(st), "task 02 — pending, but its marks say")

    def test_commit_without_done(self):
        st = base_state()
        st["tickets"][1]["commit"] = "beef"
        self.flag(self.audit(st), "task 02 committed (beef), but status is")

    def test_finishedAt_without_terminal(self):
        st = base_state()
        st["tickets"][1]["finishedAt"] = TS % 30
        self.flag(self.audit(st), "task 02 has finishedAt, but status")

    def test_done_without_commit(self):
        st = base_state()
        st["tickets"][0].pop("commit")
        self.flag(self.audit(st), "task 01 done without a commit")

    def test_duplicate_ticket_ids(self):
        st = base_state()
        st["tickets"].append(ticket("01", "pending"))
        self.flag(self.audit(st), "duplicate task id 01")

    def test_blockedBy_missing_ticket(self):
        st = base_state()
        st["tickets"][1]["blockedBy"] = ["99"]
        self.flag(self.audit(st), "task 02 waits on blocker 99 — no such task")

    def test_blockedBy_self(self):
        st = base_state()
        st["tickets"][1]["blockedBy"] = ["02"]
        self.flag(self.audit(st), "task 02 blocks itself")

    def test_blockedBy_cycle_two(self):
        st = base_state()
        st["tickets"] = [ticket("01", "pending", blockedBy=["02"]),
                         ticket("02", "pending", blockedBy=["01"])]
        self.flag(self.audit(st), "blockedBy cycle: 01, 02")

    def test_blockedBy_cycle_three(self):
        st = base_state()
        st["tickets"] = [ticket("01", "pending", blockedBy=["03"]),
                         ticket("02", "pending", blockedBy=["01"]),
                         ticket("03", "pending", blockedBy=["02"])]
        out = self.audit(st)
        self.flag(out, "blockedBy cycle")
        self.assertIn("01", self.flag(out, "blockedBy cycle"))

    def test_dependent_moved_blocker_pending(self):
        st = base_state()
        st["tickets"][0]["status"] = "pending"
        st["tickets"][0].pop("commit")
        st["tickets"][0].pop("finishedAt")
        st["tickets"][0].pop("startedAt")   # clean pending — the flag names the chain
        self.flag(self.audit(st), "its blocker 01 is still pending")

    def test_done_dependent_blocker_flying(self):
        st = base_state()
        st["tickets"][0]["status"] = "review"
        st["tickets"][0].pop("commit")
        st["tickets"][1]["status"] = "done"
        st["tickets"][1]["finishedAt"] = TS % 30
        st["tickets"][1]["commit"] = "beef"
        self.flag(self.audit(st), "blocker done not recorded")

    def test_review_ticket_stage_pending(self):
        st = base_state()
        st["tickets"][1]["status"] = "review"
        st["stages"][6] = stage("review")
        self.flag(self.audit(st), "task 02 in review, but the review stage is not open")

    def test_review_ticket_no_handles(self):
        st = base_state(reviewers={"manifestSpec": None, "craft": None})
        st["tickets"][1]["status"] = "review"
        st["stages"][6] = stage("review", "active", startedAt=TS % 10)
        self.flag(self.audit(st), "task 02 in review, but reviewer handles")

    def test_review_done_tickets_hanging(self):
        st = base_state()
        st["stages"][6] = stage("review", "done",
                                startedAt=TS % 10, finishedAt=TS % 30)
        st["tickets"][1]["status"] = "repair"
        self.flag(self.audit(st), "review stage done, but tasks 02 are still under review")

    def test_interval_backwards(self):
        st = base_state()
        st["tickets"][1]["finishedAt"] = TS % 10    # earlier than startedAt=21
        self.flag(self.audit(st), "task 02: finishedAt earlier than startedAt")

    def test_mark_after_landing(self):
        st = base_state(finishedAt=TS % 25)
        st["tickets"][0]["finishedAt"] = TS % 40
        self.flag(self.audit(st), "task 01: mark later than the run's finishedAt")

    def test_manifest_done_no_file(self):
        os.remove(os.path.join(self.rundir, "manifest.md"))
        self.flag(self.audit(base_state()), "manifest stage done, but manifest.md is missing")

    def test_manifest_done_no_briefFile_field(self):
        st = base_state()
        st.pop("briefFile")
        self.flag(self.audit(st), "manifest stage done, but briefFile is not recorded")

    def test_manifest_done_brief_file_missing(self):
        os.remove(os.path.join(self.rundir, "2026-09-23-brief.md"))
        self.flag(self.audit(base_state()), "brief file")

    def test_spec_done_no_file(self):
        os.remove(os.path.join(self.rundir, "spec.md"))
        self.flag(self.audit(base_state()), "spec stage done, but spec.md is missing")

    def test_spec_done_coverage_null(self):
        st = base_state(coverage=None)
        self.flag(self.audit(st), "gate G2 skipped")

    def test_plan_done_no_interfaces(self):
        os.remove(os.path.join(self.rundir, "interfaces.md"))
        self.flag(self.audit(base_state()), "interfaces.md is missing")

    def test_plan_done_no_tickets_non_t0(self):
        st = base_state(tickets=[])
        self.flag(self.audit(st), "no tasks — the breakdown is not recorded")

    def test_plan_done_no_tickets_t0_is_clean(self):
        st = base_state(tickets=[], tier="T0",
                        singlePass={"startedAt": TS % 6})
        self.no_flags(self.audit(st))

    def test_build_done_tickets_open(self):
        st = base_state()
        st["stages"][5] = stage("build", "done",
                                startedAt=TS % 5, finishedAt=TS % 30)
        self.flag(self.audit(st), "build stage done, but tasks 02 are not closed")

    def test_tickets_flying_build_pending(self):
        st = base_state()
        st["stages"][5] = stage("build")
        self.flag(self.audit(st), "tasks 02 in work, but the build stage is not open")

    def test_final_done_no_finishedAt(self):
        st = base_state()
        st["stages"][7] = stage("final", "done",
                                startedAt=TS % 29, finishedAt=TS % 30)
        st["blind"] = {"ranAt": TS % 29}
        self.flag(self.audit(st), "final stage done, but the run's finishedAt is not recorded")

    def test_final_done_no_blind(self):
        st = base_state()
        st["stages"][7] = stage("final", "done",
                                startedAt=TS % 29, finishedAt=TS % 30)
        self.flag(self.audit(st), "blind acceptance is not recorded")

    def test_final_done_blind_no_counts(self):
        st = base_state()
        st["stages"][7] = stage("final", "done",
                                startedAt=TS % 29, finishedAt=TS % 30)
        st["blind"] = {"ranAt": TS % 29}
        self.flag(self.audit(st), "blind recorded without the checked/matched")

    def test_pulse_behind_marks(self):
        st = base_state()
        st["updatedAt"] = "2026-09-23T09:00:00+00:00"   # every mark is newer
        self.flag(self.audit(st), "newer than updatedAt")

    def test_landed_run_live_stage(self):
        st = base_state(finishedAt=TS % 40)
        st["stages"][7] = stage("final", "done",
                                startedAt=TS % 38, finishedAt=TS % 39)
        st["blind"] = {"ranAt": TS % 38}
        st["tickets"][1]["status"] = "done"
        st["tickets"][1]["finishedAt"] = TS % 30
        st["tickets"][1]["commit"] = "beef"
        self.flag(self.audit(st), "the run is closed, but stage build is still active")

    def test_landed_run_live_ticket(self):
        st = base_state(finishedAt=TS % 40)
        st["blind"] = {"ranAt": TS % 38}
        self.flag(self.audit(st), "the run is closed, but task 02 is still in-progress")


# ——— parity: the dashboard audit must see what the console audit does ————

class TestJsParity(SyncCase):
    """auditState() from the template vs audit() from sync.py on one state.

    Skipped without node. The console's file-related strings (artifacts on
    disk) cannot exist in the JS version — they are cut from the comparison.
    """

    FILE_FLAGS = ("passed without an artifact", "brief file",
                  "interfaces.md is missing")

    def js_audit(self, st):
        with open(TEMPLATE, encoding="utf-8") as fh:
            html = fh.read()
        js = max(re.findall(r"<script>(.*?)</script>", html, re.S), key=len)
        body = js[js.index("function auditState"):js.index("function render")]
        script = ("const S = %s;\n%s\nconsole.log(JSON.stringify(auditState(S)));"
                  % (json.dumps(st, ensure_ascii=False), body))
        f = os.path.join(self.dir, "parity.js")
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(script)
        r = subprocess.run(["node", f], capture_output=True, text=True,
                           timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        return set(json.loads(r.stdout))

    def py_audit(self, st):
        # The console prints audit()[:5] — the full list is unreachable via
        # the CLI. Import the sandbox copy as a module and call audit()
        # directly.
        spec = importlib.util.spec_from_file_location("syncmod", self.sync)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return {l for l in mod.audit(st)
                if not any(f in l for f in self.FILE_FLAGS)}

    def parity(self, st):
        if shutil.which("node") is None:
            self.skipTest("node not found")
        py = self.py_audit(st)
        js = self.js_audit(st)
        self.assertEqual(py, js,
                         "differ:\npy only: %s\njs only: %s"
                         % (sorted(py - js), sorted(js - py)))

    def test_parity_dirty(self):
        st = base_state()
        st["stages"][2] = stage("briefing", "skipped")
        st["stages"][6] = stage("review")
        st["tickets"] = [
            ticket("01", "in-progress", commit="abc", repairs=3,
                   blockedBy=["99"]),
            ticket("02", "review", blockedBy=["03"]),
            ticket("03", "pending", blockedBy=["02"]),
        ]
        self.parity(st)

    def test_parity_clean(self):
        self.parity(base_state())

    def test_parity_landed(self):
        st = base_state(finishedAt=TS % 40, blind={"ranAt": TS % 39})
        st["tickets"][0]["finishedAt"] = TS % 45      # a mark after landing
        self.parity(st)


# ——— state.js parsing ———————————————————————————————————————————————

class TestParse(SyncCase):
    def test_missing_state(self):
        self.assertIn("no state.js yet", self.call())

    def test_corrupt_state(self):
        with open(os.path.join(self.dir, "state.js"), "w",
                  encoding="utf-8") as f:
            f.write("window.STATE=\n{bad json\n")
        self.assertIn("does not parse", self.call())

    def test_raw_json_parses_and_normalizes(self):
        with open(os.path.join(self.dir, "state.js"), "w",
                  encoding="utf-8") as f:
            f.write(json.dumps(base_state()))
        out = self.call("--set", "tickets.02.status", "review")
        self.assertIn("tickets.02.status = review", out)
        with open(os.path.join(self.dir, "state.js"), encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("window.STATE"))

    def test_head_preserved_on_save(self):
        self.write(base_state())
        self.call("--set", "tickets.02.status", "review")
        with open(os.path.join(self.dir, "state.js"), encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("window.STATE="))


# ——— the snapshot and index.html ————————————————————————————————————

class TestSnapshot(SyncCase):
    def test_no_page(self):
        self.write(base_state())
        self.assertIn("no dashboard.html", self.call())

    def test_page_without_markers(self):
        self.dashboard(markers=False)
        self.write(base_state())
        self.assertIn("no snapshot markers", self.call())

    def test_snapshot_written(self):
        self.dashboard()
        self.write(base_state())
        self.assertIn("snapshot written", self.call())
        with open(os.path.join(self.dir, "dashboard.html"),
                  encoding="utf-8") as f:
            page = f.read()
        self.assertIn('"id": "01"', page)

    def test_snapshot_escapes_close_script(self):
        st = base_state()
        st["tickets"][0]["title"] = "x</script><b>y"
        self.dashboard()
        self.write(st)
        self.call()
        with open(os.path.join(self.dir, "dashboard.html"),
                  encoding="utf-8") as f:
            page = f.read()
        self.assertNotIn("</script><b>", page)
        self.assertIn("<\\/script>", page)

    def test_stale_index_replaced_with_shim(self):
        self.dashboard()
        self.write(base_state())
        idx = os.path.join(self.dir, "index.html")
        with open(idx, "w", encoding="utf-8") as f:
            f.write("<html>/*STATE-BEGIN*/stale snapshot/*STATE-END*/</html>")
        self.call()
        with open(idx, encoding="utf-8") as f:
            self.assertIn("dashboard.html", f.read())

    def test_shim_is_idempotent(self):
        self.dashboard()
        self.write(base_state())
        self.call()
        idx = os.path.join(self.dir, "index.html")
        with open(idx, encoding="utf-8") as f:
            first = f.read()
        self.call()
        with open(idx, encoding="utf-8") as f:
            self.assertEqual(first, f.read())

    def test_symlink_index_untouched(self):
        self.dashboard()
        self.write(base_state())
        idx = os.path.join(self.dir, "index.html")
        try:
            os.symlink(os.path.join(self.dir, "dashboard.html"), idx)
        except OSError:
            self.skipTest("symlink unavailable")
        self.call()
        self.assertTrue(os.path.islink(idx))


# ——— recount_reqs: counters from manifest.md ————————————————————————

class TestRecount(SyncCase):
    TABLE = """| ID | Requirement | Status |
|---|---|---|
| R01 | one | done |
| R02 | two | in-ticket |
| R03i | three | in-spec |
| A01 | four | placeholder |
| G02 | five | deferred |
| D04 | six | dropped |
| R01.1 | seven | done |
"""

    def test_counts_and_line(self):
        self.manifest(self.TABLE)
        st = base_state()
        self.write(st)
        out = self.call()
        self.assertIn("requirements ← manifest.md: total 7", out)
        rq = self.state()["requirements"]
        self.assertEqual(
            (rq["done"], rq["inTicket"], rq["inSpec"], rq["placeholder"],
             rq["deferred"], rq["dropped"]), (2, 1, 1, 1, 1, 1))

    def test_no_manifest_no_recount(self):
        os.remove(os.path.join(self.rundir, "manifest.md"))
        st = base_state()
        st["requirements"] = {"total": 42}
        self.write(st)
        out = self.call()
        self.assertNotIn("requirements ←", out)
        self.assertEqual(self.state()["requirements"]["total"], 42)

    def test_manifest_without_rows_untouched(self):
        self.manifest("# manifest without a table\n")
        st = base_state()
        st["requirements"] = {"total": 42}
        self.write(st)
        out = self.call()
        self.assertNotIn("requirements ←", out)
        self.assertEqual(self.state()["requirements"]["total"], 42)

    def test_junk_rows_ignored(self):
        self.manifest("| R01 | x | done |\n| not a requirement |\n| R | y | done |\n")
        st = base_state()
        self.write(st)
        self.call()
        self.assertEqual(self.state()["requirements"]["total"], 1)


# ——— apply_edit in depth ————————————————————————————————————————————

class TestSetDeep(SyncCase):
    def test_now_stamps_iso(self):
        st = base_state()
        st["blind"] = None
        self.write(st)
        self.call("--set", "blind.ranAt", "now")
        v = self.state()["blind"]["ranAt"]
        self.assertRegex(v, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+")

    def test_json_values(self):
        self.write(base_state())
        self.call("--set", "tickets.02.tests", '{"passed":3,"failed":0}',
                  "--set", "tickets.02.retries", "2",
                  "--set", "tickets.02.fast", "true")
        t = self.state()["tickets"][1]
        self.assertEqual(t["tests"], {"passed": 3, "failed": 0})
        self.assertEqual(t["retries"], 2)
        self.assertIs(t["fast"], True)

    def test_set_whole_list_element(self):
        self.write(base_state())
        self.call("--set", "tickets.02",
                  '{"id":"02","status":"done","commit":"abc"}')
        t = self.state()["tickets"][1]
        self.assertEqual(t["status"], "done")

    def test_null_field_becomes_dict(self):
        st = base_state()
        st["blind"] = None
        self.write(st)
        self.call("--set", "blind.matched", "4")
        self.assertEqual(self.state()["blind"]["matched"], 4)

    def test_path_into_scalar_fails(self):
        self.write(base_state())
        self.assertIn("runs into a value", self.call("--set", "title.x", "1"))

    def test_add_on_non_list_fails(self):
        self.write(base_state())
        self.assertIn("not a list", self.call("--add", "tier", "x"))

    def test_inc_on_list_fails(self):
        self.write(base_state())
        self.assertIn("--inc works on numbers", self.call("--inc", "tickets"))

    def test_set_missing_value_fails(self):
        self.write(base_state())
        self.assertIn("<path> <value>", self.call("--set", "tickets.02.status"))

    def test_stage_status_via_set_stamps_finishedAt(self):
        st = base_state()
        st["stages"][6] = stage("review", "active", startedAt=TS % 10)
        self.write(st)
        self.call("--set", "stages.review.status", "done")
        s = next(x for x in self.state()["stages"] if x["id"] == "review")
        self.assertTrue(s.get("finishedAt"))


# ——— --enter in depth ———————————————————————————————————————————————

class TestEnterDeep(SyncCase):
    def test_enter_no_arg_fails(self):
        self.write(base_state())
        self.assertIn("--enter <stage id>", self.call("--enter"))

    def test_reenter_done_pops_finishedAt(self):
        st = base_state()
        st["stages"][6] = stage("review", "done",
                                startedAt=TS % 10, finishedAt=TS % 20)
        self.write(st)
        self.call("--enter", "review")
        s = next(x for x in self.state()["stages"] if x["id"] == "review")
        self.assertEqual(s["status"], "active")
        self.assertIsNone(s.get("finishedAt"))

    def test_out_of_order_enter_leaves_pending_flagged(self):
        st = base_state()
        st["stages"] = [stage("preflight", "active", startedAt=TS % 0)] + \
            [stage(i) for i in STAGE_IDS[1:]]
        self.write(st)
        out = self.call("--enter", "spec")
        # manifest and briefing stayed pending behind a live spec — the audit calls
        self.flag(out, "stage manifest stayed pending")
        self.flag(out, "stage briefing stayed pending")

    def test_zero_duration_flagged(self):
        # Deterministic: the clock is stubbed — three enters share one mark;
        # build is closed only by final (review is nested in it by contract).
        mod = self.mod()
        from datetime import datetime as _dt, timezone as _tz
        class Fixed:
            @staticmethod
            def now(tz=None):
                return _dt(2026, 9, 23, 10, 0, 0, tzinfo=_tz.utc)
        mod.datetime = Fixed
        st = base_state()
        st["stages"][5] = stage("build")
        st["stages"][6] = stage("review")
        for s in ("build", "review", "final"):
            mod.enter_stage(st, s)
        notes = mod.close_passed(st)
        self.assertTrue(any("zero duration" in n for n in notes),
                        str(notes))


# ——— write-race protection ———————————————————————————————————————————

class TestSaveGuard(SyncCase):
    def test_foreign_write_wins(self):
        st = base_state()
        self.write(st)
        mod = self.mod()
        loaded, before = mod.read_state()
        # a foreign edit between the read and the write — save must yield
        foreign = base_state(title="foreign edit")
        self.write(foreign)
        self.assertFalse(mod.save(loaded, before))
        self.assertEqual(self.state()["title"], "foreign edit")

    def test_clean_save_succeeds(self):
        st = base_state()
        self.write(st)
        mod = self.mod()
        loaded, before = mod.read_state()
        loaded["title"] = "ours"
        self.assertTrue(mod.save(loaded, before))
        self.assertEqual(self.state()["title"], "ours")


# ——— the server lifecycle ———————————————————————————————————————————

class TestServe(SyncCase):
    def clean_env(self):
        return {k: v for k, v in os.environ.items()
                if k not in ("SSH_CONNECTION", "CI")}

    def tearDown(self):
        # Orphan insurance: finish off whatever landed in serve.pids.
        try:
            mod = self.mod()
            for _, pid in mod.known():
                if mod.pid_alive(pid):
                    try:
                        os.kill(pid, 15)
                    except OSError:
                        pass
        except Exception:
            pass
        super().tearDown()

    def test_finished_run_no_server(self):
        st = base_state(finishedAt=TS % 40)
        self.write(st)
        r = subprocess.run([sys.executable, self.sync],
                           capture_output=True, text=True, timeout=30,
                           env=self.clean_env())
        self.assertIn("run landed — the server waits for the final fetch",
                      r.stdout + r.stderr)

    def test_landed_sync_writes_final_mark(self):
        # The final sync leaves the serve.final mark — by it --kill tells
        # "the page already fetched the final" from "will never ask".
        self.write(base_state(finishedAt=TS % 40))
        self.call()
        self.assertTrue(os.path.exists(os.path.join(self.dir, "serve.final")))

    def test_ci_env_no_server(self):
        st = base_state()
        self.write(st)
        r = subprocess.run([sys.executable, self.sync],
                           capture_output=True, text=True, timeout=30,
                           env={**self.clean_env(), "CI": "1"})
        self.assertIn("remote session", r.stdout + r.stderr)

    def test_kill_without_servers(self):
        self.write(base_state())
        out = self.call("--kill")
        self.assertIn("no servers were running", out)

    def test_kill_landed_no_servers(self):
        self.write(base_state(finishedAt=TS % 40))
        out = self.call("--kill")
        self.assertIn("no servers were running", out)

    def test_kill_landed_after_page_fetch(self):
        # The final fetch past the mark is already in the log — nothing to
        # wait for, it stops at once.
        self.dashboard()
        self.write(base_state())
        out = subprocess.run([sys.executable, self.sync],
                             capture_output=True, text=True, timeout=30,
                             env=self.clean_env()).stdout
        if "server up" not in out:
            self.skipTest("server did not come up: " + out.strip())
        port = int(out.split("localhost:", 1)[1].split("/")[0])
        mod = self.mod()
        mod.fetch(port, "/state.js")                    # the page poll — for the final state
        self.write(base_state(finishedAt=TS % 40))
        with open(mod.FMARK, "w") as f:
            f.write("0")
        t0 = time.time()
        out = self.call("--kill")
        self.assertLess(time.time() - t0, 20)
        self.assertIn("server stopped", out)
        self.assertNotIn("never fetched", out)

    def test_kill_landed_waits_for_fetch(self):
        # The finish is recorded, the server is alive, the page has not asked
        # yet — --kill waits for its GET in the log and stops right after,
        # not on a timer.
        mod = self.mod()
        port, srv = self.spawn_stray(mod)
        try:
            with open(mod.PIDS, "w") as f:
                f.write("%d %d\n" % (port, srv.pid))
            open(mod.LOG, "w").close()
            with open(mod.FMARK, "w") as f:
                f.write("0")
            self.write(base_state(finishedAt=TS % 40))
            proc = subprocess.Popen([sys.executable, self.sync, "--kill"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            time.sleep(2)                                # the process is up and waiting
            self.assertIsNone(proc.poll())               # waits for the fetch, not exited
            with open(mod.LOG, "a") as f:                # the page fetched the final state
                f.write('127.0.0.1 - - [x] "GET /state.js?t=1 HTTP/1.1" 200 -\n')
            out = proc.communicate(timeout=30)[0]
            self.assertIn("server stopped", out)
            self.assertNotIn("never fetched", out)
            srv.wait(timeout=5)
            self.assertIsNotNone(srv.returncode)
        finally:
            if srv.poll() is None:
                srv.kill()
            srv.wait(timeout=5)

    def test_wait_page_saw_is_bounded(self):
        # The pane that will never ask: a cap, not eternity.
        mod = self.mod()
        port, srv = self.spawn_stray(mod)
        try:
            with open(mod.PIDS, "w") as f:
                f.write("%d %d\n" % (port, srv.pid))
            open(mod.LOG, "w").close()                   # the stray's stderr is devnull — the log is empty
            t0 = time.time()
            self.assertFalse(mod.wait_page_saw(cap=2))
            self.assertLess(time.time() - t0, 15)
        finally:
            if srv.poll() is None:
                srv.kill()
            srv.wait(timeout=5)

    def test_full_cycle_up_fetch_kill(self):
        self.dashboard()
        self.write(base_state())
        out = subprocess.run([sys.executable, self.sync],
                             capture_output=True, text=True, timeout=30,
                             env=self.clean_env()).stdout
        if "server up" not in out:
            self.skipTest("server did not come up: " + out.strip())
        port = int(out.split("localhost:", 1)[1].split("/")[0])
        mod = self.mod()
        body = mod.fetch(port, "/serve.pid")
        self.assertIn(str(port), body or "")
        out = self.call("--kill")
        self.assertIn("server stopped", out)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "serve.pid")))

    def test_stray_server_killed(self):
        # A stray of this run: http.server on the sandbox directory, a
        # "port pid" entry in the journal — serves_us will prove it "ours".
        mod = self.mod()
        port = mod.free_port(None)
        self.assertTrue(port)
        srv = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port),
             "--bind", "127.0.0.1", "--directory", self.dir],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            with open(os.path.join(self.dir, "serve.pids"), "w") as f:
                f.write("%d %d\n" % (port, srv.pid))
            for _ in range(40):                      # give the server time to come up
                if mod.serves_us(port, srv.pid) is True:
                    break
                time.sleep(0.1)
            self.write(base_state())
            out = self.call("--kill")
            self.assertIn("server stopped", out)
            # pid_alive lies while any process handle is alive — Popen._handle
            # closes only on GC. The honest death check is our Popen's
            # returncode plus kill_ours' journal cleanup.
            srv.wait(timeout=5)
            self.assertIsNotNone(srv.returncode)
            self.assertFalse(os.path.exists(mod.PIDS) and open(mod.PIDS).read().strip())
            self.assertFalse(os.path.exists(mod.PIDF))
        finally:
            if srv.poll() is None:
                srv.kill()

    def spawn_stray(self, mod):
        """A live http.server on the sandbox directory, waited to serves_us."""
        port = mod.free_port(None)
        srv = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port),
             "--bind", "127.0.0.1", "--directory", self.dir],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(40):
            if mod.serves_us(port, srv.pid) is True:
                break
            time.sleep(0.1)
        return port, srv

    def serve_line(self):
        self.write(base_state())
        return subprocess.run([sys.executable, self.sync],
                              capture_output=True, text=True, timeout=30,
                              env=self.clean_env()).stdout

    def test_lost_pointer_adopts_live_server(self):
        # serve.pid got erased while the journal's server is alive — the
        # pane may be sitting on it. sync must adopt it as the pointer and
        # report the same address, not kill the server and move to a random
        # port.
        mod = self.mod()
        port, srv = self.spawn_stray(mod)
        try:
            with open(mod.PIDS, "w") as f:
                f.write("%d %d\n" % (port, srv.pid))
            out = self.serve_line()
            self.assertIn("server alive: http://localhost:%d/dashboard.html"
                          % port, out)
            self.assertIsNone(srv.poll())                    # not killed
            self.assertEqual(mod.recorded(), (port, srv.pid))
        finally:
            if srv.poll() is None:
                srv.kill()
            srv.wait(timeout=5)

    def test_dead_pointer_adopts_journal_server(self):
        # The pointer stares at a dead pair while the journal has a live
        # server — adopt it, do not spawn a new port.
        mod = self.mod()
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        port, srv = self.spawn_stray(mod)
        try:
            with open(mod.PIDS, "w") as f:
                f.write("%d %d\n" % (port, srv.pid))
            with open(mod.PIDF, "w") as f:
                f.write("1 %d\n" % dead.pid)      # port 1 dead, pid dead
            out = self.serve_line()
            self.assertIn("server alive: http://localhost:%d/dashboard.html"
                          % port, out)
            self.assertEqual(mod.recorded(), (port, srv.pid))
        finally:
            if srv.poll() is None:
                srv.kill()
            srv.wait(timeout=5)

    def test_spawn_prefers_journal_port(self):
        # Neither pointer nor live server — only a dead journal entry.
        # Its port is the last announced: if free, it is the one.
        mod = self.mod()
        dead = subprocess.Popen([sys.executable, "-c", "pass"])
        dead.wait()
        port = mod.free_port(None)
        with open(mod.PIDS, "w") as f:
            f.write("%d %d\n" % (port, dead.pid))
        out = self.serve_line()
        if "server up" not in out:
            self.skipTest("server did not come up: " + out.strip())
        self.assertIn("localhost:%d/dashboard.html" % port, out)
        self.assertNotIn("link moved", out)                  # the port stayed
        self.assertFalse(os.path.exists(mod.PIDF + ".tmp"))


# ——— remaining output invariants ————————————————————————————————————

class TestOutput(SyncCase):
    def test_audit_capped_at_five(self):
        st = base_state()
        st["stages"][2] = stage("briefing", "skipped")
        st["tickets"] = [
            ticket("01", "in-progress", commit="abc", repairs=3,
                   blockedBy=["99"]),
            ticket("02", "review", blockedBy=["03"]),
            ticket("03", "pending", blockedBy=["02"]),
            ticket("04", "pending", blockedBy=["04"]),
        ]
        self.write(st)
        self.assertLessEqual(len(self.flags(self.call())), 5)

    def test_idle_call_keeps_updatedAt(self):
        st = base_state()
        self.write(st)
        self.call()
        self.assertEqual(self.state()["updatedAt"], st["updatedAt"])

    def test_set_moves_updatedAt(self):
        st = base_state()
        self.write(st)
        self.call("--set", "tickets.02.status", "review")
        self.assertNotEqual(self.state()["updatedAt"], st["updatedAt"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
