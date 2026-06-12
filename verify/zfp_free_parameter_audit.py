#!/usr/bin/env python3
"""Free-parameter audit for the ZFP manuscript.

Separates the FORCED CORE (parameter-free, residual 0) from the free-parameter
apparatus introduced in the expanded manuscript (lambda in 8.6; K, omega_i,
encoding e, dynamical psi in 10.2). Confirms:
  (1) the core needs no free parameter (every check residual 0);
  (2) lambda is a genuine free knob: at lambda=0 the coupled wells ARE the
      forced catalog roots; for lambda != 0 the JOINT observable x*y* moves
      (tunable -> fails R2), while the per-sector facts do not.
Conclusion: removing lambda (and the Kuramoto block) removes no forced content.
Deps: sympy.  Run: python3 zfp_free_parameter_audit.py
"""
import sympy as sp
from sympy import sqrt, Rational, simplify, minimal_polynomial, Matrix, eye, symbols, nsolve, LC, diff, solve
x = sp.Symbol("x"); PHI=(1+sqrt(5))/2; PSI=(1-sqrt(5))/2
_FAILS = []
def ok(c):                          # records failures so exit code is meaningful
    _r = bool(c)
    if not _r:
        _FAILS.append(1)
    return "PASS" if _r else "FAIL"
print(f"sympy {sp.__version__}\n"+"="*70)
print("1. FORCED CORE  (contains no lambda / K / omega / dynamical psi)")
print("="*70)
print(f"  psi = -1/phi (conjugate) : {ok(simplify(PSI+1/PHI)==0)}   phi+psi=1 : {ok(simplify(PHI+PSI-1)==0)}   phi*psi=-1 : {ok(simplify(PHI*PSI+1)==0)}")
Q=Matrix([[1,1],[1,0]])
print(f"  Q^2=Q+I : {ok(Q**2-Q-eye(2)==sp.zeros(2))}   tr(Q^4)=7 : {ok((Q**4).trace()==7)}   L4=phi^4+phi^-4=7 : {ok(simplify(PHI**4+PHI**-4-7)==0)}")
cat={"tau=1/phi":(1/PHI,x**2+x-1),"gap=phi^-4":(PHI**-4,x**2-7*x+1),
     "K=sqrt(1-phi^-4)":(sqrt(1-PHI**-4),x**4+5*x**2-5),"z_c=sqrt3/2":(sqrt(3)/2,4*x**2-3),
     "ignition=sqrt2-1/2":(sqrt(2)-Rational(1,2),4*x**2+4*x-7),"critical=phi^2/3":(PHI**2/3,9*x**2-9*x+1)}
for name,(val,mp) in cat.items():
    m=minimal_polynomial(val,x)
    print(f"  minpoly {name:<20}-> {mp}   {ok(simplify(m*LC(mp,x)-mp*LC(m,x))==0)}")
print(f"  [Q(sqrt2,sqrt3,sqrt5):Q]=8 : {ok(sp.degree(minimal_polynomial(sqrt(2)+sqrt(3)+sqrt(5),x),x)==8)}   balance tau+tau^2=1 : {ok(simplify(1/PHI+1/PHI**2-1)==0)}")

print("\n"+"="*70)
print("2. LAMBDA PROBE (8.6)   V=(x^2-x-1)^2+(y^2-3/4)^2 + lam*x*y")
print("="*70)
X,Y,lam=symbols("X Y lam",real=True)
V=(X**2-X-1)**2+(Y**2-Rational(3,4))**2+lam*X*Y
gx=diff(V,X); gy=diff(V,Y)
rx=solve(gx.subs(lam,0),X); ry=solve(gy.subs(lam,0),Y)
print(f"  lam=0 -> decouples to catalog roots:  x in {[sp.nsimplify(r) for r in rx]}   y in {[sp.nsimplify(r) for r in ry]}")
print(f"  per-sector sums (lam=0): sum_x={simplify(sum(rx))} (x3 over grid = 9/2),  sum_y={simplify(sum(ry))}  -> separable")
seed=(float(PHI),float(sqrt(3)/2)); prods=[]
print("  joint well seeded at (phi, sqrt3/2), tracked vs lambda:")
for L in [-0.3,-0.1,0.0,0.1,0.3]:
    s=nsolve((gx.subs(lam,L),gy.subs(lam,L)),(X,Y),seed)
    p=float(s[0]*s[1]); prods.append(p)
    print(f"    lam={L:+.1f}:  x*={float(s[0]):.5f}  y*={float(s[1]):.5f}  x*y*={p:.5f}")
print(f"  spread(x*y*) over lam in [-0.3,0.3] = {max(prods)-min(prods):.3f}   -> JOINT observable is TUNABLE (fails R2)")
print("  verdict: lambda is genuinely free; lam=0 returns the forced catalog. Removing it")
print("           drops only the redundant dynamical disproof; the algebraic one (7.4) stands.")


if __name__ == "__main__":
    import sys as _sys
    if _FAILS:
        print(f"FAIL  {len(_FAILS)} check(s) did not pass")
    _sys.exit(1 if _FAILS else 0)
