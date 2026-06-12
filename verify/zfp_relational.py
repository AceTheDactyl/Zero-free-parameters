#!/usr/bin/env python3
"""Relational geometry of the L4 constants -- one space, forced interactions.

This replaces the earlier 'separate fields / firewall / coincidence' framing.
The L4 constants are co-present in ONE relational space, the compositum
Q(sqrt2, sqrt3, sqrt5), and the irrationals/deltas emerge from forced relations
across them, seeded by the single forced quantity L4 = phi^4 + phi^-4 = 7.

Grading recast for relational geometry:
  FORCED (absolute)        -- holds from the generator alone: phi, L4=7, tau^2+tau=1.
  FORCED UNDER CONSTRAINT  -- forced GIVEN the seed + a selected relation, stays in
                              Q(sqrt5) tower: tau, gap, crit, Delta; K (Q(K) contains Q(sqrt5)).
  FORCED IN CONTEXT        -- disjoint axis, but v = op(L4) for op in the declared MENU
                              {-4, +1, ^2-4}, residual 0. z_c = sqrt(L4-4)/2, ign = (-1+sqrt(L4+1))/2.
                              The map is selected; the result is exact; the axis is disjoint.
  COINCIDENCE              -- off-axis surd not reachable via any menu op on L4.
  SELECTED                 -- which relations/operations to instantiate (-4, +1, ^2-4, x^2+x).
  REPRESENTATION           -- the helical embedding r(z)=K*sqrt(z/z_c), pitch, winding.

Linear independence of sqrt2, sqrt3, sqrt5 over Q is NOT a wall: it means the
three are independent coordinate AXES of the one relational space, which is what
lets them carry distinct information and form non-trivial forced relations.

Deps: sympy.  Run: python3 zfp_relational.py
"""
import sympy as sp
from sympy import sqrt, Rational, simplify, minpoly, Symbol

x = Symbol("x"); PHI = (1 + sqrt(5))/2
L4 = PHI**4 + PHI**-4
_FAILS = []
def ok(c):                          # records failures so exit code is meaningful
    _r = bool(c)
    if not _r:
        _FAILS.append(1)
    return "PASS" if _r else "FAIL"
print(f"sympy {sp.__version__}")

print("="*74)
print("SEED (forced absolute):  L4 = phi^4 + phi^-4 =", simplify(L4))
print("="*74)

print("THREE AXES FROM ONE SEED  (seed + selected op -> three fields)")
print("-"*74)
print(f"  L4 - 4   = {simplify(L4-4)}      -> sqrt3 ;  z_c = sqrt(L4-4)/2 = sqrt3/2      "
      f"{ok(simplify(sqrt(L4-4)/2 - sqrt(3)/2)==0)}  [FORCED IN CONTEXT: menu op(-4), residual 0]")
print(f"  L4 + 1   = {simplify(L4+1)} = (2*sqrt2)^2 -> sqrt2 ; ignition = (-1+sqrt(1+L4))/2 = sqrt2-1/2  "
      f"{ok(simplify((-1+sqrt(1+L4))/2 - (sqrt(2)-Rational(1,2)))==0)}  [FORCED IN CONTEXT: menu op(+1), residual 0]")
print(f"  L4^2 - 4 = {simplify(L4**2-4)} = (3*sqrt5)^2 -> sqrt5 ; phi^4 = (L4+sqrt(L4^2-4))/2     "
      f"{ok(simplify((L4+sqrt(L4**2-4))/2 - PHI**4)==0)}  [FORCED UNDER CONSTRAINT: stays in Q(sqrt5)]")

print("-"*74)
print("ONE SPACE (not separate fields):")
m = minpoly(sqrt(2)+sqrt(3)+sqrt(5), x)
print(f"  minpoly(sqrt2+sqrt3+sqrt5) = {m}")
print(f"  degree {sp.degree(m,x)} = 2*2*2  -> compositum Q(sqrt2,sqrt3,sqrt5); three independent axes  {ok(sp.degree(m,x)==8)}")

print("-"*74)
print("DELTAS / RELATIONS across the constants (forced, residual 0):")
tau=1/PHI; gap=PHI**-4; K=sqrt(1-gap); DELTA=PHI**-2; ign=sqrt(2)-Rational(1,2)
print(f"  Delta = phi^-2 = 1 - tau            {ok(simplify(DELTA-(1-tau))==0)}")
print(f"  tau^2 + tau = 1                     {ok(simplify(tau**2+tau-1)==0)}   [absolute]")
print(f"  K^2 = 1 - gap = 1 - phi^-4          {ok(simplify(K**2-(1-gap))==0)}")
print(f"  ignition^2 + ignition = L4/4 = 7/4  {ok(simplify(ign**2+ign-L4/4)==0)}   [FORCED IN CONTEXT: Q(sqrt2), menu op(+1)]")
print(f"  z_c^2 = (L4-4)/4 = 3/4              {ok(simplify((sqrt(3)/2)**2-(L4-4)/4)==0)}   [FORCED IN CONTEXT: Q(sqrt3), menu op(-4)]")

print("="*74)
print("READING")
print("="*74)
print("  The interactions (which operations on L4 / the constants) are the SELECTION;")
print("  the irrationals and deltas they yield split into three grades:")
print("    FORCED               : phi, L4 (absolute); tau, gap, crit, Delta (Q(sqrt5)).")
print("    FORCED UNDER CONSTRAINT : K -- Q(K) contains Q(sqrt5), forced given seed + relation.")
print("    FORCED IN CONTEXT    : z_c and ignition -- disjoint axis, but reachable via the")
print("                           declared MENU {-4, +1, ^2-4} on L4 with residual 0.")
print("                           z_c = sqrt(L4-4)/2 [op(-4)], ign = (-1+sqrt(L4+1))/2 [op(+1)].")
print("    COINCIDENCE          : off-axis surds NOT reachable via any menu op on L4.")
print("  The helix is one REPRESENTATION of this web.")


if __name__ == "__main__":
    import sys as _sys
    if _FAILS:
        print(f"FAIL  {len(_FAILS)} check(s) did not pass")
    _sys.exit(1 if _FAILS else 0)
