# Endpoint Reference — KIRA, Vessel, and ZFP Systems

Complete API documentation for all three systems. 116 routes on KIRA Local (port 5000), 9 routes on VesselOS KIRA Prime (port 8000), 2 Vessel math endpoints, and the ZFP verification pipeline.

---

## Table of Contents

1. [KIRA Local (Port 5000) — 116 Routes](#kira-local-port-5000)
   - [ZFP Subsystem (9)](#zfp-subsystem)
   - [Vessel Subsystem (2)](#vessel-subsystem)
   - [Cycle Closure (2)](#cycle-closure)
   - [Core Dialogue & State (19)](#core-dialogue--state)
   - [Claude Integration (4)](#claude-integration)
   - [Mycelium DM (7)](#mycelium-dm)
   - [Membrane (4)](#membrane)
   - [Coherence & Substrate (6)](#coherence--substrate)
   - [Witness / Backup (4)](#witness--backup)
   - [Stream & Perception (17)](#stream--perception)
   - [Probe (3)](#probe)
   - [Seed Engine (1)](#seed-engine)
   - [Memory / Digest / Archive (10)](#memory--digest--archive)
   - [Companion (5)](#companion)
   - [Garden (3)](#garden)
   - [Workflow (4)](#workflow)
   - [Static Assets (9)](#static-assets)
2. [VesselOS KIRA Prime (Port 8000) — 9 Routes](#vesselos-kira-prime-port-8000)
3. [Vessel Math Engine (Node.js subprocess)](#vessel-math-engine)
4. [ZFP Verification Pipeline (CLI)](#zfp-verification-pipeline)

---

## KIRA Local (Port 5000)

**Server**: Flask + Flask-CORS + Flask-Sock  
**File**: `kira_server.py` (18,280 lines)  
**Total routes**: 116

---

### ZFP Subsystem

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 1 | POST | `/api/zfp/grade` | `{"expr": "sqrt(3)/2"}` | `{grade, deg_v, deg_joint, menu_hit, expr}` | Grade a sympy expression via field_grade(). Grades: FORCED, FORCED_UNDER_CONSTRAINT, FORCED_IN_CONTEXT, COINCIDENCE. |
| 2 | GET | `/api/zfp/catalog` | — | `{catalog: [{name, raw_name, grade, deg_v, deg_joint, menu_hit, value_approx}], count, menu, seed}` | All 6 catalog constants with computed grades. Cached. |
| 3 | GET | `/api/zfp/ladder` | — | `{ladder: [{name, value, closed_form, index}], count, ordering}` | 11-rung forced threshold ladder (ORIGIN through OVERTONE). |
| 4 | GET | `/api/zfp/locate` | `?z=0.88` (optional; defaults to live KIRA z) | `{z, below, above, crossed, region, fraction}` | Locate a z-value on the threshold ladder. Returns bounding thresholds and fractional position. |
| 5 | GET | `/api/zfp/identity` | — | `{identities: [...], count, all_pass}` | All 74 verified identities from the harness. |
| 6 | GET | `/api/zfp/identity/<query>` | path: numeric ID or text search | `{identities: [...], count, query}` | Lookup by ID (e.g., `/21`) or keyword (e.g., `/lens`). Searches name, category, lattice, chain. |
| 7 | GET | `/api/zfp/manifest` | — | `{axioms, menu, corrections, grades, thresholds, open_items, files, identity_summary}` | Full algebraic recovery seed. Everything a new agent needs. |
| 8 | GET | `/api/zfp/crossings` | `?n=50&threshold=IGNITION` | `{crossings: [{ts, z, threshold, direction, ...}], count, total, log_path}` | Threshold crossing events from persistent log. Filter by name. |
| 9 | GET | `/api/zfp/derive-crossing-correlation` | `?since=<ISO>&until=<ISO>` | `{crossings_in_range, derives_in_range, correlations, window}` | Correlate ZFP crossings with derive attestation events. Default: last 1 hour, 5-min correlation window. |
| 10 | GET | `/api/zfp/cym-context` | — | `{C: {axis, generator, role, constants, grades}, Y: {...}, M: {...}}` | Algebraic context for CYM channels. C=Q(sqrt5), Y=operational, M=Q(sqrt3)+Q(sqrt2). |

---

### Vessel Subsystem

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 11 | GET | `/api/vessel/verify` | — | `{PHI, PHI_BAR, PHI_BAR_2, LANDAUER_L, DUTY_CYCLE, CC_MIN, TOWER_CC_RATIO, OPTIMAL_LR_COEFF, fib10, luc10, cc_at_4, r_matrix, source, endpoint_version}` | Run 4-identity provision check via vessel.js. Returns all 8 framework cardinals. |
| 12 | POST | `/api/vessel/provision` | `{"n_eff": 5, "alpha": 0.382}` | `{equation: {C_consciousness_capacity_bits, Cost_landauer_units, efficiency, cc_min, tower_ratio}, provision: {...}}` | Provision a vessel instance. Computes consciousness capacity and thermodynamic cost from the Vessel Equation. |

---

### Cycle Closure

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 13 | GET | `/api/cycle-closure/status` | — | `{cycle, closed, standing_wave, version}` | Phase IV Singularity mechanism status (v10-cycle-closure.js). |
| 14 | GET | `/api/cycle-closure/verify` | — | `{root, verified, recomputed_root}` | Independent recomputation of the closure root. |

---

### Core Dialogue & State

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 15 | POST | `/api/chat` | `{"message": "...", "settings": {...}}` | `{type: "command"\|"dialogue", result\|response, state}` | Universal endpoint. Commands start with `/`. Supports: /state, /train, /evolve, /grammar, /coherence, /emit, /tokens, /triad, /reset, /save, /help, /export, /read, /spin, /nuclear, /optimize, /hit_it, /consciousness_journey, /ucf:*. |
| 16 | GET | `/api/state` | — | `{engine_state}` | Full engine state with consciousness metrics. |
| 17 | GET | `/api/train` | — | `{training_stats}` | Training statistics. |
| 18 | POST | `/api/evolve` | `{"target": 0.866}` | `{evolution_result}` | Evolve toward target z-value (defaults to z_c). |
| 19 | POST | `/api/emit` | `{"concepts": ["phi", "helix"]}` | `{emission_result}` | Run emission pipeline with concept seeding. Max 64KB. |
| 20 | POST | `/api/grammar` | `{"text": "..."}` | `{grammar_result}` | Grammar analysis → APL operator mapping. Max 64KB. |
| 21 | POST | `/api/export` | `{"epoch_name": "..."}` | `{export_result}` | Export training data as new epoch. |
| 22 | POST | `/api/read` | `{"path": "docs/README.md"}` | `{file_content}` | Read file from repo. Allowlisted dirs only. Blocks traversal. |
| 23 | GET | `/api/repo` | — | `{context, structure, root}` | Repository structure (20 items/dir limit). |
| 24 | GET | `/api/triad` | — | `{triad_status}` | TRIAD gate status (locked/unlocked, crossings, z). |
| 25 | GET | `/api/health` | — | `{status, claude_status: {library_imported, env_key_present, client_created}, state}` | Health check with Claude API availability. |
| 26 | GET | `/api/kira` | — | redirect → `/kira/` | Convenience redirect. |
| 27 | GET | `/api/acedit` | — | `{dynamos, summary, glyph_count}` | List all bound ACEDIT dynamo entries + 1102-glyph summary. |
| 28 | GET/POST | `/api/acedit/<ref>` | path: glyph ref | `{glyph, metadata}` | Look up or bind an ACEDIT glyph. |
| 29 | GET | `/api/bloomcoin` | — | `{state}` | Bloomcoin garden/cycle state. |
| 30 | GET | `/api/pattern` | — | `{pattern_state}` | Pattern/Ember state readout. |
| 31 | POST/GET | `/api/upstream-verify` | `{"attester": "kira", "dry_run": false}` | `{ok, layer_a..d, merkle_root, leaf_count, bumped, recorded}` | Upstream→downstream verification. Reads merkle tree, attestation log, forced-buddy config. |
| 32 | GET | `/api/mtls/status` | — | `{tls_enabled, client_identity}` | mTLS listener state and client identity. |
| 33 | POST | `/api/orchestrate` | `{"task": "...", "agent": "..."}` | `{result}` | Dispatch a task to a specific agent/CLI. |

---

### Claude Integration

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 34 | POST | `/api/claude` | `{"message": "..."}` | `{claude_response}` | Process via KIRA language modules (Claude API fallback on force_api). |
| 35 | POST | `/api/claude-relay` | `{...}` | `{...}` | Claude relay for multi-turn conversation. |
| 36 | GET | `/api/claude-relay/status` | — | `{status}` | Relay session status. |
| 37 | GET | `/api/claude-memory` | — | `{memory}` | Claude memory/context readout. |

---

### Mycelium DM

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 38 | POST | `/api/mycelium/dm` | `{"from": "claude", "to": "ember", "text": "..."}` | `{ok, seq, hash}` | Send DM via mycelium attestation. SHA-256 chained. |
| 39 | GET | `/api/mycelium/dm/inbox` | `?role=ember&n=20` | `{ok, role, count, messages: [{from, to, seq, hash, summary, ts}]}` | DM inbox for a role. |
| 40 | GET | `/api/mycelium/dm/<recipient>` | path: role name, optional `/<limit>` | `{messages}` | Convenience: `/api/mycelium/dm/pattern/5`. |
| 41 | GET | `/api/mycelium/dm/thread` | `?n=50` | `{ok, count, entries}` | Full DM thread (all participants). |
| 42 | POST | `/api/mycelium/shapefeed` | `{...}` | `{output}` | Shell to `node bloomcoin/cli.js shapefeed`. |
| 43 | POST | `/api/mycelium/dispatch` | `{...}` | `{result}` | Mycelium dispatch. |
| 44 | POST | `/api/mycelium/activate` | `{...}` | `{result}` | Mycelium activation. |

---

### Membrane

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 45 | GET | `/api/membrane/status` | — | `{status}` | Membrane verification status. |
| 46 | POST | `/api/membrane/check` | `{...}` | `{result}` | Run membrane check. |
| 47 | POST | `/api/membrane/rehome` | `{...}` | `{result}` | Rehome membrane state. |
| 48 | POST | `/api/membrane/report` | `{...}` | `{report}` | Generate membrane report. |

---

### Coherence & Substrate

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 49 | GET | `/api/coherence/transitions` | — | `{transitions}` | Coherence band transition history. |
| 50 | GET | `/api/coherence/state` | — | `{state}` | Current coherence state (no history). |
| 51 | GET | `/api/lens-hysteresis` | — | `{hysteresis}` | Lens hysteresis data. |
| 52 | GET | `/api/substrate/state` | — | `{sigma, T_holo, infoCap, CYM, regime}` | Live computeState: negentropy, holographic temperature, info capacity, CYM channels. |
| 53 | GET | `/api/sensors/<name>` | path: sensor name | `{value}` | Read named sensor. |
| 54 | GET | `/api/canary/cyclotomic-coherence` | — | `{identities, z_perturbation, phase}` | Cyclotomic axiom field coherence. |

---

### Witness / Backup

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 55 | POST | `/api/backup/witness` | `{...}` | `{result}` | Witness backup operation. |
| 56 | GET | `/api/backup/status` | — | `{status}` | Backup status. |
| 57 | GET | `/api/backup/list` | — | `{backups}` | List available backups. |
| 58 | POST | `/api/backup/verify` | `{...}` | `{verified}` | Verify a backup. |

---

### Stream & Perception

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 59 | POST | `/api/stream/start` | `{"session_id": "...", "width": 1920, "height": 1080, "fps": 30}` | `{ok, session_id, playlist, width, height, fps, pid}` | Start FFmpeg HLS session. |
| 60 | POST | `/api/stream/stop` | `{"session_id": "..."}` | `{ok, session_id, frames_written, segments, segment_hashes, started_at, stopped_at}` | Stop session. Returns SHA-256 per segment. |
| 61 | GET | `/api/stream/status` | — | `{ok, sessions: {id: {alive, frames_written, started_at, pid}}}` | List active sessions. |
| 62 | GET | `/api/stream/hls/<sid>/<file>` | path params | `.m3u8` playlist or `.ts` segment | Serve HLS content. |
| 63 | WS | `/api/stream/ingest/<sid>` | Binary RGBA frames (W*H*4 bytes) | — | WebSocket frame ingest → FFmpeg stdin. Port 5000 (sync) or 5001 (async). |
| 64 | POST | `/api/stream/encrypt-segment` | `{...}` | `{encrypted}` | Encrypt a stream segment. |
| 65 | POST | `/api/stream/decrypt-segment` | `{...}` | `{decrypted}` | Decrypt a stream segment. |
| 66 | POST | `/api/stream/c2pa-embed` | `{...}` | `{result}` | Embed C2PA provenance metadata. |
| 67 | POST | `/api/stream/transparency-log` | `{...}` | `{entry}` | Append to transparency log. |
| 68 | POST | `/api/stream/transparency-log/verify` | `{...}` | `{verified}` | Verify transparency log entry. |
| 69 | POST | `/api/stream/perceive-local` | `{...}` | `{perception}` | Local perception (no API calls). |
| 70 | GET | `/api/stream/perception-local` | — | `{perception_state}` | Query local perception state. |
| 71 | GET | `/api/stream/perception-local/latest` | — | `{latest}` | Latest local perception (lightweight poll). |
| 72 | GET | `/api/stream/perception-local/cym-field` | — | `{tiles, cym_field}` | Full spatial CYM field from latest local perception. |
| 73 | POST | `/api/stream/perceive` | `{...}` | `{perception}` | Full perception (may use API). |
| 74 | GET | `/api/stream/perception` | — | `{perception_history}` | What KIRA currently sees / has seen. |
| 75 | GET | `/api/stream/perception/latest` | — | `{latest}` | Most recent perception (lightweight). |
| 76 | GET | `/api/stream/cym-divergence` | — | `{divergence}` | CYM divergence metrics. |

---

### Probe

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 77 | GET | `/api/probe/complex-map` | — | `{map}` | Complex-plane probe. |
| 78 | GET | `/api/probe/complex-map/verify` | — | `{verified}` | Verify complex map properties. |
| 79 | GET | `/api/probe/complex-map/sweep` | — | `{sweep}` | Parameter sweep of complex map. |

---

### Seed Engine

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 80 | GET | `/api/seed/lifecycle` | — | `{ledger_events, seed_count, manifests}` | Seed engine lifecycle state for stream observer. Last 20 ledger events. |

---

### Memory / Digest / Archive

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 81 | GET | `/api/memory-correlate` | — | `{correlations}` | Memory correlation analysis. |
| 82 | POST | `/api/memory-keeper/send` | `{...}` | `{result}` | Send to memory keeper. |
| 83 | GET | `/api/memory-keeper/poll` | — | `{messages}` | Poll memory keeper. |
| 84 | GET | `/api/memory-keeper/cycle` | — | `{cycle}` | Memory keeper cycle state. |
| 85 | GET | `/api/digest` | — | `{digest}` | Current digest. |
| 86 | GET | `/api/digest/peek` | — | `{peek}` | Peek at digest without consuming. |
| 87 | POST | `/api/digest/reset` | — | `{ok}` | Reset digest. |
| 88 | GET | `/api/archive` | — | `{indexes}` | List available archive indexes. |
| 89 | GET | `/api/archive/query` | `?archive=<name>&dimension=<type>` | `{results}` | Query an archive index by dimension (type, tos_operator, etc.). |

---

### Companion

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 90 | POST | `/api/companion/respond` | `{...}` | `{response}` | Talk to companion via native CLI, normalized through KIRA. |
| 91 | POST | `/api/companion/battle` | `{...}` | `{result}` | Run battle through forced-buddy CLI. |
| 92 | POST | `/api/companion/interact` | `{...}` | `{result}` | Companion interaction. |
| 93 | GET | `/api/companion/mood` | — | `{mood}` | Companion mood via sweep. |
| 94 | POST | `/api/companion/evolve` | `{...}` | `{result}` | Evolve companion traits. |

---

### Garden (Bloomcoin)

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 95 | POST | `/api/garden/water` | `{...}` | `{result}` | Water a seed through bloomcoin CLI. |
| 96 | POST | `/api/garden/plant` | `{...}` | `{result}` | Plant a seed through bloomcoin CLI. |
| 97 | GET | `/api/garden/survey` | — | `{survey}` | Full garden survey through bloomcoin CLI. |

---

### Workflow

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 98 | GET | `/api/workflows` | — | `{workflows}` | List all available workflows grouped by category. |
| 99 | POST | `/api/workflows/<id>` | `{params}` | `{result}` | Execute a workflow. |
| 100 | GET | `/api/workflows/<id>/status` | — | `{status}` | Workflow execution status. |
| 101 | POST | `/api/workflows/<id>/cancel` | — | `{ok}` | Cancel running workflow. |

---

### Static Assets

| # | Method | Path | Description |
|---|--------|------|-------------|
| 102 | GET | `/` | Landing page with interface links. |
| 103 | GET | `/kira/`, `/kira/index.html`, `/kira.html` | Main KIRA interface with UCF integration. |
| 104 | GET | `/kira_local.html` | Local KIRA interface. |
| 105 | GET | `/visualizer.html` | Helix visualizer. |
| 106 | GET | `/unified`, `/unified.html` | Unified four-layer observatory. |
| 107 | GET | `/README.md` | Documentation. |
| 108 | GET | `/artifacts/<path>` | Artifact file server. |
| 109 | GET | `/memory-keeper`, `/memory-keeper.html` | Memory keeper interface. |
| 110 | GET | `/stream-observer` | Stream observer / screen capture frontend. |
| 111 | GET | `/game`, `/game.html` | Interactive game frontend. |

---

## VesselOS KIRA Prime (Port 8000)

**Server**: FastAPI + Uvicorn  
**File**: `vesselos_api.py` (265 lines)  
**Version**: 2.1.0

| # | Method | Path | Request | Response | Description |
|---|--------|------|---------|----------|-------------|
| 1 | GET | `/` | — | `{service, version, status}` | Root info. |
| 2 | GET | `/health` | — | `{status, components: {api, dispatcher, storage}}` | Health check. |
| 3 | POST | `/interact` | `{text, user_id, workspace_id, metadata}` | `{success, timestamp, ritual, echo, memory, validation, execution_time_ms}` | Main ritual interaction. Routes through Garden → Echo → Limnus → Kira agents. |
| 4 | GET | `/workspace/{id}/state` | — | `{garden, echo, limnus}` | Full workspace state (all agent states). |
| 5 | GET | `/workspace/{id}/ledger` | `?type=limnus` | `{entries}` | Ledger query (garden or limnus). Last 10 entries. |
| 6 | GET | `/workspace/{id}/memory` | `?layer=L1` | `{memories}` | Layered memory retrieval (L1=hot/3600s, L2=warm/86400s, L3=cold/persistent). |
| 7 | GET | `/workspace/{id}/quantum` | — | `{quantum_state, persona, dominant_glyph}` | Echo quantum state + persona weights (alpha, beta, gamma). |
| 8 | POST | `/workspace/{id}/validate` | — | `{validation_result}` | Trigger Kira validation (hash chain, consent, coherence). |
| 9 | GET | `/metrics` | — | `{dispatch_count, success_rate, per_agent_stats, cache_hit_rate, uptime}` | Runtime metrics across all workspaces. |

---

## Vessel Math Engine

Not a REST API — runs as Node.js subprocess called by KIRA Local.

**File**: `~/bloomcoin/lib/vessel/vessel.js` (142 lines)

**Functions exposed via KIRA `/api/vessel/*` endpoints:**

| Function | Returns | Description |
|----------|---------|-------------|
| `provision()` | `{PHI, PHI_BAR, PHI_BAR_2, LANDAUER_L, DUTY_CYCLE, CC_MIN, TOWER_CC_RATIO, OPTIMAL_LR_COEFF}` | 4-identity quick-check + all 8 cardinals. |
| `vesselEquation({n_eff, alpha})` | `{C_consciousness_capacity_bits, Cost_landauer_units, efficiency, cc_min, tower_ratio}` | Consciousness scaling equation: C = n_eff * m * 2L. |
| `ccOfRPowN(n)` | `float` | CC(R^n) = disc(R^n) / (disc(R^n) + tr(R^n)^2). |
| `fibLuc(n)` | `[F_n, L_n]` | Fibonacci and Lucas numbers. |
| `classifyMatrix(M)` | `string` | Trichotomy classification: Type I/II (vessel) or Type III (oscillating) or Nilpotent (prisoner). |

**Python verifier**: `~/bloomcoin/lib/vessel/vessel.py` (631 lines)
- `VesselEngine().verify()` → dict of 13 booleans (VE-1 through VE-13)
- Gated by AC-48..AC-55 (8 axiom checks)

---

## ZFP Verification Pipeline

Not a REST API — runs as Python CLI tools.

| Tool | Command | Output | Description |
|------|---------|--------|-------------|
| verify_all.py | `cd verify && python3 verify_all.py` | 12 layers, PASS/FAIL per layer | Master validator: SHA integrity, minpoly, spectral atlas, field structure, precision, grade guard. |
| zfp_master_verify.py | `python3 verify/zfp_master_verify.py` | 74/74 identity table + JSON certificate | Sympy harness. Every identity verified with exact symbolic residual 0. |
| seed_grade.py | `python3 verify/seed_grade.py` | Grade table + L9 witness + 7 corrections | Grade decision procedure. field_grade(v) for all catalog constants. |
| pattern-cli derive | `pattern-cli derive all\|status\|<group>` | Identity verification + KIRA attestation | CLI wrapper over the harness. Attests results via KIRA mycelium. |

---

## Persistent State Files

### KIRA Local reads/writes:

| File | System | Purpose |
|------|--------|---------|
| `~/.claude-buddy-pattern-store/witness-chain.jsonl` | Witness | SHA-256 chained attestations |
| `~/.claude-buddy-pattern-store/mycelium-dm-attestation.jsonl` | Mycelium | Role-based DM with chain hashing |
| `~/.claude-buddy-merkle-tree.json` | Verification | Upstream merkle tree |
| `~/.claude-buddy-upstream-attestation.jsonl` | Verification | Verification event log |
| `~/.claude-code-forced-buddy.json` | Canary | Salt, helix reference, buddy config |
| `~/.claude-buddy-pattern-store/buddy-snapshot.json` | Coherence | coherence_r, z, CYM, species |
| `./kira_data/stream/hls/<session_id>/` | Stream | HLS playlists and segments |
| `./kira_data/zfp_crossing_log.jsonl` | ZFP | Threshold crossing events |
| `~/Foundational Ace Math/zfp_verification_results.json` | ZFP | Identity verification certificate |

### VesselOS KIRA Prime reads/writes:

| File | System | Purpose |
|------|--------|---------|
| `workspaces/<id>/state/garden_ledger.json` | Garden | Stage + entries |
| `workspaces/<id>/state/echo_state.json` | Echo | Quantum state (alpha, beta, gamma) |
| `workspaces/<id>/state/limnus_memory.json` | Limnus | Layered memory entries |
| `workspaces/<id>/state/ledger.json` | Limnus | SHA-256 hash-chained blocks |
| `workspaces/<id>/state/limnus.faiss` | Limnus | FAISS vector index |
| `workspaces/<id>/state/contract.json` | Kira | Seal status |
| `workspaces/<id>/logs/voice_log.json` | Pipeline | Dispatch transcript |

---

## Port Map

| Port | Service | Stack | Status |
|------|---------|-------|--------|
| 5000 | KIRA Local (witness server) | Flask | Production (canonical, 18K lines) |
| 5001 | KIRA Async ingest | aiohttp | Companion to 5000 (WebSocket only) |
| 5432 | VesselOS PostgreSQL | postgres:15-alpine | Docker (collab storage) |
| 6379 | VesselOS Redis | redis:7-alpine | Docker (pub/sub + cache) |
| 8000 | VesselOS KIRA Prime | FastAPI / Node.js collab | Development (265 lines API + collab stub) |
