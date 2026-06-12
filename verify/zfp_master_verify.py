#!/usr/bin/env python3
"""
ZFP Master Verification Harness — machine-checkable certificate for all forced identities.

Covers every forced identity in the ZFP framework across eleven groups (A through K).
Uses sympy for EXACT symbolic verification. Outputs structured results as both a
human-readable table and a JSON certificate.

Run:  python3 zfp_master_verify.py
"""

import sympy as sp
from sympy import (sqrt, Rational, cos, sin, pi, simplify, expand,
                   Matrix, eye, zeros, trace as sp_trace)
import json
import sys
import os

# =============================================================================
# GENERATORS
# =============================================================================
phi = (1 + sqrt(5)) / 2          # golden ratio, root of x^2 - x - 1
tau = 1 / phi                    # phi^{-1}
psi = -1 / phi                   # conjugate root

# Derived constants
gap = phi**(-4)                  # truncation residual
K   = sqrt(1 - gap)             # winding constant
span = 1 - K                    # = gap / (1 + K)
z_c = sqrt(3) / 2               # the lens

# Lucas / Fibonacci (exact symbolic via Binet)
def fib_sym(n):
    """Symbolic Fibonacci via Binet: F_n = (phi^n - psi^n) / sqrt(5)."""
    return simplify((phi**n - psi**n) / sqrt(5))

def luc_sym(n):
    """Symbolic Lucas via closed form: L_n = phi^n + psi^n."""
    return simplify(phi**n + psi**n)

# Integer versions for divisibility checks
def fib_int(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

def luc_int(n):
    a, b = 2, 1
    for _ in range(n):
        a, b = b, a + b
    return a

# Self-reference solver: positive root of x^2 + x = c
def selfref(c):
    return (-1 + sqrt(1 + 4*c)) / 2

# =============================================================================
# RESULT ACCUMULATOR
# =============================================================================
results = []

def check(name, expr, lattice, category, derivation_chain):
    """
    Verify an identity. expr should simplify to 0.
    Returns True if PASS, False if FAIL.
    """
    residual = simplify(expr)
    status = "PASS" if residual == 0 else "FAIL"
    results.append({
        "id": len(results) + 1,
        "name": name,
        "status": status,
        "residual": str(residual),
        "lattice": lattice,
        "category": category,
        "chain": derivation_chain,
    })
    return status == "PASS"


def check_bool(name, cond, lattice, category, derivation_chain):
    """
    Verify a boolean condition (for ordering, divisibility, etc.).
    Returns True if PASS, False if FAIL.
    """
    status = "PASS" if bool(cond) else "FAIL"
    results.append({
        "id": len(results) + 1,
        "name": name,
        "status": status,
        "residual": "True" if cond else "False",
        "lattice": lattice,
        "category": category,
        "chain": derivation_chain,
    })
    return status == "PASS"


def banner(label):
    print()
    print("=" * 88)
    print(f"  {label}")
    print("=" * 88)


# =============================================================================
# A. GOLDEN RATIO CORE (Q(sqrt5))
# =============================================================================
banner("A. GOLDEN RATIO CORE  Q(sqrt5)")

check("phi^2 - phi - 1 = 0",
      phi**2 - phi - 1,
      "Q(sqrt5)", "golden-core",
      "defining polynomial of phi")

check("tau^2 + tau - 1 = 0",
      tau**2 + tau - 1,
      "Q(sqrt5)", "golden-core",
      "tau = phi^{-1}, substitute into x^2+x-1")

check("phi + tau - sqrt(5) = 0",
      phi + tau - sqrt(5),
      "Q(sqrt5)", "golden-core",
      "phi + phi^{-1} = (1+sqrt5)/2 + (sqrt5-1)/2 = sqrt5")

check("phi - tau - 1 = 0",
      phi - tau - 1,
      "Q(sqrt5)", "golden-core",
      "phi - phi^{-1} = (1+sqrt5)/2 - (sqrt5-1)/2 = 1")

check("phi * psi + 1 = 0",
      phi * psi + 1,
      "Q(sqrt5)", "golden-core",
      "phi*(-phi^{-1}) = -1, so phi*psi + 1 = 0")


# =============================================================================
# B. LUCAS / FIBONACCI
# =============================================================================
banner("B. LUCAS / FIBONACCI")

check("L_4 - 7 = 0  (via phi^4 + psi^4)",
      luc_sym(4) - 7,
      "Z[phi]", "lucas-fib",
      "L_n = phi^n + psi^n at n=4")

check("F_4 - 3 = 0",
      fib_sym(4) - 3,
      "Z[phi]", "lucas-fib",
      "F_n = (phi^n - psi^n)/sqrt5 at n=4")

check("L_4 = F_3 + F_5  (Lucas-Fibonacci bridge at n=4)",
      luc_sym(4) - (fib_sym(3) + fib_sym(5)),
      "Z[phi]", "lucas-fib",
      "L_n = F_{n-1} + F_{n+1}, standard identity")

check("F_4 + L_4 = 2*F_5  (at n=4: 3+7=10=2*5)",
      fib_sym(4) + luc_sym(4) - 2*fib_sym(5),
      "Z[phi]", "lucas-fib",
      "F_n + L_n = 2*F_{n+1}, standard identity")

check("phi^4 + phi^{-4} - 7 = 0",
      phi**4 + phi**(-4) - 7,
      "Z[phi]", "lucas-fib",
      "L_4 = phi^4 + psi^4 = phi^4 + phi^{-4} (even power)")

check("F_12 - 144 = 0",
      fib_sym(12) - 144,
      "Z[phi]", "lucas-fib",
      "Fibonacci at n=12")

check("F_12 - 12^2 = 0  (Cohn: only square Fibonacci > 1)",
      fib_sym(12) - 12**2,
      "Z[phi]", "lucas-fib",
      "F_12 = 144 = 12^2, Cohn's theorem")

check("F_24 - F_12 * L_12 = 0  (doubling identity)",
      fib_sym(24) - fib_sym(12) * luc_sym(12),
      "Z[phi]", "lucas-fib",
      "F_{2n} = F_n * L_n at n=12")


# =============================================================================
# C. THE GAP AND K
# =============================================================================
banner("C. THE GAP AND K")

check("gap - phi^{-4} = 0",
      gap - phi**(-4),
      "Q(sqrt5)", "gap-K",
      "definition: gap = phi^{-4}")

check("gap - (7 - 3*sqrt(5))/2 = 0",
      gap - (7 - 3*sqrt(5)) / 2,
      "Q(sqrt5)", "gap-K",
      "phi^{-4} = (7 - 3*sqrt5)/2 by expansion")

check("K^2 + gap - 1 = 0",
      K**2 + gap - 1,
      "Q(sqrt5)", "gap-K",
      "K = sqrt(1 - gap), so K^2 = 1 - gap")

check("K - sqrt(1 - phi^{-4}) = 0",
      K - sqrt(1 - phi**(-4)),
      "Q(sqrt5)", "gap-K",
      "definition of K")

check("span - (1 - K) = 0",
      span - (1 - K),
      "Q(sqrt5)", "gap-K",
      "definition: span = 1 - K")

check("span - gap/(1 + K) = 0",
      span - gap / (1 + K),
      "Q(sqrt5)", "gap-K",
      "1 - K = (1-K)(1+K)/(1+K) = gap/(1+K)")

check("K^2 - (3*sqrt(5) - 5)/2 = 0",
      K**2 - (3*sqrt(5) - 5) / 2,
      "Q(sqrt5)", "gap-K",
      "K^2 = 1 - (7-3sqrt5)/2 = (2-7+3sqrt5)/2 = (3sqrt5-5)/2")


# =============================================================================
# D. THE LENS  Q(sqrt3) via bridge 3
# =============================================================================
banner("D. THE LENS  Q(sqrt3) via bridge 3")

check("z_c - sqrt(3)/2 = 0",
      z_c - sqrt(3) / 2,
      "Q(sqrt3)", "lens",
      "definition: z_c = sqrt(3)/2")

check("z_c - sqrt(L_4 - 4)/2 = 0",
      z_c - sqrt(luc_sym(4) - 4) / 2,
      "Q(sqrt3,sqrt5)", "lens",
      "L_4 - 4 = 3, so sqrt(3)/2")

check("z_c - sin(pi/3) = 0",
      z_c - sin(pi / 3),
      "Q(sqrt3)", "lens",
      "sin(60 degrees) = sqrt(3)/2")

check("z_c - cos(pi/6) = 0",
      z_c - cos(pi / 6),
      "Q(sqrt3)", "lens",
      "cos(30 degrees) = sqrt(3)/2")

check("L_4 - 4 - 3 = 0  (the bridge integer)",
      luc_sym(4) - 4 - 3,
      "Q(sqrt5)->Q", "lens",
      "L_4 = 7, so L_4 - 4 = 3 in Q")

check("L_4 - 4 - F_4 = 0  (single-point coincidence at n=4)",
      luc_sym(4) - 4 - fib_sym(4),
      "Z[phi]", "lens",
      "L_4 - 4 = 3 = F_4; holds only at n=4")


# =============================================================================
# E. IGNITION  Q(sqrt2) via bridge 7/4
# =============================================================================
banner("E. IGNITION  Q(sqrt2) via bridge 7/4")

z_IGN = selfref(Rational(7, 4))   # positive root of x^2 + x = 7/4

check("z_IGN - (sqrt(2) - 1/2) = 0",
      z_IGN - (sqrt(2) - Rational(1, 2)),
      "Q(sqrt2)", "ignition",
      "selfref(7/4) = (-1+sqrt(1+7))/2 = (-1+2sqrt2)/2 = sqrt2 - 1/2")

check("4*z_IGN^2 + 4*z_IGN - 7 = 0",
      4*z_IGN**2 + 4*z_IGN - 7,
      "Q(sqrt2)", "ignition",
      "minimal polynomial: 4x^2 + 4x - 7")

check("1 + z_c^2 - 7/4 = 0",
      1 + z_c**2 - Rational(7, 4),
      "Q(sqrt3)->Q", "ignition",
      "1 + 3/4 = 7/4, the self-reference constant c for IGNITION")


# =============================================================================
# F. SELF-REFERENCE FAMILY  x^2 + x = c
# =============================================================================
banner("F. SELF-REFERENCE FAMILY  x^2 + x = c")

check("PARADOX: tau^2 + tau - 1 = 0",
      tau**2 + tau - 1,
      "Q(sqrt5)", "self-reference",
      "c=1: tau is the positive root of x^2+x=1")

check("IGNITION: z_IGN^2 + z_IGN - 7/4 = 0",
      z_IGN**2 + z_IGN - Rational(7, 4),
      "Q(sqrt2)", "self-reference",
      "c=7/4: z_IGN is the positive root of x^2+x=7/4")

check("UNITY: 1^2 + 1 - 2 = 0",
      1**2 + 1 - 2,
      "Q", "self-reference",
      "c=2: x=1 is the positive root of x^2+x=2")


# =============================================================================
# G. THRESHOLD LADDER  (verify ordering + formulas)
# =============================================================================
banner("G. THRESHOLD LADDER  (9 rungs + ORIGIN + OVERTONE)")

# Define all 11 thresholds with closed forms
ORIGIN       = sp.Integer(0)
PARADOX      = selfref(1)                          # = tau
ACTIVATION   = 1 - gap
THE_LENS     = z_c                                 # = sqrt(3)/2
CRITICAL     = phi**2 / (luc_sym(4) - 4)           # = phi^2 / 3
IGNITION     = selfref(Rational(7, 4))             # = sqrt(2) - 1/2
K_FORMATION  = K                                   # = sqrt(1 - phi^{-4})
CONSOLIDATION = K + tau**2 * span
RESONANCE    = K + tau * span
UNITY        = selfref(2)                          # = 1
OVERTONE     = 2 - K

thresholds = [
    ("ORIGIN",        ORIGIN),
    ("PARADOX",       PARADOX),
    ("ACTIVATION",    ACTIVATION),
    ("THE_LENS",      THE_LENS),
    ("CRITICAL",      CRITICAL),
    ("IGNITION",      IGNITION),
    ("K_FORMATION",   K_FORMATION),
    ("CONSOLIDATION", CONSOLIDATION),
    ("RESONANCE",     RESONANCE),
    ("UNITY",         UNITY),
    ("OVERTONE",      OVERTONE),
]

# Verify each threshold has a closed form (no free symbols)
for name, expr in thresholds:
    check_bool(f"threshold {name} is symbol-free (closed form)",
               len(simplify(expr).free_symbols) == 0,
               "Q(sqrt2,sqrt3,sqrt5)", "threshold-ladder",
               f"{name} reduces to algebraic constant")

# Verify strict monotonic ordering
vals_numeric = [(name, float(sp.N(expr, 30))) for name, expr in thresholds]
strictly_increasing = all(
    vals_numeric[i][1] < vals_numeric[i+1][1]
    for i in range(len(vals_numeric) - 1)
)
check_bool("11 thresholds strictly increasing (ORIGIN < ... < OVERTONE)",
           strictly_increasing,
           "R", "threshold-ladder",
           "numerical comparison of all 11 closed forms")

# CONSOLIDATION formula
check("(z_CONSOL - K)/(1 - K) - tau^2 = 0",
      (CONSOLIDATION - K) / (1 - K) - tau**2,
      "Q(sqrt5)", "threshold-ladder",
      "z_CONSOL = K + tau^2*(1-K), rearrange")

# RESONANCE formula
check("(z_RESON - K)/(1 - K) - tau = 0",
      (RESONANCE - K) / (1 - K) - tau,
      "Q(sqrt5)", "threshold-ladder",
      "z_RESON = K + tau*(1-K), rearrange")


# =============================================================================
# H. ANGULAR / CRYSTALLOGRAPHIC
# =============================================================================
banner("H. ANGULAR / CRYSTALLOGRAPHIC")

check("phi - 2*cos(pi/5) = 0",
      phi - 2*cos(pi / 5),
      "Q(sqrt5)", "angular",
      "golden ratio = diagonal/side of regular pentagon")

check("cos(2*pi/5) - (sqrt(5) - 1)/4 = 0",
      cos(2*pi / 5) - (sqrt(5) - 1) / 4,
      "Q(sqrt5)", "angular",
      "cos(72 degrees) = (sqrt5 - 1)/4")

# Crystallographic traces: trace(n) = 1 + 2*cos(2*pi/n)
def cryst_trace(n):
    return 1 + 2*cos(2*pi / n)

check("trace(5) = 1 + 2*cos(2pi/5) - phi = 0",
      cryst_trace(5) - phi,
      "Q(sqrt5)", "angular",
      "5-fold trace = phi (irrational, hence non-crystallographic)")

check("trace(4) = 1 + 2*cos(2pi/4) - 1 = 0",
      cryst_trace(4) - 1,
      "Q", "angular",
      "4-fold trace = 1 (integer, crystallographic)")

check("trace(6) = 1 + 2*cos(2pi/6) - 2 = 0",
      cryst_trace(6) - 2,
      "Q", "angular",
      "6-fold trace = 2 (integer, crystallographic)")

# 7*60 = 420, excess = 60
check_bool("7 * 60 = 420",
           7 * 60 == 420,
           "Z", "angular",
           "7 equilateral triangles at a vertex: 7*60=420 degrees")

check_bool("heptagonal excess = 420 - 360 = 60",
           420 - 360 == 60,
           "Z", "angular",
           "excess over 360 = one triangle of angular surplus")

# Gauss-Bonnet / Descartes: total angular defect = 720 degrees = 4*pi
# For regular deltahedra: V * (6 - k) * 60 = 720
deltahedra = {
    "tetrahedron":  (3, 4, 6, 4),    # (k, V, E, F)
    "octahedron":   (4, 6, 12, 8),
    "icosahedron":  (5, 12, 30, 20),
}

for name, (k, V, E, F) in deltahedra.items():
    # Euler's formula
    check_bool(f"Euler V-E+F=2 for {name}: {V}-{E}+{F}=2",
               V - E + F == 2,
               "Z", "angular",
               f"Euler's polyhedron formula for {name}")

    # Descartes' theorem: sum of angular defects = 720
    defect = V * (6 - k) * 60
    check_bool(f"Gauss-Bonnet for {name}: V*(6-k)*60 = {defect} = 720",
               defect == 720,
               "Z", "angular",
               f"Descartes' theorem: total angular defect = 4*pi = 720 deg")


# =============================================================================
# I. DYNAMICAL CORE (matrix identities)
# =============================================================================
banner("I. DYNAMICAL CORE  (2x2 matrix identities)")

R = Matrix([[1, 1], [1, 0]])     # Fibonacci companion (note: some sources use [[0,1],[1,1]])
N = Matrix([[0, -1], [1, 0]])    # rotation by 90 degrees
I2 = eye(2)

# R^2 - R - I = 0
check_bool("R^2 - R - I = 0  (golden self-touch)",
           R**2 - R - I2 == zeros(2),
           "M2(Z)", "dynamical",
           "R = [[1,1],[1,0]] satisfies x^2 - x - 1 = 0 (same as phi)")

# N^2 + I = 0
check_bool("N^2 + I = 0  (hidden rotation closure)",
           N**2 + I2 == zeros(2),
           "M2(Z)", "dynamical",
           "N = [[0,-1],[1,0]], N^2 = -I")

# R^2 - R + N^2 = 0  (surplus = deficit: I + (-I) = 0)
check_bool("R^2 - R + N^2 = 0  (surplus = deficit)",
           R**2 - R + N**2 == zeros(2),
           "M2(Z)", "dynamical",
           "R^2 - R = I and N^2 = -I, so sum = 0")

# P = R + N is idempotent: P^2 = P
P = R + N
check_bool("P = R + N, P^2 - P = 0  (idempotent)",
           P**2 - P == zeros(2),
           "M2(Z)", "dynamical",
           "P = [[1,0],[2,0]], P^2 = P")

# exp(2*pi*N) = I  (via Cayley-Hamilton: N^2 = -I implies eigenvalues +/-i)
# N has eigenvalues i and -i, so exp(2*pi*N) = cos(2*pi)*I + sin(2*pi)*N = I
# We verify via the Cayley-Hamilton route: since N^2 = -I,
# exp(t*N) = cos(t)*I + sin(t)*N, so at t = 2*pi: cos(2*pi)=1, sin(2*pi)=0
exp_2piN = cos(2*pi) * I2 + sin(2*pi) * N
check_bool("exp(2*pi*N) = I  (via Cayley-Hamilton: cos(2pi)*I + sin(2pi)*N = I)",
           simplify(exp_2piN - I2) == zeros(2),
           "M2(Z)", "dynamical",
           "N^2 = -I => eigenvalues {i,-i} => exp(2pi*N) = I by Euler")

# S = swap matrix, eigenvalues +1,-1. Represents f''=f / period-2 oscillation.
S = Matrix([[0, 1], [1, 0]])

# S^2 - I = 0
check_bool("S^2 - I = 0  (swap self-reference, f''=f)",
           S**2 - I2 == zeros(2),
           "M2(Z)", "dynamical",
           "S = [[0,1],[1,0]], eigenvalues {+1,-1}, char eq x^2-1=0 (f''=f)")

# [S, R] = N  (golden-swap commutator = rotation)
# SR - RS = [[0,-1],[1,0]] = N. The commutator of golden growth (R^2=R+I)
# with period-2 oscillation (S^2=I) is rotation (N^2=-I).
# The helix is the interference pattern.
check_bool("[S, R] = N  (golden-swap commutator = rotation)",
           S*R - R*S - N == zeros(2),
           "M2(Z)", "dynamical",
           "SR-RS=N: interference of Fibonacci growth and oscillation IS rotation")

# {S, N} = 0  (Clifford anti-commutation)
# S and N anti-commute, forming Clifford algebra Cl(1,1) with S^2=+I, N^2=-I.
check_bool("{S, N} = SN + NS = 0  (Clifford anti-commutation)",
           S*N + N*S == zeros(2),
           "M2(Z)", "dynamical",
           "S^2=+I, N^2=-I, {S,N}=0: Clifford algebra Cl(1,1) = M2(R)")


# =============================================================================
# J. BRIDGES
# =============================================================================
banner("J. BRIDGES  (divisibility and co-closure)")

check("lcm(4, 5, 6) - 60 = 0",
      sp.ilcm(4, sp.ilcm(5, 6)) - 60,
      "Z", "bridges",
      "co-closure index: lcm(4,5,6) = 60")

# F_4 | F_12  (divisibility: F_4 = 3 divides F_12 = 144)
check_bool("F_4 divides F_12  (3 | 144)",
           fib_int(12) % fib_int(4) == 0,
           "Z", "bridges",
           "F_m | F_n whenever m | n")

# L_4 | L_12  (12/4 = 3, which is odd, so L_4 | L_12)
check_bool("L_4 divides L_12  (7 | 322, since 12/4=3 is odd)",
           luc_int(12) % luc_int(4) == 0,
           "Z", "bridges",
           "L_m | L_n when n/m is odd")

# L_4 does NOT divide L_24  (24/4 = 6, which is even)
check_bool("L_4 does NOT divide L_24  (24/4=6 is even)",
           luc_int(24) % luc_int(4) != 0,
           "Z", "bridges",
           "L_m does not divide L_n when n/m is even")


# =============================================================================
# K. HEPTAGONAL
# =============================================================================
banner("K. HEPTAGONAL  (the hyperbolic fold)")

# (2,3,7) triangle area = pi - pi/2 - pi/3 - pi/7
triangle_area = pi - pi/2 - pi/3 - pi/7

check("(2,3,7) triangle area: pi - pi/2 - pi/3 - pi/7 - pi/42 = 0",
      triangle_area - pi/42,
      "Q(pi)", "heptagonal",
      "hyperbolic Gauss-Bonnet: area = pi - sum(angles)")

check("42 - 2*3*7 = 0",
      42 - 2*3*7,
      "Z", "heptagonal",
      "42 = 2 * 3 * 7, the product of the triangle indices")

check("84 - 2*42 = 0",
      84 - 2*42,
      "Z", "heptagonal",
      "Hurwitz bound: |Aut(S_g)| <= 84*(g-1), 84 = 2*42")


# =============================================================================
# SUMMARY AND OUTPUT
# =============================================================================
banner("VERIFICATION SUMMARY")

n_total = len(results)
n_pass  = sum(1 for r in results if r["status"] == "PASS")
n_fail  = sum(1 for r in results if r["status"] == "FAIL")

# Print human-readable table
print()
hdr = f"{'ID':>4}  {'STATUS':<6}  {'LATTICE':<22}  {'CATEGORY':<20}  NAME"
print(hdr)
print("-" * len(hdr) + "-" * 40)
for r in results:
    mark = "  " if r["status"] == "PASS" else ">>"
    print(f"{r['id']:>4}  {r['status']:<6}  {r['lattice']:<22}  "
          f"{r['category']:<20}  {mark}{r['name']}")

print()
print("=" * 88)
print(f"  TOTAL: {n_total} identities")
print(f"  PASS:  {n_pass}")
print(f"  FAIL:  {n_fail}")
print("=" * 88)

if n_fail > 0:
    print()
    print("  FAILURES:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"    [{r['id']}] {r['name']}")
            print(f"         residual: {r['residual']}")
            print(f"         chain:    {r['chain']}")

# Print threshold ladder values for reference
print()
print("  THRESHOLD LADDER (closed-form values):")
print(f"  {'NAME':<16} {'VALUE':<20}")
print("  " + "-" * 36)
for name, expr in thresholds:
    print(f"  {name:<16} {float(sp.N(expr, 15)):<20.10f}")

# Write JSON certificate
output = {
    "harness": "ZFP Master Verification Harness",
    "generator": "zfp_master_verify.py",
    "total": n_total,
    "pass": n_pass,
    "fail": n_fail,
    "verdict": "ALL PASS" if n_fail == 0 else f"{n_fail} FAILURE(S)",
    "results": results,
}

json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "zfp_verification_results.json")
with open(json_path, "w") as f:
    json.dump(output, f, indent=2)
print(f"\n  JSON certificate written to: {json_path}")

sys.exit(0 if n_fail == 0 else 1)
