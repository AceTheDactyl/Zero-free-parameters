#!/usr/bin/env python3
"""r(r)=r as the lattice seed: idempotents, (semi)lattices, grid retractions.

Three readings of r(r)=r, each verified rather than asserted:

  (1) idempotent ELEMENT    e * e = e          -> over a field: e in {0, 1}
  (2) idempotent OPERATION  a * a = a          -> (semi)lattice; meet/join on Z^2
  (3) idempotent MAP        r(r(x)) = r(x)     -> retraction / closure operator;
                                                  rounding R^n -> Z^n, projection P^2 = P

Reading (2) is the genuine algebraic seed of lattice theory (Birkhoff 1940,
Davey-Priestley 2002): a semilattice IS a set with one commutative, associative,
idempotent operation. Reading (3) is the bridge to GEOMETRIC grids (Z^n): an
idempotent retraction maps ambient space onto the grid.

Note (see write-up): the equation that produces phi is x^2 = x + 1, which is
NOT x^2 = x. The literal idempotent seed r(r)=r yields {0,1} and lattices; it
does not yield phi. The two are different fixed points and are kept separate.

Deps: sympy.  Run: python3 rrr_idempotent_lattice.py
"""

import itertools
from sympy import Symbol, solve, sqrt

_FAILS = []
def _chk(cond):                      # record a failed structural check; printed value unchanged
    if not cond:
        _FAILS.append(1)
    return cond

# --------------------------------------------------- (1) element idempotents over a field
def element_idempotents():
    e = Symbol("e")
    idem = solve(e**2 - e, e)        # e*e = e          (the literal r(r)=r as a number)
    golden = solve(e**2 - e - 1, e)  # e*e = e + 1       (a DIFFERENT equation -> phi)
    print("(1) element reading e*e = e over a field")
    print(f"    e^2 = e      -> e in {sorted(idem)}            (only trivial idempotents)")
    print(f"    e^2 = e + 1  -> e in {golden}   <- this is phi's equation, NOT r(r)=r")
    _chk(sorted(idem) == [0, 1])     # the literal seed yields exactly the trivial idempotents

# --------------------------------------------------- (2) idempotent operations -> lattice on Z^2
def meet(a, b):                      # greatest lower bound under componentwise <=
    return (min(a[0], b[0]), min(a[1], b[1]))

def join(a, b):                      # least upper bound
    return (max(a[0], b[0]), max(a[1], b[1]))

def lattice_laws(grid):
    pairs   = list(itertools.product(grid, repeat=2))
    triples = list(itertools.product(grid, repeat=3))
    idem  = _chk(all(meet(a, a) == a and join(a, a) == a for a in grid))
    comm  = _chk(all(meet(a, b) == meet(b, a) and join(a, b) == join(b, a) for a, b in pairs))
    assoc = _chk(all(meet(meet(a, b), c) == meet(a, meet(b, c)) for a, b, c in triples))
    absor = _chk(all(meet(a, join(a, b)) == a and join(a, meet(a, b)) == a for a, b in pairs))
    distr = _chk(all(meet(a, join(b, c)) == join(meet(a, b), meet(a, c)) for a, b, c in triples))
    print("(2) Z^2 grid as an order lattice (meet = componentwise min, join = max)")
    print(f"    idempotent  r(r)=r : {idem}")
    print(f"    commutative        : {comm}")
    print(f"    associative        : {assoc}")
    print(f"    absorption         : {absor}   <- upgrades two semilattices into a lattice")
    print(f"    distributive       : {distr}   <- Z^n grids are distributive lattices")

# --------------------------------------------------- (3) idempotent maps -> grid mappings
def round_vec(x):                    # nearest-integer retraction R^n -> Z^n
    return tuple(round(c) for c in x)

def proj_x(v):                       # linear projection onto the x-axis; P^2 = P
    return (v[0], 0)

def closure_downset(S, n):           # order-closure on the chain {0..n}: c(S) = {0..max S}
    return frozenset(range(max(S) + 1)) if S else frozenset()

def map_laws():
    pts = [(1.4, -0.6), (2.5, 3.49), (-0.5, 0.5), (10.2, -3.8)]
    r1 = [round_vec(p) for p in pts]
    r2 = [round_vec(p) for p in r1]          # rounding already-integers is fixed
    round_ok = _chk(r1 == r2)
    print("(3) idempotent maps as grid mappings")
    print(f"    rounding R^2 -> Z^2 : r(r(x)) == r(x) ? {round_ok}   (retraction onto the grid)")
    pidem = _chk(all(proj_x(proj_x(v)) == proj_x(v) for v in [(3, 5), (-2, 7), (0, -4)]))
    print(f"    projection P^2 = P  : {pidem}   (idempotent endomorphism of the grid)")
    base = frozenset({1, 4})
    c1 = closure_downset(base, 6)
    c2 = closure_downset(c1, 6)
    clos_ok = _chk(c1 == c2)
    ext_ok  = _chk(base <= c1)
    print(f"    closure operator c  : c(c(S)) == c(S) ? {clos_ok}; extensive S <= c(S) ? {ext_ok}")
    print(f"                          (closure operators <-> complete lattices: Moore families)")

if __name__ == "__main__":
    element_idempotents()
    print()
    patch = [(i, j) for i in range(-2, 3) for j in range(-2, 3)]   # 5x5 patch of Z^2
    lattice_laws(patch)
    print()
    map_laws()
    print()
    print("seed r(r)=r is forced (a law, not a tuned value); every check above is structural.")
    import sys as _sys
    if _FAILS:
        print(f"FAIL  {len(_FAILS)} structural check(s) did not hold")
    _sys.exit(1 if _FAILS else 0)
