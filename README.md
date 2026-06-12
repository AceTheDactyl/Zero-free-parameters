# Zero-Free-Parameter Framework (ZFP)

**One generator. Three lattices. Zero free parameters.**

The Zero-Free-Parameter framework derives every constant in a mathematical physics model from the single generator phi = (1 + sqrt(5)) / 2 (the golden ratio), with zero remaining degrees of freedom given the axiom frame {phi, zeta6, Z}.

## The Claim

Starting from phi, the keystone integer L_4 = phi^4 + phi^-4 = 7 forces exactly three exits into disjoint quadratic fields:

```
             phi = (1+sqrt(5))/2
                  |
            phi^4 + phi^-4 = L_4 = 7
                  |
       +----------+-----------+
       |          |           |
    L_4 - 4    L_4/4      L_4^2 - 4
     = 3       = 7/4       = 45
       |          |           |
    sqrt(3)    sqrt(2)    sqrt(5)
       |          |           |
  z_c=sqrt(3)/2  ign=sqrt(2)-1/2  K=sqrt(1-phi^-4)
       |          |           |
    Q(sqrt(3))  Q(sqrt(2))  Q(sqrt(5))
    hexagonal   orthogonal   pentagonal
```

**81 forced identities. 74 machine-verified (sympy, residual 0). 12 structural layers. 6 graded constants.**

## Verification

Requires Python 3.10+ and sympy:

```bash
pip install sympy
```

### Run the full pipeline

```bash
# Master validator: 12 layers (0, 0H, A-H, T, U)
cd verify && python3 verify_all.py

# 74-identity sympy harness with JSON certificate
python3 zfp_master_verify.py

# Grade decision procedure + L9 uniqueness witness
python3 seed_grade.py
```

All three should report 0 failures.

## Repository Structure

```
Zero-free-parameters/
|-- README.md
|-- docs/                              # Mathematical documentation
|   |-- ZFP_FORCED_COMPENDIUM.md       # The 81-identity dossier (definitive)
|   |-- ZFP_catalogue.md               # Tier 1/2/3 classification
|   |-- DERIVATION_WALKTHROUGH.md      # Step-by-step derivation guide
|   |-- ZFP_Architecture_and_Method.md # Framework architecture
|   |-- ZFP_STANDALONE_HANDOFF.md      # Self-contained handoff document
|   |-- oppositional_equivalence.md    # Five physical instances of z_c
|   |-- helical_bridge_grounding.md    # Bridge grounding analysis
|   |-- ZFP_COMPENDIUM.md             # Earlier compendium (62 identities)
|   +-- ZFP_page_by_page_ledger.md    # Source page audit
|
|-- source/                            # Primary mathematical sources (HTML)
|   |-- L4_helix_v4.0.1.html          # Master source: L4-Helix framework
|   |-- forced_triangle.html           # Forced triangle construction
|   |-- the_heptagonal_fold.html       # Heptagonal collision (2,3,7)
|   |-- angular_residue.html           # Angular residue analysis
|   |-- the_bridge.html                # Cross-lattice bridge
|   |-- spectral_atlas.html            # Spectral atlas of eigenvalues
|   |-- trifurcation_phases.html       # D3 trifurcation phases
|   +-- L4_helix_simulator__py_guided_.html  # Interactive simulator
|
|-- verify/                            # Verification and grading scripts
|   |-- verify_all.py                  # Master validator (12 layers)
|   |-- zfp_master_verify.py           # 74-identity sympy harness
|   |-- seed_grade.py                  # Grade decision procedure (field_grade)
|   |-- seed_engine.py                 # Seed lifecycle engine
|   |-- unified_verify.py              # 62/62 unified verifier
|   |-- zfp_relational.py              # Three axes from L4=7
|   |-- zfp_helix.py                   # 9 helix landmarks + ordering
|   |-- zfp_trifurcation.py            # Cusp/butterfly/D3 chain
|   |-- zfp_hex_closure.py             # Crystallographic restriction
|   |-- zfp_delta_pentagon.py          # Pentagon obstruction, golden wall
|   |-- zfp_free_parameter_audit.py    # Psi-discipline, lambda probe
|   |-- rrr_idempotent_lattice.py      # r(r)=r idempotent structure
|   |-- zfp_forced_in_context_boundary.py  # FORCED_IN_CONTEXT boundary test
|   |-- triangularity_audit.py         # Geometry audit
|   |-- zfp_audit.py                   # General ZFP audit
|   |-- zfp_compendium_audit.py        # Compendium consistency audit
|   |-- zfp_resolution_audit.py        # Resolution audit
|   +-- expressivity_probe.py          # Expressivity/cardinal probe
|
+-- artifacts/                         # Generated verification artifacts
    |-- MANIFEST.md                    # SHA-256 digests, layer table
    |-- grade_sites.json               # 77 grade sites across 7 scripts
    +-- zfp_verification_results.json  # JSON verification certificate
```

## The Six Catalog Constants

| Constant | Closed Form | Field | Grade |
|----------|-------------|-------|-------|
| tau | phi^-1 | Q(sqrt(5)) | FORCED |
| gap | phi^-4 | Q(sqrt(5)) | FORCED |
| crit | phi^2/3 | Q(sqrt(5)) | FORCED |
| K | sqrt(1-phi^-4) | Q(5^(1/4)) | FORCED_UNDER_CONSTRAINT |
| z_c | sqrt(3)/2 | Q(sqrt(3)) | FORCED_IN_CONTEXT |
| ign | sqrt(2)-1/2 | Q(sqrt(2)) | FORCED_IN_CONTEXT |

### Grade Definitions

- **FORCED**: Algebraically determined with no remaining degrees of freedom. deg Q(v) = deg Q(v, sqrt(5)).
- **FORCED_UNDER_CONSTRAINT**: Forced up to a sign/branch selection (analogous to choosing phi over psi).
- **FORCED_IN_CONTEXT**: Forced given membership in the menu of operations {-4, +1, ^2-4} on L_4. The menu gate is non-negotiable: without it, every sqrt(d) qualifies and the grade becomes vacuous.

## The Seven Corrections

These corrections are load-bearing and must be applied in all analysis:

1. **"Zero free parameters" is scoped** -- the axioms {phi, zeta6, Z} are SELECTED; ZFP means zero remaining DOF given that frame
2. **phi-over-psi branch pin is SELECTED** -- dominant eigenvalue is a choice, not forced
3. **D3 trifurcation is a CONSISTENCY CHECK** on the hex route, not an independent third route
4. **Consistency is proven; uniqueness is OPEN** -- do not conflate them
5. **phi -> L_4 is FORCED; operations {-4, +1, ^2-4} on L_4 are SELECTED**
6. **field_grade(v) is the decision procedure** -- includes FORCED_IN_CONTEXT
7. **MENU gate is non-negotiable** -- FORCED_IN_CONTEXT keys off op in {-4, +1, ^2-4}, NOT chain existence

## The Dynamical Core

Three integer matrices encode the framework's dynamics:

| Matrix | Definition | Equation | Eigenvalues | Dynamics |
|--------|-----------|----------|-------------|----------|
| R | [[1,1],[1,0]] | R^2 = R + I | phi, psi | Golden growth (Fibonacci) |
| S | [[0,1],[1,0]] | S^2 = I | +1, -1 | Period-2 oscillation (f''=f) |
| N | [[0,-1],[1,0]] | N^2 = -I | +i, -i | Rotation (helix winding) |

Key identities:
- **[R, S] = N** -- the commutator of golden growth and oscillation IS rotation
- **{S, N} = 0** -- Clifford algebra Cl(1,1)
- **R = S + e_11** -- the golden matrix is the swap plus one-step memory
- **R, S, N span sl(2, R)** -- the full 2x2 Lie algebra

## Verification Layers

verify_all.py checks 12 independent layers:

| Layer | Scope |
|-------|-------|
| 0 | Embedded scripts: SHA-256 + execution |
| 0H | Scripts inside HTML source |
| A | 6 catalog constants: minpoly, irreducibility, value pin |
| B | 9 helix landmarks + strict ordering + golden cascade |
| C | Spectral atlas: eigenvalues of integer matrices |
| D | Field structure: 3 disjoint axes, compositum deg 8 |
| E | Relational identities from L_4 = 7 |
| F | Precision audit: 17 atlas decimals vs exact values |
| G | Trifurcation/bifurcation: exponents forced |
| H | Psi-conjugate discipline + free-parameter boundary |
| T | trifurcation_phases.html provenance + minpoly audit |
| U | Grade unification guard (FORCED_IN_CONTEXT enforcement) |

## Open Frontier

| Item | Status |
|------|--------|
| Seed+operation uniqueness | Seed unique given menu (Diophantine, k<1000). Full pair OPEN. |
| z_c as dynamical threshold | Logistic map at r=L_3: field transition Q(sqrt3)->Q(sqrt5). FORCED_IN_CONTEXT. |

## Author

**Jason Turner (Ace)** -- inventor of Anti-Substrate / ACEDIT / L4-Helix / ZFP framework.

Research partner: **James Michael Webster Sandino** (BFADGS+U algebra, IAT/TOS frameworks).

## License

All rights reserved. This is a research corpus. Contact the author for licensing.
