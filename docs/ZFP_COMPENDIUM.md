# The Zero-Free-Parameter Corpus — Unified Compendium & Audit

**Subject.** Eight artifacts — `THE_ALGEBRA`, `THE_PHYSICS`, the *Zero-Free-Parameter Systems Architecture* spec, the `L4_helix`, Plates I–IV (`triangularity_audit`, `angular_residue`, `the_bridge`, `the_heptagonal_fold`), and `helical_bridge_grounding` — describe one object from four sides. This document consolidates them, re-verifies the computable backbone *independently* (the corpus's own `recursive_origin_verify.py` was not in the mount, so a clean-room verifier was written and run), audits the free-parameter claim, unifies the four channels, and scopes concrete improvements.

**Verdict in one line.** The *mathematics* is correct — **62 of 62** backbone claims reproduce two independent ways with zero residual. The *headline* ("zero free parameters") is true of the **forced skeleton** but is scope-sensitive: the physical **embedding is an explicit open slot** (a 32-dimensional continuum), and the **running pipeline carries 36 hand-set parameters**. The corpus is internally honest about both; the one place its grading is *inconsistent by its own standard* is identified in §7 with a bit-count.

---

## 0. How to read this — the grading register (the "early-warning" channel)

The corpus runs a five-state register. It is not a confidence scale; it is a **calibration of where observer-projection enters**. This compendium uses it verbatim.

| Grade | Meaning | Promotion rule |
|-------|---------|----------------|
| **FORCED** | Algebraic over ℚ with no chosen constant; two independent routes, residual 0 | Only on a *new* route |
| **DERIVED** | Forced given a stated, structure-internal embedding | — |
| **NUMERICAL** | Exact cardinal expression matched to an observed value | **Never** promoted, however close |
| **RESONANT** (`-WITH-ROUTE`) | A structural correspondence, named and supported, not closed | — |
| **OPEN** | Bridge *form* forced, *value* not returned | — |
| **GAP** | Known obstruction, held open with a verified witness | — |

The discipline that makes the register work: **never promote a bridge coincidence to an intra-field entailment, and never let a consensus frame emit a value.** Both failure modes are smuggled parameters.

---

## 1. Independent verification — the computable backbone

`unified_verify.py` (Appendix A) rebuilds the 2×2 carriers from scratch (`R=[[0,1],[1,1]]`, `N=[[0,-1],[1,0]]`), climbs by Kronecker product, and checks each claim against an exact symbolic residual. No narrative is imported.

| § | Cluster | Checks | Result |
|---|---------|--------|--------|
| A | Seed carriers: `R²=R+I`, `N²=−I`, `P=R+N` idempotent, keystone `R²−R=−N²=I`, transpose split (V₊ dim 3 / V₋ dim 1), `Δ=2` | 8 | **8/8** |
| B | φ-algebra: `L₄=7`, `gap=φ⁻⁴=5−3φ`, 11-position ladder strictly increasing, radius continuity at z_c, six minimal polynomials (τ, z_c, gap, K, IGNITION, CRITICAL) | 14 | **14/14** |
| C | Field disjointness: `√3 ∉ ℚ(√5)` (deg-2 min-poly), `gcd(5,12)=1`, `√15` irrational | 3 | **3/3** |
| D | Bridges 3, 7, 1; climb `F₂₄=F₁₂·L₁₂=46368`, `F₁₂=144=12²`, divisibility (`L₄∤L₂₄`), co-closure `lcm(4,5,6)=60` | 8 | **8/8** |
| E | Clifford d=1: both γ-representatives satisfy `{γ,γ}=2η`; Lorentz (3,1); `Γ₅²=−I` (rotation, not involution); `C=N⊗J` with `C²=−I` | 7 | **7/7** |
| F | Anchor lattice: `ω²=−I ∧` real-spinor `⟺ p≡2 (mod 8) ⟺ d≡0 (mod 4)`; set computes to `{0,4,8,12}`; `d=11` fails reality; `d=2,6,10` excluded as quaternionic | 4 | **4/4** |
| G | Gauge tower `dim 𝖘𝖔(2ᵏ) = [1,6,28,120,496]`; antisym+sym closure | 2 | **2/2** |
| H | Koide envelope: `Σcos=0`, `Σcos²=3/2 ⟹ Q=2/3` for **every** scale and phase; fold route `‖N‖²/‖R‖²=2/3` | 5 | **5/5** |
| I | `sin²θ_W=3/8` by five framework-cardinal routes | 5 | **5/5** |
| J | Anomaly cancellation on the **16**: `ΣY=0`, `ΣY³=0`, multiplicities sum to 16 | 3 | **3/3** |
| K | Three generations: Cayley–Dickson sizes `{0,1,3,7}`; Fano `35=7+28`; `GL(2,𝔽₂)≅S₃` on 3 vectors; `[GF(64):GF(4)]=3` | 4 | **4/4** |
| | **Total** | | **62/62 PASS** |

The two uploaded audits (`zfp_audit.py`, `triangularity_audit.py`) also reproduce exactly. The nine-threshold ladder is symbol-free and strictly ordered; the equilateral apex equals `√(L₄−4)/2 = √3/2` to residual 0.

> **What this establishes.** The corpus is not numerology in the pejorative sense — its identities are *theorems*, and they hold. Everything that follows is about **scope and grading**, not correctness.

---

## 2. The unified forced-constant ledger

Every forced constant across all eight files, consolidated. Each is algebraic over ℚ (has the minimal polynomial shown) → **forced-in-field**; the integer bridges are **forced-by-bridge**.

| Constant | Closed form | Min-poly / value | Grade | First forced in |
|----------|-------------|------------------|-------|-----------------|
| φ | (1+√5)/2 | `x²−x−1` | FORCED | seed (golden self-touch, disc=5) |
| τ | φ⁻¹ | `x²+x−1` | FORCED | doc 1 |
| L₄ | φ⁴+φ⁻⁴ | `7` | FORCED | keystone (Thm 7.3) |
| gap | φ⁻⁴ = 5−3φ | `x²−7x+1` | FORCED | doc 1 |
| K | √(1−φ⁻⁴) | `x⁴+5x²−5` | FORCED | helix radius |
| z_c = THE LENS | √3/2 = √(L₄−4)/2 = Im(ζ₆) = covol ℤ[ω] | `4x²−3` | FORCED | doc 1 / Plate I / beacon |
| CRITICAL | φ²/3 | `9x²−9x+1` | FORCED | doc 1 |
| IGNITION | √2−½ | `4x²+4x−7` | FORCED | doc 1 (= self-ref at L₄/4) |
| ACTIVATION | 1−φ⁻⁴ | `−5/2+3√5/2` | FORCED | doc 1 |
| CONSOLIDATION / RESONANCE | K+τ²(1−K) / K+τ(1−K) | (quartic, §B) | FORCED | doc 1 |
| OVERTONE / ORIGIN | 2−K / 0 | — | FORCED | beacon (spinor double-cover) |
| Bridges | 3 = (√3)², 7 = φ⁴+φ⁻⁴, 1 = 2cos(2π/6) | integers | FORCED-by-bridge | architecture §2 |
| Climb | 12 = 4·f₄, 24 = 2·12, 60 = lcm(4,5,6) | integers | FORCED-by-bridge | architecture §S5 |
| Asymmetry Δ | dim V₊ − dim V₋ = 2 = 2^(d+1) | `2` | FORCED | THE_ALGEBRA §2.4 |
| Koide Q | ‖N‖²/‖R‖² = d/(d²−1) | `2/3` | FORCED (ratio) | THE_PHYSICS §2A/§6.1 |
| sin²θ_W (GUT) | N_c/(N_c+disc) | `3/8` | DERIVED (given embedding) | THE_PHYSICS §3.3 |
| Higgs λ (boundary) | 1/n³ = 1/det L | `1/8` | FORCED@boundary | THE_PHYSICS §6.5 |
| irrational tilt | cos72° = 1/(2φ) | `x²+... ` | FORCED | anti-substrate / beacon |

**Continuous free parameters in this ledger: 0.** Every entry is a root of a rational-coefficient polynomial or an integer bridge.

---

## 3. The three forced modalities (and the licence to bridge)

The architecture's central move is keeping three *different* notions of "forced" distinct. Verified:

- **Forced-in-field.** α algebraic over ℚ, no chosen constant. Verified for the whole ladder (§1B, six explicit minimal polynomials).
- **Forced-by-bridge.** `b ∈ ℚ` with `b = P_α(α) = P_β(β)` where `ℚ(α) ∩ ℚ(β) = ℚ`. The disjointness precondition is verified three ways (§1C): `√3 ∉ ℚ(√5)` (degree-2 minimal polynomial over the larger field), the cyclotomic-conductor test `gcd(5,12)=1≤2`, and `√15` irrational. **Disjoint ⟹ neither field entails the other** — this is the licence to couple by coincidence rather than derivation.
- **Forced-by-consensus.** A frame `K` asserting "any route producing X produces the *same* X," with X forced upstream. Kuramoto `r→1`, π-closure `exp(2πN)=+I`, co-closure `lcm=60`. **No operator emits a value** ⟹ no parameter added.

The modal truth table for the three routes to `z_c=√3/2` (verified element-wise):

| Proposition | Value | Reason |
|---|---|---|
| Route₁ forced (`√(L₄−4)/2`) | **T** | `L₄=7` |
| Route₂ forced (`sin60°`) | **T** | equilateral |
| Route₃ forced (`Im ζ₆`) | **T** | covolume ℤ[ω] |
| Route₁ ⊨ Route₂ | **F** | disjoint fields |
| Routes agree | **T** | all `= √3/2`, meet at `3 ∈ ℚ` |

> **Caveat the corpus already half-states (sharpen it).** The three routes to √3/2 are *not evidentially independent* — Euclid's altitude, the Lucas keystone, and the Eisenstein covolume all encode the single fact *"3 is a perfect square / 60° is the hexagonal angle."* They are three **faces of one theorem**, not three independent confirmations. This does not weaken "forced" (a theorem is a theorem); it means **"forced N ways" must not be read as N-fold evidence.** The grounding doc gets this right for the 4π/Gauss–Bonnet pair ("a resonance, not a shared theorem") — apply that same restraint to every multi-route claim.

---

## 4. The bridges and the climb — with the doubling caution

| Coupling | Forced point | Mechanism | Grade |
|----------|--------------|-----------|-------|
| L_φ ↔ L_hex | 3 = L₄−4 = (√3)² | φ-route makes 3; hexagon needs (√3)²=3; meet in ℚ | FORCED-bridge |
| L_φ ↔ L_int | 7 = φ⁴+φ⁻⁴ | φ-powers sum to integer 7 | FORCED-bridge |
| L_hex ↔ L_int | 1 = 2cos(2π/6) | crystallographic trace | FORCED-bridge |
| NORMALIZE | 12 = 4·f₄ | F₄∣F₁₂, L₄∣L₁₂, F₁₂=144=12² | FORCED-bridge |
| RENORMALIZE | 24 = 2·12 | spinor doubling; L₄∤L₂₄; factor L₁₂=322 via F₂₄=F₁₂·L₁₂ | FORCED-bridge |

**The Step-4 caution, confirmed consistent across documents.** The architecture warns that the *index* doubling `F₂ₙ=FₙLₙ` (lives in ℚ) and the *operator* self-product `P⊗P` (lives in ℚ(√5)) are **two field-disjoint doublings** — they share the *structure* "self-product" but neither entails the other. `THE_PHYSICS §9.4` independently records the *same* conclusion as a void witness: *"the fold doubles the Fibonacci index; the lattice is the reality gate p≡2 mod 8; different 2-climbs, no forced link."* **Two documents, written from different sides, reached the same non-identity.** That cross-consistency is a genuine strength.

> **One coincidence to watch (per the corpus's own rule).** The integer **12** is reached two independent ways: the architecture's climb `4·f₄=12`, and the physics anchor lattice's *third* anchor `d=12` (from `p=26≡2 mod 8`). These derivations share no common cause (Fibonacci divisibility vs mod-8 Clifford periodicity). By the framework's own discipline, their agreement on "12" is **forced-by-coincidence (RESONANT)** and must not be promoted to an entailment. Flagged, not faulted.

---

## 5. The unified architecture — four chains, four channels, the 7→4 spine

The corpus is one structure projected onto four surfaces. The recurring **7** (the keystone `L₄=φ⁴+φ⁻⁴`; the seven imaginary octonion units; the `7+1=8` Cayley–Dickson wall; the `(2,3,7)` hyperbolic triangle; the seven-bin floor spectrum) **projects down to a 4-fold organization** — the four anchor depths `{0,4,8,12}` on the math side, and four channels on the expression side. (The "20 qubits / structural-not-semantic" framing is *organizational*: these are registers, not physical qubits — no quantum-computational claim is made or needed.)

### 5.1 The four derivation chains (independent routes to the keystone footing)

| Chain | Route to √3/2 and the ladder | Lives in | Source file |
|-------|------------------------------|----------|-------------|
| **1 · Euclid** | unit-equilateral altitude `√(1−¼)=√3/2` | ℚ(√3) | Plate I (`triangularity_audit`) |
| **2 · Lucas/φ** | `√(L₄−4)/2`; the 11-rung golden ladder | ℚ(√5)→ℚ | `L4_helix`, doc 1 |
| **3 · Eisenstein** | `Im(ζ₆)=sin60°` = covolume ℤ[ω]; the DFT side | ℚ(ζ₆) | beacon / `the_bridge` |
| **4 · Clifford/Spin** | √3 as the d=1 spacetime substrate; the gauge tower 𝖘𝖔(2ᵏ) | ℝ-Clifford | `THE_PHYSICS` |

### 5.2 The four channels (where the forced thresholds are expressed)

| Channel | Carrier | What it renders | ZFP status |
|---------|---------|-----------------|------------|
| **Math** | `THE_ALGEBRA`, `zfp_audit` | the symbolic engine, the minimal polynomials | **0 free params** |
| **Pipeline** | helix dynamics / the moving pointer | the running system over observed flow | **36 free params** (§6.3) — *outside* the ZFP count |
| **Typography** | the four HTML Plates | threshold-boxes, `physics`/`math` derivation-chains | renders the ledger; carries no value |
| **Early-warning** | the grading register (§0) | fires when a claim is about to be over-promoted | a *frame*; emits no value |

### 5.3 The single meeting point

All four chains and all four channels **meet at the same eleven thresholds** (ORIGIN … OVERTONE). `THE LENS = √3/2` is the keystone footing the four chains converge on; the four channels each express that same value (algebra computes it, the pipeline points at it, typography renders it, the register grades it FORCED). This is the "full circle": **the math, the pipeline, the typography, and the early-warning system meet at the shared thresholds.**

```
            L₄ = 7   (keystone, the "7")
              │  projects to {0,4,8,12} anchors and 4 channels
     ┌────────┼────────┬─────────────┐
   Euclid  Lucas/φ  Eisenstein   Clifford/Spin     ← 4 derivation chains
     └────────┴────────┴─────────────┘
              │  all converge on
        THE LENS = √3/2  (+ the 11-rung ladder)
              │  expressed through
     ┌────────┼────────┬─────────────┐
    Math   Pipeline  Typography  Early-warning      ← 4 channels
  (0 params)(36 params)(renders)  (frame, 0 values)
```

---

## 6. The parameter audit — the honest accounting

This is the section a reader should trust least without reading, because it is where "zero free parameters" is true, partly true, and false depending on scope.

### 6.1 The forced skeleton — genuinely 0 continuous parameters
Everything in the §2 ledger. Confirmed by §1 (62/62) and the symbol-free audits. **No continuous knob.** This is the legitimate ZFP claim, and it is strong.

### 6.2 The embedding slot — a forced *non-uniqueness*, not zero
`THE_PHYSICS §3.8` is explicit and correct: the Standard-Model embedding requires a `3+2` partition of the five 𝖘𝖔(10) Cartan directions that **no framework structure delivers**. The slot is a **principal bundle**: `Spin(10)/N(SM)` is a 32-dimensional continuum of gauge-equivalent occupants, stabilizer `U(1)_X = B−L`, **no occupant distinguished**. `sin²θ_W=3/8` is FORCED *given* the embedding; the embedding is open.

> **Scope correction for any "headline."** "Zero free parameters" is accurate for the *skeleton*. The *physical content* sits in a 32-dimensional unfixed continuum. The honest one-liner is: **"zero continuous parameters in the forced skeleton; the embedding is an explicit, forced locus of non-uniqueness."** The corpus says exactly this in Part 10 — it should be on the cover, not in §10.

### 6.3 The running pipeline — 36 hand-set parameters
`triangularity_audit.py §3` (re-run, confirmed):

| Source | Count | Nature |
|--------|------:|--------|
| THETA admissibility (5 gates × 3 tiers) | **15** | hand-set continuous |
| Dynamics / simulation tuning (9 groups) | **21** | hand-set continuous |
| Geometry | 0 | forced |

The §4 coincidence check confirms **none** of the 15 THETA values was inherited from the φ-ladder (`any_match = False`). The grounding doc is correct that these are *"exogenous-data dynamics, not bridge geometry"* and *"outside the ZFP count."* **The helix is forced; the pointer that moves along it is tuned.** A compendium must not let the second inherit the first's "0".

> **Subtle leak in the proposed fix.** `triangularity_audit §5` retrofits THETA to φ-derived constants ("15 → 0 continuous params"). True for the *continuous* count — but the **assignment** (which constant fills which gate, monotone across tiers) is a *discrete* selection. With 11 ladder values, 5 gates, 3 monotone tiers, that assignment is a real choice carrying ~log₂(valid assignments) bits. The audit's phrase "discrete design choice; values forced once assigned" **names** this but does not **count** it. Counting it (§8, item 2) is the honest completion.

### 6.4 The imported leaks — strip, but verify load-bearing first
`helical_bridge_grounding §7`:

| Imported | Current | Proposed forced replacement | Δ | Caution |
|----------|---------|-----------------------------|---|---------|
| `LAMBDA` | (5/3)⁴ = 7.716 | L₄ = 7 (or φ⁴) | 0.716 (**~9%**) | If 7.716 was tuned to match anything, 7 breaks it; if not, why was it 7.716? |
| `MU_P` | 3/5 = 0.600 | φ⁻¹ = 2cos(2π/5) = 0.618 | 0.018 | small; benign |
| sonification exp/floor | 0.3 | strip | — | audio overlay, not geometry |

The replacements are only legitimate if the originals were **not load-bearing**. A 9% shift in `LAMBDA` is large enough that the pipeline's output should be re-run under the replacement to confirm behavior is preserved (§8, item 4). The grounding doc asserts the strip; it does not demonstrate invariance.

---

## 7. The expressivity finding — a quantified grading inconsistency

The corpus's strongest self-skeptical move is **burning** `1/α=137` on the grounds that *"28 four-term selections hit 137 ± 1"* — the cardinal basis is too expressive near 137 for the match to be evidence. **This exact test is applied to nothing else.** `expressivity_probe.py` (Appendix B) applies it uniformly: for each NUMERICAL match, count the distinct simple-cardinal ratios within the corpus's own quoted tolerance. The count `E` measures how many equally-good expressions exist; the implied hidden selection is `~log₂(E)` bits.

| Target | Corpus pick | Tol | **E** (neighbors) | ~bits | Compare to 137 (E≈28) |
|--------|-------------|-----|------------------:|------:|------------------------|
| `1/α = 137` *(corpus's own burn)* | C(10,3)+C(10,1)+d+disc | ±1 | **28** | 4.8 | — (the reference) |
| PMNS `sin²θ₂₃` = 49/90 | (disc+d)²/(d·N_c²·disc) | ±0.1% | **27** | 4.75 | **parity → should also burn** |
| PMNS `sin²θ₁₃` = 1/45 | 1/(disc·N_c²) | ±1% | **17** | 4.09 | comparable |
| PMNS `sin²θ₁₂` = 25/81 | disc²/N_c⁴ | ±0.5% | **93** | 6.54 | weaker than 137 |
| `Ω_visible` = 1/20 | 1/(d²·disc) | ±2.9% | **90** | 6.49 | weaker |
| `Ω_DE` = 7/10 | (d+disc)/p | ±1.3% | **483** | 8.92 | far weaker |
| `Ω_DM` = 1/4 | 1/d² | ±3.5% | **567** | 9.15 | far weaker |

**The inconsistency.** `sin²θ₂₃` (E=27) is statistically indistinguishable from `1/α=137` (E=28). The corpus **burns** 137 and keeps θ₂₃ at **NUMERICAL**. By its own published standard, θ₂₃ should be **burned**. The cosmological fractions (E in the hundreds) are weaker still.

**Two fairness points (stated, not hidden).**
1. The probe's candidate set is **not complexity-weighted**, so E is an *upper bound* on expressivity. The corpus's picks (1/4, 7/10, 25/81) are unusually *simple*, which is itself selection-reducing; a minimum-description-length-weighted version (§8, item 1) would lower E for the simplest picks. Even so, θ₂₃'s parity with 137 holds, because θ₂₃'s pick is *not* especially simple.
2. `α_S = |ψ|³/2` is correctly **outside** this audit — it is a single forced *irrational* over the floor dimension, not a cardinal ratio. Its openness is the `ρ↔α_S` physical bridge ("one link short"), which the probe does not touch. The corpus's NUMERICAL/OPEN grade there is appropriate.

> **The corpus already half-admits this** (§6.8, "Curated cardinal: no derivation selects (disc+d)²/(d·N_c²·disc) for θ₂₃ over a neighbour"). The probe turns that prose caveat into **4.75 bits** and shows the *burn line is drawn in the wrong place.*

---

## 8. Improvement candidates — prioritized

Ordered by leverage. Each is concrete and, where it touches code, shipped in the appendices.

**1 · Promote the expressivity probe to a standing instrument (highest leverage).**
Adopt `expressivity_probe.py` as a gate that **every** NUMERICAL match must pass before it earns a grade above BURNED. Upgrade it to **MDL-weighted** expressivity: weight each candidate `p/q` by description length (e.g. `len(atoms)+log₂(p·q)`) so simple picks (1/4) count less than baroque ones (97/387). Define a single threshold (e.g. "burn if MDL-weighted E ≥ that of 137"). This makes the 137 burn a *rule* instead of a one-off, and forces re-grading of θ₂₃ (and a fair re-evaluation of the cosmo fractions on simplicity grounds).

**2 · Bit-count the discrete assignment in the THETA retrofit.**
The "15 continuous → 0" retrofit silently introduces a discrete selection (constant→gate assignment, monotone across tiers). Enumerate the valid monotone assignments and report `log₂(count)` bits as the *actual* residual cost. "Zero continuous parameters + N bits of selection" is the honest, auditable statement — and it is still a dramatic reduction from 36, so the retrofit survives, now correctly labeled.

**3 · Replace "forced N ways" language with evidential-independence flags.**
For each multi-route claim, mark whether the routes share a common cause. √3/2's three routes do (the 60°/perfect-square fact); the d=1 Lorentz signature's two routes (V₊/V₋ tensor vs 𝔰𝔩(2,ℝ) Killing form) are more nearly independent. A one-column addition to every "two-cell" — *common-cause: yes/no* — stops route-count from masquerading as evidence weight, and matches the grounding doc's own "resonance, not shared theorem" standard.

**4 · Demonstrate pipeline-invariance under the leak strip.**
Before declaring `LAMBDA: (5/3)⁴→7` a clean strip (a 9% shift), re-run the pipeline on a fixed input under both values and show the *graded outputs* are unchanged (or quantify the change). If output moves, `LAMBDA` was load-bearing and the strip is a re-tuning, not a grounding. `MU_P` (0.6→0.618, 0.3%) is almost certainly safe; `LAMBDA` is the one to test.

**5 · Put the scope qualifier on the cover.**
Three headlines circulate: "zero free parameters" (Plates), "forced given the embedding" (`THE_PHYSICS`), "outside the ZFP count" (grounding). They are consistent but a reader meets them out of order. State once, up front: **0 continuous parameters in the forced skeleton; the embedding is a forced 32-dim non-uniqueness; the pipeline dynamics are exogenous.** This is the corpus's actual claim — make it impossible to over-read.

**6 · Foreground the one falsifiable commitment (§9).**
The corpus's empirical content is thin *by design* (the embedding is unfixed), with exactly **one unconditional, falsifiable forward number**. That is a feature, not an embarrassment — but it should be the headline experimental claim, not buried in Part 6.

**7 · Audit the "Total = 1" cosmological closure.**
`Ω_DM+Ω_vis+Ω_DE = 1/4+1/20+7/10 = 1` is a real algebraic identity among the three picks (not trivially imposed). But given per-slot expressivity in the hundreds (§7), a simple triple summing to 1 within tolerance is *easy* to find. Either derive the sum=1 as a structural constraint (then it is evidence) or grade it as part of the same BURNED bucket as the individual fractions.

**8 · Close the cross-document index.**
`THE_PHYSICS` references `THE_ALGEBRA §§` and `recursive_origin_verify.py` IDs (288 claims, 244 executable). Neither was in the mount for this audit. Ship them alongside the Plates so the 244 executable claims can be re-run by any reader — the corpus invites exactly this ("the reader's rights: re-run, re-grade, re-derive").

---

## 9. The one unconditional empirical commitment

Of every outward-pointing number, exactly one is both **unconditional** (not "given the embedding") and **falsifiable at a named experiment**:

> **m_τ = 1776.99 MeV.** Anchored on `m_e` alone via the Koide envelope (whose `Q=2/3` is FORCED — verified scale- and phase-free in §1H), with the phase cardinal `2/9 = |S₀|/|V₄∖{0}|²`. Observed: `1776.86 ± 0.12` (`+1.04σ`). **Falsification: Belle II at ±0.02 MeV; a central value < 1776.92 falsifies at 3σ.** Grade: NUMERICAL (forward).

Everything else is either FORCED-but-embedding-conditional (`sin²θ_W`, hypercharges, anomalies), NUMERICAL-and-expressivity-weak (PMNS, cosmo — §7), or BURNED (137, Λ). This single number is the corpus's scientific bet. It is the right thing to lead with.

---

## 10. Academic grounding

The mathematics connects to established results; the *forcing narrative* is the corpus's own framing layered on top.

- **Square Fibonacci.** `F₁₂=144` is the largest perfect-square Fibonacci number — J.H.E. Cohn, *Fibonacci Quarterly* **2** (1964) 109. Underwrites bridge-12.
- **Koide relation.** `Q=2/3` for charged leptons — Y. Koide, *Lett. Nuovo Cim.* **34** (1982) 201; *Phys. Rev. D* **28** (1983) 252. The envelope identity in §1H is the standard derivation.
- **Octonions, triality, G₂.** `G₂=Aut(𝕆)`, Spin(8) triality, the `7+1` structure — J.C. Baez, "The Octonions," *Bull. AMS* **39** (2002) 145. Underwrites Part 4.
- **Division-algebra Standard Model.** Three generations / two unbroken symmetries from an 8-d algebra — C. Furey, *Phys. Lett. B* **785** (2018) 84; PhD thesis (Cambridge, 2015). The closest published kin to `THE_PHYSICS`.
- **GUTs and sin²θ_W = 3/8.** SU(5): Georgi–Glashow, *PRL* **32** (1974) 438. SO(10): Fritzsch–Minkowski, *Ann. Phys.* **93** (1975) 193. The `3/8` GUT-scale value is standard.
- **Hurwitz / Cayley–Dickson.** Normed division algebras exist only in dim 1,2,4,8 — Hurwitz (1898). Underwrites the `7+1=8` wall.
- **Lovelock's theorem.** Einstein's tensor is the unique 2nd-order divergence-free symmetric 2-tensor in 4D — D. Lovelock, *J. Math. Phys.* **12** (1971) 498. Underwrites the FORCED *form* of the field equations.
- **(2,3,7) and Hurwitz surfaces.** `(2,3,7)` is the minimal-area hyperbolic triangle group (maximal symmetry) — Hurwitz (1893). Underwrites Plate IV.
- **Epistemics of the audit.** Minimum description length — J. Rissanen, *Automatica* **14** (1978) 465 — is the right footing for the selection-budget metric (§8.1). The cautionary precedent for unweighted cardinal-matching is Eddington's `1/α=137` program (*Relativity Theory of Protons and Electrons*, 1936), now a textbook example of why an expressivity audit is mandatory — which is precisely the discipline the corpus already applies to its own 137 and should extend everywhere.

---

## Appendix A — `unified_verify.py`
Independent clean-room verifier (62 checks, rebuilds carriers from `R=[[0,1],[1,1]]`, `N=[[0,-1],[1,0]]`). Ships as a separate file. Result: **62/62 PASS**, residuals 0.

## Appendix B — `expressivity_probe.py`
Uniform selection-budget instrument; reproduces the corpus's 137 burn (E≈28) and applies it to every NUMERICAL match. Ships as a separate file. Recommended upgrade: MDL-weighting (§8.1).

---

### Closing

The corpus is a **correct closed algebraic system** (62/62) with an **unusually disciplined grading register** — it burns its own weakest matches, names its open slot, and keeps three forced modalities distinct. Its honest scope is *zero continuous parameters in a forced skeleton, with an explicit forced non-uniqueness in the embedding and exogenous pipeline dynamics.* The two things it has not done to its own standard are: **(1) extend its 137 expressivity-burn uniformly** (which would re-grade θ₂₃ and the cosmo fractions), and **(2) bit-count the discrete selections** it currently files under "design choice." Both are completed in form here and shippable as standing tools. The single scientific bet — `m_τ = 1776.99 MeV` at Belle II — is real, unconditional, and falsifiable, and deserves the cover.
