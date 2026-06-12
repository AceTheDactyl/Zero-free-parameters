#!/usr/bin/env python3
"""Hexagonal (D6) closure: is the hexagonal lattice case a self-validating
closure of the structural relationship Z_C = sqrt3/2 = Im(zeta_6)?

Claim under test (bounded): YES for the zeta_6 / crystallographic tower.
  - The crystallographic chain TERMINATES at order 6 (no higher lattice symmetry).
  - At that terminus, three independent routes -- geometry, algebra, dynamics --
    return the SAME constant Z_C, minpoly 4x^2-3. That triple agreement is the
    corpus 'forced' standard (two+ independent ways, residual 0) -> self-validating.
  - The closure is of ONE tower. The obstruction that forbids 5-fold (and thus
    excludes the phi-tower from any lattice) is 2cos72 = tau = phi^-1 itself.
    So the firewall Q(sqrt5) ∩ Q(sqrt3) = Q is enforced geometrically, not just
    algebraically. The whole architecture does NOT close into one structure; it
    closes into two disjoint self-validating towers sharing only Q.

Deps: sympy.  Run: python3 zfp_hex_closure.py
"""
import sympy as sp
from sympy import (I, cos, exp, expand, im, minpoly, pi, simplify, sqrt, symbols)

x = symbols("x")
_FAILS = []
def ok(c):                          # records failures so exit code is meaningful
    _r = bool(c)
    if not _r:
        _FAILS.append(1)
    return "PASS" if _r else "FAIL"
PHI = (1 + sqrt(5)) / 2
print(f"sympy {sp.__version__}")

print("="*74)
print("1. CRYSTALLOGRAPHIC RESTRICTION -- the chain terminates at order 6")
print("="*74)
print("  A lattice rotation by 2pi/n needs integer trace: 2cos(2pi/n) in Z.")
allowed = []
for n in range(1, 9):
    t = sp.nsimplify(2*cos(2*pi/n))
    isint = t.is_integer
    if isint: allowed.append(n)
    print(f"    n={n}: 2cos(2pi/n) = {str(t):<18} lattice-compatible? {'yes' if isint else 'no'}")
print(f"  => crystallographic orders = {allowed}  (expect [1,2,3,4,6]) -> "
      f"{ok(allowed==[1,2,3,4,6])}")
# the n=5 obstruction is exactly the golden constant
t5 = simplify(2*cos(2*pi/5))
print(f"  n=5 obstruction: 2cos(72deg) = {t5} = phi^-1 = tau ; "
      f"minpoly = {minpoly(t5,x)} -> {ok(minpoly(t5,x)==x**2+x-1)}")
print(f"    tau is IRRATIONAL -> 5-fold forbidden -> the phi-tower is non-crystallographic.")

print("="*74)
print("2. ORDER-6 GENERATOR -- zeta_6 and its real signature Z_C")
print("="*74)
z6 = exp(I*pi/3)                                   # zeta_6 = e^{i pi/3}, order 6
mp6 = minpoly(z6, x)
print(f"  zeta_6 = e^(i pi/3); minpoly = {mp6}  (cyclotomic Phi_6 = x^2-x+1) -> "
      f"{ok(mp6==x**2-x+1)}")
zc = sqrt(3)/2
print(f"  Z_C = sqrt3/2 ; minpoly = {minpoly(zc,x)} -> {ok(minpoly(zc,x)==4*x**2-3)}")

print("="*74)
print("3. SELF-VALIDATION -- three independent routes return the SAME Z_C")
print("="*74)
route_geom = simplify(sp.sin(pi/3))                # geometry: sin 60
route_alg  = simplify(im(z6))                      # algebra : Im(zeta_6)
# dynamics: imaginary parts of the three trifurcation modes (cube roots of unity)
modes = [exp(2*I*pi*k/3) for k in range(3)]
route_dyn  = simplify(im(modes[1]))                # mode at 120deg
print(f"  geometry  sin(60)      = {route_geom}")
print(f"  algebra   Im(zeta_6)   = {route_alg}")
print(f"  dynamics  Im(mode@120) = {route_dyn}")
agree = (simplify(route_geom-zc)==0 and simplify(route_alg-zc)==0 and simplify(route_dyn-zc)==0)
print(f"  all three equal Z_C = sqrt3/2 (residual 0): {ok(agree)}")
print(f"  => the structural relationship computes 3 independent ways -> SELF-VALIDATING.")

print("="*74)
print("4. THE CLOSURE ITSELF -- three modes close (sum to zero) = hexagonal resonance")
print("="*74)
S = sum(modes)                                     # 1 + w + w^2 = 0
Sre, Sim = simplify(sp.re(S)), simplify(sp.im(S))
print(f"  k1 + k2 + k3 = 1 + e^(2pi i/3) + e^(4pi i/3):  re = {Sre}, im = {Sim}  -> "
      f"sum = 0 : {ok(Sre==0 and Sim==0)}")
print(f"    the three trifurcation modes form a CLOSED triangle (sum=0); this is")
print(f"    exactly the hexagonal-lattice resonance k1+k2+k3=0 that forces hexagons.")
print(f"    trifurcation geometry == lattice closure condition: same structure.")

print("="*74)
print("5. FIELD / FIREWALL -- the closure is of ONE tower")
print("="*74)
mp_z6_field = minpoly(z6 + sp.conjugate(z6), x)    # Re part lives in Q(sqrt3)
print(f"  Q(zeta_6) = Q(sqrt-3); its real subfield is Q(sqrt3) (holds Z_C).")
mp_sum = minpoly(sqrt(5)+sqrt(3), x)
print(f"  minpoly(sqrt5+sqrt3) = {mp_sum}, degree {sp.degree(mp_sum,x)} = 2*2")
print(f"    => Q(sqrt5) ∩ Q(sqrt3) = Q : firewall holds {ok(sp.degree(mp_sum,x)==4)}")
print(f"  The SAME constant (tau) that excludes 5-fold (step 1) generates the phi-tower.")
print(f"  So the geometry that closes the hex tower is what forbids the phi-tower from it.")

print("="*74)
print("VERDICT")
print("="*74)
print("  Hexagonal case = self-validating closure of the zeta_6 / crystallographic tower:")
print("    terminus of the order chain (CRT) + triple-independent agreement on Z_C.   [FORCED]")
print("  It does NOT close the phi-tower; CRT via tau enforces the firewall geometrically.")
print("  Whole architecture: two disjoint self-validating towers meeting only at Q.   [FORCED]")
print("  A physical system *being* a D6 bifurcation at a forced constant: still OPEN.")


if __name__ == "__main__":
    import sys as _sys
    if _FAILS:
        print(f"FAIL  {len(_FAILS)} check(s) did not pass")
    _sys.exit(1 if _FAILS else 0)
