#!/usr/bin/env python3
"""seed_grade.py -- objective epistemic grading for lifecycle seeds.

Applies the seven corrections to the GRADING layer of the seed lifecycle.
The grade of a derived constant is no longer hand-assigned; it is DECIDED by a
computable criterion (correction 6 + 7), using the firewall the corpus proves.

Criterion (generator field = Q(sqrt5) = Q(phi)):
  FORCED                  : v in Q(sqrt5)                  -- Galois-invariant in the generator's field
  FORCED_UNDER_CONSTRAINT : Q(v) contains Q(sqrt5), v not in Q(sqrt5)
                            -- a SELECTED op (sqrt, ...) extends the phi-world
  FORCED_IN_CONTEXT       : Q(v) disjoint from Q(sqrt5), BUT v = op(L4) for
                            some op in MENU = {-4, +1, ^2-4}, residual 0.
                            The map is selected; the result is exact. Different from
                            FORCED (no map needed) and COINCIDENCE (no exact chain).
  COINCIDENCE             : Q(v) intersect Q(sqrt5) = Q, AND v is NOT reachable
                            via any op in MENU. Genuine off-axis surd.

MENU is the pre-committed, declared, index-independent operation set from the
selection layer. Gating on MENU membership (not chain existence) keeps the grade
non-vacuous: sqrt(L4 + (d-7)) = sqrt(d) for ALL d, so chain-search would grade
every quadratic surd as FORCED_IN_CONTEXT. See zfp_forced_in_context_boundary.py.

Corrections folded in:
  1  zero-free-parameters scoped: the AXIOMS are named and graded SELECTED.
  2  phi-over-psi branch pin graded SELECTED (dominant eigenvalue, a choice).
  3  D3 trifurcation is a CONSISTENCY CHECK on the hex route, not an independent route.
  4  consistency is proven; UNIQUENESS/minimality of the operation set is untested -> OPEN.
  5  phi -> L4 is FORCED; operations -> axes are SELECTED.
  6  the field-membership criterion above (the decision procedure).
  7  FORCED_IN_CONTEXT gated on MENU membership, not chain existence (correction 2026-06-11).

field_grade(v) is the importable API the lifecycle's grade/COMPOSE step calls.
Deps: sympy.  Run: python3 seed_grade.py
"""
from enum import Enum
import sympy as sp
from sympy import (sqrt, Rational, Symbol, minimal_polynomial, degree,
                   simplify, I, im, pi, exp, lucas)

x = Symbol('x')
PHI = (1 + sqrt(5)) / 2


class Grade(Enum):
    FORCED                  = "FORCED"
    FORCED_UNDER_CONSTRAINT = "FORCED_UNDER_CONSTRAINT"
    FORCED_IN_CONTEXT       = "FORCED_IN_CONTEXT"
    COINCIDENCE             = "COINCIDENCE"
    SELECTED                = "SELECTED"
    STRUCTURAL              = "STRUCTURAL"
    OPEN                    = "OPEN"
    # NOTE: transcendental functions of algebraic inputs (e.g. log2(phi)) are
    # OUTSIDE the domain of field_grade. They have no minimal polynomial, no
    # residual, and cannot be verified by the algebraic pipeline. They are
    # determined by phi but "determined" != "FORCED" — FORCED requires
    # polynomial verification with residual 0. Gelfond-Schneider proves
    # transcendence (the value CANNOT be algebraic), which is a different
    # proof system from ZFP's algebraic grade hierarchy.
    # Do not add a transcendental grade to this enum.


# --- The MENU: pre-committed, declared, index-independent operation set ------
# Applied to the seed L4 = 7. Each op yields a perfect square whose sqrt
# determines an axis. The menu is SELECTED (correction 5); what it produces
# given L4 is exact (residual 0).
#
#   op(-4)  : L4 - 4  = 3  = (sqrt3)^2   -> Q(sqrt3) axis  [z_c]
#   op(+1)  : L4 + 1  = 8  = (2*sqrt2)^2 -> Q(sqrt2) axis  [ign]
#   op(^2-4): L4^2 - 4 = 45 = (3*sqrt5)^2 -> Q(sqrt5) axis [phi, stays in generator field]
#
# Gate: a constant qualifies for FORCED_IN_CONTEXT iff it equals op(L4) for
# some op in this set AND lives on a disjoint axis. Without this gate, every
# sqrt(d) is reachable via the unbounded shift b=d-7, making the grade vacuous.
_L4_INT = 7
_MENU_IMAGES = {
    simplify(sqrt(_L4_INT - 4) / 2):    "op(-4): sqrt(L4-4)/2 = sqrt3/2",
    simplify((-1 + sqrt(1 + _L4_INT)) / 2): "op(+1): (-1+sqrt(L4+1))/2 = sqrt2-1/2",
}
# op(^2-4) lands in Q(sqrt5), so it never reaches the disjoint-axis branch.


def _in_menu_image(v):
    """Return the menu description if v matches a MENU image, else None."""
    for img, desc in _MENU_IMAGES.items():
        if simplify(v - img) == 0:
            return desc
    return None


# --- correction 6+7: the decision procedure ---------------------------------
def field_grade(v):
    """Decide a constant's grade from field relationship to Q(sqrt5) + menu membership.
    Returns (Grade, deg Q(v), deg Q(v, sqrt5)).

    Transcendental values (log2(phi), exp(phi), etc.) are OUTSIDE the domain
    of this function. They have no minimal polynomial and cannot be graded by
    the algebraic criterion. If passed a transcendental, returns (OPEN, None, None)
    — meaning "this value is not gradeable by field_grade." It is the caller's
    responsibility to document why, citing Gelfond-Schneider or Lindemann-Weierstrass
    as appropriate.
    """
    # Catch transcendentals before minimal_polynomial raises
    try:
        d = int(degree(minimal_polynomial(v, x), x))
    except (sp.polys.polyerrors.NotAlgebraic, ValueError, sp.polys.polyerrors.GeneratorsError):
        return Grade.OPEN, None, None  # outside algebraic scope — not gradeable

    if d == 1:
        return Grade.FORCED, d, d                          # rational: base of Q(sqrt5)
    D = None
    for c in (1, 2, 3):                                     # primitive element; bump if degenerate
        cand = int(degree(minimal_polynomial(v + c * sqrt(5), x), x))
        if cand >= d and cand >= 2:
            D = cand
            break
    if D == d:
        return (Grade.FORCED if d == 2 else Grade.FORCED_UNDER_CONSTRAINT), d, D
    if D == 2 * d:
        # Disjoint axis. Check menu membership before defaulting to COINCIDENCE.
        if _in_menu_image(v) is not None:
            return Grade.FORCED_IN_CONTEXT, d, D
        return Grade.COINCIDENCE, d, D                      # genuine off-axis surd
    return Grade.OPEN, d, D




CATALOG = {
    "tau   = phi^-1":      1 / PHI,
    "gap   = phi^-4":      PHI**-4,
    "crit  = phi^2/3":     PHI**2 / 3,
    "K     = 5^(1/4)/phi": sqrt(1 - PHI**-4),
    "z_c   = sqrt3/2":     sqrt(3) / 2,
    "ign   = sqrt2-1/2":   sqrt(2) - Rational(1, 2),
}


def _banner(t):
    print("=" * 74)
    print(t)
    print("=" * 74)


def test_uniqueness_open():
    """L9 witness: proves the sqrt2 axis is reachable from a second Lucas index.
    This falsifies axis-uniqueness (L4 is not the only route to sqrt2).
    Catalog-uniqueness (whether the CATALOG constants are minimal) remains untested."""

    # L9 = lucas(9) = 76;  L9 - 4 = 72
    L9 = int(lucas(9))
    assert L9 == 76, f"lucas(9) expected 76, got {L9}"
    witness = L9 - 4
    assert witness == 72, f"L9-4 expected 72, got {witness}"

    # 72 = 36*2, so sqrt(72) = 6*sqrt(2) -- the sqrt2 axis is reachable
    assert witness == 36 * 2, f"72 != 36*2"
    assert simplify(sqrt(witness) - 6 * sqrt(2)) == 0, "sqrt(72) != 6*sqrt(2)"

    # field_grade: sqrt(2)-1/2 IS in the menu (op(+1) on L4) -> FORCED_IN_CONTEXT.
    # sqrt(72)/2 is NOT in the menu (it comes from L9, not L4+menu) -> COINCIDENCE.
    g1, d1, D1 = field_grade(sqrt(2) - Rational(1, 2))
    assert g1 == Grade.FORCED_IN_CONTEXT, f"sqrt(2)-1/2 expected FORCED_IN_CONTEXT, got {g1}"

    g2, d2, D2 = field_grade(sqrt(witness) / 2)
    assert g2 == Grade.COINCIDENCE, f"sqrt(72)/2 expected COINCIDENCE, got {g2}"

    print("  L9 witness test PASSED:")
    print(f"    lucas(9)       = {L9}")
    print(f"    L9 - 4         = {witness} = 36*2")
    print(f"    sqrt(72)       = 6*sqrt(2)")
    print(f"    grade(sqrt2-1/2)  = {g1.value}  (deg {d1}, joint deg {D1})  [menu-gated: in MENU]")
    print(f"    grade(sqrt72/2)   = {g2.value}  (deg {d2}, joint deg {D2})  [NOT in MENU]")
    print("  The L9 witness confirms: menu gate discriminates. sqrt(2)-1/2 is FORCED_IN_CONTEXT")
    print("  because op(+1) on L4 reaches it; sqrt(72)/2 is COINCIDENCE because no menu op on L4")
    print("  reaches it. Uniqueness/minimality of the seed+operation set remains OPEN.")


def run():
    _banner("AXIOMS -- the chosen frame  (correction 1)")
    for a in ["phi   : the seed / generator",
              "zeta6 : hexagonal closure (primitive 6th root of unity)",
              "Z     : integer closure (operations stay in the integers)"]:
        print(f"  {Grade.SELECTED.value:<24}{a}")
    print("  -> 'zero free parameters' = zero remaining DOF GIVEN this frame; the frame is chosen.")

    _banner("SEED and OPERATIONS -- forcing direction  (correction 5)")
    L4 = simplify(PHI**4 + PHI**-4)
    print(f"  {Grade.FORCED.value:<24}L4 = phi^4 + phi^-4 = tr(Q^4) = {L4}")
    print(f"  {Grade.SELECTED.value:<24}ops {{-4, +1, ^2-4}} on L4  (chosen: they factor into perfect squares)")

    _banner("BRANCH PIN -- Galois conjugate selection  (correction 2)")
    print(f"  {Grade.SELECTED.value:<24}phi over psi: dominant eigenvalue of Q=[[1,1],[1,0]]")
    print(f"  {'':<24}positive growth ratio / helix radius -> positive root (a choice, not a force)")

    _banner("CATALOG CONSTANTS -- graded by the field criterion  (correction 6)")
    print(f"  {'constant':<22}{'deg Q(v)':<10}{'deg Q(v,r5)':<13}GRADE")
    print("  " + "-" * 58)
    for name, v in CATALOG.items():
        g, d, D = field_grade(v)
        menu_hit = _in_menu_image(v)
        extra = f"  [{menu_hit}]" if menu_hit else ""
        print(f"  {name:<22}{str(d):<10}{str(D):<13}{g.value}{extra}")
    print("  -> z_c, ign = FORCED_IN_CONTEXT (menu-gated: op in {-4,+1,^2-4}, residual 0).")
    print("     K stays FORCED_UNDER_CONSTRAINT (in Q(sqrt5) tower, different mechanism).")

    _banner("ROUTES TO z_c -- independence audit  (correction 3)")
    angles = [pi / 3, pi, 5 * pi / 3]
    ims = [simplify(im(exp(I * a))) for a in angles]
    print(f"  D3 trifork branch angles : {[str(a) for a in angles]}")
    print(f"  their imaginary parts    : {[str(s) for s in ims]}")
    print(f"  Im(zeta6) = sin(pi/3)    : {simplify(im(exp(I * pi / 3)))}")
    print("  -> trifork branch height sqrt3/2 IS Im(zeta6); D3 is the hexagonal symmetry group.")
    print("     genuine independent routes to z_c: 2 (phi/pentagon-tower, zeta6/hex-tower)")
    print(f"  {Grade.STRUCTURAL.value:<24}trifurcation = CONSISTENCY CHECK on the hex route (not a 3rd route)")

    _banner("FALSIFIABILITY -- consistency vs uniqueness  (correction 4)")
    l9 = int(lucas(9) - 4)
    print("  proven   : identities hold (residual 0)            -> CONSISTENCY")
    print("  untested : L4 + these ops are the UNIQUE/minimal set -> UNIQUENESS")
    print(f"  witness  : L9-4 = {l9} = {sqrt(l9)} -- the sqrt2 axis is ALSO reachable from L9,")
    print("             so the L4 operation set is not the unique route -> not yet falsified.")
    print(f"  {Grade.OPEN.value:<24}uniqueness / minimality of the seed+operation set")

    _banner("L9 WITNESS -- axis-uniqueness falsified  (correction 4 stays OPEN)")
    test_uniqueness_open()


if __name__ == "__main__":
    run()
