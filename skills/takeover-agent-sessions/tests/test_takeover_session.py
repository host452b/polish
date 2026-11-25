import base64
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import takeover_session as ts


def _encode_varint(value: int) -> bytes:
    out = bytearray()
    while True:
        chunk = value & 0x7F
        value >>= 7
        if value:
            out.append(chunk | 0x80)
        else:
            out.append(chunk)
            break
    return bytes(out)


def _pb_field_bytes(field_no: int, payload: bytes) -> bytes:
    tag = (field_no << 3) | 2
    return _encode_varint(tag) + _encode_varint(len(payload)) + payload


def _pb_field_str(field_no: int, text: str) -> bytes:
    return _pb_field_bytes(field_no, text.encode("utf-8"))


class TestCrossOsPathsAndCryptoPrimitives(unittest.TestCase):
    def test_resolve_roots_for_macos_linux_and_windows(self):
        mac = ts.resolve_harness_roots(
            os_name="macos",
            home=Path("/Users/alice"),
            env={},
        )
        self.assertIn(
            Path("/Users/alice/Library/Application Support/Cursor/User"),
            mac["cursor"]["ide_roots"],
        )
        self.assertIn(
            Path("/Users/alice/Library/Application Support/Zed/threads/threads.db"),
            mac["zed"]["thread_dbs"],
        )
        self.assertIn(
            Path("/Users/alice/.local/share/devin/cli/sessions.db"),
            mac["devin"]["dbs"],
        )

        linux = ts.resolve_harness_roots(
            os_name="linux",
            home=Path("/home/alice"),
            env={"FLATPAK_XDG_DATA_HOME": "/home/alice/.var/app/dev.zed.Zed/data"},
        )
        self.assertIn(
            Path("/home/alice/.config/Cursor/User"),
            linux["cursor"]["ide_roots"],
        )
        self.assertIn(
            Path("/home/alice/.var/app/dev.zed.Zed/data/zed/threads/threads.db"),
            linux["zed"]["thread_dbs"],
        )
        self.assertIn(
            Path("/home/alice/.local/share/opencode/opencode.db"),
            linux["opencode"]["dbs"],
        )

        win = ts.resolve_harness_roots(
            os_name="windows",
            home=Path("C:/Users/alice"),
            env={
                "APPDATA": "C:/Users/alice/AppData/Roaming",
                "LOCALAPPDATA": "C:/Users/alice/AppData/Local",
                "USERPROFILE": "C:/Users/alice",
            },
        )
        self.assertIn(
            Path("C:/Users/alice/AppData/Roaming/Cursor/User"),
            win["cursor"]["ide_roots"],
        )
        self.assertIn(
            Path("C:/Users/alice/AppData/Local/Zed/threads/threads.db"),
            win["zed"]["thread_dbs"],
        )
        self.assertIn(
            Path("C:/Users/alice/AppData/Roaming/devin/cli/sessions.db"),
            win["devin"]["dbs"],
        )
        self.assertIn(
            Path("C:/Users/alice/AppData/Local/kiro-cli/data.sqlite3"),
            win["kiro"]["headless_dbs"],
        )
        self.assertIn(
            Path("C:/Users/alice/.codeium/windsurf/cascade"),
            win["windsurf"]["cascade_dirs"],
        )

    def test_aes_256_gcm_roundtrip_and_tamper_rejection(self):
        key = ts.WINDSURF_AES_KEY
        self.assertEqual(len(key), 32)
        nonce = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c"
        plaintext = b"CortexTrajectory synthetic payload with UTF-8 \xe4\xb8\xad\xe6\x96\x87"

        sealed_pure = ts._aes256_gcm_encrypt_pure(key, nonce, plaintext)
        opened_pure = ts._aes256_gcm_decrypt_pure(key, nonce, sealed_pure)
        self.assertEqual(opened_pure, plaintext)
        self.assertEqual(ts.decrypt_aes256_gcm(key, nonce + sealed_pure), plaintext)

        tampered = bytearray(nonce + sealed_pure)
        tampered[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            ts.decrypt_aes256_gcm(key, bytes(tampered))

    def test_secret_redaction(self):
        raw = (
            "Export OPENAI_API_KEY=sk-proj-1234567890abcdefghijklmnop "
            "and token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
            "and Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def"
        )
        cleaned = ts.redact_secrets(raw)
        self.assertNotIn("sk-proj-1234567890", cleaned)
        self.assertNotIn("ghp_ABCDEF", cleaned)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIs", cleaned)
        self.assertIn("<REDACTED>", cleaned)


class TestAllNineHarnessAdapters(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name) / "home"
        self.appdata = self.home / "AppData" / "Roaming"
        self.localappdata = self.home / "AppData" / "Local"
        self.xdg_data = self.home / ".local" / "share"
        self.xdg_config = self.home / ".config"
        for p in (self.home, self.appdata, self.localappdata, self.xdg_data, self.xdg_config):
            p.mkdir(parents=True, exist_ok=True)
        self.env = {
            "HOME": str(self.home),
            "USERPROFILE": str(self.home),
            "APPDATA": str(self.appdata),
            "LOCALAPPDATA": str(self.localappdata),
            "XDG_DATA_HOME": str(self.xdg_data),
            "XDG_CONFIG_HOME": str(self.xdg_config),
        }
        self.repo_dir = "/work/acme-payments"

    def tearDown(self):
        self._tmp.cleanup()

    def test_claude_code_jsonl_and_subagent_sidechain(self):
        proj = self.home / ".claude" / "projects" / "-work-acme-payments"
        sub_dir = proj / "sess-claude-001" / "subagents"
        sub_dir.mkdir(parents=True)
        lines = [
            {
                "type": "user",
                "isMeta": True,
                "sessionId": "sess-claude-001",
                "cwd": self.repo_dir,
                "timestamp": "2026-11-20T10:00:00Z",
                "message": {"role": "user", "content": "<local-command-caveat>ignore</local-command-caveat>"},
            },
            {
                "type": "user",
                "sessionId": "sess-claude-001",
                "cwd": self.repo_dir,
                "gitBranch": "feat/webhook-retry",
                "timestamp": "2026-11-20T10:00:02Z",
                "message": {
                    "role": "user",
                    "content": "<command-name>/model</command-name>\nImplement idempotent webhook retry with backoff",
                },
            },
            {
                "type": "assistant",
                "sessionId": "sess-claude-001",
                "cwd": self.repo_dir,
                "timestamp": "2026-11-20T10:01:00Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "thinking", "thinking": "internal"},
                        {"type": "text", "text": "Updated retry handler; running pytest next."},
                        {"type": "tool_use", "name": "Edit", "input": {"file_path": "src/webhook.py"}},
                        {"type": "tool_use", "name": "Bash", "input": {"command": "pytest tests/test_webhook.py"}},
                    ],
                },
            },
            {
                "type": "user",
                "sessionId": "sess-claude-001",
                "timestamp": "2026-11-20T10:01:05Z",
                "toolUseResult": {"stdout": "huge output" * 200},
                "message": {
                    "role": "user",
                    "content": [{"type": "tool_result", "content": "AssertionError: backoff jitter missing"}],
                },
            },
        ]
        (proj / "sess-claude-001.jsonl").write_text(
            "\n".join(json.dumps(x) for x in lines) + "\n",
            encoding="utf-8",
        )
        sub_lines = [
            {
                "type": "user",
                "isSidechain": True,
                "sessionId": "sess-claude-001",
                "agentId": "sub-77",
                "timestamp": "2026-11-20T10:00:30Z",
                "message": {"role": "user", "content": "Audit retry DB migration"},
            },
            {
                "type": "assistant",
                "isSidechain": True,
                "sessionId": "sess-claude-001",
                "agentId": "sub-77",
                "timestamp": "2026-11-20T10:00:45Z",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "Migration 004 needs unique index on event_id."},
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "migrations/004_retry.sql"}},
                    ],
                },
            },
        ]
        (sub_dir / "agent-sub-77.jsonl").write_text(
            "\n".join(json.dumps(x) for x in sub_lines) + "\n",
            encoding="utf-8",
        )

        sessions = ts.list_sessions(
            harnesses=["claude"],
            os_name="linux",
            home=self.home,
            env=self.env,
            cwd_filter=self.repo_dir,
        )
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["session_id"], "sess-claude-001")
        self.assertIn("Implement idempotent webhook retry", sessions[0]["title"])

        brief = ts.build_brief(
            harness="claude",
            session_id="sess-claude-001",
            os_name="linux",
            home=self.home,
            env=self.env,
        )
        self.assertIn("Implement idempotent webhook retry", brief["goal"])
        self.assertIn("src/webhook.py", brief["files_touched"])
        self.assertIn("migrations/004_retry.sql", brief["files_touched"])
        self.assertTrue(any("pytest tests/test_webhook.py" in c["command"] for c in brief["commands"]))
        self.assertEqual(len(brief["subagents"]), 1)

    def test_codex_forked_rollout_boilerplate_strip_and_patch_paths(self):
        day_dir = self.home / ".codex" / "sessions" / "2026" / "11" / "21"
        day_dir.mkdir(parents=True)
        uuid = "019a9000-1111-7222-8333-444455556666"
        records = [
            {
                "timestamp": "2026-11-21T08:00:00Z",
                "type": "session_meta",
                "payload": {"id": uuid, "cwd": self.repo_dir, "git": {"branch": "feat/codex"}},
            },
            {
                "timestamp": "2026-11-21T08:00:00Z",
                "type": "session_meta",
                "payload": {"id": "parent-uuid-ignored", "cwd": "/wrong/parent/cwd"},
            },
            {
                "timestamp": "2026-11-21T08:00:01Z",
                "type": "response_item",
                "payload": {
                    "role": "user",
                    "content": [{"type": "input_text", "text": "# AGENTS.md instructions for /work/acme-payments\nDo X"}],
                },
            },
            {
                "timestamp": "2026-11-21T08:00:02Z",
                "type": "response_item",
                "payload": {
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Wire Stripe signature check and add unit tests"}],
                },
            },
            {
                "timestamp": "2026-11-21T08:00:10Z",
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "name": "apply_patch",
                    "input": "*** Begin Patch\n*** Update File: src/stripe_sig.py\n@@\n*** Add File: tests/test_stripe_sig.py\n*** End Patch",
                },
            },
            {
                "timestamp": "2026-11-21T08:00:15Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": json.dumps({"cmd": "pytest tests/test_stripe_sig.py"}),
                    "call_id": "call-1",
                },
            },
            {
                "timestamp": "2026-11-21T08:00:18Z",
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "call-1",
                    "output": "Process exited with code 1\nE   ValueError: timestamp skew",
                },
            },
            {
                "timestamp": "2026-11-21T08:00:20Z",
                "type": "response_item",
                "payload": {
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Hit timestamp tolerance failure; need 300s window."}],
                },
            },
        ]
        rollout_file = day_dir / f"rollout-2026-11-21T08-00-00-{uuid}.jsonl"
        rollout_file.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")

        brief = ts.build_brief(
            harness="codex",
            session_id=uuid[:13],
            os_name="linux",
            home=self.home,
            env=self.env,
        )
        self.assertEqual(brief["cwd"], self.repo_dir)
        self.assertEqual(brief["goal"], "Wire Stripe signature check and add unit tests")
        self.assertIn("src/stripe_sig.py", brief["files_touched"])
        self.assertIn("tests/test_stripe_sig.py", brief["files_touched"])
        self.assertEqual(brief["commands"][0]["exit_code"], 1)

    def test_cursor_ide_sqlite_and_cli_transcript_with_meta_cwd(self):
        # 1) Cursor IDE globalStorage/state.vscdb
        global_dir = self.xdg_config / "Cursor" / "User" / "globalStorage"
        global_dir.mkdir(parents=True)
        db_path = global_dir / "state.vscdb"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE cursorDiskKV (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO ItemTable VALUES ('cursorAuth/accessToken', 'secret-should-never-be-read')"
        )
        cid = "comp-cursor-ide-99"
        composer_val = {
            "composerId": cid,
            "name": "Refactor payment ledger",
            "unifiedMode": "agent",
            "createdAt": 1763700000000,
            "lastUpdatedAt": 1763700060000,
            "fullConversationHeadersOnly": [
                {"bubbleId": "b1", "type": 1},
                {"bubbleId": "b2", "type": 2},
            ],
        }
        b1 = {
            "type": 1,
            "text": "Split ledger posting into atomic SQL transaction",
            "workspaceProjectDir": self.repo_dir,
        }
        b2 = {
            "type": 2,
            "text": "Updated ledger.py; still need rollback test for deadlock.",
            "toolFormerData": {
                "name": "edit_file",
                "params": json.dumps({"target_file": "src/ledger.py"}),
                "status": "completed",
            },
        }
        b_orphan = {"type": 2, "text": "ORPHAN REGENERATED TURN MUST BE IGNORED"}
        conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", (f"composerData:{cid}", json.dumps(composer_val)))
        conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", (f"bubbleId:{cid}:b1", json.dumps(b1)))
        conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", (f"bubbleId:{cid}:b2", json.dumps(b2)))
        conn.execute("INSERT INTO cursorDiskKV VALUES (?, ?)", (f"bubbleId:{cid}:orphan", json.dumps(b_orphan)))
        conn.commit()
        conn.close()

        ide_brief = ts.build_brief(
            harness="cursor",
            session_id="comp-cursor",
            os_name="linux",
            home=self.home,
            env=self.env,
        )
        self.assertEqual(ide_brief["cwd"], self.repo_dir)
        self.assertIn("src/ledger.py", ide_brief["files_touched"])
        rendered = ts.format_brief_markdown(ide_brief)
        self.assertNotIn("ORPHAN REGENERATED", rendered)
        self.assertNotIn("secret-should-never-be-read", rendered)

        # 2) Cursor CLI agent-transcripts + chats/<md5>/<uuid>/meta.json
        cli_id = "cli-chat-4242"
        md5_dir = hashlib.md5(self.repo_dir.encode("utf-8")).hexdigest()
        meta_dir = self.home / ".cursor" / "chats" / md5_dir / cli_id
        meta_dir.mkdir(parents=True)
        (meta_dir / "meta.json").write_text(json.dumps({"cwd": self.repo_dir}), encoding="utf-8")

        trans_dir = self.home / ".cursor" / "projects" / "work-acme-payments" / "agent-transcripts" / cli_id
        trans_dir.mkdir(parents=True)
        cli_lines = [
            {
                "role": "user",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "<timestamp>Wednesday, Nov 25, 2026</timestamp>\n<user_query>Fix currency rounding in invoice.py</user_query>",
                        }
                    ]
                },
            },
            {
                "role": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "Patched Decimal quantize; rate limit hit before running tests."},
                        {"type": "tool_use", "name": "StrReplace", "input": {"path": "src/invoice.py"}},
                    ]
                },
            },
        ]
        (trans_dir / f"{cli_id}.jsonl").write_text(
            "\n".join(json.dumps(x) for x in cli_lines) + "\n",
            encoding="utf-8",
        )
        cli_brief = ts.build_brief(
            harness="cursor",
            session_id=cli_id,
            os_name="linux",
            home=self.home,
            env=self.env,
        )
        self.assertEqual(cli_brief["cwd"], self.repo_dir)
        self.assertEqual(cli_brief["goal"], "Fix currency rounding in invoice.py")
        self.assertIn("src/invoice.py", cli_brief["files_touched"])

    def test_windsurf_encrypted_cascade_pb(self):
        cascade_dir = self.home / ".codeium" / "windsurf" / "cascade"
        cascade_dir.mkdir(parents=True)
        cid = "cascade-ws-777"

        ws_meta = _pb_field_str(1, f"file://{self.repo_dir}") + _pb_field_str(2, f"file://{self.repo_dir}")
        traj_meta = _pb_field_bytes(1, ws_meta)
        step1 = _pb_field_bytes(19, _pb_field_str(2, "Migrate Redis lock to Redlock algorithm"))
        step2 = _pb_field_bytes(
            20,
            _pb_field_str(1, "Implemented acquire_lock in src/lock.py; release Lua script still pending."),
        )
        traj = (
            _pb_field_str(1, "traj-777")
            + _pb_field_bytes(2, step1)
            + _pb_field_bytes(2, step2)
            + _pb_field_str(6, cid)
            + _pb_field_bytes(7, traj_meta)
            + _pb_field_str(10, "Redlock migration")
        )
        nonce = b"123456789012"
        sealed = nonce + ts._aes256_gcm_encrypt_pure(ts.WINDSURF_AES_KEY, nonce, traj)
        (cascade_dir / f"{cid}.pb").write_bytes(sealed)

        brief = ts.build_brief(
            harness="windsurf",
            session_id="cascade-ws",
            os_name="linux",
            home=self.home,
            env=self.env,
        )
        self.assertEqual(brief["cwd"], self.repo_dir)
        self.assertEqual(brief["title"], "Redlock migration")
        self.assertEqual(brief["goal"], "Migrate Redis lock to Redlock algorithm")
        self.assertIn("Lua script still pending", brief["recent_turns"][-1]["text"])

    def test_copilot_cli_and_vscode_delta_jsonl(self):
        # 1) Copilot CLI
        cdir = self.home / ".copilot" / "session-state" / "dir-1"
        cdir.mkdir(parents=True)
        cli_events = [
            {
                "type": "session.start",
                "timestamp": "2026-11-22T09:00:00Z",
                "data": {"sessionId": "cop-cli-101", "context": {"cwd": self.repo_dir}},
            },
            {
                "type": "user.message",
                "timestamp": "2026-11-22T09:00:01Z",
                "data": {"content": "Add healthz endpoint to FastAPI app"},
            },
            {
                "type": "tool.execution_start",
                "timestamp": "2026-11-22T09:00:05Z",
                "data": {"toolName": "edit", "arguments": {"path": "src/api.py"}},
            },
            {
                "type": "assistant.message",
                "timestamp": "2026-11-22T09:00:10Z",
                "data": {"content": "Added /healthz; readiness DB ping still TODO."},
            },
        ]
        (cdir / "events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in cli_events) + "\n",
            encoding="utf-8",
        )
        b_cli = ts.build_brief("copilot", "cop-cli-101", os_name="linux", home=self.home, env=self.env)
        self.assertEqual(b_cli["cwd"], self.repo_dir)
        self.assertIn("src/api.py", b_cli["files_touched"])

        # 2) VS Code Copilot Chat mutation log (kind 0/1/2)
        ws_dir = self.appdata / "Code" / "User" / "workspaceStorage" / "hashabc"
        chat_dir = ws_dir / "chatSessions"
        chat_dir.mkdir(parents=True)
        (ws_dir / "workspace.json").write_text(
            json.dumps({"folder": "file:///c%3A/work/acme-payments"}),
            encoding="utf-8",
        )
        deltas = [
            {
                "kind": 0,
                "v": {
                    "sessionId": "vsc-chat-202",
                    "customTitle": "OAuth PKCE callback",
                    "creationDate": 1763800000000,
                    "requests": [],
                },
            },
            {
                "kind": 2,
                "k": ["requests"],
                "v": [
                    {
                        "message": {"text": "Implement OAuth PKCE callback verifier"},
                        "response": [
                            {"value": "Created verifier helper; token exchange route next."},
                            {"uri": {"fsPath": "C:/work/acme-payments/src/pkce.ts"}, "edits": [[{"text": "x"}]]},
                        ],
                    }
                ],
            },
        ]
        (chat_dir / "vsc-chat-202.jsonl").write_text(
            "\n".join(json.dumps(d) for d in deltas) + "\n",
            encoding="utf-8",
        )
        b_vsc = ts.build_brief("copilot", "vsc-chat-202", os_name="windows", home=self.home, env=self.env)
        self.assertEqual(b_vsc["cwd"], "C:/work/acme-payments")
        self.assertEqual(b_vsc["goal"], "Implement OAuth PKCE callback verifier")
        self.assertTrue(any("pkce.ts" in f for f in b_vsc["files_touched"]))

    def test_kiro_streaming_cli_and_ide_base64_sessions(self):
        # 1) Kiro CLI streaming chunks with same message_id
        kcli = self.home / ".kiro" / "sessions" / "cli"
        kcli.mkdir(parents=True)
        (kcli / "kiro-cli-1.json").write_text(
            json.dumps({"sessionId": "kiro-cli-1", "cwd": self.repo_dir}),
            encoding="utf-8",
        )
        klines = [
            {
                "kind": "Prompt",
                "data": {"content": [{"data": "Add DynamoDB TTL attribute"}], "meta": {"timestamp": 1763810000}},
            },
            {
                "kind": "AssistantMessage",
                "data": {"message_id": "m-1", "content": [{"data": "Added expires_at "}]},
            },
            {
                "kind": "AssistantMessage",
                "data": {"message_id": "m-1", "content": [{"data": "to table CDK construct; deploy check left."}]},
            },
        ]
        (kcli / "kiro-cli-1.jsonl").write_text(
            "\n".join(json.dumps(x) for x in klines) + "\n",
            encoding="utf-8",
        )
        b1 = ts.build_brief("kiro", "kiro-cli-1", os_name="linux", home=self.home, env=self.env)
        self.assertEqual(
            b1["recent_turns"][-1]["text"],
            "Added expires_at to table CDK construct; deploy check left.",
        )

        # 2) Kiro IDE workspace-sessions with '__' padding
        b64_ws = base64.urlsafe_b64encode(self.repo_dir.encode("utf-8")).decode("ascii").replace("=", "_")
        kide = (
            self.xdg_config
            / "Kiro"
            / "User"
            / "globalStorage"
            / "kiro.kiroagent"
            / "workspace-sessions"
            / b64_ws
        )
        kide.mkdir(parents=True)
        (kide / "sessions.json").write_text(
            json.dumps([{"sessionId": "kiro-ide-2", "dateCreated": "2026-11-23T12:00:00Z"}]),
            encoding="utf-8",
        )
        (kide / "kiro-ide-2.json").write_text(
            json.dumps(
                {
                    "sessionId": "kiro-ide-2",
                    "title": "S3 presigned upload",
                    "history": [
                        {"message": {"role": "user", "content": [{"type": "text", "text": "Build S3 presigned URL signer"}]}},
                        {"message": {"role": "assistant", "content": "Signer added; CORS policy update pending."}},
                    ],
                }
            ),
            encoding="utf-8",
        )
        b2 = ts.build_brief("kiro", "kiro-ide-2", os_name="linux", home=self.home, env=self.env)
        self.assertEqual(b2["cwd"], self.repo_dir)
        self.assertEqual(b2["goal"], "Build S3 presigned URL signer")

    def test_opencode_v1_and_v2_coexisting_sqlite(self):
        oc_dir = self.xdg_data / "opencode"
        diff_dir = oc_dir / "storage" / "session_diff"
        diff_dir.mkdir(parents=True)
        db = oc_dir / "opencode.db"
        conn = sqlite3.connect(db)
        conn.executescript(
            """
            CREATE TABLE session (id TEXT PRIMARY KEY, directory TEXT, title TEXT, time_created INTEGER, time_updated INTEGER);
            CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER, data TEXT);
            CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, time_created INTEGER, data TEXT);
            CREATE TABLE session_v2 (id TEXT PRIMARY KEY, directory TEXT, title TEXT, time_created INTEGER, time_updated INTEGER);
            CREATE TABLE session_message (id TEXT PRIMARY KEY, session_id TEXT, type TEXT, seq INTEGER, time_created INTEGER, data TEXT);
            """
        )
        # v2 session
        conn.execute(
            "INSERT INTO session_v2 VALUES ('ses_v2', ?, 'OpenCode v2 task', 1763900000000, 1763900050000)",
            (self.repo_dir,),
        )
        conn.execute(
            "INSERT INTO session_message VALUES ('m1', 'ses_v2', 'user', 1, 1763900001000, ?)",
            (json.dumps({"time": {"created": 1763900001000}, "text": "Fix Go race condition in worker pool"}),),
        )
        conn.execute(
            "INSERT INTO session_message VALUES ('m2', 'ses_v2', 'assistant', 2, 1763900010000, ?)",
            (
                json.dumps(
                    {
                        "time": {"created": 1763900010000},
                        "content": [
                            {
                                "type": "tool",
                                "name": "edit",
                                "state": {"status": "completed", "input": {"path": "pool.go"}},
                            },
                            {
                                "type": "tool",
                                "name": "shell",
                                "state": {
                                    "status": "completed",
                                    "input": {"command": "go test -race ./..."},
                                    "metadata": {"exit": 1},
                                },
                            },
                            {"type": "text", "text": "Mutex added; channel close still races on shutdown."},
                        ],
                    }
                ),
            ),
        )
        # v1 legacy session with external session_diff
        conn.execute(
            "INSERT INTO session VALUES ('ses_v1', ?, 'OpenCode v1 task', 1763800000000, 1763800050000)",
            (self.repo_dir,),
        )
        conn.execute(
            "INSERT INTO message VALUES ('mv1', 'ses_v1', 1999999999000, ?)",
            (json.dumps({"role": "user", "time": {"created": 1763800001000}}),),
        )
        conn.execute(
            "INSERT INTO part VALUES ('pv1', 'mv1', 'ses_v1', 1999999999000, ?)",
            (json.dumps({"type": "text", "text": "Legacy v1 prompt"}),),
        )
        conn.commit()
        conn.close()
        (diff_dir / "ses_v1.json").write_text(
            json.dumps([{"file": "legacy.go", "status": "modified"}]),
            encoding="utf-8",
        )

        b_v2 = ts.build_brief("opencode", "ses_v2", os_name="linux", home=self.home, env=self.env)
        self.assertIn("pool.go", b_v2["files_touched"])
        self.assertEqual(b_v2["commands"][0]["exit_code"], 1)

        b_v1 = ts.build_brief("opencode", "ses_v1", os_name="linux", home=self.home, env=self.env)
        self.assertEqual(b_v1["goal"], "Legacy v1 prompt")
        self.assertIn("legacy.go", b_v1["files_touched"])

    def test_zed_threads_sqlite_json_and_zstd(self):
        zed_dir = self.xdg_data / "zed" / "threads"
        zed_dir.mkdir(parents=True)
        db = zed_dir / "threads.db"
        conn = sqlite3.connect(db)
        conn.execute(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                data_type TEXT NOT NULL,
                data BLOB NOT NULL,
                parent_id TEXT,
                folder_paths TEXT
            )
            """
        )
        doc = {
            "version": "0.3.0",
            "title": "Zed Rust parser",
            "updated_at": "2026-11-24T15:00:00+00:00",
            "messages": [
                {"User": {"id": "u1", "content": [{"Text": "Parse RFC3339 timestamps in crate"}]}},
                {
                    "Agent": {
                        "content": [
                            {"Text": "Updated parser.rs; timezone offset test failing."},
                            {"ToolUse": {"id": "tu1", "name": "terminal", "input": {"command": "cargo test"}}},
                        ],
                        "tool_results": {
                            "tu2": {"output": {"input_path": "src/parser.rs", "diff": "@@ -1 +1 @@"}}
                        },
                    }
                },
                "Resume",
            ],
        }
        raw_bytes = json.dumps(doc).encode("utf-8")
        data_type = "json"
        blob = raw_bytes
        compressed = ts._compress_zstd_for_test(raw_bytes)
        if compressed is not None:
            data_type = "zstd"
            blob = compressed

        conn.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?, ?, NULL, ?)",
            ("zed-thread-1", "Zed Rust parser", "2026-11-24T15:00:00+00:00", data_type, blob, self.repo_dir),
        )
        conn.commit()
        conn.close()

        brief = ts.build_brief("zed", "zed-thread-1", os_name="linux", home=self.home, env=self.env)
        self.assertEqual(brief["cwd"], self.repo_dir)
        self.assertEqual(brief["goal"], "Parse RFC3339 timestamps in crate")
        self.assertIn("src/parser.rs", brief["files_touched"])
        self.assertTrue(any("cargo test" in c["command"] for c in brief["commands"]))

    def test_devin_cli_linked_nodes_and_dedup(self):
        devin_dir = self.xdg_data / "devin" / "cli"
        devin_dir.mkdir(parents=True)
        db = devin_dir / "sessions.db"
        conn = sqlite3.connect(db)
        conn.executescript(
            """
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                working_directory TEXT,
                main_chain_id TEXT,
                created_at INTEGER,
                updated_at INTEGER,
                hidden INTEGER DEFAULT 0
            );
            CREATE TABLE message_nodes (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                parent_node_id TEXT,
                message_id TEXT,
                created_at INTEGER,
                chat_message TEXT,
                metadata TEXT
            );
            """
        )
        conn.execute(
            "INSERT INTO sessions VALUES ('devin-sess-1', 'Auth middleware', ?, 'n4', 1763950000, 1763950100, 0)",
            (self.repo_dir,),
        )
        conn.execute(
            "INSERT INTO sessions VALUES ('devin-hidden', 'Hidden', ?, 'h1', 1763950000, 1763950200, 1)",
            (self.repo_dir,),
        )
        nodes = [
            (
                "n1",
                "devin-sess-1",
                None,
                "sys-1",
                1763950000,
                json.dumps({"role": "system", "content": "system prompt"}),
                json.dumps({"is_system_prefix": True}),
            ),
            (
                "n2",
                "devin-sess-1",
                "n1",
                "msg-u1",
                1763950001,
                json.dumps({"role": "user", "content": "Add JWT expiry check in middleware.py"}),
                "{}",
            ),
            # Rebuilt duplicate of msg-u1 after prefix update: must be deduped!
            (
                "n3",
                "devin-sess-1",
                "n2",
                "msg-u1",
                1763950050,
                json.dumps({"role": "user", "content": "Add JWT expiry check in middleware.py"}),
                "{}",
            ),
            (
                "n4",
                "devin-sess-1",
                "n3",
                "msg-a1",
                1763950060,
                json.dumps(
                    {
                        "role": "assistant",
                        "content": "Edited middleware.py; refresh-token rotation still open.",
                        "tool_calls": [
                            {"id": "tc1", "name": "edit", "arguments": json.dumps({"file_path": "src/middleware.py"})},
                            {"id": "tc2", "name": "exec", "arguments": json.dumps({"command": "pytest -k jwt"})},
                        ],
                    }
                ),
                "{}",
            ),
        ]
        conn.executemany("INSERT INTO message_nodes VALUES (?, ?, ?, ?, ?, ?, ?)", nodes)
        conn.commit()
        conn.close()

        listed = ts.list_sessions(
            harnesses=["devin"],
            os_name="linux",
            home=self.home,
            env=self.env,
        )
        self.assertEqual([s["session_id"] for s in listed], ["devin-sess-1"])

        brief = ts.build_brief("devin", "devin-sess-1", os_name="linux", home=self.home, env=self.env)
        user_turns = [t for t in brief["recent_turns"] if t["role"] == "user"]
        self.assertEqual(len(user_turns), 1)
        self.assertIn("src/middleware.py", brief["files_touched"])

    def test_wsl_bridge_and_exclusion_filters(self):
        win_home = Path(self._tmp.name) / "mnt_c_users_alice"
        cdir = win_home / ".copilot" / "session-state" / "wsl-cross-1"
        cdir.mkdir(parents=True)
        events = [
            {
                "type": "session.start",
                "timestamp": "2026-11-25T01:00:00Z",
                "data": {"sessionId": "win-cop-999", "context": {"cwd": r"C:\work\acme-payments"}},
            },
            {
                "type": "user.message",
                "timestamp": "2026-11-25T01:00:02Z",
                "data": {"content": "Finish Windows-side gRPC client stub"},
            },
        ]
        (cdir / "events.jsonl").write_text("\n".join(json.dumps(x) for x in events) + "\n", encoding="utf-8")

        wsl_env = dict(self.env, WSL_WIN_HOME=str(win_home))
        rows = ts.list_sessions(
            harnesses="all",
            os_name="linux",
            home=self.home,
            env=wsl_env,
            cwd_filter="/mnt/c/work/acme-payments",
        )
        self.assertEqual([r["session_id"] for r in rows], ["win-cop-999"])

        excluded = ts.list_sessions(
            harnesses="all",
            os_name="linux",
            home=self.home,
            env=wsl_env,
            exclude_sessions=["win-cop"],
        )
        self.assertEqual(excluded, [])

    def test_cli_entrypoints_and_selftest(self):
        script = SCRIPTS_DIR / "takeover_session.py"
        proc = subprocess.run(
            [sys.executable, str(script), "selftest"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
