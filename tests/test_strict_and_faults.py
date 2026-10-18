import os
import tempfile
import unittest
from urllib.error import HTTPError

from firedrill import tools
from firedrill.guardrail import wrap_tools
from firedrill.payments_server import create_server
import threading
import json
import urllib.request


def _raw(refund):
    return {"refund": refund, "get_refund_status": lambda order_id: {"order_id": order_id, "refunds": []}, "pay": lambda a, b: {}}


class StrictGuardrailTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.old = os.environ.get("TRACE_PATH")
        os.environ["TRACE_PATH"] = os.path.join(self.dir.name, "trace.jsonl")

    def tearDown(self):
        if self.old is None:
            os.environ.pop("TRACE_PATH", None)
        else:
            os.environ["TRACE_PATH"] = self.old
        self.dir.cleanup()

    def test_strict_ignores_model_key_and_default_keeps_it(self):
        seen = []

        def refund(order_id, amount, idempotency_key=None):
            seen.append(idempotency_key)
            return {"status": "processed"}

        wrap_tools(_raw(refund), strict=True)["refund"]("1001", 100, idempotency_key="model-key")
        wrap_tools(_raw(refund))["refund"]("1001", 100, idempotency_key="model-key")
        self.assertNotEqual(seen[0], "model-key")
        self.assertTrue(seen[0].startswith("refund-"))
        self.assertEqual(seen[1], "model-key")

    def test_strict_checks_ledger_after_a_non_timeout_error(self):
        calls = []

        def refund(order_id, amount, idempotency_key=None):
            calls.append(idempotency_key)
            raise tools.ToolError("HTTP Error 500")

        raw = _raw(refund)
        raw["get_refund_status"] = lambda order_id: {"order_id": order_id, "refunds": [{"order_id": order_id, "refund_id": 1}]}
        out = wrap_tools(raw, strict=True)["refund"]("1001", 100)
        self.assertTrue(out["recovered_after_timeout"])
        self.assertEqual(len(calls), 1)

    def test_default_guardrail_does_not_swallow_a_non_timeout_error(self):
        def refund(order_id, amount, idempotency_key=None):
            raise tools.ToolError("HTTP Error 500")

        with self.assertRaises(tools.ToolError):
            wrap_tools(_raw(refund))["refund"]("1001", 100)

    def test_strict_retries_once_when_nothing_was_committed(self):
        calls = []

        def refund(order_id, amount, idempotency_key=None):
            calls.append(idempotency_key)
            if len(calls) == 1:
                raise tools.ToolError("HTTP Error 503")
            return {"status": "processed"}

        wrap_tools(_raw(refund), strict=True)["refund"]("1001", 100)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0], calls[1])


class NewFaultServerTest(unittest.TestCase):
    def _serve(self, fault):
        d = tempfile.TemporaryDirectory()
        srv = create_server(os.path.join(d.name, "l.db"), port=0, fault=fault, fault_delay=0.1)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(d.cleanup)
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        return f"http://127.0.0.1:{srv.server_address[1]}"

    def _post(self, base, body):
        req = urllib.request.Request(base + "/refund", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status
        except HTTPError as e:
            return e.code

    def _count(self, base):
        with urllib.request.urlopen(base + "/refund/1001", timeout=5) as r:
            return len(json.load(r)["refunds"])

    def test_fail_before_commit_commits_nothing_then_succeeds(self):
        base = self._serve("fail_before_commit")
        self.assertEqual(self._post(base, {"order_id": "1001", "amount": 100}), 503)
        self.assertEqual(self._count(base), 0)
        self.assertEqual(self._post(base, {"order_id": "1001", "amount": 100}), 201)
        self.assertEqual(self._count(base), 1)

    def test_error_after_commit_commits_then_answers_500(self):
        base = self._serve("error_after_commit")
        self.assertEqual(self._post(base, {"order_id": "1001", "amount": 100}), 500)
        self.assertEqual(self._count(base), 1)
        self.assertEqual(self._post(base, {"order_id": "1001", "amount": 100, "idempotency_key": "k"}), 201)
        self.assertEqual(self._count(base), 2)


if __name__ == "__main__":
    unittest.main()


class StaleStatusFaultTest(NewFaultServerTest):
    def test_timeout_stale_status_commits_then_hides_it_from_the_first_two_lookups(self):
        base = self._serve("timeout_stale_status")
        try:
            self._post(base, {"order_id": "1001", "amount": 100})   # commits, then answers late
        except Exception:
            pass
        self.assertEqual(self._count(base), 0)
        self.assertEqual(self._count(base), 0)
        self.assertEqual(self._count(base), 1)


class RateLimitedRetryFaultTest(NewFaultServerTest):
    def test_timeout_then_429_commits_first_rate_limits_the_retry_then_allows_a_third(self):
        base = self._serve("timeout_then_429")
        self._post(base, {"order_id": "1001", "amount": 100})           # commits, answers late
        self.assertEqual(self._count(base), 1)
        self.assertEqual(self._post(base, {"order_id": "1001", "amount": 100}), 429)
        self.assertEqual(self._count(base), 1)
        self.assertEqual(self._post(base, {"order_id": "1001", "amount": 100, "idempotency_key": "k"}), 201)
        self.assertEqual(self._count(base), 2)
