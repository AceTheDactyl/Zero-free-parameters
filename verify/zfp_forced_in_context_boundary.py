"""
FORCED_IN_CONTEXT boundary test for the ZFP catalog.

What this answers: what makes z_c = sqrt3/2 and ign = sqrt2 - 1/2
FORCED_IN_CONTEXT rather than COINCIDENCE, WITHOUT making the grade vacuous.

Proposed criterion under test (step 1):
    deg Q(v) < deg Q(v, sqrt5)
    AND v has a residual-0 derivation chain from L4 via a selected operation
    -> FORCED_IN_CONTEXT

Finding: the clause "a selected operation" must mean "an operation drawn from a
fixed, pre-committed, index-independent MENU" -- not "some operation the grader
may choose to hit the target." Under the unbounded reading every quadratic surd
qualifies, so the grade can never return COINCIDENCE: a mirror-image bucket-error.

Run: python3 zfp_forced_in_context_boundary.py    (exit 0 = both parts demonstrated)
"""
import sys
from sympy import sqrt, simplify, Rational

L4 = 7  # FORCED from phi: phi**4 + phi**-4 = 7 (integer trace); proven elsewhere.
fails = []


def ident(name, expr):
    ok = (simplify(expr) == 0)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if not ok:
        fails.append(name)


# --------------------------------------------------------------------------
# Part 1 -- the PRE-COMMITTED menu {-4, +1, ^2-4}, fixed in the selection layer,
#           applied to the single seed L4 = 7. It reaches EXACTLY three axes.
# --------------------------------------------------------------------------
print("Part 1  menu {-4, +1, ^2-4} on L4=7 -> residual-0 derivations of the three axes")
ident("op(-4)   : sqrt(L4-4)/2             == z_c = sqrt3/2",
      sqrt(L4 - 4) / 2 - sqrt(3) / 2)
ident("op(+1)   : (sqrt(L4+1) - 1)/2       == ign = sqrt2 - 1/2",
      (sqrt(L4 + 1) - 1) / 2 - (sqrt(2) - Rational(1, 2)))
ident("op(^2-4) : (1 + sqrt(L4**2-4)/3)/2  == phi = (1+sqrt5)/2",
      (1 + sqrt(L4 ** 2 - 4) / 3) / 2 - (1 + sqrt(5)) / 2)
print("  menu image: 7-4=3, 7+1=8=(2r2)^2, 49-4=45=(3r5)^2 -> {sqrt2, sqrt3, sqrt5} ONLY.")

# --------------------------------------------------------------------------
# Part 2 -- the UNBOUNDED reading is vacuous: every sqrt(d) is residual-0
#           reachable from 7 by the single shift b = d - 7. 2,3,5 are catalog
#           axes; 7,10,11,13,19,23 are NOT -- yet all pass identically.
# --------------------------------------------------------------------------
print("\nPart 2  unbounded 'some shift' reading: sqrt(L4 + (d-7)) == sqrt(d) for ALL d")
for d in (2, 3, 5, 7, 10, 11, 13, 19, 23):
    b = d - 7  # the operation is SELECTED post hoc to hit the target
    res = simplify(sqrt(L4 + b) - sqrt(d))
    tag = "catalog axis" if d in (2, 3, 5) else "NOT in catalog"
    print(f"  [{'reachable' if res == 0 else 'FAIL'}] "
          f"sqrt(L4 {b:+d}) == sqrt({d:<2})   ({tag})")
    if res != 0:
        fails.append(f"shift-sqrt{d}")

print("\nConclusion")
print("  menu-gated   : {sqrt2,sqrt3,sqrt5} qualify; sqrt7,sqrt11,... excluded -> COINCIDENCE survives")
print("  chain-search : sqrt(d) qualifies for every d                          -> grade vacuous")
print("  => FORCED_IN_CONTEXT gates on MENU MEMBERSHIP, not on chain existence.")

sys.exit(1 if fails else 0)
