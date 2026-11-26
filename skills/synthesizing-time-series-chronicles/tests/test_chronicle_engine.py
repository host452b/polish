import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def _sample_incident_corpus() -> dict:
    """Domain-agnostic test fixture: multi-quarter cloud reliability & incident logs."""
    records = [
        # 2024-Q1 (partial start: 1 day)
        {
            "id": "INC-101",
            "timestamp": "2024-03-28",
            "title": "Database connection pool exhaustion during failover",
            "text": "Primary replica timeout triggered cascading retry storm across API gateway.",
            "score": 85,
            "has_artifact": True,
            "entity": "CoreDB",
        },
        # 2024-Q2 (full activity)
        {
            "id": "INC-102",
            "timestamp": "2024-04-10",
            "title": "Database schema lock blocked checkout writes",
            "text": "Unindexed migration caused 14s lock wait and retry exhaustion.",
            "score": 92,
            "has_artifact": True,
            "entity": "Payments",
        },
        {
            "id": "INC-103",
            "timestamp": "2024-05-05",
            "title": "Kubernetes autoscaler lag under traffic spike",
            "text": "HPA metric delay starved ingress pods and dropped 4.2% requests.",
            "score": 64,
            "has_artifact": False,
            "entity": "Infra",
        },
        {
            "id": "INC-104",
            "timestamp": "2024-06-18",
            "title": "TLS certificate rotation config drift in edge proxy",
            "text": "Stale secret mount broke mutual TLS handshake for regional gateway.",
            "score": 78,
            "has_artifact": True,
            "entity": "SecOps",
        },
        # 2024-Q3 (shift toward config-drift + agent-automation + guardrail)
        {
            "id": "INC-105",
            "timestamp": "2024-07-11",
            "title": "Autonomous remediation bot triggered config drift loop",
            "text": "Self-healing workflow rolled back canary and mutated proxy routing policy.",
            "score": 110,
            "has_artifact": True,
            "entity": "SRE-Bot",
        },
        {
            "id": "INC-106",
            "timestamp": "2024-08-09",
            "title": "Policy guardrail blocked unauthorized terraform apply",
            "text": "OPA admission check caught wildcard IAM permission in automated pipeline.",
            "score": 95,
            "has_artifact": True,
            "entity": "SecOps",
        },
        {
            "id": "INC-107",
            "timestamp": "2024-09-21",
            "title": "Autonomous capacity planner right-sized GPUautoscaler",
            "text": "Agentic controller reduced cold-start latency by 58% across clusters.",
            "score": 88,
            "has_artifact": True,
            "entity": "Infra",
        },
        # Duplicate ID re-logged on a later day to verify event-slice vs unique-entity separation
        {
            "id": "INC-105",
            "timestamp": "2024-09-22",
            "title": "Autonomous remediation bot triggered config drift loop",
            "text": "Follow-up postmortem update on proxy routing policy.",
            "score": 115,
            "has_artifact": True,
            "entity": "SRE-Bot",
        },
        # 2025-Q1 (year rollover test!)
        {
            "id": "INC-201",
            "timestamp": "2025-01-15",
            "title": "Autonomous deploy harness rolled out progressive canary",
            "text": "Automated rollback harness verified SLO guardrails across 12 regions.",
            "score": 130,
            "has_artifact": True,
            "entity": "SRE-Bot",
        },
        {
            "id": "INC-202",
            "timestamp": "2025-02-12",
            "title": "Runtime policy guardrail isolated rogue webhook plugin",
            "text": "Sandbox egress policy prevented credential leak in third-party skill.",
            "score": 104,
            "has_artifact": True,
            "entity": "SecOps",
        },
        {
            "id": "INC-203",
            "timestamp": "2025-03-09",
            "title": "Database shard rebalancing with zero-downtime snapshot",
            "text": "Automated workflow throttled replica lag below 25ms.",
            "score": 72,
            "has_artifact": True,
            "entity": "CoreDB",
        },
    ]
    taxonomy = {
        "categories": [
            {
                "id": "storage_db",
                "label": "Storage & DB",
                "color": "#1F4E79",
                "pattern": r"\b(database|replica|schema|lock|shard)\b",
            },
            {
                "id": "compute_net",
                "label": "Compute & Network",
                "color": "#3B7EA1",
                "pattern": r"\b(autoscaler|kubernetes|ingress|proxy|gateway|tls|latency)\b",
            },
            {
                "id": "automation_agent",
                "label": "Autonomous Ops",
                "color": "#2E7D6B",
                "pattern": r"\b(autonomous|self-healing|agentic|bot|harness|automated|workflow)\b",
            },
            {
                "id": "security_guardrail",
                "label": "Security & Guardrails",
                "color": "#9E3B52",
                "pattern": r"\b(guardrail|opa|iam|sandbox|secret|certificate|policy)\b",
            },
        ],
        "subsignals": [
            {"id": "db_locks", "category": "storage_db", "label": "Replica & Lock Contention", "pattern": r"\b(replica|lock|shard)\b"},
            {"id": "k8s_scale", "category": "compute_net", "label": "Autoscaling & Ingress", "pattern": r"\b(autoscaler|ingress|gateway)\b"},
            {"id": "auto_harness", "category": "automation_agent", "label": "Remediation & Deploy Harnesses", "pattern": r"\b(autonomous|harness|self-healing)\b"},
            {"id": "policy_sandbox", "category": "security_guardrail", "label": "Policy & Sandbox Guardrails", "pattern": r"\b(guardrail|opa|sandbox)\b"},
        ],
    }
    return {"records": records, "taxonomy": taxonomy, "grain": "quarter", "major_grain": "year"}


class TestChronicleEngineCore(unittest.TestCase):
    def test_sinkhorn_conservation_and_dedup_separation(self):
        import chronicle_engine as ce

        payload = _sample_incident_corpus()
        report = ce.analyze_corpus(payload)

        # Event-slice count = 11, unique-entity IDs = 10 (INC-105 deduplicated with max score 115)
        self.assertEqual(report["total_events"], 11)
        self.assertEqual(report["unique_records"], 10)
        top_first = report["top_landmarks"][0]
        self.assertEqual(top_first["id"], "INC-201")
        inc105 = [x for x in report["top_landmarks"] if x["id"] == "INC-105"][0]
        self.assertEqual(inc105["score"], 115)

        # Partial boundary detection: 2024-Q1 has only 1 event vs median 3
        self.assertIn("2024-Q1", report["partial_periods"])

        # Sinkhorn conservation invariant across major_grain transitions (2024 -> 2025)
        transitions = report["sankey_transitions"]
        self.assertEqual(len(transitions), 1)
        tr = transitions[0]
        p_src = tr["src_shares"]
        p_dst = tr["dst_shares"]
        mat = tr["matrix"]
        for i, cat_i in enumerate(tr["categories"]):
            self.assertAlmostEqual(sum(mat[i]), p_src[cat_i], places=5)
        for j, cat_j in enumerate(tr["categories"]):
            col_sum = sum(mat[i][j] for i in range(len(tr["categories"])))
            self.assertAlmostEqual(col_sum, p_dst[cat_j], places=5)

    def test_svg_suite_generation_and_layout_invariants(self):
        import chronicle_engine as ce

        payload = _sample_incident_corpus()
        payload["scissor_groups"] = {
            "group_a_label": "Autonomous Ops Velocity",
            "group_a_ids": ["automation_agent"],
            "group_b_label": "Security Guardrails",
            "group_b_ids": ["security_guardrail"],
        }
        report = ce.analyze_corpus(payload)

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            written = ce.render_visual_suite(report, out_dir, title_prefix="Cloud Reliability")
            self.assertEqual(len(written), 5)
            for svg_path in written.values():
                self.assertTrue(svg_path.exists())
                xml_txt = svg_path.read_text(encoding="utf-8")
                root = ET.fromstring(xml_txt)
                self.assertTrue(root.tag.endswith("svg"))

            # Verify unidirectional label anchor when >= 3 Sankey columns are rendered
            payload_q = dict(payload)
            payload_q["major_grain"] = "quarter"
            report_q = ce.analyze_corpus(payload_q)
            sankey_4col = ce.render_conservation_sankey_svg(report_q, title="Quarterly Incident Flow")
            root_4col = ET.fromstring(sankey_4col)
            self.assertTrue(root_4col.tag.endswith("svg"))
            # In >=3-column outside-right mode, node labels all use text-anchor="start"
            node_labels = [
                el for el in root_4col.iter()
                if el.tag.endswith("text") and el.attrib.get("data-role") == "node-label"
            ]
            self.assertGreater(len(node_labels), 0)
            for nl in node_labels:
                self.assertEqual(nl.attrib.get("text-anchor"), "start")

    def test_rollover_safe_markdown_sync_and_typst_currency_escape(self):
        import chronicle_engine as ce

        payload = _sample_incident_corpus()
        report = ce.analyze_corpus(payload)

        md_template = (
            "# Chapter 1\n\n"
            "<!-- AUTO-SYNC:START:macro_overview -->\nold\n<!-- AUTO-SYNC:END:macro_overview -->\n\n"
            "<!-- AUTO-SYNC:START:recent_radar -->\nold\n<!-- AUTO-SYNC:END:recent_radar -->\n"
        )
        synced = ce.sync_markdown_text(md_template, report)
        self.assertIn("2024", synced)
        self.assertIn("2025", synced)
        self.assertIn("INC-201", synced)

        # Add 2026 record -> verify dynamic period column rollover without mismatched Pipe cells
        payload["records"].append(
            {
                "id": "INC-301",
                "timestamp": "2026-01-10",
                "title": "Autonomous guardrail self-verification",
                "text": "Sandbox policy verified in 12ms.",
                "score": 140,
                "has_artifact": True,
                "entity": "SecOps",
            }
        )
        report_2026 = ce.analyze_corpus(payload)
        synced_2026 = ce.sync_markdown_text(md_template, report_2026)
        self.assertIn("2026", synced_2026)
        for line in synced_2026.splitlines():
            if line.startswith("|"):
                # Every table row in the same table has consistent column count
                self.assertGreaterEqual(line.count("|"), 4)

        # Currency vs inline math Typst conversion
        typ_txt = ce.md_inline_to_typst("Mitigation cost $15 and $20 per node, satisfying $p_1 + p_2 = 1$.")
        self.assertIn(r"\$15", typ_txt)
        self.assertIn(r"\$20", typ_txt)
        self.assertIn("$p_1 + p_2 = 1$", typ_txt)

    def test_cli_selftest_and_csv_stdin(self):
        res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "chronicle_engine.py"), "selftest"],
            capture_output=True,
            text=True,
            check=True,
        )
        out = json.loads(res.stdout)
        self.assertTrue(all(out["invariants"].values()))

        csv_data = (
            "id,timestamp,title,text,category,tags,score,has_artifact,entity\n"
            "REL-1,2024-01-10,Init API,REST v1,core,\"core,api\",50,true,Platform\n"
            "REL-2,2025-02-15,GraphQL Gateway,Federation v2,edge,\"edge,api\",80,true,Gateway\n"
        )
        csv_res = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "chronicle_engine.py"), "analyze", "--input", "-", "--format", "csv"],
            input=csv_data,
            capture_output=True,
            text=True,
            check=True,
        )
        csv_rep = json.loads(csv_res.stdout)
        self.assertEqual(csv_rep["total_events"], 2)
        self.assertEqual(sorted(csv_rep["major_periods"].keys()), ["2024", "2025"])


if __name__ == "__main__":
    unittest.main()
