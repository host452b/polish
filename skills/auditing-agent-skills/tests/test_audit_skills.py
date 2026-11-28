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

    def test_detects_plain_yaml_colon_and_comment_hazards(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "hazard-skill"
            bad.mkdir()
            (bad / "SKILL.md").write_text(
                "---\nname: hazard-skill\ndescription: Use when auditing YAML: unquoted colon # and trailing comment\n---\n\n# Body\n",
                encoding="utf-8",
            )
            bad_rules = {f.rule for f in MOD.audit_single_skill(bad)}
            self.assertIn("S002_PLAIN_YAML_HAZARD", bad_rules)

            good = Path(td) / "folded-skill"
            good.mkdir()
            (good / "SKILL.md").write_text(
                "---\nname: folded-skill\ndescription: >-\n  Use when auditing YAML: folded block safely carries colons and # hashes.\n---\n\n# Body\n",
                encoding="utf-8",
            )
            self.assertEqual(MOD.audit_single_skill(good), [])

    def test_detects_broken_heading_anchor_and_accepts_valid_slugs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "anchor-skill"
            (sd / "references").mkdir(parents=True)
            (sd / "references" / "guide.md").write_text(
                "# Guide\n\n## 1. Pointer and DAG Surgery\n\n## 中文标题\n\nText.\n\n<a id=\"custom-anchor\"></a>\n",
                encoding="utf-8",
            )
            (sd / "SKILL.md").write_text(
                "---\nname: anchor-skill\ndescription: Use when testing markdown anchor validation.\n---\n\n"
                "Read [ok](references/guide.md#1-pointer-and-dag-surgery), "
                "[zh](references/guide.md#%E4%B8%AD%E6%96%87%E6%A0%87%E9%A2%98), "
                "[tag](references/guide.md#custom-anchor), and "
                "[dead](references/guide.md#non-existent-section).\n",
                encoding="utf-8",
            )
            findings = MOD.audit_single_skill(sd)
            self.assertEqual([f.rule for f in findings], ["D4_BROKEN_ANCHOR"])
            self.assertIn("non-existent-section", findings[0].message)

    def test_detects_thin_router_budget_and_unconditional_reference_loading(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "bloated-router"
            sd.mkdir()
            padding = "Step detail line for router budget check.\n" * 210
            (sd / "SKILL.md").write_text(
                "---\nname: bloated-router\ndescription: Use when routing multi-domain requests.\n---\n\n"
                "This entry is a thin router, not an execution playbook.\n"
                "Always read all files in `references/` before acting.\n\n" + padding,
                encoding="utf-8",
            )
            rules = {f.rule for f in MOD.audit_single_skill(sd)}
            self.assertIn("S015_ROUTER_BUDGET", rules)
            self.assertIn("D3_UNCONDITIONAL_REF_LOAD", rules)

    def test_audit_collection_detects_cross_skill_links_and_dag_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sa = root / "skill-alpha"
            sb = root / "skill-beta"
            sa.mkdir()
            sb.mkdir()
            (sa / "SKILL.md").write_text(
                "---\nname: skill-alpha\ndescription: Use when running alpha tasks.\n---\n\nSee [beta](../skill-beta/SKILL.md).\n",
                encoding="utf-8",
            )
            (sb / "SKILL.md").write_text(
                "---\nname: skill-beta\ndescription: Use when running beta tasks.\n---\n\nSee [alpha](../skill-alpha/SKILL.md).\n",
                encoding="utf-8",
            )
            findings = MOD.audit_collection(root)
            rules = {f.rule for f in findings}
            self.assertIn("D5_CROSS_SKILL_LINK", rules)
            self.assertIn("D5_SKILL_DAG_CYCLE", rules)

    def test_detects_hardcoded_workstation_paths_in_bundled_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "scripted-skill"
            (sd / "scripts").mkdir(parents=True)
            (sd / "SKILL.md").write_text(
                "---\nname: scripted-skill\ndescription: Use when running deterministic helper scripts.\n---\n\nRun `scripts/helper.py`.\n",
                encoding="utf-8",
            )
            (sd / "scripts" / "helper.py").write_text(
                "from pathlib import Path\nBASE = Path('/Users/alice/.claude/skills/scripted-skill')\n",
                encoding="utf-8",
            )
            rules = {f.rule for f in MOD.audit_single_skill(sd)}
            self.assertIn("D6_SCRIPT_HARDCODED_PATH", rules)

            (sd / "scripts" / "helper.py").write_text(
                "from pathlib import Path\nBASE = Path(__file__).resolve().parent\n",
                encoding="utf-8",
            )
            self.assertEqual(MOD.audit_single_skill(sd), [])

    def test_validates_model_scaffolding_tags_and_openai_display_name(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "scaffold-skill"
            (sd / "agents").mkdir(parents=True)
            (sd / "agents" / "openai.yaml").write_text(
                'interface:\n  display_name: "Scaffold Skill"\n  default_prompt: "Use $scaffold-skill now."\n',
                encoding="utf-8",
            )
            (sd / "SKILL.md").write_text(
                "---\nname: scaffold-skill\ndescription: Use when testing model scaffolding metadata.\n---\n\n"
                '<!-- model-scaffolding: reason="prevent skip" -->\nRead first.\n',
                encoding="utf-8",
            )
            rules = {f.rule for f in MOD.audit_single_skill(sd)}
            self.assertIn("D7_UNCLOSED_SCAFFOLDING", rules)
            self.assertIn("D7_UNDATED_SCAFFOLDING", rules)
            self.assertIn("S016_OPENAI_DISPLAY_NAME", rules)

            (sd / "agents" / "openai.yaml").write_text(
                'interface:\n  display_name: "scaffold-skill"\n  default_prompt: "Use $scaffold-skill now."\n',
                encoding="utf-8",
            )
            (sd / "SKILL.md").write_text(
                "---\nname: scaffold-skill\ndescription: Use when testing model scaffolding metadata.\n---\n\n"
                '<!-- model-scaffolding: reason="prevent skip" review-on="next-frontier-model" -->\n'
                'Read first and keep inline mentions like `<!-- model-scaffolding: reason="..." review-on="..." -->` safe.\n'
                "<!-- /model-scaffolding -->\n",
                encoding="utf-8",
            )
            self.assertEqual(MOD.audit_single_skill(sd), [])

    def test_detects_vague_completion_repeated_rules_and_reversible_nags(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sd = Path(td) / "prose-heavy-skill"
            sd.mkdir()
            repeated = "- Never mutate output files without first reading the full source content."
            (sd / "SKILL.md").write_text(
                "---\nname: prose-heavy-skill\ndescription: Use when testing structural rule migration.\n---\n\n"
                "# Prose Heavy\n\n"
                f"{repeated}\n\n"
                "1. Ask the user for confirmation before each file edit.\n"
                "2. Iterate until everything looks good and high quality.\n\n"
                "## Notes\n\n"
                f"{repeated}\n",
                encoding="utf-8",
            )
            rules = {f.rule for f in MOD.audit_single_skill(sd)}
            self.assertIn("D8_VAGUE_COMPLETION", rules)
            self.assertIn("D9_REPEATED_PROSE_RULE", rules)
            self.assertIn("D10_REVERSIBLE_CONFIRMATION_NAG", rules)

    def test_verify_against_baseline_blocks_relaxation_and_passes_genuine_fix(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            sd = root / "target-skill"
            sd.mkdir()
            (sd / "SKILL.md").write_text(
                "---\nname: target-skill\ndescription: >-\n"
                "  Use when auditing baseline verification across target skill artifacts and preventing silent trigger gutting during polish.\n"
                "---\n\n# Target\n\nSee [broken](references/missing.md).\n",
                encoding="utf-8",
            )
            baseline = MOD.build_report(root)
            self.assertEqual(baseline["errors"], 1)

            # Case 1: Agent fixes broken link by gutting description to a stub -> must FAIL V004_DESCRIPTION_GUTTED
            (sd / "SKILL.md").write_text(
                "---\nname: target-skill\ndescription: Use when testing.\n---\n\n# Target\n\n1. Run `scripts/check.py`.\n",
                encoding="utf-8",
            )
            gutted_issues = MOD.verify_against_baseline(baseline, MOD.build_report(root))
            self.assertIn("V004_DESCRIPTION_GUTTED", {i.rule for i in gutted_issues})

            # Case 2: Agent fixes broken link and trims an 800-char bloated description to a valid 160-char trigger pointer -> must PASS ([])
            (sd / "references").mkdir()
            (sd / "references" / "missing.md").write_text("# Restored Reference\n", encoding="utf-8")
            bloated_baseline = {
                **baseline,
                "warnings": 1,
                "skills_meta": {"target-skill": {**baseline["skills_meta"]["target-skill"], "desc_len": 800}},
            }
            (sd / "SKILL.md").write_text(
                "---\nname: target-skill\ndescription: >-\n"
                "  Use when auditing baseline verification across target skill artifacts and preventing silent trigger gutting during polish runs.\n"
                "---\n\n# Target\n\nSee [restored](references/missing.md).\n",
                encoding="utf-8",
            )
            clean_issues = MOD.verify_against_baseline(bloated_baseline, MOD.build_report(root))
            self.assertEqual(clean_issues, [])


if __name__ == "__main__":
    unittest.main()
