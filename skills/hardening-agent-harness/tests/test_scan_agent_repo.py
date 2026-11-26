#!/usr/bin/env python3
"""Unit tests for skills/hardening-agent-harness/scripts/scan_agent_repo.py."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "scan_agent_repo.py"
SPEC = importlib.util.spec_from_file_location("scan_agent_repo", SCRIPT_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class ScanAgentRepoTests(unittest.TestCase):
    def test_catches_harness_fragility_patterns(self) -> None:
        fragile_py = '''
import datetime, subprocess

def refund_order(order_id: str, amount: float):
    subprocess.run(f"curl https://pay.example/{order_id}", shell=True)

def run_agent(client, user_q):
    while True:
        msgs = [
            {"role": "system", "content": f"Now: {datetime.datetime.now()}"},
            {"role": "user", "content": f"tool_call_id=1 <tool_response>ok</tool_response>"},
            {"role": "assistant", "content": None, "tool_calls": []},
        ]
        resp = client.chat.completions.create(model="x", messages=msgs, stream=True)
'''
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "fragile_agent.py"
            f.write_text(fragile_py, encoding="utf-8")
            rules = {x.rule for x in MOD.scan_target(Path(td))}
            self.assertIn("H001_DYNAMIC_SYSTEM_PREFIX_CACHE_BUST", rules)
            self.assertIn("H002_STREAM_WITHOUT_IDLE_WATCHDOG", rules)
            self.assertIn("H003_UNBOUNDED_AGENT_OR_RETRY_LOOP", rules)
            self.assertIn("H004_TOOL_RESULT_IN_USER_ROLE", rules)
            self.assertIn("H005_SHELL_TRUE_EXEC", rules)
            self.assertIn("H006_MUTATION_WITHOUT_IDEMPOTENCY", rules)
            self.assertIn("H007_DROPPED_REASONING_IN_TOOL_LOOP", rules)

    def test_clean_harness_passes(self) -> None:
        clean_py = '''
import subprocess

def refund_order(order_id: str, idempotency_key: str):
    return subprocess.run(["echo", order_id], shell=False, timeout=10)

def run_agent(client, history):
    for rounds in range(8):
        resp = client.chat.completions.create(model="x", messages=history, stream=True, timeout=30)
        msg = resp.choices[0].message
        history.append(msg.model_dump(exclude_none=True))
'''
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "clean_agent.py"
            f.write_text(clean_py, encoding="utf-8")
            self.assertEqual(MOD.scan_target(Path(td)), [])


if __name__ == "__main__":
    unittest.main()
