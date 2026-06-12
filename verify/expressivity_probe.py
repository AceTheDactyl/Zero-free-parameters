"""
expressivity_probe.py — quantify the hidden SELECTION budget at each NUMERICAL match.

The corpus already does this once: it BURNS 1/alpha=137 on the grounds that "28
four-term selections hit 137 +/- 1", i.e. the cardinal basis is so expressive near
137 that landing there is no evidence. That exact test is applied to NOTHING ELSE.

This probe applies it uniformly. For each target value we count how many DISTINCT
simple-cardinal ratios fall within the corpus's own quoted tolerance. The count is
the expressivity E(target). The implied hidden selection cost is ~log2(E) bits:
the budget spent choosing THIS expression among E equally-good ones.

Alphabet = the engine cardinals the corpus declares (disc=5, d=2, Nc=3) and their
documented derivatives (7=L4, 8, 10=p), with bounded products/sums/powers.
"""
import sympy as sp
from itertools import product

# --- bounded "simple cardinal" generator over the declared engine atoms --------
# n = 2^a 3^b 5^c, small exponents, plus pairwise sums (captures 7=2+5, 8=3+5, 10=...)
base = set()
for a,b,c in product(range(0,4), range(0,4), range(0,3)):
    v = (2**a)*(3**b)*(5**c)
    if v <= 400: base.add(v)
cardinals = set(base)
for x in list(base):
    for y in list(base):
        if x+y <= 400: cardinals.add(x+y)      # sums like disc+d=7, Nc+disc=8
        if abs(x-y) and abs(x-y) <= 400: cardinals.add(abs(x-y))
cardinals = sorted(c for c in cardinals if c>0)

# candidate ratios in (0,1)
cand = {}
for p in cardinals:
    for q in cardinals:
        r = sp.Rational(p,q)
        if 0 < r < 1:
            cand.setdefault(float(r), r)
cand_vals = sorted(cand)
print(f"alphabet size: {len(cardinals)} cardinals -> {len(cand_vals)} distinct ratios in (0,1)\n")

def expressivity(target, tol_frac, label, corpus_expr):
    """count distinct simple-cardinal ratios within tol_frac*target of target."""
    lo, hi = target*(1-tol_frac), target*(1+tol_frac)
    hits = sorted({cand[v] for v in cand_vals if lo <= v <= hi})
    bits = sp.log(len(hits),2) if hits else sp.oo
    print(f"{label}")
    print(f"   observed≈{target:.4f}  tol=±{tol_frac*100:.1f}%   corpus picks: {corpus_expr}")
    print(f"   E(target) = {len(hits)} equally-simple ratios in band   "
          f"=> hidden selection ≈ {float(bits):.2f} bits")
    show = [f"{h}={float(h):.4f}" for h in hits[:12]]
    print(f"   members: {', '.join(show)}{' ...' if len(hits)>12 else ''}\n")
    return len(hits)

print("="*78)
print("EXPRESSIVITY AUDIT — how many equally-good cardinal ratios sit at each target")
print("="*78)
# PMNS angles (corpus §6.2, tolerances are the quoted deviations)
expressivity(0.545, 0.001, "PMNS sin^2 theta_23", "(disc+d)^2/(d*Nc^2*disc)=49/90")
expressivity(0.307, 0.005, "PMNS sin^2 theta_12", "disc^2/Nc^4=25/81")
expressivity(0.022, 0.010, "PMNS sin^2 theta_13", "1/(disc*Nc^2)=1/45")
# cosmological fractions (corpus §6.4)
expressivity(0.259, 0.035, "Omega_DM", "1/d^2 = 1/4")
expressivity(0.049, 0.029, "Omega_visible", "1/(d^2*disc) = 1/20")
expressivity(0.691, 0.013, "Omega_DE", "(d+disc)/p = 7/10")
# strong coupling (corpus §6.3) — uses an irrational atom, expect LOW expressivity
print("="*78)
print("CONTRAST: alpha_S uses an IRRATIONAL atom (|psi|^3), not a cardinal ratio")
print("="*78)
aS = float((1/((1+sp.sqrt(5))/2))**3/2)
print(f"   alpha_S = |psi|^3/2 = {aS:.5f} vs observed 0.1179±0.0009")
print(f"   This is NOT in the rational-cardinal candidate set; its 'closed form' is a")
print(f"   single forced irrational over the floor dimension. Expressivity in the")
print(f"   cardinal-ratio basis is irrelevant here — the relevant question is whether")
print(f"   the rho<->alpha_S physical bridge closes (corpus: OPEN, 'one link short').\n")

print("="*78)
print("READING")
print("="*78)
print("""   High E (many neighbours) => the match is weak evidence; choosing the specific
   expression spends ~log2(E) bits of hidden selection. This reproduces the corpus's
   own verdict on 137 (E≈28 within ±1 => ~4.8 bits => BURNED) and EXTENDS it. Any
   target whose E is comparable to 137's should inherit 137's grade, not a better one.
   The corpus already says the PMNS/cosmo exponents are 'curated cardinals … no
   derivation selects them over a neighbour' (§6.8) — this probe puts a bit-count on
   exactly that admission, turning a prose caveat into an auditable number.""")
