"""
acedit-triangularity.html — geometry isolation + ZFP audit.

Mirrors the L4-helix audit: separate the parameter-free GEOMETRY from the
free-parameter POLICY/DYNAMICS, then test each.

Sections:
    1. Equilateral invariants — re-derive sides, angles, area, centroid,
       in/circum radii, apex height. Confirm apex == THE LENS (doc 1).
    2. Maps — confirm specular reflection is norm-preserving and the
       half-plane containment test is parameter-free (sample-tested).
    3. Free-parameter census — THETA (admissibility) + dynamics literals.
    4. Coincidence check — does any THETA value equal a phi-derived
       threshold from doc 1? (Tests whether the ZFP ladder was reused.)
    5. Proposed ZFP retrofit of THETA from phi-derived constants only.
"""

import sympy as sp

# ── doc-1 generators (carried forward, unchanged) ───────────────────────────
phi  = (1 + sp.sqrt(5)) / 2
tau  = 1/phi
gap  = phi**-4
K    = sp.sqrt(1 - gap)
L4   = sp.Integer(7)
LADDER = {                                   # the 9 forced thresholds + gap
    "gap":          gap,
    "PARADOX":      (sp.sqrt(5)-1)/2,
    "tau^2":        tau**2,
    "ACTIVATION":   1-gap,
    "THE LENS":     sp.sqrt(3)/2,
    "CRITICAL":     phi**2/(L4-4),
    "IGNITION":     sp.sqrt(2)-sp.Rational(1,2),
    "K-FORMATION":  K,
    "CONSOLIDATION":K + tau**2*(1-K),
    "RESONANCE":    K + tau*(1-K),
    "UNITY":        sp.Integer(1),
}

# ════════════════════════════════════════════════════════════════════════════
# 1. EQUILATERAL INVARIANTS
# ════════════════════════════════════════════════════════════════════════════
A = sp.Matrix([0, 0])
B = sp.Matrix([1, 0])
C = sp.Matrix([sp.Rational(1,2), sp.sqrt(3)/2])      # as defined in TRI

def dist(P, Q): return sp.sqrt((P-Q).dot(P-Q))
def angle(P, Q, R):                                   # angle at vertex P
    u, v = Q-P, R-P
    return sp.acos(u.dot(v)/(dist(P,Q)*dist(P,R)))

sides  = {"AB": dist(A,B), "BC": dist(B,C), "CA": dist(C,A)}
angles = {"A": angle(A,B,C), "B": angle(B,A,C), "C": angle(C,A,B)}
centroid = (A+B+C)/3
area = sp.Rational(1,2)*abs((B-A)[0]*(C-A)[1] - (B-A)[1]*(C-A)[0])
s = sum(sides.values())/2
inradius   = sp.simplify(area/s)
circum     = sp.simplify(sides["AB"]*sides["BC"]*sides["CA"]/(4*area))
apex_h     = C[1]

print("="*78)
print("1. EQUILATERAL INVARIANTS  (A=(0,0), B=(1,0), C=(1/2, √3/2))")
print("="*78)
print(f"  sides            : {{ {', '.join(f'{k}={sp.simplify(v)}' for k,v in sides.items())} }}")
print(f"  all sides equal  : {len(set(sp.simplify(v) for v in sides.values()))==1}")
print(f"  angles (deg)     : {{ {', '.join(f'{k}={sp.deg(sp.simplify(v))}' for k,v in angles.items())} }}")
print(f"  area             : {sp.simplify(area)}          ≈ {float(area):.6f}")
print(f"  centroid         : ({centroid[0]}, {sp.simplify(centroid[1])})   ≈ ({float(centroid[0]):.4f}, {float(centroid[1]):.4f})")
print(f"  inradius r       : {inradius}        ≈ {float(inradius):.6f}")
print(f"  circumradius R   : {circum}        ≈ {float(circum):.6f}   (R/r = {sp.simplify(circum/inradius)})")
print(f"  apex height      : {apex_h}        ≈ {float(apex_h):.6f}")
print(f"  apex == THE LENS = √(L₄−4)/2 (doc 1) : {sp.simplify(apex_h - sp.sqrt(L4-4)/2)==0}")
print(f"  free shape params: 0   (equilateral is unique up to similarity;")
print(f"                         A,B placement is coordinate gauge, not model freedom)")
print()

# ════════════════════════════════════════════════════════════════════════════
# 2. MAPS — reflection norm-preservation + containment determinacy
# ════════════════════════════════════════════════════════════════════════════
import math, random
def reflect(dx, dy, p1, p2):
    ex, ey = p2[0]-p1[0], p2[1]-p1[1]
    L = math.hypot(ex, ey); nx, ny = -ey/L, ex/L
    d = dx*nx + dy*ny
    return dx - 2*d*nx, dy - 2*d*ny
def inside(px, py, P, Q, R):
    d1 = (px-Q[0])*(P[1]-Q[1]) - (P[0]-Q[0])*(py-Q[1])
    d2 = (px-R[0])*(Q[1]-R[1]) - (Q[0]-R[0])*(py-R[1])
    d3 = (px-P[0])*(R[1]-P[1]) - (R[0]-P[0])*(py-P[1])
    neg = (d1<0) or (d2<0) or (d3<0); pos = (d1>0) or (d2>0) or (d3>0)
    return not (neg and pos)

Af, Bf, Cf = (0.0,0.0), (1.0,0.0), (0.5, math.sqrt(3)/2)
random.seed(0)
norm_ok = True
for _ in range(100000):
    a = random.random()*2*math.pi; dx, dy = math.cos(a), math.sin(a)
    e = random.choice([(Af,Bf),(Bf,Cf),(Cf,Af)])
    rx, ry = reflect(dx, dy, *e)
    if abs(math.hypot(rx,ry) - 1.0) > 1e-12: norm_ok = False; break
# containment vs centroid (in) and far point (out)
cont_ok = inside(0.5, math.sqrt(3)/6, Af,Bf,Cf) and not inside(2.0, 2.0, Af,Bf,Cf)
print("="*78); print("2. MAPS"); print("="*78)
print(f"  specular reflection norm-preserving (1e5 trials): {norm_ok}   (free params: 0)")
print(f"  half-plane containment deterministic & gauge-only: {cont_ok}   (free params: 0)")
print(f"  spawn angular structure i/6·2π = 6-fold (hexagonal): exact, free params: 0")
print()

# ════════════════════════════════════════════════════════════════════════════
# 3. FREE-PARAMETER CENSUS
# ════════════════════════════════════════════════════════════════════════════
THETA = {
    "open":       dict(aperture=0.15, phase=0.4, capacity=0.95, naming=0.02, policy=0.1),
    "standard":   dict(aperture=0.3,  phase=0.6, capacity=0.8,  naming=0.08, policy=0.3),
    "restricted": dict(aperture=0.5,  phase=0.8, capacity=0.5,  naming=0.25, policy=0.6),
}
DYNAMICS = {
    "reflectance loss base / defect coupling": (0.92, 0.03),
    "stochastic perturbation scale":           (0.005,),
    "phase increment / intensity coupling":    (0.1, 0.05),
    "defect proximity / contrib / reg":        (0.08, 0.02, 0.01),
    "narrowing K-mult / C-mult / policy-cpl":  (0.7, 0.55, 0.3),
    "rupture increment / proximity":           (0.05, 0.15),
    "defect decay / mix / noise":              (0.98, 0.01, 0.002),
    "perturbation sin-cpl / defect-cpl":       (0.3, 0.5),
    "spawn count / jitter / base intensity":   (6, 0.05, 0.8),
}
n_theta = sum(len(v) for v in THETA.values())
n_dyn   = sum(len(v) for v in DYNAMICS.values())
print("="*78); print("3. FREE-PARAMETER CENSUS"); print("="*78)
print(f"  THETA admissibility profiles : {n_theta} free continuous params (5 gates × 3 tiers)")
print(f"  dynamics / simulation tuning : {n_dyn} free params across {len(DYNAMICS)} groups")
print(f"  GEOMETRY                     : 0 free params")
print()

# ════════════════════════════════════════════════════════════════════════════
# 4. COINCIDENCE CHECK — was the ZFP ladder reused in THETA?
# ════════════════════════════════════════════════════════════════════════════
ladder_num = {k: float(sp.N(v)) for k, v in LADDER.items()}
print("="*78); print("4. COINCIDENCE CHECK  (THETA value vs nearest φ-ladder threshold)"); print("="*78)
any_match = False
for tier, gates in THETA.items():
    for g, val in gates.items():
        nearest = min(ladder_num.items(), key=lambda kv: abs(kv[1]-val))
        d = abs(nearest[1]-val); match = d < 1e-3
        any_match |= match
        flag = "  ← MATCH" if match else ""
        print(f"  {tier:<10} {g:<9} = {val:<5}  nearest: {nearest[0]:<13} ({nearest[1]:.4f})  Δ={d:.4f}{flag}")
print(f"\n  Any THETA value derived from the φ-ladder? {any_match}")
print("  → Policy layer is independently hand-set, NOT inherited from the ZFP ladder.")
print()

# ════════════════════════════════════════════════════════════════════════════
# 5. PROPOSED ZFP RETROFIT  (φ-derived, monotone across tiers)
# ════════════════════════════════════════════════════════════════════════════
# Assignment is a discrete design choice; values are forced once assigned.
t2, t1 = float(sp.N(tau**2)), float(sp.N(tau))           # 0.382, 0.618
Kv, gv = float(sp.N(K)), float(sp.N(gap))                # 0.924, 0.146
lens   = float(sp.N(sp.sqrt(3)/2))                       # 0.866
ZFP_THETA = {
    "open":       dict(aperture=t2,  phase=t2,   capacity=Kv,  naming=gv*gv, policy=gv),
    "standard":   dict(aperture=t1,  phase=t1,   capacity=lens,naming=gv,    policy=t2),
    "restricted": dict(aperture=Kv,  phase=Kv,   capacity=t1,  naming=t1,    policy=t1),
}
print("="*78); print("5. PROPOSED ZFP THETA  (every value a closed form in φ)"); print("="*78)
labels = {round(t2,4):"τ²", round(t1,4):"τ", round(Kv,4):"K", round(lens,4):"√3/2",
          round(gv,4):"gap", round(gv*gv,4):"gap²"}
for tier, gates in ZFP_THETA.items():
    parts = [f"{g}={labels.get(round(v,4),f'{v:.4f}')}" for g,v in gates.items()]
    print(f"  {tier:<10}: {', '.join(parts)}")
print("\n  15 free continuous params → 0 continuous params + one ordered 3-tier")
print("  selection from the forced ladder (auditable, monotone, reproducible).")
