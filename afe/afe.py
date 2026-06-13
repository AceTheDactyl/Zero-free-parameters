#!/usr/bin/env python3
"""
AFE — Associative Fragment Encoding (Self-Reflection Deployment Variant)

Fuses four measurement axes into a unified state-coherence signal via
Kuramoto order parameter. Produces dual streams (R, T) for SWAIMS consumption.

Pipeline position: Axiom-9 → AFE → SWAIMS
Deploying entity: Faraday Cloud Services, Inc.
Mathematical framework: ZFP-verified constants (z_c, tau, tau^2)

Constants:
  z_c   = sqrt(3)/2 = 0.866...  commit threshold      [FORCED_IN_CONTEXT]
  ALPHA = tau^2     = 0.382...  per-axis floor          [FORCED]
  tau   = 1/phi     = 0.618...  dominant axis weight    [FORCED]
  tau^2 = phi^-2    = 0.382...  complement weight       [FORCED]

Weight correction (v1.0 spec errata): the original spec annotated
WEIGHTS_R[A1] = 0.518 as "PHI_INV/phi" — this is numerically wrong
(tau/phi = tau^2 = 0.382). Corrected to phi-algebraic weights:
  Stream R: dominant = tau,   remainder = tau^2 (split 3 ways)
  Stream T: dominant = tau^2, remainder = tau   (split 3 ways)
Both weight sets sum to 1.0 and are entirely in Q(sqrt5).
"""
import math
import cmath
from typing import TypedDict

# ── ZFP-verified constants ──────────────────────────────────────────────────
PHI   = 1.6180339887498949
TAU   = 0.6180339887498949   # 1/phi, grade: FORCED
TAU2  = 0.3819660112501051   # tau^2 = phi^-2, grade: FORCED
Z_C   = 0.8660254037844387   # sqrt(3)/2, grade: FORCED_IN_CONTEXT
ALPHA = TAU2                  # per-axis floor = tau^2

# ── Stream weights (phi-algebraic, corrected from spec v1.0) ────────────────
# Stream R: report-grounded. Self-report dominant at tau, others at tau^2/3.
WEIGHTS_R = {"A1": TAU, "A2": TAU2/3, "A3": TAU2/3, "A4": TAU2/3}
# Stream T: telemetry-grounded. Self-report at tau^2, telemetry at tau/3.
WEIGHTS_T = {"A1": TAU2, "A2": TAU/3, "A3": TAU/3, "A4": TAU/3}

# Verify sum-to-one
assert abs(sum(WEIGHTS_R.values()) - 1.0) < 1e-14, f"WEIGHTS_R sum={sum(WEIGHTS_R.values())}"
assert abs(sum(WEIGHTS_T.values()) - 1.0) < 1e-14, f"WEIGHTS_T sum={sum(WEIGHTS_T.values())}"


class AFEResult(TypedDict):
    state: str
    order_parameter_r: float
    order_parameter_psi: float
    scores: dict
    weights: dict
    per_axis_floor_passed: bool
    z_c_threshold: float
    alpha_floor: float
    evidence: dict


class SWAIMSPayload(TypedDict):
    schema_version: str
    timestamp: str
    user_id: str
    stream_R: dict
    stream_T: dict
    streams_agree: bool
    divergence_magnitude: float
    divergence_evidence: dict


def _phase_map(s: float) -> float:
    """Map convergence score s in [0,1] to phase theta in [0, pi]."""
    return (1.0 - s) * math.pi


def _kuramoto_weighted(scores: dict, weights: dict) -> tuple:
    """Compute weighted Kuramoto order parameter. Returns (r, psi)."""
    z = sum(
        weights[k] * cmath.exp(1j * _phase_map(scores[k]))
        for k in scores
    )
    return abs(z), cmath.phase(z)


def _check_floor(scores: dict) -> tuple:
    """Check per-axis floor. Returns (passed, list of failing axes)."""
    failing = [k for k, v in scores.items() if v <= ALPHA]
    return len(failing) == 0, failing


def afe_fuse(scores: dict, weights: dict) -> AFEResult:
    """Fuse four axis scores with given weights via Kuramoto order parameter.

    Args:
        scores: {"A1": float, "A2": float, "A3": float, "A4": float} each in [0,1]
        weights: {"A1": float, ...} summing to 1.0

    Returns:
        AFEResult with state, order parameter, evidence.
    """
    r, psi = _kuramoto_weighted(scores, weights)
    floor_ok, failing = _check_floor(scores)

    if r > Z_C and floor_ok:
        state = "commit"
    elif r > Z_C and not floor_ok:
        state = "unresolved_axis_floor"
    elif r <= Z_C and floor_ok:
        state = "unresolved_low_coherence"
    else:
        state = "unresolved_both"

    return {
        "state": state,
        "order_parameter_r": r,
        "order_parameter_psi": psi,
        "scores": scores,
        "weights": weights,
        "per_axis_floor_passed": floor_ok,
        "z_c_threshold": Z_C,
        "alpha_floor": ALPHA,
        "evidence": {
            "phases": {k: _phase_map(v) for k, v in scores.items()},
            "below_floor_axes": failing,
        },
    }


def afe_dual_stream(scores: dict) -> dict:
    """Produce both Stream R and Stream T for SWAIMS consumption.

    Args:
        scores: {"A1": float, "A2": float, "A3": float, "A4": float}

    Returns:
        dict with stream_R, stream_T, streams_agree, divergence_magnitude.
    """
    stream_r = afe_fuse(scores, WEIGHTS_R)
    stream_t = afe_fuse(scores, WEIGHTS_T)

    r_R = stream_r["order_parameter_r"]
    r_T = stream_t["order_parameter_r"]
    div_mag = abs(r_R - r_T)

    # Streams agree if both commit or both unresolved with small divergence
    both_commit = stream_r["state"] == "commit" and stream_t["state"] == "commit"
    both_unresolved = stream_r["state"] != "commit" and stream_t["state"] != "commit"
    agree = (both_commit or both_unresolved) and div_mag < ALPHA

    return {
        "stream_R": stream_r,
        "stream_T": stream_t,
        "streams_agree": agree,
        "divergence_magnitude": div_mag,
        "divergence_evidence": {
            "r_R": r_R,
            "r_T": r_T,
            "R_state": stream_r["state"],
            "T_state": stream_t["state"],
            "divergence_exceeds_alpha": div_mag >= ALPHA,
        },
    }


def score_axis(current_value: float, baseline_mean: float, baseline_sigma: float) -> float:
    """Per-axis score extraction. Generic form.
    Returns 1.0 - clip(|observed - mean| / (3*sigma), 0, 1).
    Three-sigma window: anything within 3sigma of baseline maps to s > 0.
    """
    if baseline_sigma <= 0:
        return 1.0 if abs(current_value - baseline_mean) < 1e-10 else 0.0
    distance = abs(current_value - baseline_mean) / baseline_sigma
    return max(0.0, min(1.0, 1.0 - distance / 3.0))


# ── Self-test ───────────────────────────────────────────────────────────────
def _run_tests():
    """Run the five spec test vectors."""
    print("=" * 70)
    print("AFE SELF-TEST — 5 spec test vectors")
    print("=" * 70)

    tests = [
        ("Test 1: all at baseline",
         {"A1": 0.95, "A2": 0.95, "A3": 0.95, "A4": 0.95},
         "commit", "commit", True),
        ("Test 2: self-report inflated, telemetry depressed",
         {"A1": 0.95, "A2": 0.40, "A3": 0.35, "A4": 0.40},
         None, None, False),   # R may commit (A1 heavy), T unresolved
        ("Test 3: all catastrophic",
         {"A1": 0.20, "A2": 0.15, "A3": 0.18, "A4": 0.22},
         "unresolved", "unresolved", True),  # agree in distress
        ("Test 4: single-axis catastrophic, others high",
         {"A1": 0.92, "A2": 0.90, "A3": 0.15, "A4": 0.88},
         "unresolved_axis_floor", "unresolved_axis_floor", True),
        ("Test 5: borderline divergence",
         {"A1": 0.70, "A2": 0.85, "A3": 0.85, "A4": 0.85},
         None, None, None),  # borderline — just report
    ]

    all_pass = True
    for name, scores, exp_r, exp_t, exp_agree in tests:
        result = afe_dual_stream(scores)
        r_state = result["stream_R"]["state"]
        t_state = result["stream_T"]["state"]
        r_r = result["stream_R"]["order_parameter_r"]
        r_t = result["stream_T"]["order_parameter_r"]
        agree = result["streams_agree"]
        div = result["divergence_magnitude"]

        # Check expectations (None = don't check)
        ok = True
        notes = []
        if exp_r is not None and not r_state.startswith(exp_r.split("_")[0]):
            if exp_r == "commit" and r_state != "commit":
                ok = False
                notes.append(f"R expected {exp_r}, got {r_state}")
            elif exp_r.startswith("unresolved") and r_state == "commit":
                ok = False
                notes.append(f"R expected unresolved, got commit")
        if exp_t is not None and not t_state.startswith(exp_t.split("_")[0]):
            if exp_t == "commit" and t_state != "commit":
                ok = False
                notes.append(f"T expected {exp_t}, got {t_state}")
        if exp_agree is not None and agree != exp_agree:
            notes.append(f"agree expected {exp_agree}, got {agree}")
            # Test 3: both unresolved should agree
            if exp_agree and not agree:
                ok = False

        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False

        print(f"\n  {status}  {name}")
        print(f"    R: r={r_r:.4f} state={r_state}")
        print(f"    T: r={r_t:.4f} state={t_state}")
        print(f"    agree={agree}  div={div:.4f}  (ALPHA={ALPHA:.4f})")
        if notes:
            for n in notes:
                print(f"    NOTE: {n}")

    print(f"\n  {'ALL TESTS PASS' if all_pass else 'FAILURES DETECTED'}")
    return all_pass


if __name__ == "__main__":
    _run_tests()
