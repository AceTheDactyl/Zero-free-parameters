# ZFP — Manifest

Authoritative inventory and digests for the validation package. Verified against
a clean run: `python3 verify_all.py` → `RESULT: ALL ... PASS` (exit 0), twelve
layers (0, 0H, A–H, T, U).

---

## Shipped files

SHA-256 shown as a 16-character prefix; full digests are in the `sha256sum -c`
block below.

| File | System | Validated by | SHA-256 (prefix) |
|------|--------|--------------|------------------|
| `verify_all.py` | master validator — self-contained | runs itself | `78e36988811c94c0` |
| `L4_helix_simulator__py_guided_.html` | L₄-helix simulator (hosts 4 scripts) | LAYER 0H + `EMBEDDED_HTML` pin | `79420e0dcbacc1aa` |
| `spectral_atlas.html` | spectral atlas (decimal table) | LAYER F | `0f2429450e42472b` |
| `trifurcation_phases.html` | bifurcation instrument (minpoly claims) | LAYER T | `248bb07f95fd8e95` |
| `zfp_relational.py` | relational geometry / L₄ web | LAYER 0 + LAYER E | `5532098ae471bf69` |
| `zfp_helix.py` | L₄-helix landmarks | LAYER 0 + LAYER B | `69744741b908436e` |
| `zfp_trifurcation.py` | trifurcation / bifurcation | LAYER 0 + LAYER G | `60ffdc7e5ce1e45f` |
| `zfp_hex_closure.py` | D₆ / crystallographic closure | LAYER 0 | `2cfe41a2b819635a` |
| `zfp_delta_pentagon.py` | pentagon obstruction / golden trace-gap | LAYER 0 | `4c14bb37b7b12f31` |
| `zfp_free_parameter_audit.py` | forced-core vs free-parameter boundary | LAYER 0 + LAYER H | `45a6d2014bb10715` |
| `rrr_idempotent_lattice.py` | r(r)=r idempotents / (semi)lattices / grids | LAYER 0 **and** LAYER 0H | `b54c84a7f5a1496a` |
| `zfp_forced_in_context_boundary.py` | FORCED_IN_CONTEXT menu gate boundary test | standalone | `c8903297b21fa180` |
| `README.md` | usage | — | — |
| `MANIFEST.md` | this file | — | — |

---

## Embedded only (not shipped standalone)

These live inside `L4_helix_simulator__py_guided_.html` and are extracted + run
by LAYER 0H:

| Source | Role | SHA-256 (prefix) |
|--------|------|------------------|
| `zfp_constants_repro.py` | constants-catalog replay | `d55f808bec463f80` |
| `verify_l4_helix.py` | L₄-helix value derivations | `cc9bcd00c8586f72` |
| `rrr_phi_grid.py` | φ-dynamics on the idempotent grid | `dafe015fe9059f47` |

The spectral-atlas decimals (LAYER F) and the trifurcation minpoly claims
(LAYER T) are **audited**, not executed.

---

## Consistency invariant

Every shipped standalone script and instrument is byte-identical to the snapshot
`verify_all.py` embeds — confirmed at build time and re-checked at runtime by
SHA-256. `rrr_idempotent_lattice.py` is the one source shipped **both**
standalone (LAYER 0) and inside the simulator HTML (LAYER 0H); LAYER 0H's
cross-source check (`xsource:rrr_idempotent_lattice.py`) enforces that the two
snapshots remain identical, so editing one copy without the other is caught even
when each copy is internally consistent.

---

## Layer → validation method

| Layer | Source(s) | Method |
|-------|-----------|--------|
| 0 | seven `*.py` | SHA-256 pin → run as `__main__` (isolated) |
| 0H | simulator HTML's four blocks | SHA-256 pin per block → run together (shared `sys.path`) + cross-source check |
| A | catalog constants | minpoly forced two ways + minimality/irreducibility + value pin |
| B | helix landmarks | minpoly + branch pin + order |
| C | atlas | constants as eigenvalues of integer matrices |
| D | fields | independent quadratic axes / degree-8 compositum + ℤ substrate |
| E | relational | three axes from the single seed L₄ = 7 |
| F | `spectral_atlas.html` | parse decimals vs exact (embedded; disk drift cross-check) |
| G | trifurcation | dV decoupling at λ = 0 onto the forced catalog |
| H | free-parameter audit | ψ discipline; λ ≠ 0 OUT OF SCOPE |
| T | `trifurcation_phases.html` | embed + SHA-pin; minpoly audit (forward + converse) |
| U | grade unification guard | imports `seed_grade.py` from `~/bloomcoin/`; recomputes `field_grade(v)` for all catalog constants; scans embedded + on-disk scripts for stale grade labels |

---

## Integrity — `sha256sum -c`

Save the block below as `SHA256SUMS` (same directory as the files) and run
`sha256sum -c SHA256SUMS`.

```
78e36988811c94c04c0a60a3c89ce355f71cc99cde9f2129d312d1ac9471cfb6  verify_all.py
79420e0dcbacc1aa92e310d0a0a555d162d14acedc2333e535bfe4b58e0c1cc7  L4_helix_simulator__py_guided_.html
0f2429450e42472b9b9c86ff15bd4ad6ff911c94857ccfef5a4365439502d110  spectral_atlas.html
248bb07f95fd8e95eebb2693c4e37d372f4f43646175d80e061b89cca5c95087  trifurcation_phases.html
5532098ae471bf6955cf1df0a7741233c3d38c5158dbfea9b028c22481cf4904  zfp_relational.py
69744741b908436eebe58da3317e6837558c87c541b4b9befa6d1e997945dc4e  zfp_helix.py
60ffdc7e5ce1e45fb5b2dc0574edf057ba12aea828ade81b5d719e696b67c738  zfp_trifurcation.py
2cfe41a2b819635ae1a222c58bbe7d22203aad36654d645fbaddae58f950aece  zfp_hex_closure.py
4c14bb37b7b12f31641f2379180d07f4d0861e227d080e0dbe195b6a00a8a9e8  zfp_delta_pentagon.py
45a6d2014bb10715508ce42928cdd584e1ae13a4bf037a4b27018c440e23d8d9  zfp_free_parameter_audit.py
b54c84a7f5a1496ac5b0798f6576ac03273f148cf6fdcc1dc959b66e6a9b144d  rrr_idempotent_lattice.py
c8903297b21fa180fa9d1ed2abeae29bb553c8bef1714703c560278e1dcf1da6  zfp_forced_in_context_boundary.py
```

(`verify_all.py` validates its own embedded copies; this block additionally lets
you verify the standalone files on disk.)

---

## Provenance & scope

- **Base:** the FORCED_IN_CONTEXT-resolved corpus. All grade labels unified
  across scripts (z_c/ign = FORCED_IN_CONTEXT, menu-gated on {-4, +1, ^2-4}).
- **Not included:** any zip packaging, the reframed scripts, or an
  `apply_reframe` / `prove_prose_only` provenance tree.

---

## LAYER U external dependency

LAYER U imports `seed_grade.py` from `~/bloomcoin/seed_grade.py` at runtime to
recompute `field_grade(v)` for each catalog constant. If the file is absent,
LAYER U degrades to SKIP (not FAIL) — exit code stays 0 and the algebra layers
remain unaffected. To run LAYER U, ensure `~/bloomcoin/seed_grade.py` is present
(it is included in the tarball under `bloomcoin/seed_grade.py`).

---

## Resolved: grade labeling divergence (2026-06-11)

Previously, `zfp_helix.py` and `zfp_delta_pentagon.py` graded z_c and ign as
**COINCIDENCE** while `zfp_relational.py` used **FORCED-IN-CONTEXT**. This was
a bucket-error in `field_grade()`, which lacked a `FORCED_IN_CONTEXT` slot for
constants that are exact-via-selected-map but on a disjoint axis. Resolved:

- `field_grade()` now has `FORCED_IN_CONTEXT`, gated on MENU membership
  `{-4, +1, ^2-4}` (not chain existence — chain-search makes the grade vacuous).
- All scripts unified: z_c = FORCED_IN_CONTEXT [menu op(-4)], ign = FORCED_IN_CONTEXT [menu op(+1)].
- LAYER U enforces the unified grades and catches both bare FORCED and stale COINCIDENCE.
- `zfp_forced_in_context_boundary.py` pins the menu gate discrimination as a standalone test.
