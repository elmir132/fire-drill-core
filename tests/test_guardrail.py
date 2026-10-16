import json
import os
import unittest

from firedrill import guardrail, simulate


class GuardrailTest(unittest.TestCase):
    def test_guardrail_off_double_refunds(self):
        r = simulate.run(False)
        self.assertEqual(r["refunds_total"], 2)
        self.assertEqual(r["duplicate_refunds"], 1)
        self.assertFalse(r["safe"])

    def test_guardrail_on_single_refund(self):
        r = simulate.run(True)
        self.assertEqual(r["refunds_total"], 1)
        self.assertEqual(r["duplicate_refunds"], 0)
        self.assertTrue(r["safe"])
        self.assertEqual(r["score"], 100)

    def test_guarded_run_uses_one_key_only(self):
        r = simulate.run(True)
        keys = set()
        with open(os.path.join(r["workdir"], "trace.jsonl")) as f:
            for line in f:
                e = json.loads(line)
                if e["tool"] == "refund":
                    keys.add(e["args"]["idempotency_key"])
        self.assertEqual(len(keys), 1)
        self.assertNotIn(None, keys)

    def test_no_fault_single_refund_in_both_modes(self):
        for g in (False, True):
            r = simulate.run(g, fault="")
            self.assertEqual(r["refunds_total"], 1, g)
            self.assertTrue(r["safe"])

    def test_stable_key_is_deterministic(self):
        self.assertEqual(guardrail.stable_key("1001", 100), guardrail.stable_key("1001", 100))
        self.assertNotEqual(guardrail.stable_key("1001", 100), guardrail.stable_key("1002", 100))


if __name__ == "__main__":
    unittest.main()
