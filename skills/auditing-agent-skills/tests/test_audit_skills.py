#!/usr/bin/env python3
"""Unit tests for skills/auditing-agent-skills/scripts/audit_skills.py."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_skills.py"
SPEC = importlib.util.spec_from_file_location("audit_skills", SCRIPT_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class AuditSkillsTests(unittest.TestCase):
    def test_clean_skill_passes_with_zero_findings(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "clean-skill"
            sd.mkdir()
            (sd / "SKILL.md").write_text(
                "---\nname: clean-skill\ndescription: Use when testing clean skill auditing.\n---\n\n# Clean Skill\n\n1. Run check.\n",
                encoding="utf-8",
            )
            findings = MOD.audit_single_skill(sd)
            self.assertEqual(findings, [])

    def test_detects_workflow_leak_and_broken_link_and_angle_brackets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "leaky-skill"
            sd.mkdir()
            (sd / "SKILL.md").write_text(
                "---\nname: leaky-skill\ndescription: 设计系统时使用——覆盖步骤一与 <bad> 标签。\n---\n\nSee [missing](references/missing.md) and `book/chapter2.md`.\n",
                encoding="utf-8",
            )
            rules = {f.rule for f in MOD.audit_single_skill(sd)}
            self.assertIn("S008_ANGLE_BRACKETS_IN_DESC", rules)
            self.assertIn("D1_SDO_WORKFLOW_LEAK", rules)
            self.assertIn("D4_BROKEN_LINK", rules)
            self.assertIn("D4_REPO_COUPLED_PATH", rules)


if __name__ == "__main__":
    unittest.main()
