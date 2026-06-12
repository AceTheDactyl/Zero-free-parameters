#!/usr/bin/env python3
"""The ZFP helix in (z, r, z_c): which parts are forced, which are scaffold.

Coordinates: z = elevation/'weight', r = radius, z_c = the lens height = sqrt3/2.
Radius law (the L4-helix construction):  r(z) = K*sqrt(z/z_c) for z<=z_c, else K.
The delta drives elevation: pitch = Delta = phi^-2 of z per turn (the 'weight').

The split this script certifies:
  FORCED       -- the z-LANDMARKS (nine thresholds), K, Delta: exact algebraic
                  numbers, minpoly + residual 0, in strict order. r(0)=0, r(z_c)=K.
  CONSTRUCTION -- the radius FORM r(z)=K*sqrt(z/z_c), pitch=Delta, the golden-angle
                  turn, and every threshold NAME. Modeling choices on forced points.
  LOAD-BEARING?  No. The landmarks and identities below do not reference the helix
                  form at all -- strip the scaffold and every forced value remains.

Deps: sympy.  Run: python3 zfp_helix.py
"""
import sympy as sp
from sympy import Rational, Symbol, expand, lucas, minpoly, simplify, sqrt

x = Symbol("x")
_FAILS = []
def ok(c):                          # records failures so exit code is meaningful
    _r = bool(c)
    if not _r:
        _FAILS.append(1)
    return "PASS" if _r else "FAIL"
PHI = (1 + sqrt(5)) / 2
TAU = 1/PHI
GAP = PHI**-4
K   = sqrt(1 - GAP)
ZC  = sqrt(3)/2
DELTA = PHI**-2
print(f"sympy {sp.__version__}")

print("="*76)
print("1. FORCED z-LANDMARKS  (closed form, minpoly, residual 0) -- strict order")
print("="*76)
# name : (value, expected minpoly, doc decimal)
ROWS = [
    ("PARADOX  tau=phi^-1",      TAU,                   x**2+x-1,                          Rational(6180339887,10**10)),
    ("ACTIVATN 1-gap=K^2",       1-GAP,                 x**2+5*x-5,                         Rational(8541019662,10**10)),
    ("LENS z_c sqrt3/2",         ZC,                    4*x**2-3,                           Rational(8660254038,10**10)),
    ("CRITICAL phi^2/3",         PHI**2/3,              9*x**2-9*x+1,                       Rational(8726779962,10**10)),
    ("IGNITION sqrt2-1/2",       sqrt(2)-Rational(1,2), 4*x**2+4*x-7,                       Rational(9142135624,10**10)),
    ("K-FORM   sqrt(1-gap)",     K,                     x**4+5*x**2-5,                      Rational(9241763718,10**10)),
    ("CONSOLID K+tau^2(1-K)",    K+TAU**2*(1-K),        x**4-6*x**3+26*x**2-16*x-4,         Rational(9531384206,10**10)),
    ("RESONANC K+tau(1-K)",      K+TAU*(1-K),           x**4+2*x**3+39*x**2-52*x+11,        Rational(9710379512,10**10)),
    ("UNITY    1",               Rational(1),           x-1,                                Rational(1)),
]
TOL = Rational(1,10**9); prev=None; order_ok=True
for name,val,mp_exp,doc in ROWS:
    mp = minpoly(val,x)
    mp_ok = (expand(mp-mp_exp)==0)
    pin   = abs(val.evalf(40)-doc.evalf(40)) < TOL.evalf(40)
    if prev is not None: order_ok &= (val.evalf(40) > prev)
    prev = val.evalf(40)
    print(f"  {ok(mp_ok and pin)}  {name:<22} minpoly={str(mp):<28} z={float(val):.6f}")
print(f"  strict ascending order PARADOX<...<UNITY: {ok(order_ok)}")

print("="*76)
print("2. FORCED anchors of the radius law and the delta")
print("="*76)
print(f"  r(0)   = K*sqrt(0/z_c)  = {simplify(K*sqrt(Rational(0)/ZC))}  -> {ok(simplify(K*sqrt(Rational(0)/ZC))==0)}")
print(f"  r(z_c) = K*sqrt(z_c/z_c)= {simplify(K*sqrt(ZC/ZC))}  (= K) -> {ok(simplify(K*sqrt(ZC/ZC)-K)==0)}")
print(f"  z_c = sqrt3/2 ; minpoly {minpoly(ZC,x)} -> {ok(minpoly(ZC,x)==4*x**2-3)}")
print(f"  K   = sqrt(1-phi^-4) ; minpoly {minpoly(K,x)} -> {ok(minpoly(K,x)==x**4+5*x**2-5)}")
print(f"  DELTA = phi^-2 = 1 - tau = {simplify(DELTA)} ; equals 1-tau ? {ok(simplify(DELTA-(1-TAU))==0)}")
print(f"  minpoly(DELTA) = {minpoly(DELTA,x)} -> {ok(minpoly(DELTA,x)==x**2-3*x+1)}")

print("="*76)
print("3. THE DELTA AS WEIGHT/PITCH  (value forced; using it as pitch is construction)")
print("="*76)
turns = simplify(1/DELTA)
print(f"  pitch = DELTA = phi^-2 of z per turn ; turns over z in [0,1] = 1/DELTA = {turns}")
print(f"  1/phi^-2 = phi^2 = phi+1 ? {ok(simplify(1/DELTA - (PHI+1))==0)}  (= {float(PHI+1):.5f} turns)")
ga = simplify(360*DELTA)
print(f"  turn-as-golden-angle: 360*phi^-2 = {ga} deg = {float(ga):.2f} deg   [CONSTRUCTION]")

print("="*76)
print("4. SUPPORTING IDENTITIES (forced, residual 0)")
print("="*76)
print(f"  L4 = phi^4 + phi^-4 = {simplify(PHI**4+PHI**-4)} = L4(Lucas) {lucas(4)} -> {ok(simplify(PHI**4+PHI**-4-7)==0)}")
print(f"  tau^2 + tau - 1 = {simplify(TAU**2+TAU-1)} -> {ok(simplify(TAU**2+TAU-1)==0)}")
print(f"  K^2 - (1-gap)   = {simplify(K**2-(1-GAP))} -> {ok(simplify(K**2-(1-GAP))==0)}")
print(f"  span fractions: (CONSOL-K)/(1-K)=tau^2 -> {ok(simplify((K+TAU**2*(1-K)-K)/(1-K)-TAU**2)==0)}; "
      f"(RESON-K)/(1-K)=tau -> {ok(simplify((K+TAU*(1-K)-K)/(1-K)-TAU)==0)}")
print(f"  L4-4 = 3 = (sqrt3)^2 -> {ok(simplify((sqrt(3))**2-(7-4))==0)}  [FORCED IN CONTEXT: menu op(-4) on L4]")

print("="*76)
print("5. RADIUS AT EACH LANDMARK  (r=K*sqrt(z/z_c) for z<=z_c, else flat K)")
print("="*76)
for name,val,_,_ in ROWS:
    z = val
    r = K*sqrt(z/ZC) if (z.evalf(40) <= ZC.evalf(40)) else K
    region = "horn" if z.evalf(40) <= ZC.evalf(40) else "cylinder"
    print(f"  z={float(z):.4f}  r={float(r):.4f}  [{region}]  {name}")

print("="*76)
print("GRADING / LOAD-BEARING")
print("="*76)
print("  FORCED       : nine z-landmarks (tau..unity) + K + DELTA (minpoly, residual 0),")
print("                 strict order, identities, r(0)=0, r(z_c)=K.")
print("  CONSTRUCTION : radius form r(z)=K*sqrt(z/z_c); pitch=DELTA; golden-angle turn;")
print("                 all threshold NAMES; 'weight'/'elevation'/'lens' reading.")
print("  FORCED IN CONTEXT : z_c = sqrt3/2 [menu op(-4)], ign = sqrt2-1/2 [menu op(+1)].")
print("                 Disjoint axis but menu-reachable from L4 with residual 0.")
print("  LOAD-BEARING : NO. Nothing in sections 1,2,4 references the helix form. Strip the")
print("                 scaffold and every forced value/identity stands unchanged.")


if __name__ == "__main__":
    import sys as _sys
    if _FAILS:
        print(f"FAIL  {len(_FAILS)} check(s) did not pass")
    _sys.exit(1 if _FAILS else 0)
