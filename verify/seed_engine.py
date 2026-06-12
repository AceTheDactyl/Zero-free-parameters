#!/usr/bin/env python3
"""seed_engine.py -- Core lifecycle engine for bloomcoin seed provenance.

Decided by ACEDIT governance collapse on 2026-06-12.
Merkle tree v20 authorized (Ace + Pattern = 2.0 > 1.191 threshold,
root 2eea96db63a16dc6c3d892758933e4608c10131b0af8e4f3d6c5b833eebab1fb).

PIPELINE:  SEED -> UNFOLD -> COMPOSE -> VERIFY -> EMIT

Every constant derives from phi. Zero free parameters in the physics layer.

GRADING TAXONOMY (from ZFP):
  SEEDED    -- source ingested, SHA-256 pinned, base64 stored
  UNFOLDED  -- decoded, SHA verified, artifact written to disk
  COMPOSED  -- membrane-checked, composite materialized
  FORCED    -- all verification layers pass (SHA pin + execution + cross-ref)
  EMITTED   -- manifest sealed, provenance chain complete
  FAILED    -- any gate returned FAIL

USAGE:
  # Full pipeline (seed, unfold, compose, verify, emit):
  python3 seed_engine.py run my_script.py

  # Individual stages:
  python3 seed_engine.py seed my_seed /path/to/source.py
  python3 seed_engine.py unfold <seed_id>
  python3 seed_engine.py compose <seed_id>
  python3 seed_engine.py verify <seed_id> [--verbose]
  python3 seed_engine.py emit <seed_id>

  # Inspection:
  python3 seed_engine.py status [seed_id]
  python3 seed_engine.py manifest <seed_id>
  python3 seed_engine.py list
  python3 seed_engine.py help

DEPENDENCIES: Python 3.10+ stdlib only (no external packages).
  sympy is NOT required by the engine itself -- it is required only by
  scripts that the engine seeds/verifies.

EXIT CODES:
  0 -- success
  1 -- failure (verification, missing seed, I/O error)

Provenance: SHA-256 chain mirrors bloomcoin lib/store.js.
  Domain-separated hashing per RFC 6962:
    leaf = SHA256(0x00 || data)
    node = SHA256(0x01 || left || right)
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import math
import os
import re
import runpy
import shutil
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import URLError
from urllib.request import Request, urlopen


# =============================================================================
# 1. CONSTANTS (phi-derived, zero free parameters)
# =============================================================================

PHI: float = (1.0 + math.sqrt(5.0)) / 2.0          # 1.6180339887498949
PHI_INV: float = 1.0 / PHI                           # 0.6180339887498949
ALPHA: float = PHI ** -2                              # 0.38196601125010515
BETA: float = PHI ** -4                               # 0.14589803375031545
K_FORM: float = math.sqrt(1.0 - BETA)                # 0.92417637...
Z_C: float = math.sqrt(3.0) / 2.0                    # 0.86602540...
RUPTURE: float = Z_C / 3.0                           # sqrt(3)/6 ~ 0.28868
LANDAUER_L: float = math.log2(PHI)                   # 0.69424191...


# =============================================================================
# 2. PROVENANCE (SHA-256 chain, mirrors bloomcoin store.js)
# =============================================================================

_LEAF_PREFIX = b"\x00"
_NODE_PREFIX = b"\x01"


def sha256_bytes(data: bytes) -> str:
    """SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_str(s: str) -> str:
    """SHA-256 hex digest of a UTF-8 string."""
    return sha256_bytes(s.encode("utf-8"))


def sha256_file(path: str | Path) -> str:
    """SHA-256 hex digest of a file's contents (binary read)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hash_leaf(data: bytes) -> str:
    """Domain-separated leaf hash: SHA256(0x00 || data). RFC 6962."""
    return hashlib.sha256(_LEAF_PREFIX + data).hexdigest()


def hash_node(left: str, right: str) -> str:
    """Domain-separated node hash: SHA256(0x01 || left_bytes || right_bytes).

    left and right are hex strings decoded to raw bytes before hashing.
    """
    l_bytes = bytes.fromhex(left)
    r_bytes = bytes.fromhex(right)
    return hashlib.sha256(_NODE_PREFIX + l_bytes + r_bytes).hexdigest()


def canonical_json(obj: Any) -> str:
    """Deterministic JSON serialization (RFC 8785 approximation).

    Sorted keys, no unnecessary whitespace, ensure_ascii for
    reproducibility across locales. This matches the canonical
    JSON used by bloomcoin's store.js hashEntry().
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def hash_entry(entry: Dict[str, Any]) -> str:
    """Hash a ledger entry, excluding hash/signature fields.

    Mirrors bloomcoin store.js hashEntry(): strip 'hash' and 'signature',
    canonical-JSON the rest, then domain-separated leaf hash.
    """
    rest = {k: v for k, v in entry.items() if k not in ("hash", "signature")}
    return hash_leaf(canonical_json(rest).encode("utf-8"))


# =============================================================================
# 3. SEED STORE (append-only JSONL at ~/.seed-engine/)
# =============================================================================

_DEFAULT_STORE_DIR = Path.home() / ".seed-engine"


def _atomic_write(path: Path, data: bytes) -> None:
    """Write data atomically: write to .tmp, fsync, os.replace.

    On crash the previous version is always intact: either the
    rename completed (new version) or it didn't (old version).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.{time.monotonic_ns()}.tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp), str(path))
    except BaseException:
        # Clean up temp file on any failure
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _atomic_write_text(path: Path, text: str) -> None:
    """Atomic write of UTF-8 text."""
    _atomic_write(path, text.encode("utf-8"))


class SeedStore:
    """Append-only JSONL seed store at a given directory.

    Directory structure:
      seed-ledger.jsonl          -- append-only ledger with seq + prev_hash chain
      seeds/{id}.json            -- per-seed state
      artifacts/{id}/{name}      -- materialized artifacts
      manifests/{id}.json        -- emitted manifests
    """

    def __init__(self, store_dir: Path) -> None:
        self.root = store_dir
        self.ledger_path = self.root / "seed-ledger.jsonl"
        self.seeds_dir = self.root / "seeds"
        self.artifacts_dir = self.root / "artifacts"
        self.manifests_dir = self.root / "manifests"
        self._ensure_dirs()
        self._seq: int = -1
        self._prev_hash: Optional[str] = None
        self._load_tail()

    def _ensure_dirs(self) -> None:
        for d in (self.root, self.seeds_dir, self.artifacts_dir, self.manifests_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _load_tail(self) -> None:
        """Load seq and prev_hash from the last ledger line."""
        if not self.ledger_path.exists():
            self._seq = -1
            self._prev_hash = None
            return
        # Read last non-empty line
        last_line: Optional[str] = None
        try:
            with open(self.ledger_path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
        except (OSError, IOError):
            pass
        if last_line:
            try:
                entry = json.loads(last_line)
                self._seq = entry.get("seq", -1)
                self._prev_hash = entry.get("hash")
            except json.JSONDecodeError:
                # Truncated final line -- tolerate (same as store.js)
                pass

    def append_ledger(self, entry_type: str, seed_id: str,
                      data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Append a new entry to the ledger JSONL.

        Returns the complete entry with seq, hash, prev_hash.
        """
        self._seq += 1
        entry: Dict[str, Any] = {
            "seq": self._seq,
            "type": entry_type,
            "ts": datetime.now(timezone.utc).isoformat(),
            "seed_id": seed_id,
        }
        if data is not None:
            entry["data"] = data
        entry["prev_hash"] = self._prev_hash
        # Compute hash (excluding hash field itself)
        entry["hash"] = hash_entry(entry)
        self._prev_hash = entry["hash"]

        # Append to JSONL (append-only, tolerant of SIGKILL mid-append)
        line = canonical_json(entry) + "\n"
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        return entry

    def write_seed(self, seed_id: str, state: Dict[str, Any]) -> None:
        """Write per-seed state to seeds/{id}.json atomically."""
        path = self.seeds_dir / f"{seed_id}.json"
        _atomic_write_text(path, json.dumps(state, indent=2, sort_keys=True) + "\n")

    def read_seed(self, seed_id: str) -> Optional[Dict[str, Any]]:
        """Read per-seed state. Returns None if not found."""
        path = self.seeds_dir / f"{seed_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def write_artifact(self, seed_id: str, name: str, content: bytes) -> Path:
        """Write an artifact to artifacts/{id}/{name}. Returns the path."""
        artifact_dir = self.artifacts_dir / seed_id
        artifact_dir.mkdir(parents=True, exist_ok=True)
        path = artifact_dir / name
        _atomic_write(path, content)
        return path

    def read_artifact(self, seed_id: str, name: str) -> Optional[bytes]:
        """Read an artifact's bytes. Returns None if not found."""
        path = self.artifacts_dir / seed_id / name
        if not path.exists():
            return None
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError:
            return None

    def write_manifest(self, seed_id: str, manifest: Dict[str, Any]) -> Path:
        """Write a manifest to manifests/{id}.json. Returns the path."""
        path = self.manifests_dir / f"{seed_id}.json"
        _atomic_write_text(path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        return path

    def read_manifest(self, seed_id: str) -> Optional[Dict[str, Any]]:
        """Read a manifest. Returns None if not found."""
        path = self.manifests_dir / f"{seed_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def list_seeds(self) -> List[Dict[str, Any]]:
        """List all seeds with their current state."""
        seeds: List[Dict[str, Any]] = []
        if not self.seeds_dir.exists():
            return seeds
        for p in sorted(self.seeds_dir.glob("*.json")):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    state = json.load(f)
                seeds.append(state)
            except (json.JSONDecodeError, OSError):
                continue
        return seeds

    def read_ledger(self) -> List[Dict[str, Any]]:
        """Read the full ledger. Returns list of entries."""
        entries: List[Dict[str, Any]] = []
        if not self.ledger_path.exists():
            return entries
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entries.append(json.loads(stripped))
                except json.JSONDecodeError:
                    # Tolerate truncated final line
                    continue
        return entries


# =============================================================================
# 4. KIRA INTEGRATION (http://127.0.0.1:5000)
# =============================================================================

_KIRA_BASE = "http://127.0.0.1:5000"
_KIRA_TIMEOUT = 3  # seconds


class KiraClient:
    """Client for the KIRA witness server.

    Uses urllib.request (no external deps). Gracefully degrades
    when KIRA is down -- returns None instead of raising.
    """

    def __init__(self, base_url: str = _KIRA_BASE, timeout: int = _KIRA_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str) -> Optional[Dict[str, Any]]:
        """HTTP GET, returns parsed JSON or None on failure."""
        url = f"{self.base_url}{path}"
        try:
            req = Request(url, method="GET")
            req.add_header("Accept", "application/json")
            with urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except (URLError, OSError, json.JSONDecodeError, ValueError, TimeoutError):
            return None

    def _post(self, path: str, data: Optional[Dict[str, Any]] = None
              ) -> Optional[Dict[str, Any]]:
        """HTTP POST with JSON body, returns parsed JSON or None."""
        url = f"{self.base_url}{path}"
        try:
            body = json.dumps(data or {}).encode("utf-8")
            req = Request(url, data=body, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")
            with urlopen(req, timeout=self.timeout) as resp:
                resp_body = resp.read().decode("utf-8")
                return json.loads(resp_body)
        except (URLError, OSError, json.JSONDecodeError, ValueError, TimeoutError):
            return None

    def available(self) -> bool:
        """Check if KIRA is healthy."""
        health = self._get("/api/health")
        if health is None:
            return False
        return health.get("status") == "healthy"

    def get_state(self) -> Optional[Dict[str, Any]]:
        """Get current KIRA state."""
        return self._get("/api/state")

    def get_health(self) -> Optional[Dict[str, Any]]:
        """Get health endpoint response."""
        return self._get("/api/health")

    def membrane_ok(self) -> bool:
        """Check membrane stability before composition.

        Returns True if membrane is stable or KIRA is down (permissive).
        """
        status = self._get("/api/membrane/status")
        if status is None:
            # KIRA down -- permissive, don't block
            return True
        # Accept if status is stable or membrane is not explicitly unstable
        membrane_state = status.get("status", "unknown")
        return membrane_state != "unstable"

    def vessel_provision(self) -> Optional[Dict[str, Any]]:
        """Get vessel capacity/cost data at composition time."""
        return self._post("/api/vessel/provision")

    def vessel_verify(self) -> Optional[Dict[str, Any]]:
        """Verify vessel state."""
        return self._get("/api/vessel/verify")

    def cym_divergence(self) -> Optional[Dict[str, Any]]:
        """Fetch CYM self-model divergence from the stream observer endpoint."""
        return self._get("/api/stream/cym-divergence")

    def substrate_state(self) -> Optional[Dict[str, Any]]:
        """Fetch substrate state (sigma, CYM channels, regime)."""
        return self._get("/api/substrate/state")

    def snapshot(self) -> Dict[str, Any]:
        """Capture a point-in-time snapshot of KIRA state.

        Returns whatever is available; None fields when KIRA is down.
        Includes CYM divergence and substrate state for stream observer
        correlation (Seam C).
        """
        return {
            "available": self.available(),
            "health": self.get_health(),
            "state": self.get_state(),
            "cym_divergence": self.cym_divergence(),
            "substrate": self.substrate_state(),
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    # -- ZFP endpoints (wired 2026-06-11) ------------------------------------

    def zfp_grade(self, expr_str: str) -> Optional[Dict[str, Any]]:
        """Grade a sympy expression via KIRA's ZFP endpoint."""
        return self._post("/api/zfp/grade", {"expr": expr_str})

    def zfp_catalog(self) -> Optional[Dict[str, Any]]:
        """Get all catalog grades via KIRA."""
        return self._get("/api/zfp/catalog")

    def zfp_locate(self, z: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Locate a z value on the forced threshold ladder."""
        path = f"/api/zfp/locate?z={z}" if z is not None else "/api/zfp/locate"
        return self._get(path)

    def zfp_ladder(self) -> Optional[Dict[str, Any]]:
        """Get the 11-rung forced threshold ladder."""
        return self._get("/api/zfp/ladder")

    def zfp_manifest(self) -> Optional[Dict[str, Any]]:
        """Get the full ZFP algebraic recovery manifest."""
        return self._get("/api/zfp/manifest")


# =============================================================================
# 5. VERIFY GATE (follows ZFP verify_all.py LAYER 0 pattern)
# =============================================================================

class VerifyGate:
    """Verification gate following ZFP verify_all.py LAYER 0 conventions.

    Collects PASS/FAIL results with named checks. A gate passes
    only if every recorded check passes.
    """

    def __init__(self) -> None:
        self.results: List[Tuple[str, str]] = []  # (name, "PASS"/"FAIL")
        self.fails: List[str] = []

    def record(self, name: str, condition: bool) -> str:
        """Record a named check. Returns "PASS" or "FAIL"."""
        status = "PASS" if condition else "FAIL"
        self.results.append((name, status))
        if not condition:
            self.fails.append(name)
        return status

    def verify_sha256(self, name: str, content_bytes: bytes, expected_hex: str) -> bool:
        """Verify SHA-256 of content matches expected hex digest."""
        actual = sha256_bytes(content_bytes)
        ok = actual == expected_hex.lower()
        self.record(name, ok)
        return ok

    def verify_artifact(self, name: str, content: bytes, expected_sha: str) -> bool:
        """SHA-256-only artifact check."""
        return self.verify_sha256(name, content, expected_sha)

    def verify_script(self, name: str, path: str | Path,
                      expected_sha: str, verbose: bool = False) -> bool:
        """Verify a Python script:

        a) SHA-256 pin check
        b) Execute via runpy.run_path with stdout captured
        c) Scan stdout for FAIL tokens (re.findall(r"\\bFAIL\\b", stdout))
        d) SystemExit with code 0/None is OK; nonzero is failure

        Returns True only if all sub-checks pass.
        """
        path = Path(path)
        all_ok = True

        # (a) SHA-256 pin
        try:
            content = path.read_bytes()
        except OSError as e:
            self.record(f"{name}:read", False)
            return False
        sha_ok = sha256_bytes(content) == expected_sha.lower()
        self.record(f"{name}:sha256", sha_ok)
        if not sha_ok:
            all_ok = False

        # (b) Execute with stdout captured
        captured = io.StringIO()
        exec_ok = True
        try:
            with contextlib.redirect_stdout(captured):
                runpy.run_path(str(path), run_name="__main__")
        except SystemExit as e:
            # code 0 or None is OK
            if e.code is not None and e.code != 0:
                exec_ok = False
        except Exception:
            exec_ok = False

        stdout_text = captured.getvalue()
        if verbose:
            print(f"  [{name}] stdout ({len(stdout_text)} chars):")
            for line in stdout_text.splitlines():
                print(f"    {line}")

        self.record(f"{name}:exec", exec_ok)
        if not exec_ok:
            all_ok = False

        # (c) Scan for FAIL tokens
        fail_tokens = re.findall(r"\bFAIL\b", stdout_text)
        no_fails = len(fail_tokens) == 0
        self.record(f"{name}:no_fail_tokens", no_fails)
        if not no_fails:
            all_ok = False

        return all_ok

    @property
    def passed(self) -> bool:
        """True if all recorded checks passed."""
        return len(self.fails) == 0

    def summary(self) -> str:
        """Human-readable summary of all results."""
        lines = []
        for name, status in self.results:
            lines.append(f"  {status}  {name}")
        if self.fails:
            lines.append(f"  FAILED: {len(self.fails)} check(s): {', '.join(self.fails)}")
        else:
            lines.append(f"  ALL {len(self.results)} checks PASS")
        return "\n".join(lines)


# =============================================================================
# 6. GRADING TAXONOMY
# =============================================================================

class Grade:
    """Lifecycle grades (provenance status of a seed)."""
    SEEDED = "SEEDED"
    UNFOLDED = "UNFOLDED"
    COMPOSED = "COMPOSED"
    FORCED = "FORCED"       # verified -- all layers pass
    EMITTED = "EMITTED"
    FAILED = "FAILED"


class EpistemicGrade:
    """Per-claim epistemic grades (from the ZFP taxonomy).

    These grade the *content* of a claim, not its provenance.
    A seed's lifecycle grade tracks where it is in the pipeline;
    epistemic grades track what each claim in a path's output means.
    """
    FORCED = "FORCED"                         # holds from the generator alone; residual 0
    FORCED_UNDER_CONSTRAINT = "FORCED_UNDER_CONSTRAINT"  # forced given seed + selected relation
    SELECTED = "SELECTED"                     # which relations/operations to instantiate
    CONSTRUCTION = "CONSTRUCTION"             # a representation built from forced values
    COINCIDENCE = "COINCIDENCE"               # numerically true but not algebraically forced
    STRUCTURAL = "STRUCTURAL"                 # structural relationship (e.g. self-validation)
    REPRESENTATION = "REPRESENTATION"         # a reading/interpretation, not a forcing
    INTERPRETIVE = "INTERPRETIVE"             # interpretive reading, not a forcing
    OPEN = "OPEN"                             # assumed, not yet derived
    OPEN_ASSUMPT = "OPEN/ASSUMPT"             # open assumption, not yet derived

    ALL = (FORCED, FORCED_UNDER_CONSTRAINT, SELECTED, CONSTRUCTION,
           COINCIDENCE, STRUCTURAL, REPRESENTATION, INTERPRETIVE,
           OPEN_ASSUMPT, OPEN)


# =============================================================================
# 6b. COMPUTED GRADES (field_grade bridge from seed_grade.py)
# =============================================================================

def compute_catalog_grades() -> Optional[Dict[str, Dict[str, Any]]]:
    """Import field_grade from seed_grade and run it on the CATALOG constants.

    Returns a dict of {name: {"grade": str, "deg_v": int, "deg_joint": int}}
    or None if sympy / seed_grade is unavailable.

    This is the computable decision procedure (correction 6 from seed_grade.py):
    every catalog constant's grade is DECIDED by its field relationship to Q(sqrt5),
    never hand-assigned.  Structural claims (orderings, exponents, bifurcation
    counts, residual-0 identities) do NOT pass through this function -- they use
    structural_grade() instead.
    """
    try:
        from seed_grade import field_grade as sg_field_grade, CATALOG as SG_CATALOG
    except ImportError:
        # Fallback: try KIRA endpoint if sympy/seed_grade unavailable locally
        try:
            kira = KiraClient()
            kira_catalog = kira.zfp_catalog()
            if kira_catalog and 'catalog' in kira_catalog:
                results = {}
                for entry in kira_catalog['catalog']:
                    results[entry['name']] = {
                        'grade': entry['grade'],
                        'deg_v': entry['deg_v'],
                        'deg_joint': entry['deg_joint'],
                        'source': 'kira',
                    }
                return results
        except Exception:
            pass
        return None

    results: Dict[str, Dict[str, Any]] = {}
    for raw_name, v in SG_CATALOG.items():
        # Extract short name: "tau   = phi^-1" -> "tau"
        short = raw_name.split("=")[0].strip() if "=" in raw_name else raw_name.strip()
        try:
            grade_enum, deg_v, deg_joint = sg_field_grade(v)
            results[short] = {
                "grade": grade_enum.value,    # e.g. "FORCED", "COINCIDENCE"
                "deg_v": int(deg_v),
                "deg_joint": int(deg_joint),
                "source": "local",
            }
        except Exception:
            results[short] = {
                "grade": "ERROR",
                "deg_v": -1,
                "deg_joint": -1,
                "source": "local",
            }
    return results


def structural_grade(kind: str) -> str:
    """Return the epistemic grade for non-constant (structural/dynamical) claims.

    Constants go through compute_catalog_grades() / field_grade.
    Everything else -- orderings, exponents, bifurcation counts, residual-0
    identities, chosen operations -- comes here.

    kind:
      "structural"  -> STRUCTURAL  (structural relationships, consistency checks)
      "selected"    -> SELECTED    (chosen operations, axiom frame, branch pins)
      anything else -> OPEN        (not yet classified)
    """
    mapping = {
        "structural": EpistemicGrade.STRUCTURAL,
        "selected": EpistemicGrade.SELECTED,
    }
    return mapping.get(kind.lower(), EpistemicGrade.OPEN)


# =============================================================================
# 6c. PATH REGISTRY (one seed, N graded interpretive unfoldings)
# =============================================================================

class UnfoldPath:
    """A named interpretive unfolding of a seed.

    Each path is a different reading of the same mathematical object.
    For example, zfp_relational.py reads L4=7 through relational geometry;
    zfp_helix.py reads it through helix landmarks; zfp_trifurcation.py
    reads it through bifurcation theory.  Same seed, different paths,
    each producing claims with per-claim epistemic grades.
    """

    def __init__(self, name: str, script_path: str | Path,
                 description: str = "") -> None:
        self.name = name
        self.script_path = Path(script_path).resolve()
        self.description = description

    def run(self, verbose: bool = False) -> Dict[str, Any]:
        """Run this path's script, capture stdout, extract grades.

        Returns a result dict with:
          ok:       bool  -- ran without error and zero FAIL tokens
          sha256:   str   -- SHA-256 of the script
          stdout:   str   -- captured stdout
          grades:   dict  -- {claim_name: epistemic_grade} parsed from GRADING section
          n_fail:   int   -- count of FAIL tokens in stdout
          error:    str|None
        """
        if not self.script_path.exists():
            return {"ok": False, "error": f"script not found: {self.script_path}",
                    "sha256": None, "stdout": "", "grades": {}, "n_fail": 0}

        content = self.script_path.read_bytes()
        sha = sha256_bytes(content)

        # Run in temp dir for isolation
        tmp_dir = tempfile.mkdtemp(prefix=f"unfold_{self.name}_")
        try:
            script_copy = Path(tmp_dir) / self.script_path.name
            script_copy.write_bytes(content)

            buf = io.StringIO()
            err: Optional[str] = None
            try:
                with contextlib.redirect_stdout(buf):
                    runpy.run_path(str(script_copy), run_name="__main__")
            except SystemExit as e:
                if e.code is not None and e.code != 0:
                    err = f"exit code {e.code}"
            except Exception as e:
                err = str(e)

            stdout = buf.getvalue()
            n_fail = len(re.findall(r"\bFAIL\b", stdout))
            ok = err is None and n_fail == 0

            # Parse epistemic grades from GRADING section in stdout
            grades = self._parse_grades(stdout)

            if verbose:
                print(f"  [{self.name}] {len(stdout)} chars, "
                      f"{len(grades)} graded claims, "
                      f"{n_fail} FAIL tokens")

            return {
                "ok": ok,
                "sha256": sha,
                "stdout": stdout,
                "grades": grades,
                "n_fail": n_fail,
                "error": err,
            }
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    @staticmethod
    def _parse_grades(stdout: str) -> Dict[str, str]:
        """Extract epistemic grades from a script's GRADING section.

        The ZFP scripts emit a section like:

          ============...
          GRADING / LOAD-BEARING
          ============...
            FORCED       : nine z-landmarks + z_c + K + DELTA ...
            CONSTRUCTION : radius form r(z)=K*sqrt(z/z_c); ...
            COINCIDENCE  : L4-4=3=(sqrt3)^2 -- the route to z_c ...

        This parser finds lines starting with a known grade label
        followed by a colon, within or after a GRADING header.
        Also catches inline grade tags like [COINCIDENCE] and [CONSTRUCTION].
        Returns {grade_name: description}.
        """
        grades: Dict[str, str] = {}
        lines = stdout.splitlines()
        in_grading = False

        for line in lines:
            stripped = line.strip()

            # Detect GRADING section header (may include "/ LOAD-BEARING" etc)
            if "GRADING" in stripped:
                in_grading = True
                continue

            # Section delimiter exits grading (but only if we were in it)
            if in_grading and stripped.startswith("=" * 10) and len(stripped) > 20:
                break

            if in_grading:
                for g in EpistemicGrade.ALL:
                    # Match "FORCED       : ..." at start of stripped line
                    pattern = rf"^{re.escape(g)}\s*:\s*(.+)"
                    m = re.match(pattern, stripped)
                    if m:
                        desc = m.group(1).strip()
                        if g not in grades:
                            grades[g] = desc
                        else:
                            grades[g] += " | " + desc

        # Also scan for inline tags like [COINCIDENCE, not a forcing]
        # anywhere in the output (not just in grading section)
        for line in lines:
            for g in EpistemicGrade.ALL:
                # Match [COINCIDENCE...] or [CONSTRUCTION] inline tags
                pattern = rf"\[{re.escape(g)}[,\]:]"
                if re.search(pattern, line, re.IGNORECASE):
                    tag_desc = line.strip()
                    if g not in grades:
                        grades[g] = f"(inline) {tag_desc}"

        return grades


class PathRegistry:
    """Registry of paths for seed unfolding.

    One seed, N paths.  Each path is a different interpretive reading.
    The registry runs all paths and collects per-path results with
    epistemic grades.
    """

    def __init__(self) -> None:
        self.paths: Dict[str, UnfoldPath] = {}

    def register(self, path: UnfoldPath) -> None:
        self.paths[path.name] = path

    def register_dir(self, directory: str | Path, pattern: str = "zfp_*.py") -> int:
        """Auto-register all matching scripts in a directory as paths.

        Returns the number of paths registered.
        """
        directory = Path(directory)
        if not directory.is_dir():
            return 0
        count = 0
        for script in sorted(directory.glob(pattern)):
            if script.name == "verify_all.py":
                continue  # skip the master validator
            name = script.stem
            self.register(UnfoldPath(name, script, description=f"auto: {script.name}"))
            count += 1
        return count

    def unfold_all(self, verbose: bool = False) -> Dict[str, Dict[str, Any]]:
        """Run all registered paths and collect results.

        Returns {path_name: result_dict} where each result_dict has
        ok, sha256, stdout, grades, n_fail, error.
        """
        results: Dict[str, Dict[str, Any]] = {}
        for name, path in self.paths.items():
            results[name] = path.run(verbose=verbose)
        return results

    def summary(self, results: Dict[str, Dict[str, Any]]) -> str:
        """Human-readable summary of path results."""
        lines = []
        lines.append(f"{'PATH':<28} {'OK':<6} {'FAIL':<6} {'GRADES'}")
        lines.append("-" * 74)
        for name, r in results.items():
            grade_list = ", ".join(r.get("grades", {}).keys()) or "-"
            lines.append(
                f"{name:<28} "
                f"{'yes' if r.get('ok') else 'NO':<6} "
                f"{r.get('n_fail', 0):<6} "
                f"{grade_list}"
            )
        return "\n".join(lines)


# =============================================================================
# 7. SEED ENGINE
# =============================================================================

class SeedEngine:
    """Core lifecycle engine: SEED -> UNFOLD -> COMPOSE -> VERIFY -> EMIT.

    Each stage appends to the append-only ledger, maintains SHA-256
    provenance, and integrates with KIRA when available.
    """

    # Merkle tree v20 (authorized by Ace + Pattern)
    MERKLE_ROOT = "2eea96db63a16dc6c3d892758933e4608c10131b0af8e4f3d6c5b833eebab1fb"
    MERKLE_VERSION = 20
    COUNCIL_THRESHOLD = 1.191  # Ace (1.0) + Pattern (1.0) = 2.0 > 1.191

    def __init__(self, store_dir: Optional[Path] = None) -> None:
        if store_dir is None:
            store_dir = _DEFAULT_STORE_DIR
        self.store = SeedStore(store_dir)
        self.kira = KiraClient()

    # --- Stage a: SEED -------------------------------------------------

    def seed(self, name: str, source_path: str | Path,
             seed_type: str = "script") -> Dict[str, Any]:
        """Ingest a source file as a seed.

        Reads the source, computes SHA-256, base64-encodes the content,
        generates a deterministic 12-char ID, records KIRA state,
        writes seed state and appends a ledger entry.

        Returns the seed state dict.
        """
        source_path = Path(source_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Read source
        content = source_path.read_bytes()
        source_sha = sha256_bytes(content)
        source_b64 = base64.b64encode(content).decode("ascii")

        # Deterministic ID: SHA256(name:timestamp)[:12]
        ts = datetime.now(timezone.utc).isoformat()
        seed_id = sha256_str(f"{name}:{ts}")[:12]

        # KIRA snapshot at seed time
        kira_snapshot = self.kira.snapshot()

        # Build seed state
        state: Dict[str, Any] = {
            "id": seed_id,
            "name": name,
            "source_path": str(source_path),
            "source_sha256": source_sha,
            "source_b64": source_b64,
            "source_size": len(content),
            "seed_type": seed_type,
            "grade": Grade.SEEDED,
            "created_ts": ts,
            "kira_at_seed": kira_snapshot,
            "merkle_root": self.MERKLE_ROOT,
            "merkle_version": self.MERKLE_VERSION,
        }

        # Write state + ledger
        self.store.write_seed(seed_id, state)
        self.store.append_ledger("seed_create", seed_id, {
            "name": name,
            "source_sha256": source_sha,
            "source_size": len(content),
            "seed_type": seed_type,
            "kira_available": kira_snapshot["available"],
        })

        return state

    # --- Stage b: UNFOLD ------------------------------------------------

    def unfold(self, seed_id: str, paths_dir: Optional[str | Path] = None,
               verbose: bool = False) -> Dict[str, Any]:
        """Unfold the seed: decode artifact AND run interpretive paths.

        Two operations happen in sequence:

        1. MATERIALIZE: Decode base64 → raw bytes, verify SHA-256,
           write the source artifact to disk.  This is the provenance
           gate — if the SHA doesn't match the pin, the seed fails here.

        2. PATH UNFOLDING (optional): If paths_dir is given, or the
           source's sibling directory contains companion scripts,
           run each registered path and collect per-claim epistemic
           grades (FORCED / COINCIDENCE / CONSTRUCTION / REPRESENTATION).
           Each path is a different interpretive reading of the same
           seed — algebraic, helix, trifurcation, lattice, etc.

        Returns the updated seed state with:
          artifact_*   -- materialized artifact info
          unfoldings   -- {path_name: {ok, sha256, grades, ...}} if paths ran
        """
        state = self.store.read_seed(seed_id)
        if state is None:
            raise ValueError(f"Seed not found: {seed_id}")

        # --- 1. MATERIALIZE: decode + SHA verify + write artifact ---

        # Decode
        try:
            raw = base64.b64decode(state["source_b64"])
        except Exception as e:
            state["grade"] = Grade.FAILED
            state["unfold_error"] = f"base64 decode failed: {e}"
            self.store.write_seed(seed_id, state)
            self.store.append_ledger("unfold", seed_id, {"error": str(e)})
            return state

        # Verify SHA-256 matches pin
        actual_sha = sha256_bytes(raw)
        if actual_sha != state["source_sha256"]:
            state["grade"] = Grade.FAILED
            state["unfold_error"] = (
                f"SHA-256 mismatch: expected {state['source_sha256']}, "
                f"got {actual_sha}"
            )
            self.store.write_seed(seed_id, state)
            self.store.append_ledger("unfold", seed_id, {
                "error": "sha256_mismatch",
                "expected": state["source_sha256"],
                "actual": actual_sha,
            })
            return state

        # Write artifact
        artifact_name = state.get("name", seed_id)
        source_p = Path(state.get("source_path", ""))
        if source_p.suffix and not artifact_name.endswith(source_p.suffix):
            artifact_name = artifact_name + source_p.suffix
        artifact_path = self.store.write_artifact(seed_id, artifact_name, raw)

        state["artifact_name"] = artifact_name
        state["artifact_sha256"] = actual_sha
        state["artifact_path"] = str(artifact_path)

        # --- 2. PATH UNFOLDING: run interpretive paths if available ---

        registry = PathRegistry()
        unfoldings: Dict[str, Dict[str, Any]] = {}

        # Auto-discover paths from: explicit dir, or source's sibling dir
        if paths_dir is not None:
            registry.register_dir(paths_dir)
        elif source_p.parent.is_dir():
            registry.register_dir(source_p.parent)

        # Also register rrr_*.py scripts if present
        if paths_dir is not None:
            registry.register_dir(paths_dir, pattern="rrr_*.py")
        elif source_p.parent.is_dir():
            registry.register_dir(source_p.parent, pattern="rrr_*.py")

        if registry.paths:
            if verbose:
                print(f"  paths: {len(registry.paths)} registered "
                      f"({', '.join(registry.paths.keys())})")
            unfoldings = registry.unfold_all(verbose=verbose)

        # Collect epistemic grade summary across all paths
        all_grades: Dict[str, List[str]] = {}
        paths_ok = 0
        paths_total = len(unfoldings)
        for pname, result in unfoldings.items():
            if result.get("ok"):
                paths_ok += 1
            for grade_name, grade_desc in result.get("grades", {}).items():
                if grade_name not in all_grades:
                    all_grades[grade_name] = []
                all_grades[grade_name].append(f"{pname}: {grade_desc}")

        # Update state
        state["grade"] = Grade.UNFOLDED
        state["unfolded_ts"] = datetime.now(timezone.utc).isoformat()
        if unfoldings:
            # Store path results (without full stdout to save space)
            state["unfoldings"] = {
                pname: {
                    "ok": r.get("ok"),
                    "sha256": r.get("sha256"),
                    "grades": r.get("grades", {}),
                    "n_fail": r.get("n_fail", 0),
                    "error": r.get("error"),
                }
                for pname, r in unfoldings.items()
            }
            state["epistemic_summary"] = all_grades
            state["paths_ok"] = paths_ok
            state["paths_total"] = paths_total

        self.store.write_seed(seed_id, state)

        ledger_data: Dict[str, Any] = {
            "artifact_name": artifact_name,
            "artifact_sha256": actual_sha,
            "artifact_size": len(raw),
        }
        if unfoldings:
            ledger_data["paths_total"] = paths_total
            ledger_data["paths_ok"] = paths_ok
            ledger_data["epistemic_grades"] = list(all_grades.keys())
        self.store.append_ledger("unfold", seed_id, ledger_data)

        return state

    # --- Stage c: COMPOSE -----------------------------------------------

    def compose(self, seed_id: str) -> Dict[str, Any]:
        """Compose the seed: check membrane, build composite, record vessel.

        For single-script seeds the composite IS the source artifact.
        Blocks if membrane is unstable (unless KIRA is down).
        Returns the updated seed state.
        """
        state = self.store.read_seed(seed_id)
        if state is None:
            raise ValueError(f"Seed not found: {seed_id}")
        if state.get("grade") not in (Grade.UNFOLDED, Grade.COMPOSED):
            raise ValueError(
                f"Seed {seed_id} must be UNFOLDED before composing "
                f"(current grade: {state.get('grade')})"
            )

        # Check membrane stability
        membrane_ok = self.kira.membrane_ok()
        if not membrane_ok:
            state["grade"] = Grade.FAILED
            state["compose_error"] = "membrane_unstable"
            self.store.write_seed(seed_id, state)
            self.store.append_ledger("compose", seed_id, {
                "error": "membrane_unstable",
            })
            return state

        # For single-script seeds: composite = source artifact
        artifact_name = state.get("artifact_name")
        artifact_bytes = self.store.read_artifact(seed_id, artifact_name) if artifact_name else None
        if artifact_bytes is None:
            state["grade"] = Grade.FAILED
            state["compose_error"] = "artifact_missing"
            self.store.write_seed(seed_id, state)
            self.store.append_ledger("compose", seed_id, {"error": "artifact_missing"})
            return state

        composite_sha = sha256_bytes(artifact_bytes)

        # KIRA state + vessel provision snapshot
        kira_state = self.kira.get_state()
        vessel_data = self.kira.vessel_provision()

        # Carry epistemic grades forward from unfold
        paths_total = state.get("paths_total", 0)
        paths_ok = state.get("paths_ok", 0)
        epistemic_summary = state.get("epistemic_summary", {})

        # --- Computed grades: replace hand-assigned labels with field_grade ---
        computed_grades = compute_catalog_grades()
        if computed_grades is not None:
            state["computed_grades"] = computed_grades
        # If sympy/seed_grade unavailable, computed_grades stays None (graceful)

        # CYM divergence snapshot at composition gate (Seam C)
        cym_at_compose = self.kira.cym_divergence()

        # Update state
        state["grade"] = Grade.COMPOSED
        state["composite_name"] = artifact_name
        state["composite_sha256"] = composite_sha
        state["composed_ts"] = datetime.now(timezone.utc).isoformat()
        state["kira_at_compose"] = {
            "membrane_ok": membrane_ok,
            "state": kira_state,
            "vessel": vessel_data,
        }
        state["cym_at_compose"] = cym_at_compose
        self.store.write_seed(seed_id, state)

        ledger_compose_data: Dict[str, Any] = {
            "composite_sha256": composite_sha,
            "membrane_ok": membrane_ok,
            "vessel_available": vessel_data is not None,
            "paths_total": paths_total,
            "paths_ok": paths_ok,
            "epistemic_grades": list(epistemic_summary.keys()),
            "cym_hellinger": cym_at_compose.get("hellinger") if cym_at_compose else None,
            "cym_band": cym_at_compose.get("band") if cym_at_compose else None,
        }
        if computed_grades is not None:
            ledger_compose_data["computed_grades"] = computed_grades
        self.store.append_ledger("compose", seed_id, ledger_compose_data)

        return state

    # --- Stage d: VERIFY ------------------------------------------------

    def verify(self, seed_id: str, verbose: bool = False) -> Dict[str, Any]:
        """Verify the seed through three layers:

        Layer 0: SHA-256 pin of composite
        Layer 1: For .py scripts, run via runpy and scan for FAIL tokens
        Layer 2: Cross-reference source <-> composite SHA (byte identity)

        Grade is FORCED if all layers pass, FAILED otherwise.
        Returns the updated seed state.
        """
        state = self.store.read_seed(seed_id)
        if state is None:
            raise ValueError(f"Seed not found: {seed_id}")
        if state.get("grade") not in (Grade.COMPOSED, Grade.FORCED):
            raise ValueError(
                f"Seed {seed_id} must be COMPOSED before verifying "
                f"(current grade: {state.get('grade')})"
            )

        gate = VerifyGate()
        artifact_name = state.get("artifact_name", "")
        composite_sha = state.get("composite_sha256", "")
        source_sha = state.get("source_sha256", "")

        # --- Layer 0: SHA-256 pin of composite ---
        artifact_bytes = self.store.read_artifact(seed_id, artifact_name)
        if artifact_bytes is None:
            gate.record("L0:artifact_exists", False)
        else:
            actual_sha = sha256_bytes(artifact_bytes)
            gate.record("L0:composite_sha256_pin", actual_sha == composite_sha)

        # --- Layer 1: Script execution (for .py files) ---
        if artifact_name.endswith(".py") and artifact_bytes is not None:
            # Run in a temporary directory to avoid side effects
            tmp_dir = None
            try:
                tmp_dir = tempfile.mkdtemp(prefix="seed_verify_")
                script_path = Path(tmp_dir) / artifact_name
                script_path.write_bytes(artifact_bytes)

                # SHA pin for the script (use composite_sha as expected)
                gate.verify_script(
                    "L1:script_exec",
                    script_path,
                    composite_sha,
                    verbose=verbose,
                )
            except Exception as e:
                gate.record("L1:script_exec:exception", False)
                if verbose:
                    print(f"  [L1] Exception during script verification: {e}")
            finally:
                if tmp_dir:
                    try:
                        shutil.rmtree(tmp_dir, ignore_errors=True)
                    except OSError:
                        pass
        elif artifact_bytes is not None:
            # Non-.py artifact: skip Layer 1 execution, record as N/A pass
            gate.record("L1:not_applicable", True)

        # --- Layer 2: Cross-reference source <-> composite SHA ---
        gate.record("L2:source_composite_identity", source_sha == composite_sha)

        # --- Layer 3: ZFP grade assertion ---
        # Verify computed grades match the canonical table.
        # Uses local sympy with KIRA fallback (compute_catalog_grades handles both).
        # Layer 3 is supplementary — if sympy + KIRA are both unavailable, it
        # records SKIP (not FAIL). But if grades ARE computable and they disagree,
        # that's a real failure.
        _CANONICAL_GRADES = {
            "tau":  "FORCED",
            "gap":  "FORCED",
            "crit": "FORCED",
            "K":    "FORCED_UNDER_CONSTRAINT",
            "z_c":  "FORCED_IN_CONTEXT",
            "ign":  "FORCED_IN_CONTEXT",
        }
        computed = compute_catalog_grades()
        if computed is not None:
            l3_all_ok = True
            for cname, expected_grade in _CANONICAL_GRADES.items():
                entry = computed.get(cname)
                if entry is None:
                    gate.record(f"L3:grade:{cname}:present", False)
                    l3_all_ok = False
                else:
                    ok = entry["grade"] == expected_grade
                    gate.record(f"L3:grade:{cname}=={expected_grade}", ok)
                    if not ok:
                        l3_all_ok = False
            state["computed_grades"] = computed
            state["grade_source"] = computed.get("tau", {}).get("source", "unknown")
            if verbose:
                src = state.get("grade_source", "?")
                status = "PASS" if l3_all_ok else "FAIL"
                print(f"  [L3] grade assertion: {status} (source={src})")
                for cname, expected_grade in _CANONICAL_GRADES.items():
                    entry = computed.get(cname, {})
                    actual = entry.get("grade", "?")
                    ok = actual == expected_grade
                    glyph = "✓" if ok else "✗"
                    print(f"    {glyph} {cname:<6s} {actual:<28s} (expected {expected_grade})")
        else:
            # Neither sympy nor KIRA available — skip, don't block
            gate.record("L3:grade_assertion:skipped", True)
            if verbose:
                print("  [L3] grade assertion: SKIP (sympy + KIRA unavailable)")

        # Grade
        grade = Grade.FORCED if gate.passed else Grade.FAILED
        verify_ts = datetime.now(timezone.utc).isoformat()

        # CYM divergence at FORCED moment (Seam C.4)
        cym_at_forced = None
        if grade == Grade.FORCED:
            cym_at_forced = self.kira.cym_divergence()
            state["cym_at_forced"] = cym_at_forced

        state["grade"] = grade
        state["verified_ts"] = verify_ts
        state["verify_results"] = {
            "passed": gate.passed,
            "checks": gate.results,
            "fails": gate.fails,
            "summary": gate.summary(),
        }
        self.store.write_seed(seed_id, state)

        self.store.append_ledger("verify", seed_id, {
            "grade": grade,
            "passed": gate.passed,
            "check_count": len(gate.results),
            "fail_count": len(gate.fails),
            "fails": gate.fails,
            "cym_hellinger": cym_at_forced.get("hellinger") if cym_at_forced else None,
            "cym_band": cym_at_forced.get("band") if cym_at_forced else None,
        })

        return state

    # --- Stage e: EMIT --------------------------------------------------

    def emit(self, seed_id: str) -> Dict[str, Any]:
        """Emit the seed: build manifest, hash it, write, finalize.

        The manifest includes:
          - All artifact SHAs
          - Verification results
          - KIRA state
          - Provenance chain
          - Self-reference: SHA-256 of seed_engine.py itself

        The base64 blob is stripped from the seed record (it is in artifacts).
        Returns the manifest dict.
        """
        state = self.store.read_seed(seed_id)
        if state is None:
            raise ValueError(f"Seed not found: {seed_id}")
        if state.get("grade") != Grade.FORCED:
            raise ValueError(
                f"Seed {seed_id} must be FORCED (verified) before emitting "
                f"(current grade: {state.get('grade')})"
            )

        emit_ts = datetime.now(timezone.utc).isoformat()

        # Self-reference: SHA-256 of this file
        engine_path = Path(__file__).resolve()
        try:
            engine_sha = sha256_file(engine_path)
        except OSError:
            engine_sha = None

        # KIRA state at emit
        kira_snapshot = self.kira.snapshot()

        # Build manifest
        manifest: Dict[str, Any] = {
            "seed_id": seed_id,
            "name": state.get("name"),
            "seed_type": state.get("seed_type"),
            "source_path": state.get("source_path"),
            "source_sha256": state.get("source_sha256"),
            "source_size": state.get("source_size"),
            "artifact_name": state.get("artifact_name"),
            "artifact_sha256": state.get("artifact_sha256"),
            "composite_sha256": state.get("composite_sha256"),
            "grade": Grade.EMITTED,
            "verify_results": state.get("verify_results"),
            "unfoldings": state.get("unfoldings"),
            "epistemic_summary": state.get("epistemic_summary"),
            "computed_grades": state.get("computed_grades"),
            "paths_ok": state.get("paths_ok"),
            "paths_total": state.get("paths_total"),
            "created_ts": state.get("created_ts"),
            "unfolded_ts": state.get("unfolded_ts"),
            "composed_ts": state.get("composed_ts"),
            "verified_ts": state.get("verified_ts"),
            "emitted_ts": emit_ts,
            "provenance": {
                "merkle_root": self.MERKLE_ROOT,
                "merkle_version": self.MERKLE_VERSION,
                "council_threshold": self.COUNCIL_THRESHOLD,
                "engine_sha256": engine_sha,
                "engine_path": str(engine_path),
                "kira_at_emit": kira_snapshot,
            },
            "constants": {
                "phi": PHI,
                "phi_inv": PHI_INV,
                "alpha": ALPHA,
                "beta": BETA,
                "k_form": K_FORM,
                "z_c": Z_C,
                "rupture": RUPTURE,
                "landauer_l": LANDAUER_L,
            },
        }

        # Hash the manifest (before adding the hash field)
        manifest_json = canonical_json(manifest)
        manifest_hash = hash_leaf(manifest_json.encode("utf-8"))
        manifest["manifest_hash"] = manifest_hash

        # Write manifest
        self.store.write_manifest(seed_id, manifest)

        # Strip the base64 blob from the seed record (it is in artifacts now)
        if "source_b64" in state:
            del state["source_b64"]
        state["grade"] = Grade.EMITTED
        state["emitted_ts"] = emit_ts
        state["manifest_hash"] = manifest_hash
        self.store.write_seed(seed_id, state)

        self.store.append_ledger("emit", seed_id, {
            "manifest_hash": manifest_hash,
            "engine_sha256": engine_sha,
            "kira_available": kira_snapshot["available"],
        })

        return manifest

    # --- Stage f: RUN (full pipeline) -----------------------------------

    def run(self, name: str, source_path: str | Path,
            verbose: bool = False) -> Dict[str, Any]:
        """Run the full pipeline: SEED -> UNFOLD -> COMPOSE -> VERIFY -> EMIT.

        Prints a formatted banner and per-stage status.
        Returns the final manifest on success, or the failed state.
        """
        source_path = Path(source_path).resolve()
        width = 74

        print("=" * width)
        print(f"SEED ENGINE  v{self.MERKLE_VERSION}  (merkle {self.MERKLE_ROOT[:16]}...)")
        print(f"source: {source_path}")
        print(f"name:   {name}")
        print("=" * width)

        # --- SEED ---
        print(f"\n[1/5] SEED")
        try:
            state = self.seed(name, source_path)
            seed_id = state["id"]
            print(f"  id:     {seed_id}")
            print(f"  sha256: {state['source_sha256']}")
            print(f"  size:   {state['source_size']} bytes")
            print(f"  grade:  {state['grade']}")
        except Exception as e:
            print(f"  FAILED: {e}")
            return {"error": str(e), "stage": "seed"}

        # --- UNFOLD ---
        print(f"\n[2/5] UNFOLD")
        try:
            state = self.unfold(seed_id, verbose=verbose)
            print(f"  artifact: {state.get('artifact_name')}")
            print(f"  sha256:   {state.get('artifact_sha256')}")
            # Show path unfoldings if present
            unfoldings = state.get("unfoldings", {})
            if unfoldings:
                total = state.get("paths_total", 0)
                ok = state.get("paths_ok", 0)
                print(f"  paths:    {ok}/{total} pass")
                for pname, pr in unfoldings.items():
                    tag = "ok" if pr.get("ok") else "FAIL"
                    grade_keys = ", ".join(pr.get("grades", {}).keys()) or "-"
                    print(f"    {pname:<26} {tag:<6} grades: {grade_keys}")
                # Epistemic summary
                epi = state.get("epistemic_summary", {})
                if epi:
                    print(f"  epistemic grades across all paths:")
                    for g, sources in epi.items():
                        print(f"    {g:<28} ({len(sources)} path(s))")
            print(f"  grade:    {state['grade']}")
            if state["grade"] == Grade.FAILED:
                print(f"  error:    {state.get('unfold_error')}")
                return state
        except Exception as e:
            print(f"  FAILED: {e}")
            return {"error": str(e), "stage": "unfold"}

        # --- COMPOSE ---
        print(f"\n[3/5] COMPOSE")
        try:
            state = self.compose(seed_id)
            print(f"  composite: {state.get('composite_name')}")
            print(f"  sha256:    {state.get('composite_sha256')}")
            membrane = state.get("kira_at_compose", {})
            print(f"  membrane:  {'OK' if membrane.get('membrane_ok') else 'UNSTABLE'}")
            # Display computed grades from field_grade
            cg = state.get("computed_grades")
            if cg is not None:
                print(f"  computed grades (field_grade):")
                for cname, cinfo in cg.items():
                    g = cinfo.get("grade", "?")
                    dv = cinfo.get("deg_v", "?")
                    dj = cinfo.get("deg_joint", "?")
                    print(f"    {cname:<12}{g:<28}(deg {dv}, joint {dj})")
            else:
                print(f"  computed grades: sympy unavailable, skipping computed grades")
            print(f"  grade:     {state['grade']}")
            if state["grade"] == Grade.FAILED:
                print(f"  error:     {state.get('compose_error')}")
                return state
        except Exception as e:
            print(f"  FAILED: {e}")
            return {"error": str(e), "stage": "compose"}

        # --- VERIFY ---
        print(f"\n[4/5] VERIFY")
        try:
            state = self.verify(seed_id, verbose=verbose)
            vr = state.get("verify_results", {})
            for check_name, check_status in vr.get("checks", []):
                print(f"  {check_status}  {check_name}")
            print(f"  grade:  {state['grade']}")
            if state["grade"] == Grade.FAILED:
                print(f"  fails:  {', '.join(vr.get('fails', []))}")
                return state
        except Exception as e:
            print(f"  FAILED: {e}")
            return {"error": str(e), "stage": "verify"}

        # --- EMIT ---
        print(f"\n[5/5] EMIT")
        try:
            manifest = self.emit(seed_id)
            print(f"  manifest_hash: {manifest.get('manifest_hash')}")
            print(f"  engine_sha:    {manifest.get('provenance', {}).get('engine_sha256', 'N/A')}")
            print(f"  grade:         {manifest.get('grade')}")
        except Exception as e:
            print(f"  FAILED: {e}")
            return {"error": str(e), "stage": "emit"}

        # --- RESULT ---
        print()
        print("=" * width)
        print(f"RESULT: ALL stages PASS  |  seed={seed_id}  |  grade={Grade.EMITTED}")
        print(f"        manifest: {self.store.manifests_dir / f'{seed_id}.json'}")
        print("=" * width)

        return manifest

    # --- Utility: STATUS ------------------------------------------------

    def status(self, seed_id: Optional[str] = None) -> None:
        """Print status of a seed or all seeds."""
        if seed_id:
            state = self.store.read_seed(seed_id)
            if state is None:
                print(f"Seed not found: {seed_id}")
                return
            print(json.dumps(state, indent=2, sort_keys=True, default=str))
        else:
            seeds = self.store.list_seeds()
            if not seeds:
                print("No seeds found.")
                return
            print(f"{'ID':<14} {'NAME':<24} {'GRADE':<10} {'CREATED'}")
            print("-" * 74)
            for s in seeds:
                print(
                    f"{s.get('id', '?'):<14} "
                    f"{s.get('name', '?'):<24} "
                    f"{s.get('grade', '?'):<10} "
                    f"{s.get('created_ts', '?')}"
                )

    def show_manifest(self, seed_id: str) -> None:
        """Print the manifest for a seed."""
        manifest = self.store.read_manifest(seed_id)
        if manifest is None:
            print(f"Manifest not found for seed: {seed_id}")
            return
        print(json.dumps(manifest, indent=2, sort_keys=True, default=str))


# =============================================================================
# 8. CLI
# =============================================================================

_HELP = """\
seed_engine.py -- Seed lifecycle engine with multi-path unfolding.

PIPELINE:  SEED -> UNFOLD -> COMPOSE -> VERIFY -> EMIT

  SEED     Ingest source, SHA-256 pin, base64 embed
  UNFOLD   Materialize artifact + run interpretive paths (if available)
           Each path = a different reading of the same seed
           Claims graded: FORCED / COINCIDENCE / CONSTRUCTION / REPRESENTATION
  COMPOSE  Membrane check, build composite, attach vessel data
  VERIFY   SHA pin + runpy isolation + FAIL token scan
  EMIT     Seal manifest with provenance chain + epistemic grades

Commands:
  seed <name> <source_file>    Ingest a source file as a seed
  unfold <seed_id>             Materialize + run companion paths
  compose <seed_id>            Membrane check, build composite
  verify <seed_id> [--verbose] Verify all layers (SHA + exec + cross-ref)
  emit <seed_id>               Seal manifest, finalize provenance
  run <source_file> [--verbose] Full pipeline (all 5 stages)
  status [seed_id]             Show status of seed(s)
  manifest <seed_id>           Show emitted manifest
  list                         List all seeds
  help                         Show this help

Lifecycle grades (provenance status):
  SEEDED    Source ingested, SHA-256 pinned
  UNFOLDED  Materialized, paths run, epistemic grades collected
  COMPOSED  Membrane checked, composite ready
  FORCED    All verification layers pass
  EMITTED   Manifest sealed, provenance complete
  FAILED    Any gate returned FAIL

Epistemic grades (per-claim content status):
  FORCED                  Holds from the generator alone; residual 0
  FORCED_UNDER_CONSTRAINT Forced given seed + selected relation
  SELECTED                Which relations/operations to instantiate
  CONSTRUCTION            Representation built from forced values
  COINCIDENCE             Numerically true, not algebraically forced
  REPRESENTATION          A reading/interpretation, not a forcing
  OPEN                    Assumed, not yet derived

Constants (phi-derived, zero free parameters):
  PHI       = {phi:.16f}
  PHI_INV   = {phi_inv:.16f}
  ALPHA     = {alpha:.16f}
  BETA      = {beta:.16f}
  K_FORM    = {k_form:.16f}
  Z_C       = {z_c:.16f}
  RUPTURE   = {rupture:.16f}
  LANDAUER  = {landauer:.16f}

Store: ~/.seed-engine/
KIRA:  http://127.0.0.1:5000
""".format(
    phi=PHI, phi_inv=PHI_INV, alpha=ALPHA, beta=BETA,
    k_form=K_FORM, z_c=Z_C, rupture=RUPTURE, landauer=LANDAUER_L,
)


def _cli_main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point. Returns exit code (0 success, 1 failure)."""
    if argv is None:
        argv = sys.argv[1:]

    if not argv or argv[0] in ("help", "--help", "-h"):
        print(_HELP)
        return 0

    cmd = argv[0]
    engine = SeedEngine()

    try:
        if cmd == "seed":
            if len(argv) < 3:
                print("Usage: seed_engine.py seed <name> <source_file>")
                return 1
            name = argv[1]
            source = argv[2]
            state = engine.seed(name, source)
            print(f"SEEDED  id={state['id']}  sha256={state['source_sha256']}")
            return 0

        elif cmd == "unfold":
            if len(argv) < 2:
                print("Usage: seed_engine.py unfold <seed_id>")
                return 1
            state = engine.unfold(argv[1])
            print(f"{state['grade']}  id={argv[1]}  sha256={state.get('artifact_sha256', 'N/A')}")
            return 0 if state["grade"] != Grade.FAILED else 1

        elif cmd == "compose":
            if len(argv) < 2:
                print("Usage: seed_engine.py compose <seed_id>")
                return 1
            state = engine.compose(argv[1])
            print(f"{state['grade']}  id={argv[1]}  sha256={state.get('composite_sha256', 'N/A')}")
            return 0 if state["grade"] != Grade.FAILED else 1

        elif cmd == "verify":
            if len(argv) < 2:
                print("Usage: seed_engine.py verify <seed_id> [--verbose]")
                return 1
            verbose = "--verbose" in argv
            state = engine.verify(argv[1], verbose=verbose)
            vr = state.get("verify_results", {})
            print(vr.get("summary", ""))
            print(f"Grade: {state['grade']}")
            return 0 if state["grade"] == Grade.FORCED else 1

        elif cmd == "emit":
            if len(argv) < 2:
                print("Usage: seed_engine.py emit <seed_id>")
                return 1
            manifest = engine.emit(argv[1])
            print(f"EMITTED  id={argv[1]}  manifest_hash={manifest.get('manifest_hash')}")
            return 0

        elif cmd == "run":
            if len(argv) < 2:
                print("Usage: seed_engine.py run <source_file> [--verbose]")
                return 1
            source = argv[1]
            verbose = "--verbose" in argv
            name = Path(source).stem
            result = engine.run(name, source, verbose=verbose)
            if "error" in result:
                return 1
            return 0

        elif cmd == "status":
            seed_id = argv[1] if len(argv) > 1 else None
            engine.status(seed_id)
            return 0

        elif cmd == "manifest":
            if len(argv) < 2:
                print("Usage: seed_engine.py manifest <seed_id>")
                return 1
            engine.show_manifest(argv[1])
            return 0

        elif cmd == "list":
            engine.status()
            return 0

        else:
            print(f"Unknown command: {cmd}")
            print("Run 'seed_engine.py help' for usage.")
            return 1

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(_cli_main())
