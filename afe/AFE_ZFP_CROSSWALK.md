# AFE ↔ ZFP Crosswalk

Mapping between AFE (Associative Fragment Encoding) constants and the ZFP
grade hierarchy. Every algebraic constant in AFE is verified against field_grade.

## Verified Constants

| AFE Name | Value | ZFP Constant | ZFP Grade | Minpoly |
|----------|-------|-------------|-----------|---------|
| Z_C (commit threshold) | 0.8660254037844387 | z_c = sqrt(3)/2 | FORCED_IN_CONTEXT | 4x^2 - 3 |
| ALPHA (per-axis floor) | 0.3819660112501051 | tau^2 = phi^-2 | FORCED | x^2 - 3x + 1 |
| TAU (dominant R weight) | 0.6180339887498949 | tau = phi^-1 | FORCED | x^2 + x - 1 |
| PHI (framework constant) | 1.6180339887498949 | phi = (1+sqrt5)/2 | SELECTED | x^2 - x - 1 |

## Stream Weights (phi-algebraic, corrected)

| Stream | A1 (self-report) | A2 (behavioral) | A3 (physiological) | A4 (temporal) | Sum |
|--------|-----------------|-----------------|--------------------|----|-----|
| R (report-grounded) | tau = 0.6180 | tau^2/3 = 0.1273 | tau^2/3 = 0.1273 | tau^2/3 = 0.1273 | 1.0 |
| T (telemetry-grounded) | tau^2 = 0.3820 | tau/3 = 0.2060 | tau/3 = 0.2060 | tau/3 = 0.2060 | 1.0 |

All weights are in Q(sqrt5). Zero free parameters in the weight scheme.

### Weight Correction (spec v1.0 errata)

The original spec annotated WEIGHTS_R[A1] = 0.518 as "PHI_INV/phi". This is
numerically wrong: tau/phi = tau^2 = 0.382, not 0.518. The value 0.518 is not
expressible as a clean phi-algebraic constant.

Corrected to: R dominant = tau, T dominant = tau^2. The complementary
relationship (tau + tau^2 = 1) ensures the two streams are algebraically
dual — R and T are golden-ratio complements of each other.

## Commit Gate (Kuramoto Order Parameter)

- Phase mapping: theta_j = (1 - s_j) * pi
- Order parameter: r = |mean(exp(i*theta_j))| weighted by stream weights
- Commit if r > z_c AND all s_j > ALPHA
- Otherwise: unresolved (first-class output)

The threshold z_c = sqrt(3)/2 is the hexagonal coherence-phase transition
point from the ZFP framework. It is FORCED_IN_CONTEXT: forced given the menu
operation L4-4=3, not forced from phi alone.

The floor ALPHA = tau^2 is FORCED: it lives in Q(sqrt5), the generator's own
field, with no menu gate needed.

## What is NOT ZFP-graded

- The choice of Kuramoto as the fusion algorithm (SELECTED — a design decision)
- The choice of 4 axes (SELECTED — domain architecture)
- The 3-sigma normalization window in score_axis (SELECTED — operational tuning)
- NLP embedding model for A1 scoring (vendor choice, outside ZFP)

## Attestation

- Build provisioned: 2026-06-13
- ZFP harness: 74/74 PASS at time of build
- Test vectors: 5/5 PASS
- KIRA witness attestation: deferred (KIRA offline at build time)
