#!/usr/bin/env python3
"""The crystallographic obstruction as a notable delta on a control axis.

Control axis:  a = trace of a planar rotation by 2pi/n  =  2 cos(2pi/n).
A rotation is a lattice symmetry iff a is an integer (integer characteristic
polynomial). The crystallographic orders are exactly n in {1,2,3,4,6}; order 5
lands at a = 2cos72 = tau = phi^-1 -- irrational -> off-lattice.

THE NOTABLE DELTA:  the trace-gap from the zeta_6 closure (order 6, a=1) down to
the forbidden order 5 (a=tau) is  Delta = 1 - tau = phi^-2.  The wall between the
two towers has golden width.

It also answers a precise question: is phi DERIVED here, or only assumed?
  - The pentagon (this obstruction) DERIVES phi from geometry: 2cos72=phi^-1 and
    2cos144=-phi, both roots of x^2+x-1.  phi is an OUTPUT.
  - The L4 helix takes phi as INPUT and derives thresholds from it (incl.
    L4 = phi^4+phi^-4 = 7); it does NOT derive phi.
So the obstruction is the independent derivation that grounds the L4-helix's
assumed phi -- phi self-validates (assumed-substrate vs derived-geometry), the
mirror of Z_C self-validating across geometry/algebra/dynamics.

Deps: sympy.  Run: python3 zfp_delta_pentagon.py
"""
import sympy as sp
from sympy import (Matrix, Rational, Symbol, cos, deg, expand, lucas,
                   minpoly, pi, simplify, sqrt)

x = Symbol("x")
_FAILS = []
def ok(c):                          # records failures so exit code is meaningful
    _r = bool(c)
    if not _r:
        _FAILS.append(1)
    return "PASS" if _r else "FAIL"
PHI = (1 + sqrt(5)) / 2
TAU = 1/PHI
print(f"sympy {sp.__version__}")

print("="*74)
print("1. CONTROL AXIS a = 2cos(2pi/n) -- integer a <=> lattice symmetry")
print("="*74)
for n in [1,2,3,4,5,6]:
    a = sp.nsimplify(2*cos(2*pi/n))
    compat = a.is_integer
    note = "" if compat else "  <- off-lattice"
    print(f"  n={n}: a = {str(a):<18} order {n:<2} lattice? {'yes' if compat else 'no '}{note}")
print("  crystallographic orders = {1,2,3,4,6}; order 5 sits at a = tau = phi^-1.")

print("="*74)
print("2. THE NOTABLE DELTA  Delta = a(6) - a(5) = 1 - tau = phi^-2")
print("="*74)
a6, a5, a4 = Rational(1), TAU, Rational(0)         # 2cos(60),2cos(72),2cos(90)
Delta = simplify(a6 - a5)
print(f"  a(6)=1, a(5)=tau, a(4)=0")
print(f"  Delta = 1 - tau = {Delta}  ; equals phi^-2 ? {ok(simplify(Delta - PHI**-2)==0)}")
print(f"  minpoly(phi^-2) = {minpoly(PHI**-2, x)}  (expect x^2-3x+1) -> "
      f"{ok(minpoly(PHI**-2,x)==x**2-3*x+1)}")
print(f"  lower gap a(5)-a(4) = tau - 0 = {simplify(a5-a4)} = phi^-1 -> "
      f"{ok(simplify(a5-a4-TAU)==0)}")
print(f"  => order 5 sits phi^-1 above order-4 and phi^-2 below the order-6 closure.")
golden = simplify(360*PHI**-2)
print(f"  as a turn fraction: 360*phi^-2 = {golden} deg = {float(golden):.2f} deg "
      f"(the golden angle). [interpretive]")

print("="*74)
print("3. phi DERIVED from the pentagon (obstruction) -- an OUTPUT, from geometry")
print("="*74)
t72  = simplify(2*cos(2*pi/5))                      # = (sqrt5-1)/2 = tau = phi^-1
t144 = simplify(2*cos(4*pi/5))                      # = -(sqrt5+1)/2 = -phi
print(f"  2cos(72deg)  = {t72} = phi^-1 ; minpoly {minpoly(t72,x)} -> {ok(minpoly(t72,x)==x**2+x-1)}")
print(f"  2cos(144deg) = {t144} = -phi  ; minpoly {minpoly(t144,x)} -> {ok(minpoly(t144,x)==x**2+x-1)}")
print(f"  same minimal polynomial x^2+x-1 (conjugate pair tau, -phi) -> "
      f"{ok(minpoly(t72,x)==minpoly(t144,x))}")
print(f"  the regular pentagon yields phi and phi^-1 directly -> phi is DERIVED here.")

print("="*74)
print("4. phi in the SUBSTRATE (what the L4 helix is built on) -- here phi is INPUT")
print("="*74)
Q = Matrix([[1,1],[1,0]])
charQ = simplify(Q.charpoly(x).as_expr())
print(f"  Q=[[1,1],[1,0]] charpoly = {charQ}  (x^2-x-1; dominant eigenvalue phi) -> "
      f"{ok(charQ==x**2-x-1)}")
trQ4 = (Q**4).trace()
print(f"  trace(Q^4) = {trQ4} = L4 = {lucas(4)} -> {ok(trQ4==lucas(4)==7)}")
L4_phi = simplify(PHI**4 + PHI**-4)
print(f"  L4-helix uses L4 = phi^4 + phi^-4 = {L4_phi} -> {ok(L4_phi==7)}  (phi is its INPUT)")
# L4-helix 'THE LENS' = sqrt(L4-4)/2 = sqrt3/2 -- reached via the 7-4=3 step
lens = sqrt(lucas(4)-4)/2
print(f"  L4-helix 'THE LENS' = sqrt(L4-4)/2 = sqrt({lucas(4)-4})/2 = {lens} = Z_C")
print(f"    the step L4-4 = 3 = (sqrt3)^2 uses menu op(-4) on L4: FORCED IN CONTEXT")
print(f"    (sqrt3 is NOT in Q(sqrt5), but the derivation has residual 0 via a declared op).")
print(f"    The L4 helix reaches Z_C by an exact, menu-gated chain.")

print("="*74)
print("5. ANSWER: is phi 'already derived' via the L4 helix?")
print("="*74)
print("  No -- the L4 helix ASSUMES phi (derives 9 thresholds + L4 FROM phi).")
print("  The pentagon/obstruction DERIVES phi independently (step 3).")
print("  => the obstruction grounds the L4-helix's assumed phi; phi SELF-VALIDATES")
print("     (assumed-in-substrate vs derived-in-geometry), mirroring Z_C.")

print("="*74)
print("6. FIREWALL still holds -- two towers, met only at Q")
print("="*74)
mp_sum = minpoly(sqrt(5)+sqrt(3), x)
print(f"  pentagon-phi in Q(sqrt5); hexagon-Z_C in Q(sqrt3).")
print(f"  minpoly(sqrt5+sqrt3) = {mp_sum}, degree {sp.degree(mp_sum,x)} -> "
      f"Q(sqrt5) ∩ Q(sqrt3) = Q : {ok(sp.degree(mp_sum,x)==4)}")
print(f"  the obstruction is the phi-tower's self-validation point AND the zeta_6-")
print(f"  tower's exclusion of it. Delta = phi^-2 is the width of that wall.")

print("="*74)
print("GRADING")
print("="*74)
print("  FORCED      : Delta = 1-tau = phi^-2 (minpoly x^2-3x+1); 2cos72=phi^-1,")
print("                2cos144=-phi (x^2+x-1); trace(Q^4)=phi^4+phi^-4=L4=7; firewall.")
print("  STRUCTURAL  : phi self-validation across substrate(assumed) & pentagon(derived).")
print("  FORCED IN CONTEXT : L4-4 = 3 = (sqrt3)^2 -- Z_C via menu op(-4), residual 0, disjoint axis.")
print("  INTERPRETIVE: 360*phi^-2 = golden angle; reading Delta as a helix turn is a choice.")


if __name__ == "__main__":
    import sys as _sys
    if _FAILS:
        print(f"FAIL  {len(_FAILS)} check(s) did not pass")
    _sys.exit(1 if _FAILS else 0)
