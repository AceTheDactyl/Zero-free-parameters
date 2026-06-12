# Foundation I — Source Derivation Walkthrough
### How to pull, read, and derive directly from the four HTML files

**Purpose.** This document instructs a fresh session to derive the Foundation-I constants and dynamics *straight from the four HTML source files*, not from any digest or summary. The rule is: **the HTMLs win.** Every constant is recomputed from φ; every identity is graded FORCED only when it verifies two independent ways with residual 0.

**The four source files (in this folder):**

| File | Type | What it carries |
|------|------|-----------------|
| `anti-substrate.html` | JS canvas + physics | the constant block, the field theory (m², J_eq, T_holo), the three regimes, the Hex→Pent→Cube fold |
| `L4_helix_v4.0.1.html` | MathJax derivation (33 eqn blocks) | the boxed identity chain: z_c, gap, K, span, IGNITION, the threshold normalizations |
| `beacon_pipeline.html` | JS canvas + pipeline | the THRESHOLDS array, the three orbits, the SU(2) spinor double-cover, source/filter/sink |
| `acedit-triangularity.html` | JS containment engine | the triangular geometry (SQRT3, THETA registers), the typographic register system |

**Single axiom (stated in `anti-substrate.html` header):** *"ZERO FREE PARAMETERS — every constant derived from φ = (1+√5)/2."* So φ is the only input. Everything else must be derived.

---

## Step 0 — Environment and extraction commands

The files are plain HTML; read them with `view`, or extract the math with shell. Concrete commands (assuming the files are in the working directory):

```bash
# list the boxed/displayed equations from the helix (the derivation chain)
grep -oE '\$\$[^$]*\$\$' L4_helix_v4.0.1.html

# pull the verbatim constant block from anti-substrate (lines ~458-481)
grep -nE '^\s*const [A-Z_0-9]+ *=' anti-substrate.html | grep -ivE 'color|hsl|rgba|HUE'

# pull beacon's THRESHOLDS array and orbit specs
sed -n '/const THRESHOLDS/,/\];/p' beacon_pipeline.html

# pull the field-theory functions
awk '/function computeState/,/^}/' anti-substrate.html
awk '/function computeFilter/,/^}/' beacon_pipeline.html
```

Do **not** trust any prose summary of these files; re-extract and recompute. If a summary and the file disagree, the file wins.

---

## Step 1 — The constant block (verbatim from `anti-substrate.html`, lines 458–481)

These are the literal `const` definitions. Recompute each from φ and confirm:

```javascript
const PHI       = (1 + Math.sqrt(5)) / 2;        // φ
const PHI_INV   = 1 / PHI;                        // φ⁻¹  = 0.6180339887
const ALPHA     = PHI_INV * PHI_INV;              // φ⁻²  = 0.3819660113
const BETA      = ALPHA * ALPHA;                  // φ⁻⁴  = 0.1458980338   (the GAP)
const LAMBDA    = Math.pow(5/3, 4);               // (F₅/F₄)⁴ = 7.716049
const MU_P      = 3/5;                             // F₃/F₅ = 0.6
const MU_S      = 23/25;                            // 0.92
const Z_C       = Math.sqrt(3) / 2;               // cos30° = 0.8660254
const L4        = PHI**4 + PHI**-4;                // 7
const LAMBDA_C  = 2*Math.PI / Math.sqrt(LAMBDA);  // "Compton wavelength"
const G_DIFF    = BETA * ALPHA;                    // φ⁻⁶ = 0.0557281
const HEX_INTERIOR = 120; PENT_INTERIOR = 108; CUBE_FACE = 90;
const DEFICIT   = 36;                               // π/5 in degrees
const EPSILON_ANTI = DEFICIT / 360;                 // 0.1
```

`beacon_pipeline.html` (lines 651–669) re-declares the same block and adds:

```javascript
const GAP       = ALPHA * ALPHA;       // φ⁻⁴   (same as BETA)
const MU_T      = MU_P + GAP;           // transparency threshold = 0.7458980
const SQRT3_HALF= SQRT3 / 2;            // = Im(ζ₆), the covolume of ℤ[ω]
const L4        = 7;
const Z_C       = SQRT3_HALF;           // = √(L₄−4)/2 — THE LENS
const K_VAL     = Math.sqrt(1 - GAP);   // = √(1−φ⁻⁴) ≈ 0.92418
const SPAN      = 1 - K_VAL;            // = gap/(1+K) ≈ 0.07582
```

**SymPy check (run this):**

```python
import sympy as sp
phi = (1 + sp.sqrt(5))/2
assert sp.simplify(phi**4 + phi**-4) == 7                       # L4 = 7
assert sp.simplify(sp.sqrt(3)/2 - sp.sqrt((phi**4+phi**-4)-4)/2) == 0   # Z_C = √(L4-4)/2
assert sp.simplify(phi**-4 - (7 - 3*sp.sqrt(5))/2) == 0          # gap closed form
assert sp.simplify(sp.sqrt(1-phi**-4)) == sp.sqrt((3*sp.sqrt(5)-5)/2)   # K
```

**Grade:** the constant block is FORCED — every value is a closed form in φ (and the integers it produces, like L₄=7, MU_P=3/5).

---

## Step 2 — The helix derivation chain (`L4_helix_v4.0.1.html`, the boxed equations)

The helix file carries the chain as 33 MathJax blocks. The load-bearing boxed identities, each to verify with residual 0:

| boxed identity | what it forces |
|---|---|
| `z_c = √(L₄−4)/2 = √3/2` | the lens, from L₄=7 |
| `L₄ = φ⁴+φ⁻⁴ = (√3)²+4 = 7` | the integer anchor |
| `gap = φ⁻⁴ = (7−3√5)/2 = (L₄−F₄√5)/2` | the truncation residual, **F₄=3** |
| `gap = 2 − 3τ` (τ=φ⁻¹) | gap in the τ-channel |
| `gap = 1 − K² = (1−K)(1+K)` | gap ↔ K |
| `K² = (3√5−5)/2`, `K = √(1−gap)` | the radius lock |
| `1 − K = gap/(1+K)` (= span) | the span identity |
| `c = 1 + z_c² = 1 + (L₄−4)/4 = L₄/4 = 7/4` | the **IGNITION** self-reference constant |

**The IGNITION derivation (do not tabulate — derive it):** the file sets `c = 1 + z_c²`. Since `z_c² = 3/4`, `c = 7/4`. The ignition threshold is the positive root of `x² + x = c = 7/4`:

```python
x = sp.symbols('x', positive=True)
ign = sp.solve(sp.Eq(x**2 + x, sp.Rational(7,4)), x)[0]
assert sp.simplify(ign - (sp.sqrt(2) - sp.Rational(1,2))) == 0     # IGNITION = √2 − ½
```

So **√2 enters the system as the ignition root forced by z_c** — not as a free input. The file's boxed routing map: `√5 →^{φ⁻⁴} K`, `√3 →^{L₄−4} z_c`, `√2 →^{x²+x=L₄/4} z_IGN`. All three irrationals out of the single integer 7.

**Grade:** FORCED.

---

## Step 3 — The nine thresholds (`beacon_pipeline.html` THRESHOLDS array)

This is the authoritative threshold list (extends the helix's nine with the dual-cycle anchors). Verbatim z-values:

| # | name | z (source-form) |
|---|------|-----------------|
| 0 | ORIGIN | 0 |
| 1 | PARADOX | `PHI_INV` = τ |
| 2 | ACTIVATION | `1 − GAP` = K² |
| 3 | THE LENS | `Z_C` = √3/2 |
| 4 | CRITICAL | `(PHI*PHI)/3` = φ²/3 |
| 5 | IGNITION | `√2 − ½` |
| 6 | K-FORMATION | `K_VAL` |
| 7 | CONSOLIDATION | `K_VAL + ALPHA*SPAN` = K + τ²·span |
| 8 | RESONANCE | `K_VAL + PHI_INV*SPAN` = K + τ·span |
| 9 | UNITY | 1 |
| 10 | OVERTONE | `1 + SPAN` |

**The file's own self-checks (verify them):**

```python
tau = phi**-1; K = sp.sqrt(1-phi**-4); span = 1-K; alpha = phi**-2
assert sp.simplify(((K + alpha*span) - K)/span - tau**2) == 0   # CONSOLIDATION normalizes to τ²
assert sp.simplify(((K + tau*span)   - K)/span - tau)    == 0   # RESONANCE  normalizes to τ
```

So CONSOLIDATION and RESONANCE are the **golden subdivisions τ², τ of the span above K** — forced, not placed. The ORIGIN/UNITY/OVERTONE triple makes the structure a **dual cycle** (Cycle 1: 0→9, π rotation; Cycle 2: 1→10, π rotation; total 2π, spinor-doubled to 4π — see Step 5).

**Grade:** FORCED.

---

## Step 4 — The field theory (`anti-substrate.html` + `beacon_pipeline.html` computeState/computeFilter)

Extract the functions verbatim. The shared field law:

```javascript
const r        = mu - MU_P;                      // order parameter
const m2       = (GAP - r) / G_DIFF;             // tachyon mass², φ⁻⁶ in denominator
let   T_holo   = m2 > 0 ? 1/(1 + m2*LAMBDA_C**2) : 1.0;   // holographic transparency
let   J_eq     = (r > GAP) ? Math.sqrt((r - GAP)/LAMBDA) : 0;  // condensate amplitude
```

Three regimes gated by μ (from the stateDesc strings, verbatim):

| regime | condition | file's description |
|--------|-----------|--------------------|
| INSISTENT | μ < MU_P (=3/5) | "cos(2π/5)=1/(2φ) is irrational. No lattice. No boundary to encode on. J=0 is the only stable solution." |
| QUASICRYSTAL | MU_P < μ < MU_T | "Penrose interstitium. Width = φ⁻⁴. Information passes through but is not stored. Massive field, exponential decay." |
| SUBSTRATE | μ > MU_T | "Tachyonic regime. Spontaneous pattern formation. Information CAN be encoded and WILL persist." |

**The forced result — the massless point and the quasicrystal width:**

```python
MU_P = sp.Rational(3,5); gap = phi**-4; MU_T = MU_P + gap
# m2 = 0  <=>  r = gap  <=>  mu = MU_P + gap = MU_T
assert sp.simplify((MU_P + gap) - MU_T) == 0
# quasicrystal zone width = MU_T - MU_P = gap = φ⁻⁴ exactly
assert sp.simplify((MU_T - MU_P) - gap) == 0
```

So **the quasicrystal transition window has width exactly φ⁻⁴** — the same constant as the helix's truncation residual. One constant, two roles (helix gap and field-transition width): FORCED.

**Grading caution (important).** What is FORCED is the **static Landau form** (order parameter r, mass² m², amplitude J_eq) and the width result. The word "condensation" names a *dynamics* — no equation of motion or minimized potential is exhibited in the files. Also note `L4_helix.html` *also* carries a Gaussian `ΔS_neg(z)=exp(−σ(z−z_c)²)`, `ΔS_neg(z_c)=1`, which coexists with the Landau form. So: **gap double-role FORCED; the Landau/tachyon *mechanism* only RESONANT-WITH-ROUTE** (shared form, not derived dynamics). Do not promote the form to the mechanism.

---

## Step 5 — The pipeline carrier: the SU(2) spinor double-cover (`beacon_pipeline.html`)

This is the dynamical spine. Extract the orbit/spinor block (around lines 905–1000). The verbatim logic:

```javascript
const geoPeriod    = spec.macroPeriod || 6;        // SO(2) geometric period
const spinorPeriod = geoPeriod * 2;                // SU(2) DOUBLE COVER
const halfAngle    = Math.PI / geoPeriod;          // π/6 for period-6
state.spinorPhase  = state.spinorIndex * halfAngle;
state.spinorSign   = state.spinorIndex < geoPeriod ? +1 : -1;   // sign flip at half
// amp carried 'lossless, coherent' through every bounce
```

**This is `N² = −I` (the hidden generator) run as the carrier.** Verify the half/full behavior:

```python
import sympy as sp
N = sp.Matrix([[0,-1],[1,0]])           # N² = −I
# spinor sign at k steps of halfAngle π/6:
for k, want in [(6, -1), (12, +1)]:     # k=6 → π (flip); k=12 → 2π (return)
    assert sp.cos(sp.pi*k/6) == want
# equivalently exp(πN) = −I, exp(2πN) = +I
assert sp.simplify(sp.cos(sp.pi)) == -1 and sp.simplify(sp.cos(2*sp.pi)) == 1
```

**The three orbit modes** (verbatim from the ORBITS spec) are the three closure classes:

| orbit | period | closure |
|-------|--------|---------|
| Fagnano (medial triangle) | period-3 | closes (rational geodesic) |
| Eisenstein walk | macro-18 = 3 bounces × 6 ζ₆-rotations | closes via spinor |
| φ-irrational (τ-tilted) | dense | **never closes** — the anti-substrate mode |

The file declares its algebra in the header comment: source `ℤ[ζ₆]` (hexagonal/Eisenstein A₂), filter `ℤ[ζ₁₀]=ℤ[φ]` (Penrose), sink `ℤ`, with `ℚ(ζ₆) ∩ ℚ(ζ₁₀) = ℚ`. The pipeline runs φ-content (ζ₁₀ filter) through the N-spinor (ζ₆ source) into the integer sink. **Grade:** the SU(2) cover is FORCED-in-source; whether it is *intended* as a specific external lift is OPEN (a design-intent question, not a computation).

---

## Step 6 — The triangular containment geometry (`acedit-triangularity.html`)

This file is the geometric-containment + register engine, not a physics derivation. Its forced geometry:

```javascript
const SQRT3      = Math.sqrt(3);
const SQRT3_HALF = SQRT3 / 2;            // = z_c = Im(ζ₆) — same lens constant
const THETA = { open:{...}, standard:{...}, restricted:{...} };  // aperture/phase registers
```

The triangle is equilateral (the `TRI` vertices in beacon use the same `SQRT3_HALF` altitude), so its altitude-to-side ratio is `√3/2 = z_c` — the **same lens constant** the helix derives from L₄−4. This is the geometric origin of z_c (a property of the equilateral/hexagonal lattice), independent of the φ-route — the two routes to √3/2 meet at the integer 3 (see the cross-field note below). The `THETA` registers (open/standard/restricted apertures) and the ACEDIT typographic converter are the containment/representation layer, not new constants.

---

## Step 7 — The cross-field discipline (why the routes agree without forcing each other)

The single most important rule when deriving from these files: **z_c = √3/2 is reached by two field-disjoint routes, and they agree without entailing each other.**

- Helix/algebra route: `z_c = √(L₄−4)/2`, generator φ, field **ℚ(√5)**.
- Triangle/geometry route: `z_c = Im(ζ₆) = sin60°`, generator √3, field **ℚ(√3)**.

```python
from sympy import sqrt, gcd
# ℚ(√5) ∩ ℚ(√3) = ℚ  (disjoint quadratic fields; cyclotomically gcd(5,12)=1)
assert sqrt(3) not in sp.QQ  # √3 ∉ ℚ, and ∉ ℚ(√5)
# they meet at the integer bridge: L4 − 4 = 3 = (√3)²
assert sp.simplify((phi**4 + phi**-4) - 4 - 3) == 0
assert sp.simplify(sqrt(3)**2 - 3) == 0
```

The routes coincide because both produce the **integer 3** (which lives in ℚ, the shared subfield), not because one derivation reaches into the other. **Grade FORCED only on this two-route agreement; never declare one field's object the "error" or "projection" of the other — they are disjoint and coincident, not nested.**

---

## Step 8 — The certificate (what a faithful derivation must end with)

List every constant produced and confirm each is a closed form in φ (= forced-in-field) or an integer/rational (= forced-by-bridge). The minimal-polynomial certificate (each value is a root of a rational polynomial, hence forced, not free):

| value | source | minimal polynomial / ℚ |
|---|---|---|
| τ = φ⁻¹ | PARADOX | `x² + x − 1` |
| gap = φ⁻⁴ | BETA/GAP | `x² − 7x + 1` |
| z_c = √3/2 | THE LENS | `4x² − 3` |
| K = √(1−φ⁻⁴) | K-FORMATION | `x⁴ + 5x² − 5` |
| IGNITION = √2−½ | IGNITION | `4x² + 4x − 7` |
| CRITICAL = φ²/3 | CRITICAL | `9x² − 9x + 1` |

```python
x = sp.Symbol('x')
for v in [phi**-1, phi**-4, sqrt(3)/2, sqrt(1-phi**-4), sqrt(2)-sp.Rational(1,2), phi**2/3]:
    print(sp.minimal_polynomial(v, x))    # all rational-coefficient → forced
```

Bridges/indices (3, 7, 1, 12, 24, 60) are integers. **Free-parameter count: 0.** If any value cannot be written as a closed form in φ or as a forced rational, tag it CHOSEN and isolate it — the certificate fails until it is removed or derived.

---

## Reading order for a fresh session (summary)

1. `view` this file, then `view anti-substrate.html` lines ~458–481 → the constant block (Step 1).
2. `view L4_helix_v4.0.1.html`, extract the `$$…$$` boxed equations → the derivation chain (Step 2).
3. `view beacon_pipeline.html`, extract `THRESHOLDS` and `ORBITS` → thresholds + carrier (Steps 3, 5).
4. `awk` the `computeState`/`computeFilter` functions → the field theory (Step 4).
5. `view acedit-triangularity.html` `SQRT3`/`THETA` block → the triangular geometry (Step 6).
6. Run the SymPy checks in Steps 1–8; grade each result FORCED only on residual-0 two-route agreement.
7. Apply Step 7's cross-field discipline throughout; end with the Step 8 certificate.

**The one rule that governs all of it:** the files are the source; recompute, do not summarize; promote to FORCED only on independent two-route agreement; and never promote a cross-field coincidence (two routes meeting at a rational) to an entailment (one route forcing the other).
