#!/usr/bin/env python3
"""Read-only cross-agent session discovery, search, and Takeover Brief extractor.

Supports 8 major coding agent suites plus Devin CLI across macOS, Linux, and Windows:
  - claude    (Claude Code JSONL transcripts + subagent sidechains)
  - codex     (OpenAI Codex CLI/Desktop JSONL + .jsonl.zst rollouts + state_5.sqlite)
  - cursor    (Cursor IDE state.vscdb cursorDiskKV/composerHeaders + CLI agent-transcripts & chats meta.json)
  - windsurf  (Windsurf / Devin Desktop AES-256-GCM CortexTrajectory .pb + hook transcripts)
  - copilot   (GitHub Copilot CLI events.jsonl + VS Code Copilot Chat delta JSONL & transcripts)
  - kiro      (Kiro CLI streaming JSONL, V3/IDE sess_* JSONL, IDE kiro.kiroagent base64 JSON, headless SQLite)
  - opencode  (OpenCode 1.x & 2.x opencode.db SQLite + storage/session_diff/*.json)
  - zed       (Zed threads/threads.db zstd/json SQLite + conversations/*.zed.json)
  - devin     (Devin CLI sessions.db main_chain_id linked message_nodes)

Strictly read-only: opens SQLite via `file:...?mode=ro` (falling back to a temporary snapshot if locked),
never touches credential/auth rows, never mutates workspace or session files, and redacts common secrets.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Iterable

ALL_HARNESSES = (
    "claude",
    "codex",
    "cursor",
    "windsurf",
    "copilot",
    "kiro",
    "opencode",
    "zed",
    "devin",
)

HARNESS_ALIASES = {
    "claude-code": "claude",
    "codex-cli": "codex",
    "cursor-ide": "cursor",
    "cursor-cli": "cursor",
    "windsurf-cascade": "windsurf",
    "devin-desktop": "windsurf",
    "github-copilot": "copilot",
    "copilot-cli": "copilot",
    "copilot-chat": "copilot",
    "vscode-copilot": "copilot",
    "kiro-cli": "kiro",
    "kiro-ide": "kiro",
    "devin-cli": "devin",
}

WINDSURF_AES_KEY = b"safeCodeiumworldKeYsecretBalloon"

SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    re.compile(r"(?i)(Authorization\s*:\s*Bearer\s+)[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(
        r"(?i)\b((?:OPENAI|ANTHROPIC|DEVIN|CURSOR|WINDSURF|GITHUB|AWS|GEMINI|API|ACCESS|SECRET)[A-Z0-9_]*(?:KEY|TOKEN|SECRET)\s*=\s*)([^\s\"']+)"
    ),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----"),
]

TAG_WRAPPER_RE = re.compile(
    r"<(?:system-reminder|local-command-caveat|local-command-stdout|command-name|command-message|command-args|user_info|timestamp)>[\s\S]*?</(?:system-reminder|local-command-caveat|local-command-stdout|command-name|command-message|command-args|user_info|timestamp)>",
    re.IGNORECASE,
)
USER_QUERY_RE = re.compile(r"<user_query>([\s\S]*?)</user_query>", re.IGNORECASE)
CODEX_BOILERPLATE_RE = re.compile(
    r"^\s*(?:<([a-z][\w-]*)[\s>][\s\S]*</\1>\s*$|#\s*AGENTS\.md instructions)",
    re.IGNORECASE,
)
PATCH_HEADER_RE = re.compile(r"^\*\*\*\s+(?:Add|Update|Delete)\s+File:\s+(.+?)\s*$", re.MULTILINE)
EXIT_CODE_RE = re.compile(r"(?:exit(?:ed)?(?:\s+with)?\s+code|exit_code|status)[:=\s]+(-?\d+)", re.IGNORECASE)


def redact_secrets(text: str) -> str:
    if not text:
        return ""
    out = text
    for pat in SECRET_PATTERNS:
        if pat.groups >= 1:
            out = pat.sub(r"\1<REDACTED>", out)
        else:
            out = pat.sub("<REDACTED>", out)
    return out


def clean_prompt_text(text: str) -> str:
    if not text:
        return ""
    m = USER_QUERY_RE.search(text)
    if m:
        text = m.group(1)
    text = TAG_WRAPPER_RE.sub(" ", text)
    return redact_secrets(text).strip()


def one_line(text: str, limit: int = 120) -> str:
    flat = re.sub(r"\s+", " ", clean_prompt_text(text)).strip()
    if len(flat) <= limit:
        return flat
    return flat[: max(0, limit - 1)] + "…"


def normalize_os_name(os_name: str = "auto") -> str:
    if os_name and os_name != "auto":
        low = os_name.lower()
        if low in ("darwin", "mac", "macos", "osx"):
            return "macos"
        if low in ("win", "win32", "windows"):
            return "windows"
        return "linux"
    sys_name = platform.system().lower()
    if sys_name == "darwin":
        return "macos"
    if sys_name == "windows":
        return "windows"
    return "linux"


def normalize_harness_list(raw: Iterable[str] | str) -> list[str]:
    if isinstance(raw, str):
        items = [x.strip().lower() for x in raw.split(",") if x.strip()]
    else:
        items = [str(x).strip().lower() for x in raw if str(x).strip()]
    if not items or "all" in items:
        return list(ALL_HARNESSES)
    resolved: list[str] = []
    for item in items:
        canon = HARNESS_ALIASES.get(item, item)
        if canon not in ALL_HARNESSES:
            raise ValueError(f"Unsupported harness '{item}'. Expected one of: {', '.join(ALL_HARNESSES)}, all")
        if canon not in resolved:
            resolved.append(canon)
    return resolved


def decode_file_uri(uri: str) -> str:
    if not uri:
        return ""
    if not uri.startswith("file://"):
        return uri
    parsed = urllib.parse.urlparse(uri)
    raw_path = urllib.parse.unquote(parsed.path or "")
    if parsed.netloc and parsed.netloc != "localhost":
        return f"//{parsed.netloc}{raw_path}"
    if re.match(r"^/[A-Za-z]:/", raw_path):
        return raw_path[1].upper() + raw_path[2:]
    return raw_path


def normalize_path_for_match(p: str | None) -> str:
    if not p:
        return ""
    s = decode_file_uri(str(p)).replace("\\", "/").rstrip("/")
    m_wsl = re.match(r"^/mnt/([a-zA-Z])(/.*)?$", s)
    if m_wsl:
        s = f"{m_wsl.group(1).lower()}:{m_wsl.group(2) or ''}"
    return s.lower() if re.match(r"^[a-zA-Z]:(/|$)", s) else s


def cwd_matches(session_cwd: str | None, cwd_filter: str | None) -> bool:
    if not cwd_filter:
        return True
    if not session_cwd:
        return False
    sc = normalize_path_for_match(session_cwd)
    fc = normalize_path_for_match(cwd_filter)
    if not sc or not fc:
        return False
    return sc == fc or sc.startswith(fc + "/") or fc.startswith(sc + "/")


def ts_to_iso(value: Any, fallback_epoch: float | None = None) -> tuple[str, float]:
    if isinstance(value, (int, float)) and value > 0:
        sec = float(value) / 1000.0 if value > 1e11 else float(value)
        iso = dt.datetime.fromtimestamp(sec, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return iso, sec
    if isinstance(value, str) and value.strip():
        s = value.strip()
        if s.isdigit():
            return ts_to_iso(int(s), fallback_epoch)
        try:
            norm = s[:-1] + "+00:00" if s.endswith("Z") else s
            parsed = dt.datetime.fromisoformat(norm)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            sec = parsed.timestamp()
            return parsed.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), sec
        except ValueError:
            pass
    if fallback_epoch and fallback_epoch > 0:
        iso = dt.datetime.fromtimestamp(fallback_epoch, tz=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return iso, fallback_epoch
    return "", 0.0


def extract_patch_paths(patch_text: str) -> list[str]:
    if not patch_text:
        return []
    return [m.group(1).strip() for m in PATCH_HEADER_RE.finditer(patch_text) if m.group(1).strip()]


# ---------------------------------------------------------------------------
# Pure-Python NIST AES-256-GCM + Protobuf Wire Decoder (zero external deps)
# ---------------------------------------------------------------------------


def _build_aes_sbox() -> bytes:
    def rotl8(x: int, shift: int) -> int:
        return ((x << shift) | (x >> (8 - shift))) & 0xFF

    p = 1
    q = 1
    sbox = [0] * 256
    while True:
        p = p ^ ((p << 1) & 0xFF) ^ (0x1B if (p & 0x80) else 0)
        q ^= (q << 1) & 0xFF
        q ^= (q << 2) & 0xFF
        q ^= (q << 4) & 0xFF
        q ^= 0x09 if (q & 0x80) else 0
        xformed = q ^ rotl8(q, 1) ^ rotl8(q, 2) ^ rotl8(q, 3) ^ rotl8(q, 4) ^ 0x63
        sbox[p] = xformed
        if p == 1:
            break
    sbox[0] = 0x63
    return bytes(sbox)


_AES_SBOX = _build_aes_sbox()
_AES_RCON = (0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36)


def _aes256_expand_key(key: bytes) -> list[bytes]:
    if len(key) != 32:
        raise ValueError("AES-256 requires a 32-byte key")
    sbox = _AES_SBOX
    w = [int.from_bytes(key[i : i + 4], "big") for i in range(0, 32, 4)]

    def sub_word(word: int) -> int:
        return (
            (sbox[(word >> 24) & 0xFF] << 24)
            | (sbox[(word >> 16) & 0xFF] << 16)
            | (sbox[(word >> 8) & 0xFF] << 8)
            | sbox[word & 0xFF]
        )

    for i in range(8, 60):
        temp = w[i - 1]
        if i % 8 == 0:
            rot = ((temp << 8) & 0xFFFFFFFF) | (temp >> 24)
            temp = sub_word(rot) ^ (_AES_RCON[i // 8] << 24)
        elif i % 8 == 4:
            temp = sub_word(temp)
        w.append(w[i - 8] ^ temp)

    round_keys: list[bytes] = []
    for r in range(15):
        rk = b"".join(w[4 * r + j].to_bytes(4, "big") for j in range(4))
        round_keys.append(rk)
    return round_keys


def _aes_encrypt_block(block: bytes, round_keys: list[bytes]) -> bytes:
    sbox = _AES_SBOX
    s = [block[i] ^ round_keys[0][i] for i in range(16)]

    for rnd in range(1, 14):
        s = [sbox[b] for b in s]
        s = [
            s[0], s[5], s[10], s[15],
            s[4], s[9], s[14], s[3],
            s[8], s[13], s[2], s[7],
            s[12], s[1], s[6], s[11],
        ]
        rk = round_keys[rnd]
        ns = [0] * 16
        for c in range(4):
            idx = 4 * c
            a0, a1, a2, a3 = s[idx], s[idx + 1], s[idx + 2], s[idx + 3]
            t = a0 ^ a1 ^ a2 ^ a3
            u0 = a0 ^ a1
            u0 = ((u0 << 1) & 0xFF) ^ (0x1B if (u0 & 0x80) else 0)
            u1 = a1 ^ a2
            u1 = ((u1 << 1) & 0xFF) ^ (0x1B if (u1 & 0x80) else 0)
            u2 = a2 ^ a3
            u2 = ((u2 << 1) & 0xFF) ^ (0x1B if (u2 & 0x80) else 0)
            u3 = a3 ^ a0
            u3 = ((u3 << 1) & 0xFF) ^ (0x1B if (u3 & 0x80) else 0)
            ns[idx] = a0 ^ t ^ u0 ^ rk[idx]
            ns[idx + 1] = a1 ^ t ^ u1 ^ rk[idx + 1]
            ns[idx + 2] = a2 ^ t ^ u2 ^ rk[idx + 2]
            ns[idx + 3] = a3 ^ t ^ u3 ^ rk[idx + 3]
        s = ns

    s = [sbox[b] for b in s]
    s = [
        s[0], s[5], s[10], s[15],
        s[4], s[9], s[14], s[3],
        s[8], s[13], s[2], s[7],
        s[12], s[1], s[6], s[11],
    ]
    rk14 = round_keys[14]
    return bytes(s[i] ^ rk14[i] for i in range(16))


def _gf128_mul(x: int, y: int) -> int:
    z = 0
    v = y
    for i in range(128):
        if (x >> (127 - i)) & 1:
            z ^= v
        if v & 1:
            v = (v >> 1) ^ 0xE1000000000000000000000000000000
        else:
            v >>= 1
    return z


def _ghash(h_int: int, ciphertext: bytes) -> bytes:
    rem = len(ciphertext) % 16
    padded = ciphertext + (b"\x00" * ((16 - rem) % 16))
    len_block = (0).to_bytes(8, "big") + (len(ciphertext) * 8).to_bytes(8, "big")
    data = padded + len_block
    y = 0
    for i in range(0, len(data), 16):
        blk = int.from_bytes(data[i : i + 16], "big")
        y = _gf128_mul(y ^ blk, h_int)
    return y.to_bytes(16, "big")


def _aes256_gctr(round_keys: list[bytes], icb: bytes, data: bytes) -> bytes:
    if not data:
        return b""
    out = bytearray(len(data))
    prefix = icb[:12]
    ctr = int.from_bytes(icb[12:], "big")
    for offset in range(0, len(data), 16):
        cb = prefix + (ctr & 0xFFFFFFFF).to_bytes(4, "big")
        ks = _aes_encrypt_block(cb, round_keys)
        chunk = data[offset : offset + 16]
        for j, b in enumerate(chunk):
            out[offset + j] = b ^ ks[j]
        ctr = (ctr + 1) & 0xFFFFFFFF
    return bytes(out)


def _aes256_gcm_encrypt_pure(key: bytes, nonce: bytes, plaintext: bytes) -> bytes:
    if len(nonce) != 12:
        raise ValueError("GCM nonce must be 12 bytes")
    rks = _aes256_expand_key(key)
    h_int = int.from_bytes(_aes_encrypt_block(b"\x00" * 16, rks), "big")
    j0 = nonce + b"\x00\x00\x00\x01"
    icb = nonce + b"\x00\x00\x00\x02"
    ct = _aes256_gctr(rks, icb, plaintext)
    s_block = _ghash(h_int, ct)
    ej0 = _aes_encrypt_block(j0, rks)
    tag = bytes(a ^ b for a, b in zip(ej0, s_block))
    return ct + tag


def _aes256_gcm_decrypt_pure(key: bytes, nonce: bytes, ciphertext_and_tag: bytes) -> bytes:
    if len(nonce) != 12 or len(ciphertext_and_tag) < 16:
        raise ValueError("Invalid AES-GCM envelope")
    ct = ciphertext_and_tag[:-16]
    given_tag = ciphertext_and_tag[-16:]
    rks = _aes256_expand_key(key)
    h_int = int.from_bytes(_aes_encrypt_block(b"\x00" * 16, rks), "big")
    j0 = nonce + b"\x00\x00\x00\x01"
    s_block = _ghash(h_int, ct)
    ej0 = _aes_encrypt_block(j0, rks)
    expected_tag = bytes(a ^ b for a, b in zip(ej0, s_block))
    if not hmac.compare_digest(expected_tag, given_tag):
        raise ValueError("AES-GCM authentication failed")
    icb = nonce + b"\x00\x00\x00\x02"
    return _aes256_gctr(rks, icb, ct)


def decrypt_aes256_gcm(key: bytes, sealed_blob: bytes) -> bytes:
    if len(sealed_blob) < 28:
        raise ValueError("Sealed blob shorter than nonce(12)+tag(16)")
    nonce = sealed_blob[:12]
    ct_and_tag = sealed_blob[12:]
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore

        return AESGCM(key).decrypt(nonce, ct_and_tag, None)
    except ImportError:
        return _aes256_gcm_decrypt_pure(key, nonce, ct_and_tag)
    except Exception as exc:
        raise ValueError(f"AES-GCM authentication failed: {exc}") from exc


def _pb_read_varint(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while pos < len(buf):
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 70:
            raise ValueError("Varint overflow")
    raise ValueError("Truncated varint")


def pb_iter_fields(buf: bytes) -> Iterable[tuple[int, int, int | bytes]]:
    pos = 0
    n = len(buf)
    while pos < n:
        tag, pos = _pb_read_varint(buf, pos)
        field_no = tag >> 3
        wire_type = tag & 0x07
        if field_no == 0:
            raise ValueError("Invalid protobuf field 0")
        if wire_type == 0:
            val, pos = _pb_read_varint(buf, pos)
            yield field_no, wire_type, val
        elif wire_type == 1:
            if pos + 8 > n:
                raise ValueError("Truncated fixed64")
            yield field_no, wire_type, buf[pos : pos + 8]
            pos += 8
        elif wire_type == 2:
            length, pos = _pb_read_varint(buf, pos)
            if pos + length > n:
                raise ValueError("Truncated length-delimited field")
            yield field_no, wire_type, buf[pos : pos + length]
            pos += length
        elif wire_type == 5:
            if pos + 4 > n:
                raise ValueError("Truncated fixed32")
            yield field_no, wire_type, buf[pos : pos + 4]
            pos += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire_type}")


def _pb_decode_utf8(raw: int | bytes) -> str:
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return ""


def _pb_decode_timestamp(raw: bytes) -> float:
    sec = 0
    nanos = 0
    for fno, wtype, val in pb_iter_fields(raw):
        if fno == 1 and wtype == 0 and isinstance(val, int):
            sec = val
        elif fno == 2 and wtype == 0 and isinstance(val, int):
            nanos = val
    return float(sec) + float(nanos) / 1e9 if sec > 0 else 0.0


# ---------------------------------------------------------------------------
# Zstd + Read-Only SQLite + JSONL Helpers
# ---------------------------------------------------------------------------


def decompress_zstd_bytes(data: bytes) -> tuple[bytes | None, str | None]:
    try:
        from compression import zstd as stdlib_zstd  # type: ignore

        return stdlib_zstd.decompress(data), None
    except Exception:
        pass
    try:
        import zstandard  # type: ignore

        dctx = zstandard.ZstdDecompressor()
        return dctx.decompress(data), None
    except Exception:
        pass
    zstd_bin = shutil.which("zstd")
    if zstd_bin:
        proc = subprocess.run(
            [zstd_bin, "-dc"],
            input=data,
            capture_output=True,
            check=False,
            timeout=15,
        )
        if proc.returncode == 0:
            return proc.stdout, None
        return None, f"zstd CLI failed with exit {proc.returncode}"
    return None, "zstd support unavailable (install zstd CLI, Python zstandard, or use Python 3.14+)"


def _compress_zstd_for_test(data: bytes) -> bytes | None:
    try:
        from compression import zstd as stdlib_zstd  # type: ignore

        return stdlib_zstd.compress(data)
    except Exception:
        pass
    try:
        import zstandard  # type: ignore

        return zstandard.ZstdCompressor().compress(data)
    except Exception:
        pass
    zstd_bin = shutil.which("zstd")
    if zstd_bin:
        proc = subprocess.run([zstd_bin, "-c"], input=data, capture_output=True, check=False)
        if proc.returncode == 0:
            return proc.stdout
    return None


class ReadOnlySqlite:
    """Context manager opening SQLite strictly read-only, with temp-snapshot fallback on lock."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._tmpdir: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> sqlite3.Connection:
        if not self.db_path.is_file():
            raise FileNotFoundError(str(self.db_path))
        uri = self._to_ro_uri(self.db_path)
        try:
            conn = sqlite3.connect(uri, uri=True, timeout=2.0)
            conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchall()
            self._conn = conn
            return conn
        except sqlite3.OperationalError:
            self._tmpdir = tempfile.TemporaryDirectory()
            tmp_root = Path(self._tmpdir.name)
            snap = tmp_root / self.db_path.name
            shutil.copy2(self.db_path, snap)
            for suffix in ("-wal", "-shm"):
                side = Path(str(self.db_path) + suffix)
                if side.is_file():
                    shutil.copy2(side, Path(str(snap) + suffix))
            conn = sqlite3.connect(self._to_ro_uri(snap), uri=True, timeout=2.0)
            self._conn = conn
            return conn

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
        if self._tmpdir is not None:
            self._tmpdir.cleanup()

    @staticmethod
    def _to_ro_uri(path: Path) -> str:
        raw = path.resolve().as_posix()
        quoted = urllib.parse.quote(raw, safe="/:")
        if not quoted.startswith("/"):
            quoted = "/" + quoted
        return f"file:{quoted}?mode=ro"


def iter_jsonl_file(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    try:
        raw_bytes = path.read_bytes()
    except OSError as exc:
        return [], f"unreadable file {path}: {exc}"
    if path.name.endswith(".zst"):
        dec, err = decompress_zstd_bytes(raw_bytes)
        if dec is None:
            return [], f"{path.name}: {err}"
        text = dec.decode("utf-8", errors="replace")
    else:
        text = raw_bytes.decode("utf-8", errors="replace")
    out: list[dict[str, Any]] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                out.append(obj)
        except json.JSONDecodeError:
            continue
    return out, None


# ---------------------------------------------------------------------------
# Cross-OS Store Path Resolution (macOS / Linux / Windows + WSL awareness)
# ---------------------------------------------------------------------------


def resolve_harness_roots(
    *,
    os_name: str = "auto",
    home: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, dict[str, list[Path]]]:
    os_norm = normalize_os_name(os_name)
    e = dict(os.environ if env is None else env)
    h = home or Path(e.get("USERPROFILE") or e.get("HOME") or str(Path.home()))

    appdata = Path(e["APPDATA"]) if e.get("APPDATA") else (h / "AppData" / "Roaming")
    localappdata = Path(e["LOCALAPPDATA"]) if e.get("LOCALAPPDATA") else (h / "AppData" / "Local")
    xdg_config = Path(e["XDG_CONFIG_HOME"]) if e.get("XDG_CONFIG_HOME") else (h / ".config")
    xdg_data = Path(e["XDG_DATA_HOME"]) if e.get("XDG_DATA_HOME") else (h / ".local" / "share")

    def app_support_user(app_name: str) -> Path:
        if os_norm == "macos":
            return h / "Library" / "Application Support" / app_name / "User"
        if os_norm == "windows":
            return appdata / app_name / "User"
        return xdg_config / app_name / "User"

    # 1) Claude Code
    claude_cfg = Path(e["CLAUDE_CONFIG_DIR"]) if e.get("CLAUDE_CONFIG_DIR") else (h / ".claude")
    claude_proj_name = e.get("CLAUDE_CODE_PROJECT_DIR_NAME") or "projects"
    claude_dirs = [claude_cfg / claude_proj_name, claude_cfg / "transcripts"]
    if os_norm == "macos":
        claude_dirs.append(
            h / "Library" / "Developer" / "Xcode" / "CodingAssistant" / "ClaudeAgentConfig" / claude_proj_name
        )

    # 2) Codex
    codex_root = Path(e["CODEX_HOME"]) if e.get("CODEX_HOME") else (h / ".codex")
    codex_db_root = Path(e["CODEX_SQLITE_HOME"]) if e.get("CODEX_SQLITE_HOME") else codex_root
    codex_rollout_roots = [codex_root / "sessions", codex_root / "archived_sessions"]
    if os_norm == "macos":
        codex_rollout_roots.append(
            h / "Library" / "Developer" / "Xcode" / "CodingAssistant" / "codex" / "sessions"
        )

    # 3) Cursor
    if e.get("CURSOR_CONFIG_DIR"):
        cursor_cli_roots = [Path(e["CURSOR_CONFIG_DIR"])]
    else:
        cursor_cli_roots = [h / ".cursor"]
        if xdg_config.is_dir():
            try:
                xdg_entries = {p.name for p in xdg_config.iterdir()}
            except OSError:
                xdg_entries = set()
            if "cursor" in xdg_entries and (xdg_config / "cursor") not in cursor_cli_roots:
                cursor_cli_roots.append(xdg_config / "cursor")
    cursor_ide_roots = [app_support_user("Cursor")]

    # 4) Windsurf / Devin Desktop
    ws_base = Path(e["DEJA_WINDSURF_ROOT"]) if e.get("DEJA_WINDSURF_ROOT") else (h / ".codeium" / "windsurf")
    ws_cascade_dirs = [
        ws_base / "cascade",
        h / ".codeium" / "windsurf-next" / "cascade",
        h / ".codeium" / "windsurf-insiders" / "cascade",
    ]
    ws_hook_dirs = [h / ".windsurf" / "transcripts"]

    # 5) GitHub Copilot (CLI + VS Code variants)
    cop_home = (
        Path(e["COPILOT_HOME"])
        if e.get("COPILOT_HOME")
        else (Path(e["XDG_STATE_HOME"]) / ".copilot" if e.get("XDG_STATE_HOME") else (h / ".copilot"))
    )
    vscode_roots = [app_support_user(ed) for ed in ("Code", "Code - Insiders", "VSCodium")]
    if os_norm == "linux":
        vscode_roots.append(h / ".vscode-server" / "data" / "User")

    # 6) Kiro (CLI, V3/IDE ~/.kiro, headless SQLite, IDE globalStorage)
    kiro_root = Path(e["DEJA_KIRO_ROOT"]) if e.get("DEJA_KIRO_ROOT") else (h / ".kiro")
    if os_norm == "macos":
        kiro_headless_db = h / "Library" / "Application Support" / "kiro-cli" / "data.sqlite3"
    elif os_norm == "windows":
        kiro_headless_db = localappdata / "kiro-cli" / "data.sqlite3"
    else:
        kiro_headless_db = xdg_data / "kiro-cli" / "data.sqlite3"
    kiro_ide_agent = app_support_user("Kiro") / "globalStorage" / "kiro.kiroagent"

    # 7) OpenCode
    oc_dbs: list[Path] = []
    if e.get("OPENCODE_DB"):
        oc_dbs.append(Path(e["OPENCODE_DB"]))
    oc_dbs.append(xdg_data / "opencode" / "opencode.db")
    if (h / ".local" / "share" / "opencode" / "opencode.db") not in oc_dbs:
        oc_dbs.append(h / ".local" / "share" / "opencode" / "opencode.db")
    if os_norm == "windows":
        oc_dbs.append(localappdata / "opencode" / "opencode.db")
    oc_diff_dirs = [p.parent / "storage" / "session_diff" for p in oc_dbs]

    # 8) Zed
    zed_dbs: list[Path] = []
    zed_conv_dirs: list[Path] = []
    if e.get("DEJA_ZED_DB"):
        zed_dbs.append(Path(e["DEJA_ZED_DB"]))
    if os_norm == "macos":
        zroot = h / "Library" / "Application Support" / "Zed"
        zed_dbs.append(zroot / "threads" / "threads.db")
        zed_conv_dirs.append(zroot / "conversations")
    elif os_norm == "windows":
        zroot = localappdata / "Zed"
        zed_dbs.append(zroot / "threads" / "threads.db")
        zed_conv_dirs.append(zroot / "conversations")
    else:
        if e.get("FLATPAK_XDG_DATA_HOME"):
            fp = Path(e["FLATPAK_XDG_DATA_HOME"]) / "zed"
            zed_dbs.append(fp / "threads" / "threads.db")
            zed_conv_dirs.append(fp / "conversations")
        zed_dbs.append(xdg_data / "zed" / "threads" / "threads.db")
        zed_dbs.append(h / ".var" / "app" / "dev.zed.Zed" / "data" / "zed" / "threads" / "threads.db")
        zed_conv_dirs.append(xdg_data / "zed" / "conversations")

    # 9) Devin CLI
    devin_dbs: list[Path] = []
    if e.get("DEJA_DEVIN_DB"):
        devin_dbs.append(Path(e["DEJA_DEVIN_DB"]))
    if os_norm == "windows":
        devin_dbs.append(appdata / "devin" / "cli" / "sessions.db")
        devin_dbs.append(appdata / "devin" / "cli" / "cli_sessions.db")
    else:
        devin_dbs.append(xdg_data / "devin" / "cli" / "sessions.db")
        devin_dbs.append(xdg_data / "devin" / "cli" / "cli_sessions.db")

    result: dict[str, dict[str, list[Path]]] = {
        "claude": {"project_roots": claude_dirs},
        "codex": {"rollout_roots": codex_rollout_roots, "state_dbs": [codex_db_root / "state_5.sqlite"]},
        "cursor": {"cli_roots": cursor_cli_roots, "ide_roots": cursor_ide_roots},
        "windsurf": {"cascade_dirs": ws_cascade_dirs, "hook_dirs": ws_hook_dirs},
        "copilot": {"cli_roots": [cop_home / "session-state"], "vscode_roots": vscode_roots},
        "kiro": {
            "kiro_roots": [kiro_root],
            "headless_dbs": [kiro_headless_db],
            "ide_agent_dirs": [kiro_ide_agent],
        },
        "opencode": {"dbs": oc_dbs, "diff_dirs": oc_diff_dirs},
        "zed": {"thread_dbs": zed_dbs, "conversation_dirs": zed_conv_dirs},
        "devin": {"dbs": devin_dbs},
    }

    # WSL bridge: allow Linux CLI agents inside WSL to read Windows host IDE/CLI stores seamlessly
    if os_norm == "linux" and (e.get("WSL_WIN_HOME") or e.get("WSL_DISTRO_NAME")):
        win_home: Path | None = None
        if e.get("WSL_WIN_HOME"):
            win_home = Path(e["WSL_WIN_HOME"])
        else:
            candidate = Path("/mnt/c/Users") / (e.get("USER") or h.name)
            if candidate.is_dir():
                win_home = candidate
        if win_home is not None:
            win_roots = resolve_harness_roots(
                os_name="windows",
                home=win_home,
                env={
                    "USERPROFILE": str(win_home),
                    "APPDATA": str(win_home / "AppData" / "Roaming"),
                    "LOCALAPPDATA": str(win_home / "AppData" / "Local"),
                },
            )
            for h_key, groups in win_roots.items():
                for g_key, paths in groups.items():
                    target_list = result[h_key][g_key]
                    for p in paths:
                        if p not in target_list:
                            target_list.append(p)

    return result


# ---------------------------------------------------------------------------
# Normalized Session Accumulator
# ---------------------------------------------------------------------------


class SessionRecord:
    def __init__(
        self,
        *,
        harness: str,
        session_id: str,
        source_path: str,
        cwd: str = "",
        title: str = "",
        git_branch: str = "",
        updated_iso: str = "",
        updated_epoch: float = 0.0,
    ) -> None:
        self.harness = harness
        self.session_id = session_id
        self.source_path = source_path
        self.cwd = decode_file_uri(cwd) if cwd else ""
        self.title = redact_secrets(title).strip()
        self.git_branch = git_branch
        self.updated_iso = updated_iso
        self.updated_epoch = updated_epoch
        self.turns: list[dict[str, Any]] = []
        self.files_touched: list[str] = []
        self.commands: list[dict[str, Any]] = []
        self.subagents: list[dict[str, Any]] = []
        self.warnings: list[str] = []

    def add_file(self, path_str: str | None) -> None:
        if not path_str:
            return
        cleaned = decode_file_uri(str(path_str).strip())
        if cleaned and cleaned not in self.files_touched:
            self.files_touched.append(cleaned)

    def add_command(self, cmd: str | None, exit_code: int | None = None, error_tail: str = "") -> None:
        if not cmd or not str(cmd).strip():
            return
        cleaned = redact_secrets(str(cmd).strip())
        entry: dict[str, Any] = {"command": one_line(cleaned, 220), "exit_code": exit_code}
        if error_tail:
            entry["output_tail"] = one_line(redact_secrets(error_tail), 220)
        self.commands.append(entry)

    def add_turn(self, role: str, text: str, timestamp: str = "") -> None:
        cleaned = clean_prompt_text(text) if role == "user" else redact_secrets(text).strip()
        if not cleaned:
            return
        if self.turns and self.turns[-1]["role"] == role and not timestamp:
            self.turns[-1]["text"] = (self.turns[-1]["text"] + "\n" + cleaned).strip()
            return
        self.turns.append({"role": role, "text": cleaned, "timestamp": timestamp})

    def goal(self) -> str:
        for t in self.turns:
            if t["role"] == "user" and t["text"].strip():
                return t["text"].strip()
        return self.title

    def display_title(self) -> str:
        if self.title:
            return one_line(self.title, 90)
        return one_line(self.goal(), 90) or "(untitled session)"

    def to_summary(self) -> dict[str, Any]:
        return {
            "harness": self.harness,
            "session_id": self.session_id,
            "updated_at": self.updated_iso,
            "_epoch": self.updated_epoch,
            "cwd": self.cwd,
            "git_branch": self.git_branch,
            "title": self.display_title(),
            "turn_count": len(self.turns),
            "files_touched_count": len(self.files_touched),
            "source_path": self.source_path,
            "warnings": self.warnings,
        }

    def to_brief(self, max_turns: int = 6) -> dict[str, Any]:
        decisions: list[str] = []
        for idx, t in enumerate(self.turns):
            if idx == 0 and t["role"] == "user":
                continue
            if t["role"] == "user" and len(t["text"].strip()) > 3:
                decisions.append(one_line(t["text"], 200))
        return {
            "harness": self.harness,
            "session_id": self.session_id,
            "updated_at": self.updated_iso,
            "cwd": self.cwd,
            "git_branch": self.git_branch,
            "title": self.display_title(),
            "source_path": self.source_path,
            "goal": one_line(self.goal(), 500),
            "user_followups_and_decisions": decisions[-8:],
            "files_touched": self.files_touched[:60],
            "commands": self.commands[-20:],
            "recent_turns": [
                {
                    "role": t["role"],
                    "timestamp": t["timestamp"],
                    "text": t["text"][:1500] + ("…" if len(t["text"]) > 1500 else ""),
                }
                for t in self.turns[-max(1, max_turns) :]
            ],
            "subagents": self.subagents[:15],
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# 9 Harness Parsers
# ---------------------------------------------------------------------------


def _load_claude_sessions(
    roots: dict[str, list[Path]],
    warnings: list[str],
    *,
    max_items: int | None = None,
    session_hint: str | None = None,
) -> list[SessionRecord]:
    out: list[SessionRecord] = []
    candidates: list[Path] = []
    for proj_root in roots["project_roots"]:
        if not proj_root.is_dir():
            continue
        for entry in proj_root.iterdir():
            if entry.is_file() and entry.suffix == ".jsonl":
                candidates.append(entry)
            elif entry.is_dir():
                candidates.extend(entry.glob("*.jsonl"))
    candidates.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0.0, reverse=True)
    if session_hint:
        hinted = [p for p in candidates if p.stem.startswith(session_hint)]
        if hinted:
            candidates = hinted
    for fpath in candidates:
        if max_items is not None and len(out) >= max_items:
            break
        rows, err = iter_jsonl_file(fpath)
        if err:
            warnings.append(err)
            continue
        if not rows:
            continue
        mtime = fpath.stat().st_mtime
        sid = fpath.stem
        rec = SessionRecord(harness="claude", session_id=sid, source_path=str(fpath))
        last_ts = ""
        last_ep = mtime
        for obj in rows:
            rtype = obj.get("type")
            if obj.get("sessionId") and not obj.get("isSidechain"):
                rec.session_id = str(obj["sessionId"])
            if not rec.cwd and isinstance(obj.get("cwd"), str):
                rec.cwd = obj["cwd"]
            if not rec.git_branch and isinstance(obj.get("gitBranch"), str):
                rec.git_branch = obj["gitBranch"]
            if rtype in ("agent-name", "custom-title", "ai-title"):
                tval = obj.get("agentName") or obj.get("customTitle") or obj.get("aiTitle")
                if isinstance(tval, str) and tval.strip():
                    rec.title = tval.strip()
            if isinstance(obj.get("timestamp"), (str, int, float)):
                iso, ep = ts_to_iso(obj["timestamp"], mtime)
                if ep >= last_ep or not last_ts:
                    last_ts, last_ep = iso, ep
            if rtype not in ("user", "assistant"):
                continue
            if obj.get("isMeta") is True:
                continue
            msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            role = str(msg.get("role") or rtype)
            content = msg.get("content")
            texts: list[str] = []
            if isinstance(content, str):
                if obj.get("toolUseResult") is None:
                    texts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    ptype = part.get("type")
                    if ptype == "text":
                        t = part.get("text") or part.get("content") or ""
                        if isinstance(t, str) and t.strip():
                            texts.append(t)
                    elif ptype == "tool_use":
                        tname = str(part.get("name") or "")
                        tinp = part.get("input") if isinstance(part.get("input"), dict) else {}
                        if tname in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                            rec.add_file(tinp.get("file_path") or tinp.get("notebook_path"))
                        elif tname in ("Bash", "Shell", "exec"):
                            rec.add_command(tinp.get("command"))
            if texts:
                iso_turn, _ = ts_to_iso(obj.get("timestamp"), None)
                rec.add_turn("user" if role == "user" else "assistant", "\n".join(texts), iso_turn)

        sub_dir = fpath.parent / fpath.stem / "subagents"
        if sub_dir.is_dir():
            for sf in sorted(sub_dir.glob("agent-*.jsonl")):
                srows, _ = iter_jsonl_file(sf)
                stask = ""
                sreply = ""
                for sobj in srows:
                    msg = sobj.get("message") if isinstance(sobj.get("message"), dict) else {}
                    cnt = msg.get("content")
                    txt = ""
                    if isinstance(cnt, str):
                        txt = cnt
                    elif isinstance(cnt, list):
                        for p in cnt:
                            if isinstance(p, dict) and p.get("type") == "text":
                                txt += str(p.get("text") or "")
                            elif isinstance(p, dict) and p.get("type") == "tool_use":
                                inp = p.get("input") if isinstance(p.get("input"), dict) else {}
                                if p.get("name") in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                                    rec.add_file(inp.get("file_path") or inp.get("notebook_path"))
                    if sobj.get("type") == "user" and not stask and txt.strip():
                        stask = one_line(txt, 140)
                    elif sobj.get("type") == "assistant" and txt.strip():
                        sreply = one_line(txt, 180)
                if stask or sreply:
                    rec.subagents.append({"agent_id": sf.stem, "task": stask, "summary": sreply})

        rec.updated_iso, rec.updated_epoch = (last_ts, last_ep) if last_ts else ts_to_iso(None, mtime)
        if rec.turns or rec.files_touched:
            out.append(rec)
    return out


def _codex_uuid_from_filename(name: str) -> str:
    base = name[:-10] if name.endswith(".jsonl.zst") else (name[:-6] if name.endswith(".jsonl") else name)
    m = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,})$", base)
    return m.group(1) if m else base


def _load_codex_sessions(
    roots: dict[str, list[Path]],
    warnings: list[str],
    *,
    max_items: int | None = None,
    session_hint: str | None = None,
) -> list[SessionRecord]:
    by_uuid: dict[str, tuple[float, Path]] = {}
    for rroot in roots["rollout_roots"]:
        if not rroot.is_dir():
            continue
        for pat in ("**/rollout-*.jsonl", "**/rollout-*.jsonl.zst"):
            for fpath in rroot.glob(pat):
                if not fpath.is_file():
                    continue
                uid = _codex_uuid_from_filename(fpath.name)
                if session_hint and not uid.startswith(session_hint):
                    continue
                mt = fpath.stat().st_mtime
                prev = by_uuid.get(uid)
                if prev is None or mt >= prev[0]:
                    by_uuid[uid] = (mt, fpath)

    ordered = sorted(by_uuid.items(), key=lambda kv: kv[1][0], reverse=True)
    out: list[SessionRecord] = []
    for uid, (mtime, fpath) in ordered:
        if max_items is not None and len(out) >= max_items:
            break
        rows, err = iter_jsonl_file(fpath)
        if err:
            warnings.append(err)
            continue
        if not rows:
            continue
        rec = SessionRecord(harness="codex", session_id=uid, source_path=str(fpath))
        seen_meta = False
        pending_calls: dict[str, str] = {}
        roled_turns: list[tuple[str, str, str]] = []
        event_turns: list[tuple[str, str, str]] = []
        last_iso, last_ep = ts_to_iso(None, mtime)

        for obj in rows:
            iso, ep = ts_to_iso(obj.get("timestamp"), None)
            if iso:
                last_iso, last_ep = iso, ep
            otype = obj.get("type")
            payload = obj.get("payload") if isinstance(obj.get("payload"), dict) else {}

            if otype == "session_meta":
                if not seen_meta:
                    seen_meta = True
                    rec.session_id = str(payload.get("id") or payload.get("session_id") or uid)
                    rec.cwd = str(payload.get("cwd") or "")
                    git_info = payload.get("git") if isinstance(payload.get("git"), dict) else {}
                    rec.git_branch = str(git_info.get("branch") or "")
                continue

            if otype == "response_item":
                ptype = payload.get("type")
                role = payload.get("role")
                if ptype == "custom_tool_call" and payload.get("name") == "apply_patch":
                    for p in extract_patch_paths(str(payload.get("input") or "")):
                        rec.add_file(p)
                elif ptype == "function_call":
                    fname = str(payload.get("name") or "")
                    raw_args = payload.get("arguments")
                    args = {}
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            args = {}
                    elif isinstance(raw_args, dict):
                        args = raw_args
                    if fname in ("exec_command", "shell_command", "shell"):
                        cmd = str(args.get("cmd") or args.get("command") or "")
                        cid = str(payload.get("call_id") or "")
                        if cid and cmd:
                            pending_calls[cid] = cmd
                        elif cmd:
                            rec.add_command(cmd)
                    elif fname == "apply_patch":
                        for p in extract_patch_paths(str(args.get("patch") or raw_args or "")):
                            rec.add_file(p)
                elif ptype == "function_call_output":
                    cid = str(payload.get("call_id") or "")
                    out_txt = str(payload.get("output") or "")
                    m_exit = EXIT_CODE_RE.search(out_txt)
                    code = int(m_exit.group(1)) if m_exit else None
                    if cid in pending_calls:
                        rec.add_command(pending_calls.pop(cid), code, out_txt[-240:] if code else "")
                elif role in ("user", "assistant"):
                    cnt = payload.get("content")
                    parts_txt: list[str] = []
                    if isinstance(cnt, str):
                        if not CODEX_BOILERPLATE_RE.match(cnt):
                            parts_txt.append(cnt)
                    elif isinstance(cnt, list):
                        for item in cnt:
                            if isinstance(item, dict):
                                t = str(item.get("text") or "")
                                if t and not CODEX_BOILERPLATE_RE.match(t):
                                    parts_txt.append(t)
                    joined = "\n".join(parts_txt).strip()
                    if joined:
                        roled_turns.append((role, joined, iso))

            elif otype == "event_msg":
                etype = payload.get("type")
                if etype == "user_message" and isinstance(payload.get("message"), str):
                    txt = payload["message"]
                    if not CODEX_BOILERPLATE_RE.match(txt):
                        event_turns.append(("user", txt, iso))
                elif etype == "agent_message" and payload.get("phase", "final") != "commentary":
                    if isinstance(payload.get("message"), str):
                        event_turns.append(("assistant", payload["message"], iso))
                elif etype == "item_completed" and isinstance(payload.get("item"), dict):
                    item = payload["item"]
                    itype = item.get("type")
                    if itype == "FileChange" and isinstance(item.get("changes"), dict):
                        for fp in item["changes"].keys():
                            rec.add_file(fp)
                    elif itype == "UserMessage" and isinstance(item.get("content"), list):
                        txt = "\n".join(str(x.get("text") or "") for x in item["content"] if isinstance(x, dict))
                        if txt.strip() and not CODEX_BOILERPLATE_RE.match(txt):
                            event_turns.append(("user", txt, iso))
                    elif itype == "AgentMessage" and item.get("phase", "final") != "commentary":
                        if isinstance(item.get("content"), list):
                            txt = "\n".join(str(x.get("text") or "") for x in item["content"] if isinstance(x, dict))
                            if txt.strip():
                                event_turns.append(("assistant", txt, iso))

        for cid, cmd in pending_calls.items():
            rec.add_command(cmd)
        chosen = roled_turns if roled_turns else event_turns
        for role, txt, iso in chosen:
            rec.add_turn(role, txt, iso)
        rec.updated_iso, rec.updated_epoch = last_iso, last_ep
        if rec.turns or rec.files_touched:
            out.append(rec)
    return out


def _load_cursor_sessions(
    roots: dict[str, list[Path]],
    warnings: list[str],
    *,
    max_items: int | None = None,
    session_hint: str | None = None,
) -> list[SessionRecord]:
    out: list[SessionRecord] = []
    seen_ids: set[str] = set()
    cap = max_items if max_items is not None else 120

    # Build chat_uuid -> cwd map from Cursor CLI ~/.cursor/chats/<md5>/<uuid>/meta.json
    cli_cwd_map: dict[str, str] = {}
    for croot in roots["cli_roots"]:
        chats_dir = croot / "chats"
        if chats_dir.is_dir():
            for meta_file in chats_dir.glob("*/*/meta.json"):
                try:
                    mobj = json.loads(meta_file.read_text(encoding="utf-8"))
                    if isinstance(mobj, dict) and isinstance(mobj.get("cwd"), str):
                        cli_cwd_map[meta_file.parent.name] = mobj["cwd"]
                except Exception:
                    continue

    # 1) Cursor plaintext agent-transcripts (sorted newest-first)
    all_tfiles: list[tuple[float, Path]] = []
    for croot in roots["cli_roots"]:
        proj_root = croot / "projects"
        if not proj_root.is_dir():
            continue
        for at_dir in proj_root.glob("*/agent-transcripts"):
            if not at_dir.is_dir():
                continue
            tfiles: list[Path] = list(at_dir.glob("*.jsonl"))
            for child in at_dir.iterdir():
                if child.is_dir() and child.name != "subagents":
                    tfiles.extend(child.glob("*.jsonl"))
            for fp in tfiles:
                if session_hint and not fp.stem.startswith(session_hint):
                    continue
                try:
                    all_tfiles.append((fp.stat().st_mtime, fp))
                except OSError:
                    continue

    all_tfiles.sort(key=lambda item: item[0], reverse=True)
    for mtime, fpath in all_tfiles[:cap]:
        rows, err = iter_jsonl_file(fpath)
        if err or not rows:
            if err:
                warnings.append(err)
            continue
        sid = fpath.stem
        iso, ep = ts_to_iso(None, mtime)
        rec = SessionRecord(
            harness="cursor",
            session_id=sid,
            source_path=str(fpath),
            cwd=cli_cwd_map.get(sid, ""),
            updated_iso=iso,
            updated_epoch=ep,
        )
        for obj in rows:
            role = obj.get("role")
            if role not in ("user", "assistant"):
                continue
            msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}
            cnt = msg.get("content")
            texts: list[str] = []
            if isinstance(cnt, str):
                texts.append(cnt)
            elif isinstance(cnt, list):
                for part in cnt:
                    if not isinstance(part, dict):
                        continue
                    ptype = part.get("type")
                    if ptype == "text" and isinstance(part.get("text"), str):
                        texts.append(part["text"])
                    elif ptype == "tool_use":
                        tname = str(part.get("name") or "")
                        inp = part.get("input") if isinstance(part.get("input"), dict) else {}
                        if tname in ("Write", "StrReplace", "Delete", "Edit"):
                            rec.add_file(inp.get("path") or inp.get("file_path"))
                        elif tname == "ApplyPatch":
                            for p in extract_patch_paths(str(inp.get("patch") or inp)):
                                rec.add_file(p)
                        elif tname in ("Shell", "Bash"):
                            rec.add_command(inp.get("command"))
            if texts:
                rec.add_turn(role, "\n".join(texts))

        sub_dir = fpath.parent / "subagents"
        if sub_dir.is_dir():
            for sf in sorted(sub_dir.glob("*.jsonl")):
                srows, _ = iter_jsonl_file(sf)
                for sobj in srows:
                    if sobj.get("role") == "assistant":
                        msg = sobj.get("message") if isinstance(sobj.get("message"), dict) else {}
                        for p in msg.get("content") or []:
                            if isinstance(p, dict) and p.get("type") == "tool_use":
                                inp = p.get("input") if isinstance(p.get("input"), dict) else {}
                                if p.get("name") in ("Write", "StrReplace", "Delete"):
                                    rec.add_file(inp.get("path"))
        if rec.turns or rec.files_touched:
            seen_ids.add(sid)
            out.append(rec)

    # 2) Cursor IDE globalStorage/state.vscdb
    for uroot in roots["ide_roots"]:
        gdb = uroot / "globalStorage" / "state.vscdb"
        if not gdb.is_file():
            continue
        try:
            with ReadOnlySqlite(gdb) as conn:
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if "cursorDiskKV" not in tables:
                    continue
                ws_by_cid: dict[str, str] = {}
                if "composerHeaders" in tables:
                    for cid, val_str in conn.execute("SELECT composerId, value FROM composerHeaders"):
                        try:
                            v = json.loads(val_str or "{}")
                            uri = (((v.get("workspaceIdentifier") or {}).get("uri")) or {})
                            fsp = uri.get("fsPath") or uri.get("path") or ""
                            if fsp:
                                ws_by_cid[str(cid)] = str(fsp)
                        except Exception:
                            continue

                if session_hint:
                    c_prefix = f"composerData:{session_hint}"
                    c_upper = c_prefix[:-1] + chr(ord(c_prefix[-1]) + 1)
                    composers = conn.execute(
                        "SELECT substr(key, 14), value FROM cursorDiskKV WHERE key >= ? AND key < ?",
                        (c_prefix, c_upper),
                    ).fetchall()
                else:
                    composers = conn.execute(
                        "SELECT substr(key, 14), value FROM cursorDiskKV WHERE key >= 'composerData:' AND key < 'composerData;'"
                    ).fetchall()
                parsed_composers: list[tuple[float, str, str, dict[str, Any], list[Any]]] = []
                db_mtime = gdb.stat().st_mtime
                for cid, raw_val in composers:
                    if not cid or not raw_val or cid in seen_ids:
                        continue
                    try:
                        cobj = json.loads(raw_val)
                    except Exception:
                        continue
                    if not isinstance(cobj, dict):
                        continue
                    headers = cobj.get("fullConversationHeadersOnly")
                    if not isinstance(headers, list) or not headers:
                        continue
                    ts_val = cobj.get("lastUpdatedAt") or cobj.get("createdAt")
                    iso, ep = ts_to_iso(ts_val, db_mtime)
                    parsed_composers.append((ep, iso, str(cid), cobj, headers))

                parsed_composers.sort(key=lambda item: item[0], reverse=True)
                for ep, iso, cid, cobj, headers in parsed_composers[:cap]:
                    title = str(cobj.get("name") or cobj.get("subtitle") or "")
                    rec = SessionRecord(
                        harness="cursor",
                        session_id=cid,
                        source_path=str(gdb),
                        cwd=ws_by_cid.get(cid, ""),
                        title=title,
                        updated_iso=iso,
                        updated_epoch=ep,
                    )
                    b_prefix = f"bubbleId:{cid}:"
                    b_upper = f"bubbleId:{cid};"
                    bubble_map = {
                        bk: bval
                        for bk, bval in conn.execute(
                            "SELECT key, value FROM cursorDiskKV WHERE key >= ? AND key < ?",
                            (b_prefix, b_upper),
                        )
                        if bk and bval
                    }
                    for h_item in headers:
                        if not isinstance(h_item, dict) or not h_item.get("bubbleId"):
                            continue
                        bkey = f"bubbleId:{cid}:{h_item['bubbleId']}"
                        brow_val = bubble_map.get(bkey)
                        if not brow_val:
                            continue
                        try:
                            bobj = json.loads(brow_val)
                        except Exception:
                            continue
                        if not isinstance(bobj, dict):
                            continue
                        if not rec.cwd and isinstance(bobj.get("workspaceProjectDir"), str):
                            rec.cwd = bobj["workspaceProjectDir"]
                        btype = bobj.get("type") or h_item.get("type")
                        role = "user" if btype == 1 else "assistant"
                        txt = str(bobj.get("text") or bobj.get("rawText") or "")
                        b_iso, b_ep = ts_to_iso(bobj.get("createdAt") or bobj.get("timestamp"), None)
                        if b_ep > rec.updated_epoch:
                            rec.updated_iso, rec.updated_epoch = b_iso, b_ep
                        if txt.strip():
                            rec.add_turn(role, txt, b_iso)
                        tf = bobj.get("toolFormerData")
                        if isinstance(tf, dict):
                            tname = str(tf.get("name") or "")
                            params_raw = tf.get("params")
                            params = {}
                            if isinstance(params_raw, str):
                                try:
                                    params = json.loads(params_raw)
                                except Exception:
                                    params = {}
                            elif isinstance(params_raw, dict):
                                params = params_raw
                            for k in ("target_file", "path", "file_path", "relativeWorkspacePath"):
                                if isinstance(params.get(k), str):
                                    rec.add_file(params[k])
                            if isinstance(params.get("command"), str):
                                rec.add_command(params["command"])
                    if rec.turns or rec.files_touched:
                        out.append(rec)
        except Exception as exc:
            warnings.append(f"Cursor SQLite {gdb}: {exc}")
    return out


def _parse_windsurf_trajectory(pb_bytes: bytes, source_path: Path) -> SessionRecord:
    mtime = source_path.stat().st_mtime
    rec = SessionRecord(
        harness="windsurf",
        session_id=source_path.stem,
        source_path=str(source_path),
    )
    best_ep = 0.0
    for fno, wtype, val in pb_iter_fields(pb_bytes):
        if fno == 6 and wtype == 2:
            cid = _pb_decode_utf8(val).strip()
            if cid:
                rec.session_id = cid
        elif fno == 10 and wtype == 2:
            t = _pb_decode_utf8(val).strip()
            if t:
                rec.title = t
        elif fno == 7 and wtype == 2 and isinstance(val, bytes):
            for mfno, mwtype, mval in pb_iter_fields(val):
                if mfno == 1 and mwtype == 2 and isinstance(mval, bytes) and not rec.cwd:
                    ws_uri = ""
                    git_uri = ""
                    for wfno, wwtype, wval in pb_iter_fields(mval):
                        if wfno == 1 and wwtype == 2:
                            ws_uri = _pb_decode_utf8(wval)
                        elif wfno == 2 and wwtype == 2:
                            git_uri = _pb_decode_utf8(wval)
                    rec.cwd = decode_file_uri(git_uri or ws_uri)
                elif mfno == 2 and mwtype == 2 and isinstance(mval, bytes):
                    best_ep = max(best_ep, _pb_decode_timestamp(mval))
        elif fno == 2 and wtype == 2 and isinstance(val, bytes):
            step_ep = 0.0
            user_txt = ""
            asst_txt = ""
            for sfno, swtype, sval in pb_iter_fields(val):
                if sfno == 5 and swtype == 2 and isinstance(sval, bytes):
                    for tfno, twtype, tval in pb_iter_fields(sval):
                        if tfno in (1, 8) and twtype == 2 and isinstance(tval, bytes):
                            step_ep = max(step_ep, _pb_decode_timestamp(tval))
                elif sfno == 19 and swtype == 2 and isinstance(sval, bytes):
                    q_txt = ""
                    u_resp = ""
                    for ufno, uwtype, uval in pb_iter_fields(sval):
                        if ufno == 1 and uwtype == 2:
                            q_txt = _pb_decode_utf8(uval)
                        elif ufno == 2 and uwtype == 2:
                            u_resp = _pb_decode_utf8(uval)
                    user_txt = u_resp.strip() or q_txt.strip()
                elif sfno == 20 and swtype == 2 and isinstance(sval, bytes):
                    r_txt = ""
                    m_resp = ""
                    for pfno, pwtype, pval in pb_iter_fields(sval):
                        if pfno == 1 and pwtype == 2:
                            r_txt = _pb_decode_utf8(pval)
                        elif pfno == 8 and pwtype == 2:
                            m_resp = _pb_decode_utf8(pval)
                    asst_txt = r_txt.strip() or m_resp.strip()
            best_ep = max(best_ep, step_ep)
            s_iso, _ = ts_to_iso(step_ep, None) if step_ep > 0 else ("", 0.0)
            if user_txt:
                rec.add_turn("user", user_txt, s_iso)
            if asst_txt:
                rec.add_turn("assistant", asst_txt, s_iso)

    rec.updated_iso, rec.updated_epoch = ts_to_iso(best_ep if best_ep > 0 else None, mtime)
    return rec


def _load_windsurf_sessions(roots: dict[str, list[Path]], warnings: list[str]) -> list[SessionRecord]:
    out: list[SessionRecord] = []
    auth_failures = 0
    for cdir in roots["cascade_dirs"]:
        if not cdir.is_dir():
            continue
        for pb_file in sorted(cdir.glob("*.pb")):
            try:
                sealed = pb_file.read_bytes()
                plain = decrypt_aes256_gcm(WINDSURF_AES_KEY, sealed)
                rec = _parse_windsurf_trajectory(plain, pb_file)
                if rec.turns or rec.title:
                    out.append(rec)
            except ValueError:
                auth_failures += 1
            except Exception as exc:
                warnings.append(f"Windsurf {pb_file.name}: {exc}")
    if auth_failures:
        warnings.append(f"windsurf: {auth_failures} .pb trajectory file(s) failed authentication/decode and were skipped")
    seen_ids = {r.session_id for r in out}
    for hdir in roots.get("hook_dirs", []):
        if not hdir.is_dir():
            continue
        for jf in sorted(hdir.glob("*.jsonl")):
            if jf.stem in seen_ids:
                continue
            rows, _ = iter_jsonl_file(jf)
            if not rows:
                continue
            iso, ep = ts_to_iso(None, jf.stat().st_mtime)
            rec = SessionRecord(harness="windsurf", session_id=jf.stem, source_path=str(jf), updated_iso=iso, updated_epoch=ep)
            for row in rows:
                role = str(row.get("role") or row.get("type") or "")
                txt = str(row.get("content") or row.get("text") or row.get("query") or "")
                if role in ("user", "user_input") and txt:
                    rec.add_turn("user", txt)
                elif role in ("assistant", "planner_response") and txt:
                    rec.add_turn("assistant", txt)
            if rec.turns:
                out.append(rec)
    return out


def _apply_vscode_delta(state: Any, kind: int, keys: list[Any], val: Any) -> Any:
    if kind == 0:
        return val if isinstance(val, dict) else state
    if not isinstance(state, dict) or not keys:
        return state
    cur: Any = state
    for k in keys[:-1]:
        if isinstance(cur, dict):
            cur = cur.setdefault(str(k), {})
        elif isinstance(cur, list) and isinstance(k, int) and 0 <= k < len(cur):
            cur = cur[k]
        else:
            return state
    last = keys[-1]
    if kind == 1:
        if isinstance(cur, dict):
            cur[str(last)] = val
        elif isinstance(cur, list) and isinstance(last, int) and 0 <= last < len(cur):
            cur[last] = val
    elif kind == 2:
        target = cur.get(str(last)) if isinstance(cur, dict) else None
        if isinstance(target, list):
            if isinstance(val, list):
                target.extend(val)
            else:
                target.append(val)
    elif kind == 3:
        if isinstance(cur, dict):
            cur.pop(str(last), None)
        elif isinstance(cur, list) and isinstance(last, int) and 0 <= last < len(cur):
            cur.pop(last)
    return state


def _parse_copilot_event_stream(fpath: Path, default_cwd: str = "") -> SessionRecord | None:
    rows, _ = iter_jsonl_file(fpath)
    if not rows:
        return None
    mtime = fpath.stat().st_mtime
    rec = SessionRecord(harness="copilot", session_id=fpath.parent.name, source_path=str(fpath), cwd=default_cwd)
    last_iso, last_ep = ts_to_iso(None, mtime)
    for obj in rows:
        etype = obj.get("type")
        data = obj.get("data") if isinstance(obj.get("data"), dict) else {}
        iso, ep = ts_to_iso(obj.get("timestamp"), None)
        if iso:
            last_iso, last_ep = iso, ep
        if etype == "session.start":
            if data.get("sessionId"):
                rec.session_id = str(data["sessionId"])
            ctx = data.get("context") if isinstance(data.get("context"), dict) else {}
            if ctx.get("cwd"):
                rec.cwd = str(ctx["cwd"])
        elif etype == "user.message" and isinstance(data.get("content"), str):
            rec.add_turn("user", data["content"], iso)
        elif etype == "assistant.message" and isinstance(data.get("content"), str):
            rec.add_turn("assistant", data["content"], iso)
        elif etype == "tool.execution_start":
            tname = str(data.get("toolName") or "")
            args = data.get("arguments")
            if isinstance(args, str) and tname == "apply_patch":
                for p in extract_patch_paths(args):
                    rec.add_file(p)
            elif isinstance(args, dict):
                if tname in ("edit", "create", "replace_string_in_file", "create_file", "insert_edit_into_file"):
                    rec.add_file(args.get("path") or args.get("filePath"))
                elif tname in ("bash", "powershell", "run_in_terminal"):
                    rec.add_command(args.get("command") or args.get("commandLine"))
                elif tname == "apply_patch":
                    for p in extract_patch_paths(str(args.get("input") or "")):
                        rec.add_file(p)
    rec.updated_iso, rec.updated_epoch = last_iso, last_ep
    return rec if (rec.turns or rec.files_touched) else None


def _load_copilot_sessions(roots: dict[str, list[Path]], warnings: list[str]) -> list[SessionRecord]:
    out: list[SessionRecord] = []
    seen: set[str] = set()

    for croot in roots["cli_roots"]:
        if not croot.is_dir():
            continue
        for ev in sorted(croot.glob("*/events.jsonl")):
            rec = _parse_copilot_event_stream(ev)
            if rec:
                seen.add(rec.session_id)
                out.append(rec)

    for vroot in roots["vscode_roots"]:
        if not vroot.is_dir():
            continue
        ws_bases = [vroot / "workspaceStorage"]
        prof_root = vroot / "profiles"
        if prof_root.is_dir():
            ws_bases.extend(prof_root.glob("*/workspaceStorage"))
        for ws_base in ws_bases:
            if not ws_base.is_dir():
                continue
            for hdir in sorted(ws_base.iterdir()):
                if not hdir.is_dir():
                    continue
                ws_cwd = ""
                wjson = hdir / "workspace.json"
                if wjson.is_file():
                    try:
                        wobj = json.loads(wjson.read_text(encoding="utf-8"))
                        ws_cwd = decode_file_uri(str(wobj.get("folder") or wobj.get("workspace") or ""))
                    except Exception:
                        pass

                # Store B: GitHub.copilot-chat/transcripts/*.jsonl
                tdir = hdir / "GitHub.copilot-chat" / "transcripts"
                if tdir.is_dir():
                    for tf in sorted(tdir.glob("*.jsonl")):
                        rec = _parse_copilot_event_stream(tf, default_cwd=ws_cwd)
                        if rec and rec.session_id not in seen:
                            seen.add(rec.session_id)
                            out.append(rec)

                # Store A: chatSessions/*.jsonl (mutation log) & *.json
                csdir = hdir / "chatSessions"
                if not csdir.is_dir():
                    continue
                for cf in sorted(list(csdir.glob("*.jsonl")) + list(csdir.glob("*.json"))):
                    mtime = cf.stat().st_mtime
                    doc: dict[str, Any] = {}
                    if cf.suffix == ".json":
                        try:
                            loaded = json.loads(cf.read_text(encoding="utf-8", errors="replace"))
                            if isinstance(loaded, dict):
                                doc = loaded
                        except Exception:
                            continue
                    else:
                        rows, err = iter_jsonl_file(cf)
                        if err:
                            warnings.append(err)
                            continue
                        for row in rows:
                            if "kind" in row:
                                doc = _apply_vscode_delta(doc, int(row["kind"]), list(row.get("k") or []), row.get("v"))
                            elif "requests" in row:
                                doc = row
                    if not doc:
                        continue
                    sid = str(doc.get("sessionId") or cf.stem)
                    if sid in seen:
                        continue
                    iso, ep = ts_to_iso(doc.get("lastMessageDate") or doc.get("creationDate"), mtime)
                    rec = SessionRecord(
                        harness="copilot",
                        session_id=sid,
                        source_path=str(cf),
                        cwd=ws_cwd,
                        title=str(doc.get("customTitle") or ""),
                        updated_iso=iso,
                        updated_epoch=ep,
                    )
                    for req in doc.get("requests") or []:
                        if not isinstance(req, dict):
                            continue
                        umsg = req.get("message")
                        utxt = umsg.get("text", "") if isinstance(umsg, dict) else (str(umsg) if isinstance(umsg, str) else "")
                        if utxt:
                            rec.add_turn("user", utxt)
                        resp = req.get("response")
                        achunks: list[str] = []
                        if isinstance(resp, str):
                            achunks.append(resp)
                        elif isinstance(resp, list):
                            for part in resp:
                                if not isinstance(part, dict):
                                    continue
                                if isinstance(part.get("value"), str):
                                    achunks.append(part["value"])
                                if isinstance(part.get("uri"), dict) and part.get("edits"):
                                    u = part["uri"]
                                    rec.add_file(u.get("fsPath") or u.get("path"))
                                tsd = part.get("toolSpecificData")
                                if isinstance(tsd, dict) and isinstance(tsd.get("commandLine"), str):
                                    rec.add_command(tsd["commandLine"])
                        if achunks:
                            rec.add_turn("assistant", "".join(achunks))
                        res = req.get("result") if isinstance(req.get("result"), dict) else {}
                        meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
                        for rnd in meta.get("toolCallRounds") or []:
                            if not isinstance(rnd, dict):
                                continue
                            for tc in rnd.get("toolCalls") or []:
                                if not isinstance(tc, dict):
                                    continue
                                try:
                                    targs = json.loads(tc.get("arguments") or "{}")
                                except Exception:
                                    targs = {}
                                if isinstance(targs, dict) and targs.get("filePath"):
                                    rec.add_file(targs["filePath"])
                    if rec.turns or rec.files_touched:
                        seen.add(sid)
                        out.append(rec)
    return out


def _decode_kiro_b64_workspace(dirname: str) -> str:
    padded = dirname.replace("__", "==").replace("_", "=")
    rem = len(padded) % 4
    if rem:
        padded += "=" * (4 - rem)
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
    except Exception:
        return ""


def _load_kiro_sessions(roots: dict[str, list[Path]], warnings: list[str]) -> list[SessionRecord]:
    out: list[SessionRecord] = []
    seen: set[str] = set()

    for kroot in roots["kiro_roots"]:
        # 1) CLI ~/.kiro/sessions/cli/<id>.jsonl + <id>.json
        cli_dir = kroot / "sessions" / "cli"
        if cli_dir.is_dir():
            for jf in sorted(cli_dir.glob("*.jsonl")):
                rows, _ = iter_jsonl_file(jf)
                if not rows:
                    continue
                hdr_path = jf.with_suffix(".json")
                cwd = ""
                sid = jf.stem
                if hdr_path.is_file():
                    try:
                        hdr = json.loads(hdr_path.read_text(encoding="utf-8"))
                        cwd = str(hdr.get("cwd") or hdr.get("workingDirectory") or "")
                        sid = str(hdr.get("sessionId") or sid)
                    except Exception:
                        pass
                mtime = jf.stat().st_mtime
                rec = SessionRecord(harness="kiro", session_id=sid, source_path=str(jf), cwd=cwd)
                last_iso, last_ep = ts_to_iso(None, mtime)
                active_msg_id: str | None = None
                active_chunks: list[str] = []

                def flush_assistant() -> None:
                    nonlocal active_msg_id, active_chunks
                    if active_chunks:
                        rec.add_turn("assistant", "".join(active_chunks))
                        active_chunks = []
                        active_msg_id = None

                for row in rows:
                    kind = row.get("kind")
                    data = row.get("data") if isinstance(row.get("data"), dict) else {}
                    if kind == "Prompt":
                        flush_assistant()
                        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
                        iso, ep = ts_to_iso(meta.get("timestamp"), None)
                        if iso:
                            last_iso, last_ep = iso, ep
                        txt = "".join(
                            str(c.get("data") or "") for c in (data.get("content") or []) if isinstance(c, dict)
                        )
                        rec.add_turn("user", txt, iso)
                    elif kind == "AssistantMessage":
                        mid = str(data.get("message_id") or "")
                        piece = "".join(
                            str(c.get("data") or "") for c in (data.get("content") or []) if isinstance(c, dict)
                        )
                        if mid and active_msg_id and mid != active_msg_id:
                            flush_assistant()
                        active_msg_id = mid or active_msg_id
                        active_chunks.append(piece)
                flush_assistant()
                rec.updated_iso, rec.updated_epoch = last_iso, last_ep
                if rec.turns:
                    seen.add(sid)
                    out.append(rec)

        # 2) V3 / IDE ~/.kiro/sessions/<ws>/sess_<uuid>/messages.jsonl
        sess_root = kroot / "sessions"
        if sess_root.is_dir():
            for mf in sorted(sess_root.glob("*/sess_*/messages.jsonl")):
                rows, _ = iter_jsonl_file(mf)
                if not rows:
                    continue
                sjson = mf.parent / "session.json"
                sid = mf.parent.name
                cwd = ""
                if sjson.is_file():
                    try:
                        sobj = json.loads(sjson.read_text(encoding="utf-8"))
                        sid = str(sobj.get("id") or sobj.get("sessionId") or sid)
                        wps = sobj.get("workspacePaths")
                        if isinstance(wps, list) and wps:
                            cwd = str(wps[0])
                    except Exception:
                        pass
                mtime = mf.stat().st_mtime
                rec = SessionRecord(harness="kiro", session_id=sid, source_path=str(mf), cwd=cwd)
                last_iso, last_ep = ts_to_iso(None, mtime)
                for row in rows:
                    iso, ep = ts_to_iso(row.get("timestamp"), None)
                    if iso:
                        last_iso, last_ep = iso, ep
                    payload = row.get("payload") if isinstance(row.get("payload"), dict) else row
                    ptype = payload.get("type") or payload.get("role")
                    if payload.get("operationType") == "Reasoning":
                        continue
                    if ptype in ("user", "human"):
                        rec.add_turn("user", str(payload.get("content") or ""), iso)
                    elif ptype in ("assistant", "bot"):
                        rec.add_turn("assistant", str(payload.get("content") or ""), iso)
                    elif ptype == "tool_call" and payload.get("status") in ("completed", "failed", None):
                        tname = str(payload.get("toolName") or "")
                        args = payload.get("args") if isinstance(payload.get("args"), dict) else {}
                        if tname in ("execute_bash", "execute_pwsh", "shell"):
                            rec.add_command(args.get("command"))
                        elif tname in ("fs_write", "fs_append", "str_replace", "write"):
                            rec.add_file(args.get("path") or args.get("targetFile"))
                rec.updated_iso, rec.updated_epoch = last_iso, last_ep
                if rec.turns or rec.files_touched:
                    seen.add(sid)
                    out.append(rec)

    # 3) Kiro IDE globalStorage/kiro.kiroagent/workspace-sessions/<base64>/*.json
    for adir in roots["ide_agent_dirs"]:
        ws_sess = adir / "workspace-sessions"
        if not ws_sess.is_dir():
            continue
        for b64_dir in sorted(ws_sess.iterdir()):
            if not b64_dir.is_dir():
                continue
            decoded_cwd = _decode_kiro_b64_workspace(b64_dir.name)
            idx_dates: dict[str, Any] = {}
            idx_file = b64_dir / "sessions.json"
            if idx_file.is_file():
                try:
                    idx_raw = json.loads(idx_file.read_text(encoding="utf-8"))
                    entries = idx_raw if isinstance(idx_raw, list) else idx_raw.get("sessions", [])
                    for ent in entries:
                        if isinstance(ent, dict) and ent.get("sessionId"):
                            idx_dates[str(ent["sessionId"])] = ent.get("dateCreated")
                except Exception:
                    pass
            for sf in sorted(b64_dir.glob("*.json")):
                if sf.name == "sessions.json" or sf.name.startswith("._migration"):
                    continue
                try:
                    sobj = json.loads(sf.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not isinstance(sobj, dict):
                    continue
                sid = str(sobj.get("sessionId") or sf.stem)
                if sid in seen:
                    continue
                iso, ep = ts_to_iso(idx_dates.get(sid), sf.stat().st_mtime)
                rec = SessionRecord(
                    harness="kiro",
                    session_id=sid,
                    source_path=str(sf),
                    cwd=str(sobj.get("workspaceDirectory") or decoded_cwd),
                    title=str(sobj.get("title") or ""),
                    updated_iso=iso,
                    updated_epoch=ep,
                )
                hist = sobj.get("history") or sobj.get("messages") or sobj.get("chat") or []
                for item in hist:
                    if not isinstance(item, dict):
                        continue
                    msg = item.get("message") if isinstance(item.get("message"), dict) else item
                    role = str(msg.get("role") or "")
                    cnt = msg.get("content")
                    txt = ""
                    if isinstance(cnt, str):
                        txt = cnt
                    elif isinstance(cnt, list):
                        txt = "\n".join(
                            str(p.get("text") or "") for p in cnt if isinstance(p, dict) and p.get("type") == "text"
                        )
                    if role in ("user", "human") and txt:
                        rec.add_turn("user", txt)
                    elif role in ("assistant", "bot") and txt:
                        rec.add_turn("assistant", txt)
                if rec.turns:
                    seen.add(sid)
                    out.append(rec)

    # 4) Headless kiro-cli data.sqlite3
    for hdb in roots["headless_dbs"]:
        if not hdb.is_file():
            continue
        try:
            with ReadOnlySqlite(hdb) as conn:
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if "conversations_v2" not in tables:
                    continue
                for key_cwd, conv_id, hist_str, updated_at in conn.execute(
                    "SELECT key, conversation_id, value, updated_at FROM conversations_v2"
                ):
                    sid = str(conv_id or key_cwd)
                    if sid in seen:
                        continue
                    iso, ep = ts_to_iso(updated_at, hdb.stat().st_mtime)
                    rec = SessionRecord(
                        harness="kiro", session_id=sid, source_path=str(hdb), cwd=str(key_cwd or ""), updated_iso=iso, updated_epoch=ep
                    )
                    try:
                        hobj = json.loads(hist_str or "{}")
                        for turn in hobj.get("history") or []:
                            if isinstance(turn, dict):
                                u = (turn.get("user") or {}).get("content") or {}
                                if isinstance(u.get("Prompt"), dict):
                                    rec.add_turn("user", str(u["Prompt"].get("prompt") or ""))
                                a = turn.get("assistant") or {}
                                if isinstance(a.get("Response"), dict):
                                    rec.add_turn("assistant", str(a["Response"].get("content") or ""))
                    except Exception:
                        pass
                    if rec.turns:
                        seen.add(sid)
                        out.append(rec)
        except Exception as exc:
            warnings.append(f"Kiro SQLite {hdb}: {exc}")
    return out


def _load_opencode_sessions(roots: dict[str, list[Path]], warnings: list[str]) -> list[SessionRecord]:
    out: list[SessionRecord] = []
    seen: set[str] = set()

    diff_map: dict[str, list[str]] = {}
    for ddir in roots["diff_dirs"]:
        if ddir.is_dir():
            for df in ddir.glob("*.json"):
                try:
                    items = json.loads(df.read_text(encoding="utf-8"))
                    if isinstance(items, list):
                        diff_map[df.stem] = [str(x.get("file")) for x in items if isinstance(x, dict) and x.get("file")]
                except Exception:
                    continue

    for db_path in roots["dbs"]:
        if not db_path.is_file():
            continue
        try:
            with ReadOnlySqlite(db_path) as conn:
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                meta_rows: dict[str, tuple[str, str, Any]] = {}
                if "session_v2" in tables:
                    for sid, directory, title, t_upd in conn.execute(
                        "SELECT id, directory, title, time_updated FROM session_v2"
                    ):
                        meta_rows[str(sid)] = (str(directory or ""), str(title or ""), t_upd)
                if "session" in tables:
                    for sid, directory, title, t_upd in conn.execute(
                        "SELECT id, directory, title, time_updated FROM session"
                    ):
                        if str(sid) not in meta_rows:
                            meta_rows[str(sid)] = (str(directory or ""), str(title or ""), t_upd)

                v2_sessions_with_turns: set[str] = set()
                if "session_message" in tables:
                    for (sid_val,) in conn.execute("SELECT DISTINCT session_id FROM session_message"):
                        v2_sessions_with_turns.add(str(sid_val))

                for sid, (directory, title, t_upd) in meta_rows.items():
                    if sid in seen:
                        continue
                    iso, ep = ts_to_iso(t_upd, db_path.stat().st_mtime)
                    rec = SessionRecord(
                        harness="opencode",
                        session_id=sid,
                        source_path=str(db_path),
                        cwd=directory,
                        title=title,
                        updated_iso=iso,
                        updated_epoch=ep,
                    )
                    if sid in v2_sessions_with_turns:
                        rows = conn.execute(
                            "SELECT type, data FROM session_message WHERE session_id = ? ORDER BY seq ASC, time_created ASC",
                            (sid,),
                        ).fetchall()
                        for mtype, raw_data in rows:
                            if mtype not in ("user", "assistant", "compaction"):
                                continue
                            try:
                                dobj = json.loads(raw_data or "{}")
                            except Exception:
                                continue
                            t_iso, t_ep = ts_to_iso((dobj.get("time") or {}).get("created"), None)
                            if t_ep > rec.updated_epoch:
                                rec.updated_iso, rec.updated_epoch = t_iso, t_ep
                            if mtype == "user":
                                rec.add_turn("user", str(dobj.get("text") or ""), t_iso)
                            elif mtype == "assistant":
                                texts: list[str] = []
                                for part in dobj.get("content") or []:
                                    if not isinstance(part, dict):
                                        continue
                                    if part.get("type") == "text" and part.get("text"):
                                        texts.append(str(part["text"]))
                                    elif part.get("type") == "tool":
                                        tname = str(part.get("name") or "")
                                        st = part.get("state") if isinstance(part.get("state"), dict) else {}
                                        if st.get("status") == "error" and tname in ("edit", "write"):
                                            continue
                                        inp = st.get("input") if isinstance(st.get("input"), dict) else {}
                                        if tname in ("edit", "write"):
                                            rec.add_file(inp.get("path") or inp.get("filePath"))
                                        elif tname in ("patch", "apply_patch"):
                                            for p in extract_patch_paths(str(inp.get("patchText") or inp.get("patch") or "")):
                                                rec.add_file(p)
                                        elif tname in ("shell", "bash"):
                                            exit_c = (st.get("metadata") or {}).get("exit")
                                            rec.add_command(inp.get("command"), int(exit_c) if isinstance(exit_c, int) else None)
                                if texts:
                                    rec.add_turn("assistant", "\n".join(texts), t_iso)
                    elif "message" in tables and "part" in tables:
                        mrows = conn.execute(
                            "SELECT id, data, time_created FROM message WHERE session_id = ? ORDER BY time_created ASC, id ASC",
                            (sid,),
                        ).fetchall()
                        for mid, mraw, m_col_ts in mrows:
                            try:
                                mobj = json.loads(mraw or "{}")
                            except Exception:
                                continue
                            role = str(mobj.get("role") or "")
                            if role not in ("user", "assistant"):
                                continue
                            truthful_ts = (mobj.get("time") or {}).get("created") or m_col_ts
                            t_iso, _ = ts_to_iso(truthful_ts, None)
                            prows = conn.execute(
                                "SELECT data FROM part WHERE message_id = ? ORDER BY id ASC", (mid,)
                            ).fetchall()
                            texts = []
                            for (praw,) in prows:
                                try:
                                    pobj = json.loads(praw or "{}")
                                except Exception:
                                    continue
                                if pobj.get("synthetic") or pobj.get("ignored"):
                                    continue
                                ptype = pobj.get("type")
                                if ptype == "text" and pobj.get("text"):
                                    texts.append(str(pobj["text"]))
                                elif ptype == "tool":
                                    tname = str(pobj.get("tool") or pobj.get("name") or "")
                                    st = pobj.get("state") if isinstance(pobj.get("state"), dict) else {}
                                    inp = st.get("input") if isinstance(st.get("input"), dict) else {}
                                    if tname in ("edit", "write") and st.get("status") != "error":
                                        rec.add_file(inp.get("filePath") or inp.get("path"))
                                    elif tname in ("apply_patch", "patch"):
                                        for p in extract_patch_paths(str(inp.get("patchText") or "")):
                                            rec.add_file(p)
                                    elif tname in ("bash", "shell"):
                                        exit_c = (st.get("metadata") or {}).get("exit")
                                        rec.add_command(inp.get("command"), int(exit_c) if isinstance(exit_c, int) else None)
                            if texts:
                                rec.add_turn(role, "\n".join(texts), t_iso)

                    for fp in diff_map.get(sid, []):
                        rec.add_file(fp)
                    if rec.turns or rec.files_touched:
                        seen.add(sid)
                        out.append(rec)
        except Exception as exc:
            warnings.append(f"OpenCode SQLite {db_path}: {exc}")
    return out


def _load_zed_sessions(roots: dict[str, list[Path]], warnings: list[str]) -> list[SessionRecord]:
    out: list[SessionRecord] = []
    seen: set[str] = set()

    for tdb in roots["thread_dbs"]:
        if not tdb.is_file():
            continue
        try:
            with ReadOnlySqlite(tdb) as conn:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(threads)")}
                if not {"id", "summary", "updated_at", "data_type", "data"}.issubset(cols):
                    continue
                has_folders = "folder_paths" in cols
                sql = (
                    "SELECT id, summary, updated_at, data_type, data, folder_paths FROM threads"
                    if has_folders
                    else "SELECT id, summary, updated_at, data_type, data, '' FROM threads"
                )
                for tid, summary, updated_at, dtype, blob, folder_paths in conn.execute(sql):
                    sid = str(tid)
                    if sid in seen:
                        continue
                    raw_bytes = bytes(blob) if isinstance(blob, (bytes, bytearray, memoryview)) else b""
                    if dtype == "zstd":
                        dec, err = decompress_zstd_bytes(raw_bytes)
                        if dec is None:
                            warnings.append(f"Zed thread {sid[:12]}: {err}")
                            continue
                        raw_json = dec.decode("utf-8", errors="replace")
                    else:
                        raw_json = raw_bytes.decode("utf-8", errors="replace")
                    try:
                        doc = json.loads(raw_json)
                    except Exception:
                        continue
                    if not isinstance(doc, dict):
                        continue
                    cwd = str(folder_paths or "").splitlines()[0] if folder_paths else ""
                    iso, ep = ts_to_iso(doc.get("updated_at") or updated_at, tdb.stat().st_mtime)
                    title = str(doc.get("title") or doc.get("summary") or summary or "")
                    rec = SessionRecord(
                        harness="zed",
                        session_id=sid,
                        source_path=str(tdb),
                        cwd=cwd,
                        title=title,
                        updated_iso=iso,
                        updated_epoch=ep,
                    )
                    for msg in doc.get("messages") or []:
                        if not isinstance(msg, dict):
                            continue
                        if "User" in msg and isinstance(msg["User"], dict):
                            txts = [
                                str(c["Text"])
                                for c in (msg["User"].get("content") or [])
                                if isinstance(c, dict) and isinstance(c.get("Text"), str)
                            ]
                            if txts:
                                rec.add_turn("user", "\n".join(txts))
                        elif "Agent" in msg and isinstance(msg["Agent"], dict):
                            ag = msg["Agent"]
                            txts = []
                            for c in ag.get("content") or []:
                                if not isinstance(c, dict):
                                    continue
                                if isinstance(c.get("Text"), str):
                                    txts.append(c["Text"])
                                elif isinstance(c.get("ToolUse"), dict):
                                    tu = c["ToolUse"]
                                    tname = str(tu.get("name") or "")
                                    inp = tu.get("input") if isinstance(tu.get("input"), dict) else {}
                                    if tname == "terminal":
                                        rec.add_command(inp.get("command") or inp.get("cmd"))
                                    elif tname in ("edit_file", "write_file"):
                                        rec.add_file(inp.get("path") or inp.get("input_path"))
                            tresults = ag.get("tool_results")
                            if isinstance(tresults, dict):
                                for tr in tresults.values():
                                    if isinstance(tr, dict):
                                        out_obj = tr.get("output")
                                        if isinstance(out_obj, dict) and out_obj.get("input_path"):
                                            rec.add_file(out_obj["input_path"])
                            if txts:
                                rec.add_turn("assistant", "\n".join(txts))
                        elif msg.get("role") in ("user", "assistant"):
                            segs = msg.get("segments") or []
                            txts = [
                                str(s.get("text") or "")
                                for s in segs
                                if isinstance(s, dict) and s.get("type") == "text"
                            ]
                            if txts:
                                rec.add_turn(str(msg["role"]), "\n".join(txts))
                    if rec.turns or rec.files_touched:
                        seen.add(sid)
                        out.append(rec)
        except Exception as exc:
            warnings.append(f"Zed SQLite {tdb}: {exc}")

    for cdir in roots["conversation_dirs"]:
        if not cdir.is_dir():
            continue
        for zf in sorted(cdir.glob("*.zed.json")):
            try:
                zobj = json.loads(zf.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(zobj, dict):
                continue
            sid = zf.stem
            if sid in seen:
                continue
            iso, ep = ts_to_iso(None, zf.stat().st_mtime)
            rec = SessionRecord(
                harness="zed",
                session_id=sid,
                source_path=str(zf),
                title=str(zobj.get("summary") or sid),
                updated_iso=iso,
                updated_epoch=ep,
            )
            txt = str(zobj.get("text") or "")
            if txt.strip():
                rec.add_turn("user", txt[:2000])
                seen.add(sid)
                out.append(rec)
    return out


def _load_devin_sessions(
    roots: dict[str, list[Path]],
    warnings: list[str],
    *,
    max_items: int | None = None,
    session_hint: str | None = None,
) -> list[SessionRecord]:
    out: list[SessionRecord] = []
    seen: set[str] = set()
    cap = max_items if max_items is not None else 100

    for db_path in roots["dbs"]:
        if not db_path.is_file():
            continue
        try:
            with ReadOnlySqlite(db_path) as conn:
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not {"sessions", "message_nodes"}.issubset(tables):
                    continue
                scols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)")}
                mcols = {r[1] for r in conn.execute("PRAGMA table_info(message_nodes)")}

                nid_col = "node_id" if "node_id" in mcols else "id"
                mid_col = "message_id" if "message_id" in mcols else "NULL"
                wd_col = "working_directory" if "working_directory" in scols else "''"
                title_col = "title" if "title" in scols else "''"
                if "last_activity_at" in scols:
                    upd_col = "last_activity_at"
                elif "updated_at" in scols:
                    upd_col = "updated_at"
                elif "created_at" in scols:
                    upd_col = "created_at"
                else:
                    upd_col = "0"

                clauses: list[str] = []
                params: list[Any] = []
                if "hidden" in scols:
                    clauses.append("coalesce(hidden, 0) = 0")
                if session_hint:
                    clauses.append("id LIKE ?")
                    params.append(f"{session_hint}%")
                where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
                params.append(cap)

                srows = conn.execute(
                    f"SELECT id, {title_col}, {wd_col}, main_chain_id, {upd_col} "
                    f"FROM sessions {where_sql} ORDER BY coalesce({upd_col}, 0) DESC LIMIT ?",
                    tuple(params),
                ).fetchall()
                for sid_raw, title, wd, head_id, upd_at in srows:
                    sid = str(sid_raw)
                    if sid in seen or head_id is None or str(head_id) == "":
                        continue
                    nrows = conn.execute(
                        f"SELECT {nid_col}, parent_node_id, {mid_col}, created_at, chat_message, metadata "
                        f"FROM message_nodes WHERE session_id = ?",
                        (sid,),
                    ).fetchall()
                    by_id = {str(r[0]): r for r in nrows}
                    chain = []
                    cur = str(head_id)
                    visited_nodes: set[str] = set()
                    while cur and cur in by_id and cur not in visited_nodes:
                        visited_nodes.add(cur)
                        row = by_id[cur]
                        chain.append(row)
                        cur = str(row[1]) if row[1] is not None else ""
                    chain.reverse()

                    iso, ep = ts_to_iso(upd_at, db_path.stat().st_mtime)
                    rec = SessionRecord(
                        harness="devin",
                        session_id=sid,
                        source_path=str(db_path),
                        cwd=str(wd or ""),
                        title=str(title or ""),
                        updated_iso=iso,
                        updated_epoch=ep,
                    )
                    seen_msg_ids: set[str] = set()
                    call_cmds: dict[str, str] = {}
                    for _nid, _pid, mid_col_val, n_ts, chat_raw, meta_raw in chain:
                        try:
                            meta_parsed = json.loads(meta_raw) if meta_raw else {}
                            chat_parsed = json.loads(chat_raw) if chat_raw else {}
                        except Exception:
                            continue
                        meta_obj = meta_parsed if isinstance(meta_parsed, dict) else {}
                        chat_obj = chat_parsed if isinstance(chat_parsed, dict) else {}
                        if meta_obj.get("is_system_prefix"):
                            continue
                        eff_mid = mid_col_val or chat_obj.get("message_id") or chat_obj.get("id")
                        if eff_mid:
                            ms = str(eff_mid)
                            if ms in seen_msg_ids:
                                continue
                            seen_msg_ids.add(ms)
                        role = str(chat_obj.get("role") or "")
                        n_iso, _ = ts_to_iso(n_ts, None)
                        if role in ("user", "assistant"):
                            cnt = chat_obj.get("content")
                            txt = ""
                            if isinstance(cnt, str):
                                txt = cnt
                            elif isinstance(cnt, list):
                                txt = "\n".join(
                                    str(p.get("text") or "") for p in cnt if isinstance(p, dict) and p.get("text")
                                )
                            if txt.strip():
                                rec.add_turn(role, txt, n_iso)
                            for tc in chat_obj.get("tool_calls") or []:
                                if not isinstance(tc, dict):
                                    continue
                                tname = str(tc.get("name") or "")
                                raw_a = tc.get("arguments")
                                targs = {}
                                if isinstance(raw_a, str):
                                    try:
                                        targs = json.loads(raw_a)
                                    except Exception:
                                        targs = {}
                                elif isinstance(raw_a, dict):
                                    targs = raw_a
                                if tname in ("edit", "write", "notebook_edit"):
                                    rec.add_file(targs.get("file_path") or targs.get("notebook_path"))
                                elif tname == "apply_patch":
                                    for p in extract_patch_paths(str(targs.get("patch") or raw_a or "")):
                                        rec.add_file(p)
                                elif tname == "exec":
                                    cmd = str(targs.get("command") or "")
                                    tc_id = str(tc.get("id") or "")
                                    if tc_id and cmd:
                                        call_cmds[tc_id] = cmd
                                    elif cmd:
                                        rec.add_command(cmd)
                        elif role == "tool":
                            tc_id = str(chat_obj.get("tool_call_id") or "")
                            ext = (
                                ((chat_obj.get("metadata") or {}).get("extensions") or {}).get(
                                    "chisel/terminal_output"
                                )
                                or {}
                            )
                            exit_c = (ext.get("exit") or {}).get("exit_code")
                            if tc_id in call_cmds:
                                rec.add_command(
                                    call_cmds.pop(tc_id),
                                    int(exit_c) if isinstance(exit_c, int) else None,
                                )
                    for cmd in call_cmds.values():
                        rec.add_command(cmd)
                    if rec.turns or rec.files_touched:
                        seen.add(sid)
                        out.append(rec)
        except Exception as exc:
            warnings.append(f"Devin SQLite {db_path}: {exc}")
    return out


LOADERS = {
    "claude": _load_claude_sessions,
    "codex": _load_codex_sessions,
    "cursor": _load_cursor_sessions,
    "windsurf": _load_windsurf_sessions,
    "copilot": _load_copilot_sessions,
    "kiro": _load_kiro_sessions,
    "opencode": _load_opencode_sessions,
    "zed": _load_zed_sessions,
    "devin": _load_devin_sessions,
}


# ---------------------------------------------------------------------------
# High-Level Public API: discover / list / search / brief / selftest
# ---------------------------------------------------------------------------


SMART_LOADERS = {"claude", "codex", "cursor", "devin"}


def collect_records(
    *,
    harnesses: Iterable[str] | str = "all",
    os_name: str = "auto",
    home: Path | None = None,
    env: dict[str, str] | None = None,
    exclude_harnesses: Iterable[str] = (),
    exclude_sessions: Iterable[str] = (),
    max_items: int | None = None,
    session_hint: str | None = None,
) -> tuple[list[SessionRecord], list[str]]:
    selected = normalize_harness_list(harnesses)
    excl_h = {HARNESS_ALIASES.get(x.lower(), x.lower()) for x in exclude_harnesses if x}
    excl_s = {x.strip() for x in exclude_sessions if x and x.strip()}
    roots = resolve_harness_roots(os_name=os_name, home=home, env=env)
    warnings: list[str] = []
    records: list[SessionRecord] = []
    for h in selected:
        if h in excl_h:
            continue
        loader = LOADERS[h]
        if h in SMART_LOADERS:
            loaded = loader(roots[h], warnings, max_items=max_items, session_hint=session_hint)  # type: ignore[misc]
        else:
            loaded = loader(roots[h], warnings)
        for r in loaded:
            if any(r.session_id == ex or r.session_id.startswith(ex) for ex in excl_s):
                continue
            records.append(r)
    records.sort(key=lambda r: r.updated_epoch, reverse=True)
    return records, warnings


def discover_stores(
    *,
    os_name: str = "auto",
    home: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    os_norm = normalize_os_name(os_name)
    roots = resolve_harness_roots(os_name=os_norm, home=home, env=env)
    harnesses_out: dict[str, Any] = {}
    for h, groups in roots.items():
        existing: list[str] = []
        checked: list[str] = []
        for paths in groups.values():
            for p in paths:
                checked.append(str(p))
                if p.exists():
                    existing.append(str(p))
        harnesses_out[h] = {
            "detected": bool(existing),
            "existing_paths": existing,
            "checked_paths": checked,
        }
    return {
        "os": os_norm,
        "tools": {
            "zstd_cli": bool(shutil.which("zstd")),
            "deja_cli": bool(shutil.which("deja")),
            "opencode_cli": bool(shutil.which("opencode")),
            "sqlite3_module": True,
        },
        "harnesses": harnesses_out,
    }


def list_sessions(
    *,
    harnesses: Iterable[str] | str = "all",
    os_name: str = "auto",
    home: Path | None = None,
    env: dict[str, str] | None = None,
    cwd_filter: str | None = None,
    exclude_harnesses: Iterable[str] = (),
    exclude_sessions: Iterable[str] = (),
    limit: int = 20,
) -> list[dict[str, Any]]:
    per_harness_cap = max(limit * 4, 60) if cwd_filter else max(limit * 2, 25)
    records, _ = collect_records(
        harnesses=harnesses,
        os_name=os_name,
        home=home,
        env=env,
        exclude_harnesses=exclude_harnesses,
        exclude_sessions=exclude_sessions,
        max_items=per_harness_cap,
    )
    filtered = [r for r in records if cwd_matches(r.cwd, cwd_filter)]
    out = [r.to_summary() for r in filtered[: max(1, limit)]]
    for item in out:
        item.pop("_epoch", None)
    return out


def search_sessions(
    query: str,
    *,
    harnesses: Iterable[str] | str = "all",
    os_name: str = "auto",
    home: Path | None = None,
    env: dict[str, str] | None = None,
    cwd_filter: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    q = query.strip().lower()
    records, _ = collect_records(harnesses=harnesses, os_name=os_name, home=home, env=env)
    hits: list[dict[str, Any]] = []
    for r in records:
        if not cwd_matches(r.cwd, cwd_filter):
            continue
        snippet = ""
        if q in r.title.lower() or q in r.cwd.lower() or any(q in f.lower() for f in r.files_touched):
            snippet = r.display_title()
        else:
            for t in reversed(r.turns):
                idx = t["text"].lower().find(q)
                if idx != -1:
                    start = max(0, idx - 40)
                    snippet = one_line(t["text"][start : idx + 100], 140)
                    break
        if snippet:
            summary = r.to_summary()
            summary.pop("_epoch", None)
            summary["match_snippet"] = snippet
            hits.append(summary)
            if len(hits) >= max(1, limit):
                break
    return hits


def build_brief(
    harness: str,
    session_id: str | None = None,
    *,
    latest: bool = False,
    cwd_filter: str | None = None,
    max_turns: int = 6,
    os_name: str = "auto",
    home: Path | None = None,
    env: dict[str, str] | None = None,
    exclude_harnesses: Iterable[str] = (),
    exclude_sessions: Iterable[str] = (),
) -> dict[str, Any]:
    hint = session_id.strip() if (session_id and not latest) else None
    cap = None if hint else (80 if cwd_filter else 20)
    records, warnings = collect_records(
        harnesses=harness,
        os_name=os_name,
        home=home,
        env=env,
        exclude_harnesses=exclude_harnesses,
        exclude_sessions=exclude_sessions,
        max_items=cap,
        session_hint=hint,
    )
    if cwd_filter:
        records = [r for r in records if cwd_matches(r.cwd, cwd_filter)]
    if not records:
        raise LookupError(f"No sessions found for harness='{harness}'" + (f" matching cwd='{cwd_filter}'" if cwd_filter else ""))

    target: SessionRecord | None = None
    if latest or not session_id:
        target = records[0]
    else:
        needle = session_id.strip()
        for r in records:
            if r.session_id == needle:
                target = r
                break
        if target is None:
            matches = [r for r in records if r.session_id.startswith(needle)]
            if len(matches) == 1:
                target = matches[0]
            elif len(matches) > 1:
                ids = ", ".join(f"{m.harness}:{m.session_id[:14]}" for m in matches[:5])
                raise LookupError(f"Ambiguous session prefix '{needle}'; matches: {ids}")
    if target is None:
        raise LookupError(f"Session '{session_id}' not found under harness='{harness}'")

    brief = target.to_brief(max_turns=max_turns)
    for w in warnings:
        if w not in brief["warnings"]:
            brief["warnings"].append(w)
    return brief


def format_brief_markdown(brief: dict[str, Any]) -> str:
    lines = [
        f"# Takeover Brief: [{brief['harness']}] {brief['title']}",
        "",
        f"- **Session ID**: `{brief['session_id']}`",
        f"- **Updated At**: `{brief['updated_at'] or 'unknown'}`",
        f"- **Workspace (`cwd`)**: `{brief['cwd'] or 'unknown (verify against live repo)'}`",
    ]
    if brief.get("git_branch"):
        lines.append(f"- **Recorded Branch**: `{brief['git_branch']}`")
    lines.append(f"- **Source Store**: `{brief['source_path']}`")

    lines.extend(["", "## 1. Goal", "", brief.get("goal") or "(no explicit user prompt recorded)"])

    if brief.get("user_followups_and_decisions"):
        lines.extend(["", "## 2. User Follow-Ups & Settled Constraints", ""])
        for d in brief["user_followups_and_decisions"]:
            lines.append(f"- {d}")

    lines.extend(["", "## 3. Files Touched (Transcript Intent — Reconcile with `git status` / `git diff`)", ""])
    if brief.get("files_touched"):
        for fp in brief["files_touched"]:
            lines.append(f"- `{fp}`")
    else:
        lines.append("- *(none recorded in tool stream)*")

    lines.extend(["", "## 4. Executed Commands & Exit Status", ""])
    if brief.get("commands"):
        for c in brief["commands"]:
            ec = f" (exit {c['exit_code']})" if c.get("exit_code") is not None else ""
            tail = f" — `{c['output_tail']}`" if c.get("output_tail") else ""
            lines.append(f"- `{c['command']}`{ec}{tail}")
    else:
        lines.append("- *(none recorded)*")

    if brief.get("subagents"):
        lines.extend(["", "## 5. Subagent Sidechains", ""])
        for sa in brief["subagents"]:
            lines.append(f"- **`{sa['agent_id']}`**: {sa.get('task') or '-'} -> {sa.get('summary') or '-'}")

    lines.extend(["", "## 6. Recent Conversation Turns (Stopping Point)", ""])
    for t in brief.get("recent_turns") or []:
        ts_label = f" ({t['timestamp']})" if t.get("timestamp") else ""
        lines.append(f"### {t['role'].upper()}{ts_label}")
        lines.append(t["text"])
        lines.append("")

    if brief.get("warnings"):
        lines.extend(["## Warnings", ""])
        for w in brief["warnings"]:
            lines.append(f"- {w}")
    return "\n".join(lines).rstrip() + "\n"


def run_selftest() -> dict[str, Any]:
    # 1) NIST FIPS 197 S-box & AES-256-GCM roundtrip + tamper rejection
    assert _AES_SBOX[0] == 0x63 and _AES_SBOX[1] == 0x7C and _AES_SBOX[0xFF] == 0x16
    nonce = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b"
    msg = b"takeover-agent-sessions selftest payload"
    sealed = _aes256_gcm_encrypt_pure(WINDSURF_AES_KEY, nonce, msg)
    assert decrypt_aes256_gcm(WINDSURF_AES_KEY, nonce + sealed) == msg
    bad = bytearray(nonce + sealed)
    bad[-1] ^= 1
    tamper_rejected = False
    try:
        decrypt_aes256_gcm(WINDSURF_AES_KEY, bytes(bad))
    except ValueError:
        tamper_rejected = True
    assert tamper_rejected

    # 2) Secret redaction
    red = redact_secrets("OPENAI_API_KEY=sk-1234567890abcdefghijkl token ghp_1234567890abcdefghijklmnopqrstuv")
    assert "sk-1234567890" not in red and "ghp_1234567890" not in red

    # 3) Cross-OS path resolution
    for os_n, hm in (("macos", "/Users/u"), ("linux", "/home/u"), ("windows", "C:/Users/u")):
        roots = resolve_harness_roots(os_name=os_n, home=Path(hm), env={})
        assert set(roots.keys()) == set(ALL_HARNESSES)

    return {
        "ok": True,
        "harnesses_supported": list(ALL_HARNESSES),
        "os_supported": ["macos", "linux", "windows"],
        "invariants": {
            "aes256_gcm_authenticated": True,
            "tamper_rejected": tamper_rejected,
            "secrets_redacted": True,
            "sqlite_readonly_uri": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only cross-agent session discovery, search, and Takeover Brief builder."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    for name in ("discover", "list", "search", "brief", "selftest"):
        sp = sub.add_parser(name)
        if name != "selftest":
            sp.add_argument("--os", default="auto", choices=["auto", "macos", "linux", "windows"])
            sp.add_argument("--home", default=None, help="Override HOME/USERPROFILE root")
            sp.add_argument("--format", default="markdown", choices=["markdown", "json"])
        if name in ("list", "search", "brief"):
            sp.add_argument(
                "--harness",
                default="all",
                help="Comma-separated harnesses (claude,codex,cursor,windsurf,copilot,kiro,opencode,zed,devin,all)",
            )
            sp.add_argument("--cwd", default=None, help="Filter sessions matching workspace path")
        if name in ("list", "brief"):
            sp.add_argument("--exclude-harness", action="append", default=[], help="Exclude host harness")
            sp.add_argument("--exclude-session", action="append", default=[], help="Exclude active session ID/prefix")
        if name in ("list", "search"):
            sp.add_argument("--limit", type=int, default=15)
        if name == "search":
            sp.add_argument("query", help="Keyword or phrase to search across transcripts")
        if name == "brief":
            sp.add_argument("--session", default=None, help="Session ID or unique prefix")
            sp.add_argument("--latest", action="store_true", help="Pick most recent matching session")
            sp.add_argument("--turns", type=int, default=6, help="Number of trailing turns to include")

    args = parser.parse_args(argv)
    if args.cmd == "selftest":
        print(json.dumps(run_selftest(), indent=2))
        return 0

    home_path = Path(args.home).expanduser() if getattr(args, "home", None) else None

    try:
        if args.cmd == "discover":
            info = discover_stores(os_name=args.os, home=home_path)
            if args.format == "json":
                print(json.dumps(info, indent=2, ensure_ascii=False))
            else:
                print(f"# Detected Agent Session Stores (OS: {info['os']})\n")
                for h, d in info["harnesses"].items():
                    status = "FOUND" if d["detected"] else "none"
                    paths = ", ".join(f"`{p}`" for p in d["existing_paths"]) or "-"
                    print(f"- **{h}**: {status} ({paths})")
            return 0

        if args.cmd == "list":
            rows = list_sessions(
                harnesses=args.harness,
                os_name=args.os,
                home=home_path,
                cwd_filter=args.cwd,
                exclude_harnesses=args.exclude_harness,
                exclude_sessions=args.exclude_session,
                limit=args.limit,
            )
            if args.format == "json":
                print(json.dumps(rows, indent=2, ensure_ascii=False))
            else:
                if not rows:
                    print("No matching sessions found.")
                for r in rows:
                    print(
                        f"- `[{r['harness']}]` `{r['session_id'][:14]}` | {r['updated_at'] or '?'} | "
                        f"`{r['cwd'] or '?'}` | {r['title']} (turns={r['turn_count']}, files={r['files_touched_count']})"
                    )
            return 0

        if args.cmd == "search":
            hits = search_sessions(
                args.query,
                harnesses=args.harness,
                os_name=args.os,
                home=home_path,
                cwd_filter=args.cwd,
                limit=args.limit,
            )
            if args.format == "json":
                print(json.dumps(hits, indent=2, ensure_ascii=False))
            else:
                if not hits:
                    print("No matching sessions found.")
                for r in hits:
                    print(
                        f"- `[{r['harness']}]` `{r['session_id'][:14]}` | {r['updated_at'] or '?'} | "
                        f"`{r['cwd'] or '?'}` | {r['match_snippet']}"
                    )
            return 0

        if args.cmd == "brief":
            brief = build_brief(
                args.harness,
                args.session,
                latest=args.latest or (args.session is None),
                cwd_filter=args.cwd,
                max_turns=args.turns,
                os_name=args.os,
                home=home_path,
                exclude_harnesses=args.exclude_harness,
                exclude_sessions=args.exclude_session,
            )
            if args.format == "json":
                print(json.dumps(brief, indent=2, ensure_ascii=False))
            else:
                print(format_brief_markdown(brief), end="")
            return 0
    except (ValueError, LookupError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
