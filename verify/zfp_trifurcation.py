#!/usr/bin/env python3
"""Trifurcation and its multi-dimensional dynamics, as a chain-of-derivation study.

Thesis under test: the FORCED structural outputs (how many branches, the
amplitude exponent, the number field the branches live in) are determined by
the *chain* -- the germ degree, the symmetry group, the dimension. The chain is
the selection-layer input; everything below it is forced. Change a link, and
the forced output changes in a specified, checkable way.

Two realizations of "1 -> 3":
  (A) 1D, reflection (Z2) symmetry: the symmetric cusp x^3 + a x  -- a pitchfork.
  (B) multi-D, three-fold (D3/Z3) symmetry: zbar^2  -- a transcritical trifork.
They produce three branches by *different* mechanisms, with *different* forced
exponents, in *different* fields.  Both are verified here, residual 0.

Deps: sympy.  Run: python3 zfp_trifurcation.py
"""
import sympy as sp
from sympy import (I, Integer, Matrix, Poly, Rational, conjugate, diff,
                   discriminant, exp, expand, factor, minpoly, pi, simplify,
                   solve, sqrt, symbols)

x, a, b, lam, u, v = symbols("x a b lambda u v", real=True)
_FAILS = []
def ok(c):                          # records failures so exit code is meaningful
    _r = bool(c)
    if not _r:
        _FAILS.append(1)
    return "PASS" if _r else "FAIL"
print(f"sympy {sp.__version__}")

print("="*74)
print("A. 1D TRIFURCATION -- symmetric cusp  V = x^4/4 + a x^2/2,  V' = x^3 + a x")
print("="*74)
Vp = x**3 + a*x                                   # = x (x^2 + a)
roots = [Integer(0), sqrt(-a), -sqrt(-a)]
res_ok = all(simplify(Vp.subs(x, r)) == 0 for r in roots)
print(f"  factor(V')        = {factor(Vp)}")
print(f"  three branches {{0, +sqrt(-a), -sqrt(-a)}} are roots (residual 0): {ok(res_ok)}")
disc = discriminant(Poly(Vp, x), x)
print(f"  discriminant(V')  = {expand(disc)}   (expect -4a^3) -> {ok(expand(disc+4*a**3)==0)}")
print(f"    => disc = 0 only at a = 0 : the TRIFURCATION POINT (triple root at x=0)")
print(f"    => a < 0 gives disc = -4a^3 > 0 : three distinct real branches")
# stability via Hessian V'' = 3x^2 + a
Vpp = diff(x**4/4 + a*x**2/2, x, 2)
h0  = simplify(Vpp.subs(x, 0))                    # a
hpm = simplify(Vpp.subs(x, sqrt(-a)))             # -2a
print(f"  Hessian at x=0:        V'' = {h0}    (trivial branch; stable a>0, unstable a<0)")
print(f"  Hessian at +/-sqrt(-a): V'' = {hpm}  (broken pair; stable for a<0) -> exchange at a=0")
print(f"  amplitude scaling: |x| = |a|^(1/2)  -> FORCED exponent 1/2 (pitchfork)")

print("="*74)
print("B. THE CHAIN -- even germs x^(2m), symmetric section, FORCED branch count")
print("="*74)
print("  V' = x * (degree-(2m-2) even poly)  =>  up to 2m-1 real branches (odd, +2 per link)")
reps = {
    "x^4  cusp     (m=2)": (x**3 - x,                       [0, 1, -1]),
    "x^6  butterfly(m=3)": (x**5 - 5*x**3 + 4*x,            [0, 1, -1, 2, -2]),
    "x^8           (m=4)": (x**7 - 14*x**5 + 49*x**3 - 36*x, [0, 1, -1, 2, -2, 3, -3]),
}
for name, (poly, rts) in reps.items():
    res_ok = all(simplify(poly.subs(x, r)) == 0 for r in rts)
    n_real = len(Poly(poly, x).real_roots())
    print(f"  {ok(res_ok and n_real == len(rts))}  {name}: factor={factor(poly)}  branches={n_real}")
print("  3 -> 5 -> 7 : raising the germ degree (the chain) forces +2 branches each step.")

print("="*74)
print("C. MULTI-D TRIFURCATION -- D3/Z3 equivariant  zdot = lam z + zbar^2")
print("="*74)
w = exp(2*I*pi/3)                                  # primitive cube root, = zeta_6^2
equivar = simplify(conjugate(w)**2 - w)            # zbar^2 equivariant <=> conj(w)^2 = w
print(f"  Z3-equivariance of zbar^2:  conj(w)^2 - w = {equivar}  -> {ok(equivar == 0)}")
# real coordinates z=u+iv :  zbar^2 = (u-iv)^2 = (u^2-v^2) - 2i u v
f1 = lam*u + u**2 - v**2
f2 = lam*v - 2*u*v
sols = solve([f1, f2], [u, v], dict=True)
nontrivial = [s for s in sols if not (s[u] == 0 and s[v] == 0)]
print(f"  steady states solved: {len(sols)} total, {len(nontrivial)} nontrivial branches")
all_res, all_r2 = True, True
for s in sols:
    r1 = simplify(f1.subs(s)); r2 = simplify(f2.subs(s)); all_res &= (r1 == 0 and r2 == 0)
for s in nontrivial:
    r2val = simplify(s[u]**2 + s[v]**2); all_r2 &= (simplify(r2val - lam**2) == 0)
print(f"  every branch satisfies both field equations (residual 0): {ok(all_res)}")
print(f"  every nontrivial branch has r^2 = lambda^2  => r = |lambda|: {ok(all_r2)}")
print(f"  amplitude scaling: r = |lambda|^1  -> FORCED exponent 1 (transcritical), NOT 1/2")
# the three branch directions and the sqrt3/2 = Z_C signature
print(f"  branches (u,v):")
for s in sols:
    print(f"      ({s[u]}, {s[v]})")
zc = sqrt(3)/2
print(f"  branch height at |lambda|=1 is sqrt(3)/2 = Im(zeta_6) = Z_C ; "
      f"minpoly = {minpoly(zc, x)} -> {ok(minpoly(zc, x) == 4*x**2 - 3)}")
# Jacobian / stability at the theta=0 branch (u,v)=(-lam,0)
J = Matrix([[diff(f1, u), diff(f1, v)], [diff(f2, u), diff(f2, v)]])
J0 = J.subs({u: -lam, v: 0})
ev = sorted(J0.eigenvals().keys(), key=lambda e: str(e))
print(f"  Jacobian eigenvalues at theta=0 branch: {ev}  (expect -lambda, 3*lambda)")
print(f"    -> opposite signs => SADDLE; the quadratic D3 trifork is unstable "
      f"(cubic |z|^2 z terms needed to stabilize).")

print("="*74)
print("D. FIELD DISCIPLINE & FIREWALL -- the chain also selects the NUMBER FIELD")
print("="*74)
print(f"  D3 branch geometry lives in Q(sqrt3): minpoly(sqrt3/2) = {minpoly(sqrt(3)/2,x)}")
mp_sum = minpoly(sqrt(5)+sqrt(3), x)
print(f"  phi-cuspoid world is Q(sqrt5); minpoly(sqrt5+sqrt3) = {mp_sum}")
print(f"    degree {sp.degree(mp_sum,x)} = 2*2 => Q(sqrt5) ∩ Q(sqrt3) = Q : firewall holds {ok(sp.degree(mp_sum,x)==4)}")
print(f"  => the SAME word 'trifurcation' forces outputs in DIFFERENT fields depending")
print(f"     on the symmetry chain (Z2 cuspoid -> Q(sqrt(-a)); D3 -> Q(sqrt3)).")
print(f"  COINCIDENCE flag (NOT a forcing): (sqrt3)^2 = {sqrt(3)**2} = the D3 branch count 3;")
print(f"     this is not the earlier integer 3 = L4-4, and the two must not be conflated.")

print("="*74)
print("CHAIN -> FORCED OUTPUT  (change a link, the output changes, all forced)")
print("="*74)
rows = [
    ("Z2 symmetric cusp x^4 (1D)",     "3",        "1/2",  "Q(sqrt(-a))"),
    ("Z2 symmetric butterfly x^6 (1D)","5",        "1/2",  "Q(radicals of a,b)"),
    ("Z2 even germ x^(2m) (1D)",       "2m-1",     "1/2",  "field of the radicals"),
    ("D3 equivariant zbar^2 (2D)",     "3",        "1",    "Q(sqrt3)"),
]
print(f"  {'chain link':<34}{'branches':<10}{'amp exp':<9}{'field'}")
for r in rows:
    print(f"  {r[0]:<34}{r[1]:<10}{r[2]:<9}{r[3]}")

print("="*74)
print("GRADING")
print("="*74)
print("  FORCED       : branch counts, discriminants, trifurcation point a=0,")
print("                 D3 equivariance + three 120-deg branches, r=|lambda|,")
print("                 sqrt3/2 = Z_C identity, firewall -- all residual 0 above.")
print("  CONSTRUCTION : a specific (a,b,..) realizing a given count is illustrative;")
print("                 the COUNT is forced by the germ, the instance is chosen.")
print("  OPEN/ASSUMPT : that a physical DeltaH_V realizes a trifurcation at a forced")
print("                 constant needs the operator+metric. sqrt3/2 here is a real")
print("                 structural identity but does NOT bridge to the phi-family.")


if __name__ == "__main__":
    import sys as _sys
    if _FAILS:
        print(f"FAIL  {len(_FAILS)} check(s) did not pass")
    _sys.exit(1 if _FAILS else 0)
