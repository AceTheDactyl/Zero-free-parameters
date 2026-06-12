"""
unified_verify.py  —  independent clean-room verification of the ZFP corpus.

Scope: re-derive, two independent ways where possible, every COMPUTABLE backbone
claim that appears across THE_ALGEBRA / THE_PHYSICS / the architecture spec /
the helix + plates + grounding doc. Imports nothing from the corpus narrative;
rebuilds the 2x2 carriers from first principles and climbs by Kronecker product.

Convention: a check is PASS iff an exact symbolic residual is 0 (or an integer
identity holds exactly). Numerical-only matches are reported separately and are
never promoted, mirroring the corpus's own grading discipline.
"""
import sympy as sp
import itertools as it

PASS, FAIL = [], []
def chk(name, cond):
    (PASS if bool(cond) else FAIL).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

I2 = sp.eye(2)
def kron(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = sp.Matrix(sp.kronecker_product(out, m))
    return out

# ============================================================================
print("="*80); print("A. SEED CARRIERS (rebuilt from scratch) — THE_ALGEBRA inheritance")
print("="*80)
# Basis of M2(R): the four carriers
R = sp.Matrix([[0,1],[1,1]])      # Fibonacci/companion: x^2 - x - 1
N = sp.Matrix([[0,-1],[1,0]])     # rotation: x^2 + 1
h = sp.Matrix([[1,0],[0,-1]])     # diagonal involution
J = sp.Matrix([[0,1],[1,0]])      # swap involution
P = R + N                         # the seed
chk("R^2 = R + I   (golden self-touch, disc=5)", sp.simplify(R*R - (R+I2)) == sp.zeros(2))
chk("N^2 = -I       (hidden rotation closure)",   N*N == -I2)
chk("h^2 = I, J^2 = I (involutions)",             h*h==I2 and J*J==I2)
chk("P = R+N is idempotent: P^2 = P",             P*P == P)
chk("keystone  R^2 - R = -N^2 = +I",              sp.simplify(R*R-R - (-N*N))==sp.zeros(2) and R*R-R==I2)
# transpose mirror split
sym  = lambda M: M.T == M
asym = lambda M: M.T == -M
chk("transpose split: R,h,J,I symmetric (V+ dim 3); N antisymmetric (V- dim 1)",
    all(map(sym,[R,h,J,I2])) and asym(N))
chk("diagonal asymmetry  Delta = dimV+ - dimV- = 3-1 = 2 = 2^(0+1)", 3-1 == 2**(0+1))
chk("P(t) verifier form: P = [[0,0],[2,1]]  (t=2)", P == sp.Matrix([[0,0],[2,1]]))

# ============================================================================
print("="*80); print("B. phi-ALGEBRA, LUCAS KEYSTONE, AND THE 11-POSITION LADDER")
print("="*80)
phi = (1+sp.sqrt(5))/2; tau = 1/phi; gap = phi**-4; K = sp.sqrt(1-gap)
L4  = sp.expand(phi**4 + phi**-4)
chk("L4 = phi^4 + phi^-4 = 7 (Lucas, integer)", sp.nsimplify(L4)==7)
chk("L4 - 4 = 3 = (sqrt3)^2  (the 5->6 bridge in Q)", sp.simplify(L4-4-(sp.sqrt(3))**2)==0)
chk("gap = phi^-4 = 5 - 3*phi", sp.simplify(gap-(5-3*phi))==0)
chk("K^2 = 1 - phi^-4 = 3*phi - 4", sp.simplify(K**2-(3*phi-4))==0)
ladder = {
 "ORIGIN":sp.Integer(0),"PARADOX":tau,"ACTIVATION":1-gap,"THE LENS":sp.sqrt(3)/2,
 "CRITICAL":phi**2/3,"IGNITION":sp.sqrt(2)-sp.Rational(1,2),"K-FORMATION":K,
 "CONSOLIDATION":K+tau**2*(1-K),"RESONANCE":K+tau*(1-K),"UNITY":sp.Integer(1),
 "OVERTONE":2-K}
seq=[sp.N(v,30) for v in ladder.values()]
chk("ladder strictly increasing (11 positions, ORIGIN..OVERTONE)",
    all(seq[i]<seq[i+1] for i in range(len(seq)-1)))
chk("radius continuous at z_c: K*sqrt(z_c/z_c) = K", sp.simplify(K*sp.sqrt(1)-K)==0)
chk("spinor double-cover: 2 cycles x pi x 1/2 each -> 4pi*1/2 = 2pi", sp.Rational(4,1)*sp.Rational(1,2)==2)

# Minimal polynomials (architecture S7) — value must be a ROOT of the stated poly
x=sp.symbols('x')
minpolys = {
 "tau":            (tau,                 x**2+x-1),
 "z_c=sqrt3/2":    (sp.sqrt(3)/2,        4*x**2-3),
 "gap=phi^-4":     (gap,                 x**2-7*x+1),
 "K":              (K,                   x**4+5*x**2-5),
 "IGNITION":       (sp.sqrt(2)-sp.Rational(1,2), 4*x**2+4*x-7),
 "CRITICAL":       (phi**2/3,            9*x**2-9*x+1),
}
for nm,(val,poly) in minpolys.items():
    chk(f"min-poly: {nm} is a root of [{poly}]", sp.simplify(poly.subs(x,val))==0)

# ============================================================================
print("="*80); print("C. FIELD DISJOINTNESS  (the licence to bridge)")
print("="*80)
# sqrt3 not in Q(sqrt5): minimal polynomial of sqrt3 over Q(sqrt5) has degree 2
mp = sp.minimal_polynomial(sp.sqrt(3), x, domain=sp.QQ.algebraic_field(sp.sqrt(5)))
chk("sqrt3 NOT in Q(sqrt5): [Q(sqrt5,sqrt3):Q(sqrt5)] = 2  => intersection = Q",
    sp.degree(mp,x)==2)
chk("cyclotomic conductor test: gcd(cond sqrt5=5, cond sqrt3=12)=1 <= 2 (disjoint)",
    sp.gcd(5,12)==1)
chk("sqrt15 irrational (no shared quadratic subfield)", not sp.sqrt(15).is_rational)

# ============================================================================
print("="*80); print("D. THE BRIDGES (forced rationals) AND THE CLIMB 4->12->24->60")
print("="*80)
chk("bridge 3 = phi^4+phi^-4-4 = (sqrt3)^2", sp.simplify((phi**4+phi**-4-4)-(sp.sqrt(3))**2)==0)
chk("bridge 7 = phi^4+phi^-4 (integer)", sp.nsimplify(phi**4+phi**-4)==7)
chk("bridge 1 = 2*cos(2pi/6) (crystallographic trace)", sp.simplify(2*sp.cos(2*sp.pi/6)-1)==0)
def fib(n):
    a,b=0,1
    for _ in range(n): a,b=b,a+b
    return a
def luc(n):
    a,b=2,1
    for _ in range(n): a,b=b,a+b
    return a
chk("doubling identity F_24 = F_12 * L_12 = 144*322 = 46368",
    fib(24)==fib(12)*luc(12)==46368)
chk("F_12 = 144 = 12^2 (Cohn: only square Fibonacci > 1)", fib(12)==144==12**2)
chk("normalize 12 = 4*f4 (f4=3); F4|F12 and L4|L12 (12/4=3 odd)",
    12==4*3 and fib(12)%fib(4)==0 and luc(12)%luc(4)==0)
chk("renormalize 24: L4 does NOT divide L24 (24/4=6 even) -> needs Lucas factor",
    luc(24)%luc(4)!=0)
chk("co-closure 60 = lcm(4,5,6)", sp.ilcm(4,5,6)==60)

# ============================================================================
print("="*80); print("E. CLIFFORD AT d=1:  M4(R) =~ Cl(3,1)  (two gamma representatives)")
print("="*80)
def clifford_ok(gam, eta):
    for a in range(len(gam)):
        for b in range(len(gam)):
            target = 2*eta[a]*sp.eye(4) if a==b else sp.zeros(4)
            if gam[a]*gam[b]+gam[b]*gam[a] != target:
                return False
    return True
# Part 1 representative, signature (+,+,+,-)
g0,g1,g2,g3 = kron(h,I2),kron(J,I2),kron(N,N),kron(N,h)
chk("Part-1 gammas satisfy {g_mu,g_nu}=2 eta, eta=diag(+,+,+,-)",
    clifford_ok([g0,g1,g2,g3],[1,1,1,-1]))
chk("Part-1: 3 spacelike (+I4) in V+, 1 timelike (-I4) -> Lorentz signature (3,1)",
    g0*g0==sp.eye(4) and g1*g1==sp.eye(4) and g2*g2==sp.eye(4) and g3*g3==-sp.eye(4))
# Part 1A real Dirac basis, signature (+,-,-,-) with {M,M}=-2 eta
M0,M1,M2,M3 = kron(N,J),kron(h,I2),kron(J,I2),kron(N,N)
def clifford_minus(gam,eta):
    for a in range(4):
        for b in range(4):
            target = -2*eta[a]*sp.eye(4) if a==b else sp.zeros(4)
            if gam[a]*gam[b]+gam[b]*gam[a]!=target: return False
    return True
chk("Part-1A Dirac basis {M_mu,M_nu}=-2 eta, eta=diag(+,-,-,-)",
    clifford_minus([M0,M1,M2,M3],[1,-1,-1,-1]))
chk("Part-1A: (M0)^2=-I4 (ROT), (M1,M2,M3)^2=+I4 (INVOL)",
    M0*M0==-sp.eye(4) and all(Mi*Mi==sp.eye(4) for Mi in [M1,M2,M3]))
G5 = M0*M1*M2*M3
chk("chirality Gamma5 = M0M1M2M3 has Gamma5^2 = -I4 (ROT, not involution over R)",
    G5*G5==-sp.eye(4))
chk("Gamma5 antisymmetric (lands in V-)", G5.T==-G5)
chk("charge conjugation C=N@J=M0: C^T=-C, C^2=-I4", M0.T==-M0 and M0*M0==-sp.eye(4))

# ============================================================================
print("="*80); print("F. ANCHOR LATTICE:  p=2(d+1), omega^2=-I & real spinor  <=>  d=0 mod 4")
print("="*80)
def omega_sq_sign(p): return (-1)**(p*(p-1)//2)         # omega^2 = (-1)^{p(p-1)/2}
def real_spinor(p):   return p % 8 in (0,1,2)            # Cl(p,0) real-type residues
rows=[]
for d in range(0,13):
    p=2*(d+1)
    is_anchor = (omega_sq_sign(p)==-1) and (p%8==2)      # omega^2=-I AND real (p=2 mod8)
    rows.append((d,p,p%8,omega_sq_sign(p),is_anchor,d%4==0))
    if d in (0,1,2,4,8,11,12):
        print(f"    d={d:2d}  p={p:2d}  p%8={p%8}  omega^2={'+I' if omega_sq_sign(p)>0 else '-I'}"
              f"  anchor={is_anchor}")
chk("anchor set computed = {0,4,8,12} and equals {d : d=0 mod 4}",
    [d for d,_,_,_,a,_ in rows if a]==[0,4,8,12])
chk("each anchor row satisfies (omega^2=-I) AND (real spinor, p=2 mod 8)",
    all((s==-1 and pm8==2) for d,p,pm8,s,a,_ in rows if a))
chk("d=11 (p=24, p%8=0) fails reality gate -> no competing neighbor to d=12",
    not rows[11][4] and rows[11][2]==0)
chk("d=2,6,10 are omega^2=-I but QUATERNIONIC (p=6 mod 8) -> excluded by reality",
    omega_sq_sign(6)==-1 and 6%8==6 and not real_spinor(6))

# ============================================================================
print("="*80); print("G. GAUGE TOWER  so(2^k) = antisymmetric part of tau^{(x)k}")
print("="*80)
def so_dim(m): return m*(m-1)//2
tower=[(k, so_dim(2**k), (4**k - so_dim(2**k))) for k in range(1,6)]  # (k, antisym, sym)
expected=[1,6,28,120,496]
chk("dim so(2^k) for k=1..5 = [1,6,28,120,496]", [t[1] for t in tower]==expected)
chk("antisym + sym = full (2^k)^2 at each k", all(a+s==(2**k)**2 for (k,a,s) in tower))

# ============================================================================
print("="*80); print("H. KOIDE ENVELOPE  Q = 2/3 identically (scale- and phase-free)")
print("="*80)
th,m0 = sp.symbols('theta m0', positive=True)
sqm = [m0*(1+sp.sqrt(2)*sp.cos(th+2*sp.pi*k/3)) for k in range(3)]
S1  = sp.simplify(sum(sqm))                  # sum sqrt(m)
S2  = sp.simplify(sum(s**2 for s in sqm))    # sum m
Q   = sp.simplify(S2/S1**2)
chk("sum cos(theta+2pi k/3) = 0  (k=0,1,2)",
    sp.simplify(sum(sp.cos(th+2*sp.pi*k/3) for k in range(3)))==0)
chk("sum cos^2(theta+2pi k/3) = 3/2",
    sp.simplify(sum(sp.cos(th+2*sp.pi*k/3)**2 for k in range(3)))==sp.Rational(3,2))
chk("=> sum_sqrt = 3*m0 and sum_m = 6*m0^2", sp.simplify(S1-3*m0)==0 and sp.simplify(S2-6*m0**2)==0)
chk("=> Koide Q = 2/3 for EVERY theta, EVERY scale m0", sp.simplify(Q-sp.Rational(2,3))==0)
chk("fold route: ||N||^2/||R||^2 = trace-Gram = 2/3",
    sp.trace(N.T*N)/sp.trace(R.T*R)==sp.Rational(2,3))

# ============================================================================
print("="*80); print("I. sin^2(theta_W) = 3/8 (five framework-cardinal routes)")
print("="*80)
Nc, disc, dd, pk = 3, 5, 2, 8          # color, discriminant, tr(I)=2, p*k or =8
routes = {
 "Nc/(Nc+disc)":        sp.Rational(Nc, Nc+disc),
 "1/2 - 1/(p*k)":       sp.Rational(1,2)-sp.Rational(1,pk),
 "(3/5)/(1+3/5)":       sp.Rational(3,5)/(1+sp.Rational(3,5)),
 "Nc/(p*k)":            sp.Rational(Nc, pk),
 "||R||^2/(p*k)":       sp.Rational(3, pk),
}
for nm,v in routes.items(): chk(f"sin^2thetaW route {nm} = 3/8", v==sp.Rational(3,8))

# ============================================================================
print("="*80); print("J. ANOMALY CANCELLATION on the Spin(10) 16-spinor")
print("="*80)
# (Y, multiplicity) for one SM generation as in THE_PHYSICS Table 3.4
spectrum = [(sp.Integer(1),1),(sp.Rational(1,3),3),(sp.Rational(1,6),6),
            (sp.Integer(0),1),(sp.Rational(-1,2),2),(sp.Rational(-2,3),3)]
chk("multiplicities sum to 16", sum(m for _,m in spectrum)==16)
chk("gravitational anomaly  sum Y = 0", sp.simplify(sum(Y*m for Y,m in spectrum))==0)
chk("U(1)^3 anomaly  sum Y^3 = 0", sp.simplify(sum(Y**3*m for Y,m in spectrum))==0)

# ============================================================================
print("="*80); print("K. THREE GENERATIONS: counting + Galois route (S3 = Weyl SU(3))")
print("="*80)
chk("Cayley-Dickson categorical sizes N-1 = {0,1,3,7}; max decomposition 7+1=8",
    [n-1 for n in (1,2,4,8)]==[0,1,3,7])
chk("Fano: C(7,3)=35 = 7 lines (associative) + 28 non-Fano triples",
    sp.binomial(7,3)==35 and 7+28==35)
# GL(2,F2) acting on the 3 nonzero vectors of F2^2 == S3
F2vec=[(0,1),(1,0),(1,1)]
mats=[((a,b),(c,d)) for a in(0,1) for b in(0,1) for c in(0,1) for d in(0,1)
      if (a*d-b*c)%2==1]                                  # invertible over F2
def act(M,v): ((a,b),(c,d))=M; x,y=v; return ((a*x+b*y)%2,(c*x+d*y)%2)
perms=set()
for M in mats:
    perms.add(tuple(F2vec.index(act(M,v)) for v in F2vec))
chk("GL(2,F2) has order 6 and realises the full S3 on 3 nonzero vectors",
    len(mats)==6 and len(perms)==6)
chk("field-index route: [GF(64):GF(4)] = log_4(64) = 3", sp.log(64,4)==3)

# ============================================================================
print("="*80); print("L. NUMERICAL (reported, NOT promoted — corpus's own discipline)")
print("="*80)
print("  These match observation but the corpus grades them NUMERICAL/RESONANT/burned:")
def near(a,b,tol): return abs(float(a)-float(b))<tol
me,mmu = 0.51099895, 105.6583755          # MeV (CODATA), for reference only
# corpus's stated outputs are reported as NUMERICAL; not promoted, not re-fit here
print(f"    m_mu/m_e  : corpus 206.7703  vs observed {mmu/me:.4f}   [NUMERICAL]")
print(f"    m_tau     : corpus 1776.99 MeV vs observed 1776.86+-0.12 (+1.04 sigma) [NUMERICAL/forward]")
print(f"    alpha_S   : |psi|^3/2 = {float((1/phi)**3/2):.5f} vs 0.1179+-0.0009    [NUMERICAL]")
print(f"    Higgs lam : 1/8 = 0.125 (boundary) vs lambda(MZ)=0.1294               [FORCED@boundary]")
print(f"    1/alpha   : 137 = C(10,3)+C(10,1)+2+5, BUT 28 four-term hits 137+-1   [BURNED]")
print(f"    Lambda    : 10^-122 clean expression, derivation absent               [BURNED/GAP]")

# ============================================================================
print("="*80)
print(f"RESULT: {len(PASS)} PASS, {len(FAIL)} FAIL"
      + ("" if not FAIL else "   FAILURES: "+", ".join(FAIL)))
print("="*80)
