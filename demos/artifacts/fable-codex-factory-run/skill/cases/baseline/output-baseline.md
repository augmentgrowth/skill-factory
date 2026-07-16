# Baseline output — Fable-only, no skill, no codex

Captured 2026-07-15. Run per `input.md`: disposable worktree at frozen commit `6eec1b8`, single Claude Fable general-purpose agent, no fable-codex skill, no codex CLI. Worktree discarded after capture.

## Agent summary (verbatim)

The baseline agent reported:

- `pm_agent/proposals.py` (~L43–82, L155–161): added the registry — `TRIAGE_PROPOSAL_KINDS` (derived from the five triage decisions that can become proposals: `triage_close/propose/decay_archive/recategorize/file_label`, matching triage.py's dynamic `f"triage_{decision}"`), named constants `KIND_TIER_GRADUATION`, `KIND_CAPTURE_WHICH_TEAM`, `KIND_CAPTURE_FILE`, `KIND_CAPTURE_MAYBE`, `KIND_FREEFORM_REQUEST`, and `VALID_PROPOSAL_KINDS` as their union. `ProposalStore.create()` now raises `ProposalError` on unknown kinds (message names the bad kind, where to register it, and the valid set) — checked before the lock, before any write.
- Call sites now use registry constants: `capture.py` (3 create sites), `anneal.py`, `replies.py` (incl. `CAPTURE_FILE_KIND` re-pointed), `standup.py` (duplicate constants replaced with imports). `triage.py` kept its literals/f-string — validated at create; the f-string is the documented creation pattern.
- Tests: new `test_create_rejects_unknown_kind` and `test_create_accepts_every_registered_kind`; test-only placeholder kinds (`relabel`, `recategorize`, `reprioritize`, `stale_check` — actually ledger action types) swapped to registered kinds across 6 test files.
- Key decision: registry lists only kinds production code creates; test-only placeholders updated rather than registered.
- Test run: `python3 -m pytest tests/ -q` from `pm-agent/` — **545 passed, 59 subtests passed, 0 failed**.

Tokens spent (baseline pass): ~117k subagent tokens, 30 tool uses, ~7.4 min.

## Captured diff

```diff
diff --git a/pm-agent/pm_agent/anneal.py b/pm-agent/pm_agent/anneal.py
index face969..39f7764 100644
--- a/pm-agent/pm_agent/anneal.py
+++ b/pm-agent/pm_agent/anneal.py
@@ -35,7 +35,7 @@ run(ctx, now, dry_run) steps:
      from state/standup_state.json into the tier table; attempt
      graduations (engagement-gated by tiers.graduate). Tier changes are
      act-then-report: applied immediately, then ledgered, noticed, and a
-     kind="tier_graduation" proposal is created for visibility.
+     kind=KIND_TIER_GRADUATION proposal is created for visibility.
   c. Self-review: ask-rate, per-category override rate, ignored-push /
      skipped-standup counts, felt-cost counters vs baseline -> written to
      state/self_review.json for the next daily push to include.
@@ -75,7 +75,7 @@ from . import telegram_out
 from .config import KILL_SWITCH_ENV, PmAgentConfig, load_config, refusal_for
 from .ledger import Ledger
 from .overrides import OverrideLog
-from .proposals import ProposalStore
+from .proposals import KIND_TIER_GRADUATION, ProposalStore
 from .self_mod import SelfModContext
 from .tiers import CONSEQUENTIAL_OVERRIDE_KINDS, GraduationBlocked, TierStore
 
diff --git a/pm-agent/pm_agent/capture.py b/pm-agent/pm_agent/capture.py
index de731f3..d71adec 100644
--- a/pm-agent/pm_agent/capture.py
+++ b/pm-agent/pm_agent/capture.py
@@ -39,7 +39,12 @@ from typing import TYPE_CHECKING, Any, Callable, Iterator
 
 from .actions import ActionContext, ActionError, file_issue
 from .ledger import Ledger
-from .proposals import ProposalStore
+from .proposals import (
+    KIND_CAPTURE_FILE,
+    KIND_CAPTURE_MAYBE,
+    KIND_CAPTURE_WHICH_TEAM,
+    ProposalStore,
+)
 from .telegram_out import ConfigError as TelegramConfigError
 from .telegram_out import TelegramSendError
 from .telegram_out import send as telegram_send
@@ -376,7 +381,7 @@ def _process_item(
             if not dry_run:
                 proposal = ctx.proposals.create(
                     item_ref=file_ref,
-                    kind="capture_which_team",
+                    kind=KIND_CAPTURE_WHICH_TEAM,
                     recommendation=(
                         f"Unknown/unvalidated Linear team {raw_team!r} for action item from "
                         f"{file_ref}. Which team should this file under?\n\n{_quote_note(item.get('raw', ''))}"
@@ -437,7 +442,7 @@ def _process_item(
             if not dry_run:
                 proposal = ctx.proposals.create(
                     item_ref=file_ref or "unfiled",
-                    kind="capture_file",
+                    kind=KIND_CAPTURE_FILE,
                     recommendation=recommendation,
                     detail={"team_id": resolved_team, "title": title, "description": description},
                 )
@@ -524,7 +529,7 @@ def _process_item(
         if not dry_run:
             proposal = ctx.proposals.create(
                 item_ref=file_ref,
-                kind="capture_maybe",
+                kind=KIND_CAPTURE_MAYBE,
                 recommendation=recommendation,
             )
         ctx.ledger.append(
diff --git a/pm-agent/pm_agent/proposals.py b/pm-agent/pm_agent/proposals.py
index 8bd8051..3b7b4e1 100644
--- a/pm-agent/pm_agent/proposals.py
+++ b/pm-agent/pm_agent/proposals.py
@@ -41,6 +41,46 @@ from .locking import file_lock
 
 STATES = ("open", "executing", "confirmed", "rejected", "expired", "decayed", "failed")
 
+# ---------------------------------------------------------------------------
+# Proposal-kind registry.
+#
+# Every kind a proposal can be created with, in one place. `create()` rejects
+# anything not listed here, so a typo (or a new kind someone forgot to
+# register) fails loudly at the creation boundary instead of flowing silently
+# into the store and confusing downstream consumers (triage, replies, anneal,
+# standup, daily_push) that switch on specific kinds.
+#
+# Adding a new proposal kind == add it here (and, if it needs bespoke
+# handling, teach the relevant consumer about it).
+
+# triage.py creates kind=f"triage_{decision}" for propose_first-tier
+# decisions; the decision vocabulary is fixed in triage.JudgeResult
+# (close | propose | decay_archive | recategorize | file_label —
+# no_action never becomes a proposal).
+TRIAGE_PROPOSAL_KINDS = frozenset(
+    f"triage_{decision}"
+    for decision in ("close", "propose", "decay_archive", "recategorize", "file_label")
+)
+
+# anneal.py — tier-graduation visibility proposal.
+KIND_TIER_GRADUATION = "tier_graduation"
+# capture.py — capture pipeline proposals.
+KIND_CAPTURE_WHICH_TEAM = "capture_which_team"
+KIND_CAPTURE_FILE = "capture_file"
+KIND_CAPTURE_MAYBE = "capture_maybe"
+# replies.py — freeform inbound request parked as a proposal.
+KIND_FREEFORM_REQUEST = "freeform_request"
+
+VALID_PROPOSAL_KINDS = TRIAGE_PROPOSAL_KINDS | frozenset(
+    {
+        KIND_TIER_GRADUATION,
+        KIND_CAPTURE_WHICH_TEAM,
+        KIND_CAPTURE_FILE,
+        KIND_CAPTURE_MAYBE,
+        KIND_FREEFORM_REQUEST,
+    }
+)
+
 # Allowed transitions: from-state -> set of legal to-states, for the
 # general-purpose `transition()` method. `failed -> open` is intentionally
 # EXCLUDED here — it is only reachable via the dedicated `retry()` method,
@@ -147,6 +187,12 @@ class ProposalStore:
         {team_id, title, description} so `go` can file the new issue (U4).
         Kept as a nested dict so adding a proposal kind never widens the core
         columns; existing kinds omit it and are unaffected."""
+        if kind not in VALID_PROPOSAL_KINDS:
+            raise ProposalError(
+                f"unknown proposal kind: {kind!r}; register it in "
+                f"VALID_PROPOSAL_KINDS (pm_agent/proposals.py) before creating "
+                f"proposals with it. Valid kinds: {', '.join(sorted(VALID_PROPOSAL_KINDS))}"
+            )
         with self._locked():
             data = self._load()
             if dedupe_open:
diff --git a/pm-agent/pm_agent/replies.py b/pm-agent/pm_agent/replies.py
index 653ad94..6797bf7 100644
--- a/pm-agent/pm_agent/replies.py
+++ b/pm-agent/pm_agent/replies.py
@@ -38,7 +38,13 @@ from . import actions as actions_mod
 from . import telegram_out
 from .actions import ActionContext, UnknownActionType
 from .ledger import Ledger
-from .proposals import InvalidTransition, NotFound, ProposalStore
+from .proposals import (
+    KIND_CAPTURE_FILE,
+    KIND_FREEFORM_REQUEST,
+    InvalidTransition,
+    NotFound,
+    ProposalStore,
+)
 from .undo import ActionNotFound, DryRunUndoRefused, OutcomeMissingOrFailed, undo as undo_fn
 
 ALLOWED_USER_IDS_ENV = "TELEGRAM_ALLOWED_USERS"
@@ -477,7 +483,8 @@ def _execute_defer(ctx: ReplyContext, proposal: dict[str, Any], rest: str) -> Re
     )
 
 
-CAPTURE_FILE_KIND = "capture_file"
+# Canonical value lives in the proposal-kind registry (pm_agent/proposals.py).
+CAPTURE_FILE_KIND = KIND_CAPTURE_FILE
 
 
 def _execute_file(ctx: ReplyContext, proposal: dict[str, Any]) -> ReplyResult:
@@ -659,7 +666,7 @@ def _handle_status(ctx: ReplyContext) -> ReplyResult:
 def _freeform_result(ctx: ReplyContext, text: str) -> ReplyResult:
     proposal = ctx.proposals.create(
         item_ref="telegram-freeform",
-        kind="freeform_request",
+        kind=KIND_FREEFORM_REQUEST,
         recommendation=text,
     )
     return ReplyResult(
diff --git a/pm-agent/pm_agent/standup.py b/pm-agent/pm_agent/standup.py
index 911725a..6efe86d 100644
--- a/pm-agent/pm_agent/standup.py
+++ b/pm-agent/pm_agent/standup.py
@@ -77,7 +77,7 @@ from . import telegram_out
 from .ledger import Ledger
 from .locking import file_lock
 from .overrides import OverrideLog
-from .proposals import ProposalStore
+from .proposals import KIND_CAPTURE_MAYBE, KIND_TIER_GRADUATION, ProposalStore
 from .tiers import CONSEQUENTIAL_OVERRIDE_KINDS  # noqa: F401 - re-exported for callers' convenience
 
 CATEGORY = "standup"
@@ -86,8 +86,8 @@ QUEUE_CAP_DEFAULT = 10
 SKIP_HOURS_DEFAULT = 48
 DECAY_ADJACENT_STALE_DAYS = 21
 
-KIND_TIER_GRADUATION = "tier_graduation"
-KIND_CAPTURE_MAYBE = "capture_maybe"
+# KIND_TIER_GRADUATION / KIND_CAPTURE_MAYBE come from the proposal-kind
+# registry in pm_agent/proposals.py (imported above).
 _ADMIN_HYGIENE_KINDS = frozenset({"triage_file_label", "capture_maybe", "capture_which_team"})
 _DECAY_ADJACENT_KIND_PREFIXES = ("triage_decay_archive", "triage_close")
 
diff --git a/pm-agent/tests/test_anneal.py b/pm-agent/tests/test_anneal.py
index d162649..c13bddc 100644
--- a/pm-agent/tests/test_anneal.py
+++ b/pm-agent/tests/test_anneal.py
@@ -470,7 +470,7 @@ class TestRefusalsAndReports(AnnealBase):
         # Fake a prior run 7 days ago so the window is real.
         anneal._append_run_report(self.state_dir, {"ts": _iso(NOW - timedelta(days=7)), "status": "ok"})
         self.proposals.create(
-            item_ref="LAB-1", kind="stale_check", recommendation="close?",
+            item_ref="LAB-1", kind="freeform_request", recommendation="close?",
             created_ts=_iso(NOW - timedelta(days=2)),
         )
         self._override("LAB:stale", "ratification", "r1", ts=_iso(NOW - timedelta(days=3)))
diff --git a/pm-agent/tests/test_cli_reply.py b/pm-agent/tests/test_cli_reply.py
index eab37ce..3d71234 100644
--- a/pm-agent/tests/test_cli_reply.py
+++ b/pm-agent/tests/test_cli_reply.py
@@ -44,7 +44,7 @@ class CliReplyTestBase(unittest.TestCase):
         # Seed one open proposal (id "p1") whose `go` executor comments on LAB-1.
         self.proposals = ProposalStore(os.path.join(self.state_dir, "proposals.json"))
         self.proposal = self.proposals.create(
-            item_ref="LAB-1", kind="reprioritize", recommendation="do the thing"
+            item_ref="LAB-1", kind="freeform_request", recommendation="do the thing"
         )
         self.client = FakeLinearClient()
         self.client.seed_issue("LAB-1")
diff --git a/pm-agent/tests/test_injection_suite.py b/pm-agent/tests/test_injection_suite.py
index 340e541..cb634ed 100644
--- a/pm-agent/tests/test_injection_suite.py
+++ b/pm-agent/tests/test_injection_suite.py
@@ -447,7 +447,7 @@ class TestInjectionTelegramForeignIdentity(unittest.TestCase):
     def test_injection_foreign_identity_rejected_before_proposal_read(self):
         self.client.seed_issue("LAB-1")
         proposal = self.proposals.create(
-            item_ref="LAB-1", kind="reprioritize", recommendation="do the thing"
+            item_ref="LAB-1", kind="freeform_request", recommendation="do the thing"
         )
         pid = proposal["proposal_id"]
 
diff --git a/pm-agent/tests/test_proposals.py b/pm-agent/tests/test_proposals.py
index 7dc04e3..b15c933 100644
--- a/pm-agent/tests/test_proposals.py
+++ b/pm-agent/tests/test_proposals.py
@@ -6,7 +6,13 @@ import unittest
 
 sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
 
-from pm_agent.proposals import InvalidTransition, NotFound, ProposalStore
+from pm_agent.proposals import (
+    VALID_PROPOSAL_KINDS,
+    InvalidTransition,
+    NotFound,
+    ProposalError,
+    ProposalStore,
+)
 
 
 class TestProposals(unittest.TestCase):
@@ -18,9 +24,27 @@ class TestProposals(unittest.TestCase):
     def tearDown(self):
         shutil.rmtree(self.tmpdir, ignore_errors=True)
 
+    def test_create_rejects_unknown_kind(self):
+        # A typo'd or unregistered kind must fail loudly at creation time,
+        # never flow silently into the store.
+        with self.assertRaises(ProposalError) as caught:
+            self.store.create(item_ref="ENG-1", kind="triage_recategorise", recommendation="x")
+        message = str(caught.exception)
+        self.assertIn("triage_recategorise", message)
+        self.assertIn("VALID_PROPOSAL_KINDS", message)
+        # Nothing was written.
+        self.assertEqual(self.store.list_all(), [])
+
+    def test_create_accepts_every_registered_kind(self):
+        for kind in sorted(VALID_PROPOSAL_KINDS):
+            proposal = self.store.create(item_ref=f"ENG-{kind}", kind=kind, recommendation="x")
+            self.assertEqual(proposal["kind"], kind)
+            self.assertEqual(proposal["state"], "open")
+        self.assertEqual(len(self.store.list_open()), len(VALID_PROPOSAL_KINDS))
+
     def test_create_and_get(self):
         proposal = self.store.create(
-            item_ref="ENG-1", kind="recategorize", recommendation="move to Bugs"
+            item_ref="ENG-1", kind="triage_recategorize", recommendation="move to Bugs"
         )
         self.assertEqual(proposal["state"], "open")
         fetched = self.store.get(proposal["proposal_id"])
@@ -41,7 +65,7 @@ class TestProposals(unittest.TestCase):
         self.assertEqual(fetched["detail"]["description"], "body")
 
     def test_create_without_detail_omits_the_key(self):
-        proposal = self.store.create(item_ref="ENG-1", kind="recategorize", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-1", kind="triage_recategorize", recommendation="x")
         self.assertNotIn("detail", self.store.get(proposal["proposal_id"]))
 
     def test_create_dedupes_open_item_ref_and_kind(self):
@@ -77,43 +101,43 @@ class TestProposals(unittest.TestCase):
         can never be confirmed while the underlying action might still
         fail, because open->confirmed directly is no longer a legal edge.
         """
-        proposal = self.store.create(item_ref="ENG-2", kind="relabel", recommendation="add label X")
+        proposal = self.store.create(item_ref="ENG-2", kind="triage_file_label", recommendation="add label X")
         executing = self.store.transition(proposal["proposal_id"], "executing")
         self.assertEqual(executing["state"], "executing")
         updated = self.store.transition(proposal["proposal_id"], "confirmed")
         self.assertEqual(updated["state"], "confirmed")
 
     def test_open_to_confirmed_directly_raises(self):
-        proposal = self.store.create(item_ref="ENG-2b", kind="relabel", recommendation="add label X")
+        proposal = self.store.create(item_ref="ENG-2b", kind="triage_file_label", recommendation="add label X")
         with self.assertRaises(InvalidTransition):
             self.store.transition(proposal["proposal_id"], "confirmed")
 
     def test_open_to_rejected(self):
-        proposal = self.store.create(item_ref="ENG-3", kind="relabel", recommendation="add label X")
+        proposal = self.store.create(item_ref="ENG-3", kind="triage_file_label", recommendation="add label X")
         updated = self.store.transition(proposal["proposal_id"], "rejected")
         self.assertEqual(updated["state"], "rejected")
 
     def test_expired_to_confirmed_raises(self):
-        proposal = self.store.create(item_ref="ENG-4", kind="relabel", recommendation="add label X")
+        proposal = self.store.create(item_ref="ENG-4", kind="triage_file_label", recommendation="add label X")
         self.store.transition(proposal["proposal_id"], "expired")
         with self.assertRaises(InvalidTransition):
             self.store.transition(proposal["proposal_id"], "confirmed")
 
     def test_confirmed_to_rejected_raises(self):
-        proposal = self.store.create(item_ref="ENG-5", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-5", kind="triage_file_label", recommendation="x")
         self.store.transition(proposal["proposal_id"], "executing")
         self.store.transition(proposal["proposal_id"], "confirmed")
         with self.assertRaises(InvalidTransition):
             self.store.transition(proposal["proposal_id"], "rejected")
 
     def test_rejected_to_anything_raises(self):
-        proposal = self.store.create(item_ref="ENG-6", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-6", kind="triage_file_label", recommendation="x")
         self.store.transition(proposal["proposal_id"], "rejected")
         with self.assertRaises(InvalidTransition):
             self.store.transition(proposal["proposal_id"], "open")
 
     def test_decayed_is_terminal(self):
-        proposal = self.store.create(item_ref="ENG-7", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-7", kind="triage_file_label", recommendation="x")
         self.store.transition(proposal["proposal_id"], "decayed")
         with self.assertRaises(InvalidTransition):
             self.store.transition(proposal["proposal_id"], "confirmed")
@@ -123,8 +147,8 @@ class TestProposals(unittest.TestCase):
             self.store.get("p999")
 
     def test_list_open(self):
-        p1 = self.store.create(item_ref="ENG-8", kind="relabel", recommendation="x")
-        p2 = self.store.create(item_ref="ENG-9", kind="relabel", recommendation="y")
+        p1 = self.store.create(item_ref="ENG-8", kind="triage_file_label", recommendation="x")
+        p2 = self.store.create(item_ref="ENG-9", kind="triage_file_label", recommendation="y")
         self.store.transition(p2["proposal_id"], "rejected")
         open_list = self.store.list_open()
         self.assertEqual(len(open_list), 1)
@@ -133,7 +157,7 @@ class TestProposals(unittest.TestCase):
     def test_default_expiry_is_seven_days(self):
         from datetime import datetime
 
-        proposal = self.store.create(item_ref="ENG-10", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-10", kind="triage_file_label", recommendation="x")
         created = datetime.fromisoformat(proposal["created_ts"])
         expiry = datetime.fromisoformat(proposal["expiry_ts"])
         delta_days = (expiry - created).total_seconds() / 86400.0
@@ -144,7 +168,7 @@ class TestProposals(unittest.TestCase):
 
         past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
         proposal = self.store.create(
-            item_ref="ENG-11", kind="relabel", recommendation="x", expiry_ts=past
+            item_ref="ENG-11", kind="triage_file_label", recommendation="x", expiry_ts=past
         )
         expired = self.store.expire_due()
         self.assertEqual(len(expired), 1)
@@ -156,7 +180,7 @@ class TestProposals(unittest.TestCase):
 
         future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
         proposal = self.store.create(
-            item_ref="ENG-12", kind="relabel", recommendation="x", expiry_ts=future
+            item_ref="ENG-12", kind="triage_file_label", recommendation="x", expiry_ts=future
         )
         expired = self.store.expire_due()
         self.assertEqual(len(expired), 0)
@@ -164,7 +188,7 @@ class TestProposals(unittest.TestCase):
         self.assertEqual(fetched["state"], "open")
 
     def test_persists_across_store_instances(self):
-        proposal = self.store.create(item_ref="ENG-13", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-13", kind="triage_file_label", recommendation="x")
         reopened = ProposalStore(self.path)
         fetched = reopened.get(proposal["proposal_id"])
         self.assertEqual(fetched["item_ref"], "ENG-13")
@@ -185,7 +209,7 @@ class TestF3ExecutingStateMachine(unittest.TestCase):
         shutil.rmtree(self.tmpdir, ignore_errors=True)
 
     def test_executing_to_failed(self):
-        proposal = self.store.create(item_ref="ENG-20", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-20", kind="triage_file_label", recommendation="x")
         self.store.transition(proposal["proposal_id"], "executing")
         updated = self.store.transition(proposal["proposal_id"], "failed")
         self.assertEqual(updated["state"], "failed")
@@ -193,20 +217,20 @@ class TestF3ExecutingStateMachine(unittest.TestCase):
     def test_executing_to_rejected_raises(self):
         """executing only resolves to confirmed or failed -- not rejected,
         expired, or decayed (those are open-only terminal-ish edges)."""
-        proposal = self.store.create(item_ref="ENG-21", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-21", kind="triage_file_label", recommendation="x")
         self.store.transition(proposal["proposal_id"], "executing")
         with self.assertRaises(InvalidTransition):
             self.store.transition(proposal["proposal_id"], "rejected")
 
     def test_failed_to_open_via_bare_transition_raises(self):
-        proposal = self.store.create(item_ref="ENG-22", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-22", kind="triage_file_label", recommendation="x")
         self.store.transition(proposal["proposal_id"], "executing")
         self.store.transition(proposal["proposal_id"], "failed")
         with self.assertRaises(InvalidTransition):
             self.store.transition(proposal["proposal_id"], "open")
 
     def test_failed_to_open_via_retry_succeeds(self):
-        proposal = self.store.create(item_ref="ENG-23", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-23", kind="triage_file_label", recommendation="x")
         self.store.transition(proposal["proposal_id"], "executing")
         self.store.transition(proposal["proposal_id"], "failed")
         reopened = self.store.retry(proposal["proposal_id"])
@@ -217,12 +241,12 @@ class TestF3ExecutingStateMachine(unittest.TestCase):
         self.assertEqual(confirmed["state"], "confirmed")
 
     def test_retry_from_non_failed_state_raises(self):
-        proposal = self.store.create(item_ref="ENG-24", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-24", kind="triage_file_label", recommendation="x")
         with self.assertRaises(InvalidTransition):
             self.store.retry(proposal["proposal_id"])
 
     def test_confirmed_is_terminal_no_retry(self):
-        proposal = self.store.create(item_ref="ENG-25", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-25", kind="triage_file_label", recommendation="x")
         self.store.transition(proposal["proposal_id"], "executing")
         self.store.transition(proposal["proposal_id"], "confirmed")
         with self.assertRaises(InvalidTransition):
@@ -246,7 +270,7 @@ class TestF5ProposalsLock(unittest.TestCase):
 
     def test_lock_file_created_on_first_write(self):
         self.assertFalse(os.path.exists(self.store.lock_path))
-        self.store.create(item_ref="ENG-30", kind="relabel", recommendation="x")
+        self.store.create(item_ref="ENG-30", kind="triage_file_label", recommendation="x")
         self.assertTrue(os.path.exists(self.store.lock_path))
 
     def test_second_transition_after_out_of_band_mutation_gets_invalid_transition(self):
@@ -256,7 +280,7 @@ class TestF5ProposalsLock(unittest.TestCase):
         'executing'. Process A's transition() call re-reads under the lock
         and correctly rejects its now-stale assumption.
         """
-        proposal = self.store.create(item_ref="ENG-31", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-31", kind="triage_file_label", recommendation="x")
         pid = proposal["proposal_id"]
 
         # Process A "reads" the proposal (simulating having decided, based
@@ -284,7 +308,7 @@ class TestF5ProposalsLock(unittest.TestCase):
         """
         import json as _json
 
-        proposal = self.store.create(item_ref="ENG-33", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-33", kind="triage_file_label", recommendation="x")
         pid = proposal["proposal_id"]
 
         read_before = self.store.get(pid)
@@ -306,7 +330,7 @@ class TestF5ProposalsLock(unittest.TestCase):
         note): two attempts to confirm the same proposal -- the second
         must fail cleanly, never double-apply.
         """
-        proposal = self.store.create(item_ref="ENG-32", kind="relabel", recommendation="x")
+        proposal = self.store.create(item_ref="ENG-32", kind="triage_file_label", recommendation="x")
         pid = proposal["proposal_id"]
         self.store.transition(pid, "executing")
         first = self.store.transition(pid, "confirmed")
@@ -335,7 +359,7 @@ class TestF5ProposalsLock(unittest.TestCase):
         self.assertEqual(final["surfaced_in"], "daily_push_fallback")
 
     def test_update_metadata_never_overwrites_state(self):
-        p = self.store.create(item_ref="ENG-41", kind="relabel", recommendation="x")
+        p = self.store.create(item_ref="ENG-41", kind="triage_file_label", recommendation="x")
         pid = p["proposal_id"]
         self.store.update_metadata({pid: {"state": "confirmed", "surfaced_in": "x"}})
         # state is a reserved key — update_metadata must not change it.
diff --git a/pm-agent/tests/test_replies.py b/pm-agent/tests/test_replies.py
index 329b043..b643f1a 100644
--- a/pm-agent/tests/test_replies.py
+++ b/pm-agent/tests/test_replies.py
@@ -58,7 +58,7 @@ class RepliesTestBase(unittest.TestCase):
     def _make_open_proposal(self, item_ref="LAB-1", recommendation="do the thing", surfaced_in=None):
         self.client.seed_issue(item_ref)
         return self.proposals.create(
-            item_ref=item_ref, kind="reprioritize", recommendation=recommendation, surfaced_in=surfaced_in
+            item_ref=item_ref, kind="freeform_request", recommendation=recommendation, surfaced_in=surfaced_in
         )
 
 
diff --git a/pm-agent/tests/test_standup.py b/pm-agent/tests/test_standup.py
index f499b7a..308d4e7 100644
--- a/pm-agent/tests/test_standup.py
+++ b/pm-agent/tests/test_standup.py
@@ -68,7 +68,7 @@ class TestQueueOrdering(StandupTestBase):
     def test_client_facing_team_proposals_come_first(self):
         self._create("LAB-1", "triage_close", "regular one", created_ts=_iso(NOW - timedelta(days=1)))
         client_facing = self._create(
-            "RES-1", "reprioritize", "client facing one", created_ts=_iso(NOW - timedelta(days=1))
+            "RES-1", "freeform_request", "client facing one", created_ts=_iso(NOW - timedelta(days=1))
         )
         result = build_queue(self.ctx, now=NOW)
         self.assertEqual(result.queue[0]["proposal_id"], client_facing["proposal_id"])
@@ -90,7 +90,7 @@ class TestQueueOrdering(StandupTestBase):
             "LAB-1", "triage_close", "recent close", created_ts=_iso(NOW - timedelta(days=2))
         )
         old_rest = self._create(
-            "LAB-2", "reprioritize", "an old rest-bucket item", created_ts=_iso(NOW - timedelta(days=40))
+            "LAB-2", "freeform_request", "an old rest-bucket item", created_ts=_iso(NOW - timedelta(days=40))
         )
         result = build_queue(self.ctx, now=NOW)
         ids = result.proposal_ids
@@ -99,43 +99,43 @@ class TestQueueOrdering(StandupTestBase):
         self.assertLess(ids.index(old_rest["proposal_id"]), ids.index(recent["proposal_id"]))
 
     def test_rest_bucket_ordered_oldest_first(self):
-        newer = self._create("LAB-1", "reprioritize", "newer", created_ts=_iso(NOW - timedelta(days=1)))
-        older = self._create("LAB-2", "reprioritize", "older", created_ts=_iso(NOW - timedelta(days=5)))
+        newer = self._create("LAB-1", "freeform_request", "newer", created_ts=_iso(NOW - timedelta(days=1)))
+        older = self._create("LAB-2", "freeform_request", "older", created_ts=_iso(NOW - timedelta(days=5)))
         result = build_queue(self.ctx, now=NOW)
         ids = result.proposal_ids
         self.assertLess(ids.index(older["proposal_id"]), ids.index(newer["proposal_id"]))
 
     def test_queue_capped_at_10_with_overflow_reported(self):
         for i in range(14):
-            self._create(f"LAB-{i}", "reprioritize", f"item {i}", created_ts=_iso(NOW - timedelta(days=i)))
+            self._create(f"LAB-{i}", "freeform_request", f"item {i}", created_ts=_iso(NOW - timedelta(days=i)))
         result = build_queue(self.ctx, now=NOW)
         self.assertEqual(len(result.queue), 10)
         self.assertEqual(result.overflow_count, 4)
 
     def test_custom_queue_cap_honored(self):
         for i in range(5):
-            self._create(f"LAB-{i}", "reprioritize", f"item {i}", created_ts=_iso(NOW - timedelta(days=i)))
+            self._create(f"LAB-{i}", "freeform_request", f"item {i}", created_ts=_iso(NOW - timedelta(days=i)))
         self.ctx.queue_cap = 3
         result = build_queue(self.ctx, now=NOW)
         self.assertEqual(len(result.queue), 3)
         self.assertEqual(result.overflow_count, 2)
 
     def test_non_open_proposals_excluded(self):
-        p = self._create("LAB-1", "reprioritize", "closed already")
+        p = self._create("LAB-1", "freeform_request", "closed already")
         self.proposals.transition(p["proposal_id"], "rejected")
         result = build_queue(self.ctx, now=NOW)
         self.assertEqual(result.queue, [])
 
     def test_admin_hygiene_proposals_excluded(self):
         self._create("LAB-1", "triage_file_label", "Recommend filing/labeling LAB-1.")
-        real = self._create("LAB-2", "reprioritize", "Real priority decision.")
+        real = self._create("LAB-2", "freeform_request", "Real priority decision.")
         result = build_queue(self.ctx, now=NOW)
         self.assertEqual(result.proposal_ids, [real["proposal_id"]])
 
 
 class TestKickoffMessageShape(StandupTestBase):
     def test_kickoff_message_is_numbered_one_beat_with_verbs(self):
-        self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         result = kickoff(self.ctx, now=NOW)
         message = result["message"]
         self.assertIn("1. LAB-1", message)
@@ -145,12 +145,12 @@ class TestKickoffMessageShape(StandupTestBase):
         self.assertIn("reply free-text to redirect", message)
 
     def test_kickoff_never_uses_bare_still_active_question(self):
-        self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         result = kickoff(self.ctx, now=NOW)
         self.assertNotIn("still active?", result["message"].lower())
 
     def test_kickoff_sends_via_standup_kind_and_starts_session(self):
-        p = self._create("LAB-1", "reprioritize", "do the thing")
+        p = self._create("LAB-1", "freeform_request", "do the thing")
         kickoff(self.ctx, now=NOW)
         self.notify.assert_called_once()
         args = self.notify.call_args[0]
@@ -163,21 +163,21 @@ class TestKickoffMessageShape(StandupTestBase):
         self.assertEqual(session["skip_count"], 0)
 
     def test_kickoff_dry_run_sends_nothing_and_writes_no_session(self):
-        self._create("LAB-1", "reprioritize", "do the thing")
+        self._create("LAB-1", "freeform_request", "do the thing")
         kickoff(self.ctx, now=NOW, dry_run=True)
         self.notify.assert_not_called()
         self.assertIsNone(self.state.load())
 
     def test_kickoff_reports_overflow_count_in_message(self):
         for i in range(12):
-            self._create(f"LAB-{i}", "reprioritize", f"item {i}")
+            self._create(f"LAB-{i}", "freeform_request", f"item {i}")
         result = kickoff(self.ctx, now=NOW)
         self.assertIn("2 more open proposal", result["message"])
 
 
 class TestOverrideCaptureRatification(StandupTestBase):
     def test_ratify_writes_override_entry_with_full_fields(self):
-        p = self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        p = self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         kickoff(self.ctx, now=NOW)
 
         verb_result = {
@@ -205,7 +205,7 @@ class TestOverrideCaptureRatification(StandupTestBase):
         self.assertEqual(stored[0]["override_id"], entry["override_id"])
 
     def test_ratify_marks_answered_in_session_state(self):
-        p = self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        p = self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         kickoff(self.ctx, now=NOW)
         verb_result = {"kind": "executed", "proposal_id": p["proposal_id"], "detail": {"verb": "go"}}
         record_answer(p["proposal_id"], verb_result, self.ctx, now=_iso(NOW))
@@ -216,7 +216,7 @@ class TestOverrideCaptureRatification(StandupTestBase):
         """record_answer must never itself call proposals.transition or
         actions — the verb execution already happened via replies.py before
         record_answer is invoked."""
-        p = self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        p = self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         kickoff(self.ctx, now=NOW)
         with mock.patch.object(self.proposals, "transition", wraps=self.proposals.transition) as spy:
             verb_result = {"kind": "executed", "proposal_id": p["proposal_id"], "detail": {"verb": "go"}}
@@ -229,7 +229,7 @@ class TestOverrideCaptureRatification(StandupTestBase):
 
 class TestOverrideCaptureRedirect(StandupTestBase):
     def test_redirect_with_reason_captured_verbatim_as_opaque_data(self):
-        p = self._create("LAB-1", "reprioritize", "Recommend going ahead with LAB-1.")
+        p = self._create("LAB-1", "freeform_request", "Recommend going ahead with LAB-1.")
         kickoff(self.ctx, now=NOW)
         reason = "actually let's wait until Q3, budget isn't approved yet"
         verb_result = {
@@ -242,7 +242,7 @@ class TestOverrideCaptureRedirect(StandupTestBase):
         self.assertEqual(entry["reason_text"], reason)
 
     def test_kill_when_agent_did_not_recommend_closing_is_redirect(self):
-        p = self._create("LAB-1", "reprioritize", "Recommend going ahead with LAB-1.")
+        p = self._create("LAB-1", "freeform_request", "Recommend going ahead with LAB-1.")
         kickoff(self.ctx, now=NOW)
         verb_result = {"kind": "executed", "proposal_id": p["proposal_id"], "detail": {"verb": "kill"}}
         entry = record_answer(p["proposal_id"], verb_result, self.ctx, now=_iso(NOW))
@@ -251,7 +251,7 @@ class TestOverrideCaptureRedirect(StandupTestBase):
 
 class TestRepliesHookSeam(StandupTestBase):
     def test_replies_hook_records_when_in_active_session(self):
-        p = self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        p = self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         kickoff(self.ctx, now=NOW)
         result = {"kind": "executed", "proposal_id": p["proposal_id"], "detail": {"verb": "go"}}
         entry = replies_hook(result, self.ctx, now=_iso(NOW + timedelta(hours=1)))
@@ -259,7 +259,7 @@ class TestRepliesHookSeam(StandupTestBase):
         self.assertEqual(entry["proposal_id"], p["proposal_id"])
 
     def test_replies_hook_noop_outside_active_session(self):
-        p = self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        p = self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         kickoff(self.ctx, now=NOW)
         # 49h later — session (48h skip window) is no longer "active".
         result = {"kind": "executed", "proposal_id": p["proposal_id"], "detail": {"verb": "go"}}
@@ -271,9 +271,9 @@ class TestRepliesHookSeam(StandupTestBase):
         self.assertIsNone(entry)
 
     def test_replies_hook_noop_when_proposal_not_in_queue(self):
-        self._create("LAB-1", "reprioritize", "queued")
+        self._create("LAB-1", "freeform_request", "queued")
         kickoff(self.ctx, now=NOW)
-        other = self._create("LAB-2", "reprioritize", "not queued")
+        other = self._create("LAB-2", "freeform_request", "not queued")
         # Force a tiny queue via cap so LAB-2 is overflow, not in-session.
         self.ctx.queue_cap = 1
         session = self.state.load()
@@ -284,7 +284,7 @@ class TestRepliesHookSeam(StandupTestBase):
         self.assertIsNone(entry)
 
     def test_replies_hook_idempotent_on_repeat_call(self):
-        p = self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        p = self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         kickoff(self.ctx, now=NOW)
         result = {"kind": "executed", "proposal_id": p["proposal_id"], "detail": {"verb": "go"}}
         first = replies_hook(result, self.ctx, now=_iso(NOW + timedelta(hours=1)))
@@ -333,7 +333,7 @@ class TestCmdReplyWiresStandupHook(unittest.TestCase):
         overrides = OverrideLog(os.path.join(self.state_dir, "overrides.jsonl"))
 
         p = proposals.create(
-            item_ref="LAB-1", kind="reprioritize", recommendation="Recommend closing LAB-1: stale."
+            item_ref="LAB-1", kind="freeform_request", recommendation="Recommend closing LAB-1: stale."
         )
         # Start a live session (real-time) so is_active() passes when cmd_reply
         # (which uses real now) runs.
@@ -390,7 +390,7 @@ class TestSkipFallback(StandupTestBase):
         self.assertEqual(self.ignored.get("LAB-1"), 1)
 
     def test_skip_does_not_fire_if_any_answer_recorded(self):
-        p = self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
+        p = self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
         kickoff(self.ctx, now=NOW)
         verb_result = {"kind": "executed", "proposal_id": p["proposal_id"], "detail": {"verb": "go"}}
         record_answer(p["proposal_id"], verb_result, self.ctx, now=_iso(NOW + timedelta(hours=1)))
@@ -400,7 +400,7 @@ class TestSkipFallback(StandupTestBase):
 
     def test_skip_marks_top3_queue_items_daily_push_fallback(self):
         for i in range(5):
-            self._create(f"LAB-{i}", "reprioritize", f"item {i}", created_ts=_iso(NOW - timedelta(days=i)))
+            self._create(f"LAB-{i}", "freeform_request", f"item {i}", created_ts=_iso(NOW - timedelta(days=i)))
         kickoff(self.ctx, now=NOW)
         result = check_skip(self.ctx, now=NOW + timedelta(hours=49))
         self.assertEqual(len(result["fallback_marked"]), 3)
@@ -424,9 +424,9 @@ class TestSkipFallback(StandupTestBase):
 
 class TestCloseSession(StandupTestBase):
     def test_close_session_reports_counts(self):
-        p1 = self._create("LAB-1", "reprioritize", "Recommend closing LAB-1: stale.")
-        p2 = self._create("LAB-2", "reprioritize", "Recommend going ahead with LAB-2.")
-        self._create("LAB-3", "reprioritize", "untouched")
+        p1 = self._create("LAB-1", "freeform_request", "Recommend closing LAB-1: stale.")
+        p2 = self._create("LAB-2", "freeform_request", "Recommend going ahead with LAB-2.")
+        self._create("LAB-3", "freeform_request", "untouched")
         kickoff(self.ctx, now=NOW)
 
         record_answer(
@@ -453,7 +453,7 @@ class TestCloseSession(StandupTestBase):
         self.assertEqual(args[0], "standup")
 
     def test_close_session_clears_state(self):
-        self._create("LAB-1", "reprioritize", "do the thing")
+        self._create("LAB-1", "freeform_request", "do the thing")
         kickoff(self.ctx, now=NOW)
         close_session(self.ctx, now=NOW + timedelta(hours=1))
         self.assertIsNone(self.state.load())
```
