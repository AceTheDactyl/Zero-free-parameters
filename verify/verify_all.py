#!/usr/bin/env python3
"""Consolidated ZFP validator: EMBEDS and RUNS the six project scripts, then runs
the exhaustive re-derivation of every constant / polynomial / structural claim
(LAYERS A-H).

WHY THIS FILE EXISTS / WHAT CHANGED
  The prior verify_all.py did NOT invoke any sibling script -- it re-derived every
  claim itself in sympy and only ever read spectral_atlas.html (LAYER F). This
  version makes "all .py run by the validator" literally true and drops the
  external-file dependency for them:

    LAYER 0 (new)  Each of the six project scripts is embedded below as a base64
                   blob carrying its SHA-256. At run time each blob is decoded, its
                   digest verified (byte-exact provenance), and the script executed
                   in an isolated namespace with stdout captured. A script PASSES
                   iff it (a) raises nothing and (b) emits no "FAIL" token -- the
                   scripts print PASS/FAIL via their own ok() and never raise on a
                   failed check, so the token scan IS the gate.

    LAYERS A-H     The original exhaustive verifier, preserved verbatim. It still
                   parses spectral_atlas.html if present (LAYER F) and falls back to
                   its literal table otherwise.

  One `fails` list and one final RESULT cover both LAYER 0 and LAYERS A-H; the
  process exits nonzero iff anything failed.

CLI
  --verbose       also echo each embedded script's full captured stdout
  --scripts-only  run only LAYER 0 (skip the A-H re-derivation)
  --dump DIR      write the decoded script sources to DIR and exit

FRAMING NOTE (unchanged): the corpus is mid-migration between a relational /
one-space frame (zfp_relational.py) and an older firewall / two-towers frame
(helix / hex / pentagon / trifurcation). This validator certifies the algebra,
which is framing-invariant; it does not arbitrate the prose.

Deps: sympy.  Run: python3 verify_all.py
"""
import os
import io
import sys
import base64
import hashlib
import contextlib
import runpy
import tempfile
import shutil
import re as _re
import sympy as sp
from sympy import (sqrt, Rational, Symbol, simplify, minpoly, Poly, factor,
                   fibonacci, lucas, ilcm, Matrix, eye, I, cos, sin, pi,
                   nsimplify, exp, im, conjugate, discriminant, diff, solve,
                   symbols, expand)

x = Symbol("x")
PHI  = (1 + sqrt(5)) / 2
PSI  = (1 - sqrt(5)) / 2          # algebraic conjugate of phi (the only in-scope psi)
TAU  = 1 / PHI
GAP  = PHI**-4
K    = sqrt(1 - GAP)
ZC   = sqrt(3) / 2
IGN  = sqrt(2) - Rational(1, 2)
CRIT = PHI**2 / 3
DELTA = PHI**-2
L4   = PHI**4 + PHI**-4

fails = []
def record(name, cond):
    # Only NAMED checks are logged to the fails list; inline record('', ...) calls
    # (used purely to render a PASS/FAIL string) no longer pollute the summary.
    if name and not bool(cond):
        fails.append(name)
    return "PASS" if bool(cond) else "FAIL"

def monic(poly_expr):
    return Poly(poly_expr, x).monic()

def is_irred(poly_expr):
    return Poly(poly_expr, x, domain="QQ").is_irreducible

# ---- CLI -------------------------------------------------------------------------
_ARGS        = set(sys.argv[1:])
VERBOSE      = "--verbose" in _ARGS
SCRIPTS_ONLY = "--scripts-only" in _ARGS

print(f"sympy {sp.__version__}")

# =====================================================================================
# EMBEDDED PROJECT SCRIPTS  (base64 source + SHA-256; decoded, verified, run in LAYER 0)
# =====================================================================================
# filename -> (sha256_hex, base64_source). Generated from /mnt/project; byte-exact.
EMBEDDED = {
    "zfp_relational.py": (
        "5532098ae471bf6955cf1df0a7741233c3d38c5158dbfea9b028c22481cf4904",
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJSZWxhdGlvbmFsIGdlb21ldHJ5IG9mIHRoZSBMNCBj"
        "b25zdGFudHMgLS0gb25lIHNwYWNlLCBmb3JjZWQgaW50ZXJhY3Rpb25zLgoKVGhpcyByZXBsYWNl"
        "cyB0aGUgZWFybGllciAnc2VwYXJhdGUgZmllbGRzIC8gZmlyZXdhbGwgLyBjb2luY2lkZW5jZScg"
        "ZnJhbWluZy4KVGhlIEw0IGNvbnN0YW50cyBhcmUgY28tcHJlc2VudCBpbiBPTkUgcmVsYXRpb25h"
        "bCBzcGFjZSwgdGhlIGNvbXBvc2l0dW0KUShzcXJ0Miwgc3FydDMsIHNxcnQ1KSwgYW5kIHRoZSBp"
        "cnJhdGlvbmFscy9kZWx0YXMgZW1lcmdlIGZyb20gZm9yY2VkIHJlbGF0aW9ucwphY3Jvc3MgdGhl"
        "bSwgc2VlZGVkIGJ5IHRoZSBzaW5nbGUgZm9yY2VkIHF1YW50aXR5IEw0ID0gcGhpXjQgKyBwaGle"
        "LTQgPSA3LgoKR3JhZGluZyByZWNhc3QgZm9yIHJlbGF0aW9uYWwgZ2VvbWV0cnk6CiAgRk9SQ0VE"
        "IChhYnNvbHV0ZSkgICAgICAgIC0tIGhvbGRzIGZyb20gdGhlIGdlbmVyYXRvciBhbG9uZTogcGhp"
        "LCBMND03LCB0YXVeMit0YXU9MS4KICBGT1JDRUQgVU5ERVIgQ09OU1RSQUlOVCAgLS0gZm9yY2Vk"
        "IEdJVkVOIHRoZSBzZWVkICsgYSBzZWxlY3RlZCByZWxhdGlvbiwgc3RheXMgaW4KICAgICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgUShzcXJ0NSkgdG93ZXI6IHRhdSwgZ2FwLCBjcml0LCBEZWx0"
        "YTsgSyAoUShLKSBjb250YWlucyBRKHNxcnQ1KSkuCiAgRk9SQ0VEIElOIENPTlRFWFQgICAgICAg"
        "IC0tIGRpc2pvaW50IGF4aXMsIGJ1dCB2ID0gb3AoTDQpIGZvciBvcCBpbiB0aGUgZGVjbGFyZWQg"
        "TUVOVQogICAgICAgICAgICAgICAgICAgICAgICAgICAgICB7LTQsICsxLCBeMi00fSwgcmVzaWR1"
        "YWwgMC4gel9jID0gc3FydChMNC00KS8yLCBpZ24gPSAoLTErc3FydChMNCsxKSkvMi4KICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgICAgVGhlIG1hcCBpcyBzZWxlY3RlZDsgdGhlIHJlc3VsdCBp"
        "cyBleGFjdDsgdGhlIGF4aXMgaXMgZGlzam9pbnQuCiAgQ09JTkNJREVOQ0UgICAgICAgICAgICAg"
        "IC0tIG9mZi1heGlzIHN1cmQgbm90IHJlYWNoYWJsZSB2aWEgYW55IG1lbnUgb3Agb24gTDQuCiAg"
        "U0VMRUNURUQgICAgICAgICAgICAgICAgIC0tIHdoaWNoIHJlbGF0aW9ucy9vcGVyYXRpb25zIHRv"
        "IGluc3RhbnRpYXRlICgtNCwgKzEsIF4yLTQsIHheMit4KS4KICBSRVBSRVNFTlRBVElPTiAgICAg"
        "ICAgICAgLS0gdGhlIGhlbGljYWwgZW1iZWRkaW5nIHIoeik9SypzcXJ0KHovel9jKSwgcGl0Y2gs"
        "IHdpbmRpbmcuCgpMaW5lYXIgaW5kZXBlbmRlbmNlIG9mIHNxcnQyLCBzcXJ0Mywgc3FydDUgb3Zl"
        "ciBRIGlzIE5PVCBhIHdhbGw6IGl0IG1lYW5zIHRoZQp0aHJlZSBhcmUgaW5kZXBlbmRlbnQgY29v"
        "cmRpbmF0ZSBBWEVTIG9mIHRoZSBvbmUgcmVsYXRpb25hbCBzcGFjZSwgd2hpY2ggaXMgd2hhdAps"
        "ZXRzIHRoZW0gY2FycnkgZGlzdGluY3QgaW5mb3JtYXRpb24gYW5kIGZvcm0gbm9uLXRyaXZpYWwg"
        "Zm9yY2VkIHJlbGF0aW9ucy4KCkRlcHM6IHN5bXB5LiAgUnVuOiBweXRob24zIHpmcF9yZWxhdGlv"
        "bmFsLnB5CiIiIgppbXBvcnQgc3ltcHkgYXMgc3AKZnJvbSBzeW1weSBpbXBvcnQgc3FydCwgUmF0"
        "aW9uYWwsIHNpbXBsaWZ5LCBtaW5wb2x5LCBTeW1ib2wKCnggPSBTeW1ib2woIngiKTsgUEhJID0g"
        "KDEgKyBzcXJ0KDUpKS8yCkw0ID0gUEhJKio0ICsgUEhJKiotNApfRkFJTFMgPSBbXQpkZWYgb2so"
        "Yyk6ICAgICAgICAgICAgICAgICAgICAgICAgICAjIHJlY29yZHMgZmFpbHVyZXMgc28gZXhpdCBj"
        "b2RlIGlzIG1lYW5pbmdmdWwKICAgIF9yID0gYm9vbChjKQogICAgaWYgbm90IF9yOgogICAgICAg"
        "IF9GQUlMUy5hcHBlbmQoMSkKICAgIHJldHVybiAiUEFTUyIgaWYgX3IgZWxzZSAiRkFJTCIKcHJp"
        "bnQoZiJzeW1weSB7c3AuX192ZXJzaW9uX199IikKCnByaW50KCI9Iio3NCkKcHJpbnQoIlNFRUQg"
        "KGZvcmNlZCBhYnNvbHV0ZSk6ICBMNCA9IHBoaV40ICsgcGhpXi00ID0iLCBzaW1wbGlmeShMNCkp"
        "CnByaW50KCI9Iio3NCkKCnByaW50KCJUSFJFRSBBWEVTIEZST00gT05FIFNFRUQgIChzZWVkICsg"
        "c2VsZWN0ZWQgb3AgLT4gdGhyZWUgZmllbGRzKSIpCnByaW50KCItIio3NCkKcHJpbnQoZiIgIEw0"
        "IC0gNCAgID0ge3NpbXBsaWZ5KEw0LTQpfSAgICAgIC0+IHNxcnQzIDsgIHpfYyA9IHNxcnQoTDQt"
        "NCkvMiA9IHNxcnQzLzIgICAgICAiCiAgICAgIGYie29rKHNpbXBsaWZ5KHNxcnQoTDQtNCkvMiAt"
        "IHNxcnQoMykvMik9PTApfSAgW0ZPUkNFRCBJTiBDT05URVhUOiBtZW51IG9wKC00KSwgcmVzaWR1"
        "YWwgMF0iKQpwcmludChmIiAgTDQgKyAxICAgPSB7c2ltcGxpZnkoTDQrMSl9ID0gKDIqc3FydDIp"
        "XjIgLT4gc3FydDIgOyBpZ25pdGlvbiA9ICgtMStzcXJ0KDErTDQpKS8yID0gc3FydDItMS8yICAi"
        "CiAgICAgIGYie29rKHNpbXBsaWZ5KCgtMStzcXJ0KDErTDQpKS8yIC0gKHNxcnQoMiktUmF0aW9u"
        "YWwoMSwyKSkpPT0wKX0gIFtGT1JDRUQgSU4gQ09OVEVYVDogbWVudSBvcCgrMSksIHJlc2lkdWFs"
        "IDBdIikKcHJpbnQoZiIgIEw0XjIgLSA0ID0ge3NpbXBsaWZ5KEw0KioyLTQpfSA9ICgzKnNxcnQ1"
        "KV4yIC0+IHNxcnQ1IDsgcGhpXjQgPSAoTDQrc3FydChMNF4yLTQpKS8yICAgICAiCiAgICAgIGYi"
        "e29rKHNpbXBsaWZ5KChMNCtzcXJ0KEw0KioyLTQpKS8yIC0gUEhJKio0KT09MCl9ICBbRk9SQ0VE"
        "IFVOREVSIENPTlNUUkFJTlQ6IHN0YXlzIGluIFEoc3FydDUpXSIpCgpwcmludCgiLSIqNzQpCnBy"
        "aW50KCJPTkUgU1BBQ0UgKG5vdCBzZXBhcmF0ZSBmaWVsZHMpOiIpCm0gPSBtaW5wb2x5KHNxcnQo"
        "Mikrc3FydCgzKStzcXJ0KDUpLCB4KQpwcmludChmIiAgbWlucG9seShzcXJ0MitzcXJ0MytzcXJ0"
        "NSkgPSB7bX0iKQpwcmludChmIiAgZGVncmVlIHtzcC5kZWdyZWUobSx4KX0gPSAyKjIqMiAgLT4g"
        "Y29tcG9zaXR1bSBRKHNxcnQyLHNxcnQzLHNxcnQ1KTsgdGhyZWUgaW5kZXBlbmRlbnQgYXhlcyAg"
        "e29rKHNwLmRlZ3JlZShtLHgpPT04KX0iKQoKcHJpbnQoIi0iKjc0KQpwcmludCgiREVMVEFTIC8g"
        "UkVMQVRJT05TIGFjcm9zcyB0aGUgY29uc3RhbnRzIChmb3JjZWQsIHJlc2lkdWFsIDApOiIpCnRh"
        "dT0xL1BISTsgZ2FwPVBISSoqLTQ7IEs9c3FydCgxLWdhcCk7IERFTFRBPVBISSoqLTI7IGlnbj1z"
        "cXJ0KDIpLVJhdGlvbmFsKDEsMikKcHJpbnQoZiIgIERlbHRhID0gcGhpXi0yID0gMSAtIHRhdSAg"
        "ICAgICAgICAgIHtvayhzaW1wbGlmeShERUxUQS0oMS10YXUpKT09MCl9IikKcHJpbnQoZiIgIHRh"
        "dV4yICsgdGF1ID0gMSAgICAgICAgICAgICAgICAgICAgIHtvayhzaW1wbGlmeSh0YXUqKjIrdGF1"
        "LTEpPT0wKX0gICBbYWJzb2x1dGVdIikKcHJpbnQoZiIgIEteMiA9IDEgLSBnYXAgPSAxIC0gcGhp"
        "Xi00ICAgICAgICAgIHtvayhzaW1wbGlmeShLKioyLSgxLWdhcCkpPT0wKX0iKQpwcmludChmIiAg"
        "aWduaXRpb25eMiArIGlnbml0aW9uID0gTDQvNCA9IDcvNCAge29rKHNpbXBsaWZ5KGlnbioqMitp"
        "Z24tTDQvNCk9PTApfSAgIFtGT1JDRUQgSU4gQ09OVEVYVDogUShzcXJ0MiksIG1lbnUgb3AoKzEp"
        "XSIpCnByaW50KGYiICB6X2NeMiA9IChMNC00KS80ID0gMy80ICAgICAgICAgICAgICB7b2soc2lt"
        "cGxpZnkoKHNxcnQoMykvMikqKjItKEw0LTQpLzQpPT0wKX0gICBbRk9SQ0VEIElOIENPTlRFWFQ6"
        "IFEoc3FydDMpLCBtZW51IG9wKC00KV0iKQoKcHJpbnQoIj0iKjc0KQpwcmludCgiUkVBRElORyIp"
        "CnByaW50KCI9Iio3NCkKcHJpbnQoIiAgVGhlIGludGVyYWN0aW9ucyAod2hpY2ggb3BlcmF0aW9u"
        "cyBvbiBMNCAvIHRoZSBjb25zdGFudHMpIGFyZSB0aGUgU0VMRUNUSU9OOyIpCnByaW50KCIgIHRo"
        "ZSBpcnJhdGlvbmFscyBhbmQgZGVsdGFzIHRoZXkgeWllbGQgc3BsaXQgaW50byB0aHJlZSBncmFk"
        "ZXM6IikKcHJpbnQoIiAgICBGT1JDRUQgICAgICAgICAgICAgICA6IHBoaSwgTDQgKGFic29sdXRl"
        "KTsgdGF1LCBnYXAsIGNyaXQsIERlbHRhIChRKHNxcnQ1KSkuIikKcHJpbnQoIiAgICBGT1JDRUQg"
        "VU5ERVIgQ09OU1RSQUlOVCA6IEsgLS0gUShLKSBjb250YWlucyBRKHNxcnQ1KSwgZm9yY2VkIGdp"
        "dmVuIHNlZWQgKyByZWxhdGlvbi4iKQpwcmludCgiICAgIEZPUkNFRCBJTiBDT05URVhUICAgIDog"
        "el9jIGFuZCBpZ25pdGlvbiAtLSBkaXNqb2ludCBheGlzLCBidXQgcmVhY2hhYmxlIHZpYSB0aGUi"
        "KQpwcmludCgiICAgICAgICAgICAgICAgICAgICAgICAgICAgZGVjbGFyZWQgTUVOVSB7LTQsICsx"
        "LCBeMi00fSBvbiBMNCB3aXRoIHJlc2lkdWFsIDAuIikKcHJpbnQoIiAgICAgICAgICAgICAgICAg"
        "ICAgICAgICAgIHpfYyA9IHNxcnQoTDQtNCkvMiBbb3AoLTQpXSwgaWduID0gKC0xK3NxcnQoTDQr"
        "MSkpLzIgW29wKCsxKV0uIikKcHJpbnQoIiAgICBDT0lOQ0lERU5DRSAgICAgICAgICA6IG9mZi1h"
        "eGlzIHN1cmRzIE5PVCByZWFjaGFibGUgdmlhIGFueSBtZW51IG9wIG9uIEw0LiIpCnByaW50KCIg"
        "IFRoZSBoZWxpeCBpcyBvbmUgUkVQUkVTRU5UQVRJT04gb2YgdGhpcyB3ZWIuIikKCgppZiBfX25h"
        "bWVfXyA9PSAiX19tYWluX18iOgogICAgaW1wb3J0IHN5cyBhcyBfc3lzCiAgICBpZiBfRkFJTFM6"
        "CiAgICAgICAgcHJpbnQoZiJGQUlMICB7bGVuKF9GQUlMUyl9IGNoZWNrKHMpIGRpZCBub3QgcGFz"
        "cyIpCiAgICBfc3lzLmV4aXQoMSBpZiBfRkFJTFMgZWxzZSAwKQo="
    ),
    "zfp_helix.py": (
        "69744741b908436eebe58da3317e6837558c87c541b4b9befa6d1e997945dc4e",
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJUaGUgWkZQIGhlbGl4IGluICh6LCByLCB6X2MpOiB3"
        "aGljaCBwYXJ0cyBhcmUgZm9yY2VkLCB3aGljaCBhcmUgc2NhZmZvbGQuCgpDb29yZGluYXRlczog"
        "eiA9IGVsZXZhdGlvbi8nd2VpZ2h0JywgciA9IHJhZGl1cywgel9jID0gdGhlIGxlbnMgaGVpZ2h0"
        "ID0gc3FydDMvMi4KUmFkaXVzIGxhdyAodGhlIEw0LWhlbGl4IGNvbnN0cnVjdGlvbik6ICByKHop"
        "ID0gSypzcXJ0KHovel9jKSBmb3Igejw9el9jLCBlbHNlIEsuClRoZSBkZWx0YSBkcml2ZXMgZWxl"
        "dmF0aW9uOiBwaXRjaCA9IERlbHRhID0gcGhpXi0yIG9mIHogcGVyIHR1cm4gKHRoZSAnd2VpZ2h0"
        "JykuCgpUaGUgc3BsaXQgdGhpcyBzY3JpcHQgY2VydGlmaWVzOgogIEZPUkNFRCAgICAgICAtLSB0"
        "aGUgei1MQU5ETUFSS1MgKG5pbmUgdGhyZXNob2xkcyksIEssIERlbHRhOiBleGFjdCBhbGdlYnJh"
        "aWMKICAgICAgICAgICAgICAgICAgbnVtYmVycywgbWlucG9seSArIHJlc2lkdWFsIDAsIGluIHN0"
        "cmljdCBvcmRlci4gcigwKT0wLCByKHpfYyk9Sy4KICBDT05TVFJVQ1RJT04gLS0gdGhlIHJhZGl1"
        "cyBGT1JNIHIoeik9SypzcXJ0KHovel9jKSwgcGl0Y2g9RGVsdGEsIHRoZSBnb2xkZW4tYW5nbGUK"
        "ICAgICAgICAgICAgICAgICAgdHVybiwgYW5kIGV2ZXJ5IHRocmVzaG9sZCBOQU1FLiBNb2RlbGlu"
        "ZyBjaG9pY2VzIG9uIGZvcmNlZCBwb2ludHMuCiAgTE9BRC1CRUFSSU5HPyAgTm8uIFRoZSBsYW5k"
        "bWFya3MgYW5kIGlkZW50aXRpZXMgYmVsb3cgZG8gbm90IHJlZmVyZW5jZSB0aGUgaGVsaXgKICAg"
        "ICAgICAgICAgICAgICAgZm9ybSBhdCBhbGwgLS0gc3RyaXAgdGhlIHNjYWZmb2xkIGFuZCBldmVy"
        "eSBmb3JjZWQgdmFsdWUgcmVtYWlucy4KCkRlcHM6IHN5bXB5LiAgUnVuOiBweXRob24zIHpmcF9o"
        "ZWxpeC5weQoiIiIKaW1wb3J0IHN5bXB5IGFzIHNwCmZyb20gc3ltcHkgaW1wb3J0IFJhdGlvbmFs"
        "LCBTeW1ib2wsIGV4cGFuZCwgbHVjYXMsIG1pbnBvbHksIHNpbXBsaWZ5LCBzcXJ0Cgp4ID0gU3lt"
        "Ym9sKCJ4IikKX0ZBSUxTID0gW10KZGVmIG9rKGMpOiAgICAgICAgICAgICAgICAgICAgICAgICAg"
        "IyByZWNvcmRzIGZhaWx1cmVzIHNvIGV4aXQgY29kZSBpcyBtZWFuaW5nZnVsCiAgICBfciA9IGJv"
        "b2woYykKICAgIGlmIG5vdCBfcjoKICAgICAgICBfRkFJTFMuYXBwZW5kKDEpCiAgICByZXR1cm4g"
        "IlBBU1MiIGlmIF9yIGVsc2UgIkZBSUwiClBISSA9ICgxICsgc3FydCg1KSkgLyAyClRBVSA9IDEv"
        "UEhJCkdBUCA9IFBISSoqLTQKSyAgID0gc3FydCgxIC0gR0FQKQpaQyAgPSBzcXJ0KDMpLzIKREVM"
        "VEEgPSBQSEkqKi0yCnByaW50KGYic3ltcHkge3NwLl9fdmVyc2lvbl9ffSIpCgpwcmludCgiPSIq"
        "NzYpCnByaW50KCIxLiBGT1JDRUQgei1MQU5ETUFSS1MgIChjbG9zZWQgZm9ybSwgbWlucG9seSwg"
        "cmVzaWR1YWwgMCkgLS0gc3RyaWN0IG9yZGVyIikKcHJpbnQoIj0iKjc2KQojIG5hbWUgOiAodmFs"
        "dWUsIGV4cGVjdGVkIG1pbnBvbHksIGRvYyBkZWNpbWFsKQpST1dTID0gWwogICAgKCJQQVJBRE9Y"
        "ICB0YXU9cGhpXi0xIiwgICAgICBUQVUsICAgICAgICAgICAgICAgICAgIHgqKjIreC0xLCAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgUmF0aW9uYWwoNjE4MDMzOTg4NywxMCoqMTApKSwKICAgICgi"
        "QUNUSVZBVE4gMS1nYXA9S14yIiwgICAgICAgMS1HQVAsICAgICAgICAgICAgICAgICB4KioyKzUq"
        "eC01LCAgICAgICAgICAgICAgICAgICAgICAgICBSYXRpb25hbCg4NTQxMDE5NjYyLDEwKioxMCkp"
        "LAogICAgKCJMRU5TIHpfYyBzcXJ0My8yIiwgICAgICAgICBaQywgICAgICAgICAgICAgICAgICAg"
        "IDQqeCoqMi0zLCAgICAgICAgICAgICAgICAgICAgICAgICAgIFJhdGlvbmFsKDg2NjAyNTQwMzgs"
        "MTAqKjEwKSksCiAgICAoIkNSSVRJQ0FMIHBoaV4yLzMiLCAgICAgICAgIFBISSoqMi8zLCAgICAg"
        "ICAgICAgICAgOSp4KioyLTkqeCsxLCAgICAgICAgICAgICAgICAgICAgICAgUmF0aW9uYWwoODcy"
        "Njc3OTk2MiwxMCoqMTApKSwKICAgICgiSUdOSVRJT04gc3FydDItMS8yIiwgICAgICAgc3FydCgy"
        "KS1SYXRpb25hbCgxLDIpLCA0KngqKjIrNCp4LTcsICAgICAgICAgICAgICAgICAgICAgICBSYXRp"
        "b25hbCg5MTQyMTM1NjI0LDEwKioxMCkpLAogICAgKCJLLUZPUk0gICBzcXJ0KDEtZ2FwKSIsICAg"
        "ICBLLCAgICAgICAgICAgICAgICAgICAgIHgqKjQrNSp4KioyLTUsICAgICAgICAgICAgICAgICAg"
        "ICAgIFJhdGlvbmFsKDkyNDE3NjM3MTgsMTAqKjEwKSksCiAgICAoIkNPTlNPTElEIEsrdGF1XjIo"
        "MS1LKSIsICAgIEsrVEFVKioyKigxLUspLCAgICAgICAgeCoqNC02KngqKjMrMjYqeCoqMi0xNip4"
        "LTQsICAgICAgICAgUmF0aW9uYWwoOTUzMTM4NDIwNiwxMCoqMTApKSwKICAgICgiUkVTT05BTkMg"
        "Syt0YXUoMS1LKSIsICAgICAgSytUQVUqKDEtSyksICAgICAgICAgICB4Kio0KzIqeCoqMyszOSp4"
        "KioyLTUyKngrMTEsICAgICAgICBSYXRpb25hbCg5NzEwMzc5NTEyLDEwKioxMCkpLAogICAgKCJV"
        "TklUWSAgICAxIiwgICAgICAgICAgICAgICBSYXRpb25hbCgxKSwgICAgICAgICAgIHgtMSwgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgICAgICAgIFJhdGlvbmFsKDEpKSwKXQpUT0wgPSBSYXRpb25h"
        "bCgxLDEwKio5KTsgcHJldj1Ob25lOyBvcmRlcl9vaz1UcnVlCmZvciBuYW1lLHZhbCxtcF9leHAs"
        "ZG9jIGluIFJPV1M6CiAgICBtcCA9IG1pbnBvbHkodmFsLHgpCiAgICBtcF9vayA9IChleHBhbmQo"
        "bXAtbXBfZXhwKT09MCkKICAgIHBpbiAgID0gYWJzKHZhbC5ldmFsZig0MCktZG9jLmV2YWxmKDQw"
        "KSkgPCBUT0wuZXZhbGYoNDApCiAgICBpZiBwcmV2IGlzIG5vdCBOb25lOiBvcmRlcl9vayAmPSAo"
        "dmFsLmV2YWxmKDQwKSA+IHByZXYpCiAgICBwcmV2ID0gdmFsLmV2YWxmKDQwKQogICAgcHJpbnQo"
        "ZiIgIHtvayhtcF9vayBhbmQgcGluKX0gIHtuYW1lOjwyMn0gbWlucG9seT17c3RyKG1wKTo8Mjh9"
        "IHo9e2Zsb2F0KHZhbCk6LjZmfSIpCnByaW50KGYiICBzdHJpY3QgYXNjZW5kaW5nIG9yZGVyIFBB"
        "UkFET1g8Li4uPFVOSVRZOiB7b2sob3JkZXJfb2spfSIpCgpwcmludCgiPSIqNzYpCnByaW50KCIy"
        "LiBGT1JDRUQgYW5jaG9ycyBvZiB0aGUgcmFkaXVzIGxhdyBhbmQgdGhlIGRlbHRhIikKcHJpbnQo"
        "Ij0iKjc2KQpwcmludChmIiAgcigwKSAgID0gSypzcXJ0KDAvel9jKSAgPSB7c2ltcGxpZnkoSypz"
        "cXJ0KFJhdGlvbmFsKDApL1pDKSl9ICAtPiB7b2soc2ltcGxpZnkoSypzcXJ0KFJhdGlvbmFsKDAp"
        "L1pDKSk9PTApfSIpCnByaW50KGYiICByKHpfYykgPSBLKnNxcnQoel9jL3pfYyk9IHtzaW1wbGlm"
        "eShLKnNxcnQoWkMvWkMpKX0gICg9IEspIC0+IHtvayhzaW1wbGlmeShLKnNxcnQoWkMvWkMpLUsp"
        "PT0wKX0iKQpwcmludChmIiAgel9jID0gc3FydDMvMiA7IG1pbnBvbHkge21pbnBvbHkoWkMseCl9"
        "IC0+IHtvayhtaW5wb2x5KFpDLHgpPT00KngqKjItMyl9IikKcHJpbnQoZiIgIEsgICA9IHNxcnQo"
        "MS1waGleLTQpIDsgbWlucG9seSB7bWlucG9seShLLHgpfSAtPiB7b2sobWlucG9seShLLHgpPT14"
        "Kio0KzUqeCoqMi01KX0iKQpwcmludChmIiAgREVMVEEgPSBwaGleLTIgPSAxIC0gdGF1ID0ge3Np"
        "bXBsaWZ5KERFTFRBKX0gOyBlcXVhbHMgMS10YXUgPyB7b2soc2ltcGxpZnkoREVMVEEtKDEtVEFV"
        "KSk9PTApfSIpCnByaW50KGYiICBtaW5wb2x5KERFTFRBKSA9IHttaW5wb2x5KERFTFRBLHgpfSAt"
        "PiB7b2sobWlucG9seShERUxUQSx4KT09eCoqMi0zKngrMSl9IikKCnByaW50KCI9Iio3NikKcHJp"
        "bnQoIjMuIFRIRSBERUxUQSBBUyBXRUlHSFQvUElUQ0ggICh2YWx1ZSBmb3JjZWQ7IHVzaW5nIGl0"
        "IGFzIHBpdGNoIGlzIGNvbnN0cnVjdGlvbikiKQpwcmludCgiPSIqNzYpCnR1cm5zID0gc2ltcGxp"
        "ZnkoMS9ERUxUQSkKcHJpbnQoZiIgIHBpdGNoID0gREVMVEEgPSBwaGleLTIgb2YgeiBwZXIgdHVy"
        "biA7IHR1cm5zIG92ZXIgeiBpbiBbMCwxXSA9IDEvREVMVEEgPSB7dHVybnN9IikKcHJpbnQoZiIg"
        "IDEvcGhpXi0yID0gcGhpXjIgPSBwaGkrMSA/IHtvayhzaW1wbGlmeSgxL0RFTFRBIC0gKFBISSsx"
        "KSk9PTApfSAgKD0ge2Zsb2F0KFBISSsxKTouNWZ9IHR1cm5zKSIpCmdhID0gc2ltcGxpZnkoMzYw"
        "KkRFTFRBKQpwcmludChmIiAgdHVybi1hcy1nb2xkZW4tYW5nbGU6IDM2MCpwaGleLTIgPSB7Z2F9"
        "IGRlZyA9IHtmbG9hdChnYSk6LjJmfSBkZWcgICBbQ09OU1RSVUNUSU9OXSIpCgpwcmludCgiPSIq"
        "NzYpCnByaW50KCI0LiBTVVBQT1JUSU5HIElERU5USVRJRVMgKGZvcmNlZCwgcmVzaWR1YWwgMCki"
        "KQpwcmludCgiPSIqNzYpCnByaW50KGYiICBMNCA9IHBoaV40ICsgcGhpXi00ID0ge3NpbXBsaWZ5"
        "KFBISSoqNCtQSEkqKi00KX0gPSBMNChMdWNhcykge2x1Y2FzKDQpfSAtPiB7b2soc2ltcGxpZnko"
        "UEhJKio0K1BISSoqLTQtNyk9PTApfSIpCnByaW50KGYiICB0YXVeMiArIHRhdSAtIDEgPSB7c2lt"
        "cGxpZnkoVEFVKioyK1RBVS0xKX0gLT4ge29rKHNpbXBsaWZ5KFRBVSoqMitUQVUtMSk9PTApfSIp"
        "CnByaW50KGYiICBLXjIgLSAoMS1nYXApICAgPSB7c2ltcGxpZnkoSyoqMi0oMS1HQVApKX0gLT4g"
        "e29rKHNpbXBsaWZ5KEsqKjItKDEtR0FQKSk9PTApfSIpCnByaW50KGYiICBzcGFuIGZyYWN0aW9u"
        "czogKENPTlNPTC1LKS8oMS1LKT10YXVeMiAtPiB7b2soc2ltcGxpZnkoKEsrVEFVKioyKigxLUsp"
        "LUspLygxLUspLVRBVSoqMik9PTApfTsgIgogICAgICBmIihSRVNPTi1LKS8oMS1LKT10YXUgLT4g"
        "e29rKHNpbXBsaWZ5KChLK1RBVSooMS1LKS1LKS8oMS1LKS1UQVUpPT0wKX0iKQpwcmludChmIiAg"
        "TDQtNCA9IDMgPSAoc3FydDMpXjIgLT4ge29rKHNpbXBsaWZ5KChzcXJ0KDMpKSoqMi0oNy00KSk9"
        "PTApfSAgW0ZPUkNFRCBJTiBDT05URVhUOiBtZW51IG9wKC00KSBvbiBMNF0iKQoKcHJpbnQoIj0i"
        "Kjc2KQpwcmludCgiNS4gUkFESVVTIEFUIEVBQ0ggTEFORE1BUksgIChyPUsqc3FydCh6L3pfYykg"
        "Zm9yIHo8PXpfYywgZWxzZSBmbGF0IEspIikKcHJpbnQoIj0iKjc2KQpmb3IgbmFtZSx2YWwsXyxf"
        "IGluIFJPV1M6CiAgICB6ID0gdmFsCiAgICByID0gSypzcXJ0KHovWkMpIGlmICh6LmV2YWxmKDQw"
        "KSA8PSBaQy5ldmFsZig0MCkpIGVsc2UgSwogICAgcmVnaW9uID0gImhvcm4iIGlmIHouZXZhbGYo"
        "NDApIDw9IFpDLmV2YWxmKDQwKSBlbHNlICJjeWxpbmRlciIKICAgIHByaW50KGYiICB6PXtmbG9h"
        "dCh6KTouNGZ9ICByPXtmbG9hdChyKTouNGZ9ICBbe3JlZ2lvbn1dICB7bmFtZX0iKQoKcHJpbnQo"
        "Ij0iKjc2KQpwcmludCgiR1JBRElORyAvIExPQUQtQkVBUklORyIpCnByaW50KCI9Iio3NikKcHJp"
        "bnQoIiAgRk9SQ0VEICAgICAgIDogbmluZSB6LWxhbmRtYXJrcyAodGF1Li51bml0eSkgKyBLICsg"
        "REVMVEEgKG1pbnBvbHksIHJlc2lkdWFsIDApLCIpCnByaW50KCIgICAgICAgICAgICAgICAgIHN0"
        "cmljdCBvcmRlciwgaWRlbnRpdGllcywgcigwKT0wLCByKHpfYyk9Sy4iKQpwcmludCgiICBDT05T"
        "VFJVQ1RJT04gOiByYWRpdXMgZm9ybSByKHopPUsqc3FydCh6L3pfYyk7IHBpdGNoPURFTFRBOyBn"
        "b2xkZW4tYW5nbGUgdHVybjsiKQpwcmludCgiICAgICAgICAgICAgICAgICBhbGwgdGhyZXNob2xk"
        "IE5BTUVTOyAnd2VpZ2h0Jy8nZWxldmF0aW9uJy8nbGVucycgcmVhZGluZy4iKQpwcmludCgiICBG"
        "T1JDRUQgSU4gQ09OVEVYVCA6IHpfYyA9IHNxcnQzLzIgW21lbnUgb3AoLTQpXSwgaWduID0gc3Fy"
        "dDItMS8yIFttZW51IG9wKCsxKV0uIikKcHJpbnQoIiAgICAgICAgICAgICAgICAgRGlzam9pbnQg"
        "YXhpcyBidXQgbWVudS1yZWFjaGFibGUgZnJvbSBMNCB3aXRoIHJlc2lkdWFsIDAuIikKcHJpbnQo"
        "IiAgTE9BRC1CRUFSSU5HIDogTk8uIE5vdGhpbmcgaW4gc2VjdGlvbnMgMSwyLDQgcmVmZXJlbmNl"
        "cyB0aGUgaGVsaXggZm9ybS4gU3RyaXAgdGhlIikKcHJpbnQoIiAgICAgICAgICAgICAgICAgc2Nh"
        "ZmZvbGQgYW5kIGV2ZXJ5IGZvcmNlZCB2YWx1ZS9pZGVudGl0eSBzdGFuZHMgdW5jaGFuZ2VkLiIp"
        "CgoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIGltcG9ydCBzeXMgYXMgX3N5cwogICAg"
        "aWYgX0ZBSUxTOgogICAgICAgIHByaW50KGYiRkFJTCAge2xlbihfRkFJTFMpfSBjaGVjayhzKSBk"
        "aWQgbm90IHBhc3MiKQogICAgX3N5cy5leGl0KDEgaWYgX0ZBSUxTIGVsc2UgMCkK"
    ),
    "zfp_trifurcation.py": (
        "60ffdc7e5ce1e45fb5b2dc0574edf057ba12aea828ade81b5d719e696b67c738",
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJUcmlmdXJjYXRpb24gYW5kIGl0cyBtdWx0aS1kaW1lbnNpb25hbCBkeW5hbWlj"
        "cywgYXMgYSBjaGFpbi1vZi1kZXJpdmF0aW9uIHN0dWR5LgoKVGhlc2lzIHVuZGVyIHRlc3Q6IHRoZSBGT1JDRUQgc3RydWN0"
        "dXJhbCBvdXRwdXRzIChob3cgbWFueSBicmFuY2hlcywgdGhlCmFtcGxpdHVkZSBleHBvbmVudCwgdGhlIG51bWJlciBmaWVs"
        "ZCB0aGUgYnJhbmNoZXMgbGl2ZSBpbikgYXJlIGRldGVybWluZWQgYnkKdGhlICpjaGFpbiogLS0gdGhlIGdlcm0gZGVncmVl"
        "LCB0aGUgc3ltbWV0cnkgZ3JvdXAsIHRoZSBkaW1lbnNpb24uIFRoZSBjaGFpbiBpcwp0aGUgc2VsZWN0aW9uLWxheWVyIGlu"
        "cHV0OyBldmVyeXRoaW5nIGJlbG93IGl0IGlzIGZvcmNlZC4gQ2hhbmdlIGEgbGluaywgYW5kCnRoZSBmb3JjZWQgb3V0cHV0"
        "IGNoYW5nZXMgaW4gYSBzcGVjaWZpZWQsIGNoZWNrYWJsZSB3YXkuCgpUd28gcmVhbGl6YXRpb25zIG9mICIxIC0+IDMiOgog"
        "IChBKSAxRCwgcmVmbGVjdGlvbiAoWjIpIHN5bW1ldHJ5OiB0aGUgc3ltbWV0cmljIGN1c3AgeF4zICsgYSB4ICAtLSBhIHBp"
        "dGNoZm9yay4KICAoQikgbXVsdGktRCwgdGhyZWUtZm9sZCAoRDMvWjMpIHN5bW1ldHJ5OiB6YmFyXjIgIC0tIGEgdHJhbnNj"
        "cml0aWNhbCB0cmlmb3JrLgpUaGV5IHByb2R1Y2UgdGhyZWUgYnJhbmNoZXMgYnkgKmRpZmZlcmVudCogbWVjaGFuaXNtcywg"
        "d2l0aCAqZGlmZmVyZW50KiBmb3JjZWQKZXhwb25lbnRzLCBpbiAqZGlmZmVyZW50KiBmaWVsZHMuICBCb3RoIGFyZSB2ZXJp"
        "ZmllZCBoZXJlLCByZXNpZHVhbCAwLgoKRGVwczogc3ltcHkuICBSdW46IHB5dGhvbjMgemZwX3RyaWZ1cmNhdGlvbi5weQoi"
        "IiIKaW1wb3J0IHN5bXB5IGFzIHNwCmZyb20gc3ltcHkgaW1wb3J0IChJLCBJbnRlZ2VyLCBNYXRyaXgsIFBvbHksIFJhdGlv"
        "bmFsLCBjb25qdWdhdGUsIGRpZmYsCiAgICAgICAgICAgICAgICAgICBkaXNjcmltaW5hbnQsIGV4cCwgZXhwYW5kLCBmYWN0"
        "b3IsIG1pbnBvbHksIHBpLCBzaW1wbGlmeSwKICAgICAgICAgICAgICAgICAgIHNvbHZlLCBzcXJ0LCBzeW1ib2xzKQoKeCwg"
        "YSwgYiwgbGFtLCB1LCB2ID0gc3ltYm9scygieCBhIGIgbGFtYmRhIHUgdiIsIHJlYWw9VHJ1ZSkKX0ZBSUxTID0gW10KZGVm"
        "IG9rKGMpOiAgICAgICAgICAgICAgICAgICAgICAgICAgIyByZWNvcmRzIGZhaWx1cmVzIHNvIGV4aXQgY29kZSBpcyBtZWFu"
        "aW5nZnVsCiAgICBfciA9IGJvb2woYykKICAgIGlmIG5vdCBfcjoKICAgICAgICBfRkFJTFMuYXBwZW5kKDEpCiAgICByZXR1"
        "cm4gIlBBU1MiIGlmIF9yIGVsc2UgIkZBSUwiCnByaW50KGYic3ltcHkge3NwLl9fdmVyc2lvbl9ffSIpCgpwcmludCgiPSIq"
        "NzQpCnByaW50KCJBLiAxRCBUUklGVVJDQVRJT04gLS0gc3ltbWV0cmljIGN1c3AgIFYgPSB4XjQvNCArIGEgeF4yLzIsICBW"
        "JyA9IHheMyArIGEgeCIpCnByaW50KCI9Iio3NCkKVnAgPSB4KiozICsgYSp4ICAgICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgICAgICAjID0geCAoeF4yICsgYSkKcm9vdHMgPSBbSW50ZWdlcigwKSwgc3FydCgtYSksIC1zcXJ0KC1hKV0KcmVzX29r"
        "ID0gYWxsKHNpbXBsaWZ5KFZwLnN1YnMoeCwgcikpID09IDAgZm9yIHIgaW4gcm9vdHMpCnByaW50KGYiICBmYWN0b3IoVicp"
        "ICAgICAgICA9IHtmYWN0b3IoVnApfSIpCnByaW50KGYiICB0aHJlZSBicmFuY2hlcyB7ezAsICtzcXJ0KC1hKSwgLXNxcnQo"
        "LWEpfX0gYXJlIHJvb3RzIChyZXNpZHVhbCAwKToge29rKHJlc19vayl9IikKZGlzYyA9IGRpc2NyaW1pbmFudChQb2x5KFZw"
        "LCB4KSwgeCkKcHJpbnQoZiIgIGRpc2NyaW1pbmFudChWJykgID0ge2V4cGFuZChkaXNjKX0gICAoZXhwZWN0IC00YV4zKSAt"
        "PiB7b2soZXhwYW5kKGRpc2MrNCphKiozKT09MCl9IikKcHJpbnQoZiIgICAgPT4gZGlzYyA9IDAgb25seSBhdCBhID0gMCA6"
        "IHRoZSBUUklGVVJDQVRJT04gUE9JTlQgKHRyaXBsZSByb290IGF0IHg9MCkiKQpwcmludChmIiAgICA9PiBhIDwgMCBnaXZl"
        "cyBkaXNjID0gLTRhXjMgPiAwIDogdGhyZWUgZGlzdGluY3QgcmVhbCBicmFuY2hlcyIpCiMgc3RhYmlsaXR5IHZpYSBIZXNz"
        "aWFuIFYnJyA9IDN4XjIgKyBhClZwcCA9IGRpZmYoeCoqNC80ICsgYSp4KioyLzIsIHgsIDIpCmgwICA9IHNpbXBsaWZ5KFZw"
        "cC5zdWJzKHgsIDApKSAgICAgICAgICAgICAgICAgICAgIyBhCmhwbSA9IHNpbXBsaWZ5KFZwcC5zdWJzKHgsIHNxcnQoLWEp"
        "KSkgICAgICAgICAgICAgIyAtMmEKcHJpbnQoZiIgIEhlc3NpYW4gYXQgeD0wOiAgICAgICAgVicnID0ge2gwfSAgICAodHJp"
        "dmlhbCBicmFuY2g7IHN0YWJsZSBhPjAsIHVuc3RhYmxlIGE8MCkiKQpwcmludChmIiAgSGVzc2lhbiBhdCArLy1zcXJ0KC1h"
        "KTogVicnID0ge2hwbX0gIChicm9rZW4gcGFpcjsgc3RhYmxlIGZvciBhPDApIC0+IGV4Y2hhbmdlIGF0IGE9MCIpCnByaW50"
        "KGYiICBhbXBsaXR1ZGUgc2NhbGluZzogfHh8ID0gfGF8XigxLzIpICAtPiBGT1JDRUQgZXhwb25lbnQgMS8yIChwaXRjaGZv"
        "cmspIikKCnByaW50KCI9Iio3NCkKcHJpbnQoIkIuIFRIRSBDSEFJTiAtLSBldmVuIGdlcm1zIHheKDJtKSwgc3ltbWV0cmlj"
        "IHNlY3Rpb24sIEZPUkNFRCBicmFuY2ggY291bnQiKQpwcmludCgiPSIqNzQpCnByaW50KCIgIFYnID0geCAqIChkZWdyZWUt"
        "KDJtLTIpIGV2ZW4gcG9seSkgID0+ICB1cCB0byAybS0xIHJlYWwgYnJhbmNoZXMgKG9kZCwgKzIgcGVyIGxpbmspIikKcmVw"
        "cyA9IHsKICAgICJ4XjQgIGN1c3AgICAgIChtPTIpIjogKHgqKjMgLSB4LCAgICAgICAgICAgICAgICAgICAgICAgWzAsIDEs"
        "IC0xXSksCiAgICAieF42ICBidXR0ZXJmbHkobT0zKSI6ICh4Kio1IC0gNSp4KiozICsgNCp4LCAgICAgICAgICAgIFswLCAx"
        "LCAtMSwgMiwgLTJdKSwKICAgICJ4XjggICAgICAgICAgIChtPTQpIjogKHgqKjcgLSAxNCp4Kio1ICsgNDkqeCoqMyAtIDM2"
        "KngsIFswLCAxLCAtMSwgMiwgLTIsIDMsIC0zXSksCn0KZm9yIG5hbWUsIChwb2x5LCBydHMpIGluIHJlcHMuaXRlbXMoKToK"
        "ICAgIHJlc19vayA9IGFsbChzaW1wbGlmeShwb2x5LnN1YnMoeCwgcikpID09IDAgZm9yIHIgaW4gcnRzKQogICAgbl9yZWFs"
        "ID0gbGVuKFBvbHkocG9seSwgeCkucmVhbF9yb290cygpKQogICAgcHJpbnQoZiIgIHtvayhyZXNfb2sgYW5kIG5fcmVhbCA9"
        "PSBsZW4ocnRzKSl9ICB7bmFtZX06IGZhY3Rvcj17ZmFjdG9yKHBvbHkpfSAgYnJhbmNoZXM9e25fcmVhbH0iKQpwcmludCgi"
        "ICAzIC0+IDUgLT4gNyA6IHJhaXNpbmcgdGhlIGdlcm0gZGVncmVlICh0aGUgY2hhaW4pIGZvcmNlcyArMiBicmFuY2hlcyBl"
        "YWNoIHN0ZXAuIikKCnByaW50KCI9Iio3NCkKcHJpbnQoIkMuIE1VTFRJLUQgVFJJRlVSQ0FUSU9OIC0tIEQzL1ozIGVxdWl2"
        "YXJpYW50ICB6ZG90ID0gbGFtIHogKyB6YmFyXjIiKQpwcmludCgiPSIqNzQpCncgPSBleHAoMipJKnBpLzMpICAgICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgICAgICMgcHJpbWl0aXZlIGN1YmUgcm9vdCwgPSB6ZXRhXzZeMgplcXVpdmFyID0gc2lt"
        "cGxpZnkoY29uanVnYXRlKHcpKioyIC0gdykgICAgICAgICAgICAjIHpiYXJeMiBlcXVpdmFyaWFudCA8PT4gY29uaih3KV4y"
        "ID0gdwpwcmludChmIiAgWjMtZXF1aXZhcmlhbmNlIG9mIHpiYXJeMjogIGNvbmoodyleMiAtIHcgPSB7ZXF1aXZhcn0gIC0+"
        "IHtvayhlcXVpdmFyID09IDApfSIpCiMgcmVhbCBjb29yZGluYXRlcyB6PXUraXYgOiAgemJhcl4yID0gKHUtaXYpXjIgPSAo"
        "dV4yLXZeMikgLSAyaSB1IHYKZjEgPSBsYW0qdSArIHUqKjIgLSB2KioyCmYyID0gbGFtKnYgLSAyKnUqdgpzb2xzID0gc29s"
        "dmUoW2YxLCBmMl0sIFt1LCB2XSwgZGljdD1UcnVlKQpub250cml2aWFsID0gW3MgZm9yIHMgaW4gc29scyBpZiBub3QgKHNb"
        "dV0gPT0gMCBhbmQgc1t2XSA9PSAwKV0KcHJpbnQoZiIgIHN0ZWFkeSBzdGF0ZXMgc29sdmVkOiB7bGVuKHNvbHMpfSB0b3Rh"
        "bCwge2xlbihub250cml2aWFsKX0gbm9udHJpdmlhbCBicmFuY2hlcyIpCmFsbF9yZXMsIGFsbF9yMiA9IFRydWUsIFRydWUK"
        "Zm9yIHMgaW4gc29sczoKICAgIHIxID0gc2ltcGxpZnkoZjEuc3VicyhzKSk7IHIyID0gc2ltcGxpZnkoZjIuc3VicyhzKSk7"
        "IGFsbF9yZXMgJj0gKHIxID09IDAgYW5kIHIyID09IDApCmZvciBzIGluIG5vbnRyaXZpYWw6CiAgICByMnZhbCA9IHNpbXBs"
        "aWZ5KHNbdV0qKjIgKyBzW3ZdKioyKTsgYWxsX3IyICY9IChzaW1wbGlmeShyMnZhbCAtIGxhbSoqMikgPT0gMCkKcHJpbnQo"
        "ZiIgIGV2ZXJ5IGJyYW5jaCBzYXRpc2ZpZXMgYm90aCBmaWVsZCBlcXVhdGlvbnMgKHJlc2lkdWFsIDApOiB7b2soYWxsX3Jl"
        "cyl9IikKcHJpbnQoZiIgIGV2ZXJ5IG5vbnRyaXZpYWwgYnJhbmNoIGhhcyByXjIgPSBsYW1iZGFeMiAgPT4gciA9IHxsYW1i"
        "ZGF8OiB7b2soYWxsX3IyKX0iKQpwcmludChmIiAgYW1wbGl0dWRlIHNjYWxpbmc6IHIgPSB8bGFtYmRhfF4xICAtPiBGT1JD"
        "RUQgZXhwb25lbnQgMSAodHJhbnNjcml0aWNhbCksIE5PVCAxLzIiKQojIHRoZSB0aHJlZSBicmFuY2ggZGlyZWN0aW9ucyBh"
        "bmQgdGhlIHNxcnQzLzIgPSBaX0Mgc2lnbmF0dXJlCnByaW50KGYiICBicmFuY2hlcyAodSx2KToiKQpmb3IgcyBpbiBzb2xz"
        "OgogICAgcHJpbnQoZiIgICAgICAoe3NbdV19LCB7c1t2XX0pIikKemMgPSBzcXJ0KDMpLzIKcHJpbnQoZiIgIGJyYW5jaCBo"
        "ZWlnaHQgYXQgfGxhbWJkYXw9MSBpcyBzcXJ0KDMpLzIgPSBJbSh6ZXRhXzYpID0gWl9DIDsgIgogICAgICBmIm1pbnBvbHkg"
        "PSB7bWlucG9seSh6YywgeCl9IC0+IHtvayhtaW5wb2x5KHpjLCB4KSA9PSA0KngqKjIgLSAzKX0iKQojIEphY29iaWFuIC8g"
        "c3RhYmlsaXR5IGF0IHRoZSB0aGV0YT0wIGJyYW5jaCAodSx2KT0oLWxhbSwwKQpKID0gTWF0cml4KFtbZGlmZihmMSwgdSks"
        "IGRpZmYoZjEsIHYpXSwgW2RpZmYoZjIsIHUpLCBkaWZmKGYyLCB2KV1dKQpKMCA9IEouc3Vicyh7dTogLWxhbSwgdjogMH0p"
        "CmV2ID0gc29ydGVkKEowLmVpZ2VudmFscygpLmtleXMoKSwga2V5PWxhbWJkYSBlOiBzdHIoZSkpCnByaW50KGYiICBKYWNv"
        "YmlhbiBlaWdlbnZhbHVlcyBhdCB0aGV0YT0wIGJyYW5jaDoge2V2fSAgKGV4cGVjdCAtbGFtYmRhLCAzKmxhbWJkYSkiKQpw"
        "cmludChmIiAgICAtPiBvcHBvc2l0ZSBzaWducyA9PiBTQURETEU7IHRoZSBxdWFkcmF0aWMgRDMgdHJpZm9yayBpcyB1bnN0"
        "YWJsZSAiCiAgICAgIGYiKGN1YmljIHx6fF4yIHogdGVybXMgbmVlZGVkIHRvIHN0YWJpbGl6ZSkuIikKCnByaW50KCI9Iio3"
        "NCkKcHJpbnQoIkQuIEZJRUxEIERJU0NJUExJTkUgJiBGSVJFV0FMTCAtLSB0aGUgY2hhaW4gYWxzbyBzZWxlY3RzIHRoZSBO"
        "VU1CRVIgRklFTEQiKQpwcmludCgiPSIqNzQpCnByaW50KGYiICBEMyBicmFuY2ggZ2VvbWV0cnkgbGl2ZXMgaW4gUShzcXJ0"
        "Myk6IG1pbnBvbHkoc3FydDMvMikgPSB7bWlucG9seShzcXJ0KDMpLzIseCl9IikKbXBfc3VtID0gbWlucG9seShzcXJ0KDUp"
        "K3NxcnQoMyksIHgpCnByaW50KGYiICBwaGktY3VzcG9pZCB3b3JsZCBpcyBRKHNxcnQ1KTsgbWlucG9seShzcXJ0NStzcXJ0"
        "MykgPSB7bXBfc3VtfSIpCnByaW50KGYiICAgIGRlZ3JlZSB7c3AuZGVncmVlKG1wX3N1bSx4KX0gPSAyKjIgPT4gUShzcXJ0"
        "NSkg4oipIFEoc3FydDMpID0gUSA6IGZpcmV3YWxsIGhvbGRzIHtvayhzcC5kZWdyZWUobXBfc3VtLHgpPT00KX0iKQpwcmlu"
        "dChmIiAgPT4gdGhlIFNBTUUgd29yZCAndHJpZnVyY2F0aW9uJyBmb3JjZXMgb3V0cHV0cyBpbiBESUZGRVJFTlQgZmllbGRz"
        "IGRlcGVuZGluZyIpCnByaW50KGYiICAgICBvbiB0aGUgc3ltbWV0cnkgY2hhaW4gKFoyIGN1c3BvaWQgLT4gUShzcXJ0KC1h"
        "KSk7IEQzIC0+IFEoc3FydDMpKS4iKQpwcmludChmIiAgQ09JTkNJREVOQ0UgZmxhZyAoTk9UIGEgZm9yY2luZyk6IChzcXJ0"
        "MyleMiA9IHtzcXJ0KDMpKioyfSA9IHRoZSBEMyBicmFuY2ggY291bnQgMzsiKQpwcmludChmIiAgICAgdGhpcyBpcyBub3Qg"
        "dGhlIGVhcmxpZXIgaW50ZWdlciAzID0gTDQtNCwgYW5kIHRoZSB0d28gbXVzdCBub3QgYmUgY29uZmxhdGVkLiIpCgpwcmlu"
        "dCgiPSIqNzQpCnByaW50KCJDSEFJTiAtPiBGT1JDRUQgT1VUUFVUICAoY2hhbmdlIGEgbGluaywgdGhlIG91dHB1dCBjaGFu"
        "Z2VzLCBhbGwgZm9yY2VkKSIpCnByaW50KCI9Iio3NCkKcm93cyA9IFsKICAgICgiWjIgc3ltbWV0cmljIGN1c3AgeF40ICgx"
        "RCkiLCAgICAgIjMiLCAgICAgICAgIjEvMiIsICAiUShzcXJ0KC1hKSkiKSwKICAgICgiWjIgc3ltbWV0cmljIGJ1dHRlcmZs"
        "eSB4XjYgKDFEKSIsIjUiLCAgICAgICAgIjEvMiIsICAiUShyYWRpY2FscyBvZiBhLGIpIiksCiAgICAoIloyIGV2ZW4gZ2Vy"
        "bSB4XigybSkgKDFEKSIsICAgICAgICIybS0xIiwgICAgICIxLzIiLCAgImZpZWxkIG9mIHRoZSByYWRpY2FscyIpLAogICAg"
        "KCJEMyBlcXVpdmFyaWFudCB6YmFyXjIgKDJEKSIsICAgICAiMyIsICAgICAgICAiMSIsICAgICJRKHNxcnQzKSIpLApdCnBy"
        "aW50KGYiICB7J2NoYWluIGxpbmsnOjwzNH17J2JyYW5jaGVzJzo8MTB9eydhbXAgZXhwJzo8OX17J2ZpZWxkJ30iKQpmb3Ig"
        "ciBpbiByb3dzOgogICAgcHJpbnQoZiIgIHtyWzBdOjwzNH17clsxXTo8MTB9e3JbMl06PDl9e3JbM119IikKCnByaW50KCI9"
        "Iio3NCkKcHJpbnQoIkdSQURJTkciKQpwcmludCgiPSIqNzQpCnByaW50KCIgIEZPUkNFRCAgICAgICA6IGJyYW5jaCBjb3Vu"
        "dHMsIGRpc2NyaW1pbmFudHMsIHRyaWZ1cmNhdGlvbiBwb2ludCBhPTAsIikKcHJpbnQoIiAgICAgICAgICAgICAgICAgRDMg"
        "ZXF1aXZhcmlhbmNlICsgdGhyZWUgMTIwLWRlZyBicmFuY2hlcywgcj18bGFtYmRhfCwiKQpwcmludCgiICAgICAgICAgICAg"
        "ICAgICBzcXJ0My8yID0gWl9DIGlkZW50aXR5LCBmaXJld2FsbCAtLSBhbGwgcmVzaWR1YWwgMCBhYm92ZS4iKQpwcmludCgi"
        "ICBDT05TVFJVQ1RJT04gOiBhIHNwZWNpZmljIChhLGIsLi4pIHJlYWxpemluZyBhIGdpdmVuIGNvdW50IGlzIGlsbHVzdHJh"
        "dGl2ZTsiKQpwcmludCgiICAgICAgICAgICAgICAgICB0aGUgQ09VTlQgaXMgZm9yY2VkIGJ5IHRoZSBnZXJtLCB0aGUgaW5z"
        "dGFuY2UgaXMgY2hvc2VuLiIpCnByaW50KCIgIE9QRU4vQVNTVU1QVCA6IHRoYXQgYSBwaHlzaWNhbCBEZWx0YUhfViByZWFs"
        "aXplcyBhIHRyaWZ1cmNhdGlvbiBhdCBhIGZvcmNlZCIpCnByaW50KCIgICAgICAgICAgICAgICAgIGNvbnN0YW50IG5lZWRz"
        "IHRoZSBvcGVyYXRvcittZXRyaWMuIHNxcnQzLzIgaGVyZSBpcyBhIHJlYWwiKQpwcmludCgiICAgICAgICAgICAgICAgICBz"
        "dHJ1Y3R1cmFsIGlkZW50aXR5IGJ1dCBkb2VzIE5PVCBicmlkZ2UgdG8gdGhlIHBoaS1mYW1pbHkuIikKCgppZiBfX25hbWVf"
        "XyA9PSAiX19tYWluX18iOgogICAgaW1wb3J0IHN5cyBhcyBfc3lzCiAgICBpZiBfRkFJTFM6CiAgICAgICAgcHJpbnQoZiJG"
        "QUlMICB7bGVuKF9GQUlMUyl9IGNoZWNrKHMpIGRpZCBub3QgcGFzcyIpCiAgICBfc3lzLmV4aXQoMSBpZiBfRkFJTFMgZWxz"
        "ZSAwKQo="
    ),
    "zfp_hex_closure.py": (
        "2cfe41a2b819635ae1a222c58bbe7d22203aad36654d645fbaddae58f950aece",
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJIZXhhZ29uYWwgKEQ2KSBjbG9zdXJlOiBpcyB0aGUgaGV4YWdvbmFsIGxhdHRp"
        "Y2UgY2FzZSBhIHNlbGYtdmFsaWRhdGluZwpjbG9zdXJlIG9mIHRoZSBzdHJ1Y3R1cmFsIHJlbGF0aW9uc2hpcCBaX0MgPSBz"
        "cXJ0My8yID0gSW0oemV0YV82KT8KCkNsYWltIHVuZGVyIHRlc3QgKGJvdW5kZWQpOiBZRVMgZm9yIHRoZSB6ZXRhXzYgLyBj"
        "cnlzdGFsbG9ncmFwaGljIHRvd2VyLgogIC0gVGhlIGNyeXN0YWxsb2dyYXBoaWMgY2hhaW4gVEVSTUlOQVRFUyBhdCBvcmRl"
        "ciA2IChubyBoaWdoZXIgbGF0dGljZSBzeW1tZXRyeSkuCiAgLSBBdCB0aGF0IHRlcm1pbnVzLCB0aHJlZSBpbmRlcGVuZGVu"
        "dCByb3V0ZXMgLS0gZ2VvbWV0cnksIGFsZ2VicmEsIGR5bmFtaWNzIC0tCiAgICByZXR1cm4gdGhlIFNBTUUgY29uc3RhbnQg"
        "Wl9DLCBtaW5wb2x5IDR4XjItMy4gVGhhdCB0cmlwbGUgYWdyZWVtZW50IGlzIHRoZQogICAgY29ycHVzICdmb3JjZWQnIHN0"
        "YW5kYXJkICh0d28rIGluZGVwZW5kZW50IHdheXMsIHJlc2lkdWFsIDApIC0+IHNlbGYtdmFsaWRhdGluZy4KICAtIFRoZSBj"
        "bG9zdXJlIGlzIG9mIE9ORSB0b3dlci4gVGhlIG9ic3RydWN0aW9uIHRoYXQgZm9yYmlkcyA1LWZvbGQgKGFuZCB0aHVzCiAg"
        "ICBleGNsdWRlcyB0aGUgcGhpLXRvd2VyIGZyb20gYW55IGxhdHRpY2UpIGlzIDJjb3M3MiA9IHRhdSA9IHBoaV4tMSBpdHNl"
        "bGYuCiAgICBTbyB0aGUgZmlyZXdhbGwgUShzcXJ0NSkg4oipIFEoc3FydDMpID0gUSBpcyBlbmZvcmNlZCBnZW9tZXRyaWNh"
        "bGx5LCBub3QganVzdAogICAgYWxnZWJyYWljYWxseS4gVGhlIHdob2xlIGFyY2hpdGVjdHVyZSBkb2VzIE5PVCBjbG9zZSBp"
        "bnRvIG9uZSBzdHJ1Y3R1cmU7IGl0CiAgICBjbG9zZXMgaW50byB0d28gZGlzam9pbnQgc2VsZi12YWxpZGF0aW5nIHRvd2Vy"
        "cyBzaGFyaW5nIG9ubHkgUS4KCkRlcHM6IHN5bXB5LiAgUnVuOiBweXRob24zIHpmcF9oZXhfY2xvc3VyZS5weQoiIiIKaW1w"
        "b3J0IHN5bXB5IGFzIHNwCmZyb20gc3ltcHkgaW1wb3J0IChJLCBjb3MsIGV4cCwgZXhwYW5kLCBpbSwgbWlucG9seSwgcGks"
        "IHNpbXBsaWZ5LCBzcXJ0LCBzeW1ib2xzKQoKeCA9IHN5bWJvbHMoIngiKQpfRkFJTFMgPSBbXQpkZWYgb2soYyk6ICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAjIHJlY29yZHMgZmFpbHVyZXMgc28gZXhpdCBjb2RlIGlzIG1lYW5pbmdmdWwKICAgIF9y"
        "ID0gYm9vbChjKQogICAgaWYgbm90IF9yOgogICAgICAgIF9GQUlMUy5hcHBlbmQoMSkKICAgIHJldHVybiAiUEFTUyIgaWYg"
        "X3IgZWxzZSAiRkFJTCIKUEhJID0gKDEgKyBzcXJ0KDUpKSAvIDIKcHJpbnQoZiJzeW1weSB7c3AuX192ZXJzaW9uX199IikK"
        "CnByaW50KCI9Iio3NCkKcHJpbnQoIjEuIENSWVNUQUxMT0dSQVBISUMgUkVTVFJJQ1RJT04gLS0gdGhlIGNoYWluIHRlcm1p"
        "bmF0ZXMgYXQgb3JkZXIgNiIpCnByaW50KCI9Iio3NCkKcHJpbnQoIiAgQSBsYXR0aWNlIHJvdGF0aW9uIGJ5IDJwaS9uIG5l"
        "ZWRzIGludGVnZXIgdHJhY2U6IDJjb3MoMnBpL24pIGluIFouIikKYWxsb3dlZCA9IFtdCmZvciBuIGluIHJhbmdlKDEsIDkp"
        "OgogICAgdCA9IHNwLm5zaW1wbGlmeSgyKmNvcygyKnBpL24pKQogICAgaXNpbnQgPSB0LmlzX2ludGVnZXIKICAgIGlmIGlz"
        "aW50OiBhbGxvd2VkLmFwcGVuZChuKQogICAgcHJpbnQoZiIgICAgbj17bn06IDJjb3MoMnBpL24pID0ge3N0cih0KTo8MTh9"
        "IGxhdHRpY2UtY29tcGF0aWJsZT8geyd5ZXMnIGlmIGlzaW50IGVsc2UgJ25vJ30iKQpwcmludChmIiAgPT4gY3J5c3RhbGxv"
        "Z3JhcGhpYyBvcmRlcnMgPSB7YWxsb3dlZH0gIChleHBlY3QgWzEsMiwzLDQsNl0pIC0+ICIKICAgICAgZiJ7b2soYWxsb3dl"
        "ZD09WzEsMiwzLDQsNl0pfSIpCiMgdGhlIG49NSBvYnN0cnVjdGlvbiBpcyBleGFjdGx5IHRoZSBnb2xkZW4gY29uc3RhbnQK"
        "dDUgPSBzaW1wbGlmeSgyKmNvcygyKnBpLzUpKQpwcmludChmIiAgbj01IG9ic3RydWN0aW9uOiAyY29zKDcyZGVnKSA9IHt0"
        "NX0gPSBwaGleLTEgPSB0YXUgOyAiCiAgICAgIGYibWlucG9seSA9IHttaW5wb2x5KHQ1LHgpfSAtPiB7b2sobWlucG9seSh0"
        "NSx4KT09eCoqMit4LTEpfSIpCnByaW50KGYiICAgIHRhdSBpcyBJUlJBVElPTkFMIC0+IDUtZm9sZCBmb3JiaWRkZW4gLT4g"
        "dGhlIHBoaS10b3dlciBpcyBub24tY3J5c3RhbGxvZ3JhcGhpYy4iKQoKcHJpbnQoIj0iKjc0KQpwcmludCgiMi4gT1JERVIt"
        "NiBHRU5FUkFUT1IgLS0gemV0YV82IGFuZCBpdHMgcmVhbCBzaWduYXR1cmUgWl9DIikKcHJpbnQoIj0iKjc0KQp6NiA9IGV4"
        "cChJKnBpLzMpICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIHpldGFfNiA9IGVee2kgcGkvM30sIG9yZGVy"
        "IDYKbXA2ID0gbWlucG9seSh6NiwgeCkKcHJpbnQoZiIgIHpldGFfNiA9IGVeKGkgcGkvMyk7IG1pbnBvbHkgPSB7bXA2fSAg"
        "KGN5Y2xvdG9taWMgUGhpXzYgPSB4XjIteCsxKSAtPiAiCiAgICAgIGYie29rKG1wNj09eCoqMi14KzEpfSIpCnpjID0gc3Fy"
        "dCgzKS8yCnByaW50KGYiICBaX0MgPSBzcXJ0My8yIDsgbWlucG9seSA9IHttaW5wb2x5KHpjLHgpfSAtPiB7b2sobWlucG9s"
        "eSh6Yyx4KT09NCp4KioyLTMpfSIpCgpwcmludCgiPSIqNzQpCnByaW50KCIzLiBTRUxGLVZBTElEQVRJT04gLS0gdGhyZWUg"
        "aW5kZXBlbmRlbnQgcm91dGVzIHJldHVybiB0aGUgU0FNRSBaX0MiKQpwcmludCgiPSIqNzQpCnJvdXRlX2dlb20gPSBzaW1w"
        "bGlmeShzcC5zaW4ocGkvMykpICAgICAgICAgICAgICAgICMgZ2VvbWV0cnk6IHNpbiA2MApyb3V0ZV9hbGcgID0gc2ltcGxp"
        "ZnkoaW0oejYpKSAgICAgICAgICAgICAgICAgICAgICAjIGFsZ2VicmEgOiBJbSh6ZXRhXzYpCiMgZHluYW1pY3M6IGltYWdp"
        "bmFyeSBwYXJ0cyBvZiB0aGUgdGhyZWUgdHJpZnVyY2F0aW9uIG1vZGVzIChjdWJlIHJvb3RzIG9mIHVuaXR5KQptb2RlcyA9"
        "IFtleHAoMipJKnBpKmsvMykgZm9yIGsgaW4gcmFuZ2UoMyldCnJvdXRlX2R5biAgPSBzaW1wbGlmeShpbShtb2Rlc1sxXSkp"
        "ICAgICAgICAgICAgICAgICMgbW9kZSBhdCAxMjBkZWcKcHJpbnQoZiIgIGdlb21ldHJ5ICBzaW4oNjApICAgICAgPSB7cm91"
        "dGVfZ2VvbX0iKQpwcmludChmIiAgYWxnZWJyYSAgIEltKHpldGFfNikgICA9IHtyb3V0ZV9hbGd9IikKcHJpbnQoZiIgIGR5"
        "bmFtaWNzICBJbShtb2RlQDEyMCkgPSB7cm91dGVfZHlufSIpCmFncmVlID0gKHNpbXBsaWZ5KHJvdXRlX2dlb20temMpPT0w"
        "IGFuZCBzaW1wbGlmeShyb3V0ZV9hbGctemMpPT0wIGFuZCBzaW1wbGlmeShyb3V0ZV9keW4temMpPT0wKQpwcmludChmIiAg"
        "YWxsIHRocmVlIGVxdWFsIFpfQyA9IHNxcnQzLzIgKHJlc2lkdWFsIDApOiB7b2soYWdyZWUpfSIpCnByaW50KGYiICA9PiB0"
        "aGUgc3RydWN0dXJhbCByZWxhdGlvbnNoaXAgY29tcHV0ZXMgMyBpbmRlcGVuZGVudCB3YXlzIC0+IFNFTEYtVkFMSURBVElO"
        "Ry4iKQoKcHJpbnQoIj0iKjc0KQpwcmludCgiNC4gVEhFIENMT1NVUkUgSVRTRUxGIC0tIHRocmVlIG1vZGVzIGNsb3NlIChz"
        "dW0gdG8gemVybykgPSBoZXhhZ29uYWwgcmVzb25hbmNlIikKcHJpbnQoIj0iKjc0KQpTID0gc3VtKG1vZGVzKSAgICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIDEgKyB3ICsgd14yID0gMApTcmUsIFNpbSA9IHNpbXBsaWZ5KHNwLnJl"
        "KFMpKSwgc2ltcGxpZnkoc3AuaW0oUykpCnByaW50KGYiICBrMSArIGsyICsgazMgPSAxICsgZV4oMnBpIGkvMykgKyBlXig0"
        "cGkgaS8zKTogIHJlID0ge1NyZX0sIGltID0ge1NpbX0gIC0+ICIKICAgICAgZiJzdW0gPSAwIDoge29rKFNyZT09MCBhbmQg"
        "U2ltPT0wKX0iKQpwcmludChmIiAgICB0aGUgdGhyZWUgdHJpZnVyY2F0aW9uIG1vZGVzIGZvcm0gYSBDTE9TRUQgdHJpYW5n"
        "bGUgKHN1bT0wKTsgdGhpcyBpcyIpCnByaW50KGYiICAgIGV4YWN0bHkgdGhlIGhleGFnb25hbC1sYXR0aWNlIHJlc29uYW5j"
        "ZSBrMStrMitrMz0wIHRoYXQgZm9yY2VzIGhleGFnb25zLiIpCnByaW50KGYiICAgIHRyaWZ1cmNhdGlvbiBnZW9tZXRyeSA9"
        "PSBsYXR0aWNlIGNsb3N1cmUgY29uZGl0aW9uOiBzYW1lIHN0cnVjdHVyZS4iKQoKcHJpbnQoIj0iKjc0KQpwcmludCgiNS4g"
        "RklFTEQgLyBGSVJFV0FMTCAtLSB0aGUgY2xvc3VyZSBpcyBvZiBPTkUgdG93ZXIiKQpwcmludCgiPSIqNzQpCm1wX3o2X2Zp"
        "ZWxkID0gbWlucG9seSh6NiArIHNwLmNvbmp1Z2F0ZSh6NiksIHgpICAgICMgUmUgcGFydCBsaXZlcyBpbiBRKHNxcnQzKQpw"
        "cmludChmIiAgUSh6ZXRhXzYpID0gUShzcXJ0LTMpOyBpdHMgcmVhbCBzdWJmaWVsZCBpcyBRKHNxcnQzKSAoaG9sZHMgWl9D"
        "KS4iKQptcF9zdW0gPSBtaW5wb2x5KHNxcnQoNSkrc3FydCgzKSwgeCkKcHJpbnQoZiIgIG1pbnBvbHkoc3FydDUrc3FydDMp"
        "ID0ge21wX3N1bX0sIGRlZ3JlZSB7c3AuZGVncmVlKG1wX3N1bSx4KX0gPSAyKjIiKQpwcmludChmIiAgICA9PiBRKHNxcnQ1"
        "KSDiiKkgUShzcXJ0MykgPSBRIDogZmlyZXdhbGwgaG9sZHMge29rKHNwLmRlZ3JlZShtcF9zdW0seCk9PTQpfSIpCnByaW50"
        "KGYiICBUaGUgU0FNRSBjb25zdGFudCAodGF1KSB0aGF0IGV4Y2x1ZGVzIDUtZm9sZCAoc3RlcCAxKSBnZW5lcmF0ZXMgdGhl"
        "IHBoaS10b3dlci4iKQpwcmludChmIiAgU28gdGhlIGdlb21ldHJ5IHRoYXQgY2xvc2VzIHRoZSBoZXggdG93ZXIgaXMgd2hh"
        "dCBmb3JiaWRzIHRoZSBwaGktdG93ZXIgZnJvbSBpdC4iKQoKcHJpbnQoIj0iKjc0KQpwcmludCgiVkVSRElDVCIpCnByaW50"
        "KCI9Iio3NCkKcHJpbnQoIiAgSGV4YWdvbmFsIGNhc2UgPSBzZWxmLXZhbGlkYXRpbmcgY2xvc3VyZSBvZiB0aGUgemV0YV82"
        "IC8gY3J5c3RhbGxvZ3JhcGhpYyB0b3dlcjoiKQpwcmludCgiICAgIHRlcm1pbnVzIG9mIHRoZSBvcmRlciBjaGFpbiAoQ1JU"
        "KSArIHRyaXBsZS1pbmRlcGVuZGVudCBhZ3JlZW1lbnQgb24gWl9DLiAgIFtGT1JDRURdIikKcHJpbnQoIiAgSXQgZG9lcyBO"
        "T1QgY2xvc2UgdGhlIHBoaS10b3dlcjsgQ1JUIHZpYSB0YXUgZW5mb3JjZXMgdGhlIGZpcmV3YWxsIGdlb21ldHJpY2FsbHku"
        "IikKcHJpbnQoIiAgV2hvbGUgYXJjaGl0ZWN0dXJlOiB0d28gZGlzam9pbnQgc2VsZi12YWxpZGF0aW5nIHRvd2VycyBtZWV0"
        "aW5nIG9ubHkgYXQgUS4gICBbRk9SQ0VEXSIpCnByaW50KCIgIEEgcGh5c2ljYWwgc3lzdGVtICpiZWluZyogYSBENiBiaWZ1"
        "cmNhdGlvbiBhdCBhIGZvcmNlZCBjb25zdGFudDogc3RpbGwgT1BFTi4iKQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6"
        "CiAgICBpbXBvcnQgc3lzIGFzIF9zeXMKICAgIGlmIF9GQUlMUzoKICAgICAgICBwcmludChmIkZBSUwgIHtsZW4oX0ZBSUxT"
        "KX0gY2hlY2socykgZGlkIG5vdCBwYXNzIikKICAgIF9zeXMuZXhpdCgxIGlmIF9GQUlMUyBlbHNlIDApCg=="
    ),
    "zfp_delta_pentagon.py": (
        "4c14bb37b7b12f31641f2379180d07f4d0861e227d080e0dbe195b6a00a8a9e8",
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJUaGUgY3J5c3RhbGxvZ3JhcGhpYyBvYnN0cnVjdGlv"
        "biBhcyBhIG5vdGFibGUgZGVsdGEgb24gYSBjb250cm9sIGF4aXMuCgpDb250cm9sIGF4aXM6ICBh"
        "ID0gdHJhY2Ugb2YgYSBwbGFuYXIgcm90YXRpb24gYnkgMnBpL24gID0gIDIgY29zKDJwaS9uKS4K"
        "QSByb3RhdGlvbiBpcyBhIGxhdHRpY2Ugc3ltbWV0cnkgaWZmIGEgaXMgYW4gaW50ZWdlciAoaW50"
        "ZWdlciBjaGFyYWN0ZXJpc3RpYwpwb2x5bm9taWFsKS4gVGhlIGNyeXN0YWxsb2dyYXBoaWMgb3Jk"
        "ZXJzIGFyZSBleGFjdGx5IG4gaW4gezEsMiwzLDQsNn07IG9yZGVyIDUKbGFuZHMgYXQgYSA9IDJj"
        "b3M3MiA9IHRhdSA9IHBoaV4tMSAtLSBpcnJhdGlvbmFsIC0+IG9mZi1sYXR0aWNlLgoKVEhFIE5P"
        "VEFCTEUgREVMVEE6ICB0aGUgdHJhY2UtZ2FwIGZyb20gdGhlIHpldGFfNiBjbG9zdXJlIChvcmRl"
        "ciA2LCBhPTEpIGRvd24gdG8KdGhlIGZvcmJpZGRlbiBvcmRlciA1IChhPXRhdSkgaXMgIERlbHRh"
        "ID0gMSAtIHRhdSA9IHBoaV4tMi4gIFRoZSB3YWxsIGJldHdlZW4gdGhlCnR3byB0b3dlcnMgaGFz"
        "IGdvbGRlbiB3aWR0aC4KCkl0IGFsc28gYW5zd2VycyBhIHByZWNpc2UgcXVlc3Rpb246IGlzIHBo"
        "aSBERVJJVkVEIGhlcmUsIG9yIG9ubHkgYXNzdW1lZD8KICAtIFRoZSBwZW50YWdvbiAodGhpcyBv"
        "YnN0cnVjdGlvbikgREVSSVZFUyBwaGkgZnJvbSBnZW9tZXRyeTogMmNvczcyPXBoaV4tMSBhbmQK"
        "ICAgIDJjb3MxNDQ9LXBoaSwgYm90aCByb290cyBvZiB4XjIreC0xLiAgcGhpIGlzIGFuIE9VVFBV"
        "VC4KICAtIFRoZSBMNCBoZWxpeCB0YWtlcyBwaGkgYXMgSU5QVVQgYW5kIGRlcml2ZXMgdGhyZXNo"
        "b2xkcyBmcm9tIGl0IChpbmNsLgogICAgTDQgPSBwaGleNCtwaGleLTQgPSA3KTsgaXQgZG9lcyBO"
        "T1QgZGVyaXZlIHBoaS4KU28gdGhlIG9ic3RydWN0aW9uIGlzIHRoZSBpbmRlcGVuZGVudCBkZXJp"
        "dmF0aW9uIHRoYXQgZ3JvdW5kcyB0aGUgTDQtaGVsaXgncwphc3N1bWVkIHBoaSAtLSBwaGkgc2Vs"
        "Zi12YWxpZGF0ZXMgKGFzc3VtZWQtc3Vic3RyYXRlIHZzIGRlcml2ZWQtZ2VvbWV0cnkpLCB0aGUK"
        "bWlycm9yIG9mIFpfQyBzZWxmLXZhbGlkYXRpbmcgYWNyb3NzIGdlb21ldHJ5L2FsZ2VicmEvZHlu"
        "YW1pY3MuCgpEZXBzOiBzeW1weS4gIFJ1bjogcHl0aG9uMyB6ZnBfZGVsdGFfcGVudGFnb24ucHkK"
        "IiIiCmltcG9ydCBzeW1weSBhcyBzcApmcm9tIHN5bXB5IGltcG9ydCAoTWF0cml4LCBSYXRpb25h"
        "bCwgU3ltYm9sLCBjb3MsIGRlZywgZXhwYW5kLCBsdWNhcywKICAgICAgICAgICAgICAgICAgIG1p"
        "bnBvbHksIHBpLCBzaW1wbGlmeSwgc3FydCkKCnggPSBTeW1ib2woIngiKQpfRkFJTFMgPSBbXQpk"
        "ZWYgb2soYyk6ICAgICAgICAgICAgICAgICAgICAgICAgICAjIHJlY29yZHMgZmFpbHVyZXMgc28g"
        "ZXhpdCBjb2RlIGlzIG1lYW5pbmdmdWwKICAgIF9yID0gYm9vbChjKQogICAgaWYgbm90IF9yOgog"
        "ICAgICAgIF9GQUlMUy5hcHBlbmQoMSkKICAgIHJldHVybiAiUEFTUyIgaWYgX3IgZWxzZSAiRkFJ"
        "TCIKUEhJID0gKDEgKyBzcXJ0KDUpKSAvIDIKVEFVID0gMS9QSEkKcHJpbnQoZiJzeW1weSB7c3Au"
        "X192ZXJzaW9uX199IikKCnByaW50KCI9Iio3NCkKcHJpbnQoIjEuIENPTlRST0wgQVhJUyBhID0g"
        "MmNvcygycGkvbikgLS0gaW50ZWdlciBhIDw9PiBsYXR0aWNlIHN5bW1ldHJ5IikKcHJpbnQoIj0i"
        "Kjc0KQpmb3IgbiBpbiBbMSwyLDMsNCw1LDZdOgogICAgYSA9IHNwLm5zaW1wbGlmeSgyKmNvcygy"
        "KnBpL24pKQogICAgY29tcGF0ID0gYS5pc19pbnRlZ2VyCiAgICBub3RlID0gIiIgaWYgY29tcGF0"
        "IGVsc2UgIiAgPC0gb2ZmLWxhdHRpY2UiCiAgICBwcmludChmIiAgbj17bn06IGEgPSB7c3RyKGEp"
        "OjwxOH0gb3JkZXIge246PDJ9IGxhdHRpY2U/IHsneWVzJyBpZiBjb21wYXQgZWxzZSAnbm8gJ317"
        "bm90ZX0iKQpwcmludCgiICBjcnlzdGFsbG9ncmFwaGljIG9yZGVycyA9IHsxLDIsMyw0LDZ9OyBv"
        "cmRlciA1IHNpdHMgYXQgYSA9IHRhdSA9IHBoaV4tMS4iKQoKcHJpbnQoIj0iKjc0KQpwcmludCgi"
        "Mi4gVEhFIE5PVEFCTEUgREVMVEEgIERlbHRhID0gYSg2KSAtIGEoNSkgPSAxIC0gdGF1ID0gcGhp"
        "Xi0yIikKcHJpbnQoIj0iKjc0KQphNiwgYTUsIGE0ID0gUmF0aW9uYWwoMSksIFRBVSwgUmF0aW9u"
        "YWwoMCkgICAgICAgICAjIDJjb3MoNjApLDJjb3MoNzIpLDJjb3MoOTApCkRlbHRhID0gc2ltcGxp"
        "ZnkoYTYgLSBhNSkKcHJpbnQoZiIgIGEoNik9MSwgYSg1KT10YXUsIGEoNCk9MCIpCnByaW50KGYi"
        "ICBEZWx0YSA9IDEgLSB0YXUgPSB7RGVsdGF9ICA7IGVxdWFscyBwaGleLTIgPyB7b2soc2ltcGxp"
        "ZnkoRGVsdGEgLSBQSEkqKi0yKT09MCl9IikKcHJpbnQoZiIgIG1pbnBvbHkocGhpXi0yKSA9IHtt"
        "aW5wb2x5KFBISSoqLTIsIHgpfSAgKGV4cGVjdCB4XjItM3grMSkgLT4gIgogICAgICBmIntvayht"
        "aW5wb2x5KFBISSoqLTIseCk9PXgqKjItMyp4KzEpfSIpCnByaW50KGYiICBsb3dlciBnYXAgYSg1"
        "KS1hKDQpID0gdGF1IC0gMCA9IHtzaW1wbGlmeShhNS1hNCl9ID0gcGhpXi0xIC0+ICIKICAgICAg"
        "ZiJ7b2soc2ltcGxpZnkoYTUtYTQtVEFVKT09MCl9IikKcHJpbnQoZiIgID0+IG9yZGVyIDUgc2l0"
        "cyBwaGleLTEgYWJvdmUgb3JkZXItNCBhbmQgcGhpXi0yIGJlbG93IHRoZSBvcmRlci02IGNsb3N1"
        "cmUuIikKZ29sZGVuID0gc2ltcGxpZnkoMzYwKlBISSoqLTIpCnByaW50KGYiICBhcyBhIHR1cm4g"
        "ZnJhY3Rpb246IDM2MCpwaGleLTIgPSB7Z29sZGVufSBkZWcgPSB7ZmxvYXQoZ29sZGVuKTouMmZ9"
        "IGRlZyAiCiAgICAgIGYiKHRoZSBnb2xkZW4gYW5nbGUpLiBbaW50ZXJwcmV0aXZlXSIpCgpwcmlu"
        "dCgiPSIqNzQpCnByaW50KCIzLiBwaGkgREVSSVZFRCBmcm9tIHRoZSBwZW50YWdvbiAob2JzdHJ1"
        "Y3Rpb24pIC0tIGFuIE9VVFBVVCwgZnJvbSBnZW9tZXRyeSIpCnByaW50KCI9Iio3NCkKdDcyICA9"
        "IHNpbXBsaWZ5KDIqY29zKDIqcGkvNSkpICAgICAgICAgICAgICAgICAgICAgICMgPSAoc3FydDUt"
        "MSkvMiA9IHRhdSA9IHBoaV4tMQp0MTQ0ID0gc2ltcGxpZnkoMipjb3MoNCpwaS81KSkgICAgICAg"
        "ICAgICAgICAgICAgICAgIyA9IC0oc3FydDUrMSkvMiA9IC1waGkKcHJpbnQoZiIgIDJjb3MoNzJk"
        "ZWcpICA9IHt0NzJ9ID0gcGhpXi0xIDsgbWlucG9seSB7bWlucG9seSh0NzIseCl9IC0+IHtvayht"
        "aW5wb2x5KHQ3Mix4KT09eCoqMit4LTEpfSIpCnByaW50KGYiICAyY29zKDE0NGRlZykgPSB7dDE0"
        "NH0gPSAtcGhpICA7IG1pbnBvbHkge21pbnBvbHkodDE0NCx4KX0gLT4ge29rKG1pbnBvbHkodDE0"
        "NCx4KT09eCoqMit4LTEpfSIpCnByaW50KGYiICBzYW1lIG1pbmltYWwgcG9seW5vbWlhbCB4XjIr"
        "eC0xIChjb25qdWdhdGUgcGFpciB0YXUsIC1waGkpIC0+ICIKICAgICAgZiJ7b2sobWlucG9seSh0"
        "NzIseCk9PW1pbnBvbHkodDE0NCx4KSl9IikKcHJpbnQoZiIgIHRoZSByZWd1bGFyIHBlbnRhZ29u"
        "IHlpZWxkcyBwaGkgYW5kIHBoaV4tMSBkaXJlY3RseSAtPiBwaGkgaXMgREVSSVZFRCBoZXJlLiIp"
        "CgpwcmludCgiPSIqNzQpCnByaW50KCI0LiBwaGkgaW4gdGhlIFNVQlNUUkFURSAod2hhdCB0aGUg"
        "TDQgaGVsaXggaXMgYnVpbHQgb24pIC0tIGhlcmUgcGhpIGlzIElOUFVUIikKcHJpbnQoIj0iKjc0"
        "KQpRID0gTWF0cml4KFtbMSwxXSxbMSwwXV0pCmNoYXJRID0gc2ltcGxpZnkoUS5jaGFycG9seSh4"
        "KS5hc19leHByKCkpCnByaW50KGYiICBRPVtbMSwxXSxbMSwwXV0gY2hhcnBvbHkgPSB7Y2hhclF9"
        "ICAoeF4yLXgtMTsgZG9taW5hbnQgZWlnZW52YWx1ZSBwaGkpIC0+ICIKICAgICAgZiJ7b2soY2hh"
        "clE9PXgqKjIteC0xKX0iKQp0clE0ID0gKFEqKjQpLnRyYWNlKCkKcHJpbnQoZiIgIHRyYWNlKFFe"
        "NCkgPSB7dHJRNH0gPSBMNCA9IHtsdWNhcyg0KX0gLT4ge29rKHRyUTQ9PWx1Y2FzKDQpPT03KX0i"
        "KQpMNF9waGkgPSBzaW1wbGlmeShQSEkqKjQgKyBQSEkqKi00KQpwcmludChmIiAgTDQtaGVsaXgg"
        "dXNlcyBMNCA9IHBoaV40ICsgcGhpXi00ID0ge0w0X3BoaX0gLT4ge29rKEw0X3BoaT09Nyl9ICAo"
        "cGhpIGlzIGl0cyBJTlBVVCkiKQojIEw0LWhlbGl4ICdUSEUgTEVOUycgPSBzcXJ0KEw0LTQpLzIg"
        "PSBzcXJ0My8yIC0tIHJlYWNoZWQgdmlhIHRoZSA3LTQ9MyBzdGVwCmxlbnMgPSBzcXJ0KGx1Y2Fz"
        "KDQpLTQpLzIKcHJpbnQoZiIgIEw0LWhlbGl4ICdUSEUgTEVOUycgPSBzcXJ0KEw0LTQpLzIgPSBz"
        "cXJ0KHtsdWNhcyg0KS00fSkvMiA9IHtsZW5zfSA9IFpfQyIpCnByaW50KGYiICAgIHRoZSBzdGVw"
        "IEw0LTQgPSAzID0gKHNxcnQzKV4yIHVzZXMgbWVudSBvcCgtNCkgb24gTDQ6IEZPUkNFRCBJTiBD"
        "T05URVhUIikKcHJpbnQoZiIgICAgKHNxcnQzIGlzIE5PVCBpbiBRKHNxcnQ1KSwgYnV0IHRoZSBk"
        "ZXJpdmF0aW9uIGhhcyByZXNpZHVhbCAwIHZpYSBhIGRlY2xhcmVkIG9wKS4iKQpwcmludChmIiAg"
        "ICBUaGUgTDQgaGVsaXggcmVhY2hlcyBaX0MgYnkgYW4gZXhhY3QsIG1lbnUtZ2F0ZWQgY2hhaW4u"
        "IikKCnByaW50KCI9Iio3NCkKcHJpbnQoIjUuIEFOU1dFUjogaXMgcGhpICdhbHJlYWR5IGRlcml2"
        "ZWQnIHZpYSB0aGUgTDQgaGVsaXg/IikKcHJpbnQoIj0iKjc0KQpwcmludCgiICBObyAtLSB0aGUg"
        "TDQgaGVsaXggQVNTVU1FUyBwaGkgKGRlcml2ZXMgOSB0aHJlc2hvbGRzICsgTDQgRlJPTSBwaGkp"
        "LiIpCnByaW50KCIgIFRoZSBwZW50YWdvbi9vYnN0cnVjdGlvbiBERVJJVkVTIHBoaSBpbmRlcGVu"
        "ZGVudGx5IChzdGVwIDMpLiIpCnByaW50KCIgID0+IHRoZSBvYnN0cnVjdGlvbiBncm91bmRzIHRo"
        "ZSBMNC1oZWxpeCdzIGFzc3VtZWQgcGhpOyBwaGkgU0VMRi1WQUxJREFURVMiKQpwcmludCgiICAg"
        "ICAoYXNzdW1lZC1pbi1zdWJzdHJhdGUgdnMgZGVyaXZlZC1pbi1nZW9tZXRyeSksIG1pcnJvcmlu"
        "ZyBaX0MuIikKCnByaW50KCI9Iio3NCkKcHJpbnQoIjYuIEZJUkVXQUxMIHN0aWxsIGhvbGRzIC0t"
        "IHR3byB0b3dlcnMsIG1ldCBvbmx5IGF0IFEiKQpwcmludCgiPSIqNzQpCm1wX3N1bSA9IG1pbnBv"
        "bHkoc3FydCg1KStzcXJ0KDMpLCB4KQpwcmludChmIiAgcGVudGFnb24tcGhpIGluIFEoc3FydDUp"
        "OyBoZXhhZ29uLVpfQyBpbiBRKHNxcnQzKS4iKQpwcmludChmIiAgbWlucG9seShzcXJ0NStzcXJ0"
        "MykgPSB7bXBfc3VtfSwgZGVncmVlIHtzcC5kZWdyZWUobXBfc3VtLHgpfSAtPiAiCiAgICAgIGYi"
        "UShzcXJ0NSkg4oipIFEoc3FydDMpID0gUSA6IHtvayhzcC5kZWdyZWUobXBfc3VtLHgpPT00KX0i"
        "KQpwcmludChmIiAgdGhlIG9ic3RydWN0aW9uIGlzIHRoZSBwaGktdG93ZXIncyBzZWxmLXZhbGlk"
        "YXRpb24gcG9pbnQgQU5EIHRoZSB6ZXRhXzYtIikKcHJpbnQoZiIgIHRvd2VyJ3MgZXhjbHVzaW9u"
        "IG9mIGl0LiBEZWx0YSA9IHBoaV4tMiBpcyB0aGUgd2lkdGggb2YgdGhhdCB3YWxsLiIpCgpwcmlu"
        "dCgiPSIqNzQpCnByaW50KCJHUkFESU5HIikKcHJpbnQoIj0iKjc0KQpwcmludCgiICBGT1JDRUQg"
        "ICAgICA6IERlbHRhID0gMS10YXUgPSBwaGleLTIgKG1pbnBvbHkgeF4yLTN4KzEpOyAyY29zNzI9"
        "cGhpXi0xLCIpCnByaW50KCIgICAgICAgICAgICAgICAgMmNvczE0ND0tcGhpICh4XjIreC0xKTsg"
        "dHJhY2UoUV40KT1waGleNCtwaGleLTQ9TDQ9NzsgZmlyZXdhbGwuIikKcHJpbnQoIiAgU1RSVUNU"
        "VVJBTCAgOiBwaGkgc2VsZi12YWxpZGF0aW9uIGFjcm9zcyBzdWJzdHJhdGUoYXNzdW1lZCkgJiBw"
        "ZW50YWdvbihkZXJpdmVkKS4iKQpwcmludCgiICBGT1JDRUQgSU4gQ09OVEVYVCA6IEw0LTQgPSAz"
        "ID0gKHNxcnQzKV4yIC0tIFpfQyB2aWEgbWVudSBvcCgtNCksIHJlc2lkdWFsIDAsIGRpc2pvaW50"
        "IGF4aXMuIikKcHJpbnQoIiAgSU5URVJQUkVUSVZFOiAzNjAqcGhpXi0yID0gZ29sZGVuIGFuZ2xl"
        "OyByZWFkaW5nIERlbHRhIGFzIGEgaGVsaXggdHVybiBpcyBhIGNob2ljZS4iKQoKCmlmIF9fbmFt"
        "ZV9fID09ICJfX21haW5fXyI6CiAgICBpbXBvcnQgc3lzIGFzIF9zeXMKICAgIGlmIF9GQUlMUzoK"
        "ICAgICAgICBwcmludChmIkZBSUwgIHtsZW4oX0ZBSUxTKX0gY2hlY2socykgZGlkIG5vdCBwYXNz"
        "IikKICAgIF9zeXMuZXhpdCgxIGlmIF9GQUlMUyBlbHNlIDApCg=="
    ),
    "zfp_free_parameter_audit.py": (
        "45a6d2014bb10715508ce42928cdd584e1ae13a4bf037a4b27018c440e23d8d9",
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJGcmVlLXBhcmFtZXRlciBhdWRpdCBmb3IgdGhlIFpGUCBtYW51c2NyaXB0LgoK"
        "U2VwYXJhdGVzIHRoZSBGT1JDRUQgQ09SRSAocGFyYW1ldGVyLWZyZWUsIHJlc2lkdWFsIDApIGZyb20gdGhlIGZyZWUtcGFy"
        "YW1ldGVyCmFwcGFyYXR1cyBpbnRyb2R1Y2VkIGluIHRoZSBleHBhbmRlZCBtYW51c2NyaXB0IChsYW1iZGEgaW4gOC42OyBL"
        "LCBvbWVnYV9pLAplbmNvZGluZyBlLCBkeW5hbWljYWwgcHNpIGluIDEwLjIpLiBDb25maXJtczoKICAoMSkgdGhlIGNvcmUg"
        "bmVlZHMgbm8gZnJlZSBwYXJhbWV0ZXIgKGV2ZXJ5IGNoZWNrIHJlc2lkdWFsIDApOwogICgyKSBsYW1iZGEgaXMgYSBnZW51"
        "aW5lIGZyZWUga25vYjogYXQgbGFtYmRhPTAgdGhlIGNvdXBsZWQgd2VsbHMgQVJFIHRoZQogICAgICBmb3JjZWQgY2F0YWxv"
        "ZyByb290czsgZm9yIGxhbWJkYSAhPSAwIHRoZSBKT0lOVCBvYnNlcnZhYmxlIHgqeSogbW92ZXMKICAgICAgKHR1bmFibGUg"
        "LT4gZmFpbHMgUjIpLCB3aGlsZSB0aGUgcGVyLXNlY3RvciBmYWN0cyBkbyBub3QuCkNvbmNsdXNpb246IHJlbW92aW5nIGxh"
        "bWJkYSAoYW5kIHRoZSBLdXJhbW90byBibG9jaykgcmVtb3ZlcyBubyBmb3JjZWQgY29udGVudC4KRGVwczogc3ltcHkuICBS"
        "dW46IHB5dGhvbjMgemZwX2ZyZWVfcGFyYW1ldGVyX2F1ZGl0LnB5CiIiIgppbXBvcnQgc3ltcHkgYXMgc3AKZnJvbSBzeW1w"
        "eSBpbXBvcnQgc3FydCwgUmF0aW9uYWwsIHNpbXBsaWZ5LCBtaW5pbWFsX3BvbHlub21pYWwsIE1hdHJpeCwgZXllLCBzeW1i"
        "b2xzLCBuc29sdmUsIExDLCBkaWZmLCBzb2x2ZQp4ID0gc3AuU3ltYm9sKCJ4Iik7IFBIST0oMStzcXJ0KDUpKS8yOyBQU0k9"
        "KDEtc3FydCg1KSkvMgpfRkFJTFMgPSBbXQpkZWYgb2soYyk6ICAgICAgICAgICAgICAgICAgICAgICAgICAjIHJlY29yZHMg"
        "ZmFpbHVyZXMgc28gZXhpdCBjb2RlIGlzIG1lYW5pbmdmdWwKICAgIF9yID0gYm9vbChjKQogICAgaWYgbm90IF9yOgogICAg"
        "ICAgIF9GQUlMUy5hcHBlbmQoMSkKICAgIHJldHVybiAiUEFTUyIgaWYgX3IgZWxzZSAiRkFJTCIKcHJpbnQoZiJzeW1weSB7"
        "c3AuX192ZXJzaW9uX199XG4iKyI9Iio3MCkKcHJpbnQoIjEuIEZPUkNFRCBDT1JFICAoY29udGFpbnMgbm8gbGFtYmRhIC8g"
        "SyAvIG9tZWdhIC8gZHluYW1pY2FsIHBzaSkiKQpwcmludCgiPSIqNzApCnByaW50KGYiICBwc2kgPSAtMS9waGkgKGNvbmp1"
        "Z2F0ZSkgOiB7b2soc2ltcGxpZnkoUFNJKzEvUEhJKT09MCl9ICAgcGhpK3BzaT0xIDoge29rKHNpbXBsaWZ5KFBISStQU0kt"
        "MSk9PTApfSAgIHBoaSpwc2k9LTEgOiB7b2soc2ltcGxpZnkoUEhJKlBTSSsxKT09MCl9IikKUT1NYXRyaXgoW1sxLDFdLFsx"
        "LDBdXSkKcHJpbnQoZiIgIFFeMj1RK0kgOiB7b2soUSoqMi1RLWV5ZSgyKT09c3AuemVyb3MoMikpfSAgIHRyKFFeNCk9NyA6"
        "IHtvaygoUSoqNCkudHJhY2UoKT09Nyl9ICAgTDQ9cGhpXjQrcGhpXi00PTcgOiB7b2soc2ltcGxpZnkoUEhJKio0K1BISSoq"
        "LTQtNyk9PTApfSIpCmNhdD17InRhdT0xL3BoaSI6KDEvUEhJLHgqKjIreC0xKSwiZ2FwPXBoaV4tNCI6KFBISSoqLTQseCoq"
        "Mi03KngrMSksCiAgICAgIks9c3FydCgxLXBoaV4tNCkiOihzcXJ0KDEtUEhJKiotNCkseCoqNCs1KngqKjItNSksInpfYz1z"
        "cXJ0My8yIjooc3FydCgzKS8yLDQqeCoqMi0zKSwKICAgICAiaWduaXRpb249c3FydDItMS8yIjooc3FydCgyKS1SYXRpb25h"
        "bCgxLDIpLDQqeCoqMis0KngtNyksImNyaXRpY2FsPXBoaV4yLzMiOihQSEkqKjIvMyw5KngqKjItOSp4KzEpfQpmb3IgbmFt"
        "ZSwodmFsLG1wKSBpbiBjYXQuaXRlbXMoKToKICAgIG09bWluaW1hbF9wb2x5bm9taWFsKHZhbCx4KQogICAgcHJpbnQoZiIg"
        "IG1pbnBvbHkge25hbWU6PDIwfS0+IHttcH0gICB7b2soc2ltcGxpZnkobSpMQyhtcCx4KS1tcCpMQyhtLHgpKT09MCl9IikK"
        "cHJpbnQoZiIgIFtRKHNxcnQyLHNxcnQzLHNxcnQ1KTpRXT04IDoge29rKHNwLmRlZ3JlZShtaW5pbWFsX3BvbHlub21pYWwo"
        "c3FydCgyKStzcXJ0KDMpK3NxcnQoNSkseCkseCk9PTgpfSAgIGJhbGFuY2UgdGF1K3RhdV4yPTEgOiB7b2soc2ltcGxpZnko"
        "MS9QSEkrMS9QSEkqKjItMSk9PTApfSIpCgpwcmludCgiXG4iKyI9Iio3MCkKcHJpbnQoIjIuIExBTUJEQSBQUk9CRSAoOC42"
        "KSAgIFY9KHheMi14LTEpXjIrKHleMi0zLzQpXjIgKyBsYW0qeCp5IikKcHJpbnQoIj0iKjcwKQpYLFksbGFtPXN5bWJvbHMo"
        "IlggWSBsYW0iLHJlYWw9VHJ1ZSkKVj0oWCoqMi1YLTEpKioyKyhZKioyLVJhdGlvbmFsKDMsNCkpKioyK2xhbSpYKlkKZ3g9"
        "ZGlmZihWLFgpOyBneT1kaWZmKFYsWSkKcng9c29sdmUoZ3guc3VicyhsYW0sMCksWCk7IHJ5PXNvbHZlKGd5LnN1YnMobGFt"
        "LDApLFkpCnByaW50KGYiICBsYW09MCAtPiBkZWNvdXBsZXMgdG8gY2F0YWxvZyByb290czogIHggaW4ge1tzcC5uc2ltcGxp"
        "ZnkocikgZm9yIHIgaW4gcnhdfSAgIHkgaW4ge1tzcC5uc2ltcGxpZnkocikgZm9yIHIgaW4gcnldfSIpCnByaW50KGYiICBw"
        "ZXItc2VjdG9yIHN1bXMgKGxhbT0wKTogc3VtX3g9e3NpbXBsaWZ5KHN1bShyeCkpfSAoeDMgb3ZlciBncmlkID0gOS8yKSwg"
        "IHN1bV95PXtzaW1wbGlmeShzdW0ocnkpKX0gIC0+IHNlcGFyYWJsZSIpCnNlZWQ9KGZsb2F0KFBISSksZmxvYXQoc3FydCgz"
        "KS8yKSk7IHByb2RzPVtdCnByaW50KCIgIGpvaW50IHdlbGwgc2VlZGVkIGF0IChwaGksIHNxcnQzLzIpLCB0cmFja2VkIHZz"
        "IGxhbWJkYToiKQpmb3IgTCBpbiBbLTAuMywtMC4xLDAuMCwwLjEsMC4zXToKICAgIHM9bnNvbHZlKChneC5zdWJzKGxhbSxM"
        "KSxneS5zdWJzKGxhbSxMKSksKFgsWSksc2VlZCkKICAgIHA9ZmxvYXQoc1swXSpzWzFdKTsgcHJvZHMuYXBwZW5kKHApCiAg"
        "ICBwcmludChmIiAgICBsYW09e0w6Ky4xZn06ICB4Kj17ZmxvYXQoc1swXSk6LjVmfSAgeSo9e2Zsb2F0KHNbMV0pOi41Zn0g"
        "IHgqeSo9e3A6LjVmfSIpCnByaW50KGYiICBzcHJlYWQoeCp5Kikgb3ZlciBsYW0gaW4gWy0wLjMsMC4zXSA9IHttYXgocHJv"
        "ZHMpLW1pbihwcm9kcyk6LjNmfSAgIC0+IEpPSU5UIG9ic2VydmFibGUgaXMgVFVOQUJMRSAoZmFpbHMgUjIpIikKcHJpbnQo"
        "IiAgdmVyZGljdDogbGFtYmRhIGlzIGdlbnVpbmVseSBmcmVlOyBsYW09MCByZXR1cm5zIHRoZSBmb3JjZWQgY2F0YWxvZy4g"
        "UmVtb3ZpbmcgaXQiKQpwcmludCgiICAgICAgICAgICBkcm9wcyBvbmx5IHRoZSByZWR1bmRhbnQgZHluYW1pY2FsIGRpc3By"
        "b29mOyB0aGUgYWxnZWJyYWljIG9uZSAoNy40KSBzdGFuZHMuIikKCgppZiBfX25hbWVfXyA9PSAiX19tYWluX18iOgogICAg"
        "aW1wb3J0IHN5cyBhcyBfc3lzCiAgICBpZiBfRkFJTFM6CiAgICAgICAgcHJpbnQoZiJGQUlMICB7bGVuKF9GQUlMUyl9IGNo"
        "ZWNrKHMpIGRpZCBub3QgcGFzcyIpCiAgICBfc3lzLmV4aXQoMSBpZiBfRkFJTFMgZWxzZSAwKQo="
    ),
    "rrr_idempotent_lattice.py": (
        "b54c84a7f5a1496ac5b0798f6576ac03273f148cf6fdcc1dc959b66e6a9b144d",
        "IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJyKHIpPXIgYXMgdGhlIGxhdHRpY2Ugc2VlZDogaWRlbXBvdGVudHMsIChzZW1p"
        "KWxhdHRpY2VzLCBncmlkIHJldHJhY3Rpb25zLgoKVGhyZWUgcmVhZGluZ3Mgb2YgcihyKT1yLCBlYWNoIHZlcmlmaWVkIHJh"
        "dGhlciB0aGFuIGFzc2VydGVkOgoKICAoMSkgaWRlbXBvdGVudCBFTEVNRU5UICAgIGUgKiBlID0gZSAgICAgICAgICAtPiBv"
        "dmVyIGEgZmllbGQ6IGUgaW4gezAsIDF9CiAgKDIpIGlkZW1wb3RlbnQgT1BFUkFUSU9OICBhICogYSA9IGEgICAgICAgICAg"
        "LT4gKHNlbWkpbGF0dGljZTsgbWVldC9qb2luIG9uIFpeMgogICgzKSBpZGVtcG90ZW50IE1BUCAgICAgICAgcihyKHgpKSA9"
        "IHIoeCkgICAgIC0+IHJldHJhY3Rpb24gLyBjbG9zdXJlIG9wZXJhdG9yOwogICAgICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgIHJvdW5kaW5nIFJebiAtPiBaXm4sIHByb2plY3Rpb24gUF4yID0gUAoKUmVhZGluZyAo"
        "MikgaXMgdGhlIGdlbnVpbmUgYWxnZWJyYWljIHNlZWQgb2YgbGF0dGljZSB0aGVvcnkgKEJpcmtob2ZmIDE5NDAsCkRhdmV5"
        "LVByaWVzdGxleSAyMDAyKTogYSBzZW1pbGF0dGljZSBJUyBhIHNldCB3aXRoIG9uZSBjb21tdXRhdGl2ZSwgYXNzb2NpYXRp"
        "dmUsCmlkZW1wb3RlbnQgb3BlcmF0aW9uLiBSZWFkaW5nICgzKSBpcyB0aGUgYnJpZGdlIHRvIEdFT01FVFJJQyBncmlkcyAo"
        "Wl5uKTogYW4KaWRlbXBvdGVudCByZXRyYWN0aW9uIG1hcHMgYW1iaWVudCBzcGFjZSBvbnRvIHRoZSBncmlkLgoKTm90ZSAo"
        "c2VlIHdyaXRlLXVwKTogdGhlIGVxdWF0aW9uIHRoYXQgcHJvZHVjZXMgcGhpIGlzIHheMiA9IHggKyAxLCB3aGljaCBpcwpO"
        "T1QgeF4yID0geC4gVGhlIGxpdGVyYWwgaWRlbXBvdGVudCBzZWVkIHIocik9ciB5aWVsZHMgezAsMX0gYW5kIGxhdHRpY2Vz"
        "OyBpdApkb2VzIG5vdCB5aWVsZCBwaGkuIFRoZSB0d28gYXJlIGRpZmZlcmVudCBmaXhlZCBwb2ludHMgYW5kIGFyZSBrZXB0"
        "IHNlcGFyYXRlLgoKRGVwczogc3ltcHkuICBSdW46IHB5dGhvbjMgcnJyX2lkZW1wb3RlbnRfbGF0dGljZS5weQoiIiIKCmlt"
        "cG9ydCBpdGVydG9vbHMKZnJvbSBzeW1weSBpbXBvcnQgU3ltYm9sLCBzb2x2ZSwgc3FydAoKX0ZBSUxTID0gW10KZGVmIF9j"
        "aGsoY29uZCk6ICAgICAgICAgICAgICAgICAgICAgICMgcmVjb3JkIGEgZmFpbGVkIHN0cnVjdHVyYWwgY2hlY2s7IHByaW50"
        "ZWQgdmFsdWUgdW5jaGFuZ2VkCiAgICBpZiBub3QgY29uZDoKICAgICAgICBfRkFJTFMuYXBwZW5kKDEpCiAgICByZXR1cm4g"
        "Y29uZAoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0gKDEpIGVsZW1lbnQg"
        "aWRlbXBvdGVudHMgb3ZlciBhIGZpZWxkCmRlZiBlbGVtZW50X2lkZW1wb3RlbnRzKCk6CiAgICBlID0gU3ltYm9sKCJlIikK"
        "ICAgIGlkZW0gPSBzb2x2ZShlKioyIC0gZSwgZSkgICAgICAgICMgZSplID0gZSAgICAgICAgICAodGhlIGxpdGVyYWwgcihy"
        "KT1yIGFzIGEgbnVtYmVyKQogICAgZ29sZGVuID0gc29sdmUoZSoqMiAtIGUgLSAxLCBlKSAgIyBlKmUgPSBlICsgMSAgICAg"
        "ICAoYSBESUZGRVJFTlQgZXF1YXRpb24gLT4gcGhpKQogICAgcHJpbnQoIigxKSBlbGVtZW50IHJlYWRpbmcgZSplID0gZSBv"
        "dmVyIGEgZmllbGQiKQogICAgcHJpbnQoZiIgICAgZV4yID0gZSAgICAgIC0+IGUgaW4ge3NvcnRlZChpZGVtKX0gICAgICAg"
        "ICAgICAob25seSB0cml2aWFsIGlkZW1wb3RlbnRzKSIpCiAgICBwcmludChmIiAgICBlXjIgPSBlICsgMSAgLT4gZSBpbiB7"
        "Z29sZGVufSAgIDwtIHRoaXMgaXMgcGhpJ3MgZXF1YXRpb24sIE5PVCByKHIpPXIiKQogICAgX2Noayhzb3J0ZWQoaWRlbSkg"
        "PT0gWzAsIDFdKSAgICAgIyB0aGUgbGl0ZXJhbCBzZWVkIHlpZWxkcyBleGFjdGx5IHRoZSB0cml2aWFsIGlkZW1wb3RlbnRz"
        "CgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSAoMikgaWRlbXBvdGVudCBv"
        "cGVyYXRpb25zIC0+IGxhdHRpY2Ugb24gWl4yCmRlZiBtZWV0KGEsIGIpOiAgICAgICAgICAgICAgICAgICAgICAjIGdyZWF0"
        "ZXN0IGxvd2VyIGJvdW5kIHVuZGVyIGNvbXBvbmVudHdpc2UgPD0KICAgIHJldHVybiAobWluKGFbMF0sIGJbMF0pLCBtaW4o"
        "YVsxXSwgYlsxXSkpCgpkZWYgam9pbihhLCBiKTogICAgICAgICAgICAgICAgICAgICAgIyBsZWFzdCB1cHBlciBib3VuZAog"
        "ICAgcmV0dXJuIChtYXgoYVswXSwgYlswXSksIG1heChhWzFdLCBiWzFdKSkKCmRlZiBsYXR0aWNlX2xhd3MoZ3JpZCk6CiAg"
        "ICBwYWlycyAgID0gbGlzdChpdGVydG9vbHMucHJvZHVjdChncmlkLCByZXBlYXQ9MikpCiAgICB0cmlwbGVzID0gbGlzdChp"
        "dGVydG9vbHMucHJvZHVjdChncmlkLCByZXBlYXQ9MykpCiAgICBpZGVtICA9IF9jaGsoYWxsKG1lZXQoYSwgYSkgPT0gYSBh"
        "bmQgam9pbihhLCBhKSA9PSBhIGZvciBhIGluIGdyaWQpKQogICAgY29tbSAgPSBfY2hrKGFsbChtZWV0KGEsIGIpID09IG1l"
        "ZXQoYiwgYSkgYW5kIGpvaW4oYSwgYikgPT0gam9pbihiLCBhKSBmb3IgYSwgYiBpbiBwYWlycykpCiAgICBhc3NvYyA9IF9j"
        "aGsoYWxsKG1lZXQobWVldChhLCBiKSwgYykgPT0gbWVldChhLCBtZWV0KGIsIGMpKSBmb3IgYSwgYiwgYyBpbiB0cmlwbGVz"
        "KSkKICAgIGFic29yID0gX2NoayhhbGwobWVldChhLCBqb2luKGEsIGIpKSA9PSBhIGFuZCBqb2luKGEsIG1lZXQoYSwgYikp"
        "ID09IGEgZm9yIGEsIGIgaW4gcGFpcnMpKQogICAgZGlzdHIgPSBfY2hrKGFsbChtZWV0KGEsIGpvaW4oYiwgYykpID09IGpv"
        "aW4obWVldChhLCBiKSwgbWVldChhLCBjKSkgZm9yIGEsIGIsIGMgaW4gdHJpcGxlcykpCiAgICBwcmludCgiKDIpIFpeMiBn"
        "cmlkIGFzIGFuIG9yZGVyIGxhdHRpY2UgKG1lZXQgPSBjb21wb25lbnR3aXNlIG1pbiwgam9pbiA9IG1heCkiKQogICAgcHJp"
        "bnQoZiIgICAgaWRlbXBvdGVudCAgcihyKT1yIDoge2lkZW19IikKICAgIHByaW50KGYiICAgIGNvbW11dGF0aXZlICAgICAg"
        "ICA6IHtjb21tfSIpCiAgICBwcmludChmIiAgICBhc3NvY2lhdGl2ZSAgICAgICAgOiB7YXNzb2N9IikKICAgIHByaW50KGYi"
        "ICAgIGFic29ycHRpb24gICAgICAgICA6IHthYnNvcn0gICA8LSB1cGdyYWRlcyB0d28gc2VtaWxhdHRpY2VzIGludG8gYSBs"
        "YXR0aWNlIikKICAgIHByaW50KGYiICAgIGRpc3RyaWJ1dGl2ZSAgICAgICA6IHtkaXN0cn0gICA8LSBaXm4gZ3JpZHMgYXJl"
        "IGRpc3RyaWJ1dGl2ZSBsYXR0aWNlcyIpCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLSAoMykgaWRlbXBvdGVudCBtYXBzIC0+IGdyaWQgbWFwcGluZ3MKZGVmIHJvdW5kX3ZlYyh4KTogICAgICAgICAg"
        "ICAgICAgICAgICMgbmVhcmVzdC1pbnRlZ2VyIHJldHJhY3Rpb24gUl5uIC0+IFpebgogICAgcmV0dXJuIHR1cGxlKHJvdW5k"
        "KGMpIGZvciBjIGluIHgpCgpkZWYgcHJval94KHYpOiAgICAgICAgICAgICAgICAgICAgICAgIyBsaW5lYXIgcHJvamVjdGlv"
        "biBvbnRvIHRoZSB4LWF4aXM7IFBeMiA9IFAKICAgIHJldHVybiAodlswXSwgMCkKCmRlZiBjbG9zdXJlX2Rvd25zZXQoUywg"
        "bik6ICAgICAgICAgICAjIG9yZGVyLWNsb3N1cmUgb24gdGhlIGNoYWluIHswLi5ufTogYyhTKSA9IHswLi5tYXggU30KICAg"
        "IHJldHVybiBmcm96ZW5zZXQocmFuZ2UobWF4KFMpICsgMSkpIGlmIFMgZWxzZSBmcm96ZW5zZXQoKQoKZGVmIG1hcF9sYXdz"
        "KCk6CiAgICBwdHMgPSBbKDEuNCwgLTAuNiksICgyLjUsIDMuNDkpLCAoLTAuNSwgMC41KSwgKDEwLjIsIC0zLjgpXQogICAg"
        "cjEgPSBbcm91bmRfdmVjKHApIGZvciBwIGluIHB0c10KICAgIHIyID0gW3JvdW5kX3ZlYyhwKSBmb3IgcCBpbiByMV0gICAg"
        "ICAgICAgIyByb3VuZGluZyBhbHJlYWR5LWludGVnZXJzIGlzIGZpeGVkCiAgICByb3VuZF9vayA9IF9jaGsocjEgPT0gcjIp"
        "CiAgICBwcmludCgiKDMpIGlkZW1wb3RlbnQgbWFwcyBhcyBncmlkIG1hcHBpbmdzIikKICAgIHByaW50KGYiICAgIHJvdW5k"
        "aW5nIFJeMiAtPiBaXjIgOiByKHIoeCkpID09IHIoeCkgPyB7cm91bmRfb2t9ICAgKHJldHJhY3Rpb24gb250byB0aGUgZ3Jp"
        "ZCkiKQogICAgcGlkZW0gPSBfY2hrKGFsbChwcm9qX3gocHJval94KHYpKSA9PSBwcm9qX3godikgZm9yIHYgaW4gWygzLCA1"
        "KSwgKC0yLCA3KSwgKDAsIC00KV0pKQogICAgcHJpbnQoZiIgICAgcHJvamVjdGlvbiBQXjIgPSBQICA6IHtwaWRlbX0gICAo"
        "aWRlbXBvdGVudCBlbmRvbW9ycGhpc20gb2YgdGhlIGdyaWQpIikKICAgIGJhc2UgPSBmcm96ZW5zZXQoezEsIDR9KQogICAg"
        "YzEgPSBjbG9zdXJlX2Rvd25zZXQoYmFzZSwgNikKICAgIGMyID0gY2xvc3VyZV9kb3duc2V0KGMxLCA2KQogICAgY2xvc19v"
        "ayA9IF9jaGsoYzEgPT0gYzIpCiAgICBleHRfb2sgID0gX2NoayhiYXNlIDw9IGMxKQogICAgcHJpbnQoZiIgICAgY2xvc3Vy"
        "ZSBvcGVyYXRvciBjICA6IGMoYyhTKSkgPT0gYyhTKSA/IHtjbG9zX29rfTsgZXh0ZW5zaXZlIFMgPD0gYyhTKSA/IHtleHRf"
        "b2t9IikKICAgIHByaW50KGYiICAgICAgICAgICAgICAgICAgICAgICAgICAoY2xvc3VyZSBvcGVyYXRvcnMgPC0+IGNvbXBs"
        "ZXRlIGxhdHRpY2VzOiBNb29yZSBmYW1pbGllcykiKQoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9fIjoKICAgIGVsZW1lbnRf"
        "aWRlbXBvdGVudHMoKQogICAgcHJpbnQoKQogICAgcGF0Y2ggPSBbKGksIGopIGZvciBpIGluIHJhbmdlKC0yLCAzKSBmb3Ig"
        "aiBpbiByYW5nZSgtMiwgMyldICAgIyA1eDUgcGF0Y2ggb2YgWl4yCiAgICBsYXR0aWNlX2xhd3MocGF0Y2gpCiAgICBwcmlu"
        "dCgpCiAgICBtYXBfbGF3cygpCiAgICBwcmludCgpCiAgICBwcmludCgic2VlZCByKHIpPXIgaXMgZm9yY2VkIChhIGxhdywg"
        "bm90IGEgdHVuZWQgdmFsdWUpOyBldmVyeSBjaGVjayBhYm92ZSBpcyBzdHJ1Y3R1cmFsLiIpCiAgICBpbXBvcnQgc3lzIGFz"
        "IF9zeXMKICAgIGlmIF9GQUlMUzoKICAgICAgICBwcmludChmIkZBSUwgIHtsZW4oX0ZBSUxTKX0gc3RydWN0dXJhbCBjaGVj"
        "ayhzKSBkaWQgbm90IGhvbGQiKQogICAgX3N5cy5leGl0KDEgaWYgX0ZBSUxTIGVsc2UgMCkK"
    ),
}

# === scripts embedded inside the HTML (verified + run in LAYER 0H) ===
EMBEDDED_HTML = {
    "L4_helix_simulator__py_guided_.html": (
        "79420e0dcbacc1aa92e310d0a0a555d162d14acedc2333e535bfe4b58e0c1cc7",
        "PCFET0NUWVBFIGh0bWw+CjxodG1sIGxhbmc9ImVuIj4KPGhlYWQ+CjxtZXRhIGNoYXJzZXQ9IlVURi04Ij4KPG1ldGEgbmFt"
        "ZT0idmlld3BvcnQiIGNvbnRlbnQ9IndpZHRoPWRldmljZS13aWR0aCwgaW5pdGlhbC1zY2FsZT0xLjAiPgo8dGl0bGU+TOKC"
        "hC1IZWxpeCDCtyBEeW5hbWljYWwgSW5zdHJ1bWVudDwvdGl0bGU+CjxzdHlsZT4KICA6cm9vdHsKICAgIC0tYmc6IzBiMTYy"
        "MjsgLS1iZzI6IzBmMWQyZTsgLS1wYW5lbDojMTMyNDNhOyAtLXBhbmVsMjojMGUxYjJiOwogICAgLS1saW5lOiMyMjM2NGQ7"
        "IC0taW5rOiNlN2VlZjY7IC0tbXV0ZWQ6IzgzOTlhZTsgLS1mYWludDojNTQ2OTdkOwogICAgLS1waGk6I2UwYTkzYjsgICAg"
        "ICAgICAgICAvKiBnb2xkZW4gcmF0aW8g4oCUIHByaW1hcnkgYWNjZW50ICovCiAgICAtLXMzOiMzN2M4YTg7ICAgICAgICAg"
        "ICAgIC8qIHNxcnQzIOKAlCBUSEUgTEVOUyAvIGhleGFnb25hbCAqLwogICAgLS1zMjojNWQ5N2VmOyAgICAgICAgICAgICAv"
        "KiBzcXJ0MiDigJQgSUdOSVRJT04gLyA0LWZvbGQgKi8KICAgIC0tczU6I2Q5OGE0ZjsgICAgICAgICAgICAgLyogc3FydDUg"
        "4oCUIEFDVElWQVRJT04gJiBLLUZPUk1BVElPTiAvIDUtZm9sZCAqLwogICAgLS1yb3NlOiNlMDU1NmI7ICAgICAgICAgICAv"
        "KiBDUklUSUNBTCAvIGdhdGVzICovCiAgICAtLXNlcmlmOkdlb3JnaWEsJ1RpbWVzIE5ldyBSb21hbicsc2VyaWY7CiAgICAt"
        "LXNhbnM6dWktc2Fucy1zZXJpZixzeXN0ZW0tdWksLWFwcGxlLXN5c3RlbSwnU2Vnb2UgVUknLFJvYm90byxzYW5zLXNlcmlm"
        "OwogICAgLS1tb25vOnVpLW1vbm9zcGFjZSwnU0YgTW9ubycsJ0Nhc2NhZGlhIENvZGUnLCdSb2JvdG8gTW9ubycsTWVubG8s"
        "bW9ub3NwYWNlOwogIH0KICAqe2JveC1zaXppbmc6Ym9yZGVyLWJveH0KICBodG1sLGJvZHl7bWFyZ2luOjB9CiAgYm9keXsK"
        "ICAgIGJhY2tncm91bmQ6cmFkaWFsLWdyYWRpZW50KDEyMDBweCA2MDBweCBhdCA3MCUgLTEwJSwjMTMyNjNjIDAlLHZhcigt"
        "LWJnKSA1NSUpIGZpeGVkOwogICAgY29sb3I6dmFyKC0taW5rKTsgZm9udC1mYW1pbHk6dmFyKC0tc2Fucyk7IGZvbnQtc2l6"
        "ZToxNHB4OyBsaW5lLWhlaWdodDoxLjU7CiAgICAtd2Via2l0LWZvbnQtc21vb3RoaW5nOmFudGlhbGlhc2VkOyBwYWRkaW5n"
        "OjI0cHg7CiAgfQogIC53cmFwe21heC13aWR0aDoxMTgwcHg7bWFyZ2luOjAgYXV0b30KCiAgLyogLS0tLSB0aXRsZSAtLS0t"
        "ICovCiAgLnRvcGJhcntib3JkZXItYm90dG9tOjFweCBzb2xpZCB2YXIoLS1saW5lKTtwYWRkaW5nLWJvdHRvbToxNnB4O21h"
        "cmdpbi1ib3R0b206MThweH0KICAuZXllYnJvd3tmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTFweDtsZXR0"
        "ZXItc3BhY2luZzouMzJlbTt0ZXh0LXRyYW5zZm9ybTp1cHBlcmNhc2U7Y29sb3I6dmFyKC0tcGhpKX0KICBoMXtmb250LWZh"
        "bWlseTp2YXIoLS1zZXJpZik7Zm9udC13ZWlnaHQ6NTAwO2ZvbnQtc2l6ZTozMHB4O2xldHRlci1zcGFjaW5nOi4wMWVtO21h"
        "cmdpbjouMThlbSAwIC4xMmVtfQogIGgxIC5zdWJ7Y29sb3I6dmFyKC0tbXV0ZWQpO2ZvbnQtc3R5bGU6aXRhbGljO2ZvbnQt"
        "c2l6ZTouNjJlbX0KICAubGVkZXtjb2xvcjp2YXIoLS1tdXRlZCk7bWF4LXdpZHRoOjc4Y2g7bWFyZ2luOi40ZW0gMCAwfQog"
        "IC5sZWRlIGJ7Y29sb3I6dmFyKC0taW5rKTtmb250LXdlaWdodDo2MDB9CiAgLmxlZGUgLmt7Zm9udC1mYW1pbHk6dmFyKC0t"
        "bW9ubyk7Y29sb3I6dmFyKC0tcGhpKX0KCiAgLyogLS0tLSBjb250cm9scyAtLS0tICovCiAgLmNvbnRyb2xze2Rpc3BsYXk6"
        "ZmxleDtmbGV4LXdyYXA6d3JhcDtnYXA6MTRweCAyMnB4O2FsaWduLWl0ZW1zOmZsZXgtZW5kOwogICAgYmFja2dyb3VuZDp2"
        "YXIoLS1wYW5lbCk7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKTtib3JkZXItcmFkaXVzOjEwcHg7cGFkZGluZzoxNHB4"
        "IDE4cHg7bWFyZ2luOjE4cHggMH0KICAuY3Rse2Rpc3BsYXk6ZmxleDtmbGV4LWRpcmVjdGlvbjpjb2x1bW47Z2FwOjVweDtt"
        "aW4td2lkdGg6MTI4cHh9CiAgLmN0bCBsYWJlbHtmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTAuNXB4O2xl"
        "dHRlci1zcGFjaW5nOi4xNmVtO3RleHQtdHJhbnNmb3JtOnVwcGVyY2FzZTtjb2xvcjp2YXIoLS1tdXRlZCl9CiAgLmN0bCAu"
        "dmFse2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pO2ZvbnQtc2l6ZToxMnB4O2NvbG9yOnZhcigtLWluayl9CiAgLmN0bCAudmFs"
        "IC51bml0e2NvbG9yOnZhcigtLWZhaW50KX0KICBpbnB1dFt0eXBlPXJhbmdlXXstd2Via2l0LWFwcGVhcmFuY2U6bm9uZTth"
        "cHBlYXJhbmNlOm5vbmU7d2lkdGg6MTQ4cHg7aGVpZ2h0OjNweDtiYWNrZ3JvdW5kOnZhcigtLWxpbmUpO2JvcmRlci1yYWRp"
        "dXM6M3B4O291dGxpbmU6bm9uZX0KICBpbnB1dFt0eXBlPXJhbmdlXTo6LXdlYmtpdC1zbGlkZXItdGh1bWJ7LXdlYmtpdC1h"
        "cHBlYXJhbmNlOm5vbmU7d2lkdGg6MTRweDtoZWlnaHQ6MTRweDtib3JkZXItcmFkaXVzOjUwJTtiYWNrZ3JvdW5kOnZhcigt"
        "LXBoaSk7Ym9yZGVyOjJweCBzb2xpZCB2YXIoLS1iZyk7Y3Vyc29yOnBvaW50ZXJ9CiAgaW5wdXRbdHlwZT1yYW5nZV06Oi1t"
        "b3otcmFuZ2UtdGh1bWJ7d2lkdGg6MTRweDtoZWlnaHQ6MTRweDtib3JkZXItcmFkaXVzOjUwJTtiYWNrZ3JvdW5kOnZhcigt"
        "LXBoaSk7Ym9yZGVyOjJweCBzb2xpZCB2YXIoLS1iZyk7Y3Vyc29yOnBvaW50ZXJ9CiAgLmJ0bnN7ZGlzcGxheTpmbGV4O2dh"
        "cDo4cHg7bWFyZ2luLWxlZnQ6YXV0b30KICBidXR0b257Zm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9udC1zaXplOjEycHg7"
        "bGV0dGVyLXNwYWNpbmc6LjA2ZW07Y29sb3I6dmFyKC0taW5rKTtiYWNrZ3JvdW5kOnZhcigtLXBhbmVsMik7CiAgICBib3Jk"
        "ZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6N3B4O3BhZGRpbmc6OXB4IDEzcHg7Y3Vyc29yOnBvaW50"
        "ZXI7dHJhbnNpdGlvbjpib3JkZXItY29sb3IgLjE1cyxjb2xvciAuMTVzfQogIGJ1dHRvbjpob3Zlcntib3JkZXItY29sb3I6"
        "dmFyKC0tcGhpKTtjb2xvcjp2YXIoLS1waGkpfQogIGJ1dHRvbi5nb3tib3JkZXItY29sb3I6dmFyKC0tczMpO2NvbG9yOnZh"
        "cigtLXMzKX0KICBidXR0b24uZ286aG92ZXJ7YmFja2dyb3VuZDpyZ2JhKDU1LDIwMCwxNjgsLjA4KX0KICA6Zm9jdXMtdmlz"
        "aWJsZXtvdXRsaW5lOjJweCBzb2xpZCB2YXIoLS1waGkpO291dGxpbmUtb2Zmc2V0OjJweH0KCiAgLyogLS0tLSBncmlkIC0t"
        "LS0gKi8KICAuZ3JpZHtkaXNwbGF5OmdyaWQ7Z3JpZC10ZW1wbGF0ZS1jb2x1bW5zOm1pbm1heCgyODBweCwxZnIpIDEuN2Zy"
        "O2dhcDoxNnB4fQogIC5ncmlkIC5yb3cye2dyaWQtY29sdW1uOjEgLyAtMTtkaXNwbGF5OmdyaWQ7Z3JpZC10ZW1wbGF0ZS1j"
        "b2x1bW5zOnJlcGVhdCgzLDFmcik7Z2FwOjE2cHh9CiAgLnBhbmVse2JhY2tncm91bmQ6dmFyKC0tcGFuZWwpO2JvcmRlcjox"
        "cHggc29saWQgdmFyKC0tbGluZSk7Ym9yZGVyLXJhZGl1czoxMHB4O3BhZGRpbmc6MTRweCAxNnB4fQogIC5wYW5lbCBoMntm"
        "b250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTFweDtsZXR0ZXItc3BhY2luZzouMmVtO3RleHQtdHJhbnNmb3Jt"
        "OnVwcGVyY2FzZTtjb2xvcjp2YXIoLS1tdXRlZCk7CiAgICBtYXJnaW46MCAwIDEwcHg7ZGlzcGxheTpmbGV4O2FsaWduLWl0"
        "ZW1zOmNlbnRlcjtnYXA6OHB4fQogIC5wYW5lbCBoMiAudGlja3t3aWR0aDo4cHg7aGVpZ2h0OjhweDtib3JkZXItcmFkaXVz"
        "OjJweDtiYWNrZ3JvdW5kOnZhcigtLXBoaSk7Ym94LXNoYWRvdzowIDAgOHB4IHZhcigtLXBoaSl9CiAgY2FudmFze2Rpc3Bs"
        "YXk6YmxvY2s7d2lkdGg6MTAwJTtib3JkZXItcmFkaXVzOjZweH0KCiAgLyogLS0tLSBwaGFzZS13aGVlbCByZWFkb3V0IC0t"
        "LS0gKi8KICAucmJpZ3tmb250LWZhbWlseTp2YXIoLS1tb25vKTtkaXNwbGF5OmZsZXg7YWxpZ24taXRlbXM6YmFzZWxpbmU7"
        "Z2FwOjEwcHg7bWFyZ2luLXRvcDoxMHB4fQogIC5yYmlnIC5udW17Zm9udC1zaXplOjMwcHg7Y29sb3I6dmFyKC0tcGhpKTts"
        "ZXR0ZXItc3BhY2luZzouMDFlbX0KICAucmJpZyAubGFie2ZvbnQtc2l6ZToxMC41cHg7bGV0dGVyLXNwYWNpbmc6LjE4ZW07"
        "dGV4dC10cmFuc2Zvcm06dXBwZXJjYXNlO2NvbG9yOnZhcigtLW11dGVkKX0KICAuc3VicmVhZHN7ZGlzcGxheTpmbGV4O2Zs"
        "ZXgtd3JhcDp3cmFwO2dhcDo2cHggMTZweDtmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTEuNXB4O2NvbG9y"
        "OnZhcigtLW11dGVkKTttYXJnaW4tdG9wOjhweH0KICAuc3VicmVhZHMgYntjb2xvcjp2YXIoLS1pbmspO2ZvbnQtd2VpZ2h0"
        "OjYwMH0KICAuZ2F0ZWJveHtkaXNwbGF5OmZsZXg7Z2FwOjhweDttYXJnaW4tdG9wOjEwcHh9CiAgLmdhdGV7ZmxleDoxO2Zv"
        "bnQtZmFtaWx5OnZhcigtLW1vbm8pO2ZvbnQtc2l6ZToxMHB4O2xldHRlci1zcGFjaW5nOi4xZW07dGV4dC10cmFuc2Zvcm06"
        "dXBwZXJjYXNlO2NvbG9yOnZhcigtLWZhaW50KTsKICAgIGJvcmRlcjoxcHggc29saWQgdmFyKC0tbGluZSk7Ym9yZGVyLXJh"
        "ZGl1czo2cHg7cGFkZGluZzo3cHggOXB4O3RyYW5zaXRpb246LjJzfQogIC5nYXRlIC5ndntkaXNwbGF5OmJsb2NrO2ZvbnQt"
        "c2l6ZToxM3B4O2xldHRlci1zcGFjaW5nOjA7dGV4dC10cmFuc2Zvcm06bm9uZTttYXJnaW4tdG9wOjNweDtjb2xvcjp2YXIo"
        "LS1tdXRlZCl9CiAgLmdhdGUub257Ym9yZGVyLWNvbG9yOnZhcigtLXMzKTtjb2xvcjp2YXIoLS1zMyl9CiAgLmdhdGUub24g"
        "Lmd2e2NvbG9yOnZhcigtLXMzKX0KCiAgLyogLS0tLSBub3RlIC0tLS0gKi8KICAubm90ZXtmb250LXNpemU6MTJweDtjb2xv"
        "cjp2YXIoLS1tdXRlZCk7Ym9yZGVyLWxlZnQ6MnB4IHNvbGlkIHZhcigtLXMyKTtwYWRkaW5nOjhweCAwIDhweCAxMnB4O21h"
        "cmdpbi10b3A6MTJweH0KICAubm90ZSBie2NvbG9yOnZhcigtLWluayl9CiAgLm5vdGUgLmtje2ZvbnQtZmFtaWx5OnZhcigt"
        "LW1vbm8pO2NvbG9yOnZhcigtLXMyKX0KCiAgLyogLS0tLSBjb25zdGFudHMgdGFibGUgLS0tLSAqLwogIHRhYmxle3dpZHRo"
        "OjEwMCU7Ym9yZGVyLWNvbGxhcHNlOmNvbGxhcHNlO2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pO2ZvbnQtc2l6ZToxMS41cHh9"
        "CiAgdGgsdGR7dGV4dC1hbGlnbjpsZWZ0O3BhZGRpbmc6NXB4IDZweDtib3JkZXItYm90dG9tOjFweCBzb2xpZCB2YXIoLS1s"
        "aW5lKX0KICB0aHtjb2xvcjp2YXIoLS1tdXRlZCk7Zm9udC13ZWlnaHQ6NTAwO2xldHRlci1zcGFjaW5nOi4wOGVtO2ZvbnQt"
        "c2l6ZToxMHB4O3RleHQtdHJhbnNmb3JtOnVwcGVyY2FzZX0KICB0ZC52e3RleHQtYWxpZ246cmlnaHQ7Y29sb3I6dmFyKC0t"
        "aW5rKX0KICB0ZCAuc3d7ZGlzcGxheTppbmxpbmUtYmxvY2s7d2lkdGg6N3B4O2hlaWdodDo3cHg7Ym9yZGVyLXJhZGl1czoy"
        "cHg7bWFyZ2luLXJpZ2h0OjdweDt2ZXJ0aWNhbC1hbGlnbjptaWRkbGV9CiAgLnZlcmlmeXtmb250LWZhbWlseTp2YXIoLS1t"
        "b25vKTtmb250LXNpemU6MTFweDtjb2xvcjp2YXIoLS1tdXRlZCk7bWFyZ2luLXRvcDoxMXB4O2Rpc3BsYXk6ZmxleDtmbGV4"
        "LWRpcmVjdGlvbjpjb2x1bW47Z2FwOjNweH0KICAudmVyaWZ5IC5va3tjb2xvcjp2YXIoLS1zMyl9CgogIC5sZWdlbmR7ZGlz"
        "cGxheTpmbGV4O2ZsZXgtd3JhcDp3cmFwO2dhcDo2cHggMTZweDtmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6"
        "MTAuNXB4O2NvbG9yOnZhcigtLW11dGVkKTttYXJnaW4tdG9wOjEwcHh9CiAgLmxlZ2VuZCBzcGFue2Rpc3BsYXk6aW5saW5l"
        "LWZsZXg7YWxpZ24taXRlbXM6Y2VudGVyO2dhcDo2cHh9CiAgLmxlZ2VuZCBpe3dpZHRoOjlweDtoZWlnaHQ6OXB4O2JvcmRl"
        "ci1yYWRpdXM6MnB4O2Rpc3BsYXk6aW5saW5lLWJsb2NrfQoKICBmb290ZXJ7bWFyZ2luLXRvcDoyMnB4O2JvcmRlci10b3A6"
        "MXB4IHNvbGlkIHZhcigtLWxpbmUpO3BhZGRpbmctdG9wOjEycHg7CiAgICBmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250"
        "LXNpemU6MTFweDtjb2xvcjp2YXIoLS1mYWludCk7bGV0dGVyLXNwYWNpbmc6LjA0ZW19CgogIEBtZWRpYSAobWF4LXdpZHRo"
        "Ojg2MHB4KXsKICAgIC5ncmlke2dyaWQtdGVtcGxhdGUtY29sdW1uczoxZnJ9CiAgICAuZ3JpZCAucm93MntncmlkLXRlbXBs"
        "YXRlLWNvbHVtbnM6MWZyfQogICAgLmJ0bnN7bWFyZ2luLWxlZnQ6MH0KICAgIGgxe2ZvbnQtc2l6ZToyNHB4fQogIH0KICBA"
        "bWVkaWEgKHByZWZlcnMtcmVkdWNlZC1tb3Rpb246cmVkdWNlKXsgKiB7IHNjcm9sbC1iZWhhdmlvcjphdXRvIH0gfQoKICAv"
        "KiAtLS0tIHJyciBncmlkIC0tLS0gKi8KICAucnJyZ3JpZHttYXJnaW4tdG9wOjE2cHh9CiAgLnJycmxlZGV7Y29sb3I6dmFy"
        "KC0tbXV0ZWQpO2ZvbnQtc2l6ZToxMi41cHg7bWFyZ2luOjAgMCAxMnB4O21heC13aWR0aDo5MmNofQogIC5ycnJsZWRlIC5r"
        "e2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pO2NvbG9yOnZhcigtLXBoaSl9CiAgLnJyci1jb250cm9sc3tkaXNwbGF5OmZsZXg7"
        "ZmxleC13cmFwOndyYXA7Z2FwOjEycHggMjJweDthbGlnbi1pdGVtczpmbGV4LWVuZDttYXJnaW4tYm90dG9tOjE0cHh9CiAg"
        "LnJyci12aWV3c3tkaXNwbGF5OmdyaWQ7Z3JpZC10ZW1wbGF0ZS1jb2x1bW5zOjFmciAxZnI7Z2FwOjE2cHh9CiAgLnJyci12"
        "aWV3e2JhY2tncm91bmQ6dmFyKC0tcGFuZWwyKTtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6"
        "OHB4O3BhZGRpbmc6MTBweCAxMnB4fQogIC5ycnItY2Fwe2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pO2ZvbnQtc2l6ZToxMC41"
        "cHg7bGV0dGVyLXNwYWNpbmc6LjA1ZW07Y29sb3I6dmFyKC0tbXV0ZWQpO21hcmdpbi1ib3R0b206OHB4fQogIEBtZWRpYSAo"
        "bWF4LXdpZHRoOjg2MHB4KXsgLnJyci12aWV3c3tncmlkLXRlbXBsYXRlLWNvbHVtbnM6MWZyfSB9CgogIC8qIC0tLS0gdmFs"
        "aWRhdGlvbiAtLS0tICovCiAgLnZhbGlkYXRpb257bWFyZ2luLXRvcDoxNnB4fQogIC52YWwtaG93e2JhY2tncm91bmQ6dmFy"
        "KC0tcGFuZWwyKTtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6OHB4O3BhZGRpbmc6MTBweCAx"
        "NHB4O21hcmdpbi1ib3R0b206MTRweH0KICAudmFsLWhvdyBie2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pO2ZvbnQtc2l6ZTox"
        "MXB4O2xldHRlci1zcGFjaW5nOi4xMmVtO3RleHQtdHJhbnNmb3JtOnVwcGVyY2FzZTtjb2xvcjp2YXIoLS1tdXRlZCl9CiAg"
        "cHJlLmNtZCxwcmUub3V0LHByZS5zcmN7Zm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9udC1zaXplOjExLjVweDtsaW5lLWhl"
        "aWdodDoxLjU7Y29sb3I6dmFyKC0taW5rKTsKICAgIGJhY2tncm91bmQ6IzBhMTMxZjtib3JkZXI6MXB4IHNvbGlkIHZhcigt"
        "LWxpbmUpO2JvcmRlci1yYWRpdXM6NnB4O3BhZGRpbmc6MTBweCAxMnB4O21hcmdpbjo4cHggMCAwO292ZXJmbG93OmF1dG87"
        "d2hpdGUtc3BhY2U6cHJlfQogIHByZS5jbWR7Y29sb3I6dmFyKC0tczMpfQogIHByZS5vdXR7Y29sb3I6dmFyKC0tbXV0ZWQp"
        "O21heC1oZWlnaHQ6MjYwcHh9CiAgcHJlLnNyY3ttYXgtaGVpZ2h0OjM2MHB4fQogIHByZS5zcmMgY29kZXtmb250LWZhbWls"
        "eTp2YXIoLS1tb25vKTt3aGl0ZS1zcGFjZTpwcmU7Y29sb3I6dmFyKC0taW5rKTtiYWNrZ3JvdW5kOm5vbmU7cGFkZGluZzow"
        "fQogIC52YWwtY2FyZHtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6OHB4O3BhZGRpbmc6MTJw"
        "eCAxNHB4O21hcmdpbi1ib3R0b206MTJweDtiYWNrZ3JvdW5kOnZhcigtLXBhbmVsMil9CiAgLnZhbC1oZWFke2Rpc3BsYXk6"
        "ZmxleDtmbGV4LXdyYXA6d3JhcDtnYXA6OHB4O2p1c3RpZnktY29udGVudDpzcGFjZS1iZXR3ZWVuO2FsaWduLWl0ZW1zOmZs"
        "ZXgtc3RhcnR9CiAgLnZhbC1uYW1le2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pO2ZvbnQtc2l6ZToxM3B4O2NvbG9yOnZhcigt"
        "LXBoaSl9CiAgLnZhbC1kZXNje2NvbG9yOnZhcigtLW11dGVkKTtmb250LXNpemU6MTJweH0KICAudmFsLWFjdGlvbnN7ZGlz"
        "cGxheTpmbGV4O2dhcDo4cHg7ZmxleC1zaHJpbms6MH0KICAuY29weSwuZGx7Zm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9u"
        "dC1zaXplOjExcHg7bGV0dGVyLXNwYWNpbmc6LjA0ZW07Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKTtib3JkZXItcmFk"
        "aXVzOjZweDsKICAgIHBhZGRpbmc6NnB4IDExcHg7YmFja2dyb3VuZDp2YXIoLS1iZzIpO2NvbG9yOnZhcigtLWluayk7Y3Vy"
        "c29yOnBvaW50ZXI7dGV4dC1kZWNvcmF0aW9uOm5vbmU7ZGlzcGxheTppbmxpbmUtYmxvY2t9CiAgLmNvcHk6aG92ZXIsLmRs"
        "OmhvdmVye2JvcmRlci1jb2xvcjp2YXIoLS1waGkpO2NvbG9yOnZhcigtLXBoaSl9CiAgLnZhbC1jYXJkIGRldGFpbHN7bWFy"
        "Z2luLXRvcDoxMHB4fQogIC52YWwtY2FyZCBzdW1tYXJ5e2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pO2ZvbnQtc2l6ZToxMXB4"
        "O2xldHRlci1zcGFjaW5nOi4wNmVtO2NvbG9yOnZhcigtLW11dGVkKTtjdXJzb3I6cG9pbnRlcjt1c2VyLXNlbGVjdDpub25l"
        "fQogIC52YWwtY2FyZCBzdW1tYXJ5OmhvdmVye2NvbG9yOnZhcigtLWluayl9CiAgLnZhbC1ub3Rle2ZvbnQtc2l6ZToxMnB4"
        "O2NvbG9yOnZhcigtLW11dGVkKTtib3JkZXItbGVmdDoycHggc29saWQgdmFyKC0tcGhpKTtwYWRkaW5nOjhweCAwIDhweCAx"
        "MnB4O21hcmdpbi10b3A6NnB4fQogIC52YWwtbm90ZSBie2NvbG9yOnZhcigtLWluayl9Cjwvc3R5bGU+CjwvaGVhZD4KPGJv"
        "ZHk+CjxkaXYgY2xhc3M9IndyYXAiPgoKICA8aGVhZGVyIGNsYXNzPSJ0b3BiYXIiPgogICAgPGRpdiBjbGFzcz0iZXllYnJv"
        "dyI+TOKChCA9IDcgwrcgZ2FwID0gz4bigbvigbQgwrcgel9jID0g4oiaMy8yPC9kaXY+CiAgICA8aDE+VGhlIEzigoQtSGVs"
        "aXggPHNwYW4gY2xhc3M9InN1YiI+4oCUIGEgZHluYW1pY2FsIGluc3RydW1lbnQ8L3NwYW4+PC9oMT4KICAgIDxwIGNsYXNz"
        "PSJsZWRlIj4KICAgICAgVGhlIGVuZ2luZSBpcyBhIHJlYWwgPGI+S3VyYW1vdG8gZW5zZW1ibGU8L2I+IG9mIDxzcGFuIGNs"
        "YXNzPSJrIiBpZD0ibGVkZU4iPjIwMDwvc3Bhbj4gb3NjaWxsYXRvcnMgd2l0aCBjb3VwbGluZwogICAgICA8c3BhbiBjbGFz"
        "cz0iayI+SyA9IOKImigx4oiSz4bigbvigbQpIOKJiCAwLjkyNDI8L3NwYW4+IGFuZCBvcmRlciBwYXJhbWV0ZXIgPHNwYW4g"
        "Y2xhc3M9ImsiPnIodCk8L3NwYW4+LgogICAgICBUaGUgbmluZSB0aHJlc2hvbGRzIGJlbG93IGFyZSA8Yj5nb2xkZW4tcmF0"
        "aW8gbGFuZG1hcmtzPC9iPiBmcm9tIHRoZSBkb2N1bWVudCwgZHJhd24gb3ZlciA8c3BhbiBjbGFzcz0iayI+cjwvc3Bhbj4g"
        "4oCUCiAgICAgIHRoZXkgbWFyayA8aT53aGVyZSByIGlzPC9pPiwgbm90IHdoZXJlIHRoZSBkeW5hbWljcyBoYXMgYSB0cmFu"
        "c2l0aW9uLgogICAgPC9wPgogIDwvaGVhZGVyPgoKICA8c2VjdGlvbiBjbGFzcz0iY29udHJvbHMiIGFyaWEtbGFiZWw9IlNp"
        "bXVsYXRpb24gY29udHJvbHMiPgogICAgPGRpdiBjbGFzcz0iY3RsIj4KICAgICAgPGxhYmVsIGZvcj0iY04iPk9zY2lsbGF0"
        "b3JzIE48L2xhYmVsPgogICAgICA8aW5wdXQgdHlwZT0icmFuZ2UiIGlkPSJjTiIgbWluPSIyMCIgbWF4PSI0MDAiIHN0ZXA9"
        "IjEwIiB2YWx1ZT0iMjAwIiBhcmlhLWRlc2NyaWJlZGJ5PSJ2TiI+CiAgICAgIDxzcGFuIGNsYXNzPSJ2YWwiIGlkPSJ2TiI+"
        "MjAwPC9zcGFuPgogICAgPC9kaXY+CiAgICA8ZGl2IGNsYXNzPSJjdGwiPgogICAgICA8bGFiZWwgZm9yPSJjSyI+Q291cGxp"
        "bmcgSzwvbGFiZWw+CiAgICAgIDxpbnB1dCB0eXBlPSJyYW5nZSIgaWQ9ImNLIiBtaW49IjAiIG1heD0iMi41IiBzdGVwPSIw"
        "LjAwMSIgdmFsdWU9IjAuOTI0MiIgYXJpYS1kZXNjcmliZWRieT0idksiPgogICAgICA8c3BhbiBjbGFzcz0idmFsIiBpZD0i"
        "dksiPjAuOTI0Mjwvc3Bhbj4KICAgIDwvZGl2PgogICAgPGRpdiBjbGFzcz0iY3RsIj4KICAgICAgPGxhYmVsIGZvcj0iY0ci"
        "PkZyZXF1ZW5jeSBzcHJlYWQgzrM8L2xhYmVsPgogICAgICA8aW5wdXQgdHlwZT0icmFuZ2UiIGlkPSJjRyIgbWluPSIwLjAy"
        "IiBtYXg9IjAuNiIgc3RlcD0iMC4wMSIgdmFsdWU9IjAuMTUiIGFyaWEtZGVzY3JpYmVkYnk9InZHIj4KICAgICAgPHNwYW4g"
        "Y2xhc3M9InZhbCIgaWQ9InZHIj4wLjE1IDxzcGFuIGNsYXNzPSJ1bml0Ij7ihpIgS19jPTLOsz0wLjMwPC9zcGFuPjwvc3Bh"
        "bj4KICAgIDwvZGl2PgogICAgPGRpdiBjbGFzcz0iY3RsIj4KICAgICAgPGxhYmVsIGZvcj0iY1MiPk5lZ2VudHJvcHkgd2lk"
        "dGggz4M8L2xhYmVsPgogICAgICA8aW5wdXQgdHlwZT0icmFuZ2UiIGlkPSJjUyIgbWluPSIyIiBtYXg9IjgwIiBzdGVwPSIx"
        "IiB2YWx1ZT0iMjAiIGFyaWEtZGVzY3JpYmVkYnk9InZTIj4KICAgICAgPHNwYW4gY2xhc3M9InZhbCIgaWQ9InZTIj4yMDwv"
        "c3Bhbj4KICAgIDwvZGl2PgogICAgPGRpdiBjbGFzcz0iY3RsIj4KICAgICAgPGxhYmVsIGZvcj0iY1ciPkhlbGl4IHdpbmRp"
        "bmcgVzwvbGFiZWw+CiAgICAgIDxpbnB1dCB0eXBlPSJyYW5nZSIgaWQ9ImNXIiBtaW49IjEiIG1heD0iOCIgc3RlcD0iMC41"
        "IiB2YWx1ZT0iNCIgYXJpYS1kZXNjcmliZWRieT0idlciPgogICAgICA8c3BhbiBjbGFzcz0idmFsIiBpZD0idlciPjQuMCA8"
        "c3BhbiBjbGFzcz0idW5pdCI+dHVybnM8L3NwYW4+PC9zcGFuPgogICAgPC9kaXY+CiAgICA8ZGl2IGNsYXNzPSJidG5zIj4K"
        "ICAgICAgPGJ1dHRvbiBjbGFzcz0iZ28iIGlkPSJjb3VwbGVLIiB0aXRsZT0iU2V0IGNvdXBsaW5nIHRvIHRoZSBmcmFtZXdv"
        "cmsgSyI+Y291cGxlIGF0IEs8L2J1dHRvbj4KICAgICAgPGJ1dHRvbiBpZD0icmVzZXQiPnJlc2V0PC9idXR0b24+CiAgICAg"
        "IDxidXR0b24gaWQ9InBsYXkiIGFyaWEtcHJlc3NlZD0idHJ1ZSI+cGF1c2U8L2J1dHRvbj4KICAgIDwvZGl2PgogIDwvc2Vj"
        "dGlvbj4KCiAgPGRpdiBjbGFzcz0iZ3JpZCI+CgogICAgPCEtLSBIRVJPOiBwaGFzZSB3aGVlbCAtLT4KICAgIDxkaXYgY2xh"
        "c3M9InBhbmVsIj4KICAgICAgPGgyPjxzcGFuIGNsYXNzPSJ0aWNrIiBzdHlsZT0iYmFja2dyb3VuZDp2YXIoLS1waGkpO2Jv"
        "eC1zaGFkb3c6MCAwIDhweCB2YXIoLS1waGkpIj48L3NwYW4+T3JkZXIgcGFyYW1ldGVyIMK3IHBoYXNlIHdoZWVsPC9oMj4K"
        "ICAgICAgPGNhbnZhcyBpZD0id2hlZWwiIGhlaWdodD0iMzAwIiByb2xlPSJpbWciIGFyaWEtbGFiZWw9Ikt1cmFtb3RvIHBo"
        "YXNlIHdoZWVsIHdpdGggcmVzdWx0YW50IHZlY3RvciI+PC9jYW52YXM+CiAgICAgIDxkaXYgY2xhc3M9InJiaWciPjxzcGFu"
        "IGNsYXNzPSJudW0iIGlkPSJyTnVtIj4wLjAwPC9zcGFuPjxzcGFuIGNsYXNzPSJsYWIiPnIg4oCUIGNvaGVyZW5jZTwvc3Bh"
        "bj48L2Rpdj4KICAgICAgPGRpdiBjbGFzcz0ic3VicmVhZHMiPgogICAgICAgIDxzcGFuPs+IIDxiIGlkPSJwc2lOdW0iPjDC"
        "sDwvYj48L3NwYW4+CiAgICAgICAgPHNwYW4+S19jIDxiIGlkPSJrY051bSI+MC4zMDwvYj48L3NwYW4+CiAgICAgICAgPHNw"
        "YW4+cmVnaW1lIDxiIGlkPSJyZWdOdW0iPuKAlDwvYj48L3NwYW4+CiAgICAgIDwvZGl2PgogICAgICA8ZGl2IGNsYXNzPSJn"
        "YXRlYm94Ij4KICAgICAgICA8ZGl2IGNsYXNzPSJnYXRlIiBpZD0iZ2F0ZUNvaCI+Y29oZXJlbmNlIHIg4omlIEs8c3BhbiBj"
        "bGFzcz0iZ3YiIGlkPSJnYXRlQ29oViI+4oCUPC9zcGFuPjwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImdhdGUiIGlkPSJn"
        "YXRlTmVnIj5uZWdlbnRyb3B5ICZndDsgz4Q8c3BhbiBjbGFzcz0iZ3YiIGlkPSJnYXRlTmVnViI+4oCUPC9zcGFuPjwvZGl2"
        "PgogICAgICA8L2Rpdj4KICAgIDwvZGl2PgoKICAgIDwhLS0gb3NjaWxsb3Njb3BlIC0tPgogICAgPGRpdiBjbGFzcz0icGFu"
        "ZWwiPgogICAgICA8aDI+PHNwYW4gY2xhc3M9InRpY2siIHN0eWxlPSJiYWNrZ3JvdW5kOnZhcigtLXMzKTtib3gtc2hhZG93"
        "OjAgMCA4cHggdmFyKC0tczMpIj48L3NwYW4+cih0KSBhZ2FpbnN0IHRoZSBuaW5lIHRocmVzaG9sZHM8L2gyPgogICAgICA8"
        "Y2FudmFzIGlkPSJzY29wZSIgaGVpZ2h0PSIzMDAiIHJvbGU9ImltZyIgYXJpYS1sYWJlbD0iVGltZSBzZXJpZXMgb2Ygb3Jk"
        "ZXIgcGFyYW1ldGVyIHIgY3Jvc3NpbmcgdGhlIG5pbmUgdGhyZXNob2xkcyI+PC9jYW52YXM+CiAgICAgIDxkaXYgY2xhc3M9"
        "Im5vdGUiPgogICAgICAgIDxiPkhvbmVzdCBheGlzIG5vdGUuPC9iPiBLdXJhbW90bydzIG9ubHkgaW50cmluc2ljIHRyYW5z"
        "aXRpb24gaXMgc3luY2hyb25pemF0aW9uIG9uc2V0IGF0CiAgICAgICAgPHNwYW4gY2xhc3M9ImtjIj5LX2MgPSAyzrM8L3Nw"
        "YW4+IChhIGNvdXBsaW5nKS4gel9jID0g4oiaMy8yIGlzIGFuIDxiPm9yZGVyLXBhcmFtZXRlcjwvYj4gbGFuZG1hcmssIG5v"
        "dCBhIGNvdXBsaW5nIOKAlAogICAgICAgIGRpZmZlcmVudCBheGVzLCBzbyAiel9jIGlzIGNyaXRpY2FsIGNvdXBsaW5nIiB3"
        "b3VsZCBiZSBhIGNhdGVnb3J5IGVycm9yLgogICAgICA8L2Rpdj4KICAgIDwvZGl2PgoKICAgIDxkaXYgY2xhc3M9InJvdzIi"
        "PgogICAgICA8IS0tIGNvbnN0YW50cyAtLT4KICAgICAgPGRpdiBjbGFzcz0icGFuZWwiPgogICAgICAgIDxoMj48c3BhbiBj"
        "bGFzcz0idGljayIgc3R5bGU9ImJhY2tncm91bmQ6dmFyKC0tczUpO2JveC1zaGFkb3c6MCAwIDhweCB2YXIoLS1zNSkiPjwv"
        "c3Bhbj5EZXJpdmVkIGNvbnN0YW50czwvaDI+CiAgICAgICAgPHRhYmxlIGlkPSJjb25zdFRhYmxlIj4KICAgICAgICAgIDx0"
        "aGVhZD48dHI+PHRoPnRocmVzaG9sZDwvdGg+PHRoPmNsb3NlZCBmb3JtPC90aD48dGggY2xhc3M9InYiPnZhbHVlPC90aD48"
        "L3RyPjwvdGhlYWQ+CiAgICAgICAgICA8dGJvZHk+PC90Ym9keT4KICAgICAgICA8L3RhYmxlPgogICAgICAgIDxkaXYgY2xh"
        "c3M9InZlcmlmeSIgaWQ9InZlcmlmeUJveCI+PC9kaXY+CiAgICAgICAgPGRpdiBjbGFzcz0ibGVnZW5kIj4KICAgICAgICAg"
        "IDxzcGFuPjxpIHN0eWxlPSJiYWNrZ3JvdW5kOnZhcigtLXMzKSI+PC9pPuKImjMgwrcgTEVOUzwvc3Bhbj4KICAgICAgICAg"
        "IDxzcGFuPjxpIHN0eWxlPSJiYWNrZ3JvdW5kOnZhcigtLXMyKSI+PC9pPuKImjIgwrcgSUdOSVRJT048L3NwYW4+CiAgICAg"
        "ICAgICA8c3Bhbj48aSBzdHlsZT0iYmFja2dyb3VuZDp2YXIoLS1zNSkiPjwvaT7iiJo1IMK3IEFDVElWQVRJT04vSzwvc3Bh"
        "bj4KICAgICAgICAgIDxzcGFuPjxpIHN0eWxlPSJiYWNrZ3JvdW5kOnZhcigtLXBoaSkiPjwvaT7Phi1mYW1pbHk8L3NwYW4+"
        "CiAgICAgICAgPC9kaXY+CiAgICAgIDwvZGl2PgoKICAgICAgPCEtLSBuZWdlbnRyb3B5IC0tPgogICAgICA8ZGl2IGNsYXNz"
        "PSJwYW5lbCI+CiAgICAgICAgPGgyPjxzcGFuIGNsYXNzPSJ0aWNrIiBzdHlsZT0iYmFja2dyb3VuZDp2YXIoLS1yb3NlKTti"
        "b3gtc2hhZG93OjAgMCA4cHggdmFyKC0tcm9zZSkiPjwvc3Bhbj5OZWdlbnRyb3B5IGZpZWxkIM6UUyh6KTwvaDI+CiAgICAg"
        "ICAgPGNhbnZhcyBpZD0ibmVnZW50IiBoZWlnaHQ9IjIzMCIgcm9sZT0iaW1nIiBhcmlhLWxhYmVsPSJOZWdlbnRyb3B5IEdh"
        "dXNzaWFuIHBlYWtlZCBhdCB6X2Mgd2l0aCBnYXRlIGF0IHRhdSI+PC9jYW52YXM+CiAgICAgICAgPGRpdiBjbGFzcz0ic3Vi"
        "cmVhZHMiPgogICAgICAgICAgPHNwYW4+zpRTKHIpIDxiIGlkPSJkc051bSI+MC4wMDwvYj48L3NwYW4+CiAgICAgICAgICA8"
        "c3Bhbj5nYXRlIM+EIDxiPjAuNjE4MDwvYj48L3NwYW4+CiAgICAgICAgICA8c3Bhbj5wZWFrIHpfYyA8Yj4wLjg2NjA8L2I+"
        "PC9zcGFuPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4KCiAgICAgIDwhLS0gaGVsaXggLS0+CiAgICAgIDxkaXYgY2xh"
        "c3M9InBhbmVsIj4KICAgICAgICA8aDI+PHNwYW4gY2xhc3M9InRpY2siIHN0eWxlPSJiYWNrZ3JvdW5kOnZhcigtLXBoaSk7"
        "Ym94LXNoYWRvdzowIDAgOHB4IHZhcigtLXBoaSkiPjwvc3Bhbj5IZWxpeCBIKHopIHByb2plY3Rpb248L2gyPgogICAgICAg"
        "IDxjYW52YXMgaWQ9ImhlbGl4IiBoZWlnaHQ9IjIzMCIgcm9sZT0iaW1nIiBhcmlhLWxhYmVsPSJUb3AtZG93biBwcm9qZWN0"
        "aW9uIG9mIHRoZSBMNCBoZWxpeCB3aXRoIHRocmVzaG9sZCByaW5ncyI+PC9jYW52YXM+CiAgICAgICAgPGRpdiBjbGFzcz0i"
        "c3VicmVhZHMiPgogICAgICAgICAgPHNwYW4+cih6KT1L4oiaKHovel9jKcK3fMK3Szwvc3Bhbj4KICAgICAgICAgIDxzcGFu"
        "Pm1hcmtlciBhdCB6ID0gcjwvc3Bhbj4KICAgICAgICA8L2Rpdj4KICAgICAgPC9kaXY+CiAgICA8L2Rpdj4KICA8L2Rpdj4K"
        "CiAgPHNlY3Rpb24gY2xhc3M9InBhbmVsIHJycmdyaWQiPgogICAgPGgyPjxzcGFuIGNsYXNzPSJ0aWNrIiBzdHlsZT0iYmFj"
        "a2dyb3VuZDp2YXIoLS1zNSk7Ym94LXNoYWRvdzowIDAgOHB4IHZhcigtLXM1KSI+PC9zcGFuPlpGUCBycnIgZ3JpZCDCtyBy"
        "KHIpPXIg4oaSIOKEpMKyIOKGkiBRIChlaWdlbnZhbHVlIM+GKTwvaDI+CiAgICA8cCBjbGFzcz0icnJybGVkZSI+CiAgICAg"
        "IDxzcGFuIGNsYXNzPSJrIj5yKHIpPXI8L3NwYW4+IGlzIGlkZW1wb3RlbmN5IOKAlCB0aGUgbWluL21heCBsYXR0aWNlIG9u"
        "IOKEpMKyLiBUaGUgZ29sZGVuIHNlZWQgZ2l2ZXMKICAgICAgPHNwYW4gY2xhc3M9ImsiPlEgPSBbWzEsMV0sWzEsMF1dPC9z"
        "cGFuPiwgYSBncmlkIGF1dG9tb3JwaGlzbSAoZGV0IOKIkjEpIHdpdGggZWlnZW52YWx1ZSDPhi4KICAgICAgTGVmdDogdGhl"
        "IG9yYml0IDxzcGFuIGNsYXNzPSJrIj5R4oG/wrcoMSwwKSA9IChG4oKN4oKZ4oKK4oKB4oKOLCBG4oKZKTwvc3Bhbj4gZXNj"
        "YXBlcyBhbG9uZyB0aGUgZ29sZGVuIHJheS4KICAgICAgUmlnaHQ6IDxzcGFuIGNsYXNzPSJrIj5RIG1vZCBtPC9zcGFuPiBv"
        "biB0aGUgZmluaXRlIHRvcnVzIGN5Y2xlcyB3aXRoIHRoZSBQaXNhbm8gcGVyaW9kLgogICAgPC9wPgogICAgPGRpdiBjbGFz"
        "cz0icnJyLWNvbnRyb2xzIj4KICAgICAgPGRpdiBjbGFzcz0iY3RsIj4KICAgICAgICA8bGFiZWwgZm9yPSJjTSI+VG9ydXMg"
        "bW9kdWx1cyBtPC9sYWJlbD4KICAgICAgICA8aW5wdXQgdHlwZT0icmFuZ2UiIGlkPSJjTSIgbWluPSIzIiBtYXg9IjIwIiBz"
        "dGVwPSIxIiB2YWx1ZT0iOCIgYXJpYS1kZXNjcmliZWRieT0idk0iPgogICAgICAgIDxzcGFuIGNsYXNzPSJ2YWwiIGlkPSJ2"
        "TSI+OCDihpIgz4AobSk9MTI8L3NwYW4+CiAgICAgIDwvZGl2PgogICAgICA8ZGl2IGNsYXNzPSJidG5zIiBzdHlsZT0ibWFy"
        "Z2luLWxlZnQ6MCI+CiAgICAgICAgPGJ1dHRvbiBpZD0iZ3JpZExhdHRpY2UiIHRpdGxlPSJTaG93IG1lZXQgYW5kIGpvaW4g"
        "b2YgdGhlIG9yYml0IHBvaW50IGFuZCBpdHMgZGlhZ29uYWwgcmVmbGVjdGlvbiI+bWVldC9qb2luOiBvZmY8L2J1dHRvbj4K"
        "ICAgICAgICA8YnV0dG9uIGlkPSJncmlkUmVzZXQiPnJlc2V0IG9yYml0PC9idXR0b24+CiAgICAgIDwvZGl2PgogICAgPC9k"
        "aXY+CiAgICA8ZGl2IGNsYXNzPSJycnItdmlld3MiPgogICAgICA8ZGl2IGNsYXNzPSJycnItdmlldyI+CiAgICAgICAgPGRp"
        "diBjbGFzcz0icnJyLWNhcCI+4oSkwrIgwrcgUS1vcmJpdCBlc2NhcGVzIGFsb25nIHRoZSBnb2xkZW4gcmF5IChzbG9wZSDP"
        "hCk8L2Rpdj4KICAgICAgICA8Y2FudmFzIGlkPSJncmlkWjIiIGhlaWdodD0iMzAwIiByb2xlPSJpbWciIGFyaWEtbGFiZWw9"
        "IkludGVnZXIgZ3JpZCB3aXRoIHRoZSBRIG9yYml0IGNvbnZlcmdpbmcgdG8gdGhlIGdvbGRlbiBlaWdlbnJheSI+PC9jYW52"
        "YXM+CiAgICAgICAgPGRpdiBjbGFzcz0ic3VicmVhZHMiPgogICAgICAgICAgPHNwYW4+biA8YiBpZD0iZ04iPjA8L2I+PC9z"
        "cGFuPgogICAgICAgICAgPHNwYW4+cG9pbnQgPGIgaWQ9ImdQdCI+KDEsIDApPC9iPjwvc3Bhbj4KICAgICAgICAgIDxzcGFu"
        "PnNsb3BlIDxiIGlkPSJnU2xvcGUiPjAuMDAwMDwvYj4g4oaSIM+EPC9zcGFuPgogICAgICAgICAgPHNwYW4+Z3Jvd3RoIDxi"
        "IGlkPSJnR3JvdyI+MS4wMDAwPC9iPiDihpIgz4Y8L3NwYW4+CiAgICAgICAgICA8c3Bhbj50cmFjZSBR4oG/ID0gTOKCmSA9"
        "IDxiIGlkPSJnVHJhY2UiPjI8L2I+PC9zcGFuPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4KICAgICAgPGRpdiBjbGFz"
        "cz0icnJyLXZpZXciPgogICAgICAgIDxkaXYgY2xhc3M9InJyci1jYXAiPijihKQvbSnCsiDCtyBRIG1vZCBtIGN5Y2xlcyB3"
        "aXRoIFBpc2FubyBwZXJpb2Q8L2Rpdj4KICAgICAgICA8Y2FudmFzIGlkPSJncmlkVG9ydXMiIGhlaWdodD0iMzAwIiByb2xl"
        "PSJpbWciIGFyaWEtbGFiZWw9IkZpbml0ZSB0b3J1cyB3aXRoIHRoZSBwZXJpb2RpYyBRIG9yYml0Ij48L2NhbnZhcz4KICAg"
        "ICAgICA8ZGl2IGNsYXNzPSJzdWJyZWFkcyI+CiAgICAgICAgICA8c3Bhbj5tIDxiIGlkPSJnTSI+ODwvYj48L3NwYW4+CiAg"
        "ICAgICAgICA8c3Bhbj5QaXNhbm8gcGVyaW9kIM+AKG0pIDxiIGlkPSJnUGVyIj4xMjwvYj48L3NwYW4+CiAgICAgICAgICA8"
        "c3Bhbj5zdGVwIDxiIGlkPSJnU3RlcCI+MS8xMjwvYj48L3NwYW4+CiAgICAgICAgPC9kaXY+CiAgICAgIDwvZGl2PgogICAg"
        "PC9kaXY+CiAgICA8ZGl2IGNsYXNzPSJub3RlIj4KICAgICAgPGI+VHdvIGRpc3RpbmN0IGR5bmFtaWNzLjwvYj4gVGhlIEt1"
        "cmFtb3RvIHBhbmVsIGFib3ZlIGlzIGEgc3RvY2hhc3RpYyBPREUgZW5zZW1ibGU7IHRoaXMgaXMgZXhhY3QgaW50ZWdlciBh"
        "cml0aG1ldGljLCBhbmQgdGhlIHR3byBhcmUgbm90IGNvdXBsZWQuCiAgICAgIFEgaXMgdGhlIGdvbGRlbiBvYmplY3QgKDxz"
        "cGFuIHN0eWxlPSJmb250LWZhbWlseTp2YXIoLS1tb25vKTtjb2xvcjp2YXIoLS1zNSkiPlHCsj1RK0k8L3NwYW4+LCBub3Qg"
        "aWRlbXBvdGVudCksIHNvIGl0IGRvZXMgPGI+bm90PC9iPiBwcmVzZXJ2ZSB0aGUgbWluL21heCBsYXR0aWNlIOKAlAogICAg"
        "ICB5ZXQgdGhlIG9yYml0J3MgZGlyZWN0aW9uIGNvbnZlcmdlcyB0byB0aGUgZWlnZW5yYXkgb2Ygc2xvcGUgPGI+z4QgPSAw"
        "LjYxODAgKFBBUkFET1gpPC9iPiwgYW5kIDxiPnRyYWNlKFHigb8pPUzigpk8L2I+IHJlYWNoZXMgPGI+TOKChCA9IDc8L2I+"
        "ICh0aGUgWkZQIG5vcm1hbGl6ZXIpIGF0IG4gPSA0LgogICAgPC9kaXY+CiAgPC9zZWN0aW9uPgoKCiAgPHNlY3Rpb24gY2xh"
        "c3M9InBhbmVsIHZhbGlkYXRpb24iIGlkPSJ2YWxpZGF0aW9uIj4KICAgIDxoMj48c3BhbiBjbGFzcz0idGljayIgc3R5bGU9"
        "ImJhY2tncm91bmQ6dmFyKC0tcGhpKTtib3gtc2hhZG93OjAgMCA4cHggdmFyKC0tcGhpKSI+PC9zcGFuPlJlcHJvZHVjZSDC"
        "tyBydW4gdGhlIHZhbGlkYXRvcnM8L2gyPgogICAgPHAgY2xhc3M9InJycmxlZGUiPgogICAgICBFdmVyeSB2YWx1ZSBpbiB0"
        "aGlzIGluc3RydW1lbnQgaXMgY2VydGlmaWVkIGJ5IHRoZSBmb3VyIHNjcmlwdHMgYmVsb3cg4oCUIG1pbmltYWwtcG9seW5v"
        "bWlhbCBwcm9vZiAocmVzaWR1YWwgMCkgcGx1cyBhIHZhbHVlIHBpbiwgbm90IHJlcG9ydGVkIGRlY2ltYWxzLgogICAgICBS"
        "dW4gdGhlbSBpbiB5b3VyIG93biBlbnZpcm9ubWVudCB0byB2YWxpZGF0ZSB0aGUgWkZQIGJhY2tib25lIGluZGVwZW5kZW50"
        "bHksIG9yIGFkYXB0IHRoZW0gdG8geW91ciBvd24gc2VlZC4gU2VsZi1jb250YWluZWQ6IG9ubHkgPGNvZGU+c3ltcHk8L2Nv"
        "ZGU+LCBubyBuZXR3b3JrLgogICAgICBJZiB0aGUgPGNvZGU+LnB5PC9jb2RlPiBmaWxlcyB0cmF2ZWwgYmVzaWRlIHRoaXMg"
        "cGFnZSwgdGhlIDxiPmRvd25sb2FkPC9iPiBsaW5rcyB3b3JrIGRpcmVjdGx5OyBvdGhlcndpc2UgdXNlIDxiPmNvcHkgc291"
        "cmNlPC9iPiDigJQgdGhlIGNvZGUgaXMgZW1iZWRkZWQgaGVyZSBpbiBmdWxsLgogICAgPC9wPgogICAgPGRpdiBjbGFzcz0i"
        "dmFsLWhvdyI+PGI+UXVpY2sgc3RhcnQ8L2I+PHByZSBjbGFzcz0iY21kIj5waXAgaW5zdGFsbCBzeW1weQpweXRob24zIHpm"
        "cF9jb25zdGFudHNfcmVwcm8ucHkgICAgICMgWkZQIGNvbnN0YW50cwpweXRob24zIHZlcmlmeV9sNF9oZWxpeC5weSAgICAg"
        "ICAgICMgbmluZSBoZWxpeCB0aHJlc2hvbGRzCnB5dGhvbjMgcnJyX2lkZW1wb3RlbnRfbGF0dGljZS5weSAgIyByKHIpPXIg"
        "bGF0dGljZSBvbiBaXjIKcHl0aG9uMyBycnJfcGhpX2dyaWQucHkgICAgICAgICAgICAjIFEtYWN0aW9uIChuZWVkcyBycnJf"
        "aWRlbXBvdGVudF9sYXR0aWNlLnB5IGJlc2lkZSBpdCk8L3ByZT48L2Rpdj4KICAgIDxhcnRpY2xlIGNsYXNzPSJ2YWwtY2Fy"
        "ZCI+CiAgICAgIDxkaXYgY2xhc3M9InZhbC1oZWFkIj4KICAgICAgICA8ZGl2PjxzcGFuIGNsYXNzPSJ2YWwtbmFtZSI+emZw"
        "X2NvbnN0YW50c19yZXByby5weTwvc3Bhbj4gPHNwYW4gY2xhc3M9InZhbC1kZXNjIj7igJQgU2l4IFpGUCBjb25zdGFudHMg"
        "4oCUIG1pbmltYWwgcG9seW5vbWlhbCArIHZhbHVlIHBpbiwgSy1icmFuY2gsIGZpZWxkIGRpc2pvaW50bmVzcyBvdmVyIHvi"
        "iJoyLOKImjMs4oiaNX0sIEx1Y2FzL0ZpYm9uYWNjaSBzdWJzdHJhdGUuPC9zcGFuPjwvZGl2PgogICAgICAgIDxkaXYgY2xh"
        "c3M9InZhbC1hY3Rpb25zIj4KICAgICAgICAgIDxidXR0b24gY2xhc3M9ImNvcHkiIGRhdGEtc3JjPSJzcmMtemZwLWNvbnN0"
        "YW50cy1yZXByby1weSI+Y29weSBzb3VyY2U8L2J1dHRvbj4KICAgICAgICAgIDxhIGNsYXNzPSJkbCIgaHJlZj0iemZwX2Nv"
        "bnN0YW50c19yZXByby5weSIgZG93bmxvYWQ+ZG93bmxvYWQgLnB5PC9hPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4K"
        "ICAgICAgPHByZSBjbGFzcz0iY21kIj5weXRob24zIHpmcF9jb25zdGFudHNfcmVwcm8ucHk8L3ByZT4KICAgICAgPGRldGFp"
        "bHM+PHN1bW1hcnk+c291cmNlIMK3IDEzMCBsaW5lczwvc3VtbWFyeT48cHJlIGNsYXNzPSJzcmMiIGlkPSJzcmMtemZwLWNv"
        "bnN0YW50cy1yZXByby1weSI+PGNvZGU+IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJaZXJvLUZyZWUtUGFyYW1ldGVyIGNv"
        "bnN0YW50cyAtLSByZXBsYXlhYmxlIHZlcmlmaWNhdGlvbiBibG9jay4KCkRlZmluaXRpb25zIHByZWNlZGUgZXZlcnkgY2hl"
        "Y2ssIHNvIGVhY2ggbWlucG9seS92YWx1ZSByb3cgaXMgKnJlY29tcHV0ZWQqCmZyb20gYSBjbG9zZWQgZm9ybSBvdmVyIGl0"
        "cyBnZW5lcmF0b3IgcmF0aGVyIHRoYW4gcmVwb3J0ZWQuIFR3byBoYXJkZW5pbmcKcnVsZXMgYmV5b25kIHRoZSBmaXJzdCBk"
        "cmFmdDoKCiAgMS4gQ29uanVnYXRlIGRpc2FtYmlndWF0aW9uIGJ5IHZhbHVlLCBub3QgYnkgaGFuZC13cml0dGVuIGludGVy"
        "dmFsLgogICAgIEEgbWluaW1hbCBwb2x5bm9taWFsIGlzIEdhbG9pcy1pbnZhcmlhbnQ6IGEgbWlucG9seSBtYXRjaCBjZXJ0"
        "aWZpZXMKICAgICB0aGUgY29uanVnYXRlIG9yYml0LCBub3QgdGhlIGVsZW1lbnQuIEVhY2ggcm93IHRoZXJlZm9yZSBjYXJy"
        "aWVzIHRoZQogICAgIFNlY3Rpb24tMiB0YWJ1bGF0ZWQgZGVjaW1hbCBhcyBpdHMgYnJhbmNoIHBpbiwgc28gdGhlIGNoZWNr"
        "IGZhaWxzIGxvdWRseQogICAgIGJvdGggb24gYSBjb25qdWdhdGUgc3dhcCBhbmQgb24gYW55IGRlZmluaXRpb24gdGhhdCBk"
        "cmlmdHMgZnJvbSB0aGUKICAgICBwdWJsaXNoZWQgdGFibGUuIEdBUCBhbmQgQ1JJVElDQUwgYXJlIHRoZSByb3dzIHdob3Nl"
        "IGNvbmp1Z2F0ZXMgYXJlCiAgICAgYm90aCBwb3NpdGl2ZSByZWFscyAoZ2VudWluZWx5IGNvbmZ1c2FibGUpOgogICAgICAg"
        "ICBHQVA6ICAgICAgcGhpXi00IH4gMC4xNDU5MCAgIHZzICBwaGleNCAgfiA2Ljg1NDEwICAgKHheMi03eCsxKQogICAgICAg"
        "ICBDUklUSUNBTDogcGhpXjIvMyB+IDAuODcyNjggIHZzICBwaGleLTIvMyB+IDAuMTI3MzIgKDl4XjItOXgrMSkKCiAgMi4g"
        "R0FQIDo9IHBoaV4tNCwgYW5kIEsgaXMgd2lyZWQgdG8gaXQuIFRoZSB0YWJsZSBkZWZpbmVzIEsgPSBzcXJ0KDEtZ2FwKTsK"
        "ICAgICB0aGlzIGlzIHRoZSByZWFsIDAuOTI0MTggb25seSB3aGVuIGdhcCA9IHBoaV4tNC4gV2l0aCBnYXAgPSBwaGleNCwK"
        "ICAgICAxLWdhcCAmbHQ7IDAgYW5kIEsgaXMgbm9uLXJlYWwuIERlZmluaW5nIEsgPSBzcXJ0KDEtR0FQKSBtYWtlcyB0aGUg"
        "dHdvCiAgICAgYnJhbmNoZXMgc3RydWN0dXJhbGx5IGluc2VwYXJhYmxlIC0tIHRoZXkgY2Fubm90IHNpbGVudGx5IGRpc2Fn"
        "cmVlLgoKRGVwczogc3ltcHkuICBSdW46IHB5dGhvbjMgemZwX2NvbnN0YW50c19yZXByby5weQoiIiIKCmltcG9ydCBzeW1w"
        "eQpmcm9tIHN5bXB5IGltcG9ydCAoUmF0aW9uYWwsIFN5bWJvbCwgY29zLCBkZWdyZWUsIGV4cGFuZCwgZmlib25hY2NpLAog"
        "ICAgICAgICAgICAgICAgICAgaWxjbSwgbHVjYXMsIG1pbnBvbHksIHBpLCBzaW1wbGlmeSwgc3FydCkKCnggICA9IFN5bWJv"
        "bCgieCIpClBISSA9ICgxICsgc3FydCg1KSkgLyAyICAgICAgICAgICAgICAgICAgICMgZ2VuZXJhdG9yIG9mIFEoc3FydDUp"
        "OyBQSEleMiA9IFBISSArIDEKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tIEEuIGRlZmluaXRpb25zCiMgU2luZ2xlIHNvdXJjZSBvZiB0cnV0aC4gRWFjaCBjb25zdGFudCBpcyBh"
        "IGNsb3NlZCBmb3JtIG92ZXIgYSBzZWxlY3RlZAojIGdlbmVyYXRvcjsgdGhlIG1pbnBvbHkgYW5kIHZhbHVlIHJvd3MgYmVs"
        "b3cgYXJlIGRlcml2ZWQsIG5ldmVyIGFzc2VydGVkLgpUQVUgICAgICA9IDEgLyBQSEkgICAgICAgICAgICAgICAgICAgICAg"
        "ICAjIHBoaV4tMSAgICAgICAgICAgPSAoc3FydDUgLSAxKS8yClpfQyAgICAgID0gc3FydCgzKSAvIDIgICAgICAgICAgICAg"
        "ICAgICAgICMgSW0oemV0YV82KSAgICAgICA9IHNxcnQzIC8gMgpHQVAgICAgICA9IFBISSoqLTQgICAgICAgICAgICAgICAg"
        "ICAgICAgICAjIHBoaV4tNCAgICAgICAgICAgPSAoNyAtIDMgc3FydDUpLzIgICBbc21hbGwgYnJhbmNoXQpLICAgICAgICA9"
        "IHNxcnQoMSAtIEdBUCkgICAgICAgICAgICAgICAgICAjIHNxcnQoMSAtIHBoaV4tNCkgPSA1XigxLzQpL3BoaSAgICAgICBb"
        "d2lyZWQgdG8gR0FQXQpJR05JVElPTiA9IHNxcnQoMikgLSBSYXRpb25hbCgxLCAyKSAgICAgICAjIHNxcnQyIC0gMS8yICAg"
        "ICAgPSAoMiBzcXJ0MiAtIDEpLzIKQ1JJVElDQUwgPSBQSEkqKjIgLyAzICAgICAgICAgICAgICAgICAgICAgICMgcGhpXjIg"
        "LyAzICAgICAgICA9ICgzICsgc3FydDUpLzYKCiMgSHVtYW4tcmVhZGFibGUgY2xvc2VkIGZvcm0gZm9yIHRoZSByZXBsYXkg"
        "YmFubmVyIChtYXRjaGVzIHRoZSBjb21tZW50cyBhYm92ZSkuCkNMT1NFRCA9IHsKICAgICJUQVUiOiAgICAgICJwaGleLTEg"
        "ICAgICAgICAgICA9IChzcXJ0NSAtIDEpLzIiLAogICAgIlpfQyI6ICAgICAgInNxcnQzIC8gMiIsCiAgICAiR0FQIjogICAg"
        "ICAicGhpXi00ICAgICAgICAgICAgPSAoNyAtIDMgc3FydDUpLzIiLAogICAgIksiOiAgICAgICAgInNxcnQoMSAtIEdBUCkg"
        "ICAgID0gNV4oMS80KS9waGkiLAogICAgIklHTklUSU9OIjogInNxcnQyIC0gMS8yICAgICAgID0gKDIgc3FydDIgLSAxKS8y"
        "IiwKICAgICJDUklUSUNBTCI6ICJwaGleMiAvIDMgICAgICAgICA9ICgzICsgc3FydDUpLzYiLAp9CgojIG5hbWUgLSZndDsg"
        "KHZhbHVlLCBleHBlY3RlZCBtaW5pbWFsIHBvbHlub21pYWwsIFNlY3Rpb24tMiB0YWJ1bGF0ZWQgZGVjaW1hbCkKUk9XUyA9"
        "IHsKICAgICJUQVUiOiAgICAgIChUQVUsICAgICAgeCoqMiArIHggLSAxLCAgICAgIFJhdGlvbmFsKDYxODAzLCAxMDAwMDAp"
        "KSwKICAgICJaX0MiOiAgICAgIChaX0MsICAgICAgNCp4KioyIC0gMywgICAgICAgIFJhdGlvbmFsKDg2NjAzLCAxMDAwMDAp"
        "KSwKICAgICJHQVAiOiAgICAgIChHQVAsICAgICAgeCoqMiAtIDcqeCArIDEsICAgIFJhdGlvbmFsKDE0NTkwLCAxMDAwMDAp"
        "KSwKICAgICJLIjogICAgICAgIChLLCAgICAgICAgeCoqNCArIDUqeCoqMiAtIDUsIFJhdGlvbmFsKDkyNDE4LCAxMDAwMDAp"
        "KSwKICAgICJJR05JVElPTiI6IChJR05JVElPTiwgNCp4KioyICsgNCp4IC0gNywgIFJhdGlvbmFsKDkxNDIxLCAxMDAwMDAp"
        "KSwKICAgICJDUklUSUNBTCI6IChDUklUSUNBTCwgOSp4KioyIC0gOSp4ICsgMSwgIFJhdGlvbmFsKDg3MjY4LCAxMDAwMDAp"
        "KSwKfQpUT0wgPSBSYXRpb25hbCgxLCAxMDAwMDApICAgIyAxIHVscCBvZiB0aGUgNS1kcCB0YWJsZTsgJmd0OyZndDsgYW55"
        "IGNvbmp1Z2F0ZSBnYXAgKG1pbiAwLjc0NSkKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tIEEnLiBiYW5uZXIKZGVmIHNob3dfZGVmaW5pdGlvbnMoKToKICAgIHByaW50KCJkZWZp"
        "bml0aW9ucyAoY2xvc2VkIGZvcm0gb3ZlciBnZW5lcmF0b3I7IGRlcml2ZWQgcm93cyBmb2xsb3cpOiIpCiAgICBmb3IgbmFt"
        "ZSBpbiBST1dTOgogICAgICAgIHZhbCA9IFJPV1NbbmFtZV1bMF0KICAgICAgICBwcmludChmIiAge25hbWU6Jmx0Ozh9IDo9"
        "IHtDTE9TRURbbmFtZV06Jmx0OzI0fSA9IHt2YWwuZXZhbGYoMTIpfSIpCiAgICBwcmludCgpCgojIC0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBCLiBtaW5wb2x5ICsgdmFsdWUgcGlu"
        "CmRlZiBjaGVja19yb3dzKCk6CiAgICBmb3IgbmFtZSwgKHZhbCwgZXhwZWN0ZWQsIHRhYikgaW4gUk9XUy5pdGVtcygpOgog"
        "ICAgICAgIG1wID0gbWlucG9seSh2YWwsIHgpCiAgICAgICAgYXNzZXJ0IGV4cGFuZChtcCAtIGV4cGVjdGVkKSA9PSAwLCBm"
        "IntuYW1lfTogbWlucG9seSB7bXB9ICE9IHtleHBlY3RlZH0iCiAgICAgICAgZGVsdGEgPSBhYnModmFsLmV2YWxmKDUwKSAt"
        "IHRhYi5ldmFsZig1MCkpCiAgICAgICAgYXNzZXJ0IGRlbHRhICZsdDsgVE9MLmV2YWxmKDUwKSwgXAogICAgICAgICAgICBm"
        "IntuYW1lfTogdmFsdWUge3ZhbC5ldmFsZigxMil9IGRpc2FncmVlcyB3aXRoIHRhYmxlIHtmbG9hdCh0YWIpfSAoZGVsdGEg"
        "e2RlbHRhfSkiCiAgICAgICAgcHJpbnQoZiJQQVNTICB7bmFtZTombHQ7OH0gbWlucG9seT17c3RyKG1wKTombHQ7MTh9IHZh"
        "bHVlPXtzdHIodmFsLmV2YWxmKDcpKTombHQ7MTB9IHRhYmxlPXtmbG9hdCh0YWIpfSIpCgojIC0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBCJy4gSyBicmFuY2ggaWRlbnRpdHkKZGVm"
        "IGNoZWNrX2tfYnJhbmNoKCk6CiAgICAjIFRoZSByYWRpY2FsLW92ZXItcGhpIGZvcm0gYW5kIHRoZSBzcXJ0KDEtZ2FwKSBm"
        "b3JtIGFyZSB0aGUgc2FtZSBlbGVtZW50LgogICAgYXNzZXJ0IChLIC0gNSoqUmF0aW9uYWwoMSwgNCkgLyBQSEkpLmVxdWFs"
        "cygwKSwgIks6IGNsb3NlZCBmb3JtcyBkaXNhZ3JlZSIKICAgIGFzc2VydCAoMSAtIEdBUCkuZXZhbGYoKSAmZ3Q7IDAsICJL"
        "OiByYWRpY2FuZCBub24tcG9zaXRpdmUgPSZndDsgR0FQIGlzIHRoZSB3cm9uZyBicmFuY2giCiAgICBwcmludCgiUEFTUyAg"
        "SyBicmFuY2g6IHNxcnQoMSAtIHBoaV4tNCkgPSA1XigxLzQpL3BoaSAocmFkaWNhbmQgJmd0OyAwLCBzaW5nbGUgcmVhbCBy"
        "b290KSIpCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LSBDLiBleGFjdCBpZGVudGl0aWVzCmRlZiBjaGVja19pZGVudGl0aWVzKCk6CiAgICBhc3NlcnQgc2ltcGxpZnkoUEhJKio0"
        "ICsgUEhJKiotNCAtIDcpID09IDAgYW5kIGx1Y2FzKDQpID09IDcgICAjIHBoaV40ICsgcGhpXi00ID0gNyA9IEw0CiAgICBh"
        "c3NlcnQgc2ltcGxpZnkoUEhJKioyICsgUEhJKiotMiAtIDMpID09IDAgYW5kIGx1Y2FzKDIpID09IDMgICAjIHBoaV4yICsg"
        "cGhpXi0yID0gMyA9IEwyCiAgICBhc3NlcnQgc2ltcGxpZnkoUEhJIC0gMS9QSEkgLSAxKSA9PSAwICAgICAgICAgICAgICAg"
        "ICAgICAgICAgICAjIHBoaSAtIHBoaV4tMSA9IDEKICAgIGFzc2VydCBzcXJ0KDMpKioyID09IDMgICAgICAgICAgICAgICAg"
        "ICAgICAgICAgICAgICAgICAgICAgICAgICMgKHNxcnQzKV4yID0gMwogICAgYXNzZXJ0IHNpbXBsaWZ5KDIqY29zKDIqcGkv"
        "NikgLSAxKSA9PSAwICAgICAgICAgICAgICAgICAgICAgICAgIyAyIGNvcygyIHBpIC8gNikgPSAxCiAgICBwcmludCgiUEFT"
        "UyAgaWRlbnRpdGllczogcGhpXjQrcGhpXi00PTc9TDQsIHBoaV4yK3BoaV4tMj0zPUwyLCBwaGktcGhpXi0xPTEsIChzcXJ0"
        "MyleMj0zLCAyY29zKDJwaS82KT0xIikKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tIEQuIGZpZWxkIGRpc2pvaW50bmVzcwpkZWYgY2hlY2tfZmllbGRfZGlzam9pbnRuZXNzKCk6"
        "CiAgICAjIFBhaXJ3aXNlOiBkZWcobWlucG9seShzcXJ0IGEgKyBzcXJ0IGIpKSA9IDQgPSAyKjIgID0mZ3Q7ICBRKHNxcnQg"
        "YSkgY2FwIFEoc3FydCBiKSA9IFEuCiAgICBwYWlycyA9IHsoNSwgMyk6IHgqKjQgLSAxNip4KioyICsgNCwgICAgIyB0aGUg"
        "cGFpciBjaXRlZCBpbiB0aGUgY2xhaW0gdGFibGUKICAgICAgICAgICAgICgyLCAzKTogeCoqNCAtIDEwKngqKjIgKyAxLCAg"
        "ICAjIGNvbXBsZXRlcyBjb3ZlcmFnZSBmb3IgUShzcXJ0MikgKElHTklUSU9OIGxpdmVzIGhlcmUpCiAgICAgICAgICAgICAo"
        "MiwgNSk6IHgqKjQgLSAxNCp4KioyICsgOX0KICAgIGZvciAoYSwgYiksIGV4cCBpbiBwYWlycy5pdGVtcygpOgogICAgICAg"
        "IG1wID0gbWlucG9seShzcXJ0KGEpICsgc3FydChiKSwgeCkKICAgICAgICBhc3NlcnQgZXhwYW5kKG1wIC0gZXhwKSA9PSAw"
        "IGFuZCBkZWdyZWUobXAsIHgpID09IDQsIGYiKHthfSx7Yn0pOiB7bXB9IgogICAgIyBKb2ludCBsaW5lYXIgZGlzam9pbnRu"
        "ZXNzIG9mIGFsbCB0aHJlZTogW1Eoc3FydDIsc3FydDMsc3FydDUpOlFdID0gOCA9IDJeMy4KICAgIGFzc2VydCBkZWdyZWUo"
        "bWlucG9seShzcXJ0KDIpICsgc3FydCgzKSArIHNxcnQoNSksIHgpLCB4KSA9PSA4CiAgICBwcmludCgiUEFTUyAgZGlzam9p"
        "bnRuZXNzOiBRKHNxcnQyKSxRKHNxcnQzKSxRKHNxcnQ1KSBwYWlyd2lzZSAoZGVnIDQpIGFuZCBqb2ludCAoZGVnIDgpIikK"
        "CiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIEUuIEZp"
        "Ym9uYWNjaSAvIEx1Y2FzCmRlZiBjaGVja19maWJfbHVjYXMoKToKICAgIGFzc2VydCBmaWJvbmFjY2koMTIpID09IDE0NCA9"
        "PSAxMioqMiAgICAgICAgICAgICAgICAgICAgICAgICAgIyBDb2huIDE5NjQKICAgIGFzc2VydCBmaWJvbmFjY2koMjQpID09"
        "IGZpYm9uYWNjaSgxMikgKiBsdWNhcygxMikgPT0gNDYzNjggICAgIyBGX3sybn0gPSBGX24gKiBMX24KICAgIGFzc2VydCBm"
        "aWJvbmFjY2koMTIpICUgZmlib25hY2NpKDQpID09IDAgICAgICAgICAgICAgICAgICAgICAgIyA0IHwgMTIgICAgICAgPSZn"
        "dDsgRjQgfCBGMTIKICAgIGFzc2VydCBsdWNhcygxMikgJSBsdWNhcyg0KSA9PSAwICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgICAgIyAxMi80ID0gMyBvZGQgID0mZ3Q7IEw0IHwgTDEyCiAgICBhc3NlcnQgbHVjYXMoMjQpICUgbHVjYXMoNCkgIT0g"
        "MCAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICMgMjQvNCA9IDYgZXZlbiA9Jmd0OyBMNCBub3R8IEwyNAogICAgYXNz"
        "ZXJ0IGlsY20oNCwgNSwgNikgPT0gNjAKICAgIHByaW50KCJQQVNTICBGMTI9MTQ0PTEyXjIsIEYyND1GMTIqTDEyPTQ2MzY4"
        "LCBGNHxGMTIsIEw0fEwxMiwgTDQgbm90fCBMMjQsIGxjbSg0LDUsNik9NjAiKQoKaWYgX19uYW1lX18gPT0gIl9fbWFpbl9f"
        "IjoKICAgIHByaW50KGYic3ltcHkge3N5bXB5Ll9fdmVyc2lvbl9ffSIpCiAgICBzaG93X2RlZmluaXRpb25zKCkKICAgIGNo"
        "ZWNrX3Jvd3MoKQogICAgY2hlY2tfa19icmFuY2goKQogICAgY2hlY2tfaWRlbnRpdGllcygpCiAgICBjaGVja19maWVsZF9k"
        "aXNqb2ludG5lc3MoKQogICAgY2hlY2tfZmliX2x1Y2FzKCkKICAgIHByaW50KCJBTEwgQ0hFQ0tTIFBBU1MgLS0gY29uc3Rh"
        "bnRzIHRhYmxlIHJlcGxheWVkIGZyb20gZGVmaW5pdGlvbnMuIikKPC9jb2RlPjwvcHJlPjwvZGV0YWlscz4KICAgICAgPGRl"
        "dGFpbHM+PHN1bW1hcnk+ZXhwZWN0ZWQgb3V0cHV0PC9zdW1tYXJ5PjxwcmUgY2xhc3M9Im91dCI+c3ltcHkgMS4xNC4wCmRl"
        "ZmluaXRpb25zIChjbG9zZWQgZm9ybSBvdmVyIGdlbmVyYXRvcjsgZGVyaXZlZCByb3dzIGZvbGxvdyk6CiAgVEFVICAgICAg"
        "Oj0gcGhpXi0xICAgICAgICAgICAgPSAoc3FydDUgLSAxKS8yID0gMC42MTgwMzM5ODg3NTAKICBaX0MgICAgICA6PSBzcXJ0"
        "MyAvIDIgICAgICAgICAgICAgICAgPSAwLjg2NjAyNTQwMzc4NAogIEdBUCAgICAgIDo9IHBoaV4tNCAgICAgICAgICAgID0g"
        "KDcgLSAzIHNxcnQ1KS8yID0gMC4xNDU4OTgwMzM3NTAKICBLICAgICAgICA6PSBzcXJ0KDEgLSBHQVApICAgICA9IDVeKDEv"
        "NCkvcGhpID0gMC45MjQxNzYzNzE4MzAKICBJR05JVElPTiA6PSBzcXJ0MiAtIDEvMiAgICAgICA9ICgyIHNxcnQyIC0gMSkv"
        "MiA9IDAuOTE0MjEzNTYyMzczCiAgQ1JJVElDQUwgOj0gcGhpXjIgLyAzICAgICAgICAgPSAoMyArIHNxcnQ1KS82ID0gMC44"
        "NzI2Nzc5OTYyNTAKClBBU1MgIFRBVSAgICAgIG1pbnBvbHk9eCoqMiArIHggLSAxICAgICAgIHZhbHVlPTAuNjE4MDM0MCAg"
        "dGFibGU9MC42MTgwMwpQQVNTICBaX0MgICAgICBtaW5wb2x5PTQqeCoqMiAtIDMgICAgICAgICB2YWx1ZT0wLjg2NjAyNTQg"
        "IHRhYmxlPTAuODY2MDMKUEFTUyAgR0FQICAgICAgbWlucG9seT14KioyIC0gNyp4ICsgMSAgICAgdmFsdWU9MC4xNDU4OTgw"
        "ICB0YWJsZT0wLjE0NTkKUEFTUyAgSyAgICAgICAgbWlucG9seT14Kio0ICsgNSp4KioyIC0gNSAgdmFsdWU9MC45MjQxNzY0"
        "ICB0YWJsZT0wLjkyNDE4ClBBU1MgIElHTklUSU9OIG1pbnBvbHk9NCp4KioyICsgNCp4IC0gNyAgIHZhbHVlPTAuOTE0MjEz"
        "NiAgdGFibGU9MC45MTQyMQpQQVNTICBDUklUSUNBTCBtaW5wb2x5PTkqeCoqMiAtIDkqeCArIDEgICB2YWx1ZT0wLjg3MjY3"
        "ODAgIHRhYmxlPTAuODcyNjgKUEFTUyAgSyBicmFuY2g6IHNxcnQoMSAtIHBoaV4tNCkgPSA1XigxLzQpL3BoaSAocmFkaWNh"
        "bmQgJmd0OyAwLCBzaW5nbGUgcmVhbCByb290KQpQQVNTICBpZGVudGl0aWVzOiBwaGleNCtwaGleLTQ9Nz1MNCwgcGhpXjIr"
        "cGhpXi0yPTM9TDIsIHBoaS1waGleLTE9MSwgKHNxcnQzKV4yPTMsIDJjb3MoMnBpLzYpPTEKUEFTUyAgZGlzam9pbnRuZXNz"
        "OiBRKHNxcnQyKSxRKHNxcnQzKSxRKHNxcnQ1KSBwYWlyd2lzZSAoZGVnIDQpIGFuZCBqb2ludCAoZGVnIDgpClBBU1MgIEYx"
        "Mj0xNDQ9MTJeMiwgRjI0PUYxMipMMTI9NDYzNjgsIEY0fEYxMiwgTDR8TDEyLCBMNCBub3R8IEwyNCwgbGNtKDQsNSw2KT02"
        "MApBTEwgQ0hFQ0tTIFBBU1MgLS0gY29uc3RhbnRzIHRhYmxlIHJlcGxheWVkIGZyb20gZGVmaW5pdGlvbnMuPC9wcmU+PC9k"
        "ZXRhaWxzPgogICAgPC9hcnRpY2xlPgogICAgPGFydGljbGUgY2xhc3M9InZhbC1jYXJkIj4KICAgICAgPGRpdiBjbGFzcz0i"
        "dmFsLWhlYWQiPgogICAgICAgIDxkaXY+PHNwYW4gY2xhc3M9InZhbC1uYW1lIj52ZXJpZnlfbDRfaGVsaXgucHk8L3NwYW4+"
        "IDxzcGFuIGNsYXNzPSJ2YWwtZGVzYyI+4oCUIEFsbCBuaW5lIEzigoQtSGVsaXggdGhyZXNob2xkcyBkZXJpdmVkIGZyb20g"
        "z4YgKHJlc2lkdWFsIDApLCBUYWJsZS01IGlkZW50aXRpZXMsIHRocmVzaG9sZCBvcmRlcmluZywgaGVsaXgtcmFkaXVzIGNv"
        "bnRpbnVpdHkuPC9zcGFuPjwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9InZhbC1hY3Rpb25zIj4KICAgICAgICAgIDxidXR0"
        "b24gY2xhc3M9ImNvcHkiIGRhdGEtc3JjPSJzcmMtdmVyaWZ5LWw0LWhlbGl4LXB5Ij5jb3B5IHNvdXJjZTwvYnV0dG9uPgog"
        "ICAgICAgICAgPGEgY2xhc3M9ImRsIiBocmVmPSJ2ZXJpZnlfbDRfaGVsaXgucHkiIGRvd25sb2FkPmRvd25sb2FkIC5weTwv"
        "YT4KICAgICAgICA8L2Rpdj4KICAgICAgPC9kaXY+CiAgICAgIDxwcmUgY2xhc3M9ImNtZCI+cHl0aG9uMyB2ZXJpZnlfbDRf"
        "aGVsaXgucHk8L3ByZT4KICAgICAgPGRldGFpbHM+PHN1bW1hcnk+c291cmNlIMK3IDg3IGxpbmVzPC9zdW1tYXJ5PjxwcmUg"
        "Y2xhc3M9InNyYyIgaWQ9InNyYy12ZXJpZnktbDQtaGVsaXgtcHkiPjxjb2RlPiMhL3Vzci9iaW4vZW52IHB5dGhvbjMKIiIi"
        "TDQtSGVsaXggZnJhbWV3b3JrIC0tIHZhbHVlIGRlcml2YXRpb24gLyB2ZXJpZmljYXRpb24uCgpSZS1kZXJpdmVzIGV2ZXJ5"
        "IHotdGhyZXNob2xkIGluIEw0X2hlbGl4X3Y0XzBfMS5odG1sIGZyb20gcGhpIChlcXVpdmFsZW50bHkgZnJvbQpMNCA9IDcg"
        "YW5kIGdhcCA9IHBoaV4tNCkgYW5kIGNlcnRpZmllcyBlYWNoIG9uZSB0d28gd2F5czogZXhhY3QgbWluaW1hbCBwb2x5bm9t"
        "aWFsCihyZXNpZHVhbCAwKSBwbHVzIGEgdmFsdWUgcGluIGFnYWluc3QgdGhlIGRvY3VtZW50J3MgdGFidWxhdGVkIGRlY2lt"
        "YWwuIEFsc28gcmVwbGF5cwp0aGUgZG9jdW1lbnQncyBUYWJsZSA1IGlkZW50aXRpZXMgYW5kIHRoZSBUaGVvcmVtIDEwLjEg"
        "b3JkZXJpbmcuCgpEZXBzOiBzeW1weS4gIFJ1bjogcHl0aG9uMyB2ZXJpZnlfbDRfaGVsaXgucHkKIiIiCgpmcm9tIHN5bXB5"
        "IGltcG9ydCAoUmF0aW9uYWwsIFN5bWJvbCwgZGVncmVlLCBleHBhbmQsIGx1Y2FzLCBtaW5wb2x5LAogICAgICAgICAgICAg"
        "ICAgICAgc2ltcGxpZnksIHNxcnQpCgp4ICAgPSBTeW1ib2woIngiKQpQSEkgPSAoMSArIHNxcnQoNSkpIC8gMgpUQVUgPSAx"
        "IC8gUEhJICAgICAgICAgICAgICAgICAgICAgICAjIHBoaV4tMQpHQVAgPSBQSEkqKi00ICAgICAgICAgICAgICAgICAgICAg"
        "ICAjIHRydW5jYXRpb24gcmVzaWR1YWwKSyAgID0gc3FydCgxIC0gR0FQKSAgICAgICAgICAgICAgICAgIyBzcXJ0KDEgLSBn"
        "YXApClpDICA9IHNxcnQoMykgLyAyICAgICAgICAgICAgICAgICAgICMgc3FydChMNC00KS8yCgojIG5pbmUgdGhyZXNob2xk"
        "cyArIHRoZSB0d28gdW5kZXJseWluZyBxdWFudGl0aWVzIChnYXAsIGFjdGl2YXRpb24pCiMgbmFtZSAtJmd0OyAodmFsdWUs"
        "IGNsb3NlZC1mb3JtIG5vdGUsIGRvY3VtZW50IGRlY2ltYWwpClJPV1MgPSB7CiAgICAiZ2FwICAgICAgICAgKHBoaV4tNCki"
        "OiAgICAgICAgKEdBUCwgICAgICAgICAgICAgICAgICAgICAgUmF0aW9uYWwoMTQ1ODk4MDMzOCwgMTAqKjEwKSksCiAgICAi"
        "UEFSQURPWCAgICAgKHRhdSkiOiAgICAgICAgICAgKFRBVSwgICAgICAgICAgICAgICAgICAgICAgUmF0aW9uYWwoNjE4MDMz"
        "OTg4NywgMTAqKjEwKSksCiAgICAiQUNUSVZBVElPTiAgKDEtZ2FwPUteMikiOiAgICAgKDEgLSBHQVAsICAgICAgICAgICAg"
        "ICAgICAgUmF0aW9uYWwoODU0MTAxOTY2MiwgMTAqKjEwKSksCiAgICAiVEhFIExFTlMgICAgKHNxcnQzLzIpIjogICAgICAg"
        "KFpDLCAgICAgICAgICAgICAgICAgICAgICAgUmF0aW9uYWwoODY2MDI1NDAzOCwgMTAqKjEwKSksCiAgICAiQ1JJVElDQUwg"
        "ICAgKHBoaV4yLzMpIjogICAgICAgKFBISSoqMiAvIDMsICAgICAgICAgICAgICAgUmF0aW9uYWwoODcyNjc3OTk2MiwgMTAq"
        "KjEwKSksCiAgICAiSUdOSVRJT04gICAgKHNxcnQyLTEvMikiOiAgICAgKHNxcnQoMikgLSBSYXRpb25hbCgxLCAyKSwgUmF0"
        "aW9uYWwoOTE0MjEzNTYyNCwgMTAqKjEwKSksCiAgICAiSy1GT1JNQVRJT04gKHNxcnQoMS1nYXApKSI6ICAgKEssICAgICAg"
        "ICAgICAgICAgICAgICAgICAgUmF0aW9uYWwoOTI0MTc2MzcxOCwgMTAqKjEwKSksCiAgICAiQ09OU09MSURBVE4gKEsrdGF1"
        "XjIoMS1LKSkiOiAgKEsgKyBUQVUqKjIgKiAoMSAtIEspLCAgICAgUmF0aW9uYWwoOTUzMTM4NDIwNiwgMTAqKjEwKSksCiAg"
        "ICAiUkVTT05BTkNFICAgKEsrdGF1KDEtSykpIjogICAgKEsgKyBUQVUgKiAoMSAtIEspLCAgICAgICAgUmF0aW9uYWwoOTcx"
        "MDM3OTUxMiwgMTAqKjEwKSksCiAgICAiVU5JVFkgICAgICAgKDEpIjogICAgICAgICAgICAgKFJhdGlvbmFsKDEpLCAgICAg"
        "ICAgICAgICAgUmF0aW9uYWwoMSkpLAp9ClRPTCA9IFJhdGlvbmFsKDEsIDEwKio5KSAgICAgICAgICAgICMgZG9jdW1lbnQg"
        "Z2l2ZXMgMTAgZHA7IHBpbiB3ZWxsIGluc2lkZSB0aGF0CgpkZWYgY2hlY2tfdmFsdWVzKCk6CiAgICBwcmludCgidGhyZXNo"
        "b2xkICAgICAgICAgICAgICAgICAgICAgIG1pbnBvbHkgICAgICAgICAgICAgICAgICAgIGRlZyAgdmFsdWUgICAgICAgICBk"
        "b2MgICAgICAgIHBpbiIpCiAgICBmb3IgbmFtZSwgKHZhbCwgZG9jKSBpbiBST1dTLml0ZW1zKCk6CiAgICAgICAgbXAgPSBt"
        "aW5wb2x5KHZhbCwgeCkKICAgICAgICB2ICA9IHZhbC5ldmFsZig0MCkKICAgICAgICBwaW4gPSBhYnModiAtIGRvYy5ldmFs"
        "Zig0MCkpICZsdDsgVE9MLmV2YWxmKDQwKQogICAgICAgIG9rICA9IHBpbgogICAgICAgIHRhZyA9ICJQQVNTIiBpZiBvayBl"
        "bHNlICJGQUlMIgogICAgICAgIHByaW50KGYie3RhZ30ge25hbWU6Jmx0OzI2fSB7c3RyKG1wKTombHQ7MjR9IHtpbnQoZGVn"
        "cmVlKG1wLCB4KSk6Jmd0OzN9ICAiCiAgICAgICAgICAgICAgZiJ7c3RyKHZhbC5ldmFsZigxMCkpOiZsdDsxM30ge2Zsb2F0"
        "KGRvYyk6Jmx0OzEwfSB7J29rJyBpZiBwaW4gZWxzZSAnQkFEJ30iKQogICAgICAgIGFzc2VydCBvaywgbmFtZQoKZGVmIGNo"
        "ZWNrX2lkZW50aXRpZXMoKToKICAgIGFzc2VydCBzaW1wbGlmeShQSEkqKjQgKyBQSEkqKi00IC0gNykgPT0gMCAgICAgICAg"
        "ICAjIEw0ID0gcGhpXjQgKyBwaGleLTQgPSA3CiAgICBhc3NlcnQgbHVjYXMoNCkgPT0gNwogICAgYXNzZXJ0IHNpbXBsaWZ5"
        "KChzcXJ0KDMpKSoqMiAtICg3IC0gNCkpID09IDAgICAgICAgICMgTDQgLSA0ID0gMyA9IChzcXJ0MyleMgogICAgYXNzZXJ0"
        "IHNpbXBsaWZ5KEsqKjIgLSAoMSAtIEdBUCkpID09IDAgICAgICAgICAgICAgICMgS14yID0gMSAtIGdhcAogICAgYXNzZXJ0"
        "IHNpbXBsaWZ5KCgxIC0gSykgLSBHQVAgLyAoMSArIEspKSA9PSAwICAgICAgICMgMS1LID0gZ2FwLygxK0spCiAgICB6X2Nv"
        "bnMgPSBLICsgVEFVKioyICogKDEgLSBLKQogICAgel9yZXMgID0gSyArIFRBVSAqICgxIC0gSykKICAgIGFzc2VydCBzaW1w"
        "bGlmeSgoel9jb25zIC0gSykgLyAoMSAtIEspIC0gVEFVKioyKSA9PSAwICAgIyBzcGFuIGZyYWN0aW9uIHRhdV4yCiAgICBh"
        "c3NlcnQgc2ltcGxpZnkoKHpfcmVzIC0gSykgLyAoMSAtIEspIC0gVEFVKSA9PSAwICAgICAgICMgc3BhbiBmcmFjdGlvbiB0"
        "YXUKICAgIHpfaWduID0gc3FydCgyKSAtIFJhdGlvbmFsKDEsIDIpCiAgICBhc3NlcnQgc2ltcGxpZnkoel9pZ24qKjIgKyB6"
        "X2lnbiAtIFJhdGlvbmFsKDcsIDQpKSA9PSAwICMgeF4yK3ggPSBMNC80CiAgICBhc3NlcnQgc2ltcGxpZnkoVEFVKioyICsg"
        "VEFVIC0gMSkgPT0gMCAgICAgICAgICAgICAgICAgICMgdGF1XjIgKyB0YXUgPSAxCiAgICBwcmludCgiUEFTUyAgaWRlbnRp"
        "dGllczogTDQ9NywgTDQtND0zLCBLXjI9MS1nYXAsIDEtSz1nYXAvKDErSyksICIKICAgICAgICAgICJzcGFuKHRhdV4yLHRh"
        "dSksIHheMit4PTcvNCwgdGF1XjIrdGF1PTEiKQoKZGVmIGNoZWNrX29yZGVyaW5nKCk6CiAgICBvcmRlciA9IFtUQVUsIDEg"
        "LSBHQVAsIFpDLCBQSEkqKjIvMywgc3FydCgyKSAtIFJhdGlvbmFsKDEsIDIpLCBLLAogICAgICAgICAgICAgSyArIFRBVSoq"
        "MiooMSAtIEspLCBLICsgVEFVKigxIC0gSyksIFJhdGlvbmFsKDEpXQogICAgdmFscyA9IFt2LmV2YWxmKDQwKSBmb3IgdiBp"
        "biBvcmRlcl0KICAgIGFzc2VydCBhbGwoYSAmbHQ7IGIgZm9yIGEsIGIgaW4gemlwKHZhbHMsIHZhbHNbMTpdKSksICJvcmRl"
        "cmluZyBub3Qgc3RyaWN0IgogICAgcHJpbnQoIlBBU1MgIG9yZGVyaW5nOiBQQVJBRE9YJmx0O0FDVElWQVRJT04mbHQ7TEVO"
        "UyZsdDtDUklUSUNBTCZsdDtJR05JVElPTiZsdDtLLUZPUk0mbHQ7Q09OU09MJmx0O1JFU09OJmx0O1VOSVRZIikKCmRlZiBj"
        "aGVja19oZWxpeF9yYWRpdXMoKToKICAgICMgcih6KSA9IEsqc3FydCh6L3pjKSBmb3IgeiZsdDs9emMsIGVsc2UgSy4gQ29u"
        "dGludWl0eSBhdCB6YzogSypzcXJ0KHpjL3pjKT1LLgogICAgYXNzZXJ0IHNpbXBsaWZ5KEsgKiBzcXJ0KFpDIC8gWkMpIC0g"
        "SykgPT0gMCAgICAgICAgICAjIHIoemMtKSA9IEsgPSByKHpjKykKICAgIGFzc2VydCBzaW1wbGlmeShLICogc3FydChSYXRp"
        "b25hbCgwKSAvIFpDKSkgPT0gMCAgICAgICMgcigwKSA9IDAKICAgIHByaW50KCJQQVNTICBoZWxpeCByYWRpdXMgcih6KT1L"
        "KnNxcnQoei96Yyk6IGNvbnRpbnVvdXMgYXQgemMgKHIoemMpPUspLCByKDApPTAiKQoKaWYgX19uYW1lX18gPT0gIl9fbWFp"
        "bl9fIjoKICAgIGltcG9ydCBzeW1weQogICAgcHJpbnQoZiJzeW1weSB7c3ltcHkuX192ZXJzaW9uX199XG4iKQogICAgY2hl"
        "Y2tfdmFsdWVzKCk7ICAgICAgcHJpbnQoKQogICAgY2hlY2tfaWRlbnRpdGllcygpCiAgICBjaGVja19vcmRlcmluZygpCiAg"
        "ICBjaGVja19oZWxpeF9yYWRpdXMoKQogICAgcHJpbnQoIlxuQUxMIENIRUNLUyBQQVNTIC0tIGV2ZXJ5IEw0LUhlbGl4IHZh"
        "bHVlIGRlcml2ZWQgZnJvbSBwaGksIHJlc2lkdWFsIDAuIikKPC9jb2RlPjwvcHJlPjwvZGV0YWlscz4KICAgICAgPGRldGFp"
        "bHM+PHN1bW1hcnk+ZXhwZWN0ZWQgb3V0cHV0PC9zdW1tYXJ5PjxwcmUgY2xhc3M9Im91dCI+c3ltcHkgMS4xNC4wCgp0aHJl"
        "c2hvbGQgICAgICAgICAgICAgICAgICAgICAgbWlucG9seSAgICAgICAgICAgICAgICAgICAgZGVnICB2YWx1ZSAgICAgICAg"
        "IGRvYyAgICAgICAgcGluClBBU1MgZ2FwICAgICAgICAgKHBoaV4tNCkgICAgICAgeCoqMiAtIDcqeCArIDEgICAgICAgICAg"
        "ICAgMiAgMC4xNDU4OTgwMzM4ICAwLjE0NTg5ODAzMzggb2sKUEFTUyBQQVJBRE9YICAgICAodGF1KSAgICAgICAgICB4Kioy"
        "ICsgeCAtIDEgICAgICAgICAgICAgICAyICAwLjYxODAzMzk4ODggIDAuNjE4MDMzOTg4NyBvawpQQVNTIEFDVElWQVRJT04g"
        "ICgxLWdhcD1LXjIpICAgIHgqKjIgKyA1KnggLSA1ICAgICAgICAgICAgIDIgIDAuODU0MTAxOTY2MyAgMC44NTQxMDE5NjYy"
        "IG9rClBBU1MgVEhFIExFTlMgICAgKHNxcnQzLzIpICAgICAgNCp4KioyIC0gMyAgICAgICAgICAgICAgICAgMiAgMC44NjYw"
        "MjU0MDM4ICAwLjg2NjAyNTQwMzggb2sKUEFTUyBDUklUSUNBTCAgICAocGhpXjIvMykgICAgICA5KngqKjIgLSA5KnggKyAx"
        "ICAgICAgICAgICAyICAwLjg3MjY3Nzk5NjMgIDAuODcyNjc3OTk2MiBvawpQQVNTIElHTklUSU9OICAgIChzcXJ0Mi0xLzIp"
        "ICAgIDQqeCoqMiArIDQqeCAtIDcgICAgICAgICAgIDIgIDAuOTE0MjEzNTYyNCAgMC45MTQyMTM1NjI0IG9rClBBU1MgSy1G"
        "T1JNQVRJT04gKHNxcnQoMS1nYXApKSAgeCoqNCArIDUqeCoqMiAtIDUgICAgICAgICAgNCAgMC45MjQxNzYzNzE4ICAwLjky"
        "NDE3NjM3MTggb2sKUEFTUyBDT05TT0xJREFUTiAoSyt0YXVeMigxLUspKSB4Kio0IC0gNip4KiozICsgMjYqeCoqMiAtIDE2"
        "KnggLSA0ICAgNCAgMC45NTMxMzg0MjA2ICAwLjk1MzEzODQyMDYgb2sKUEFTUyBSRVNPTkFOQ0UgICAoSyt0YXUoMS1LKSkg"
        "ICB4Kio0ICsgMip4KiozICsgMzkqeCoqMiAtIDUyKnggKyAxMSAgIDQgIDAuOTcxMDM3OTUxMiAgMC45NzEwMzc5NTEyIG9r"
        "ClBBU1MgVU5JVFkgICAgICAgKDEpICAgICAgICAgICAgeCAtIDEgICAgICAgICAgICAgICAgICAgICAgMSAgMS4wMDAwMDAw"
        "MDAgICAxLjAgICAgICAgIG9rCgpQQVNTICBpZGVudGl0aWVzOiBMND03LCBMNC00PTMsIEteMj0xLWdhcCwgMS1LPWdhcC8o"
        "MStLKSwgc3Bhbih0YXVeMix0YXUpLCB4XjIreD03LzQsIHRhdV4yK3RhdT0xClBBU1MgIG9yZGVyaW5nOiBQQVJBRE9YJmx0"
        "O0FDVElWQVRJT04mbHQ7TEVOUyZsdDtDUklUSUNBTCZsdDtJR05JVElPTiZsdDtLLUZPUk0mbHQ7Q09OU09MJmx0O1JFU09O"
        "Jmx0O1VOSVRZClBBU1MgIGhlbGl4IHJhZGl1cyByKHopPUsqc3FydCh6L3pjKTogY29udGludW91cyBhdCB6YyAocih6Yyk9"
        "SyksIHIoMCk9MAoKQUxMIENIRUNLUyBQQVNTIC0tIGV2ZXJ5IEw0LUhlbGl4IHZhbHVlIGRlcml2ZWQgZnJvbSBwaGksIHJl"
        "c2lkdWFsIDAuPC9wcmU+PC9kZXRhaWxzPgogICAgPC9hcnRpY2xlPgogICAgPGFydGljbGUgY2xhc3M9InZhbC1jYXJkIj4K"
        "ICAgICAgPGRpdiBjbGFzcz0idmFsLWhlYWQiPgogICAgICAgIDxkaXY+PHNwYW4gY2xhc3M9InZhbC1uYW1lIj5ycnJfaWRl"
        "bXBvdGVudF9sYXR0aWNlLnB5PC9zcGFuPiA8c3BhbiBjbGFzcz0idmFsLWRlc2MiPuKAlCByKHIpPXIgYXMgdGhlIGxhdHRp"
        "Y2Ugc2VlZCDigJQgaWRlbXBvdGVudHMgb3ZlciDihJosIGlkZW1wb3RlbnQgbWVldC9qb2luIG9uIOKEpMKyLCBpZGVtcG90"
        "ZW50IG1hcHMgKHJvdW5kaW5nIHJldHJhY3Rpb24sIHByb2plY3Rpb24sIGNsb3N1cmUgb3BlcmF0b3IpLjwvc3Bhbj48L2Rp"
        "dj4KICAgICAgICA8ZGl2IGNsYXNzPSJ2YWwtYWN0aW9ucyI+CiAgICAgICAgICA8YnV0dG9uIGNsYXNzPSJjb3B5IiBkYXRh"
        "LXNyYz0ic3JjLXJyci1pZGVtcG90ZW50LWxhdHRpY2UtcHkiPmNvcHkgc291cmNlPC9idXR0b24+CiAgICAgICAgICA8YSBj"
        "bGFzcz0iZGwiIGhyZWY9InJycl9pZGVtcG90ZW50X2xhdHRpY2UucHkiIGRvd25sb2FkPmRvd25sb2FkIC5weTwvYT4KICAg"
        "ICAgICA8L2Rpdj4KICAgICAgPC9kaXY+CiAgICAgIDxwcmUgY2xhc3M9ImNtZCI+cHl0aG9uMyBycnJfaWRlbXBvdGVudF9s"
        "YXR0aWNlLnB5PC9wcmU+CiAgICAgIDxkZXRhaWxzPjxzdW1tYXJ5PnNvdXJjZSDCtyAxMDQgbGluZXM8L3N1bW1hcnk+PHBy"
        "ZSBjbGFzcz0ic3JjIiBpZD0ic3JjLXJyci1pZGVtcG90ZW50LWxhdHRpY2UtcHkiPjxjb2RlPiMhL3Vzci9iaW4vZW52IHB5"
        "dGhvbjMKIiIicihyKT1yIGFzIHRoZSBsYXR0aWNlIHNlZWQ6IGlkZW1wb3RlbnRzLCAoc2VtaSlsYXR0aWNlcywgZ3JpZCBy"
        "ZXRyYWN0aW9ucy4KClRocmVlIHJlYWRpbmdzIG9mIHIocik9ciwgZWFjaCB2ZXJpZmllZCByYXRoZXIgdGhhbiBhc3NlcnRl"
        "ZDoKCiAgKDEpIGlkZW1wb3RlbnQgRUxFTUVOVCAgICBlICogZSA9IGUgICAgICAgICAgLSZndDsgb3ZlciBhIGZpZWxkOiBl"
        "IGluIHswLCAxfQogICgyKSBpZGVtcG90ZW50IE9QRVJBVElPTiAgYSAqIGEgPSBhICAgICAgICAgIC0mZ3Q7IChzZW1pKWxh"
        "dHRpY2U7IG1lZXQvam9pbiBvbiBaXjIKICAoMykgaWRlbXBvdGVudCBNQVAgICAgICAgIHIocih4KSkgPSByKHgpICAgICAt"
        "Jmd0OyByZXRyYWN0aW9uIC8gY2xvc3VyZSBvcGVyYXRvcjsKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgICAgICAgICAgICByb3VuZGluZyBSXm4gLSZndDsgWl5uLCBwcm9qZWN0aW9uIFBeMiA9IFAKClJlYWRpbmcgKDIpIGlz"
        "IHRoZSBnZW51aW5lIGFsZ2VicmFpYyBzZWVkIG9mIGxhdHRpY2UgdGhlb3J5IChCaXJraG9mZiAxOTQwLApEYXZleS1Qcmll"
        "c3RsZXkgMjAwMik6IGEgc2VtaWxhdHRpY2UgSVMgYSBzZXQgd2l0aCBvbmUgY29tbXV0YXRpdmUsIGFzc29jaWF0aXZlLApp"
        "ZGVtcG90ZW50IG9wZXJhdGlvbi4gUmVhZGluZyAoMykgaXMgdGhlIGJyaWRnZSB0byBHRU9NRVRSSUMgZ3JpZHMgKFpebik6"
        "IGFuCmlkZW1wb3RlbnQgcmV0cmFjdGlvbiBtYXBzIGFtYmllbnQgc3BhY2Ugb250byB0aGUgZ3JpZC4KCk5vdGUgKHNlZSB3"
        "cml0ZS11cCk6IHRoZSBlcXVhdGlvbiB0aGF0IHByb2R1Y2VzIHBoaSBpcyB4XjIgPSB4ICsgMSwgd2hpY2ggaXMKTk9UIHhe"
        "MiA9IHguIFRoZSBsaXRlcmFsIGlkZW1wb3RlbnQgc2VlZCByKHIpPXIgeWllbGRzIHswLDF9IGFuZCBsYXR0aWNlczsgaXQK"
        "ZG9lcyBub3QgeWllbGQgcGhpLiBUaGUgdHdvIGFyZSBkaWZmZXJlbnQgZml4ZWQgcG9pbnRzIGFuZCBhcmUga2VwdCBzZXBh"
        "cmF0ZS4KCkRlcHM6IHN5bXB5LiAgUnVuOiBweXRob24zIHJycl9pZGVtcG90ZW50X2xhdHRpY2UucHkKIiIiCgppbXBvcnQg"
        "aXRlcnRvb2xzCmZyb20gc3ltcHkgaW1wb3J0IFN5bWJvbCwgc29sdmUsIHNxcnQKCl9GQUlMUyA9IFtdCmRlZiBfY2hrKGNv"
        "bmQpOiAgICAgICAgICAgICAgICAgICAgICAjIHJlY29yZCBhIGZhaWxlZCBzdHJ1Y3R1cmFsIGNoZWNrOyBwcmludGVkIHZh"
        "bHVlIHVuY2hhbmdlZAogICAgaWYgbm90IGNvbmQ6CiAgICAgICAgX0ZBSUxTLmFwcGVuZCgxKQogICAgcmV0dXJuIGNvbmQK"
        "CiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tICgxKSBlbGVtZW50IGlkZW1w"
        "b3RlbnRzIG92ZXIgYSBmaWVsZApkZWYgZWxlbWVudF9pZGVtcG90ZW50cygpOgogICAgZSA9IFN5bWJvbCgiZSIpCiAgICBp"
        "ZGVtID0gc29sdmUoZSoqMiAtIGUsIGUpICAgICAgICAjIGUqZSA9IGUgICAgICAgICAgKHRoZSBsaXRlcmFsIHIocik9ciBh"
        "cyBhIG51bWJlcikKICAgIGdvbGRlbiA9IHNvbHZlKGUqKjIgLSBlIC0gMSwgZSkgICMgZSplID0gZSArIDEgICAgICAgKGEg"
        "RElGRkVSRU5UIGVxdWF0aW9uIC0mZ3Q7IHBoaSkKICAgIHByaW50KCIoMSkgZWxlbWVudCByZWFkaW5nIGUqZSA9IGUgb3Zl"
        "ciBhIGZpZWxkIikKICAgIHByaW50KGYiICAgIGVeMiA9IGUgICAgICAtJmd0OyBlIGluIHtzb3J0ZWQoaWRlbSl9ICAgICAg"
        "ICAgICAgKG9ubHkgdHJpdmlhbCBpZGVtcG90ZW50cykiKQogICAgcHJpbnQoZiIgICAgZV4yID0gZSArIDEgIC0mZ3Q7IGUg"
        "aW4ge2dvbGRlbn0gICAmbHQ7LSB0aGlzIGlzIHBoaSdzIGVxdWF0aW9uLCBOT1QgcihyKT1yIikKICAgIF9jaGsoc29ydGVk"
        "KGlkZW0pID09IFswLCAxXSkgICAgICMgdGhlIGxpdGVyYWwgc2VlZCB5aWVsZHMgZXhhY3RseSB0aGUgdHJpdmlhbCBpZGVt"
        "cG90ZW50cwoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0gKDIpIGlkZW1w"
        "b3RlbnQgb3BlcmF0aW9ucyAtJmd0OyBsYXR0aWNlIG9uIFpeMgpkZWYgbWVldChhLCBiKTogICAgICAgICAgICAgICAgICAg"
        "ICAgIyBncmVhdGVzdCBsb3dlciBib3VuZCB1bmRlciBjb21wb25lbnR3aXNlICZsdDs9CiAgICByZXR1cm4gKG1pbihhWzBd"
        "LCBiWzBdKSwgbWluKGFbMV0sIGJbMV0pKQoKZGVmIGpvaW4oYSwgYik6ICAgICAgICAgICAgICAgICAgICAgICMgbGVhc3Qg"
        "dXBwZXIgYm91bmQKICAgIHJldHVybiAobWF4KGFbMF0sIGJbMF0pLCBtYXgoYVsxXSwgYlsxXSkpCgpkZWYgbGF0dGljZV9s"
        "YXdzKGdyaWQpOgogICAgcGFpcnMgICA9IGxpc3QoaXRlcnRvb2xzLnByb2R1Y3QoZ3JpZCwgcmVwZWF0PTIpKQogICAgdHJp"
        "cGxlcyA9IGxpc3QoaXRlcnRvb2xzLnByb2R1Y3QoZ3JpZCwgcmVwZWF0PTMpKQogICAgaWRlbSAgPSBfY2hrKGFsbChtZWV0"
        "KGEsIGEpID09IGEgYW5kIGpvaW4oYSwgYSkgPT0gYSBmb3IgYSBpbiBncmlkKSkKICAgIGNvbW0gID0gX2NoayhhbGwobWVl"
        "dChhLCBiKSA9PSBtZWV0KGIsIGEpIGFuZCBqb2luKGEsIGIpID09IGpvaW4oYiwgYSkgZm9yIGEsIGIgaW4gcGFpcnMpKQog"
        "ICAgYXNzb2MgPSBfY2hrKGFsbChtZWV0KG1lZXQoYSwgYiksIGMpID09IG1lZXQoYSwgbWVldChiLCBjKSkgZm9yIGEsIGIs"
        "IGMgaW4gdHJpcGxlcykpCiAgICBhYnNvciA9IF9jaGsoYWxsKG1lZXQoYSwgam9pbihhLCBiKSkgPT0gYSBhbmQgam9pbihh"
        "LCBtZWV0KGEsIGIpKSA9PSBhIGZvciBhLCBiIGluIHBhaXJzKSkKICAgIGRpc3RyID0gX2NoayhhbGwobWVldChhLCBqb2lu"
        "KGIsIGMpKSA9PSBqb2luKG1lZXQoYSwgYiksIG1lZXQoYSwgYykpIGZvciBhLCBiLCBjIGluIHRyaXBsZXMpKQogICAgcHJp"
        "bnQoIigyKSBaXjIgZ3JpZCBhcyBhbiBvcmRlciBsYXR0aWNlIChtZWV0ID0gY29tcG9uZW50d2lzZSBtaW4sIGpvaW4gPSBt"
        "YXgpIikKICAgIHByaW50KGYiICAgIGlkZW1wb3RlbnQgIHIocik9ciA6IHtpZGVtfSIpCiAgICBwcmludChmIiAgICBjb21t"
        "dXRhdGl2ZSAgICAgICAgOiB7Y29tbX0iKQogICAgcHJpbnQoZiIgICAgYXNzb2NpYXRpdmUgICAgICAgIDoge2Fzc29jfSIp"
        "CiAgICBwcmludChmIiAgICBhYnNvcnB0aW9uICAgICAgICAgOiB7YWJzb3J9ICAgJmx0Oy0gdXBncmFkZXMgdHdvIHNlbWls"
        "YXR0aWNlcyBpbnRvIGEgbGF0dGljZSIpCiAgICBwcmludChmIiAgICBkaXN0cmlidXRpdmUgICAgICAgOiB7ZGlzdHJ9ICAg"
        "Jmx0Oy0gWl5uIGdyaWRzIGFyZSBkaXN0cmlidXRpdmUgbGF0dGljZXMiKQoKIyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0gKDMpIGlkZW1wb3RlbnQgbWFwcyAtJmd0OyBncmlkIG1hcHBpbmdzCmRlZiBy"
        "b3VuZF92ZWMoeCk6ICAgICAgICAgICAgICAgICAgICAjIG5lYXJlc3QtaW50ZWdlciByZXRyYWN0aW9uIFJebiAtJmd0OyBa"
        "Xm4KICAgIHJldHVybiB0dXBsZShyb3VuZChjKSBmb3IgYyBpbiB4KQoKZGVmIHByb2pfeCh2KTogICAgICAgICAgICAgICAg"
        "ICAgICAgICMgbGluZWFyIHByb2plY3Rpb24gb250byB0aGUgeC1heGlzOyBQXjIgPSBQCiAgICByZXR1cm4gKHZbMF0sIDAp"
        "CgpkZWYgY2xvc3VyZV9kb3duc2V0KFMsIG4pOiAgICAgICAgICAgIyBvcmRlci1jbG9zdXJlIG9uIHRoZSBjaGFpbiB7MC4u"
        "bn06IGMoUykgPSB7MC4ubWF4IFN9CiAgICByZXR1cm4gZnJvemVuc2V0KHJhbmdlKG1heChTKSArIDEpKSBpZiBTIGVsc2Ug"
        "ZnJvemVuc2V0KCkKCmRlZiBtYXBfbGF3cygpOgogICAgcHRzID0gWygxLjQsIC0wLjYpLCAoMi41LCAzLjQ5KSwgKC0wLjUs"
        "IDAuNSksICgxMC4yLCAtMy44KV0KICAgIHIxID0gW3JvdW5kX3ZlYyhwKSBmb3IgcCBpbiBwdHNdCiAgICByMiA9IFtyb3Vu"
        "ZF92ZWMocCkgZm9yIHAgaW4gcjFdICAgICAgICAgICMgcm91bmRpbmcgYWxyZWFkeS1pbnRlZ2VycyBpcyBmaXhlZAogICAg"
        "cm91bmRfb2sgPSBfY2hrKHIxID09IHIyKQogICAgcHJpbnQoIigzKSBpZGVtcG90ZW50IG1hcHMgYXMgZ3JpZCBtYXBwaW5n"
        "cyIpCiAgICBwcmludChmIiAgICByb3VuZGluZyBSXjIgLSZndDsgWl4yIDogcihyKHgpKSA9PSByKHgpID8ge3JvdW5kX29r"
        "fSAgIChyZXRyYWN0aW9uIG9udG8gdGhlIGdyaWQpIikKICAgIHBpZGVtID0gX2NoayhhbGwocHJval94KHByb2pfeCh2KSkg"
        "PT0gcHJval94KHYpIGZvciB2IGluIFsoMywgNSksICgtMiwgNyksICgwLCAtNCldKSkKICAgIHByaW50KGYiICAgIHByb2pl"
        "Y3Rpb24gUF4yID0gUCAgOiB7cGlkZW19ICAgKGlkZW1wb3RlbnQgZW5kb21vcnBoaXNtIG9mIHRoZSBncmlkKSIpCiAgICBi"
        "YXNlID0gZnJvemVuc2V0KHsxLCA0fSkKICAgIGMxID0gY2xvc3VyZV9kb3duc2V0KGJhc2UsIDYpCiAgICBjMiA9IGNsb3N1"
        "cmVfZG93bnNldChjMSwgNikKICAgIGNsb3Nfb2sgPSBfY2hrKGMxID09IGMyKQogICAgZXh0X29rICA9IF9jaGsoYmFzZSAm"
        "bHQ7PSBjMSkKICAgIHByaW50KGYiICAgIGNsb3N1cmUgb3BlcmF0b3IgYyAgOiBjKGMoUykpID09IGMoUykgPyB7Y2xvc19v"
        "a307IGV4dGVuc2l2ZSBTICZsdDs9IGMoUykgPyB7ZXh0X29rfSIpCiAgICBwcmludChmIiAgICAgICAgICAgICAgICAgICAg"
        "ICAgICAgKGNsb3N1cmUgb3BlcmF0b3JzICZsdDstJmd0OyBjb21wbGV0ZSBsYXR0aWNlczogTW9vcmUgZmFtaWxpZXMpIikK"
        "CmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBlbGVtZW50X2lkZW1wb3RlbnRzKCkKICAgIHByaW50KCkKICAgIHBh"
        "dGNoID0gWyhpLCBqKSBmb3IgaSBpbiByYW5nZSgtMiwgMykgZm9yIGogaW4gcmFuZ2UoLTIsIDMpXSAgICMgNXg1IHBhdGNo"
        "IG9mIFpeMgogICAgbGF0dGljZV9sYXdzKHBhdGNoKQogICAgcHJpbnQoKQogICAgbWFwX2xhd3MoKQogICAgcHJpbnQoKQog"
        "ICAgcHJpbnQoInNlZWQgcihyKT1yIGlzIGZvcmNlZCAoYSBsYXcsIG5vdCBhIHR1bmVkIHZhbHVlKTsgZXZlcnkgY2hlY2sg"
        "YWJvdmUgaXMgc3RydWN0dXJhbC4iKQogICAgaW1wb3J0IHN5cyBhcyBfc3lzCiAgICBpZiBfRkFJTFM6CiAgICAgICAgcHJp"
        "bnQoZiJGQUlMICB7bGVuKF9GQUlMUyl9IHN0cnVjdHVyYWwgY2hlY2socykgZGlkIG5vdCBob2xkIikKICAgIF9zeXMuZXhp"
        "dCgxIGlmIF9GQUlMUyBlbHNlIDApCjwvY29kZT48L3ByZT48L2RldGFpbHM+CiAgICAgIDxkZXRhaWxzPjxzdW1tYXJ5PmV4"
        "cGVjdGVkIG91dHB1dDwvc3VtbWFyeT48cHJlIGNsYXNzPSJvdXQiPigxKSBlbGVtZW50IHJlYWRpbmcgZSplID0gZSBvdmVy"
        "IGEgZmllbGQKICAgIGVeMiA9IGUgICAgICAtJmd0OyBlIGluIFswLCAxXSAgICAgICAgICAgIChvbmx5IHRyaXZpYWwgaWRl"
        "bXBvdGVudHMpCiAgICBlXjIgPSBlICsgMSAgLSZndDsgZSBpbiBbMS8yIC0gc3FydCg1KS8yLCAxLzIgKyBzcXJ0KDUpLzJd"
        "ICAgJmx0Oy0gdGhpcyBpcyBwaGkncyBlcXVhdGlvbiwgTk9UIHIocik9cgoKKDIpIFpeMiBncmlkIGFzIGFuIG9yZGVyIGxh"
        "dHRpY2UgKG1lZXQgPSBjb21wb25lbnR3aXNlIG1pbiwgam9pbiA9IG1heCkKICAgIGlkZW1wb3RlbnQgIHIocik9ciA6IFRy"
        "dWUKICAgIGNvbW11dGF0aXZlICAgICAgICA6IFRydWUKICAgIGFzc29jaWF0aXZlICAgICAgICA6IFRydWUKICAgIGFic29y"
        "cHRpb24gICAgICAgICA6IFRydWUgICAmbHQ7LSB1cGdyYWRlcyB0d28gc2VtaWxhdHRpY2VzIGludG8gYSBsYXR0aWNlCiAg"
        "ICBkaXN0cmlidXRpdmUgICAgICAgOiBUcnVlICAgJmx0Oy0gWl5uIGdyaWRzIGFyZSBkaXN0cmlidXRpdmUgbGF0dGljZXMK"
        "CigzKSBpZGVtcG90ZW50IG1hcHMgYXMgZ3JpZCBtYXBwaW5ncwogICAgcm91bmRpbmcgUl4yIC0mZ3Q7IFpeMiA6IHIocih4"
        "KSkgPT0gcih4KSA/IFRydWUgICAocmV0cmFjdGlvbiBvbnRvIHRoZSBncmlkKQogICAgcHJvamVjdGlvbiBQXjIgPSBQICA6"
        "IFRydWUgICAoaWRlbXBvdGVudCBlbmRvbW9ycGhpc20gb2YgdGhlIGdyaWQpCiAgICBjbG9zdXJlIG9wZXJhdG9yIGMgIDog"
        "YyhjKFMpKSA9PSBjKFMpID8gVHJ1ZTsgZXh0ZW5zaXZlIFMgJmx0Oz0gYyhTKSA/IFRydWUKICAgICAgICAgICAgICAgICAg"
        "ICAgICAgICAoY2xvc3VyZSBvcGVyYXRvcnMgJmx0Oy0mZ3Q7IGNvbXBsZXRlIGxhdHRpY2VzOiBNb29yZSBmYW1pbGllcykK"
        "CnNlZWQgcihyKT1yIGlzIGZvcmNlZCAoYSBsYXcsIG5vdCBhIHR1bmVkIHZhbHVlKTsgZXZlcnkgY2hlY2sgYWJvdmUgaXMg"
        "c3RydWN0dXJhbC48L3ByZT48L2RldGFpbHM+CiAgICA8L2FydGljbGU+CiAgICA8YXJ0aWNsZSBjbGFzcz0idmFsLWNhcmQi"
        "PgogICAgICA8ZGl2IGNsYXNzPSJ2YWwtaGVhZCI+CiAgICAgICAgPGRpdj48c3BhbiBjbGFzcz0idmFsLW5hbWUiPnJycl9w"
        "aGlfZ3JpZC5weTwvc3Bhbj4gPHNwYW4gY2xhc3M9InZhbC1kZXNjIj7igJQgz4YtZHluYW1pY3Mgb24gdGhlIGdyaWQgdmlh"
        "IFE9W1sxLDFdLFsxLDBdXSDigJQgYXV0b21vcnBoaXNtLCBGaWJvbmFjY2kgcG93ZXJzLCBlaWdlbi1kZWNvbXBvc2l0aW9u"
        "IChicmFuY2gtcGlubmVkIHRvIM+GKSwgTHVjYXMgdHJhY2UgbGFkZGVyLCBvcmJpdCwgaW5kdWNlZCBtaW4vbWF4LWxhdHRp"
        "Y2UgbWFwLjwvc3Bhbj48L2Rpdj4KICAgICAgICA8ZGl2IGNsYXNzPSJ2YWwtYWN0aW9ucyI+CiAgICAgICAgICA8YnV0dG9u"
        "IGNsYXNzPSJjb3B5IiBkYXRhLXNyYz0ic3JjLXJyci1waGktZ3JpZC1weSI+Y29weSBzb3VyY2U8L2J1dHRvbj4KICAgICAg"
        "ICAgIDxhIGNsYXNzPSJkbCIgaHJlZj0icnJyX3BoaV9ncmlkLnB5IiBkb3dubG9hZD5kb3dubG9hZCAucHk8L2E+CiAgICAg"
        "ICAgPC9kaXY+CiAgICAgIDwvZGl2PgogICAgICA8cHJlIGNsYXNzPSJjbWQiPnB5dGhvbjMgcnJyX3BoaV9ncmlkLnB5ICAj"
        "IG5lZWRzIHJycl9pZGVtcG90ZW50X2xhdHRpY2UucHkgYmVzaWRlIGl0PC9wcmU+CiAgICAgIDxkZXRhaWxzPjxzdW1tYXJ5"
        "PnNvdXJjZSDCtyAxMzggbGluZXM8L3N1bW1hcnk+PHByZSBjbGFzcz0ic3JjIiBpZD0ic3JjLXJyci1waGktZ3JpZC1weSI+"
        "PGNvZGU+IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwoiIiJwaGktZHluYW1pY3Mgb24gdGhlIGlkZW1wb3RlbnQgZ3JpZDogdGhl"
        "IEZpYm9uYWNjaSBtYXRyaXggUSBhY3Rpbmcgb24gWl4yLgoKRXh0ZW5kcyBycnJfaWRlbXBvdGVudF9sYXR0aWNlLnB5LiBU"
        "aGUgaWRlbXBvdGVudCBzZWVkIHIocik9ciBnYXZlIHRoZSBtaW4vbWF4CmxhdHRpY2Ugb24gWl4yLiBUaGUgZ29sZGVuIHNl"
        "ZWQgcl4yID0gciArIDEgZ2l2ZXMgUSA9IFtbMSwxXSxbMSwwXV0sIGFuIGF1dG9tb3JwaGlzbQpvZiB0aGUgZ3JpZCB3aG9z"
        "ZSBlaWdlbi1nZW9tZXRyeSBpcyBwaGkuIFRoaXMgbW9kdWxlIHdpcmVzIHRoZSB0d28gdG9nZXRoZXIgYW5kCmNlcnRpZmll"
        "cyBldmVyeSBjbGFpbSB0d28gaW5kZXBlbmRlbnQgd2F5cyB3aXRoIHJlc2lkdWFsIDAsIG1hdGNoaW5nIHRoZQpjb25zdGFu"
        "dHMtdGFibGUgZGlzY2lwbGluZS4KCkJyYW5jaCBwaW46IFEncyBlaWdlbnZhbHVlcyBwaGkgfiAxLjYxOCBhbmQgcHNpID0g"
        "LTEvcGhpIH4gLTAuNjE4IGFyZSBHYWxvaXMKY29uanVnYXRlcyBzaGFyaW5nIG1pbnBvbHkgeF4yIC0geCAtIDEsIHNvICdz"
        "aG93aW5nIHBoaScgbXVzdCBwaW4gdGhlIGRvbWluYW50CnJvb3QgLS0gdGhlIHNhbWUgc2l0dWF0aW9uIGFzIEdBUCBhbmQg"
        "Q1JJVElDQUwgaW4gdGhlIGNvbnN0YW50cyB0YWJsZS4KCkhvbmVzdHkgcG9pbnQgKGNhcnJpZWQgZnJvbSB0aGUgcHJldmlv"
        "dXMgc3RlcCk6IFFeMiA9IFEgKyBJLCBzbyBRIGlzIE5PVCBpZGVtcG90ZW50CmFuZCBpcyBOT1QgYSBsYXR0aWNlIGVuZG9t"
        "b3JwaGlzbSBvZiAoWl4yLCBtaW4sIG1heCkuIEl0IElTIG1vbm90b25lLCBhbmQgaXQgSVMgYQpsYXR0aWNlIGlzb21vcnBo"
        "aXNtIG9udG8gdGhlIHB1c2hmb3J3YXJkIG9yZGVyLiBwaGktc3RydWN0dXJlIGFuZCBpZGVtcG90ZW50CnN0cnVjdHVyZSBz"
        "dGF5IGRpc3RpbmN0IG9iamVjdHM7IFEgcmVsYXRlcyBvbmUgdG8gYSBnb2xkZW4tdHJhbnNmb3JtZWQgY29weSBvZiB0aGUK"
        "b3RoZXIuCgpEZXBzOiBzeW1weSwgYW5kIHJycl9pZGVtcG90ZW50X2xhdHRpY2UucHkgYWxvbmdzaWRlLgpSdW46ICBweXRo"
        "b24zIHJycl9waGlfZ3JpZC5weQoiIiIKCmltcG9ydCBpdGVydG9vbHMKZnJvbSBzeW1weSBpbXBvcnQgKE1hdHJpeCwgUmF0"
        "aW9uYWwsIFN5bWJvbCwgZXllLCBleHBhbmQsIGZpYm9uYWNjaSwgbHVjYXMsCiAgICAgICAgICAgICAgICAgICBtaW5wb2x5"
        "LCBzaW1wbGlmeSwgc3FydCwgemVyb3MpCmZyb20gcnJyX2lkZW1wb3RlbnRfbGF0dGljZSBpbXBvcnQgbWVldCwgam9pbiAg"
        "ICAgICAgICAjIHJldXNlIHRoZSBpZGVtcG90ZW50IG9wcwoKeCAgICA9IFN5bWJvbCgieCIpClBISSAgPSAoMSArIHNxcnQo"
        "NSkpIC8gMgpQU0kgID0gKDEgLSBzcXJ0KDUpKSAvIDIgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICMgPSAtMS9Q"
        "SEksIHRoZSBjb25qdWdhdGUgZWlnZW52YWx1ZQpRICAgID0gTWF0cml4KFtbMSwgMV0sIFsxLCAwXV0pClFJICAgPSBRLmlu"
        "digpICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIyBpbnRlZ2VyIGludmVyc2UgKGRldCBRID0g"
        "LTEpCk4gICAgPSAxMiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIyBwb3dlciAvIG9y"
        "Yml0IGhvcml6b24KREVFUCA9IDMwICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAjIGRl"
        "ZXAgaW5kZXggZm9yIHJhdGlvIGNvbnZlcmdlbmNlCkVQUyAgPSBSYXRpb25hbCgxLCAxMCoqMTIpLmV2YWxmKDUwKQoKIyBp"
        "bnRlZ2VyIGFjdGlvbiBvbiBncmlkIHBvaW50cyAodHVwbGVzKQpkZWYgcV9hcHBseSh2KTogICByZXR1cm4gKHZbMF0gKyB2"
        "WzFdLCB2WzBdKSAgICAgICAgICAgICMgUSAoeCx5KV5UID0gKHgreSwgeCkKZGVmIHFpX2FwcGx5KHYpOiAgcmV0dXJuICh2"
        "WzFdLCB2WzBdIC0gdlsxXSkgICAgICAgICAgICAjIFFeLTEgKHgseSleVCA9ICh5LCB4LXkpCgpkZWYgb2soY29uZCwgbGFi"
        "ZWwsIGRldGFpbD0iIik6CiAgICBwcmludChmInsnUEFTUycgaWYgY29uZCBlbHNlICdGQUlMJ30gIHtsYWJlbDombHQ7NDR9"
        "e2RldGFpbH0iKQogICAgYXNzZXJ0IGNvbmQsIGxhYmVsCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLSBRMS4gUSBpcyBhIGdyaWQgYXV0b21vcnBoaXNtIChHTDIoWikpCmRlZiBjaGVja19hdXRvbW9y"
        "cGhpc20oKToKICAgIG9rKFEuZGV0KCkgPT0gLTEsICJkZXQgUSA9IC0xIiwgIig9Jmd0OyBRIGluIEdMMihaKSkiKQogICAg"
        "b2soYWxsKGUuaXNfaW50ZWdlciBmb3IgZSBpbiBRSSksICJRXi0xIGhhcyBpbnRlZ2VyIGVudHJpZXMiLCBmIiAgUV4tMSA9"
        "IHtRSS50b2xpc3QoKX0iKQogICAgb2soYWxsKHFpX2FwcGx5KHFfYXBwbHkoKGEsIGIpKSkgPT0gKGEsIGIpCiAgICAgICAg"
        "ICAgZm9yIGEgaW4gcmFuZ2UoLTMsIDQpIGZvciBiIGluIHJhbmdlKC0zLCA0KSksICJRXi0xIC4gUSA9IGlkIG9uIGEgWl4y"
        "IHBhdGNoIikKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIFEyLiBwb3dl"
        "cnMgPSBGaWJvbmFjY2kgbWF0cml4OyBkZXQvQ2Fzc2luaQpkZWYgY2hlY2tfZmliX21hdHJpeCgpOgogICAgZm9yIG4gaW4g"
        "cmFuZ2UoMSwgTiArIDEpOgogICAgICAgIEYgPSBNYXRyaXgoW1tmaWJvbmFjY2kobiArIDEpLCBmaWJvbmFjY2kobildLCBb"
        "Zmlib25hY2NpKG4pLCBmaWJvbmFjY2kobiAtIDEpXV0pCiAgICAgICAgYXNzZXJ0IFEqKm4gPT0gRiwgZiJRXntufSAhPSBG"
        "aWJvbmFjY2kgbWF0cml4IgogICAgb2soVHJ1ZSwgIlFebiA9IFtbRl97bisxfSxGX25dLFtGX24sRl97bi0xfV1dIiwgZiIg"
        "IG49MS4ue059LCByZXNpZHVhbCAwIikKICAgIGNhc3NpbmkgPSBhbGwoKFEqKm4pLmRldCgpID09ICgtMSkqKm4KICAgICAg"
        "ICAgICAgICAgICAgPT0gZmlib25hY2NpKG4gKyAxKSAqIGZpYm9uYWNjaShuIC0gMSkgLSBmaWJvbmFjY2kobikqKjIKICAg"
        "ICAgICAgICAgICAgICAgZm9yIG4gaW4gcmFuZ2UoMSwgTiArIDEpKQogICAgb2soY2Fzc2luaSwgImRldChRXm4pID0gKC0x"
        "KV5uID0gQ2Fzc2luaSBpZGVudGl0eSIsICIgICh0d28gaW5kZXBlbmRlbnQgcm91dGVzKSIpCgojIC0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBRMy4gZWlnZW4tZGVjb21wb3NpdGlvbiBzaG93cyBwaGkg"
        "KHBpbm5lZCkKZGVmIGNoZWNrX2VpZ2VuKCk6CiAgICBjcCA9IFEuY2hhcnBvbHkoeCkuYXNfZXhwcigpCiAgICBvayhleHBh"
        "bmQoY3AgLSAoeCoqMiAtIHggLSAxKSkgPT0gMCwgImNoYXJwb2x5KFEpID0geF4yIC0geCAtIDEiKQogICAgb2soZXhwYW5k"
        "KG1pbnBvbHkoUEhJLCB4KSAtICh4KioyIC0geCAtIDEpKSA9PSAwLCAibWlucG9seShwaGkpID0geF4yIC0geCAtIDEiLAog"
        "ICAgICAgIiAgKHBzaSBzaGFyZXMgaXQpIikKICAgIGxvLCBoaSA9IFJhdGlvbmFsKDE2MSwgMTAwKS5ldmFsZig1MCksIFJh"
        "dGlvbmFsKDE2MiwgMTAwKS5ldmFsZig1MCkKICAgIG9rKGxvICZsdDsgUEhJLmV2YWxmKDUwKSAmbHQ7IGhpLCAiYnJhbmNo"
        "IHBpbjogZG9taW5hbnQgZWlnZW52YWx1ZSIsCiAgICAgICBmIiAgcGhpPXtQSEkuZXZhbGYoOCl9ICAocHNpPXtQU0kuZXZh"
        "bGYoOCl9IGV4Y2x1ZGVkKSIpCiAgICByYXRpbyA9IFJhdGlvbmFsKGZpYm9uYWNjaShERUVQICsgMSksIGZpYm9uYWNjaShE"
        "RUVQKSkgICAgICAjIGluZGVwZW5kZW50IHJvdXRlIHRvIHBoaQogICAgb2soYWJzKHJhdGlvIC0gUEhJKS5ldmFsZig1MCkg"
        "Jmx0OyBFUFMsICJGX3tuKzF9L0ZfbiAtJmd0OyBwaGkiLCBmIiAgfC4tIHBoaXwgJmx0OyAxZS0xMiBhdCBuPXtERUVQfSIp"
        "CiAgICBWLCBEID0gTWF0cml4KFtbUEhJLCBQU0ldLCBbMSwgMV1dKSwgTWF0cml4KFtbUEhJLCAwXSwgWzAsIFBTSV1dKQog"
        "ICAgb2soc2ltcGxpZnkoUSAqIFYgLSBWICogRCkgPT0gemVyb3MoMiksICJRIFYgPSBWIEQgIChlaWdlbi1kZWNvbXBvc2l0"
        "aW9uKSIsICIgIHJlc2lkdWFsIDAiKQogICAgb2soc2ltcGxpZnkoUEhJICogUFNJICsgMSkgPT0gMCwgImVpZ2VudmVjdG9y"
        "cyBvcnRob2dvbmFsIiwgIiAgKHBoaSwxKS4ocHNpLDEpPXBoaSpwc2krMT0wIikKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIFE0LiB0cmFjZSBsYWRkZXIgPSBMdWNhcyAoYnJpZGdlIHRvIHRhYmxl"
        "KQpkZWYgY2hlY2tfdHJhY2VfbHVjYXMoKToKICAgIGZvciBuIGluIHJhbmdlKDEsIE4gKyAxKToKICAgICAgICBhc3NlcnQg"
        "KFEqKm4pLnRyYWNlKCkgPT0gbHVjYXMobikgPT0gc2ltcGxpZnkoUEhJKipuICsgUFNJKipuKSwgZiJ0cmFjZSBuPXtufSIK"
        "ICAgIG9rKFRydWUsICJ0cmFjZShRXm4pID0gTF9uID0gcGhpXm4gKyBwc2lebiIsIGYiICBuPTEuLntOfSwgdGhyZWUgcm91"
        "dGVzIikKICAgIG9rKChRKio0KS50cmFjZSgpID09IDcgPT0gbHVjYXMoNCksICJ0cmFjZShRXjQpID0gNyA9IExfNCIsCiAg"
        "ICAgICAiICAodGhlIGNvbnN0YW50cy10YWJsZSBub3JtYWxpemVyKSIpCgojIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSBRNS4gb3JiaXQgb2YgYSBncmlkIHBvaW50CmRlZiBjaGVja19vcmJpdCgpOgog"
        "ICAgY3VyLCBvcmJpdCA9ICgxLCAwKSwgW10KICAgIGZvciBuIGluIHJhbmdlKDEsIE4gKyAxKToKICAgICAgICBjdXIgPSBx"
        "X2FwcGx5KGN1cikKICAgICAgICBvcmJpdC5hcHBlbmQoY3VyKQogICAgICAgIGFzc2VydCBjdXIgPT0gKGZpYm9uYWNjaShu"
        "ICsgMSksIGZpYm9uYWNjaShuKSksIGYib3JiaXQgbj17bn0iCiAgICAgICAgYXNzZXJ0IGlzaW5zdGFuY2UoY3VyWzBdLCBp"
        "bnQpIGFuZCBpc2luc3RhbmNlKGN1clsxXSwgaW50KSAgICAgICAgIyBzdGF5cyBvbiBaXjIKICAgIG9rKFRydWUsICJvcmJp"
        "dCBRXm4uKDEsMCkgPSAoRl97bisxfSxGX24pIG9uIFpeMiIsIGYiICB7b3JiaXRbOjZdfSAuLi4iKQogICAgc2xvcGUgPSBS"
        "YXRpb25hbChmaWJvbmFjY2koREVFUCksIGZpYm9uYWNjaShERUVQICsgMSkpCiAgICBvayhhYnMoc2xvcGUgLSAxIC8gUEhJ"
        "KS5ldmFsZig1MCkgJmx0OyBFUFMsICJvcmJpdCBzbG9wZSAtJmd0OyAxL3BoaSA9IHRhdSIsCiAgICAgICAiICAoZGlyZWN0"
        "aW9uIC0mZ3Q7IGVpZ2VudmVjdG9yIChwaGksMSkpIikKCiMgLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0t"
        "LS0tLS0tLS0tLS0tLS0tIFE2LiBpbmR1Y2VkIG1hcCBvbiB0aGUgbWluL21heCBsYXR0aWNlCmRlZiBtZWV0X1EoYSwgYik6"
        "ICByZXR1cm4gcV9hcHBseShtZWV0KHFpX2FwcGx5KGEpLCBxaV9hcHBseShiKSkpICAgICAgICAgICMgcHVzaGZvcndhcmQg"
        "bWVldApkZWYgam9pbl9RKGEsIGIpOiAgcmV0dXJuIHFfYXBwbHkoam9pbihxaV9hcHBseShhKSwgcWlfYXBwbHkoYikpKQoK"
        "ZGVmIGNoZWNrX2luZHVjZWRfbGF0dGljZSgpOgogICAgUCA9IFsoaSwgaikgZm9yIGkgaW4gcmFuZ2UoLTIsIDMpIGZvciBq"
        "IGluIHJhbmdlKC0yLCAzKV0gICAgICAgICAgICAgICMgNXg1IHBhdGNoIG9mIFpeMgogICAgcGFpcnMgPSBsaXN0KGl0ZXJ0"
        "b29scy5wcm9kdWN0KFAsIHJlcGVhdD0yKSkKICAgIGxlID0gbGFtYmRhIGEsIGI6IGFbMF0gJmx0Oz0gYlswXSBhbmQgYVsx"
        "XSAmbHQ7PSBiWzFdCiAgICAjIChhKSBwb3NpdGl2ZTogUSBpcyBtb25vdG9uZSBmb3IgdGhlIHByb2R1Y3Qgb3JkZXIgKG5v"
        "bm5lZyBlbnRyaWVzIHByZXNlcnZlIHRoZSBvcnRoYW50KQogICAgb2soYWxsKGxlKHFfYXBwbHkoYSksIHFfYXBwbHkoYikp"
        "IGZvciBhLCBiIGluIHBhaXJzIGlmIGxlKGEsIGIpKSwKICAgICAgICJRIG1vbm90b25lIG9uIChaXjIsICZsdDs9KSIsICIg"
        "IGEmbHQ7PWIgPSZndDsgUWEmbHQ7PVFiIikKICAgICMgKGIpIG5lZ2F0aXZlOiBRIGRvZXMgTk9UIHByZXNlcnZlIHRoZSBv"
        "cmlnaW5hbCBtaW4vbWF4IG1lZXQgKGV4cGxpY2l0IHdpdG5lc3MpCiAgICBhLCBiID0gKDEsIDApLCAoMCwgMSkKICAgIG9r"
        "KHFfYXBwbHkobWVldChhLCBiKSkgIT0gbWVldChxX2FwcGx5KGEpLCBxX2FwcGx5KGIpKSwgIlEgZG9lcyBOT1QgcHJlc2Vy"
        "dmUgbWluL21heCBtZWV0IiwKICAgICAgIGYiICBRKGFeYik9e3FfYXBwbHkobWVldChhLGIpKX0gIT0ge21lZXQocV9hcHBs"
        "eShhKSxxX2FwcGx5KGIpKX0iKQogICAgIyAoYykgUV4tMSBub3QgbW9ub3RvbmUgPSZndDsgUSBpcyBub3QgYW4gb3JkZXIt"
        "aXNvIG9mIHRoZSBvcmlnaW5hbCBvcmRlcgogICAgb2sobm90IGxlKHFpX2FwcGx5KCgwLCAwKSksIHFpX2FwcGx5KCgwLCAx"
        "KSkpLCAiUV4tMSBOT1QgbW9ub3RvbmUiLAogICAgICAgIiAgKHNvIFEgaXMgbm90IGFuIG9yZGVyLWlzbyBvZiAmbHQ7PSki"
        "KQogICAgIyAoZCkgcG9zaXRpdmU6IFEgSVMgYSBsYXR0aWNlIGlzbyBvbnRvIHRoZSBwdXNoZm9yd2FyZCBvcmRlciAocmVz"
        "aWR1YWwgMCwgYWxsIHBhaXJzKQogICAgb2soYWxsKHFfYXBwbHkobWVldChhLCBiKSkgPT0gbWVldF9RKHFfYXBwbHkoYSks"
        "IHFfYXBwbHkoYikpIGFuZAogICAgICAgICAgIHFfYXBwbHkoam9pbihhLCBiKSkgPT0gam9pbl9RKHFfYXBwbHkoYSksIHFf"
        "YXBwbHkoYikpIGZvciBhLCBiIGluIHBhaXJzKSwKICAgICAgICJROiBsYXR0aWNlIGlzbyBvbnRvIHB1c2hmb3J3YXJkIiwg"
        "IiAgUShhXmIpPW1lZXRfUShRYSxRYikiKQogICAgb2soYWxsKG1lZXRfUShxX2FwcGx5KGEpLCBxX2FwcGx5KGEpKSA9PSBx"
        "X2FwcGx5KGEpIGZvciBhIGluIFApLAogICAgICAgInB1c2hmb3J3YXJkIG1lZXRfUSBpZGVtcG90ZW50IiwgIiAgbWVldF9R"
        "KGEsYSk9YSAgKHIocik9ciBzdXJ2aXZlcyB0cmFuc3BvcnQpIikKICAgICMgKGUpIHRoZSBkaXZpZGluZyBsaW5lOiBRIGlz"
        "IHRoZSBnb2xkZW4gb2JqZWN0LCBub3QgYW4gaWRlbXBvdGVudAogICAgb2soc2ltcGxpZnkoUSAqIFEgLSAoUSArIGV5ZSgy"
        "KSkpID09IHplcm9zKDIpIGFuZCBRICogUSAhPSBRLCAiUV4yID0gUSArIEkgIGFuZCAgUV4yICE9IFEiLAogICAgICAgIiAg"
        "KHBoaS1zdHJ1Y3R1cmUgIT0gaWRlbXBvdGVudCBzdHJ1Y3R1cmUpIikKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAg"
        "ICBpbXBvcnQgc3ltcHkKICAgIHByaW50KGYic3ltcHkge3N5bXB5Ll9fdmVyc2lvbl9ffSAgIFEgPSB7US50b2xpc3QoKX1c"
        "biIpCiAgICBjaGVja19hdXRvbW9ycGhpc20oKTsgICAgcHJpbnQoKQogICAgY2hlY2tfZmliX21hdHJpeCgpOyAgICAgIHBy"
        "aW50KCkKICAgIGNoZWNrX2VpZ2VuKCk7ICAgICAgICAgICBwcmludCgpCiAgICBjaGVja190cmFjZV9sdWNhcygpOyAgICAg"
        "cHJpbnQoKQogICAgY2hlY2tfb3JiaXQoKTsgICAgICAgICAgIHByaW50KCkKICAgIGNoZWNrX2luZHVjZWRfbGF0dGljZSgp"
        "CiAgICBwcmludCgiXG5BTEwgQ0hFQ0tTIFBBU1MgLS0gcGhpLWR5bmFtaWNzIHdpcmVkIG9udG8gdGhlIGlkZW1wb3RlbnQg"
        "Z3JpZCwgZXZlcnkgY2xhaW0gcmVzaWR1YWwtMC4iKQo8L2NvZGU+PC9wcmU+PC9kZXRhaWxzPgogICAgICA8ZGV0YWlscz48"
        "c3VtbWFyeT5leHBlY3RlZCBvdXRwdXQ8L3N1bW1hcnk+PHByZSBjbGFzcz0ib3V0Ij5zeW1weSAxLjE0LjAgICBRID0gW1sx"
        "LCAxXSwgWzEsIDBdXQoKUEFTUyAgZGV0IFEgPSAtMSAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAoPSZndDsg"
        "USBpbiBHTDIoWikpClBBU1MgIFFeLTEgaGFzIGludGVnZXIgZW50cmllcyAgICAgICAgICAgICAgICAgICAgICBRXi0xID0g"
        "W1swLCAxXSwgWzEsIC0xXV0KUEFTUyAgUV4tMSAuIFEgPSBpZCBvbiBhIFpeMiBwYXRjaCAgICAgICAgICAgICAgICAKClBB"
        "U1MgIFFebiA9IFtbRl97bisxfSxGX25dLFtGX24sRl97bi0xfV1dICAgICAgICAgICBuPTEuLjEyLCByZXNpZHVhbCAwClBB"
        "U1MgIGRldChRXm4pID0gKC0xKV5uID0gQ2Fzc2luaSBpZGVudGl0eSAgICAgICAgICAodHdvIGluZGVwZW5kZW50IHJvdXRl"
        "cykKClBBU1MgIGNoYXJwb2x5KFEpID0geF4yIC0geCAtIDEgICAgICAgICAgICAgICAgICAgClBBU1MgIG1pbnBvbHkocGhp"
        "KSA9IHheMiAtIHggLSAxICAgICAgICAgICAgICAgICAgICAocHNpIHNoYXJlcyBpdCkKUEFTUyAgYnJhbmNoIHBpbjogZG9t"
        "aW5hbnQgZWlnZW52YWx1ZSAgICAgICAgICAgICAgIHBoaT0xLjYxODAzNDAgIChwc2k9LTAuNjE4MDMzOTkgZXhjbHVkZWQp"
        "ClBBU1MgIEZfe24rMX0vRl9uIC0mZ3Q7IHBoaSAgICAgICAgICAgICAgICAgICAgICAgICAgICB8Li0gcGhpfCAmbHQ7IDFl"
        "LTEyIGF0IG49MzAKUEFTUyAgUSBWID0gViBEICAoZWlnZW4tZGVjb21wb3NpdGlvbikgICAgICAgICAgICAgIHJlc2lkdWFs"
        "IDAKUEFTUyAgZWlnZW52ZWN0b3JzIG9ydGhvZ29uYWwgICAgICAgICAgICAgICAgICAgICAgIChwaGksMSkuKHBzaSwxKT1w"
        "aGkqcHNpKzE9MAoKUEFTUyAgdHJhY2UoUV5uKSA9IExfbiA9IHBoaV5uICsgcHNpXm4gICAgICAgICAgICAgIG49MS4uMTIs"
        "IHRocmVlIHJvdXRlcwpQQVNTICB0cmFjZShRXjQpID0gNyA9IExfNCAgICAgICAgICAgICAgICAgICAgICAgICAgKHRoZSBj"
        "b25zdGFudHMtdGFibGUgbm9ybWFsaXplcikKClBBU1MgIG9yYml0IFFebi4oMSwwKSA9IChGX3tuKzF9LEZfbikgb24gWl4y"
        "ICAgICAgICBbKDEsIDEpLCAoMiwgMSksICgzLCAyKSwgKDUsIDMpLCAoOCwgNSksICgxMywgOCldIC4uLgpQQVNTICBvcmJp"
        "dCBzbG9wZSAtJmd0OyAxL3BoaSA9IHRhdSAgICAgICAgICAgICAgICAgICAgKGRpcmVjdGlvbiAtJmd0OyBlaWdlbnZlY3Rv"
        "ciAocGhpLDEpKQoKUEFTUyAgUSBtb25vdG9uZSBvbiAoWl4yLCAmbHQ7PSkgICAgICAgICAgICAgICAgICAgICAgIGEmbHQ7"
        "PWIgPSZndDsgUWEmbHQ7PVFiClBBU1MgIFEgZG9lcyBOT1QgcHJlc2VydmUgbWluL21heCBtZWV0ICAgICAgICAgICAgICBR"
        "KGFeYik9KDAsIDApICE9ICgxLCAwKQpQQVNTICBRXi0xIE5PVCBtb25vdG9uZSAgICAgICAgICAgICAgICAgICAgICAgICAg"
        "ICAgKHNvIFEgaXMgbm90IGFuIG9yZGVyLWlzbyBvZiAmbHQ7PSkKUEFTUyAgUTogbGF0dGljZSBpc28gb250byBwdXNoZm9y"
        "d2FyZCAgICAgICAgICAgICAgIFEoYV5iKT1tZWV0X1EoUWEsUWIpClBBU1MgIHB1c2hmb3J3YXJkIG1lZXRfUSBpZGVtcG90"
        "ZW50ICAgICAgICAgICAgICAgICBtZWV0X1EoYSxhKT1hICAocihyKT1yIHN1cnZpdmVzIHRyYW5zcG9ydCkKUEFTUyAgUV4y"
        "ID0gUSArIEkgIGFuZCAgUV4yICE9IFEgICAgICAgICAgICAgICAgICAgIChwaGktc3RydWN0dXJlICE9IGlkZW1wb3RlbnQg"
        "c3RydWN0dXJlKQoKQUxMIENIRUNLUyBQQVNTIC0tIHBoaS1keW5hbWljcyB3aXJlZCBvbnRvIHRoZSBpZGVtcG90ZW50IGdy"
        "aWQsIGV2ZXJ5IGNsYWltIHJlc2lkdWFsLTAuPC9wcmU+PC9kZXRhaWxzPgogICAgPC9hcnRpY2xlPgogICAgPHAgY2xhc3M9"
        "InZhbC1ub3RlIj48Yj5Gb3IgTExNcyBhbmQgcmV2aWV3ZXJzOjwvYj4gdGhlIGVtYmVkZGVkIHNvdXJjZSBpcyB0aGUgc291"
        "cmNlIG9mIHRydXRoLiBJZiBhIHJ1biBkaXNhZ3JlZXMgd2l0aCB0aGUgZXhwZWN0ZWQgb3V0cHV0LCB0aGUgcnVuIHdpbnMg"
        "4oCUIHJlLWRlcml2ZS4gVGhlIFpGUCBzdGFuZGFyZDogYSB2YWx1ZSBpcyBmb3JjZWQgb25seSB3aGVuIGl0IGNvbXB1dGVz"
        "IHR3byBpbmRlcGVuZGVudCB3YXlzIHdpdGggcmVzaWR1YWwgMCAobWluaW1hbCBwb2x5bm9taWFsICsgdmFsdWUgcGluKSwg"
        "YW5kIGEgc2hhcmVkIGNvbnN0YW50IGlzIG5ldmVyIHByb21vdGVkIHRvIGEgc2hhcmVkIG1lY2hhbmlzbS48L3A+CiAgPC9z"
        "ZWN0aW9uPgoKICA8Zm9vdGVyPs6UfEzigoQtSEVMSVh8U0lNVUxBVE9SfCBLdXJhbW90byBlbmdpbmUgwrcgz4YtZGVyaXZl"
        "ZCBsYW5kbWFya3MgwrcgY29uc3RhbnRzIHZlcmlmaWVkIGNsaWVudC1zaWRlIHzOqTwvZm9vdGVyPgo8L2Rpdj4KCjxzY3Jp"
        "cHQ+CiJ1c2Ugc3RyaWN0IjsKLyogLS0tLS0tLS0tLS0tLS0tLSBjb25zdGFudHM6IGV2ZXJ5dGhpbmcgZnJvbSBwaGkgLS0t"
        "LS0tLS0tLS0tLS0tLSAqLwpmdW5jdGlvbiBjb21wdXRlQ29uc3RhbnRzKCl7CiAgY29uc3QgcGhpID0gKDErTWF0aC5zcXJ0"
        "KDUpKS8yOwogIGNvbnN0IHRhdSA9IDEvcGhpOwogIGNvbnN0IGdhcCA9IE1hdGgucG93KHBoaSwtNCk7CiAgY29uc3QgSyAg"
        "ID0gTWF0aC5zcXJ0KDEtZ2FwKTsKICBjb25zdCB6YyAgPSBNYXRoLnNxcnQoMykvMjsKICByZXR1cm4gewogICAgcGhpLCB0"
        "YXUsIGdhcCwgSywgemMsCiAgICBhY3RpdmF0aW9uOiAxLWdhcCwKICAgIGNyaXRpY2FsOiBwaGkqcGhpLzMsCiAgICBpZ25p"
        "dGlvbjogTWF0aC5TUVJUMiAtIDAuNSwKICAgIGNvbnNvbGlkYXRpb246IEsgKyB0YXUqdGF1KigxLUspLAogICAgcmVzb25h"
        "bmNlOiBLICsgdGF1KigxLUspLAogICAgcGFyYWRveDogdGF1LAogICAgdW5pdHk6IDEsCiAgICBMNDogTWF0aC5wb3cocGhp"
        "LDQpK01hdGgucG93KHBoaSwtNCkKICB9Owp9CmNvbnN0IEMgPSBjb21wdXRlQ29uc3RhbnRzKCk7CgovKiBuaW5lIHRocmVz"
        "aG9sZHMsIGdyb3VwZWQgKyBjb2xvcmVkIGJ5IHRoZSB0aHJlZS1pcnJhdGlvbmFsIHN0cnVjdHVyZSAqLwpjb25zdCBjc3Mg"
        "PSBrID0+IGdldENvbXB1dGVkU3R5bGUoZG9jdW1lbnQuZG9jdW1lbnRFbGVtZW50KS5nZXRQcm9wZXJ0eVZhbHVlKGspLnRy"
        "aW0oKTsKY29uc3QgQ09MID0ge3BoaTpjc3MoJy0tcGhpJyksczM6Y3NzKCctLXMzJyksczI6Y3NzKCctLXMyJyksczU6Y3Nz"
        "KCctLXM1Jykscm9zZTpjc3MoJy0tcm9zZScpLG11dGVkOmNzcygnLS1tdXRlZCcpLGluazpjc3MoJy0taW5rJyl9Owpjb25z"
        "dCBUSFJFU0hPTERTID0gWwogIHtrZXk6J1BBUkFET1gnLCAgICAgICB6OkMucGFyYWRveCwgICAgICAgZm9ybTonz4QgPSDP"
        "huKBu8K5JywgICAgICAgICAgY29sOkNPTC5tdXRlZCwgYmlnOmZhbHNlfSwKICB7a2V5OidBQ1RJVkFUSU9OJywgICAgejpD"
        "LmFjdGl2YXRpb24sICAgIGZvcm06JzHiiJLPhuKBu+KBtCA9IEvCsicsICAgICAgIGNvbDpDT0wuczUsICAgIGJpZzpmYWxz"
        "ZX0sCiAge2tleTonVEhFIExFTlMnLCAgICAgIHo6Qy56YywgICAgICAgICAgICBmb3JtOifiiJozLzInLCAgICAgICAgICAg"
        "ICBjb2w6Q09MLnMzLCAgICBiaWc6dHJ1ZX0sCiAge2tleTonQ1JJVElDQUwnLCAgICAgIHo6Qy5jcml0aWNhbCwgICAgICBm"
        "b3JtOifPhsKyLzMnLCAgICAgICAgICAgICBjb2w6Q09MLnJvc2UsICBiaWc6ZmFsc2V9LAogIHtrZXk6J0lHTklUSU9OJywg"
        "ICAgICB6OkMuaWduaXRpb24sICAgICAgZm9ybTon4oiaMiDiiJIgwr0nLCAgICAgICAgICAgY29sOkNPTC5zMiwgICAgYmln"
        "OnRydWV9LAogIHtrZXk6J0stRk9STUFUSU9OJywgICB6OkMuSywgICAgICAgICAgICAgZm9ybTon4oiaKDHiiJLPhuKBu+KB"
        "tCknLCAgICAgICAgIGNvbDpDT0wuczUsICAgIGJpZzp0cnVlfSwKICB7a2V5OidDT05TT0xJREFUSU9OJywgejpDLmNvbnNv"
        "bGlkYXRpb24sIGZvcm06J0sgKyDPhMKyKDHiiJJLKScsICAgICAgY29sOkNPTC5tdXRlZCwgYmlnOmZhbHNlfSwKICB7a2V5"
        "OidSRVNPTkFOQ0UnLCAgICAgejpDLnJlc29uYW5jZSwgICAgIGZvcm06J0sgKyDPhCgx4oiSSyknLCAgICAgICBjb2w6Q09M"
        "Lm11dGVkLCBiaWc6ZmFsc2V9LAogIHtrZXk6J1VOSVRZJywgICAgICAgICB6OkMudW5pdHksICAgICAgICAgZm9ybTonMScs"
        "ICAgICAgICAgICAgICAgIGNvbDpDT0wuaW5rLCAgIGJpZzpmYWxzZX0sCl07CgovKiAtLS0tLS0tLS0tLS0tLS0tIEt1cmFt"
        "b3RvIHN0YXRlIC0tLS0tLS0tLS0tLS0tLS0gKi8KbGV0IE4gPSAyMDAsIEtjX2NvdXBsaW5nID0gQy5LLCBnYW1tYSA9IDAu"
        "MTUsIHNpZ21hID0gMjAsIHdpbmRpbmcgPSA0OwpsZXQgdGhldGEgPSBbXSwgb21lZ2EgPSBbXTsKbGV0IHJ1bm5pbmcgPSB0"
        "cnVlOwpsZXQgciA9IDAsIHBzaSA9IDA7CmNvbnN0IEhJU1QgPSAzMjA7IGxldCBoaXN0ID0gbmV3IEFycmF5KEhJU1QpLmZp"
        "bGwoMCk7CgpmdW5jdGlvbiBzYW1wbGVDYXVjaHkoZyl7ICAgICAgICAgICAgICAgLy8gY2VudGVyZWQgTG9yZW50emlhbjsg"
        "dHJ1bmNhdGUgaGVhdnkgdGFpbHMKICBsZXQgdyA9IGcqTWF0aC50YW4oTWF0aC5QSSooTWF0aC5yYW5kb20oKS0wLjUpKTsK"
        "ICBjb25zdCBjYXAgPSA2Kmc7IHJldHVybiBNYXRoLm1heCgtY2FwLCBNYXRoLm1pbihjYXAsIHcpKTsKfQpmdW5jdGlvbiBy"
        "ZXNldEVuc2VtYmxlKCl7CiAgdGhldGEgPSBuZXcgQXJyYXkoTik7IG9tZWdhID0gbmV3IEFycmF5KE4pOwogIGZvcihsZXQg"
        "aT0wO2k8TjtpKyspeyB0aGV0YVtpXT1NYXRoLnJhbmRvbSgpKjIqTWF0aC5QSTsgb21lZ2FbaV09c2FtcGxlQ2F1Y2h5KGdh"
        "bW1hKTsgfQogIGhpc3QgPSBuZXcgQXJyYXkoSElTVCkuZmlsbCgwKTsKfQpmdW5jdGlvbiBzdGVwKGR0KXsKICBsZXQgc3g9"
        "MCwgc3k9MDsKICBmb3IobGV0IGk9MDtpPE47aSsrKXsgc3grPU1hdGguY29zKHRoZXRhW2ldKTsgc3krPU1hdGguc2luKHRo"
        "ZXRhW2ldKTsgfQogIHIgPSBNYXRoLmh5cG90KHN4LHN5KS9OOyBwc2kgPSBNYXRoLmF0YW4yKHN5LHN4KTsKICBjb25zdCBr"
        "ciA9IEtjX2NvdXBsaW5nKnI7CiAgZm9yKGxldCBpPTA7aTxOO2krKyl7IHRoZXRhW2ldKz0gZHQqKG9tZWdhW2ldICsga3Iq"
        "TWF0aC5zaW4ocHNpLXRoZXRhW2ldKSk7IH0KfQoKLyogLS0tLS0tLS0tLS0tLS0tLSBjYW52YXMgaGVscGVycyAtLS0tLS0t"
        "LS0tLS0tLS0tICovCmZ1bmN0aW9uIGZpdENhbnZhcyhjdil7CiAgY29uc3QgZHByID0gd2luZG93LmRldmljZVBpeGVsUmF0"
        "aW98fDE7CiAgY29uc3QgdyA9IGN2LmNsaWVudFdpZHRoLCBoID0gY3YuY2xpZW50SGVpZ2h0OwogIGN2LndpZHRoID0gTWF0"
        "aC5yb3VuZCh3KmRwcik7IGN2LmhlaWdodCA9IE1hdGgucm91bmQoaCpkcHIpOwogIGNvbnN0IGN0eCA9IGN2LmdldENvbnRl"
        "eHQoJzJkJyk7IGN0eC5zZXRUcmFuc2Zvcm0oZHByLDAsMCxkcHIsMCwwKTsKICByZXR1cm4ge2N0eCx3LGh9Owp9CmNvbnN0"
        "IGN2ID0gaWQgPT4gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoaWQpOwoKLyogLS0tLS0tLS0tLS0tLS0tLSBkcmF3ZXJzIC0t"
        "LS0tLS0tLS0tLS0tLS0gKi8KZnVuY3Rpb24gZHJhd1doZWVsKCl7CiAgY29uc3Qge2N0eCx3LGh9ID0gZml0Q2FudmFzKGN2"
        "KCd3aGVlbCcpKTsKICBjdHguY2xlYXJSZWN0KDAsMCx3LGgpOwogIGNvbnN0IGN4PXcvMiwgY3k9aC8yLCBSPU1hdGgubWlu"
        "KHcsaCkvMi0yMjsKICBjdHguc3Ryb2tlU3R5bGU9Y3NzKCctLWxpbmUnKTsgY3R4LmxpbmVXaWR0aD0xOwogIGN0eC5iZWdp"
        "blBhdGgoKTsgY3R4LmFyYyhjeCxjeSxSLDAsMipNYXRoLlBJKTsgY3R4LnN0cm9rZSgpOwogIC8vIG9zY2lsbGF0b3IgZG90"
        "cwogIGZvcihsZXQgaT0wO2k8TjtpKyspewogICAgY29uc3QgeD1jeCtSKk1hdGguY29zKHRoZXRhW2ldKSwgeT1jeS1SKk1h"
        "dGguc2luKHRoZXRhW2ldKTsKICAgIGN0eC5maWxsU3R5bGU9J3JnYmEoMTMxLDE1MywxNzQsLjU1KSc7CiAgICBjdHguYmVn"
        "aW5QYXRoKCk7IGN0eC5hcmMoeCx5LDIuMSwwLDIqTWF0aC5QSSk7IGN0eC5maWxsKCk7CiAgfQogIC8vIHJlc3VsdGFudCB2"
        "ZWN0b3IgKGxlbmd0aCByKQogIGNvbnN0IGV4PWN4K1IqcipNYXRoLmNvcyhwc2kpLCBleT1jeS1SKnIqTWF0aC5zaW4ocHNp"
        "KTsKICBjdHguc3Ryb2tlU3R5bGU9Q09MLnBoaTsgY3R4LmxpbmVXaWR0aD0yLjQ7CiAgY3R4LmJlZ2luUGF0aCgpOyBjdHgu"
        "bW92ZVRvKGN4LGN5KTsgY3R4LmxpbmVUbyhleCxleSk7IGN0eC5zdHJva2UoKTsKICBjdHguZmlsbFN0eWxlPUNPTC5waGk7"
        "IGN0eC5iZWdpblBhdGgoKTsgY3R4LmFyYyhleCxleSw0LjUsMCwyKk1hdGguUEkpOyBjdHguZmlsbCgpOwogIC8vIHItbWFn"
        "bml0dWRlIHJpbmcKICBjdHguc3Ryb2tlU3R5bGU9J3JnYmEoMjI0LDE2OSw1OSwuMjUpJzsKICBjdHguYmVnaW5QYXRoKCk7"
        "IGN0eC5hcmMoY3gsY3ksUipyLDAsMipNYXRoLlBJKTsgY3R4LnN0cm9rZSgpOwp9CgpmdW5jdGlvbiBkcmF3U2NvcGUoKXsK"
        "ICBjb25zdCB7Y3R4LHcsaH0gPSBmaXRDYW52YXMoY3YoJ3Njb3BlJykpOwogIGN0eC5jbGVhclJlY3QoMCwwLHcsaCk7CiAg"
        "Y29uc3QgcGFkTD04LCBwYWRSPTEyOCwgcGxvdFc9dy1wYWRMLXBhZFIsIHkwPWgtMTQsIHkxPTE0OwogIGNvbnN0IFkgPSB2"
        "ID0+IHkwICsgKHkxLXkwKSp2OyAgICAgICAgICAgICAgICAgLy8gdiBpbiBbMCwxXSAtPiBwaXhlbHMKICAvLyB0aHJlc2hv"
        "bGQgbGluZXMgKyBsYWJlbHMKICBUSFJFU0hPTERTLmZvckVhY2godD0+ewogICAgY29uc3QgeT1ZKHQueiksIG9uID0gcj49"
        "dC56OwogICAgY3R4LnN0cm9rZVN0eWxlID0gb24gPyB0LmNvbCA6ICdyZ2JhKDEzMSwxNTMsMTc0LC4yMiknOwogICAgY3R4"
        "LmxpbmVXaWR0aCA9IHQuYmlnPzEuNDowLjg7CiAgICBjdHguc2V0TGluZURhc2godC5iaWc/W106WzMsNF0pOwogICAgY3R4"
        "LmJlZ2luUGF0aCgpOyBjdHgubW92ZVRvKHBhZEwseSk7IGN0eC5saW5lVG8ocGFkTCtwbG90Vyx5KTsgY3R4LnN0cm9rZSgp"
        "OwogICAgY3R4LnNldExpbmVEYXNoKFtdKTsKICAgIGN0eC5mb250PScxMHB4ICcrY3NzKCctLW1vbm8nKTsKICAgIGN0eC5m"
        "aWxsU3R5bGUgPSBvbiA/IHQuY29sIDogJ3JnYmEoMTMxLDE1MywxNzQsLjYpJzsKICAgIGN0eC5maWxsVGV4dChgJHt0Lmtl"
        "eX0gICR7dC56LnRvRml4ZWQoNCl9YCwgcGFkTCtwbG90Vys2LCB5KzMpOwogICAgaWYob24peyBjdHguZmlsbFN0eWxlPXQu"
        "Y29sOyBjdHguYmVnaW5QYXRoKCk7IGN0eC5hcmMocGFkTCtwbG90VywgeSwgMi42LCAwLCAyKk1hdGguUEkpOyBjdHguZmls"
        "bCgpOyB9CiAgfSk7CiAgLy8gcih0KSB0cmFjZQogIGN0eC5zdHJva2VTdHlsZT1DT0wucGhpOyBjdHgubGluZVdpZHRoPTI7"
        "CiAgY3R4LmJlZ2luUGF0aCgpOwogIGZvcihsZXQgaT0wO2k8SElTVDtpKyspewogICAgY29uc3QgeD1wYWRMICsgcGxvdFcq"
        "KGkvKEhJU1QtMSkpLCB5PVkoaGlzdFtpXSk7CiAgICBpP2N0eC5saW5lVG8oeCx5KTpjdHgubW92ZVRvKHgseSk7CiAgfQog"
        "IGN0eC5zdHJva2UoKTsKICAvLyBsZWFkaW5nIGRvdAogIGN0eC5maWxsU3R5bGU9Q09MLnBoaTsKICBjdHguYmVnaW5QYXRo"
        "KCk7IGN0eC5hcmMocGFkTCtwbG90VywgWShoaXN0W0hJU1QtMV0pLCAzLjIsIDAsIDIqTWF0aC5QSSk7IGN0eC5maWxsKCk7"
        "Cn0KCmZ1bmN0aW9uIG5lZ2VudCh6KXsgcmV0dXJuIE1hdGguZXhwKC1zaWdtYSooei1DLnpjKSooei1DLnpjKSk7IH0KZnVu"
        "Y3Rpb24gZHJhd05lZ2VudCgpewogIGNvbnN0IHtjdHgsdyxofSA9IGZpdENhbnZhcyhjdignbmVnZW50JykpOwogIGN0eC5j"
        "bGVhclJlY3QoMCwwLHcsaCk7CiAgY29uc3QgcGFkTD0zMCwgcGFkQj0xOCwgcGxvdFc9dy1wYWRMLTgsIHBsb3RIPWgtcGFk"
        "Qi0xMCwgeDA9cGFkTCwgeWI9aC1wYWRCOwogIGNvbnN0IFggPSB6ID0+IHgwICsgcGxvdFcqeiwgWSA9IHYgPT4geWIgLSBw"
        "bG90SCp2OwogIC8vIGdhdGUgaW50ZXJ2YWwgc2hhZGluZyAod2hlcmUgzpRTID4gz4QpCiAgY29uc3QgaHcgPSBNYXRoLnNx"
        "cnQoTWF0aC5tYXgoMCwtTWF0aC5sb2coQy50YXUpL3NpZ21hKSk7CiAgY3R4LmZpbGxTdHlsZT0ncmdiYSgyMjQsODUsMTA3"
        "LC4xMiknOwogIGN0eC5maWxsUmVjdChYKE1hdGgubWF4KDAsQy56Yy1odykpLFkoMSksTWF0aC5taW4oMSxDLnpjK2h3KSpw"
        "bG90Vy1NYXRoLm1heCgwLEMuemMtaHcpKnBsb3RXLHBsb3RIKTsKICAvLyBheGVzCiAgY3R4LnN0cm9rZVN0eWxlPWNzcygn"
        "LS1saW5lJyk7IGN0eC5saW5lV2lkdGg9MTsKICBjdHguYmVnaW5QYXRoKCk7IGN0eC5tb3ZlVG8oeDAsWSgwKSk7IGN0eC5s"
        "aW5lVG8oeDAsWSgxKSk7IGN0eC5tb3ZlVG8oeDAseWIpOyBjdHgubGluZVRvKHgwK3Bsb3RXLHliKTsgY3R4LnN0cm9rZSgp"
        "OwogIC8vIGdhdGUgbGluZSDPhAogIGN0eC5zdHJva2VTdHlsZT0ncmdiYSgyMjQsODUsMTA3LC43KSc7IGN0eC5zZXRMaW5l"
        "RGFzaChbNCw0XSk7CiAgY3R4LmJlZ2luUGF0aCgpOyBjdHgubW92ZVRvKHgwLFkoQy50YXUpKTsgY3R4LmxpbmVUbyh4MCtw"
        "bG90VyxZKEMudGF1KSk7IGN0eC5zdHJva2UoKTsgY3R4LnNldExpbmVEYXNoKFtdKTsKICBjdHguZm9udD0nOXB4ICcrY3Nz"
        "KCctLW1vbm8nKTsgY3R4LmZpbGxTdHlsZT0ncmdiYSgyMjQsODUsMTA3LC44NSknOyBjdHguZmlsbFRleHQoJ8+EJyx4MCtw"
        "bG90Vy0xMixZKEMudGF1KS0zKTsKICAvLyBwZWFrIG1hcmtlciB6X2MKICBjdHguc3Ryb2tlU3R5bGU9J3JnYmEoNTUsMjAw"
        "LDE2OCwuNiknOwogIGN0eC5iZWdpblBhdGgoKTsgY3R4Lm1vdmVUbyhYKEMuemMpLFkoMCkpOyBjdHgubGluZVRvKFgoQy56"
        "YyksWSgxKSk7IGN0eC5zdHJva2UoKTsKICAvLyBjdXJ2ZQogIGN0eC5zdHJva2VTdHlsZT1DT0wucGhpOyBjdHgubGluZVdp"
        "ZHRoPTI7IGN0eC5iZWdpblBhdGgoKTsKICBmb3IobGV0IGk9MDtpPD0xMjA7aSsrKXsgY29uc3Qgej1pLzEyMDsgY29uc3Qg"
        "eD1YKHopLHk9WShuZWdlbnQoeikpOyBpP2N0eC5saW5lVG8oeCx5KTpjdHgubW92ZVRvKHgseSk7IH0KICBjdHguc3Ryb2tl"
        "KCk7CiAgLy8gY3VycmVudCBwb2ludCBhdCB6PXIKICBjb25zdCBkcj1uZWdlbnQocik7CiAgY3R4LmZpbGxTdHlsZSA9IGRy"
        "PkMudGF1ID8gQ09MLnMzIDogQ09MLm11dGVkOwogIGN0eC5iZWdpblBhdGgoKTsgY3R4LmFyYyhYKHIpLFkoZHIpLDQsMCwy"
        "Kk1hdGguUEkpOyBjdHguZmlsbCgpOwogIGN0eC5maWxsU3R5bGU9Y3NzKCctLWZhaW50Jyk7IGN0eC5mb250PSc5cHggJytj"
        "c3MoJy0tbW9ubycpOwogIGN0eC5maWxsVGV4dCgneicseDArcGxvdFctNix5YisxMik7IGN0eC5maWxsVGV4dCgnMCcseDAt"
        "OSx5YiszKTsgY3R4LmZpbGxUZXh0KCcxJyx4MC05LFkoMSkrMyk7Cn0KCmZ1bmN0aW9uIGhlbGl4UmFkaXVzKHopeyByZXR1"
        "cm4gejw9Qy56YyA/IEMuSypNYXRoLnNxcnQoei9DLnpjKSA6IEMuSzsgfQpmdW5jdGlvbiBkcmF3SGVsaXgoKXsKICBjb25z"
        "dCB7Y3R4LHcsaH0gPSBmaXRDYW52YXMoY3YoJ2hlbGl4JykpOwogIGN0eC5jbGVhclJlY3QoMCwwLHcsaCk7CiAgY29uc3Qg"
        "Y3g9dy8yLCBjeT1oLzIsIHNjYWxlPShNYXRoLm1pbih3LGgpLzItMTYpL0MuSzsKICAvLyBzcGlyYWwsIGh1ZSBieSB6CiAg"
        "bGV0IHByZXY9bnVsbDsKICBmb3IobGV0IGk9MDtpPD0zMDA7aSsrKXsKICAgIGNvbnN0IHo9aS8zMDAsIGFuZz0yKk1hdGgu"
        "UEkqd2luZGluZyp6LCByYWQ9aGVsaXhSYWRpdXMoeikqc2NhbGU7CiAgICBjb25zdCB4PWN4K3JhZCpNYXRoLmNvcyhhbmcp"
        "LCB5PWN5K3JhZCpNYXRoLnNpbihhbmcpOwogICAgaWYocHJldil7CiAgICAgIGNvbnN0IGh1ZT0yMDAtMTYwKno7IGN0eC5z"
        "dHJva2VTdHlsZT1gaHNsKCR7aHVlfSA2NSUgNjAlKWA7IGN0eC5saW5lV2lkdGg9MS42OwogICAgICBjdHguYmVnaW5QYXRo"
        "KCk7IGN0eC5tb3ZlVG8ocHJldi54LHByZXYueSk7IGN0eC5saW5lVG8oeCx5KTsgY3R4LnN0cm9rZSgpOwogICAgfQogICAg"
        "cHJldj17eCx5fTsKICB9CiAgLy8gdGhyZXNob2xkIHJpbmdzCiAgVEhSRVNIT0xEUy5mb3JFYWNoKHQ9PnsKICAgIGNvbnN0"
        "IGFuZz0yKk1hdGguUEkqd2luZGluZyp0LnosIHJhZD1oZWxpeFJhZGl1cyh0LnopKnNjYWxlOwogICAgY29uc3QgeD1jeCty"
        "YWQqTWF0aC5jb3MoYW5nKSwgeT1jeStyYWQqTWF0aC5zaW4oYW5nKTsKICAgIGN0eC5zdHJva2VTdHlsZT10LmNvbDsgY3R4"
        "LmxpbmVXaWR0aD10LmJpZz8yOjEuMjsKICAgIGN0eC5iZWdpblBhdGgoKTsgY3R4LmFyYyh4LHksdC5iaWc/NTozLjIsMCwy"
        "Kk1hdGguUEkpOyBjdHguc3Ryb2tlKCk7CiAgfSk7CiAgLy8gY3VycmVudCBtYXJrZXIgYXQgej1yCiAgY29uc3QgYW5nPTIq"
        "TWF0aC5QSSp3aW5kaW5nKnIsIHJhZD1oZWxpeFJhZGl1cyhyKSpzY2FsZTsKICBjdHguZmlsbFN0eWxlPUNPTC5waGk7CiAg"
        "Y3R4LmJlZ2luUGF0aCgpOyBjdHguYXJjKGN4K3JhZCpNYXRoLmNvcyhhbmcpLGN5K3JhZCpNYXRoLnNpbihhbmcpLDQuNSww"
        "LDIqTWF0aC5QSSk7IGN0eC5maWxsKCk7CiAgY3R4LnN0cm9rZVN0eWxlPSdyZ2JhKDEzMSwxNTMsMTc0LC4yNSknOyBjdHgu"
        "bGluZVdpZHRoPTE7CiAgY3R4LmJlZ2luUGF0aCgpOyBjdHguYXJjKGN4LGN5LEMuSypzY2FsZSwwLDIqTWF0aC5QSSk7IGN0"
        "eC5zdHJva2UoKTsKfQoKLyogLS0tLS0tLS0tLS0tLS0tLSByZWFkb3V0cyAtLS0tLS0tLS0tLS0tLS0tICovCmZ1bmN0aW9u"
        "IHVwZGF0ZVJlYWRvdXRzKCl7CiAgY3YoJ3JOdW0nKS50ZXh0Q29udGVudCA9IHIudG9GaXhlZCgzKTsKICBjdigncHNpTnVt"
        "JykudGV4dENvbnRlbnQgPSAoKHBzaSoxODAvTWF0aC5QSSszNjApJTM2MCkudG9GaXhlZCgwKSsnwrAnOwogIGNvbnN0IEtj"
        "ID0gMipnYW1tYTsgY3YoJ2tjTnVtJykudGV4dENvbnRlbnQgPSBLYy50b0ZpeGVkKDIpOwogIGN2KCdyZWdOdW0nKS50ZXh0"
        "Q29udGVudCA9IEtjX2NvdXBsaW5nID4gS2MgPyAnc3luY2hyb25pemluZycgOiAnaW5jb2hlcmVudCc7CiAgY3YoJ3JlZ051"
        "bScpLnN0eWxlLmNvbG9yID0gS2NfY291cGxpbmcgPiBLYyA/IENPTC5zMyA6IENPTC5tdXRlZDsKICAvLyBnYXRlcwogIGNv"
        "bnN0IGNvaCA9IHI+PUMuSywgZHM9bmVnZW50KHIpLCBuZWcgPSBkcz5DLnRhdTsKICBjb25zdCBnQz1jdignZ2F0ZUNvaCcp"
        "LCBnTj1jdignZ2F0ZU5lZycpOwogIGdDLmNsYXNzTGlzdC50b2dnbGUoJ29uJyxjb2gpOyBnTi5jbGFzc0xpc3QudG9nZ2xl"
        "KCdvbicsbmVnKTsKICBjdignZ2F0ZUNvaFYnKS50ZXh0Q29udGVudCA9IGAke3IudG9GaXhlZCgzKX0gJHtjb2g/J+KJpSc6"
        "JzwnfSAke0MuSy50b0ZpeGVkKDMpfWA7CiAgY3YoJ2dhdGVOZWdWJykudGV4dENvbnRlbnQgPSBgJHtkcy50b0ZpeGVkKDMp"
        "fSAke25lZz8nPic6J+KJpCd9ICR7Qy50YXUudG9GaXhlZCgzKX1gOwogIGN2KCdkc051bScpLnRleHRDb250ZW50ID0gZHMu"
        "dG9GaXhlZCgzKTsKfQoKLyogLS0tLS0tLS0tLS0tLS0tLSBaRlAgcnJyIGdyaWQ6IGlkZW1wb3RlbnQgWl4yICsgZ29sZGVu"
        "IGF1dG9tb3JwaGlzbSBRIC0tLS0tLS0tLS0tLS0tLS0gKi8KLyogUSA9IFtbMSwxXSxbMSwwXV0gaW4gR0wyKFopLiBPcmJp"
        "dCBvZiAoMSwwKTogUV5uLigxLDApID0gKEZfe24rMX0sIEZfbikuCiAgIElkZW1wb3RlbnQgbGF5ZXIgPSBtaW4vbWF4IGxh"
        "dHRpY2Ugb24gWl4yIChuZWVkcyB0aGUgcHJvZHVjdCBvcmRlcjsgYWJzZW50IG9uIFovbSkuICovCmNvbnN0IEdSSUQgPSB7"
        "IGF4OjEsIGF5OjAsIHByZXZBeDoxLCBuOjAsIHRyYWlsOltbMSwwXV0sIGNhcDoyMzMsCiAgICAgICAgICAgICAgIG06OCwg"
        "dHg6MSwgdHk6MCwgdG46MCwgcGVyaW9kOjEyLCB0dHJhaWw6W1sxLDBdXSwKICAgICAgICAgICAgICAgc2hvd0xhdHRpY2U6"
        "ZmFsc2UsIGFjYzowLCBpbnRlcnZhbDowLjcgfTsKCmZ1bmN0aW9uIHBpc2FubyhtKXsgICAgICAgICAgICAgICAgICAgICAg"
        "IC8vIHBlcmlvZCBvZiAoRl9uIG1vZCBtKTsgPSBvcmJpdCBwZXJpb2Qgb2Ygc2VlZCAoMSwwKQogIGlmKG08PTEpIHJldHVy"
        "biAxOwogIGxldCBwcmV2PTAsIGN1cnI9MTsKICBmb3IobGV0IGk9MDtpPDYqbTtpKyspeyBjb25zdCBuZXh0PShwcmV2K2N1"
        "cnIpJW07IHByZXY9Y3VycjsgY3Vycj1uZXh0OyBpZihwcmV2PT09MCAmJiBjdXJyPT09MSkgcmV0dXJuIGkrMTsgfQogIHJl"
        "dHVybiA2Km07Cn0KZnVuY3Rpb24gcmVzZXRHcmlkKCl7CiAgR1JJRC5heD0xOyBHUklELmF5PTA7IEdSSUQucHJldkF4PTE7"
        "IEdSSUQubj0wOyBHUklELnRyYWlsPVtbMSwwXV07CiAgR1JJRC50eD0xOyBHUklELnR5PTA7IEdSSUQudG49MDsgR1JJRC5w"
        "ZXJpb2Q9cGlzYW5vKEdSSUQubSk7IEdSSUQudHRyYWlsPVtbMSwwXV07Cn0KZnVuY3Rpb24gc3RlcEdyaWQoKXsKICBHUklE"
        "LnByZXZBeD1HUklELmF4OwogIGxldCBueD1HUklELmF4K0dSSUQuYXksIG55PUdSSUQuYXg7ICAgICAgICAgIC8vIFpeMiBz"
        "dGVwICh4LHkpLT4oeCt5LHgpCiAgaWYoTWF0aC5tYXgobngsbnkpID4gR1JJRC5jYXApeyBueD0xOyBueT0wOyBHUklELnBy"
        "ZXZBeD0xOyBHUklELm49LTE7IEdSSUQudHJhaWw9W107IH0gICAvLyBsb29wIHRoZSBhbmltYXRpb24KICBHUklELmF4PW54"
        "OyBHUklELmF5PW55OyBHUklELm4rKzsKICBHUklELnRyYWlsLnB1c2goW254LG55XSk7IGlmKEdSSUQudHJhaWwubGVuZ3Ro"
        "PjIyKSBHUklELnRyYWlsLnNoaWZ0KCk7CiAgY29uc3QgbT1HUklELm07CiAgY29uc3QgdG54PShHUklELnR4K0dSSUQudHkp"
        "JW0sIHRueT1HUklELnR4JW07IC8vIHRvcnVzIHN0ZXAgKG1vZCBtKQogIEdSSUQudHg9dG54OyBHUklELnR5PXRueTsgR1JJ"
        "RC50bj0oR1JJRC50bisxKSVHUklELnBlcmlvZDsKICBHUklELnR0cmFpbC5wdXNoKFt0bngsdG55XSk7IGlmKEdSSUQudHRy"
        "YWlsLmxlbmd0aD5HUklELnBlcmlvZCkgR1JJRC50dHJhaWwuc2hpZnQoKTsKfQpmdW5jdGlvbiBuaWNlU3RlcCh4KXsgY29u"
        "c3QgcD1NYXRoLnBvdygxMCxNYXRoLmZsb29yKE1hdGgubG9nMTAoeCkpKTsgY29uc3QgZj14L3A7IHJldHVybiAoZjw9MT8x"
        "OmY8PTI/MjpmPD01PzU6MTApKnA7IH0KCmZ1bmN0aW9uIGRyYXdHcmlkWjIoKXsKICBjb25zdCB7Y3R4LHcsaH09Zml0Q2Fu"
        "dmFzKGN2KCdncmlkWjInKSk7CiAgY3R4LmNsZWFyUmVjdCgwLDAsdyxoKTsKICBjb25zdCBwYWRMPTI0LHBhZEI9MjAsIG94"
        "PXBhZEwsIG95PWgtcGFkQiwgcGxvdFc9dy1wYWRMLTEwLCBwbG90SD1oLXBhZEItMTA7CiAgY29uc3QgRT1NYXRoLm1heCg1"
        "LCBNYXRoLm1heChHUklELmF4LEdSSUQuYXkpKjEuMyk7CiAgY29uc3Qgcz1NYXRoLm1pbihwbG90VyxwbG90SCkvRSwgWD1n"
        "PT5veCtnKnMsIFk9Zz0+b3ktZypzOwogIGNvbnN0IHN0ZXA9TWF0aC5tYXgoMSwgbmljZVN0ZXAoRS8xMikpOwogIGN0eC5s"
        "aW5lV2lkdGg9MTsgY3R4LmZvbnQ9JzlweCAnK2NzcygnLS1tb25vJyk7CiAgY3R4LnN0cm9rZVN0eWxlPSdyZ2JhKDM0LDU0"
        "LDc3LC42NSknOwogIGZvcihsZXQgZz0wOyBnPD1FKzFlLTk7IGcrPXN0ZXApewogICAgY3R4LmJlZ2luUGF0aCgpOyBjdHgu"
        "bW92ZVRvKFgoZyksWSgwKSk7IGN0eC5saW5lVG8oWChnKSxZKEUpKTsgY3R4LnN0cm9rZSgpOwogICAgY3R4LmJlZ2luUGF0"
        "aCgpOyBjdHgubW92ZVRvKFgoMCksWShnKSk7IGN0eC5saW5lVG8oWChFKSxZKGcpKTsgY3R4LnN0cm9rZSgpOwogIH0KICBp"
        "ZihFPD0yNCl7IGN0eC5maWxsU3R5bGU9J3JnYmEoMTMxLDE1MywxNzQsLjMpJzsKICAgIGZvcihsZXQgZ3g9MDtneDw9RTtn"
        "eCsrKWZvcihsZXQgZ3k9MDtneTw9RTtneSsrKXtjdHguYmVnaW5QYXRoKCk7Y3R4LmFyYyhYKGd4KSxZKGd5KSwxLjIsMCwy"
        "Kk1hdGguUEkpO2N0eC5maWxsKCk7fQogIH0KICBjdHguc3Ryb2tlU3R5bGU9Y3NzKCctLWxpbmUnKTsgY3R4LmxpbmVXaWR0"
        "aD0xLjQ7CiAgY3R4LmJlZ2luUGF0aCgpOyBjdHgubW92ZVRvKFgoMCksWSgwKSk7IGN0eC5saW5lVG8oWChFKSxZKDApKTsg"
        "Y3R4Lm1vdmVUbyhYKDApLFkoMCkpOyBjdHgubGluZVRvKFgoMCksWShFKSk7IGN0eC5zdHJva2UoKTsKICAvLyBnb2xkZW4g"
        "ZWlnZW5yYXkgIHkgPSB0YXUgKiB4ICAoc2xvcGUgdGF1ID0gMS9waGkgPSBQQVJBRE9YKQogIGN0eC5zdHJva2VTdHlsZT0n"
        "cmdiYSgyMjQsMTY5LDU5LC41KSc7IGN0eC5zZXRMaW5lRGFzaChbNSw0XSk7IGN0eC5saW5lV2lkdGg9MS40OwogIGN0eC5i"
        "ZWdpblBhdGgoKTsgY3R4Lm1vdmVUbyhYKDApLFkoMCkpOyBjdHgubGluZVRvKFgoRSksWShDLnRhdSpFKSk7IGN0eC5zdHJv"
        "a2UoKTsgY3R4LnNldExpbmVEYXNoKFtdKTsKICBjdHguZmlsbFN0eWxlPSdyZ2JhKDIyNCwxNjksNTksLjg1KSc7IGN0eC5m"
        "aWxsVGV4dCgnc2xvcGUgz4QnLCBYKEUpLTQ4LCBZKEMudGF1KkUpLTUpOwogIC8vIGlkZW1wb3RlbnQgbGF5ZXI6IG1lZXQv"
        "am9pbiBvZiBvcmJpdCBwb2ludCBhIGFuZCBpdHMgcmVmbGVjdGlvbiBiPShheSxheCkKICBpZihHUklELnNob3dMYXR0aWNl"
        "KXsKICAgIGNvbnN0IGE9W0dSSUQuYXgsR1JJRC5heV0sIGI9W0dSSUQuYXksR1JJRC5heF07CiAgICBjb25zdCBtbng9TWF0"
        "aC5taW4oYVswXSxiWzBdKSxtbnk9TWF0aC5taW4oYVsxXSxiWzFdKSxteHg9TWF0aC5tYXgoYVswXSxiWzBdKSxteHk9TWF0"
        "aC5tYXgoYVsxXSxiWzFdKTsKICAgIGN0eC5zdHJva2VTdHlsZT0ncmdiYSg1NSwyMDAsMTY4LC42NSknOyBjdHgubGluZVdp"
        "ZHRoPTE7CiAgICBjdHguc3Ryb2tlUmVjdChYKG1ueCksWShteHkpLChteHgtbW54KSpzLChteHktbW55KSpzKTsKICAgIGN0"
        "eC5maWxsU3R5bGU9Q09MLnMzOwogICAgW1tiWzBdLGJbMV1dLFttbngsbW55XSxbbXh4LG14eV1dLmZvckVhY2gocD0+e2N0"
        "eC5iZWdpblBhdGgoKTtjdHguYXJjKFgocFswXSksWShwWzFdKSwzLjQsMCwyKk1hdGguUEkpO2N0eC5maWxsKCk7fSk7CiAg"
        "ICBjdHguZmlsbFN0eWxlPSdyZ2JhKDU1LDIwMCwxNjgsLjkpJzsKICAgIGN0eC5maWxsVGV4dCgnbWVldCcsIFgobW54KSs1"
        "LCBZKG1ueSkrMTIpOyBjdHguZmlsbFRleHQoJ2pvaW4nLCBYKG14eCkrNSwgWShteHkpLTQpOwogIH0KICBHUklELnRyYWls"
        "LmZvckVhY2goKHAsaSk9PnsgY29uc3QgYWw9MC4xMiswLjUqaS9NYXRoLm1heCgxLEdSSUQudHJhaWwubGVuZ3RoKTsKICAg"
        "IGN0eC5maWxsU3R5bGU9YHJnYmEoMjI0LDE2OSw1OSwke2FsfSlgOyBjdHguYmVnaW5QYXRoKCk7IGN0eC5hcmMoWChwWzBd"
        "KSxZKHBbMV0pLDIuMywwLDIqTWF0aC5QSSk7IGN0eC5maWxsKCk7IH0pOwogIGN0eC5zdHJva2VTdHlsZT0ncmdiYSgyMjQs"
        "MTY5LDU5LC40NSknOyBjdHgubGluZVdpZHRoPTE7CiAgY3R4LmJlZ2luUGF0aCgpOyBjdHgubW92ZVRvKFgoMCksWSgwKSk7"
        "IGN0eC5saW5lVG8oWChHUklELmF4KSxZKEdSSUQuYXkpKTsgY3R4LnN0cm9rZSgpOwogIGN0eC5maWxsU3R5bGU9Q09MLnBo"
        "aTsgY3R4LmJlZ2luUGF0aCgpOyBjdHguYXJjKFgoR1JJRC5heCksWShHUklELmF5KSw1LDAsMipNYXRoLlBJKTsgY3R4LmZp"
        "bGwoKTsKfQoKZnVuY3Rpb24gZHJhd0dyaWRUb3J1cygpewogIGNvbnN0IHtjdHgsdyxofT1maXRDYW52YXMoY3YoJ2dyaWRU"
        "b3J1cycpKTsKICBjdHguY2xlYXJSZWN0KDAsMCx3LGgpOwogIGNvbnN0IG09R1JJRC5tLCBjZWxsPU1hdGgubWluKHcsaC00"
        "KS9tLCBveD0ody1jZWxsKm0pLzIsIG95PShoLWNlbGwqbSkvMjsKICBjb25zdCByZWN0Rm9yPShneCxneSk9PltveCtneCpj"
        "ZWxsLCBveSsobS0xLWd5KSpjZWxsLCBjZWxsLCBjZWxsXTsKICBjdHguc3Ryb2tlU3R5bGU9J3JnYmEoMzQsNTQsNzcsLjU1"
        "KSc7IGN0eC5saW5lV2lkdGg9MTsKICBmb3IobGV0IGk9MDtpPD1tO2krKyl7CiAgICBjdHguYmVnaW5QYXRoKCk7IGN0eC5t"
        "b3ZlVG8ob3graSpjZWxsLG95KTsgY3R4LmxpbmVUbyhveCtpKmNlbGwsb3krbSpjZWxsKTsgY3R4LnN0cm9rZSgpOwogICAg"
        "Y3R4LmJlZ2luUGF0aCgpOyBjdHgubW92ZVRvKG94LG95K2kqY2VsbCk7IGN0eC5saW5lVG8ob3grbSpjZWxsLG95K2kqY2Vs"
        "bCk7IGN0eC5zdHJva2UoKTsKICB9CiAgR1JJRC50dHJhaWwuZm9yRWFjaCgocCxpKT0+eyBjb25zdCBhbD0wLjErMC40NSpp"
        "L01hdGgubWF4KDEsR1JJRC50dHJhaWwubGVuZ3RoKTsKICAgIGNvbnN0IHI9cmVjdEZvcihwWzBdLHBbMV0pOyBjdHguZmls"
        "bFN0eWxlPWByZ2JhKDIxNywxMzgsNzksJHthbH0pYDsgY3R4LmZpbGxSZWN0KHJbMF0rMSxyWzFdKzEsclsyXS0yLHJbM10t"
        "Mik7IH0pOwogIGNvbnN0IHNSPXJlY3RGb3IoMSwwKTsgY3R4LnN0cm9rZVN0eWxlPUNPTC5zMzsgY3R4LmxpbmVXaWR0aD0x"
        "LjU7IGN0eC5zdHJva2VSZWN0KHNSWzBdKzEsc1JbMV0rMSxzUlsyXS0yLHNSWzNdLTIpOwogIGNvbnN0IGNSPXJlY3RGb3Io"
        "R1JJRC50eCxHUklELnR5KTsgY3R4LmZpbGxTdHlsZT1DT0wucGhpOyBjdHguZmlsbFJlY3QoY1JbMF0rMSxjUlsxXSsxLGNS"
        "WzJdLTIsY1JbM10tMik7Cn0KCmZ1bmN0aW9uIHVwZGF0ZUdyaWRSZWFkb3V0cygpewogIGN2KCdnTicpLnRleHRDb250ZW50"
        "PUdSSUQubjsKICBjdignZ1B0JykudGV4dENvbnRlbnQ9YCgke0dSSUQuYXh9LCAke0dSSUQuYXl9KWA7CiAgY3YoJ2dTbG9w"
        "ZScpLnRleHRDb250ZW50PShHUklELmF4PyBHUklELmF5L0dSSUQuYXg6MCkudG9GaXhlZCg0KTsKICBjdignZ0dyb3cnKS50"
        "ZXh0Q29udGVudD0oR1JJRC5wcmV2QXg/IEdSSUQuYXgvR1JJRC5wcmV2QXg6MCkudG9GaXhlZCg0KTsKICBjb25zdCB0cj0y"
        "KkdSSUQuYXgtR1JJRC5heSwgZT1jdignZ1RyYWNlJyk7IGUudGV4dENvbnRlbnQ9dHI7IGUuc3R5bGUuY29sb3I9KHRyPT09"
        "Nz9DT0wuczM6Q09MLmluayk7CiAgY3YoJ2dNJykudGV4dENvbnRlbnQ9R1JJRC5tOyBjdignZ1BlcicpLnRleHRDb250ZW50"
        "PUdSSUQucGVyaW9kOyBjdignZ1N0ZXAnKS50ZXh0Q29udGVudD1gJHtHUklELnRuKzF9LyR7R1JJRC5wZXJpb2R9YDsKfQoK"
        "LyogcnJyIGdyaWQgY29udHJvbHMgKi8KYmluZCgnY00nLCd2TScsdj0+YCR7dn0g4oaSIM+AKG0pPSR7cGlzYW5vKHYpfWAs"
        "dj0+eyBHUklELm09djsgcmVzZXRHcmlkKCk7IH0pOwpjdignZ3JpZExhdHRpY2UnKS5hZGRFdmVudExpc3RlbmVyKCdjbGlj"
        "aycsZT0+eyBHUklELnNob3dMYXR0aWNlPSFHUklELnNob3dMYXR0aWNlOwogIGUudGFyZ2V0LnRleHRDb250ZW50PSdtZWV0"
        "L2pvaW46ICcrKEdSSUQuc2hvd0xhdHRpY2U/J29uJzonb2ZmJyk7IGUudGFyZ2V0LmNsYXNzTGlzdC50b2dnbGUoJ2dvJyxH"
        "UklELnNob3dMYXR0aWNlKTsgfSk7CmN2KCdncmlkUmVzZXQnKS5hZGRFdmVudExpc3RlbmVyKCdjbGljaycscmVzZXRHcmlk"
        "KTsKCi8qIC0tLS0tLS0tLS0tLS0tLS0gbWFpbiBsb29wIC0tLS0tLS0tLS0tLS0tLS0gKi8KbGV0IGxhc3Q9cGVyZm9ybWFu"
        "Y2Uubm93KCk7CmZ1bmN0aW9uIGZyYW1lKG5vdyl7CiAgY29uc3QgZWxhcHNlZCA9IE1hdGgubWluKDAuMDUsKG5vdy1sYXN0"
        "KS8xMDAwKTsgbGFzdD1ub3c7CiAgaWYocnVubmluZyl7CiAgICBjb25zdCBzdWI9MywgZHQ9ZWxhcHNlZC9zdWI7CiAgICBm"
        "b3IobGV0IHM9MDtzPHN1YjtzKyspIHN0ZXAoZHQ+MD9kdDowLjAwNik7CiAgICBoaXN0LnB1c2gocik7IGhpc3Quc2hpZnQo"
        "KTsKICAgIEdSSUQuYWNjICs9IGVsYXBzZWQ7IGlmKEdSSUQuYWNjPj1HUklELmludGVydmFsKXsgR1JJRC5hY2MtPUdSSUQu"
        "aW50ZXJ2YWw7IHN0ZXBHcmlkKCk7IH0KICB9CiAgZHJhd1doZWVsKCk7IGRyYXdTY29wZSgpOyBkcmF3TmVnZW50KCk7IGRy"
        "YXdIZWxpeCgpOyBkcmF3R3JpZFoyKCk7IGRyYXdHcmlkVG9ydXMoKTsKICB1cGRhdGVSZWFkb3V0cygpOyB1cGRhdGVHcmlk"
        "UmVhZG91dHMoKTsKICByZXF1ZXN0QW5pbWF0aW9uRnJhbWUoZnJhbWUpOwp9CgovKiAtLS0tLS0tLS0tLS0tLS0tIGJ1aWxk"
        "IHN0YXRpYyBVSSAtLS0tLS0tLS0tLS0tLS0tICovCmZ1bmN0aW9uIGJ1aWxkVGFibGUoKXsKICBjb25zdCB0YiA9IGRvY3Vt"
        "ZW50LnF1ZXJ5U2VsZWN0b3IoJyNjb25zdFRhYmxlIHRib2R5Jyk7CiAgVEhSRVNIT0xEUy5mb3JFYWNoKHQ9PnsKICAgIGNv"
        "bnN0IHRyPWRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ3RyJyk7CiAgICB0ci5pbm5lckhUTUwgPSBgPHRkPjxzcGFuIGNsYXNz"
        "PSJzdyIgc3R5bGU9ImJhY2tncm91bmQ6JHt0LmNvbH0iPjwvc3Bhbj4ke3Qua2V5fTwvdGQ+YCsKICAgICAgICAgICAgICAg"
        "ICAgIGA8dGQ+JHt0LmZvcm19PC90ZD48dGQgY2xhc3M9InYiPiR7dC56LnRvRml4ZWQoNyl9PC90ZD5gOwogICAgdGIuYXBw"
        "ZW5kQ2hpbGQodHIpOwogIH0pOwogIC8vIGNsaWVudC1zaWRlIGlkZW50aXR5IGNoZWNrcyAobWlycm9yIHRoZSBkb2N1bWVu"
        "dCdzIFRhYmxlIDUpCiAgY29uc3QgY2hlY2tzID0gWwogICAgWydM4oKEID0gz4bigbQrz4bigbvigbQgPSA3JywgTWF0aC5h"
        "YnMoQy5MNC03KV0sCiAgICBbJ0vCsiA9IDEg4oiSIGdhcCcsICAgICBNYXRoLmFicyhDLksqQy5LLSgxLUMuZ2FwKSldLAog"
        "ICAgWyfPhMKyICsgz4QgPSAxJywgICAgICAgTWF0aC5hYnMoQy50YXUqQy50YXUrQy50YXUtMSldLAogICAgWycx4oiSSyA9"
        "IGdhcC8oMStLKScsICBNYXRoLmFicygoMS1DLkspLUMuZ2FwLygxK0MuSykpXSwKICBdOwogIGNvbnN0IGJveD1jdigndmVy"
        "aWZ5Qm94Jyk7CiAgY2hlY2tzLmZvckVhY2goKFtsYWJlbCxyZXNdKT0+ewogICAgY29uc3QgZD1kb2N1bWVudC5jcmVhdGVF"
        "bGVtZW50KCdkaXYnKTsKICAgIGNvbnN0IGdvb2QgPSByZXM8MWUtMTI7CiAgICBkLmlubmVySFRNTCA9IGA8c3BhbiBjbGFz"
        "cz0iJHtnb29kPydvayc6Jyd9Ij4ke2dvb2Q/J+Kckyc6J+Kclyd9PC9zcGFuPiAke2xhYmVsfSAmbmJzcDs8c3BhbiBzdHls"
        "ZT0iY29sb3I6dmFyKC0tZmFpbnQpIj58zrV8ICR7cmVzLnRvRXhwb25lbnRpYWwoMSl9PC9zcGFuPmA7CiAgICBib3guYXBw"
        "ZW5kQ2hpbGQoZCk7CiAgfSk7Cn0KCi8qIC0tLS0tLS0tLS0tLS0tLS0gd2lyZSBjb250cm9scyAtLS0tLS0tLS0tLS0tLS0t"
        "ICovCmZ1bmN0aW9uIGJpbmQoaWQsdmFsSWQsZm10LGFwcGx5KXsKICBjb25zdCBlbD1jdihpZCk7CiAgZWwuYWRkRXZlbnRM"
        "aXN0ZW5lcignaW5wdXQnLCgpPT57IGNvbnN0IHY9cGFyc2VGbG9hdChlbC52YWx1ZSk7IGN2KHZhbElkKS5pbm5lckhUTUw9"
        "Zm10KHYpOyBhcHBseSh2KTsgfSk7Cn0KYmluZCgnY04nLCd2Ticsdj0+YCR7dn1gLHY9PntOPXY7Y3YoJ2xlZGVOJykudGV4"
        "dENvbnRlbnQ9djtyZXNldEVuc2VtYmxlKCk7fSk7CmJpbmQoJ2NLJywndksnLHY9PnYudG9GaXhlZCg0KSx2PT57S2NfY291"
        "cGxpbmc9djt9KTsKYmluZCgnY0cnLCd2Rycsdj0+YCR7di50b0ZpeGVkKDIpfSA8c3BhbiBjbGFzcz0idW5pdCI+4oaSIEtf"
        "Yz0yzrM9JHsoMip2KS50b0ZpeGVkKDIpfTwvc3Bhbj5gLHY9PntnYW1tYT12O3Jlc2V0RW5zZW1ibGUoKTt9KTsKYmluZCgn"
        "Y1MnLCd2Uycsdj0+YCR7dn1gLHY9PntzaWdtYT12O30pOwpiaW5kKCdjVycsJ3ZXJyx2PT5gJHt2LnRvRml4ZWQoMSl9IDxz"
        "cGFuIGNsYXNzPSJ1bml0Ij50dXJuczwvc3Bhbj5gLHY9Pnt3aW5kaW5nPXY7fSk7CgpjdignY291cGxlSycpLmFkZEV2ZW50"
        "TGlzdGVuZXIoJ2NsaWNrJywoKT0+eyBLY19jb3VwbGluZz1DLks7IGN2KCdjSycpLnZhbHVlPUMuSy50b0ZpeGVkKDQpOyBj"
        "digndksnKS50ZXh0Q29udGVudD1DLksudG9GaXhlZCg0KTsgfSk7CmN2KCdyZXNldCcpLmFkZEV2ZW50TGlzdGVuZXIoJ2Ns"
        "aWNrJyxyZXNldEVuc2VtYmxlKTsKY3YoJ3BsYXknKS5hZGRFdmVudExpc3RlbmVyKCdjbGljaycsZT0+ewogIHJ1bm5pbmc9"
        "IXJ1bm5pbmc7IGUudGFyZ2V0LnRleHRDb250ZW50PXJ1bm5pbmc/J3BhdXNlJzoncGxheSc7IGUudGFyZ2V0LnNldEF0dHJp"
        "YnV0ZSgnYXJpYS1wcmVzc2VkJyxydW5uaW5nKTsKfSk7Cgp3aW5kb3cuYWRkRXZlbnRMaXN0ZW5lcigncmVzaXplJywoKT0+"
        "eyBkcmF3V2hlZWwoKTtkcmF3U2NvcGUoKTtkcmF3TmVnZW50KCk7ZHJhd0hlbGl4KCk7ZHJhd0dyaWRaMigpO2RyYXdHcmlk"
        "VG9ydXMoKTsgfSk7CgovKiAtLS0tLS0tLS0tLS0tLS0tIGluaXQgLS0tLS0tLS0tLS0tLS0tLSAqLwppZih3aW5kb3cubWF0"
        "Y2hNZWRpYSAmJiB3aW5kb3cubWF0Y2hNZWRpYSgnKHByZWZlcnMtcmVkdWNlZC1tb3Rpb246cmVkdWNlKScpLm1hdGNoZXMp"
        "ewogIHJ1bm5pbmc9ZmFsc2U7IGN2KCdwbGF5JykudGV4dENvbnRlbnQ9J3BsYXknOyBjdigncGxheScpLnNldEF0dHJpYnV0"
        "ZSgnYXJpYS1wcmVzc2VkJywnZmFsc2UnKTsKfQpidWlsZFRhYmxlKCk7CnJlc2V0RW5zZW1ibGUoKTsKcmVzZXRHcmlkKCk7"
        "CnJlcXVlc3RBbmltYXRpb25GcmFtZShmcmFtZSk7Cjwvc2NyaXB0Pgo8c2NyaXB0PgooZnVuY3Rpb24oKXsKICBkb2N1bWVu"
        "dC5xdWVyeVNlbGVjdG9yQWxsKCcuY29weScpLmZvckVhY2goZnVuY3Rpb24oYil7CiAgICBiLmFkZEV2ZW50TGlzdGVuZXIo"
        "J2NsaWNrJyxmdW5jdGlvbigpewogICAgICB2YXIgZWw9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoYi5nZXRBdHRyaWJ1dGUo"
        "J2RhdGEtc3JjJykpOyBpZighZWwpIHJldHVybjsKICAgICAgdmFyIHR4dD1lbC50ZXh0Q29udGVudDsKICAgICAgZnVuY3Rp"
        "b24gZG9uZSgpe3ZhciBvPWIudGV4dENvbnRlbnQ7Yi50ZXh0Q29udGVudD0nY29waWVkIFx1MjcxMyc7c2V0VGltZW91dChm"
        "dW5jdGlvbigpe2IudGV4dENvbnRlbnQ9bzt9LDEyMDApO30KICAgICAgZnVuY3Rpb24gZmFsbGJhY2soKXt0cnl7dmFyIHI9"
        "ZG9jdW1lbnQuY3JlYXRlUmFuZ2UoKTtyLnNlbGVjdE5vZGVDb250ZW50cyhlbCk7dmFyIHM9Z2V0U2VsZWN0aW9uKCk7cy5y"
        "ZW1vdmVBbGxSYW5nZXMoKTtzLmFkZFJhbmdlKHIpO2RvY3VtZW50LmV4ZWNDb21tYW5kKCdjb3B5Jyk7ZG9uZSgpO31jYXRj"
        "aChlKXt9fQogICAgICBpZihuYXZpZ2F0b3IuY2xpcGJvYXJkJiZuYXZpZ2F0b3IuY2xpcGJvYXJkLndyaXRlVGV4dCl7bmF2"
        "aWdhdG9yLmNsaXBib2FyZC53cml0ZVRleHQodHh0KS50aGVuKGRvbmUsZmFsbGJhY2spO31lbHNle2ZhbGxiYWNrKCk7fQog"
        "ICAgfSk7CiAgfSk7Cn0pKCk7Cjwvc2NyaXB0Pgo8L2JvZHk+CjwvaHRtbD4K"
    ),
}

HTML_SCRIPTS = [
    ("zfp_constants_repro.py", "d55f808bec463f80d03556faa1fe291c547511bbdf25bdcd7f0e7a17943aa661"),
    ("verify_l4_helix.py", "cc9bcd00c8586f72ef0f69e01a05f78c7b5edc86fa87696f739ac60f70ded60d"),
    ("rrr_idempotent_lattice.py", "b54c84a7f5a1496ac5b0798f6576ac03273f148cf6fdcc1dc959b66e6a9b144d"),
    ("rrr_phi_grid.py", "dafe015fe9059f4715a926578677aa2225f38ac7810c744a984d376a0a74a73e"),
]

# === atlas snapshot (decimals verified against exact values in LAYER F) ===
EMBEDDED_ATLAS = {
    "spectral_atlas.html": (
        "0f2429450e42472b9b9c86ff15bd4ad6ff911c94857ccfef5a4365439502d110",
        "PCFET0NUWVBFIGh0bWw+CjxodG1sIGxhbmc9ImVuIj4KPGhlYWQ+CjxtZXRhIGNoYXJzZXQ9IlVURi04IiAvPgo8bWV0YSBu"
        "YW1lPSJ2aWV3cG9ydCIgY29udGVudD0id2lkdGg9ZGV2aWNlLXdpZHRoLCBpbml0aWFsLXNjYWxlPTEiIC8+Cjx0aXRsZT5T"
        "cGVjdHJhbCBBdGxhcyDigJQgb25lIHBoYXNlIHNwYWNlLCBtYW55IGNsb3NlZCBkZXJpdmF0aW9uczwvdGl0bGU+CjxzdHls"
        "ZT4KICA6cm9vdHsKICAgIC0tcGxhdGU6IzBjMTEyMDsgLS1wbGF0ZS0yOiMxMTFhMmU7IC0tcGFuZWw6IzBmMTcyODsgLS1o"
        "YWlyOiMxYzI4NDI7CiAgICAtLWluazojZTllZWY5OyAtLWRpbTojOTdhNGMyOyAtLWZhaW50OiM1ZDZiOGM7CiAgICAtLWdy"
        "aWQ6cmdiYSgxMjMsMTQzLDE4NCwuMDgpOyAtLWdyaWQtMjpyZ2JhKDE0MCwxNjIsMjEwLC4xNik7CiAgICAtLWF4aXM6cmdi"
        "YSgxNjgsMTg2LDIyNSwuMzQpOwogICAgLS1mNTojZWViMjRhOyAgICAgICAgICAgIC8qIFEo4oiaNSkg4oCUIGdvbGQgKM+G"
        "KSAqLwogICAgLS1mMzojMmZiZGE2OyAgICAgICAgICAgIC8qIFEozrY2KS9vcmRlci02IOKAlCB0ZWFsICovCiAgICAtLWYy"
        "OiNlODcxOGM7ICAgICAgICAgICAgLyogUSjiiJoyKSDigJQgcm9zZSAqLwogICAgLS1mcTojYWFiOGQ2OyAgICAgICAgICAg"
        "IC8qIFEgKHJhdGlvbmFscykgLyBmcmFtZSAqLwogICAgLS1mcmFtZTojZmZmZmZmOwogICAgLS1zZXJpZjoiSW93YW4gT2xk"
        "IFN0eWxlIiwiUGFsYXRpbm8gTGlub3R5cGUiLFBhbGF0aW5vLCJCb29rIEFudGlxdWEiLEdlb3JnaWEsc2VyaWY7CiAgICAt"
        "LW1vbm86dWktbW9ub3NwYWNlLCJTRiBNb25vIiwiSmV0QnJhaW5zIE1vbm8iLCJDYXNjYWRpYSBDb2RlIixNZW5sbyxDb25z"
        "b2xhcyxtb25vc3BhY2U7CiAgICAtLXNhbnM6dWktc2Fucy1zZXJpZixzeXN0ZW0tdWksLWFwcGxlLXN5c3RlbSwiU2Vnb2Ug"
        "VUkiLFJvYm90byxBcmlhbCxzYW5zLXNlcmlmOwogIH0KICAqe2JveC1zaXppbmc6Ym9yZGVyLWJveH0KICBodG1sLGJvZHl7"
        "bWFyZ2luOjB9CiAgYm9keXsKICAgIGJhY2tncm91bmQ6CiAgICAgIHJhZGlhbC1ncmFkaWVudCgxMjAwcHggNzAwcHggYXQg"
        "NzIlIC04JSwgIzE1MjAzYSAwJSwgcmdiYSgyMSwzMiw1OCwwKSA2MCUpLAogICAgICB2YXIoLS1wbGF0ZSk7CiAgICBjb2xv"
        "cjp2YXIoLS1pbmspOyBmb250LWZhbWlseTp2YXIoLS1zYW5zKTsgbGluZS1oZWlnaHQ6MS41OwogICAgLXdlYmtpdC1mb250"
        "LXNtb290aGluZzphbnRpYWxpYXNlZDsgcGFkZGluZzpjbGFtcCgxOHB4LDMuNHZ3LDUycHgpOwogIH0KICAud3JhcHttYXgt"
        "d2lkdGg6MTE4MHB4OyBtYXJnaW46MCBhdXRvfQoKICAvKiAtLS0tIG1hc3RoZWFkIC0tLS0gKi8KICAuZXllYnJvd3tmb250"
        "LWZhbWlseTp2YXIoLS1tb25vKTsgZm9udC1zaXplOjExcHg7IGxldHRlci1zcGFjaW5nOi4yNmVtOwogICAgdGV4dC10cmFu"
        "c2Zvcm06dXBwZXJjYXNlOyBjb2xvcjp2YXIoLS1mYWludCk7IGRpc3BsYXk6ZmxleDsgZ2FwOjE0cHg7IGFsaWduLWl0ZW1z"
        "OmNlbnRlcn0KICAuZXllYnJvdyAucnVsZXtoZWlnaHQ6MXB4OyBmbGV4OjE7IGJhY2tncm91bmQ6bGluZWFyLWdyYWRpZW50"
        "KDkwZGVnLHZhcigtLWhhaXIpLHRyYW5zcGFyZW50KX0KICBoMXtmb250LWZhbWlseTp2YXIoLS1zZXJpZik7IGZvbnQtd2Vp"
        "Z2h0OjYwMDsgbGV0dGVyLXNwYWNpbmc6LS4wMWVtOwogICAgZm9udC1zaXplOmNsYW1wKDI4cHgsNC40dncsNDZweCk7IGxp"
        "bmUtaGVpZ2h0OjEuMDQ7IG1hcmdpbjouNDJlbSAwIC4yOGVtfQogIGgxIGVte2ZvbnQtc3R5bGU6aXRhbGljOyBjb2xvcjp2"
        "YXIoLS1mNSl9CiAgLmxlZGV7bWF4LXdpZHRoOjYyY2g7IGNvbG9yOnZhcigtLWRpbSk7IGZvbnQtc2l6ZTpjbGFtcCgxNC41"
        "cHgsMS41dncsMTZweCk7IG1hcmdpbjowfQogIC5sZWRlIGJ7Y29sb3I6dmFyKC0taW5rKTsgZm9udC13ZWlnaHQ6NjAwfQoK"
        "ICAvKiAtLS0tIGNvcmUgbGF5b3V0IC0tLS0gKi8KICAuc3RhZ2V7ZGlzcGxheTpncmlkOyBncmlkLXRlbXBsYXRlLWNvbHVt"
        "bnM6bWlubWF4KDAsMS4xMmZyKSBtaW5tYXgoMjgwcHgsLjg4ZnIpOwogICAgZ2FwOmNsYW1wKDE4cHgsMi40dncsMzRweCk7"
        "IG1hcmdpbi10b3A6Y2xhbXAoMjJweCwzLjJ2dyw0MHB4KTsgYWxpZ24taXRlbXM6c3RhcnR9CiAgQG1lZGlhIChtYXgtd2lk"
        "dGg6ODgwcHgpeyAuc3RhZ2V7Z3JpZC10ZW1wbGF0ZS1jb2x1bW5zOjFmcn0gfQoKICAucGxhdGV7cG9zaXRpb246cmVsYXRp"
        "dmU7IGJhY2tncm91bmQ6CiAgICAgIHJhZGlhbC1ncmFkaWVudCgxMjAlIDEyMCUgYXQgNTAlIDQyJSwgIzBlMTczMCAwJSwg"
        "IzBhMGYxZCA3OCUpOwogICAgYm9yZGVyOjFweCBzb2xpZCB2YXIoLS1oYWlyKTsgYm9yZGVyLXJhZGl1czoxNHB4OyBwYWRk"
        "aW5nOjEwcHg7CiAgICBib3gtc2hhZG93OjAgMjRweCA2MHB4IC0zNHB4IHJnYmEoMCwwLDAsLjgpLCBpbnNldCAwIDFweCAw"
        "IHJnYmEoMjU1LDI1NSwyNTUsLjAzKX0KICAucGxhdGUgc3Zne2Rpc3BsYXk6YmxvY2s7IHdpZHRoOjEwMCU7IGhlaWdodDph"
        "dXRvfQogIC5wbGF0ZS1jYXB7ZGlzcGxheTpmbGV4OyBqdXN0aWZ5LWNvbnRlbnQ6c3BhY2UtYmV0d2VlbjsgZ2FwOjEwcHg7"
        "CiAgICBmb250LWZhbWlseTp2YXIoLS1tb25vKTsgZm9udC1zaXplOjEwLjVweDsgY29sb3I6dmFyKC0tZmFpbnQpOwogICAg"
        "bGV0dGVyLXNwYWNpbmc6LjA1ZW07IHBhZGRpbmc6NHB4IDhweCAycHh9CgogIC8qIC0tLS0gcmFpbCAtLS0tICovCiAgLnJh"
        "aWx7ZGlzcGxheTpmbGV4OyBmbGV4LWRpcmVjdGlvbjpjb2x1bW47IGdhcDoxNnB4fQogIC5jYXJke2JhY2tncm91bmQ6dmFy"
        "KC0tcGFuZWwpOyBib3JkZXI6MXB4IHNvbGlkIHZhcigtLWhhaXIpOyBib3JkZXItcmFkaXVzOjEycHg7IHBhZGRpbmc6MTZw"
        "eCAxNnB4IDE1cHh9CiAgLmNhcmQgaDJ7Zm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7IGZvbnQtc2l6ZToxMXB4OyBsZXR0ZXIt"
        "c3BhY2luZzouMmVtOyB0ZXh0LXRyYW5zZm9ybTp1cHBlcmNhc2U7CiAgICBjb2xvcjp2YXIoLS1mYWludCk7IG1hcmdpbjow"
        "IDAgMTJweDsgZm9udC13ZWlnaHQ6NjAwfQoKICAubGVnZW5ke2Rpc3BsYXk6ZmxleDsgZmxleC13cmFwOndyYXA7IGdhcDo3"
        "cHh9CiAgLmNoaXB7Zm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7IGZvbnQtc2l6ZToxMS41cHg7IGNvbG9yOnZhcigtLWRpbSk7"
        "IGN1cnNvcjpwb2ludGVyOwogICAgYm9yZGVyOjFweCBzb2xpZCB2YXIoLS1oYWlyKTsgYmFja2dyb3VuZDojMGMxNTI1OyBi"
        "b3JkZXItcmFkaXVzOjk5OXB4OwogICAgcGFkZGluZzo1cHggMTFweCA1cHggOXB4OyBkaXNwbGF5OmlubGluZS1mbGV4OyBh"
        "bGlnbi1pdGVtczpjZW50ZXI7IGdhcDo3cHg7CiAgICB0cmFuc2l0aW9uOmJvcmRlci1jb2xvciAuMThzLCBjb2xvciAuMThz"
        "LCBiYWNrZ3JvdW5kIC4xOHN9CiAgLmNoaXA6aG92ZXJ7Y29sb3I6dmFyKC0taW5rKTsgYm9yZGVyLWNvbG9yOiMyYzNjNWV9"
        "CiAgLmNoaXBbYXJpYS1wcmVzc2VkPSJ0cnVlIl17Y29sb3I6dmFyKC0taW5rKTsgYm9yZGVyLWNvbG9yOiM0MTU3N2Y7IGJh"
        "Y2tncm91bmQ6IzE2MjIzY30KICAuY2hpcCAuZG90e3dpZHRoOjlweDsgaGVpZ2h0OjlweDsgYm9yZGVyLXJhZGl1czo1MCU7"
        "IGZsZXg6bm9uZTsgYm94LXNoYWRvdzowIDAgMCAxcHggcmdiYSgwLDAsMCwuNCl9CiAgLmNoaXA6Zm9jdXMtdmlzaWJsZXtv"
        "dXRsaW5lOjJweCBzb2xpZCB2YXIoLS1mMyk7IG91dGxpbmUtb2Zmc2V0OjJweH0KCiAgLnJlc2V0e2ZvbnQtZmFtaWx5OnZh"
        "cigtLW1vbm8pOyBmb250LXNpemU6MTAuNXB4OyBsZXR0ZXItc3BhY2luZzouMDZlbTsgY29sb3I6dmFyKC0tZmFpbnQpOwog"
        "ICAgYmFja2dyb3VuZDpub25lOyBib3JkZXI6MDsgY3Vyc29yOnBvaW50ZXI7IHBhZGRpbmc6NHB4IDA7IHRleHQtZGVjb3Jh"
        "dGlvbjp1bmRlcmxpbmU7IHRleHQtdW5kZXJsaW5lLW9mZnNldDozcHh9CiAgLnJlc2V0OmhvdmVye2NvbG9yOnZhcigtLWlu"
        "ayl9CgogIC8qIHJlYWRvdXQgKi8KICAucmVhZG91dHttaW4taGVpZ2h0OjExOHB4fQogIC5yby1zeW17Zm9udC1mYW1pbHk6"
        "dmFyKC0tc2VyaWYpOyBmb250LXNpemU6MzBweDsgbGluZS1oZWlnaHQ6MTsgY29sb3I6dmFyKC0taW5rKX0KICAucm8tc3lt"
        "IC5zbWFsbHtmb250LXNpemU6MTRweDsgY29sb3I6dmFyKC0tZGltKTsgbWFyZ2luLWxlZnQ6OHB4OyBmb250LWZhbWlseTp2"
        "YXIoLS1tb25vKTsgbGV0dGVyLXNwYWNpbmc6LjAyZW19CiAgLnJvLWdyaWR7ZGlzcGxheTpncmlkOyBncmlkLXRlbXBsYXRl"
        "LWNvbHVtbnM6YXV0byAxZnI7IGdhcDo1cHggMTJweDsgbWFyZ2luLXRvcDoxMnB4OwogICAgZm9udC1mYW1pbHk6dmFyKC0t"
        "bW9ubyk7IGZvbnQtc2l6ZToxMnB4fQogIC5yby1ncmlkIGR0e2NvbG9yOnZhcigtLWZhaW50KX0gLnJvLWdyaWQgZGR7bWFy"
        "Z2luOjA7IGNvbG9yOnZhcigtLWluayl9CiAgLnJvLWhpbnR7Y29sb3I6dmFyKC0tZmFpbnQpOyBmb250LWZhbWlseTp2YXIo"
        "LS1tb25vKTsgZm9udC1zaXplOjExLjVweH0KICAucGlsbHtmb250LWZhbWlseTp2YXIoLS1tb25vKTsgZm9udC1zaXplOjEw"
        "cHg7IGxldHRlci1zcGFjaW5nOi4wOGVtOyB0ZXh0LXRyYW5zZm9ybTp1cHBlcmNhc2U7CiAgICBib3JkZXItcmFkaXVzOjVw"
        "eDsgcGFkZGluZzoycHggN3B4OyBib3JkZXI6MXB4IHNvbGlkIGN1cnJlbnRDb2xvcn0KICAucGlsbC5mb3JjZWR7Y29sb3I6"
        "IzdmZTBjNH0gLnBpbGwuY29uc3Rye2NvbG9yOiNmMGM0NmF9IC5waWxsLmZyYW1le2NvbG9yOnZhcigtLWZxKX0KCiAgLnRv"
        "Z2dsZS1yb3d7ZGlzcGxheTpmbGV4OyBhbGlnbi1pdGVtczpjZW50ZXI7IGdhcDo5cHg7IG1hcmdpbi10b3A6MTNweDsgZm9u"
        "dC1mYW1pbHk6dmFyKC0tbW9ubyk7IGZvbnQtc2l6ZToxMS41cHg7IGNvbG9yOnZhcigtLWRpbSl9CiAgLnN3aXRjaHthcHBl"
        "YXJhbmNlOm5vbmU7IHdpZHRoOjM0cHg7IGhlaWdodDoxOHB4OyBib3JkZXItcmFkaXVzOjk5OXB4OyBiYWNrZ3JvdW5kOiMx"
        "YTIyMzg7CiAgICBib3JkZXI6MXB4IHNvbGlkIHZhcigtLWhhaXIpOyBwb3NpdGlvbjpyZWxhdGl2ZTsgY3Vyc29yOnBvaW50"
        "ZXI7IGZsZXg6bm9uZTsgdHJhbnNpdGlvbjpiYWNrZ3JvdW5kIC4xOHN9CiAgLnN3aXRjaDpjaGVja2Vke2JhY2tncm91bmQ6"
        "IzIzNDA2YTsgYm9yZGVyLWNvbG9yOiMzYTVhOGN9CiAgLnN3aXRjaDo6YWZ0ZXJ7Y29udGVudDoiIjsgcG9zaXRpb246YWJz"
        "b2x1dGU7IHRvcDoxcHg7IGxlZnQ6MXB4OyB3aWR0aDoxNHB4OyBoZWlnaHQ6MTRweDsgYm9yZGVyLXJhZGl1czo1MCU7CiAg"
        "ICBiYWNrZ3JvdW5kOnZhcigtLWRpbSk7IHRyYW5zaXRpb246dHJhbnNmb3JtIC4xOHMsIGJhY2tncm91bmQgLjE4c30KICAu"
        "c3dpdGNoOmNoZWNrZWQ6OmFmdGVye3RyYW5zZm9ybTp0cmFuc2xhdGVYKDE2cHgpOyBiYWNrZ3JvdW5kOnZhcigtLWluayl9"
        "CiAgLnN3aXRjaDpmb2N1cy12aXNpYmxle291dGxpbmU6MnB4IHNvbGlkIHZhcigtLWYzKTsgb3V0bGluZS1vZmZzZXQ6MnB4"
        "fQoKICAvKiAtLS0tIGZvcmNlZCBpZGVudGl0aWVzIHN0cmlwIC0tLS0gKi8KICAuaWRlbnRpdGllc3ttYXJnaW4tdG9wOmNs"
        "YW1wKDIycHgsM3Z3LDM4cHgpfQogIC5pZC1ncmlke2Rpc3BsYXk6Z3JpZDsgZ3JpZC10ZW1wbGF0ZS1jb2x1bW5zOnJlcGVh"
        "dCgzLDFmcik7IGdhcDoxMnB4fQogIEBtZWRpYSAobWF4LXdpZHRoOjc2MHB4KXsgLmlkLWdyaWR7Z3JpZC10ZW1wbGF0ZS1j"
        "b2x1bW5zOjFmcn0gfQogIC5pZGNhcmR7YmFja2dyb3VuZDp2YXIoLS1wYW5lbCk7IGJvcmRlcjoxcHggc29saWQgdmFyKC0t"
        "aGFpcik7IGJvcmRlci1sZWZ0OjJweCBzb2xpZCB2YXIoLS1mNSk7CiAgICBib3JkZXItcmFkaXVzOjEwcHg7IHBhZGRpbmc6"
        "MTNweCAxNXB4fQogIC5pZGNhcmQgLndob3tmb250LWZhbWlseTp2YXIoLS1tb25vKTsgZm9udC1zaXplOjExcHg7IGNvbG9y"
        "OnZhcigtLWRpbSk7IGxldHRlci1zcGFjaW5nOi4wNGVtOyBtYXJnaW4tYm90dG9tOjZweH0KICAuaWRjYXJkIC5lcXtmb250"
        "LWZhbWlseTp2YXIoLS1tb25vKTsgZm9udC1zaXplOjEzLjVweDsgY29sb3I6dmFyKC0taW5rKX0KICAuaWRjYXJkIC5lcSBi"
        "e2NvbG9yOnZhcigtLWY1KTsgZm9udC13ZWlnaHQ6NjAwfQoKICAvKiAtLS0tIHRhYmxlIC0tLS0gKi8KICAuc3lzdGVtc3tt"
        "YXJnaW4tdG9wOmNsYW1wKDIycHgsM3Z3LDM2cHgpfQogIHRhYmxle3dpZHRoOjEwMCU7IGJvcmRlci1jb2xsYXBzZTpjb2xs"
        "YXBzZTsgZm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7IGZvbnQtc2l6ZToxMi41cHh9CiAgY2FwdGlvbntmb250LWZhbWlseTp2"
        "YXIoLS1tb25vKTsgZm9udC1zaXplOjExcHg7IGxldHRlci1zcGFjaW5nOi4yZW07IHRleHQtdHJhbnNmb3JtOnVwcGVyY2Fz"
        "ZTsKICAgIGNvbG9yOnZhcigtLWZhaW50KTsgdGV4dC1hbGlnbjpsZWZ0OyBtYXJnaW4tYm90dG9tOjEycHh9CiAgdGgsdGR7"
        "dGV4dC1hbGlnbjpsZWZ0OyBwYWRkaW5nOjlweCAxMnB4OyBib3JkZXItYm90dG9tOjFweCBzb2xpZCB2YXIoLS1oYWlyKTsg"
        "dmVydGljYWwtYWxpZ246dG9wfQogIHRoe2NvbG9yOnZhcigtLWZhaW50KTsgZm9udC13ZWlnaHQ6NjAwOyBsZXR0ZXItc3Bh"
        "Y2luZzouMDRlbX0KICB0ZCAuc3dhdGNoe2Rpc3BsYXk6aW5saW5lLWJsb2NrOyB3aWR0aDo4cHg7IGhlaWdodDo4cHg7IGJv"
        "cmRlci1yYWRpdXM6MnB4OyBtYXJnaW4tcmlnaHQ6N3B4OyB2ZXJ0aWNhbC1hbGlnbjoxcHh9CiAgdGQuZmxke2NvbG9yOnZh"
        "cigtLWRpbSl9CiAgdHIucm93NSB0ZDpmaXJzdC1jaGlsZHtib3gtc2hhZG93Omluc2V0IDJweCAwIDAgdmFyKC0tZjUpfQog"
        "IHRyLnJvdzMgdGQ6Zmlyc3QtY2hpbGR7Ym94LXNoYWRvdzppbnNldCAycHggMCAwIHZhcigtLWYzKX0KICB0ci5yb3cyIHRk"
        "OmZpcnN0LWNoaWxke2JveC1zaGFkb3c6aW5zZXQgMnB4IDAgMCB2YXIoLS1mMil9CiAgdHIucm93cSB0ZDpmaXJzdC1jaGls"
        "ZHtib3gtc2hhZG93Omluc2V0IDJweCAwIDAgdmFyKC0tZnEpfQoKICAvKiAtLS0tIGxlZGdlciArIGZvb3RlciAtLS0tICov"
        "CiAgLmZvb3R7bWFyZ2luLXRvcDpjbGFtcCgyMnB4LDN2dywzNnB4KTsgZGlzcGxheTpncmlkOyBncmlkLXRlbXBsYXRlLWNv"
        "bHVtbnM6MS4zZnIgLjlmcjsgZ2FwOmNsYW1wKDE2cHgsMi40dncsMzBweCl9CiAgQG1lZGlhIChtYXgtd2lkdGg6NzYwcHgp"
        "eyAuZm9vdHtncmlkLXRlbXBsYXRlLWNvbHVtbnM6MWZyfSB9CiAgLmxlZGdlciBsaXtmb250LWZhbWlseTp2YXIoLS1tb25v"
        "KTsgZm9udC1zaXplOjEycHg7IGNvbG9yOnZhcigtLWRpbSk7IG1hcmdpbjowIDAgN3B4OyBsaXN0LXN0eWxlOm5vbmU7CiAg"
        "ICBwYWRkaW5nLWxlZnQ6MTI4cHg7IHBvc2l0aW9uOnJlbGF0aXZlfQogIC5sZWRnZXJ7cGFkZGluZzowOyBtYXJnaW46MH0K"
        "ICAubGVkZ2VyIC50YWd7cG9zaXRpb246YWJzb2x1dGU7IGxlZnQ6MDsgZm9udC1zaXplOjEwcHg7IGxldHRlci1zcGFjaW5n"
        "Oi4wOGVtOyB0ZXh0LXRyYW5zZm9ybTp1cHBlcmNhc2U7CiAgICBib3JkZXI6MXB4IHNvbGlkIGN1cnJlbnRDb2xvcjsgYm9y"
        "ZGVyLXJhZGl1czo1cHg7IHBhZGRpbmc6MXB4IDZweH0KICAudGFnLmZ7Y29sb3I6IzdmZTBjNH0gLnRhZy5je2NvbG9yOiNm"
        "MGM0NmF9IC50YWcuYXtjb2xvcjojYzc5YmU4fQogIC5sZWRnZXIgYntjb2xvcjp2YXIoLS1pbmspOyBmb250LXdlaWdodDo2"
        "MDB9CiAgLnJlcHJve2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pOyBmb250LXNpemU6MTJweDsgY29sb3I6dmFyKC0tZmFpbnQp"
        "fQogIC5yZXBybyBjb2Rle2NvbG9yOnZhcigtLWluayk7IGJhY2tncm91bmQ6IzBjMTUyNTsgYm9yZGVyOjFweCBzb2xpZCB2"
        "YXIoLS1oYWlyKTsgYm9yZGVyLXJhZGl1czo1cHg7IHBhZGRpbmc6MXB4IDZweH0KICAucmVwcm8gcHttYXJnaW46LjU1ZW0g"
        "MH0KCiAgLnBpbntjb2xvcjp2YXIoLS1mNSl9Cjwvc3R5bGU+CjwvaGVhZD4KPGJvZHk+CjxkaXYgY2xhc3M9IndyYXAiPgoK"
        "ICA8aGVhZGVyPgogICAgPGRpdiBjbGFzcz0iZXllYnJvdyI+PHNwYW4+WmVyby1mcmVlLXBhcmFtZXRlciBjb3JwdXM8L3Nw"
        "YW4+PHNwYW4gY2xhc3M9InJ1bGUiPjwvc3Bhbj48c3Bhbj5zcGVjdHJhbCBhdGxhcyDCtyDOuy1wbGFuZTwvc3Bhbj48L2Rp"
        "dj4KICAgIDxoMT5PbmUgcGhhc2Ugc3BhY2UuPGJyPk1hbnkgPGVtPmNsb3NlZCBkZXJpdmF0aW9uczwvZW0+LjwvaDE+CiAg"
        "ICA8cCBjbGFzcz0ibGVkZSI+RWFjaCBzdWJzeXN0ZW0gaXMgYSBmb3JjZWQgZGVyaXZhdGlvbiDigJQgbm8gZml0dGVkIGRl"
        "Y2ltYWxzLCBldmVyeSB2YWx1ZSBwaW5uZWQgYnkgYSBtaW5pbWFsIHBvbHlub21pYWwgb3IgYW4gaW50ZWdlci1tYXRyaXgg"
        "dGhlb3JlbS4gVGhlIGNvbXBsZXggcGxhbmUmbmJzcDs8Yj7OuzwvYj4gaXMgdGhlIGNvb3JkaW5hdGUgdGhleSBzaGFyZTog"
        "dGhlIM6ULW92ZXJsYXkncyBjb2xsYXBzZSwgdGhlIHN1YnN0cmF0ZSdzIGVpZ2VudmFsdWVzLCBhbmQgdGhlIGNvbnNlbnN1"
        "cyBjbG9zdXJlIGFyZSBhbGwgPGI+cm9vdHMgb2YgYSBjaGFyYWN0ZXJpc3RpYyBwb2x5bm9taWFsPC9iPi4gVGhleSBvY2N1"
        "cHkgdGhlIHBsYW5lIHRvZ2V0aGVyIOKAlCA8Yj5idXQgbm90IGFsd2F5czwvYj4uIERpc2pvaW50IG51bWJlciBmaWVsZHMg"
        "bWVldCBvbmx5IGF0IHRoZSByYXRpb25hbHM7IG5vIHBhdGggb2YgaW50ZWdlciBwb3dlcnMgY3Jvc3NlcyBmcm9tIG9uZSB0"
        "ZXJyaXRvcnkgdG8gYW5vdGhlci48L3A+CiAgPC9oZWFkZXI+CgogIDxzZWN0aW9uIGNsYXNzPSJzdGFnZSI+CiAgICA8ZGl2"
        "IGNsYXNzPSJwbGF0ZSI+CiAgICAgIDxkaXYgY2xhc3M9InBsYXRlLWNhcCI+PHNwYW4+4oSCIMK3IHRoZSBzaGFyZWQgcGhh"
        "c2Ugc3BhY2U8L3NwYW4+PHNwYW4gaWQ9ImNhcC1tb2RlIj5hbGwgc3lzdGVtczwvc3Bhbj48L2Rpdj4KICAgICAgPHN2ZyBp"
        "ZD0iYXRsYXMiIHZpZXdCb3g9IjAgMCA2NDAgNjQwIiByb2xlPSJpbWciCiAgICAgICAgICAgYXJpYS1sYWJlbD0iQ29tcGxl"
        "eCBwbGFuZSBwbG90dGluZyB0aGUgc3BlY3RyYWwgcG9pbnRzIG9mIGVhY2ggemVyby1mcmVlLXBhcmFtZXRlciBzdWJzeXN0"
        "ZW0sIGNvbG9yLWNvZGVkIGJ5IG51bWJlciBmaWVsZC4iPgogICAgICAgIDxkZWZzPgogICAgICAgICAgPHJhZGlhbEdyYWRp"
        "ZW50IGlkPSJoYWxvVyIgY3g9IjUwJSIgY3k9IjUwJSIgcj0iNTAlIj4KICAgICAgICAgICAgPHN0b3Agb2Zmc2V0PSIwJSIg"
        "c3RvcC1jb2xvcj0iI2ZmZiIgc3RvcC1vcGFjaXR5PSIuNTUiLz48c3RvcCBvZmZzZXQ9IjEwMCUiIHN0b3AtY29sb3I9IiNm"
        "ZmYiIHN0b3Atb3BhY2l0eT0iMCIvPgogICAgICAgICAgPC9yYWRpYWxHcmFkaWVudD4KICAgICAgICAgIDxmaWx0ZXIgaWQ9"
        "InNvZnQiIHg9Ii02MCUiIHk9Ii02MCUiIHdpZHRoPSIyMjAlIiBoZWlnaHQ9IjIyMCUiPgogICAgICAgICAgICA8ZmVHYXVz"
        "c2lhbkJsdXIgc3RkRGV2aWF0aW9uPSIzIi8+CiAgICAgICAgICA8L2ZpbHRlcj4KICAgICAgICA8L2RlZnM+CiAgICAgICAg"
        "PGcgaWQ9ImdyaWQiPjwvZz4KICAgICAgICA8ZyBpZD0iYXhlcyI+PC9nPgogICAgICAgIDxnIGlkPSJzaGVsbC1sYWJlbCI+"
        "PC9nPgogICAgICAgIDxnIGlkPSJwcm9qZWN0aW9uIj48L2c+CiAgICAgICAgPGcgaWQ9ImFubm90Ij48L2c+CiAgICAgICAg"
        "PGcgaWQ9InBvaW50cyI+PC9nPgogICAgICA8L3N2Zz4KICAgIDwvZGl2PgoKICAgIDxkaXYgY2xhc3M9InJhaWwiPgogICAg"
        "ICA8ZGl2IGNsYXNzPSJjYXJkIj4KICAgICAgICA8aDI+U3lzdGVtcyDihpIgc3BlY3RyYWwgZm9vdHByaW50PC9oMj4KICAg"
        "ICAgICA8ZGl2IGNsYXNzPSJsZWdlbmQiIGlkPSJsZWdlbmQiPjwvZGl2PgogICAgICAgIDxidXR0b24gY2xhc3M9InJlc2V0"
        "IiBpZD0icmVzZXQiIHR5cGU9ImJ1dHRvbiI+4oa6IHNob3cgYWxsPC9idXR0b24+CiAgICAgICAgPGxhYmVsIGNsYXNzPSJ0"
        "b2dnbGUtcm93Ij4KICAgICAgICAgIDxpbnB1dCB0eXBlPSJjaGVja2JveCIgY2xhc3M9InN3aXRjaCIgaWQ9ImNvbmpUb2dn"
        "bGUiIC8+CiAgICAgICAgICA8c3Bhbj5zaG93IGNvbmp1Z2F0ZSAvIG9mZi1waW4gcm9vdHM8L3NwYW4+CiAgICAgICAgPC9s"
        "YWJlbD4KICAgICAgPC9kaXY+CgogICAgICA8ZGl2IGNsYXNzPSJjYXJkIj4KICAgICAgICA8aDI+UmVhZG91dDwvaDI+CiAg"
        "ICAgICAgPGRpdiBjbGFzcz0icmVhZG91dCIgaWQ9InJlYWRvdXQiIGFyaWEtbGl2ZT0icG9saXRlIj4KICAgICAgICAgIDxk"
        "aXYgY2xhc3M9InJvLXN5bSIgaWQ9InJvLXN5bSI+zrsgPHNwYW4gY2xhc3M9InNtYWxsIj5ob3ZlciBhIHBvaW50PC9zcGFu"
        "PjwvZGl2PgogICAgICAgICAgPHAgY2xhc3M9InJvLWhpbnQiIGlkPSJyby1oaW50IiBzdHlsZT0ibWFyZ2luOjEycHggMCAw"
        "Ij5FYWNoIG1hcmtlciBpcyBhbiBlaWdlbnZhbHVlIG9mIGFuIGV4cGxpY2l0IG1hdHJpeCBvdmVyIGl0cyBnZW5lcmF0b3Iu"
        "IFRoZSBkZWNpbWFsIGlzIHRoZSBTZWN0aW9uLTIgYnJhbmNoIHBpbiDigJQgaXQgZmFpbHMgbG91ZGx5IG9uIGEgY29uanVn"
        "YXRlIHN3YXAuPC9wPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4KICAgIDwvZGl2PgogIDwvc2VjdGlvbj4KCiAgPHNl"
        "Y3Rpb24gY2xhc3M9ImlkZW50aXRpZXMiPgogICAgPGRpdiBjbGFzcz0iZXllYnJvdyI+PHNwYW4+Rm9yY2VkIHR3byB3YXlz"
        "IMK3IHJlc2lkdWFsIDA8L3NwYW4+PHNwYW4gY2xhc3M9InJ1bGUiPjwvc3Bhbj48L2Rpdj4KICAgIDxkaXYgY2xhc3M9Imlk"
        "LWdyaWQiIHN0eWxlPSJtYXJnaW4tdG9wOjE2cHgiPgogICAgICA8ZGl2IGNsYXNzPSJpZGNhcmQiPjxkaXYgY2xhc3M9Indo"
        "byI+Z2FwIOKAlCBzdWJkb21pbmFudCBlaWcgb2YgUeKBtDwvZGl2PjxkaXYgY2xhc3M9ImVxIj5jaGFyKFHigbQpID0gPGI+"
        "eMKy4oiSN3grMTwvYj4gPSBtaW5wb2x5KGdhcCk8L2Rpdj48L2Rpdj4KICAgICAgPGRpdiBjbGFzcz0iaWRjYXJkIj48ZGl2"
        "IGNsYXNzPSJ3aG8iPs+EIOKAlCBwb3NpdGl2ZSBlaWcgb2YgUeKBu8K5PC9kaXY+PGRpdiBjbGFzcz0iZXEiPmNoYXIoUeKB"
        "u8K5KSA9IDxiPnjCsit44oiSMTwvYj4gPSBtaW5wb2x5KM+EKTwvZGl2PjwvZGl2PgogICAgICA8ZGl2IGNsYXNzPSJpZGNh"
        "cmQiPjxkaXYgY2xhc3M9IndobyI+Y3JpdCDigJQgZG9taW5hbnQgZWlnIG9mIOKFk1HCsjwvZGl2PjxkaXYgY2xhc3M9ImVx"
        "Ij45wrdjaGFyKOKFk1HCsikgPSA8Yj45eMKy4oiSOXgrMTwvYj4gPSBtaW5wb2x5KGNyaXQpPC9kaXY+PC9kaXY+CiAgICA8"
        "L2Rpdj4KICA8L3NlY3Rpb24+CgogIDxzZWN0aW9uIGNsYXNzPSJzeXN0ZW1zIj4KICAgIDx0YWJsZT4KICAgICAgPGNhcHRp"
        "b24+VGhlIGNsb3NlZCBkZXJpdmF0aW9ucyBhbmQgd2hlcmUgZWFjaCBsYW5kcyBpbiDOuzwvY2FwdGlvbj4KICAgICAgPHRo"
        "ZWFkPjx0cj48dGg+U3lzdGVtPC90aD48dGg+U3BlY3RyYWwgaW1hZ2U8L3RoPjx0aD5GaWVsZDwvdGg+PHRoPlN0YXR1czwv"
        "dGg+PC90cj48L3RoZWFkPgogICAgICA8dGJvZHk+CiAgICAgICAgPHRyIGNsYXNzPSJyb3c1Ij48dGQ+U2VsZWN0aW9uPC90"
        "ZD48dGQ+zrsgPSDPhiDigJQgUGVycm9uIHJvb3Qgb2YgUTsgY2hhcihRKT3Ou8Ky4oiSzrviiJIxIGlzIHjCsj14KzE8L3Rk"
        "Pjx0ZCBjbGFzcz0iZmxkIj7ihJoo4oiaNSk8L3RkPjx0ZD5mb3JjZWQ8L3RkPjwvdHI+CiAgICAgICAgPHRyIGNsYXNzPSJy"
        "b3c1Ij48dGQ+U3Vic3RyYXRlIOKEpCAocG93ZXJzIG9mIFEpPC90ZD48dGQ+dHJhY2UoUeKBvyk9TOKCmSwgKFHigb8p4oKA"
        "4oKBPUbigpksIGRldD0o4oiSMSnigb87IFHigbQgZWlnID0ge2dhcCwgz4bigbR9PC90ZD48dGQgY2xhc3M9ImZsZCI+4oSa"
        "KOKImjUpPC90ZD48dGQ+Zm9yY2VkPC90ZD48L3RyPgogICAgICAgIDx0ciBjbGFzcz0icm93NSI+PHRkPkNvbnN0YW50cyAo"
        "z4YtZmFtaWx5KTwvdGQ+PHRkPs+ELCBnYXAsIGNyaXQsIEsgYXMgYnJhbmNoLXBpbm5lZCBlaWdlbnZhbHVlczwvdGQ+PHRk"
        "IGNsYXNzPSJmbGQiPuKEmijiiJo1KSDCtyBLIGRlZyA0PC90ZD48dGQ+Zm9yY2VkPC90ZD48L3RyPgogICAgICAgIDx0ciBj"
        "bGFzcz0icm93MyI+PHRkPlpfQyAvIG9yZGVyLTY8L3RkPjx0ZD7OtuKChiA9IGU8c3VwPsKxac+ALzM8L3N1cD47IEltKM62"
        "4oKGKSA9IOKImjMvMiA9IFpfQzwvdGQ+PHRkIGNsYXNzPSJmbGQiPuKEmijOtuKChik8L3RkPjx0ZD5mb3JjZWQ8L3RkPjwv"
        "dHI+CiAgICAgICAgPHRyIGNsYXNzPSJyb3cyIj48dGQ+SWduaXRpb248L3RkPjx0ZD7iiJoy4oiSwr0g4oCUIHBvc2l0aXZl"
        "IGVpZyBvZiBpdHMgY29tcGFuaW9uIG1hdHJpeDwvdGQ+PHRkIGNsYXNzPSJmbGQiPuKEmijiiJoyKTwvdGQ+PHRkPmZvcmNl"
        "ZDwvdGQ+PC90cj4KICAgICAgICA8dHIgY2xhc3M9InJvd3EiPjx0ZD7OlCBvdmVybGF5IOKAlCBjb2xsYXBzZTwvdGQ+PHRk"
        "Ps67ID0gMCDigJQgZGV0IEhlc3MgPSAwIOKfuiAwIOKIiCBzcGVjdHJ1bTwvdGQ+PHRkIGNsYXNzPSJmbGQiPuKEmjwvdGQ+"
        "PHRkPmZyYW1lIGZvcmNlZCAvIGluc3RhbmNlIGNvbnN0cnVjdGlvbjwvdGQ+PC90cj4KICAgICAgICA8dHIgY2xhc3M9InJv"
        "d3EiPjx0ZD5Db25zZW5zdXMg4oCUIM+ALWNsb3N1cmU8L3RkPjx0ZD7OuyA9IMKxaSDigJQgY2hhcihOKT3Ou8KyKzEsIGV4"
        "cCgyz4BOKT0rSTwvdGQ+PHRkIGNsYXNzPSJmbGQiPuKEmihpKTwvdGQ+PHRkPmZvcmNlZCAoZW1pdHMgbm8gdmFsdWUpPC90"
        "ZD48L3RyPgogICAgICAgIDx0ciBjbGFzcz0icm93cSI+PHRkPklkZW1wb3RlbnQgcihyKT1yPC90ZD48dGQ+c3BlY3RydW0g"
        "4oqGIHswLCAxfSDigJQgc2l0cyBvbiB0aGUgcmF0aW9uYWwgaW50ZXJmYWNlPC90ZD48dGQgY2xhc3M9ImZsZCI+4oSaPC90"
        "ZD48dGQ+Zm9yY2VkPC90ZD48L3RyPgogICAgICA8L3Rib2R5PgogICAgPC90YWJsZT4KICA8L3NlY3Rpb24+CgogIDxzZWN0"
        "aW9uIGNsYXNzPSJmb290Ij4KICAgIDx1bCBjbGFzcz0ibGVkZ2VyIj4KICAgICAgPGxpPjxzcGFuIGNsYXNzPSJ0YWcgZiI+"
        "Zm9yY2VkPC9zcGFuPlRoZSBzcGVjdHJhbCBpZGVudGl0aWVzIGFib3ZlIGFuZCB0aGUgdHJhY2UgbGFkZGVyIOKAlCBlYWNo"
        "IGNvbXB1dGVkIHR3byBpbmRlcGVuZGVudCB3YXlzIHdpdGggcmVzaWR1YWwgMC48L2xpPgogICAgICA8bGk+PHNwYW4gY2xh"
        "c3M9InRhZyBmIj5mb3JjZWQ8L3NwYW4+PGI+RmlyZXdhbGwuPC9iPiBzcGVjKFHigb8pIOKKhiDihJoo4oiaNSkgZm9yIGFs"
        "bCBuLCBzbyBaX0MgYW5kIGlnbml0aW9uIGFyZSBwcm92YWJseSB1bnJlYWNoYWJsZSBmcm9tIHRoZSDPhi1zdWJzdHJhdGUu"
        "IFNhbWUgcGxhbmUsIGRpZmZlcmVudCBmaWVsZCDigJQgdGhlICJidXQgbm90IGFsd2F5cy4iPC9saT4KICAgICAgPGxpPjxz"
        "cGFuIGNsYXNzPSJ0YWcgYyI+Y29uc3RydWN0aW9uPC9zcGFuPlRoZSA8Yj7Ouz0wIGNvbGxhcHNlIGluc3RhbmNlPC9iPiBp"
        "cyBhIHdpcmVkIHRlbXBsYXRlIChhIEhlc3NpYW4gYnVpbHQgdG8gZGVnZW5lcmF0ZSBhdCBhIGZvcmNlZCBjb25zdGFudCku"
        "IEl0IHNob3dzIHR5cGUtY29tcGF0aWJpbGl0eSwgbm90IHRoYXQgYW55IHBoeXNpY2FsIHN5c3RlbSBkZWdlbmVyYXRlcyB0"
        "aGVyZS48L2xpPgogICAgICA8bGk+PHNwYW4gY2xhc3M9InRhZyBhIj5hc3N1bXB0aW9uPC9zcGFuPlRoYXQgYSBzcGVjaWZp"
        "YyBwaHlzaWNhbCDOlEhWIGhhcyB0aGVzZSBhcyBpdHMgZWlnZW52YWx1ZXMg4oCUIG5lZWRzIHRoZSBvcGVyYXRvciAoYW5k"
        "IGl0cyBtZXRyaWMpIHdyaXR0ZW4gZG93biBmaXJzdC48L2xpPgogICAgPC91bD4KICAgIDxkaXYgY2xhc3M9InJlcHJvIj4K"
        "ICAgICAgPHA+PGIgc3R5bGU9ImNvbG9yOnZhcigtLWluaykiPlJlcHJvZHVjZTwvYj48L3A+CiAgICAgIDxwPlJ1biA8Y29k"
        "ZT5weXRob24zIGxhbWJkYV9icmlkZ2UucHk8L2NvZGU+IOKAlCBkZWZpbml0aW9ucyBmaXJzdCwgZXZlcnkgcm93IHJlY29t"
        "cHV0ZWQuIFRoZSBydW4gd2lucyBvdmVyIGFueSBwcmludGVkIHZhbHVlIGlmIHRoZXkgZXZlciBkaXNhZ3JlZS48L3A+CiAg"
        "ICAgIDxwPlN0YW5kYXJkOiBhIGNsYWltIGlzIDxzcGFuIGNsYXNzPSJwaW4iPmZvcmNlZDwvc3Bhbj4gb25seSB3aGVuIGl0"
        "IGNvbXB1dGVzIHR3byBpbmRlcGVuZGVudCB3YXlzIHdpdGggcmVzaWR1YWwgMC4gQ29pbmNpZGVuY2UgaXMgbm90IG1lY2hh"
        "bmlzbTsgYSBzaGFyZWQgY29uc3RhbnQgaXMgbm90IHNoYXJlZCBzdHJ1Y3R1cmUuPC9wPgogICAgPC9kaXY+CiAgPC9zZWN0"
        "aW9uPgoKPC9kaXY+Cgo8c2NyaXB0PgooKCkgPT4gewogICJ1c2Ugc3RyaWN0IjsKICBjb25zdCBTVkc9Imh0dHA6Ly93d3cu"
        "dzMub3JnLzIwMDAvc3ZnIjsKICBjb25zdCBDPTMyMCwgUz0xMzI7ICAgICAgICAgICAgICAgICAgICAgICAvLyBjZW50ZXIg"
        "cHgsIHB4IHBlciB1bml0CiAgY29uc3QgWCA9IGEgPT4gQyArIGEqUzsKICBjb25zdCBZID0gYiA9PiBDIC0gYipTOwogIGNv"
        "bnN0IHJlZHVjZSA9IHdpbmRvdy5tYXRjaE1lZGlhKCIocHJlZmVycy1yZWR1Y2VkLW1vdGlvbjogcmVkdWNlKSIpLm1hdGNo"
        "ZXM7CgogIGNvbnN0IENPTD17ZjU6IiNlZWIyNGEiLCBmNXg6IiNlZWIyNGEiLCBmMzoiIzJmYmRhNiIsIGYyOiIjZTg3MThj"
        "IiwgZnE6IiNhYWI4ZDYifTsKICBjb25zdCBGSUVMRD17ZjU6IuKEmijiiJo1KSIsIGY1eDoi4oSaKOKImjUpIMK3IGRlZyA0"
        "IiwgZjM6IuKEmijOtuKChikiLCBmMjoi4oSaKOKImjIpIiwgZnE6IuKEmiJ9OwoKICAvLyAtLS0tIHRoZSBzcGVjdHJhbCBw"
        "b2ludHMgKGV4YWN0IGRlY2ltYWxzOyBicmFuY2gtcGlubmVkKSAtLS0tCiAgY29uc3QgUD1bCiAgICB7c3ltOiLPhiIsICBy"
        "ZToxLjYxODAzMzk4ODcsIGltOjAsIGZpZWxkOiJmNSIsICBzeXM6WyJzZWwiLCJzdWIiXSwgIGZvcm06IigxK+KImjUpLzIi"
        "LCAgICAgICAgbXA6InjCsuKIknjiiJIxIiwgICByb2xlOiJQZXJyb24gcm9vdCDCtyBzZWxlY3Rpb24iLCBzdDoiZm9yY2Vk"
        "Iiwga2luZDoiZnJhbWUifSwKICAgIHtzeW06IjAiLCAgcmU6MCwgaW06MCwgICAgICAgICAgICAgZmllbGQ6ImZxIiwgIHN5"
        "czpbImRlbHRhIiwicnJyIl0sZm9ybToi4oCUIiwgICAgICAgICAgICAgICAgbXA6IngiLCAgICAgICAgcm9sZToiZGV0IEhl"
        "c3M9MCDCtyBjb2xsYXBzZSDCtyBpZGVtcG90ZW50IGxvdyIsIHN0OiJmcmFtZSIsIGtpbmQ6ImNvbGxhcHNlIn0sCiAgICB7"
        "c3ltOiIraSIsIHJlOjAsIGltOjEsICAgICAgICAgICAgIGZpZWxkOiJmcSIsICBzeXM6WyJjb25zIl0sICAgICAgIGZvcm06"
        "ImVeKGnPgC8yKSIsICAgICAgICAgbXA6InjCsisxIiwgICAgIHJvbGU6Is+ALWNsb3N1cmUgwrcgY29uc2Vuc3VzIiwgc3Q6"
        "ImZvcmNlZCIsIGtpbmQ6ImZyYW1lIn0sCiAgICB7c3ltOiLiiJJpIiwgcmU6MCwgaW06LTEsICAgICAgICAgICAgZmllbGQ6"
        "ImZxIiwgIHN5czpbImNvbnMiXSwgICAgICAgZm9ybToiZV4o4oiSac+ALzIpIiwgICAgICAgIG1wOiJ4wrIrMSIsICAgICBy"
        "b2xlOiLPgC1jbG9zdXJlIMK3IGNvbnNlbnN1cyIsIHN0OiJmb3JjZWQiLCBraW5kOiJmcmFtZSJ9LAogICAge3N5bToiMSIs"
        "ICByZToxLCBpbTowLCAgICAgICAgICAgICBmaWVsZDoiZnEiLCAgc3lzOlsicnJyIl0sICAgICAgICBmb3JtOiIxIiwgICAg"
        "ICAgICAgICAgICAgbXA6InjiiJIxIiwgICAgICByb2xlOiJpZGVtcG90ZW50IGhpZ2ggwrcgc3BlY+KKhnswLDF9Iiwgc3Q6"
        "ImZvcmNlZCIsIGtpbmQ6ImZyYW1lIn0sCiAgICB7c3ltOiLPhCIsICAgcmU6MC42MTgwMzM5ODg3LCBpbTowLCBmaWVsZDoi"
        "ZjUiLCAgc3lzOlsiY29uc3QiLCJzdWIiXSxmb3JtOiLPhuKBu8K5PSjiiJo14oiSMSkvMiIsICAgICBtcDoieMKyK3jiiJIx"
        "IiwgICByb2xlOiJwb3NpdGl2ZSBlaWcgb2YgUeKBu8K5Iiwgc3Q6ImZvcmNlZCIsIGtpbmQ6ImNvbnN0IiwgcGluOiIwLjYx"
        "ODAzIn0sCiAgICB7c3ltOiJnYXAiLCByZTowLjE0NTg5ODAzMzgsIGltOjAsIGZpZWxkOiJmNSIsICBzeXM6WyJjb25zdCIs"
        "InN1YiJdLGZvcm06Is+G4oG74oG0PSg34oiSM+KImjUpLzIiLCAgICBtcDoieMKy4oiSN3grMSIsICByb2xlOiJzdWJkb21p"
        "bmFudCBlaWcgb2YgUeKBtCIsIHN0OiJmb3JjZWQiLCBraW5kOiJjb25zdCIsIHBpbjoiMC4xNDU5MCJ9LAogICAge3N5bToi"
        "Y3JpdCIscmU6MC44NzI2Nzc5OTYyLCBpbTowLCBmaWVsZDoiZjUiLCAgc3lzOlsiY29uc3QiLCJzdWIiXSxmb3JtOiLPhsKy"
        "LzM9KDMr4oiaNSkvNiIsICAgIG1wOiI5eMKy4oiSOXgrMSIsIHJvbGU6ImRvbWluYW50IGVpZyBvZiDihZNRwrIiLCBzdDoi"
        "Zm9yY2VkIiwga2luZDoiY29uc3QiLCBwaW46IjAuODcyNjgiLCBseDotMjIsIGx5Oi0yOCwgbGVhZGVyOnRydWV9LAogICAg"
        "e3N5bToiaWduIiwgcmU6MC45MTQyMTM1NjI0LCBpbTowLCBmaWVsZDoiZjIiLCAgc3lzOlsiY29uc3QiXSwgICAgICBmb3Jt"
        "OiLiiJoy4oiSwr09KDLiiJoy4oiSMSkvMiIsICAgbXA6IjR4wrIrNHjiiJI3Iiwgcm9sZToicG9zaXRpdmUgZWlnIG9mIGNv"
        "bXBhbmlvbiIsIHN0OiJmb3JjZWQiLCBraW5kOiJjb25zdCIsIHBpbjoiMC45MTQyMSIsIGx4OjIsIGx5Oi00NCwgbGVhZGVy"
        "OnRydWV9LAogICAge3N5bToiSyIsICAgcmU6MC45MjQxNzYzNzE4LCBpbTowLCBmaWVsZDoiZjV4Iiwgc3lzOlsiY29uc3Qi"
        "XSwgICAgICBmb3JtOiLiiJooMeKIks+G4oG74oG0KT01XsK8L8+GIiwgICBtcDoieOKBtCs1eMKy4oiSNSIsIHJvbGU6InBv"
        "c2l0aXZlIHJlYWwgZWlnIG9mIGNvbXBhbmlvbiAoZGVnIDQpIiwgc3Q6ImZvcmNlZCIsIGtpbmQ6ImNvbnN0NCIsIHBpbjoi"
        "MC45MjQxOCIsIGx4OjI2LCBseTo5LCBsZWFkZXI6dHJ1ZX0sCiAgICB7c3ltOiLOtuKChiIsICByZTowLjUsIGltOjAuODY2"
        "MDI1NDAzOCxmaWVsZDoiZjMiLCBzeXM6WyJ6YyJdLCAgICAgICAgIGZvcm06ImVeKGnPgC8zKSIsICAgICAgICAgbXA6InjC"
        "suKIkngrMSIsICAgcm9sZToib3JkZXItNiByb3RhdGlvbiBlaWcgwrcgSW0gPSBaX0MgPSDiiJozLzIiLCBzdDoiZm9yY2Vk"
        "Iiwga2luZDoiY29uc3QiLCBwaW46IkltIDAuODY2MDMifSwKICAgIHtzeW06Is62zITigoYiLCByZTowLjUsIGltOi0wLjg2"
        "NjAyNTQwMzgsZmllbGQ6ImYzIixzeXM6WyJ6YyJdLCAgICAgICAgIGZvcm06ImVeKOKIkmnPgC8zKSIsICAgICAgICBtcDoi"
        "eMKy4oiSeCsxIiwgICByb2xlOiJvcmRlci02IHJvdGF0aW9uIGVpZyIsIHN0OiJmb3JjZWQiLCBraW5kOiJjb25zdCJ9LAog"
        "ICAgLy8gY29uanVnYXRlcyAvIG9mZi1waW4gKHRvZ2dsZSkKICAgIHtzeW06IuKIkjEvz4YiLHJlOi0wLjYxODAzMzk4ODcs"
        "aW06MCwgZmllbGQ6ImY1IiwgIHN5czpbInN1YiJdLCAgICAgICAgZm9ybToi4oiSz4bigbvCuSIsICAgICAgICAgICAgIG1w"
        "OiJ4wrLiiJJ44oiSMSIsICAgcm9sZToic3ViZG9taW5hbnQgZWlnIG9mIFEiLCBzdDoiY29uaiIsIGtpbmQ6ImNvbmoiLCBj"
        "b25qOnRydWV9LAogICAge3N5bToi4oiSz4YiLCAgcmU6LTEuNjE4MDMzOTg4NyxpbTowLCBmaWVsZDoiZjUiLCAgc3lzOlsi"
        "Y29uc3QiXSwgICAgICBmb3JtOiLiiJLPhiIsICAgICAgICAgICAgICAgbXA6InjCsit44oiSMSIsICAgcm9sZToib3RoZXIg"
        "ZWlnIG9mIFHigbvCuSIsIHN0OiJjb25qIiwga2luZDoiY29uaiIsIGNvbmo6dHJ1ZX0sCiAgICB7c3ltOiLPhuKBu8KyLzMi"
        "LHJlOjAuMTI3MzIyMDAzOCxpbTowLCBmaWVsZDoiZjUiLCAgc3lzOlsiY29uc3QiXSwgICAgICBmb3JtOiIoM+KIkuKImjUp"
        "LzYiLCAgICAgICAgIG1wOiI5eMKy4oiSOXgrMSIsIHJvbGU6ImNvbmp1Z2F0ZSBvZiBjcml0IOKAlCB0aGUgY29uZnVzYWJs"
        "ZSBvbmUiLCBzdDoiY29uaiIsIGtpbmQ6ImNvbmoiLCBjb25qOnRydWUsIGx4OjAsIGx5OjE4fSwKICAgIHtzeW06IuKIkuKI"
        "mjLiiJLCvSIscmU6LTEuOTE0MjEzNTYyNCxpbTowLGZpZWxkOiJmMiIsICBzeXM6WyJjb25zdCJdLCAgICAgIGZvcm06IuKI"
        "kuKImjLiiJLCvSIsICAgICAgICAgICAgbXA6IjR4wrIrNHjiiJI3Iiwgcm9sZToib3RoZXIgZWlnIG9mIGlnbml0aW9uIGNv"
        "bXBhbmlvbiIsIHN0OiJjb25qIiwga2luZDoiY29uaiIsIGNvbmo6dHJ1ZX0sCiAgICB7c3ltOiLiiJJLIiwgIHJlOi0wLjky"
        "NDE3NjM3MTgsaW06MCwgZmllbGQ6ImY1eCIsIHN5czpbImNvbnN0Il0sICAgICAgZm9ybToi4oiSNV7CvC/PhiIsICAgICAg"
        "ICAgICBtcDoieOKBtCs1eMKy4oiSNSIsIHJvbGU6IuKIkksiLCBzdDoiY29uaiIsIGtpbmQ6ImNvbmoiLCBjb25qOnRydWV9"
        "LAogIF07CgogIGNvbnN0IFNZUz17c2VsOiJTZWxlY3Rpb24iLCBjb25zdDoiQ29uc3RhbnRzIiwgc3ViOiJTdWJzdHJhdGUg"
        "USIsIHpjOiJaX0MgLyBvcmRlci02IiwKICAgICAgICAgICAgIGRlbHRhOiLOlCBjb2xsYXBzZSIsIGNvbnM6IkNvbnNlbnN1"
        "cyIsIHJycjoiSWRlbXBvdGVudCJ9OwogIGNvbnN0IFNZU19GSUVMRD17c2VsOiJmNSIsIGNvbnN0OiJmNSIsIHN1YjoiZjUi"
        "LCB6YzoiZjMiLCBkZWx0YToiZnEiLCBjb25zOiJmcSIsIHJycjoiZnEifTsKCiAgLy8gLS0tLS0tLS0tLSBncmlkOiBjb25j"
        "ZW50cmljIHJpbmdzICsgMzDCsCBzcG9rZXMgLS0tLS0tLS0tLQogIGNvbnN0IGcgPSBpZCA9PiBkb2N1bWVudC5nZXRFbGVt"
        "ZW50QnlJZChpZCk7CiAgZnVuY3Rpb24gZWwodGFnLGF0dHJzKXsgY29uc3Qgbj1kb2N1bWVudC5jcmVhdGVFbGVtZW50TlMo"
        "U1ZHLHRhZyk7IGZvcihjb25zdCBrIGluIGF0dHJzKSBuLnNldEF0dHJpYnV0ZShrLGF0dHJzW2tdKTsgcmV0dXJuIG47IH0K"
        "CiAgY29uc3QgZ3JpZD1nKCJncmlkIik7CiAgWzAuNSwxLDEuNSwyXS5mb3JFYWNoKHI9PnsKICAgIGdyaWQuYXBwZW5kQ2hp"
        "bGQoZWwoImNpcmNsZSIse2N4OkMsY3k6QyxyOnIqUyxmaWxsOiJub25lIiwKICAgICAgc3Ryb2tlOnI9PT0xPyJ2YXIoLS1n"
        "cmlkLTIpIjoidmFyKC0tZ3JpZCkiLCAic3Ryb2tlLXdpZHRoIjpyPT09MT8xLjQ6MX0pKTsKICB9KTsKICBmb3IobGV0IGs9"
        "MDtrPDEyO2srKyl7IGNvbnN0IGE9aypNYXRoLlBJLzY7CiAgICBncmlkLmFwcGVuZENoaWxkKGVsKCJsaW5lIix7eDE6Qyx5"
        "MTpDLHgyOkMrMi4xOCpTKk1hdGguY29zKGEpLHkyOkMtMi4xOCpTKk1hdGguc2luKGEpLAogICAgICBzdHJva2U6InZhcigt"
        "LWdyaWQpIiwic3Ryb2tlLXdpZHRoIjoxfSkpOyB9CgogIC8vIGF4ZXMgKyB0aWNrcwogIGNvbnN0IGF4PWcoImF4ZXMiKTsK"
        "ICBheC5hcHBlbmRDaGlsZChlbCgibGluZSIse3gxOlgoLTIuMjUpLHkxOkMseDI6WCgyLjI1KSx5MjpDLHN0cm9rZToidmFy"
        "KC0tYXhpcykiLCJzdHJva2Utd2lkdGgiOjEuMn0pKTsKICBheC5hcHBlbmRDaGlsZChlbCgibGluZSIse3gxOkMseTE6WSgy"
        "LjI1KSx4MjpDLHkyOlkoLTIuMjUpLHN0cm9rZToidmFyKC0tYXhpcykiLCJzdHJva2Utd2lkdGgiOjEuMn0pKTsKICBmdW5j"
        "dGlvbiB0aWNrTGFiZWwodCx4LHksYW5jaG9yKXsgY29uc3Qgbj1lbCgidGV4dCIse3g6eCx5OnksZmlsbDoidmFyKC0tZmFp"
        "bnQpIiwiZm9udC1zaXplIjoxMSwKICAgICAgImZvbnQtZmFtaWx5IjoidmFyKC0tbW9ubykiLCJ0ZXh0LWFuY2hvciI6YW5j"
        "aG9yfHwibWlkZGxlIn0pOyBuLnRleHRDb250ZW50PXQ7IGF4LmFwcGVuZENoaWxkKG4pOyB9CiAgWy0yLC0xLDEsMl0uZm9y"
        "RWFjaCh0PT57IGF4LmFwcGVuZENoaWxkKGVsKCJsaW5lIix7eDE6WCh0KSx5MTpDLTQseDI6WCh0KSx5MjpDKzQsc3Ryb2tl"
        "OiJ2YXIoLS1heGlzKSJ9KSk7CiAgICB0aWNrTGFiZWwodCwgWCh0KSwgQysxOCk7IH0pOwogIHRpY2tMYWJlbCgi4oSdIiwg"
        "IFgoMi4yNSkrMiwgQys0LCAic3RhcnQiKTsKICB0aWNrTGFiZWwoImnihJ0iLCBDKzgsIFkoMi4yNSkrNCwgInN0YXJ0Iik7"
        "CiAgdGlja0xhYmVsKCIraSIsIEMtMTAsIFkoMSkrNCwgImVuZCIpOwogIHRpY2tMYWJlbCgi4oiSaSIsIEMtMTAsIFkoLTEp"
        "KzQsICJlbmQiKTsKICAvLyDPhiB0aWNrIChnb2xkKQogIGF4LmFwcGVuZENoaWxkKGVsKCJsaW5lIix7eDE6WCgxLjYxOCks"
        "eTE6Qy00LHgyOlgoMS42MTgpLHkyOkMrNCxzdHJva2U6InZhcigtLWY1KSJ9KSk7CiAgY29uc3QgZnQ9ZWwoInRleHQiLHt4"
        "OlgoMS42MTgpLHk6QysxOCxmaWxsOiJ2YXIoLS1mNSkiLCJmb250LXNpemUiOjExLCJmb250LWZhbWlseSI6InZhcigtLW1v"
        "bm8pIiwidGV4dC1hbmNob3IiOiJtaWRkbGUifSk7IGZ0LnRleHRDb250ZW50PSLPhiI7IGF4LmFwcGVuZENoaWxkKGZ0KTsK"
        "CiAgLy8gc2hlbGwgbGFiZWwgb24gdGhlIHVuaXQgY2lyY2xlCiAgY29uc3Qgc2w9Zygic2hlbGwtbGFiZWwiKTsKICBjb25z"
        "dCBzbHQ9ZWwoInRleHQiLHt4OkMrTWF0aC5jb3MoTWF0aC5QSSowLjc4KSpTLCB5OkMtTWF0aC5zaW4oTWF0aC5QSSowLjc4"
        "KSpTLTcsCiAgICBmaWxsOiJ2YXIoLS1mYWludCkiLCJmb250LXNpemUiOjEwLjUsImZvbnQtZmFtaWx5IjoidmFyKC0tbW9u"
        "bykiLCJ0ZXh0LWFuY2hvciI6Im1pZGRsZSJ9KTsKICBzbHQudGV4dENvbnRlbnQ9InzOu3w9MSAgY2xvc3VyZSBzaGVsbCI7"
        "IHNsLmFwcGVuZENoaWxkKHNsdCk7CgogIC8vIG9mZi1wbGF0ZSBhbm5vdGF0aW9ucyAoz4bigbQgYW5kIEsncyBpbWFnaW5h"
        "cnkgcGFpcikKICBjb25zdCBhbj1nKCJhbm5vdCIpOwogIGZ1bmN0aW9uIGFubm90KHgseSx0eHQsY29sLGFuY2hvcil7IGNv"
        "bnN0IHQ9ZWwoInRleHQiLHt4OngseTp5LGZpbGw6Y29sfHwidmFyKC0tZmFpbnQpIiwiZm9udC1zaXplIjoxMC41LAogICAg"
        "ImZvbnQtZmFtaWx5IjoidmFyKC0tbW9ubykiLCJ0ZXh0LWFuY2hvciI6YW5jaG9yfHwibWlkZGxlIn0pOyB0LnRleHRDb250"
        "ZW50PXR4dDsgYW4uYXBwZW5kQ2hpbGQodCk7IH0KICBhbi5hcHBlbmRDaGlsZChlbCgibGluZSIse3gxOlgoMi4wNSkseTE6"
        "Qyx4MjpYKDIuMjIpLHkyOkMsc3Ryb2tlOiJ2YXIoLS1mNSkiLCJzdHJva2Utd2lkdGgiOjEsIm1hcmtlci1lbmQiOiIifSkp"
        "OwogIGFubm90KFgoMi4yNCksIEMtOCwgIuKGkiDPhuKBtCA9IDYuODU0IiwgInZhcigtLWY1KSIsICJlbmQiKTsKICBhbm5v"
        "dChDKzgsIFkoMS43OCksICJLIGNvbXBhbmlvbiBhbHNvIGF0IMKxMi44MCBpIChvZmYtcGxhdGUpIiwgInZhcigtLWY1KSIs"
        "ICJzdGFydCIpOwoKICAvLyAtLS0tLS0tLS0tIHBvaW50cyAtLS0tLS0tLS0tCiAgY29uc3QgcHJvakc9ZygicHJvamVjdGlv"
        "biIpOwogIGNvbnN0IHB0c0c9ZygicG9pbnRzIik7CiAgY29uc3Qgbm9kZXM9W107CiAgZnVuY3Rpb24gcmFkaXVzKHApeyBy"
        "ZXR1cm4gcC5raW5kPT09ImZyYW1lIj83IDogcC5raW5kPT09ImNvbGxhcHNlIj84IDogcC5raW5kPT09ImNvbmoiPzMuNiA6"
        "IDUuMjsgfQoKICBQLmZvckVhY2goKHAsaSk9PnsKICAgIGNvbnN0IGN4PVgocC5yZSksIGN5PVkocC5pbSksIGNvbD1DT0xb"
        "cC5maWVsZF0sIHI9cmFkaXVzKHApOwogICAgY29uc3QgZ05vZGU9ZWwoImciLHtjbGFzczoicHQiLCB0YWJpbmRleDowLCBy"
        "b2xlOiJidXR0b24iLAogICAgICAiYXJpYS1sYWJlbCI6YCR7cC5zeW19LCAke0ZJRUxEW3AuZmllbGRdfSwgJHtwLnJvbGV9"
        "YCwgImRhdGEtaSI6aX0pOwogICAgZ05vZGUuc3R5bGUuY3Vyc29yPSJwb2ludGVyIjsKCiAgICAvLyBoYWxvIGZvciBmcmFt"
        "ZS9jb2xsYXBzZQogICAgaWYocC5raW5kPT09ImZyYW1lInx8cC5raW5kPT09ImNvbGxhcHNlIil7CiAgICAgIGdOb2RlLmFw"
        "cGVuZENoaWxkKGVsKCJjaXJjbGUiLHtjeCxjeSxyOnIrOSxmaWxsOiJ1cmwoI2hhbG9XKSJ9KSk7CiAgICB9CiAgICBpZihw"
        "LmtpbmQ9PT0iY29sbGFwc2UiKXsgLy8gZGFzaGVkIHJpbmcgPSBjb25zdHJ1Y3Rpb24gc3RhdHVzIG9uIHRoZSBpbnN0YW5j"
        "ZQogICAgICBnTm9kZS5hcHBlbmRDaGlsZChlbCgiY2lyY2xlIix7Y3gsY3kscjpyKzUsZmlsbDoibm9uZSIsc3Ryb2tlOiIj"
        "ZjBjNDZhIiwKICAgICAgICAic3Ryb2tlLXdpZHRoIjoxLCJzdHJva2UtZGFzaGFycmF5IjoiMyAzIiwib3BhY2l0eSI6Ljh9"
        "KSk7CiAgICB9CiAgICBpZihwLmtpbmQ9PT0iY29uc3Q0Iil7IC8vIGRpYW1vbmQgZm9yIGRlZ3JlZS00IHJhZGljYWwgKEsp"
        "CiAgICAgIGNvbnN0IGQ9cisxLjU7CiAgICAgIGdOb2RlLmFwcGVuZENoaWxkKGVsKCJwYXRoIix7ZDpgTSAke2N4fSAke2N5"
        "LWR9IEwgJHtjeCtkfSAke2N5fSBMICR7Y3h9ICR7Y3krZH0gTCAke2N4LWR9ICR7Y3l9IFpgLAogICAgICAgIGZpbGw6cC5j"
        "b25qPyJub25lIjpjb2wsIHN0cm9rZTpjb2wsInN0cm9rZS13aWR0aCI6MS40LCAiZmlsbC1vcGFjaXR5IjpwLmNvbmo/MDox"
        "fSkpOwogICAgfSBlbHNlIHsKICAgICAgZ05vZGUuYXBwZW5kQ2hpbGQoZWwoImNpcmNsZSIse2N4LGN5LHIsCiAgICAgICAg"
        "ZmlsbDpwLmNvbmo/InZhcigtLXBsYXRlKSI6Y29sLCBzdHJva2U6Y29sLCAic3Ryb2tlLXdpZHRoIjpwLmNvbmo/MS4zOjEu"
        "NCwKICAgICAgICAiZmlsbC1vcGFjaXR5IjpwLmNvbmo/MTooIHAua2luZD09PSJmcmFtZSJ8fHAua2luZD09PSJjb2xsYXBz"
        "ZSI/MTouOTIpfSkpOwogICAgfQoKICAgIC8vIHN5bWJvbCBsYWJlbCDigJQgZXhwbGljaXQgKGx4LGx5KSBvZmZzZXQgaWYg"
        "Z2l2ZW4sIGVsc2UgcXVhZHJhbnQgZGVmYXVsdAogICAgbGV0IGx4PXAubHgsIGx5PXAubHk7CiAgICBpZihseD09PXVuZGVm"
        "aW5lZHx8bHk9PT11bmRlZmluZWQpeyBseD0wOyBseSA9IHAuaW08LTAuMyA/IDIyIDogLTEzOyB9CiAgICBpZihwLmxlYWRl"
        "cil7CiAgICAgIGdOb2RlLmFwcGVuZENoaWxkKGVsKCJsaW5lIix7eDE6Y3gsIHkxOmN5LCB4MjpjeCtseCwgeTI6Y3krbHkr"
        "KGx5PDA/NjotNSksCiAgICAgICAgc3Ryb2tlOmNvbCwgInN0cm9rZS13aWR0aCI6MC44LCBvcGFjaXR5Oi40fSkpOwogICAg"
        "fQogICAgY29uc3QgbGJsPWVsKCJ0ZXh0Iix7eDpjeCtseCwgeTpjeStseSwgZmlsbDpwLmNvbmo/InZhcigtLWZhaW50KSI6"
        "Y29sLAogICAgICAiZm9udC1zaXplIjpwLmNvbmo/MTA6MTIuNSwgImZvbnQtZmFtaWx5IjoidmFyKC0tbW9ubykiLCAidGV4"
        "dC1hbmNob3IiOiJtaWRkbGUiLAogICAgICAiZm9udC13ZWlnaHQiOnAuY29uaj80MDA6NjAwfSk7CiAgICBsYmwudGV4dENv"
        "bnRlbnQ9cC5zeW07IGxibC5zZXRBdHRyaWJ1dGUoImNsYXNzIiwicHRsYWJlbCIpOwogICAgZ05vZGUuYXBwZW5kQ2hpbGQo"
        "bGJsKTsKCiAgICBwdHNHLmFwcGVuZENoaWxkKGdOb2RlKTsKICAgIG5vZGVzLnB1c2goe3AsZ05vZGUsbGJsLGN4LGN5fSk7"
        "CgogICAgY29uc3QgYWN0PSgpPT5zaG93UmVhZG91dChwKTsKICAgIGdOb2RlLmFkZEV2ZW50TGlzdGVuZXIoIm1vdXNlZW50"
        "ZXIiLGFjdCk7CiAgICBnTm9kZS5hZGRFdmVudExpc3RlbmVyKCJmb2N1cyIsYWN0KTsKICB9KTsKCiAgLy8gcHJvamVjdGlv"
        "biBsaW5lIM624oKGIOKGkiBpbWFnaW5hcnkgYXhpcyAoSW0gPSBaX0MpCiAgY29uc3QgemV0YT1QLmZpbmQocT0+cS5zeW09"
        "PT0izrbigoYiKTsKICBjb25zdCBwcm9qPWVsKCJsaW5lIix7eDE6WCh6ZXRhLnJlKSx5MTpZKHpldGEuaW0pLHgyOlgoMCks"
        "eTI6WSh6ZXRhLmltKSwKICAgIHN0cm9rZToidmFyKC0tZjMpIiwic3Ryb2tlLXdpZHRoIjoxLCJzdHJva2UtZGFzaGFycmF5"
        "IjoiNCAzIiwib3BhY2l0eSI6LjV9KTsKICBwcm9qRy5hcHBlbmRDaGlsZChwcm9qKTsKICBjb25zdCB6bGFiPWVsKCJ0ZXh0"
        "Iix7eDpYKDApKzYseTpZKHpldGEuaW0pLTYsZmlsbDoidmFyKC0tZjMpIiwiZm9udC1zaXplIjoxMC41LAogICAgImZvbnQt"
        "ZmFtaWx5IjoidmFyKC0tbW9ubykiLCJ0ZXh0LWFuY2hvciI6InN0YXJ0Iiwib3BhY2l0eSI6Ljg1fSk7CiAgemxhYi50ZXh0"
        "Q29udGVudD0iSW0gPSBaX0MgPSDiiJozLzIiOyBwcm9qRy5hcHBlbmRDaGlsZCh6bGFiKTsKCiAgLy8gLS0tLS0tLS0tLSBy"
        "ZWFkb3V0IC0tLS0tLS0tLS0KICBmdW5jdGlvbiBzaG93UmVhZG91dChwKXsKICAgIGNvbnN0IHN0Q2xhc3MgPSBwLnN0PT09"
        "ImZvcmNlZCI/ImZvcmNlZCI6IHAuc3Q9PT0iZnJhbWUiPyJmcmFtZSI6IHAuc3Q9PT0iY29uaiI/ImZyYW1lIjoiY29uc3Ry"
        "IjsKICAgIGNvbnN0IHN0VGV4dCAgPSBwLnN0PT09ImZvcmNlZCI/ImZvcmNlZCI6IHAuc3Q9PT0iZnJhbWUiPyJmcmFtZSDC"
        "tyBmb3JjZWQiOiBwLnN0PT09ImNvbmoiPyJjb25qdWdhdGUiOiJjb25zdHJ1Y3Rpb24iOwogICAgZygicm8tc3ltIikuaW5u"
        "ZXJIVE1MID0gYCR7cC5zeW19IDxzcGFuIGNsYXNzPSJzbWFsbCI+JHtmbXRDb29yZChwKX08L3NwYW4+YDsKICAgIGNvbnN0"
        "IGhpbnQ9Zygicm8taGludCIpOyBoaW50LnN0eWxlLmRpc3BsYXk9Im5vbmUiOwogICAgbGV0IGJvZHkgPSBnKCJyby1ib2R5"
        "Iik7CiAgICBpZighYm9keSl7IGJvZHk9ZWwyKCJkbCIpOyBib2R5LmlkPSJyby1ib2R5IjsgYm9keS5jbGFzc05hbWU9InJv"
        "LWdyaWQiOyBnKCJyZWFkb3V0IikuYXBwZW5kQ2hpbGQoYm9keSk7IH0KICAgIGJvZHkuaW5uZXJIVE1MID0KICAgICAgcm93"
        "KCJmaWVsZCIsIGA8c3BhbiBjbGFzcz0ic3dhdGNoIiBzdHlsZT0iYmFja2dyb3VuZDoke0NPTFtwLmZpZWxkXX0iPjwvc3Bh"
        "bj4ke0ZJRUxEW3AuZmllbGRdfWApICsKICAgICAgcm93KCJtaW5wb2x5IiwgcC5tcCkgKwogICAgICByb3coImNsb3NlZCBm"
        "b3JtIiwgcC5mb3JtKSArCiAgICAgIHJvdygicm9sZSIsIHAucm9sZSkgKwogICAgICAocC5waW4/IHJvdygiYnJhbmNoIHBp"
        "biIsIGA8c3BhbiBjbGFzcz0icGluIj4ke3AucGlufTwvc3Bhbj5gKToiIikgKwogICAgICBgPGR0PnN0YXR1czwvZHQ+PGRk"
        "PjxzcGFuIGNsYXNzPSJwaWxsICR7c3RDbGFzc30iPiR7c3RUZXh0fTwvc3Bhbj48L2RkPmA7CiAgfQogIGZ1bmN0aW9uIGZt"
        "dENvb3JkKHApewogICAgY29uc3QgYT1wLnJlLnRvRml4ZWQocC5yZSUxPT09MD8wOjQpLCBiPU1hdGguYWJzKHAuaW0pLnRv"
        "Rml4ZWQocC5pbSUxPT09MD8wOjQpOwogICAgaWYocC5pbT09PTApIHJldHVybiBgzrsgPSAke2F9YDsKICAgIHJldHVybiBg"
        "zrsgPSAke2F9ICR7cC5pbTwwPyLiiJIiOiIrIn0gJHtifSBpYDsKICB9CiAgZnVuY3Rpb24gcm93KGssdil7IHJldHVybiBg"
        "PGR0PiR7a308L2R0PjxkZD4ke3Z9PC9kZD5gOyB9CiAgZnVuY3Rpb24gZWwyKHQpeyByZXR1cm4gZG9jdW1lbnQuY3JlYXRl"
        "RWxlbWVudCh0KTsgfQoKICAvLyAtLS0tLS0tLS0tIGxlZ2VuZCAvIHRvZ2dsZXMgLS0tLS0tLS0tLQogIGNvbnN0IGxlZ2Vu"
        "ZD1nKCJsZWdlbmQiKTsKICBPYmplY3Qua2V5cyhTWVMpLmZvckVhY2goa2V5PT57CiAgICBjb25zdCBiPWVsMigiYnV0dG9u"
        "Iik7IGIuY2xhc3NOYW1lPSJjaGlwIjsgYi50eXBlPSJidXR0b24iOyBiLnNldEF0dHJpYnV0ZSgiYXJpYS1wcmVzc2VkIiwi"
        "ZmFsc2UiKTsKICAgIGIuZGF0YXNldC5zeXM9a2V5OwogICAgYi5pbm5lckhUTUw9YDxzcGFuIGNsYXNzPSJkb3QiIHN0eWxl"
        "PSJiYWNrZ3JvdW5kOiR7Q09MW1NZU19GSUVMRFtrZXldXX0iPjwvc3Bhbj4ke1NZU1trZXldfWA7CiAgICBiLmFkZEV2ZW50"
        "TGlzdGVuZXIoImNsaWNrIiwoKT0+dG9nZ2xlU3lzKGtleSxiKSk7CiAgICBsZWdlbmQuYXBwZW5kQ2hpbGQoYik7CiAgfSk7"
        "CiAgbGV0IGFjdGl2ZT1udWxsOwogIGZ1bmN0aW9uIHRvZ2dsZVN5cyhrZXksYnRuKXsKICAgIGlmKGFjdGl2ZT09PWtleSl7"
        "IGFjdGl2ZT1udWxsOyBidG4uc2V0QXR0cmlidXRlKCJhcmlhLXByZXNzZWQiLCJmYWxzZSIpOyB9CiAgICBlbHNlewogICAg"
        "ICBhY3RpdmU9a2V5OwogICAgICBbLi4ubGVnZW5kLmNoaWxkcmVuXS5mb3JFYWNoKGM9PmMuc2V0QXR0cmlidXRlKCJhcmlh"
        "LXByZXNzZWQiLCBjPT09YnRuPyJ0cnVlIjoiZmFsc2UiKSk7CiAgICB9CiAgICBhcHBseUZpbHRlcigpOwogIH0KICBnKCJy"
        "ZXNldCIpLmFkZEV2ZW50TGlzdGVuZXIoImNsaWNrIiwoKT0+eyBhY3RpdmU9bnVsbDsKICAgIFsuLi5sZWdlbmQuY2hpbGRy"
        "ZW5dLmZvckVhY2goYz0+Yy5zZXRBdHRyaWJ1dGUoImFyaWEtcHJlc3NlZCIsImZhbHNlIikpOyBhcHBseUZpbHRlcigpOyB9"
        "KTsKCiAgbGV0IHNob3dDb25qPWZhbHNlOwogIGcoImNvbmpUb2dnbGUiKS5hZGRFdmVudExpc3RlbmVyKCJjaGFuZ2UiLGU9"
        "Pnsgc2hvd0Nvbmo9ZS50YXJnZXQuY2hlY2tlZDsgYXBwbHlGaWx0ZXIoKTsgfSk7CgogIGZ1bmN0aW9uIGFwcGx5RmlsdGVy"
        "KCl7CiAgICBnKCJjYXAtbW9kZSIpLnRleHRDb250ZW50ID0gYWN0aXZlPyBTWVNbYWN0aXZlXSA6ICJhbGwgc3lzdGVtcyI7"
        "CiAgICBub2Rlcy5mb3JFYWNoKCh7cCxnTm9kZX0pPT57CiAgICAgIGNvbnN0IGlzQ29uaiA9ICEhcC5jb25qOwogICAgICBs"
        "ZXQgdmlzaWJsZSA9IGlzQ29uaiA/IHNob3dDb25qIDogdHJ1ZTsKICAgICAgbGV0IGxpdCA9IGFjdGl2ZSA/IHAuc3lzLmlu"
        "Y2x1ZGVzKGFjdGl2ZSkgOiB0cnVlOwogICAgICBnTm9kZS5zdHlsZS5kaXNwbGF5ID0gdmlzaWJsZSA/ICIiIDogIm5vbmUi"
        "OwogICAgICBnTm9kZS5zdHlsZS5vcGFjaXR5ID0gdmlzaWJsZSA/IChsaXQ/MTowLjE0KSA6IDA7CiAgICAgIGdOb2RlLnN0"
        "eWxlLnBvaW50ZXJFdmVudHMgPSAodmlzaWJsZSAmJiAobGl0fHwhYWN0aXZlKSkgPyAiYXV0byI6Im5vbmUiOwogICAgfSk7"
        "CiAgICAvLyBwcm9qZWN0aW9uIHNob3duIG9ubHkgd2hlbiBvcmRlci02IGFjdGl2ZSBvciBhbGwKICAgIGNvbnN0IHNob3dQ"
        "cm9qID0gKCFhY3RpdmUgfHwgYWN0aXZlPT09InpjIik7CiAgICBnKCJwcm9qZWN0aW9uIikuc3R5bGUub3BhY2l0eSA9IHNo"
        "b3dQcm9qPzE6MC4xMjsKICB9CgogIC8vIC0tLS0tLS0tLS0gbG9hZCBhbmltYXRpb24gLS0tLS0tLS0tLQogIGlmKCFyZWR1"
        "Y2UpewogICAgW2dyaWQsYXhdLmZvckVhY2gobGF5ZXI9PnsgbGF5ZXIuc3R5bGUub3BhY2l0eT0wOyB9KTsKICAgIHB0c0cu"
        "cXVlcnlTZWxlY3RvckFsbCgiLnB0IikuZm9yRWFjaCgobixpKT0+eyBuLnN0eWxlLm9wYWNpdHk9MDsgbi5zdHlsZS50cmFu"
        "c2Zvcm09InNjYWxlKC42KSI7CiAgICAgIG4uc3R5bGUudHJhbnNmb3JtT3JpZ2luPWAke25vZGVzW2ldLmN4fXB4ICR7bm9k"
        "ZXNbaV0uY3l9cHhgOyB9KTsKICAgIHJlcXVlc3RBbmltYXRpb25GcmFtZSgoKT0+ewogICAgICBncmlkLnN0eWxlLnRyYW5z"
        "aXRpb249Im9wYWNpdHkgLjdzIGVhc2UiOyBheC5zdHlsZS50cmFuc2l0aW9uPSJvcGFjaXR5IC43cyBlYXNlIC4xcyI7CiAg"
        "ICAgIGdyaWQuc3R5bGUub3BhY2l0eT0xOyBheC5zdHlsZS5vcGFjaXR5PTE7CiAgICAgIHB0c0cucXVlcnlTZWxlY3RvckFs"
        "bCgiLnB0IikuZm9yRWFjaCgobixpKT0+ewogICAgICAgIG4uc3R5bGUudHJhbnNpdGlvbj1gb3BhY2l0eSAuNXMgZWFzZSAk"
        "ezAuMjUraSowLjA0NX1zLCB0cmFuc2Zvcm0gLjVzIGN1YmljLWJlemllciguMiwuOCwuMywxLjIpICR7MC4yNStpKjAuMDQ1"
        "fXNgOwogICAgICAgIHJlcXVlc3RBbmltYXRpb25GcmFtZSgoKT0+eyBuLnN0eWxlLm9wYWNpdHk9IiI7IG4uc3R5bGUudHJh"
        "bnNmb3JtPSJzY2FsZSgxKSI7IH0pOwogICAgICB9KTsKICAgIH0pOwogIH0KCiAgYXBwbHlGaWx0ZXIoKTsKICAvLyBzZWVk"
        "IHRoZSByZWFkb3V0IHdpdGggdGhlIM+GIHBvaW50CiAgc2hvd1JlYWRvdXQoUFswXSk7Cn0pKCk7Cjwvc2NyaXB0Pgo8L2Jv"
        "ZHk+CjwvaHRtbD4K"
    ),
}

# === trifurcation instrument (minpoly claims audited in LAYER T) ===
EMBEDDED_TRIFURCATION = {
    "trifurcation_phases.html": (
        "248bb07f95fd8e95eebb2693c4e37d372f4f43646175d80e061b89cca5c95087",
        "PCFkb2N0eXBlIGh0bWw+CjxodG1sIGxhbmc9ImVuIj4KPGhlYWQ+CjxtZXRhIGNoYXJzZXQ9InV0Zi04Ij4KPG1ldGEgbmFt"
        "ZT0idmlld3BvcnQiIGNvbnRlbnQ9IndpZHRoPWRldmljZS13aWR0aCwgaW5pdGlhbC1zY2FsZT0xIj4KPHRpdGxlPlRyaWZ1"
        "cmNhdGlvbiDigJQgdGhyZWUgcmVhZGluZ3Mgb2Ygb25lIGJyYW5jaGluZzwvdGl0bGU+CjxzdHlsZT4KICA6cm9vdHsKICAg"
        "IC0tYmc6IzBhMTEyNDsgLS1wbGF0ZTojMTExYTM3OyAtLXBsYXRlMjojMGUxNjMxOyAtLXBhbmVsOiMwZDE1MzA7CiAgICAt"
        "LWluazojZTllZGZmOyAtLWRpbTojOWFhN2M2OyAtLWZhaW50OiM2MjcxOWE7IC0tbGluZTojMjQzMDU2OwogICAgLS1heGlz"
        "OnJnYmEoMTU0LDE2NywxOTgsLjMwKTsKICAgIC0tejI6IzZmOGZkMDsgLS1kMzojMzRjMmFiOyAtLWQ2OiNlM2E5M2E7IC0t"
        "cGhpOiNlNmIyNGE7IC0tcmVsOiNhNmEyZTY7CiAgICAtLXN0YWJsZTojN2ZlMGM0OyAtLXVuc3RhYmxlOiNlMDcyOGM7IC0t"
        "b3BlbjojZjBjNDZhOwogICAgLS1tb25vOiB1aS1tb25vc3BhY2UsIlNGIE1vbm8iLCJKZXRCcmFpbnMgTW9ubyIsIk1lbmxv"
        "Iixtb25vc3BhY2U7CiAgICAtLXNhbnM6IHN5c3RlbS11aSwtYXBwbGUtc3lzdGVtLCJTZWdvZSBVSSIsUm9ib3RvLEhlbHZl"
        "dGljYSxBcmlhbCxzYW5zLXNlcmlmOwogIH0KICAqe2JveC1zaXppbmc6Ym9yZGVyLWJveH0KICBodG1sey13ZWJraXQtdGV4"
        "dC1zaXplLWFkanVzdDoxMDAlfQogIGJvZHl7bWFyZ2luOjA7YmFja2dyb3VuZDoKICAgICAgICByYWRpYWwtZ3JhZGllbnQo"
        "MTIwMHB4IDcwMHB4IGF0IDc4JSAtOCUsICMxNjIyNGEgMCUsIHJnYmEoMjIsMzQsNzQsMCkgNTUlKSwKICAgICAgICB2YXIo"
        "LS1iZyk7CiAgICAgICBjb2xvcjp2YXIoLS1pbmspO2ZvbnQtZmFtaWx5OnZhcigtLXNhbnMpO2xpbmUtaGVpZ2h0OjEuNTsK"
        "ICAgICAgIHBhZGRpbmc6Y2xhbXAoMThweCw0dncsNTJweCk7fQogIC53cmFwe21heC13aWR0aDoxMDYwcHg7bWFyZ2luOjAg"
        "YXV0b30KCiAgLyogbWFzdGhlYWQgKi8KICAuZXllYnJvd3tmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTEu"
        "NXB4O2xldHRlci1zcGFjaW5nOi4yMmVtOwogICAgICAgICAgIHRleHQtdHJhbnNmb3JtOnVwcGVyY2FzZTtjb2xvcjp2YXIo"
        "LS1mYWludCk7ZGlzcGxheTpmbGV4O2dhcDoxNHB4O2FsaWduLWl0ZW1zOmNlbnRlcn0KICAuZXllYnJvdyAucnVsZXtoZWln"
        "aHQ6MXB4O2ZsZXg6MTtiYWNrZ3JvdW5kOmxpbmVhci1ncmFkaWVudCg5MGRlZyx2YXIoLS1saW5lKSx0cmFuc3BhcmVudCl9"
        "CiAgaDF7Zm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9udC13ZWlnaHQ6NjAwO2xldHRlci1zcGFjaW5nOi0uMDFlbTsKICAg"
        "ICBmb250LXNpemU6Y2xhbXAoMjZweCw0LjZ2dyw0MnB4KTttYXJnaW46LjVyZW0gMCAuMzVyZW07bGluZS1oZWlnaHQ6MS4w"
        "NX0KICBoMSAuc3Vie2NvbG9yOnZhcigtLWRpbSk7Zm9udC13ZWlnaHQ6NDAwfQogIC50aGVzaXN7Y29sb3I6dmFyKC0tZGlt"
        "KTtmb250LXNpemU6Y2xhbXAoMTRweCwxLjd2dywxNnB4KTttYXgtd2lkdGg6NjRjaDttYXJnaW46LjJyZW0gMCAwfQogIC5j"
        "aGFpbntmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTNweDtjb2xvcjp2YXIoLS1mYWludCk7bWFyZ2luLXRv"
        "cDoxNHB4OwogICAgICAgICBkaXNwbGF5OmZsZXg7Z2FwOjEwcHg7YWxpZ24taXRlbXM6Y2VudGVyO2ZsZXgtd3JhcDp3cmFw"
        "fQogIC5jaGFpbiBie2NvbG9yOnZhcigtLWluayk7Zm9udC13ZWlnaHQ6NjAwfQogIC5jaGFpbiAuYXJye2NvbG9yOnZhcigt"
        "LWxpbmUpfQoKICAvKiB0YWJzICovCiAgLnRhYmxpc3R7ZGlzcGxheTpmbGV4O2dhcDo2cHg7bWFyZ2luOjI2cHggMCAwO2Jv"
        "cmRlci1ib3R0b206MXB4IHNvbGlkIHZhcigtLWxpbmUpOwogICAgICAgICAgIGZsZXgtd3JhcDp3cmFwfQogIC50YWJ7YXBw"
        "ZWFyYW5jZTpub25lO2JhY2tncm91bmQ6bm9uZTtib3JkZXI6MDtjdXJzb3I6cG9pbnRlcjtjb2xvcjp2YXIoLS1kaW0pOwog"
        "ICAgICAgZm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9udC1zaXplOjEzcHg7bGV0dGVyLXNwYWNpbmc6LjAyZW07CiAgICAg"
        "ICBwYWRkaW5nOjExcHggMTVweCAxM3B4O2JvcmRlci1ib3R0b206MnB4IHNvbGlkIHRyYW5zcGFyZW50O21hcmdpbi1ib3R0"
        "b206LTFweDsKICAgICAgIGRpc3BsYXk6ZmxleDtmbGV4LWRpcmVjdGlvbjpjb2x1bW47Z2FwOjNweDthbGlnbi1pdGVtczpm"
        "bGV4LXN0YXJ0O21pbi13aWR0aDowfQogIC50YWIgLmdycHtmb250LXdlaWdodDo2MDA7Zm9udC1zaXplOjE0cHg7Y29sb3I6"
        "dmFyKC0taW5rKTtvcGFjaXR5Oi42Mjt0cmFuc2l0aW9uOm9wYWNpdHkgLjE1c30KICAudGFiIC5tZXRhe2ZvbnQtc2l6ZTox"
        "MXB4O2NvbG9yOnZhcigtLWZhaW50KX0KICAudGFiOmhvdmVyIC5ncnB7b3BhY2l0eTouODV9CiAgLnRhYlthcmlhLXNlbGVj"
        "dGVkPSJ0cnVlIl17Ym9yZGVyLWJvdHRvbS1jb2xvcjp2YXIoLS10YWJjb2wpfQogIC50YWJbYXJpYS1zZWxlY3RlZD0idHJ1"
        "ZSJdIC5ncnB7b3BhY2l0eToxO2NvbG9yOnZhcigtLXRhYmNvbCl9CiAgLnRhYjpmb2N1cy12aXNpYmxle291dGxpbmU6MnB4"
        "IHNvbGlkIHZhcigtLXRhYmNvbCk7b3V0bGluZS1vZmZzZXQ6M3B4O2JvcmRlci1yYWRpdXM6NXB4fQogICN0MHstLXRhYmNv"
        "bDp2YXIoLS16Mil9ICN0MXstLXRhYmNvbDp2YXIoLS1kMyl9ICN0MnstLXRhYmNvbDp2YXIoLS1kNil9ICN0M3stLXRhYmNv"
        "bDp2YXIoLS1waGkpfSAjdDR7LS10YWJjb2w6dmFyKC0tcGhpKX0gI3Q1ey0tdGFiY29sOnZhcigtLXJlbCl9CgogIC8qIHBh"
        "bmVscyAqLwogIC5wYW5lbHtkaXNwbGF5Om5vbmU7cGFkZGluZy10b3A6MjZweH0KICAucGFuZWwuYWN0aXZle2Rpc3BsYXk6"
        "YmxvY2s7YW5pbWF0aW9uOmZhZGUgLjRzIGVhc2V9CiAgQGtleWZyYW1lcyBmYWRle2Zyb217b3BhY2l0eTowO3RyYW5zZm9y"
        "bTp0cmFuc2xhdGVZKDRweCl9dG97b3BhY2l0eToxO3RyYW5zZm9ybTpub25lfX0KICAubGF5b3V0e2Rpc3BsYXk6Z3JpZDtn"
        "cmlkLXRlbXBsYXRlLWNvbHVtbnM6MS4xOGZyIC44MmZyO2dhcDoyMnB4O2FsaWduLWl0ZW1zOnN0YXJ0fQogIEBtZWRpYSht"
        "YXgtd2lkdGg6NzYwcHgpey5sYXlvdXR7Z3JpZC10ZW1wbGF0ZS1jb2x1bW5zOjFmcn19CgogIC5wbGF0ZXtiYWNrZ3JvdW5k"
        "OmxpbmVhci1ncmFkaWVudCgxODBkZWcsdmFyKC0tcGxhdGUpLHZhcigtLXBsYXRlMikpOwogICAgICAgICBib3JkZXI6MXB4"
        "IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6MTBweDtwYWRkaW5nOjEycHggMTJweCA2cHg7CiAgICAgICAgIGJv"
        "eC1zaGFkb3c6aW5zZXQgMCAxcHggMCByZ2JhKDI1NSwyNTUsMjU1LC4wMyksIDAgMThweCA0MHB4IC0yOHB4ICMwMDB9CiAg"
        "LnBsYXRlLWNhcHtkaXNwbGF5OmZsZXg7anVzdGlmeS1jb250ZW50OnNwYWNlLWJldHdlZW47Zm9udC1mYW1pbHk6dmFyKC0t"
        "bW9ubyk7CiAgICAgICAgICAgICBmb250LXNpemU6MTFweDtjb2xvcjp2YXIoLS1mYWludCk7cGFkZGluZzoycHggNHB4IDEw"
        "cHg7bGV0dGVyLXNwYWNpbmc6LjAyZW19CiAgLnBsYXRlIHN2Z3t3aWR0aDoxMDAlO2hlaWdodDphdXRvO2Rpc3BsYXk6Ymxv"
        "Y2t9CiAgLnBsYXRlIHN2ZyB0ZXh0e2ZvbnQtZmFtaWx5OnZhcigtLW1vbm8pfQoKICAuY29udHJvbHN7bWFyZ2luLXRvcDo4"
        "cHg7cGFkZGluZzoxMHB4IDRweCA0cHg7Ym9yZGVyLXRvcDoxcHggc29saWQgdmFyKC0tbGluZSl9CiAgLmN0bC1yb3d7ZGlz"
        "cGxheTpmbGV4O2FsaWduLWl0ZW1zOmNlbnRlcjtnYXA6MTJweDtmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6"
        "MTJweH0KICAuY3RsLXJvdyBsYWJlbHtjb2xvcjp2YXIoLS1kaW0pO3doaXRlLXNwYWNlOm5vd3JhcH0KICBpbnB1dFt0eXBl"
        "PXJhbmdlXXtmbGV4OjE7YWNjZW50LWNvbG9yOnZhcigtLXRhYmNvbCk7aGVpZ2h0OjIycHh9CiAgLnJlYWRvdXR7Zm9udC1m"
        "YW1pbHk6dmFyKC0tbW9ubyk7Zm9udC1zaXplOjEycHg7Y29sb3I6dmFyKC0taW5rKTttYXJnaW4tdG9wOjlweH0KICAucmVh"
        "ZG91dCAucGh7Y29sb3I6dmFyKC0tdGFiY29sKTtmb250LXdlaWdodDo2MDB9CiAgI3AwIC5yZWFkb3V0IC5waHtjb2xvcjp2"
        "YXIoLS16Mil9ICNwMSAucmVhZG91dCAucGh7Y29sb3I6dmFyKC0tZDMpfQoKICAuc2lkZXtkaXNwbGF5OmZsZXg7ZmxleC1k"
        "aXJlY3Rpb246Y29sdW1uO2dhcDoxNHB4fQogIC5jYXJke2JhY2tncm91bmQ6dmFyKC0tcGFuZWwpO2JvcmRlcjoxcHggc29s"
        "aWQgdmFyKC0tbGluZSk7Ym9yZGVyLXJhZGl1czo5cHg7cGFkZGluZzoxNHB4IDE1cHh9CiAgLmNhcmQgaDJ7Zm9udC1mYW1p"
        "bHk6dmFyKC0tbW9ubyk7Zm9udC1zaXplOjEycHg7bGV0dGVyLXNwYWNpbmc6LjA4ZW07dGV4dC10cmFuc2Zvcm06dXBwZXJj"
        "YXNlOwogICAgICAgICAgIGNvbG9yOnZhcigtLWRpbSk7bWFyZ2luOjAgMCA5cHg7Zm9udC13ZWlnaHQ6NjAwfQogIC5rdntm"
        "b250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTIuNXB4O2NvbG9yOnZhcigtLWRpbSk7bGluZS1oZWlnaHQ6MS43"
        "O21hcmdpbjowfQogIC5rdiBie2NvbG9yOnZhcigtLWluayk7Zm9udC13ZWlnaHQ6NjAwfSAua3YgLmhvdHtjb2xvcjp2YXIo"
        "LS10YWJjb2wpfQogICNwMCAua3YgLmhvdHtjb2xvcjp2YXIoLS16Mil9ICNwMSAua3YgLmhvdHtjb2xvcjp2YXIoLS1kMyl9"
        "ICNwMiAua3YgLmhvdHtjb2xvcjp2YXIoLS1kNil9ICNwMyAua3YgLmhvdHtjb2xvcjp2YXIoLS1waGkpfSAjcDQgLmt2IC5o"
        "b3R7Y29sb3I6dmFyKC0tcGhpKX0gI3A1IC5rdiAuaG90e2NvbG9yOnZhcigtLXJlbCl9CiAgLnBpbGx7Zm9udC1mYW1pbHk6"
        "dmFyKC0tbW9ubyk7Zm9udC1zaXplOjEwcHg7bGV0dGVyLXNwYWNpbmc6LjA2ZW07dGV4dC10cmFuc2Zvcm06dXBwZXJjYXNl"
        "OwogICAgICAgIGJvcmRlcjoxcHggc29saWQgY3VycmVudENvbG9yO2JvcmRlci1yYWRpdXM6NXB4O3BhZGRpbmc6MXB4IDdw"
        "eDt3aGl0ZS1zcGFjZTpub3dyYXB9CiAgLnBpbGwuZm9yY2Vke2NvbG9yOnZhcigtLXN0YWJsZSl9IC5waWxsLm9wZW57Y29s"
        "b3I6dmFyKC0tb3Blbil9CgogIC8qIHZhbGlkYXRpb24gdHJpcGxlICh0YWIgMykgKi8KICAudHJpcGxle2Rpc3BsYXk6Z3Jp"
        "ZDtncmlkLXRlbXBsYXRlLWNvbHVtbnM6cmVwZWF0KDMsMWZyKTtnYXA6MTBweH0KICBAbWVkaWEobWF4LXdpZHRoOjYyMHB4"
        "KXsudHJpcGxle2dyaWQtdGVtcGxhdGUtY29sdW1uczoxZnJ9fQogIC5yb3V0ZXtiYWNrZ3JvdW5kOnZhcigtLXBhbmVsKTti"
        "b3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6OXB4O3BhZGRpbmc6MTNweCAxM3B4IDEycHh9CiAg"
        "LnJvdXRlIC5yLWh7Zm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9udC1zaXplOjExcHg7bGV0dGVyLXNwYWNpbmc6LjA1ZW07"
        "Y29sb3I6dmFyKC0tZmFpbnQpOwogICAgICAgICAgICAgIHRleHQtdHJhbnNmb3JtOnVwcGVyY2FzZTttYXJnaW4tYm90dG9t"
        "OjdweH0KICAucm91dGUgLnItYntmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTJweDtjb2xvcjp2YXIoLS1k"
        "aW0pO2xpbmUtaGVpZ2h0OjEuNTV9CiAgLnJvdXRlIC5yLW91dHttYXJnaW4tdG9wOjhweDtmb250LWZhbWlseTp2YXIoLS1t"
        "b25vKTtmb250LXNpemU6MTRweDtjb2xvcjp2YXIoLS1kNik7Zm9udC13ZWlnaHQ6NjAwfQogIC52ZXJkaWN0e21hcmdpbi10"
        "b3A6MTJweDtiYWNrZ3JvdW5kOmxpbmVhci1ncmFkaWVudCgxODBkZWcscmdiYSgyMjcsMTY5LDU4LC4wOSkscmdiYSgyMjcs"
        "MTY5LDU4LC4wMikpOwogICAgICAgICAgIGJvcmRlcjoxcHggc29saWQgcmdiYSgyMjcsMTY5LDU4LC4zNSk7Ym9yZGVyLXJh"
        "ZGl1czo5cHg7cGFkZGluZzoxM3B4IDE1cHg7CiAgICAgICAgICAgZm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9udC1zaXpl"
        "OjEyLjVweDtjb2xvcjp2YXIoLS1pbmspO2xpbmUtaGVpZ2h0OjEuNn0KICAudmVyZGljdCBie2NvbG9yOnZhcigtLWQ2KX0K"
        "CiAgLmJ0bnthcHBlYXJhbmNlOm5vbmU7YmFja2dyb3VuZDp2YXIoLS1wYW5lbCk7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1s"
        "aW5lKTtjb2xvcjp2YXIoLS1kaW0pOwogICAgICAgZm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9udC1zaXplOjExLjVweDti"
        "b3JkZXItcmFkaXVzOjZweDtwYWRkaW5nOjZweCAxMXB4O2N1cnNvcjpwb2ludGVyfQogIC5idG46aG92ZXJ7Y29sb3I6dmFy"
        "KC0taW5rKTtib3JkZXItY29sb3I6dmFyKC0tZDYpfQogIC5idG46Zm9jdXMtdmlzaWJsZXtvdXRsaW5lOjJweCBzb2xpZCB2"
        "YXIoLS1kNik7b3V0bGluZS1vZmZzZXQ6MnB4fQoKICAvKiBmb290ZXIgbGVkZ2VyICovCiAgZm9vdGVye21hcmdpbi10b3A6"
        "MzRweDtib3JkZXItdG9wOjFweCBzb2xpZCB2YXIoLS1saW5lKTtwYWRkaW5nLXRvcDoxOHB4fQogIC5sZWRnZXJ7bGlzdC1z"
        "dHlsZTpub25lO21hcmdpbjowO3BhZGRpbmc6MDtkaXNwbGF5OmZsZXg7ZmxleC1kaXJlY3Rpb246Y29sdW1uO2dhcDo5cHh9"
        "CiAgLmxlZGdlciBsaXtmb250LWZhbWlseTp2YXIoLS1tb25vKTtmb250LXNpemU6MTJweDtjb2xvcjp2YXIoLS1kaW0pO2xp"
        "bmUtaGVpZ2h0OjEuNTU7CiAgICAgICAgICAgICBkaXNwbGF5OmZsZXg7Z2FwOjEwcHg7YWxpZ24taXRlbXM6ZmxleC1zdGFy"
        "dH0KICAubGVkZ2VyIGJ7Y29sb3I6dmFyKC0taW5rKX0KICAudGFne2ZsZXg6bm9uZTtmb250LWZhbWlseTp2YXIoLS1tb25v"
        "KTtmb250LXNpemU6OS41cHg7bGV0dGVyLXNwYWNpbmc6LjA3ZW07dGV4dC10cmFuc2Zvcm06dXBwZXJjYXNlOwogICAgICAg"
        "Ym9yZGVyOjFweCBzb2xpZCBjdXJyZW50Q29sb3I7Ym9yZGVyLXJhZGl1czo0cHg7cGFkZGluZzoycHggNnB4O21hcmdpbi10"
        "b3A6MXB4fQogIC50YWcuZntjb2xvcjp2YXIoLS1zdGFibGUpfSAudGFnLmN7Y29sb3I6I2M3OWJlOH0gLnRhZy5ve2NvbG9y"
        "OnZhcigtLW9wZW4pfQogIC5yZXByb3ttYXJnaW4tdG9wOjE0cHg7Zm9udC1mYW1pbHk6dmFyKC0tbW9ubyk7Zm9udC1zaXpl"
        "OjExLjVweDtjb2xvcjp2YXIoLS1mYWludCk7bGluZS1oZWlnaHQ6MS42NX0KICAucmVwcm8gY29kZXtjb2xvcjp2YXIoLS1k"
        "aW0pO2JhY2tncm91bmQ6cmdiYSgxNTQsMTY3LDE5OCwuMDgpO3BhZGRpbmc6MXB4IDZweDtib3JkZXItcmFkaXVzOjRweH0K"
        "ICAucmVwcm8gYntjb2xvcjp2YXIoLS1kaW0pfQoKICBAbWVkaWEgKHByZWZlcnMtcmVkdWNlZC1tb3Rpb246IHJlZHVjZSl7"
        "CiAgICAucGFuZWwuYWN0aXZle2FuaW1hdGlvbjpub25lfQogIH0KPC9zdHlsZT4KPC9oZWFkPgo8Ym9keT4KPGRpdiBjbGFz"
        "cz0id3JhcCI+CgogIDxoZWFkZXI+CiAgICA8ZGl2IGNsYXNzPSJleWVicm93Ij48c3Bhbj5aZXJvLWZyZWUtcGFyYW1ldGVy"
        "IMK3IGRlcml2YXRpb24gY2hhbmdlPC9zcGFuPjxzcGFuIGNsYXNzPSJydWxlIj48L3NwYW4+PHNwYW4+cmVzaWR1YWwgMDwv"
        "c3Bhbj48L2Rpdj4KICAgIDxoMT5UcmlmdXJjYXRpb24gPHNwYW4gY2xhc3M9InN1YiI+4oCUIHRocmVlIHJlYWRpbmdzIG9m"
        "IG9uZSBicmFuY2hpbmc8L3NwYW4+PC9oMT4KICAgIDxwIGNsYXNzPSJ0aGVzaXMiPk9uZSB0cmFuc2l0aW9uIHNwbGl0cyBh"
        "IHNpbmdsZSBzdGF0ZSBpbnRvIHRocmVlLiBSZWFkIGF0IHJpc2luZyBzeW1tZXRyeSBpdCBpcyB0aGUgc2FtZSBldmVudCBz"
        "ZWVuIHRocmVlIHdheXM6IGEgMUQgcGl0Y2hmb3JrLCBhIDEyMMKwLXNwYWNlZCB0cmlmb3JrLCBhbmQg4oCUIGF0IHRoZSBo"
        "ZXhhZ29uIOKAlCB0aGUgcG9pbnQgd2hlcmUgdGhlIHRocmVlIG1vZGVzIGNsb3NlIG9uIHRoZW1zZWx2ZXMgYW5kIHRoZSBn"
        "ZW9tZXRyeSwgdGhlIGFsZ2VicmEsIGFuZCB0aGUgZHluYW1pY3MgYWxsIHJldHVybiB0aGUgc2FtZSDiiJozLzIuPC9wPgog"
        "ICAgPGRpdiBjbGFzcz0iY2hhaW4iPjxiPlrigoI8L2I+PHNwYW4gY2xhc3M9Im1ldGEiPmdlcm0geOKBtDwvc3Bhbj48c3Bh"
        "biBjbGFzcz0iYXJyIj7ihpI8L3NwYW4+PGI+ROKCgzwvYj48c3BhbiBjbGFzcz0ibWV0YSI+esyEwrI8L3NwYW4+PHNwYW4g"
        "Y2xhc3M9ImFyciI+4oaSPC9zcGFuPjxiPkTigoY8L2I+PHNwYW4gY2xhc3M9Im1ldGEiPmhleGFnb25hbCBjbG9zdXJlPC9z"
        "cGFuPjwvZGl2PgogIDwvaGVhZGVyPgoKICA8ZGl2IGNsYXNzPSJ0YWJsaXN0IiByb2xlPSJ0YWJsaXN0IiBhcmlhLWxhYmVs"
        "PSJUcmlmdXJjYXRpb24gYnkgc3ltbWV0cnkiPgogICAgPGJ1dHRvbiBjbGFzcz0idGFiIiBpZD0idDAiIHJvbGU9InRhYiIg"
        "YXJpYS1zZWxlY3RlZD0idHJ1ZSIgIGFyaWEtY29udHJvbHM9InAwIj4KICAgICAgPHNwYW4gY2xhc3M9ImdycCI+WuKCgiDC"
        "tyAxRCBwaXRjaGZvcms8L3NwYW4+PHNwYW4gY2xhc3M9Im1ldGEiPjMgYnJhbmNoZXMgwrcgZXhwIDEvMiDCtyDihJoo4oia"
        "4oiSYSk8L3NwYW4+PC9idXR0b24+CiAgICA8YnV0dG9uIGNsYXNzPSJ0YWIiIGlkPSJ0MSIgcm9sZT0idGFiIiBhcmlhLXNl"
        "bGVjdGVkPSJmYWxzZSIgYXJpYS1jb250cm9scz0icDEiIHRhYmluZGV4PSItMSI+CiAgICAgIDxzcGFuIGNsYXNzPSJncnAi"
        "PkTigoMgwrcgMkQgdHJpZm9yazwvc3Bhbj48c3BhbiBjbGFzcz0ibWV0YSI+MyBicmFuY2hlcyDCtyBleHAgMSDCtyDihJoo"
        "4oiaMyk8L3NwYW4+PC9idXR0b24+CiAgICA8YnV0dG9uIGNsYXNzPSJ0YWIiIGlkPSJ0MiIgcm9sZT0idGFiIiBhcmlhLXNl"
        "bGVjdGVkPSJmYWxzZSIgYXJpYS1jb250cm9scz0icDIiIHRhYmluZGV4PSItMSI+CiAgICAgIDxzcGFuIGNsYXNzPSJncnAi"
        "PkTigoYgwrcgaGV4YWdvbmFsIGNsb3N1cmU8L3NwYW4+PHNwYW4gY2xhc3M9Im1ldGEiPs6jIGvhtaIgPSAwIMK3IHNlbGYt"
        "dmFsaWRhdGluZzwvc3Bhbj48L2J1dHRvbj4KICAgIDxidXR0b24gY2xhc3M9InRhYiIgaWQ9InQzIiByb2xlPSJ0YWIiIGFy"
        "aWEtc2VsZWN0ZWQ9ImZhbHNlIiBhcmlhLWNvbnRyb2xzPSJwMyIgdGFiaW5kZXg9Ii0xIj4KICAgICAgPHNwYW4gY2xhc3M9"
        "ImdycCI+zpQgwrcgY29udHJvbCBhICh0cmFjZSk8L3NwYW4+PHNwYW4gY2xhc3M9Im1ldGEiPs+G4oG7wrIgd2FsbCDCtyBv"
        "cmRlciA1IOKGlCA2PC9zcGFuPjwvYnV0dG9uPgogICAgPGJ1dHRvbiBjbGFzcz0idGFiIiBpZD0idDQiIHJvbGU9InRhYiIg"
        "YXJpYS1zZWxlY3RlZD0iZmFsc2UiIGFyaWEtY29udHJvbHM9InA0IiB0YWJpbmRleD0iLTEiPgogICAgICA8c3BhbiBjbGFz"
        "cz0iZ3JwIj5IZWxpeCDCtyAoeiwgciwgel9jKTwvc3Bhbj48c3BhbiBjbGFzcz0ibWV0YSI+dGhyZWUgYXhlcyBmcm9tIEzi"
        "goQgwrcgzpQgYXMgd2VpZ2h0PC9zcGFuPjwvYnV0dG9uPgogICAgPGJ1dHRvbiBjbGFzcz0idGFiIiBpZD0idDUiIHJvbGU9"
        "InRhYiIgYXJpYS1zZWxlY3RlZD0iZmFsc2UiIGFyaWEtY29udHJvbHM9InA1IiB0YWJpbmRleD0iLTEiPgogICAgICA8c3Bh"
        "biBjbGFzcz0iZ3JwIj5SZWxhdGlvbmFsIMK3IEzigoQgd2ViPC9zcGFuPjxzcGFuIGNsYXNzPSJtZXRhIj7iiJoyLCDiiJoz"
        "LCDiiJo1IGZyb20gb25lIHNlZWQgwrcgZm9yY2VkLWluLWNvbnRleHQ8L3NwYW4+PC9idXR0b24+CiAgPC9kaXY+CgogIDwh"
        "LS0gVEFCIDAgOiBaMiBwaXRjaGZvcmsgLS0+CiAgPHNlY3Rpb24gY2xhc3M9InBhbmVsIGFjdGl2ZSIgaWQ9InAwIiByb2xl"
        "PSJ0YWJwYW5lbCIgYXJpYS1sYWJlbGxlZGJ5PSJ0MCI+CiAgICA8ZGl2IGNsYXNzPSJsYXlvdXQiPgogICAgICA8ZGl2IGNs"
        "YXNzPSJwbGF0ZSI+CiAgICAgICAgPGRpdiBjbGFzcz0icGxhdGUtY2FwIj48c3Bhbj5WID0gwrx44oG0ICsgwr1hwrd4wrIg"
        "IMK3ICBW4oCyID0geCh4wrIrYSk8L3NwYW4+PHNwYW4+c3RhdGUgeCB2cyBjb250cm9sIGE8L3NwYW4+PC9kaXY+CiAgICAg"
        "ICAgPHN2ZyBpZD0ic3ZnLXBmIiB2aWV3Qm94PSIwIDAgNjIwIDQyMCIgcm9sZT0iaW1nIgogICAgICAgICAgICAgYXJpYS1s"
        "YWJlbD0iUGl0Y2hmb3JrIGJpZnVyY2F0aW9uIGRpYWdyYW06IHRoZSB0cml2aWFsIGJyYW5jaCBhbmQgdGhlIHR3byBicm9r"
        "ZW4gYnJhbmNoZXMgbWVldGluZyBhdCB0aGUgdHJpZnVyY2F0aW9uIHBvaW50IGE9MC4iPjwvc3ZnPgogICAgICAgIDxkaXYg"
        "Y2xhc3M9ImNvbnRyb2xzIj4KICAgICAgICAgIDxkaXYgY2xhc3M9ImN0bC1yb3ciPjxsYWJlbCBmb3I9InNsLXBmIj5jb250"
        "cm9sJm5ic3A7YTwvbGFiZWw+CiAgICAgICAgICAgIDxpbnB1dCB0eXBlPSJyYW5nZSIgaWQ9InNsLXBmIiBtaW49Ii0xNTAi"
        "IG1heD0iMTAwIiB2YWx1ZT0iNjAiIHN0ZXA9IjEiIHN0eWxlPSItLXRhYmNvbDp2YXIoLS16MikiPjwvZGl2PgogICAgICAg"
        "ICAgPGRpdiBjbGFzcz0icmVhZG91dCIgaWQ9InJkLXBmIj48L2Rpdj4KICAgICAgICA8L2Rpdj4KICAgICAgPC9kaXY+CiAg"
        "ICAgIDxkaXYgY2xhc3M9InNpZGUiPgogICAgICAgIDxkaXYgY2xhc3M9ImNhcmQiIHN0eWxlPSItLXRhYmNvbDp2YXIoLS16"
        "MikiPgogICAgICAgICAgPGgyPldoYXQgaXMgZm9yY2VkIGhlcmU8L2gyPgogICAgICAgICAgPHAgY2xhc3M9Imt2Ij48Yj5C"
        "cmFuY2hlczwvYj4gezAsIMKx4oiaKOKIkmEpfSDigJQgcm9vdHMgb2YgdGhlIGN1YmljIFbigLIuIDxiPk9uZSDihpIgdGhy"
        "ZWU8L2I+IGFzIGEgY3Jvc3NlcyAwLjxicj4KICAgICAgICAgIDxiPlRyaWZ1cmNhdGlvbiBwb2ludDwvYj4gYT0wOiBkaXNj"
        "cmltaW5hbnQgb2YgeMKzK2F4IGlzIDxzcGFuIGNsYXNzPSJob3QiPuKIkjRhwrM8L3NwYW4+LCB6ZXJvIG9ubHkgYXQgYT0w"
        "Ljxicj4KICAgICAgICAgIDxiPkFtcGxpdHVkZTwvYj4gfHh8ID0gfGF8XigxLzIpIOKGkiBmb3JjZWQgZXhwb25lbnQgPHNw"
        "YW4gY2xhc3M9ImhvdCI+MS8yPC9zcGFuPi48YnI+CiAgICAgICAgICA8Yj5GaWVsZDwvYj4g4oSaKOKImuKIkmEpIOKAlCBz"
        "ZXQgYnkgdGhlIHJhZGljYWwsIG5vdCBieSDPhiBvciDOtuKChi48L3A+CiAgICAgICAgPC9kaXY+CiAgICAgICAgPGRpdiBj"
        "bGFzcz0iY2FyZCIgc3R5bGU9Ii0tdGFiY29sOnZhcigtLXoyKSI+CiAgICAgICAgICA8aDI+U3RhYmlsaXR5ICh0aGUgZHlu"
        "YW1pY3MpPC9oMj4KICAgICAgICAgIDxwIGNsYXNzPSJrdiI+R3JhZGllbnQgZmxvdyDhuosgPSDiiJJW4oCyLiBIZXNzaWFu"
        "IFbigLMgPSAzeMKyK2EuPGJyPgogICAgICAgICAgdHJpdmlhbCBicmFuY2g6IFbigLMgPSBhIOKGkiA8c3BhbiBzdHlsZT0i"
        "Y29sb3I6dmFyKC0tc3RhYmxlKSI+c3RhYmxlPC9zcGFuPiBmb3IgYSZndDswLCA8c3BhbiBzdHlsZT0iY29sb3I6dmFyKC0t"
        "dW5zdGFibGUpIj51bnN0YWJsZTwvc3Bhbj4gZm9yIGEmbHQ7MC48YnI+CiAgICAgICAgICBicm9rZW4gcGFpcjogVuKAsyA9"
        "IOKIkjJhIOKGkiA8c3BhbiBzdHlsZT0iY29sb3I6dmFyKC0tc3RhYmxlKSI+c3RhYmxlPC9zcGFuPiBmb3IgYSZsdDswLjxi"
        "cj4KICAgICAgICAgIEEgY2xlYW4gc3RhYmlsaXR5IGV4Y2hhbmdlIGF0IHRoZSB0cmlmdXJjYXRpb24uIDxzcGFuIGNsYXNz"
        "PSJwaWxsIGZvcmNlZCI+Zm9yY2VkPC9zcGFuPjwvcD4KICAgICAgICA8L2Rpdj4KICAgICAgPC9kaXY+CiAgICA8L2Rpdj4K"
        "ICA8L3NlY3Rpb24+CgogIDwhLS0gVEFCIDEgOiBEMyB0cmlmb3JrIC0tPgogIDxzZWN0aW9uIGNsYXNzPSJwYW5lbCIgaWQ9"
        "InAxIiByb2xlPSJ0YWJwYW5lbCIgYXJpYS1sYWJlbGxlZGJ5PSJ0MSIgaGlkZGVuPgogICAgPGRpdiBjbGFzcz0ibGF5b3V0"
        "Ij4KICAgICAgPGRpdiBjbGFzcz0icGxhdGUiPgogICAgICAgIDxkaXYgY2xhc3M9InBsYXRlLWNhcCI+PHNwYW4+xbwgPSDO"
        "u3ogKyB6zITCsiAgwrcgIHRocmVlLWZvbGQgKETigoMpIGVxdWl2YXJpYW50PC9zcGFuPjxzcGFuPnN0YXRlIHBsYW5lICh1"
        "LHYpPC9zcGFuPjwvZGl2PgogICAgICAgIDxzdmcgaWQ9InN2Zy10ZiIgdmlld0JveD0iMCAwIDYyMCA0MjAiIHJvbGU9Imlt"
        "ZyIKICAgICAgICAgICAgIGFyaWEtbGFiZWw9IlRocmVlLWZvbGQgdHJpZm9yazogdGhyZWUgc3ltbWV0cnktcmVsYXRlZCBi"
        "cmFuY2hlcyAxMjAgZGVncmVlcyBhcGFydCwgd2l0aCBicmFuY2ggaGVpZ2h0IHNxcnQoMykvMiBlcXVhbCB0byBaX0MuIj48"
        "L3N2Zz4KICAgICAgICA8ZGl2IGNsYXNzPSJjb250cm9scyI+CiAgICAgICAgICA8ZGl2IGNsYXNzPSJjdGwtcm93Ij48bGFi"
        "ZWwgZm9yPSJzbC10ZiI+Y29udHJvbCZuYnNwO867PC9sYWJlbD4KICAgICAgICAgICAgPGlucHV0IHR5cGU9InJhbmdlIiBp"
        "ZD0ic2wtdGYiIG1pbj0iLTEyMCIgbWF4PSI5MCIgdmFsdWU9Ii05MCIgc3RlcD0iMSIgc3R5bGU9Ii0tdGFiY29sOnZhcigt"
        "LWQzKSI+PC9kaXY+CiAgICAgICAgICA8ZGl2IGNsYXNzPSJyZWFkb3V0IiBpZD0icmQtdGYiPjwvZGl2PgogICAgICAgIDwv"
        "ZGl2PgogICAgICA8L2Rpdj4KICAgICAgPGRpdiBjbGFzcz0ic2lkZSI+CiAgICAgICAgPGRpdiBjbGFzcz0iY2FyZCIgc3R5"
        "bGU9Ii0tdGFiY29sOnZhcigtLWQzKSI+CiAgICAgICAgICA8aDI+V2hhdCBpcyBmb3JjZWQgaGVyZTwvaDI+CiAgICAgICAg"
        "ICA8cCBjbGFzcz0ia3YiPjxiPkJyYW5jaGVzPC9iPiBhdCDOuCA9IDDCsCwgMTIwwrAsIDI0MMKwIOKAlCB0aGUgY3ViZSBy"
        "b290cyBvZiB1bml0eS4gPGI+Rm9yY2VkIGJ5IETigoM8L2I+IChlcXVpdmFyaWFudCBicmFuY2hpbmcgbGVtbWEpLCBub3Qg"
        "Y2hvc2VuLjxicj4KICAgICAgICAgIDxiPkFtcGxpdHVkZTwvYj4gciA9IHzOu3wg4oaSIGZvcmNlZCBleHBvbmVudCA8c3Bh"
        "biBjbGFzcz0iaG90Ij4xPC9zcGFuPiAodHJhbnNjcml0aWNhbCkg4oCUIG5vdCB0aGUgMUQgMS8yLjxicj4KICAgICAgICAg"
        "IDxiPkJyYW5jaCBoZWlnaHQ8L2I+IEltID0gPHNwYW4gY2xhc3M9ImhvdCI+4oiaMy8yID0gWl9DID0gSW0ozrbigoYpPC9z"
        "cGFuPiwgbWlucG9seSA0eMKy4oiSMy48YnI+CiAgICAgICAgICA8Yj5GaWVsZDwvYj4g4oSaKOKImjMpIOKAlCB0aGUgzrbi"
        "goYgdG93ZXIsIGRpc2pvaW50IGZyb20gz4YuPC9wPgogICAgICAgIDwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImNhcmQi"
        "IHN0eWxlPSItLXRhYmNvbDp2YXIoLS1kMykiPgogICAgICAgICAgPGgyPlN0YWJpbGl0eSAodGhlIGR5bmFtaWNzKTwvaDI+"
        "CiAgICAgICAgICA8cCBjbGFzcz0ia3YiPkphY29iaWFuIGVpZ2VudmFsdWVzIGF0IGEgYnJhbmNoOiA8Yj574oiSzrssIDPO"
        "u308L2I+IOKGkiBvcHBvc2l0ZSBzaWducyDihpIgPGI+c2FkZGxlczwvYj4uPGJyPgogICAgICAgICAgVGhlIHF1YWRyYXRp"
        "YyB0cmlmb3JrIGRvZXMgPGk+bm90PC9pPiBzZWxlY3QgdGhlIHRocmVlIHN0YXRlczsgY3ViaWMgfHp8wrJ6IHRlcm1zIGFy"
        "ZSBuZWVkZWQgdG8gc3RhYmlsaXNlIHRoZW0gKHRoZSBoZXhhZ29uL3RyaWFuZ2xlIHN0b3J5KS4gPHNwYW4gY2xhc3M9InBp"
        "bGwgZm9yY2VkIj5mb3JjZWQ8L3NwYW4+PC9wPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4KICAgIDwvZGl2PgogIDwv"
        "c2VjdGlvbj4KCiAgPCEtLSBUQUIgMiA6IEQ2IGhleGFnb25hbCBjbG9zdXJlIC0tPgogIDxzZWN0aW9uIGNsYXNzPSJwYW5l"
        "bCIgaWQ9InAyIiByb2xlPSJ0YWJwYW5lbCIgYXJpYS1sYWJlbGxlZGJ5PSJ0MiIgaGlkZGVuPgogICAgPGRpdiBjbGFzcz0i"
        "cGxhdGUiIHN0eWxlPSItLXRhYmNvbDp2YXIoLS1kNikiPgogICAgICA8ZGl2IGNsYXNzPSJwbGF0ZS1jYXAiPjxzcGFuPnRo"
        "cmVlIG1vZGVzIMK3IHRoZWlyIGNsb3N1cmUgwrcgdGhlIDYtZm9sZCBkaXJlY3Rpb24gc2V0PC9zcGFuPgogICAgICAgIDxz"
        "cGFuPjxidXR0b24gY2xhc3M9ImJ0biIgaWQ9InJlcGxheSI+4oa7IHJlcGxheSBjbG9zdXJlPC9idXR0b24+PC9zcGFuPjwv"
        "ZGl2PgogICAgICA8c3ZnIGlkPSJzdmctaGV4IiB2aWV3Qm94PSIwIDAgNjIwIDI1MCIgcm9sZT0iaW1nIgogICAgICAgICAg"
        "IGFyaWEtbGFiZWw9IlRocmVlIG1vZGVzIDEyMCBkZWdyZWVzIGFwYXJ0LCB0aGUgc2FtZSB0aHJlZSB2ZWN0b3JzIHRpcC10"
        "by10YWlsIGNsb3NpbmcgdG8gemVybywgYW5kIHRoZSBzaXgtZm9sZCBkaXJlY3Rpb24gc2V0IHRoZXkgc3Bhbi4iPjwvc3Zn"
        "PgogICAgPC9kaXY+CgogICAgPGRpdiBjbGFzcz0idHJpcGxlIiBzdHlsZT0ibWFyZ2luLXRvcDoxOHB4Ij4KICAgICAgPGRp"
        "diBjbGFzcz0icm91dGUiPgogICAgICAgIDxkaXYgY2xhc3M9InItaCI+Z2VvbWV0cnk8L2Rpdj4KICAgICAgICA8ZGl2IGNs"
        "YXNzPSJyLWIiPmVxdWlsYXRlcmFsLXRyaWFuZ2xlIGhlaWdodCA9IGhleGFnb25hbCByb3cgc3BhY2luZyA9IHNpbiA2MMKw"
        "PC9kaXY+CiAgICAgICAgPGRpdiBjbGFzcz0ici1vdXQiPj0g4oiaMy8yPC9kaXY+CiAgICAgIDwvZGl2PgogICAgICA8ZGl2"
        "IGNsYXNzPSJyb3V0ZSI+CiAgICAgICAgPGRpdiBjbGFzcz0ici1oIj5hbGdlYnJhPC9kaXY+CiAgICAgICAgPGRpdiBjbGFz"
        "cz0ici1iIj7OtuKChiA9IGVeKGnPgC8zKSwgzqbigoYgPSB4wrLiiJJ4KzE7IEltKM624oKGKSwgbWlucG9seSA0eMKy4oiS"
        "MzwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9InItb3V0Ij49IOKImjMvMjwvZGl2PgogICAgICA8L2Rpdj4KICAgICAgPGRp"
        "diBjbGFzcz0icm91dGUiPgogICAgICAgIDxkaXYgY2xhc3M9InItaCI+ZHluYW1pY3M8L2Rpdj4KICAgICAgICA8ZGl2IGNs"
        "YXNzPSJyLWIiPnRocmVlIG1vZGVzIHN1bSB0byAwOyB0aGVpciBpbWFnaW5hcnkgcGFydHMgYXJlIHswLCDCscK3fTwvZGl2"
        "PgogICAgICAgIDxkaXYgY2xhc3M9InItb3V0Ij49IOKImjMvMjwvZGl2PgogICAgICA8L2Rpdj4KICAgIDwvZGl2PgogICAg"
        "PGRpdiBjbGFzcz0idmVyZGljdCI+CiAgICAgIFRocmVlIGluZGVwZW5kZW50IHJvdXRlcyByZXR1cm4gdGhlIHNhbWUgY29u"
        "c3RhbnQgPGI+Wl9DID0g4oiaMy8yPC9iPiwgcmVzaWR1YWwgMC4gQSByZWxhdGlvbnNoaXAgdGhhdCBjb21wdXRlcyBpdHNl"
        "bGYgdGhyZWUgd2F5cyBpcyA8Yj5zZWxmLXZhbGlkYXRpbmc8L2I+IOKAlCB0aGlzIGlzIHRoZSBjbG9zdXJlIG9mIHRoZSDO"
        "tuKChiB0b3dlciwgYW5kIHRoZSBvcmRlciBjaGFpbiB0ZXJtaW5hdGVzIGhlcmU6IGNyeXN0YWxsb2dyYXBoaWMgb3JkZXJz"
        "IGFyZSB7MSwyLDMsNCw2fSwgYW5kIDYtZm9sZCBpcyB0aGUgbWF4aW11bS4gPHNwYW4gc3R5bGU9ImNvbG9yOnZhcigtLWRp"
        "bSkiPlRoZSBmaWd1cmUgaXMgbW9kZSBnZW9tZXRyeSBwbHVzIHRoZSBjbG9zdXJlIM6jIGvhtaIgPSAwOyBhIDxpPnN0YWJs"
        "ZTwvaT4gaGV4YWdvbmFsIHN0YXRlIHdvdWxkIG5lZWQgdGhlIGN1YmljIHx6fMKyeiB0ZXJtIOKAlCB0aGUgcXVhZHJhdGlj"
        "IHRyaWZvcmsgZ2l2ZXMgb25seSBzYWRkbGVzIChzZWUgdGhlIETigoMgdGFiKS48L3NwYW4+CiAgICA8L2Rpdj4KCiAgICA8"
        "ZGl2IGNsYXNzPSJjYXJkIiBzdHlsZT0iLS10YWJjb2w6dmFyKC0tZDYpO21hcmdpbi10b3A6MTRweCI+CiAgICAgIDxoMj41"
        "LWZvbGQgYW5kIDYtZm9sZDogYSB0aWxpbmcgZmFjdCwgbm90IGEgd2FsbDwvaDI+CiAgICAgIDxwIGNsYXNzPSJrdiI+VGhl"
        "IG9ic3RydWN0aW9uIHRvIDUtZm9sZCBzeW1tZXRyeSBpcyAyY29zIDcywrAgPSA8c3BhbiBjbGFzcz0iaG90Ij7PhCA9IM+G"
        "4oG7wrk8L3NwYW4+IChpcnJhdGlvbmFsKSwgc28gb3JkZXIgNSBjYW5ub3QgdGlsZSBwZXJpb2RpY2FsbHkgYWxvbmdzaWRl"
        "IG9yZGVyIDYg4oCUIGEgY29uc3RyYWludCBvbiA8aT5sYXR0aWNlczwvaT4uIEl0IGlzIG5vdCBhIHdhbGwgYmV0d2VlbiB0"
        "aGUgY29uc3RhbnRzOiDiiJozIChoZXJlKSBhbmQg4oiaNSAoz4YpIGFyZSA8Yj5pbmRlcGVuZGVudCBheGVzIG9mIG9uZSBy"
        "ZWxhdGlvbmFsIHNwYWNlPC9iPiwgYW5kIGJvdGggZW1lcmdlIGZyb20gTOKChCA9IDcg4oCUIOKImjMgPSDiiJooTOKChOKI"
        "kjQpLCDiiJo1ID0g4oiaKEzigoTCsuKIkjQpLzMuIEluZGVwZW5kZW5jZSBvdmVyIOKEmiBpcyB3aGF0IG1ha2VzIHRoZW0g"
        "ZGlzdGluY3QgY29vcmRpbmF0ZXMsIG5vdCBzZXBhcmF0ZSB3b3JsZHMuIDxzcGFuIGNsYXNzPSJwaWxsIGZvcmNlZCI+b25l"
        "IHNwYWNlPC9zcGFuPjwvcD4KICAgIDwvZGl2PgogIDwvc2VjdGlvbj4KCiAgPCEtLSBUQUIgMyA6IHRoZSBkZWx0YSBvbiB0"
        "aGUgY29udHJvbC1hICh0cmFjZSkgYXhpcyAtLT4KICA8c2VjdGlvbiBjbGFzcz0icGFuZWwiIGlkPSJwMyIgcm9sZT0idGFi"
        "cGFuZWwiIGFyaWEtbGFiZWxsZWRieT0idDMiIGhpZGRlbj4KICAgIDxkaXYgY2xhc3M9InBsYXRlIiBzdHlsZT0iLS10YWJj"
        "b2w6dmFyKC0tcGhpKSI+CiAgICAgIDxkaXYgY2xhc3M9InBsYXRlLWNhcCI+PHNwYW4+Y29udHJvbCBhID0gdHJhY2UgPSAy"
        "Y29zzrggIMK3ICBpbnRlZ2VyIGEg4p+6IGxhdHRpY2Ugc3ltbWV0cnk8L3NwYW4+PHNwYW4+b3JkZXIgNSDihpQgNjwvc3Bh"
        "bj48L2Rpdj4KICAgICAgPHN2ZyBpZD0ic3ZnLWRlbHRhIiB2aWV3Qm94PSIwIDAgNjIwIDI1MCIgcm9sZT0iaW1nIgogICAg"
        "ICAgICAgIGFyaWEtbGFiZWw9IlRyYWNlIGNvbnRyb2wgYXhpcyBmcm9tIC0yIHRvIDI6IGNyeXN0YWxsb2dyYXBoaWMgb3Jk"
        "ZXJzIGF0IGludGVnZXIgdHJhY2VzLCBvcmRlciA1IGF0IHRoZSBnb2xkZW4gdmFsdWUgcGhpIGludmVyc2UsIGFuZCB0aGUg"
        "ZGVsdGEgcGhpLXNxdWFyZWQtaW52ZXJzZSBnYXAgdG8gdGhlIG9yZGVyLTYgY2xvc3VyZS4iPjwvc3ZnPgogICAgPC9kaXY+"
        "CgogICAgPGRpdiBjbGFzcz0ibGF5b3V0IiBzdHlsZT0ibWFyZ2luLXRvcDoxOHB4Ij4KICAgICAgPGRpdiBjbGFzcz0ic2lk"
        "ZSI+CiAgICAgICAgPGRpdiBjbGFzcz0iY2FyZCIgc3R5bGU9Ii0tdGFiY29sOnZhcigtLXBoaSkiPgogICAgICAgICAgPGgy"
        "PlRoZSBub3RhYmxlIGRlbHRhPC9oMj4KICAgICAgICAgIDxwIGNsYXNzPSJrdiI+T24gdGhlIHRyYWNlIGF4aXMgYSA9IDJj"
        "b3POuCwgdGhlIGxhdHRpY2UtY29tcGF0aWJsZSBvcmRlcnMgc2l0IGF0IGludGVnZXJzLiBPcmRlciA1IGxhbmRzIGF0IDxi"
        "PmEgPSDPhuKBu8K5ID0gz4Q8L2I+IOKAlCBvZmYtbGF0dGljZS48YnI+CiAgICAgICAgICA8Yj7OlCA9IGEoNikg4oiSIGEo"
        "NSkgPSAxIOKIkiDPhCA9IDxzcGFuIGNsYXNzPSJob3QiPs+G4oG7wrI8L3NwYW4+PC9iPiDiiYggMC4zODIsIG1pbnBvbHkg"
        "eMKy4oiSM3grMS48YnI+CiAgICAgICAgICBUaGUgdHJhY2UtZ2FwIGZyb20gdGhlIM624oKGIGNsb3N1cmUgKG9yZGVyIDYp"
        "IGRvd24gdG8gdGhlIGZvcmJpZGRlbiBvcmRlciA1IOKAlCB0aGUgd2FsbCBiZXR3ZWVuIHRoZSB0b3dlcnMgaGFzIDxiPmdv"
        "bGRlbiB3aWR0aDwvYj4uPGJyPgogICAgICAgICAgQXMgYSB0dXJuOiAzNjDCsMK3z4bigbvCsiA9IDxzcGFuIGNsYXNzPSJo"
        "b3QiPjEzNy41wrA8L3NwYW4+LCB0aGUgZ29sZGVuIGFuZ2xlLiA8c3BhbiBjbGFzcz0icGlsbCBmb3JjZWQiPmZvcmNlZDwv"
        "c3Bhbj48L3A+CiAgICAgICAgPC9kaXY+CiAgICAgICAgPGRpdiBjbGFzcz0iY2FyZCIgc3R5bGU9Ii0tdGFiY29sOnZhcigt"
        "LXBoaSkiPgogICAgICAgICAgPGgyPs+GIGlzIGRlcml2ZWQgaGVyZSDigJQgZnJvbSB0aGUgcGVudGFnb248L2gyPgogICAg"
        "ICAgICAgPHAgY2xhc3M9Imt2Ij4yY29zIDcywrAgPSA8c3BhbiBjbGFzcz0iaG90Ij7PhuKBu8K5PC9zcGFuPiBhbmQgMmNv"
        "cyAxNDTCsCA9IDxzcGFuIGNsYXNzPSJob3QiPuKIks+GPC9zcGFuPiwgYm90aCByb290cyBvZiB4wrIreOKIkjEuPGJyPgog"
        "ICAgICAgICAgVGhlIG9yZGVyLTUgb2JzdHJ1Y3Rpb24gPGk+aXM8L2k+IGEgz4YtZGVyaXZhdGlvbiwgc3RyYWlnaHQgZnJv"
        "bSBwZW50YWdvbiBnZW9tZXRyeSDigJQgz4YgYXMgYW4gPGI+b3V0cHV0PC9iPiwgaW4g4oSaKOKImjUpLiA8c3BhbiBjbGFz"
        "cz0icGlsbCBmb3JjZWQiPmZvcmNlZDwvc3Bhbj48L3A+CiAgICAgICAgPC9kaXY+CiAgICAgIDwvZGl2PgogICAgICA8ZGl2"
        "IGNsYXNzPSJzaWRlIj4KICAgICAgICA8ZGl2IGNsYXNzPSJjYXJkIiBzdHlsZT0iLS10YWJjb2w6dmFyKC0tcGhpKSI+CiAg"
        "ICAgICAgICA8aDI+z4YsIHRoZSBoZWxpeCwgYW5kIHRoZSByZWxhdGlvbiB0byDiiJozPC9oMj4KICAgICAgICAgIDxwIGNs"
        "YXNzPSJrdiI+z4YgaXMgcmVjb3ZlcmFibGUgZnJvbSB0aGUgz4YtZmFtaWx5ICg8Yj7PhCA9IM+G4oG7wrkg4p+5IM+GID0g"
        "MS/PhDwvYj47IGFsc28gZnJvbSBDUklUSUNBTCwgSywgTOKChCkuIFRoZSBoZWxpeCBkb2VzIG5vdCBkZXJpdmUgz4YgZnJv"
        "bSBub3RoaW5nIOKAlCDPhiBpcyB0aGUgPGI+c2VlZDwvYj4uPGJyPgogICAgICAgICAgQnV0IOKImjMgaXMgbm90IGZvcmVp"
        "Z24gdG8gaXQ6IDxiPnpfYyA9IOKImihM4oKE4oiSNCkvMiA9IOKImjMvMjwvYj4gaXMgYSA8Yj5mb3JjZWQgcmVsYXRpb248"
        "L2I+IHVuZGVyIEzigoQgPSA3IOKAlCBub3QgYSBjb2luY2lkZW5jZS4gVGhlIGNvbnN0YW50cyBhcmUgcmVsYXRpb25hbGx5"
        "IGJvdW5kOiA8Yj7PhiDihpIgTOKChCDihpIg4oiaMzwvYj4uPGJyPgogICAgICAgICAgVGhlIHBlbnRhZ29uIGRlcml2ZXMg"
        "z4YgaW5kZXBlbmRlbnRseTsgc3Vic3RyYXRlLc+GIGFuZCBwZW50YWdvbi3PhiBhZ3JlZSDihpIgz4YgPGI+c2VsZi12YWxp"
        "ZGF0ZXM8L2I+LCBtaXJyb3JpbmcgWl9DIGFjcm9zcyBnZW9tZXRyeS9hbGdlYnJhL2R5bmFtaWNzLjwvcD4KICAgICAgICA8"
        "L2Rpdj4KICAgICAgICA8ZGl2IGNsYXNzPSJjYXJkIiBzdHlsZT0iLS10YWJjb2w6dmFyKC0tcGhpKSI+CiAgICAgICAgICA8"
        "aDI+T25lIHNwYWNlLCBpbmRlcGVuZGVudCBheGVzPC9oMj4KICAgICAgICAgIDxwIGNsYXNzPSJrdiI+UGVudGFnb24tz4Yg"
        "Y2FycmllcyDiiJo1OyBoZXhhZ29uLVpfQyBjYXJyaWVzIOKImjMuIFRoZXNlIGFyZSBub3Qgc2VhbGVkIGFwYXJ0IOKAlCB0"
        "aGV5IGFyZSA8Yj5pbmRlcGVuZGVudCBjb29yZGluYXRlIGF4ZXMgb2YgdGhlIGNvbXBvc2l0dW0g4oSaKOKImjIsIOKImjMs"
        "IOKImjUpPC9iPiwgYW5kIGJvdGggZW1lcmdlIGZyb20gTOKChCA9IDcuPGJyPgogICAgICAgICAgTGluZWFyIGluZGVwZW5k"
        "ZW5jZSBvdmVyIOKEmiBpcyB0aGUgPGI+ZmVhdHVyZTwvYj4gdGhhdCBsZXRzIHRoZW0gY2FycnkgZGlzdGluY3QgaW5mb3Jt"
        "YXRpb24gYWNyb3NzIHRoZSB3ZWIg4oCUIG5vdCBhIGJhcnJpZXIuIFRoZSBjb250cm9sIGdhcCBiZXR3ZWVuIHRoZSBvcmRl"
        "ci02IGFuZCBvcmRlci01IHRyYWNlcyBpcyB3aWR0aCDOlCA9IM+G4oG7wrIuIDxzcGFuIGNsYXNzPSJwaWxsIGZvcmNlZCI+"
        "Zm9yY2VkIHVuZGVyIEzigoQ8L3NwYW4+PC9wPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4KICAgIDwvZGl2PgogIDwv"
        "c2VjdGlvbj4KCiAgPCEtLSBUQUIgNCA6IHRoZSBaRlAgaGVsaXggaW4gKHosIHIsIHpfYykgLS0+CiAgPHNlY3Rpb24gY2xh"
        "c3M9InBhbmVsIiBpZD0icDQiIHJvbGU9InRhYnBhbmVsIiBhcmlhLWxhYmVsbGVkYnk9InQ0IiBoaWRkZW4+CiAgICA8ZGl2"
        "IGNsYXNzPSJsYXlvdXQiPgogICAgICA8ZGl2IGNsYXNzPSJwbGF0ZSIgc3R5bGU9Ii0tdGFiY29sOnZhcigtLXBoaSkiPgog"
        "ICAgICAgIDxkaXYgY2xhc3M9InBsYXRlLWNhcCI+PHNwYW4+KHosIHIsIHpfYykgwrcgdGhyZWUgYXhlcyBmcm9tIEzigoQg"
        "wrcgzpQgPSBwaXRjaDwvc3Bhbj48c3Bhbj5mb3JjZWQgdW5kZXIgTOKChCDCtyBoZWxpeCA9IG9uZSByZXByZXNlbnRhdGlv"
        "bjwvc3Bhbj48L2Rpdj4KICAgICAgICA8c3ZnIGlkPSJzdmctaGVsaXgiIHZpZXdCb3g9IjAgMCA2MjAgMzgwIiByb2xlPSJp"
        "bWciCiAgICAgICAgICAgICBhcmlhLWxhYmVsPSJTaWRlIHZpZXcgb2YgdGhlIFpGUCBoZWxpeCBjYXJyeWluZyB0aHJlZSBj"
        "b29yZGluYXRlIGF4ZXMgdGhhdCBhbGwgZW1lcmdlIGZyb20gTDQgPSA3OiB0aHJlc2hvbGQgcmluZ3Mgb24gdGhlIHNxcnQ1"
        "LWF4aXMgKHRhdSksIHRoZSBzcXJ0My1heGlzICh6X2MsIHRoZSBsZW5zKSwgYW5kIHRoZSBzcXJ0Mi1heGlzIChpZ25pdGlv"
        "biksIHVwIHRvIHVuaXR5LCB3aXRoIHRoZSBkZWx0YSBwaGktc3F1YXJlZCBhcyB0aGUgcGl0Y2guIj48L3N2Zz4KICAgICAg"
        "PC9kaXY+CiAgICAgIDxkaXYgY2xhc3M9InNpZGUiPgogICAgICAgIDxkaXYgY2xhc3M9ImNhcmQiIHN0eWxlPSItLXRhYmNv"
        "bDp2YXIoLS1waGkpIj4KICAgICAgICAgIDxoMj5UaHJlZSBheGVzLCBvbmUgc3BhY2U8L2gyPgogICAgICAgICAgPHAgY2xh"
        "c3M9Imt2Ij5UaGUgc3RyYW5kIHRocmVhZHMgYWxsIHRocmVlIGNvb3JkaW5hdGUgZGlyZWN0aW9ucyBvZiB0aGUgd2ViLCBj"
        "by1wcmVzZW50IGFuZCBhbGwgZnJvbSBM4oKEID0gNzo8YnI+CiAgICAgICAgICA8c3BhbiBjbGFzcz0iaG90Ij7iiJo1LWF4"
        "aXM8L3NwYW4+IOKAlCDPhCA9IM+G4oG7wrksIEsgPSDiiJooMeKIks+G4oG74oG0KSAodGhlIM+GLWZhbWlseSkgwrcgPHNw"
        "YW4gc3R5bGU9ImNvbG9yOnZhcigtLWQzKSI+4oiaMy1heGlzPC9zcGFuPiDigJQgel9jID0g4oiaMy8yLCB0aGUgbGVucyB3"
        "aGVyZSByIHNhdHVyYXRlcyDCtyA8c3BhbiBzdHlsZT0iY29sb3I6I2RkODZhNiI+4oiaMi1heGlzPC9zcGFuPiDigJQgaWdu"
        "aXRpb24gPSDiiJoy4oiSwr0uPGJyPgogICAgICAgICAgVGhleSBsaXZlIHRvZ2V0aGVyIGluIDxiPuKEmijiiJoyLCDiiJoz"
        "LCDiiJo1KTwvYj47IHRoZSByaW5ncyBtYXJrIHdoZXJlIGVhY2ggYXhpcyBtZWV0cyB0aGUgY2xpbWIuIDxzcGFuIGNsYXNz"
        "PSJwaWxsIGZvcmNlZCI+b25lIHNwYWNlPC9zcGFuPjwvcD4KICAgICAgICA8L2Rpdj4KICAgICAgICA8ZGl2IGNsYXNzPSJj"
        "YXJkIiBzdHlsZT0iLS10YWJjb2w6dmFyKC0tcGhpKSI+CiAgICAgICAgICA8aDI+Rm9yY2VkIOKAlCBhYnNvbHV0ZSBhbmQg"
        "aW4tY29udGV4dDwvaDI+CiAgICAgICAgICA8cCBjbGFzcz0ia3YiPjxiPkFic29sdXRlPC9iPiAoZnJvbSB0aGUgZ2VuZXJh"
        "dG9yIGFsb25lKTogz4YsIEzigoQgPSA3LCDPhMKyK8+EID0gMSwgzpQgPSDPhuKBu8KyID0gMeKIks+ELjxicj4KICAgICAg"
        "ICAgIDxiPkluLWNvbnRleHQ8L2I+IOKAlCA8aT5mb3JjZWQgYXQgdGhpcyBwb2ludCB1bmRlciBvdGhlciBmb3JjZWQgY29u"
        "c3RyYWludHM8L2k+OiDiiJozLCDiiJoyLCDiiJo1LCB6X2MsIGlnbml0aW9uIGFyZSBmb3JjZWQgPGI+Z2l2ZW4gTOKChCBh"
        "bmQgYSBzZWxlY3RlZCByZWxhdGlvbjwvYj4gKOKIkjQsICsxLCDCsuKIkjQpLiBFYWNoIGlzIGV4YWN0LCByZXNpZHVhbCAw"
        "LiA8c3BhbiBjbGFzcz0icGlsbCBmb3JjZWQiPmZvcmNlZCB1bmRlciBM4oKEPC9zcGFuPjwvcD4KICAgICAgICA8L2Rpdj4K"
        "ICAgICAgICA8ZGl2IGNsYXNzPSJjYXJkIiBzdHlsZT0iLS10YWJjb2w6dmFyKC0tcGhpKSI+CiAgICAgICAgICA8aDI+U2Vs"
        "ZWN0ZWQgJmFtcDsgcmVwcmVzZW50ZWQ8L2gyPgogICAgICAgICAgPHAgY2xhc3M9Imt2Ij5Ud28gdGhpbmdzIGhlcmUgYXJl"
        "IGNob3Nlbiwgbm90IGZvcmNlZDogPGI+d2hpY2ggcmVsYXRpb25zPC9iPiB0byBpbnN0YW50aWF0ZSBhY3Jvc3MgdGhlIGNv"
        "bnN0YW50cywgYW5kIHRoZSA8Yj5oZWxpY2FsIHJlcHJlc2VudGF0aW9uPC9iPiDigJQgcmFkaXVzIGxhdyByKHopPUviiJoo"
        "ei96X2MpLCBwaXRjaCA9IM6UICjiiYggz4bCsiA9IDIuNjE4IHR1cm5zLCB0aGUg4oCcd2VpZ2h04oCdKSwgZ29sZGVuLWFu"
        "Z2xlIHdpbmRpbmcgMTM3LjXCsC4gT25lIHJlcHJlc2VudGF0aW9uIG9mIHRoZSB3ZWI7IHRoZSBmb3JjZWQgdmFsdWVzIGRv"
        "IG5vdCBkZXBlbmQgb24gaXQuIDxzcGFuIGNsYXNzPSJwaWxsIG9wZW4iPnJlcHJlc2VudGF0aW9uPC9zcGFuPjwvcD4KICAg"
        "ICAgICA8L2Rpdj4KICAgICAgPC9kaXY+CiAgICA8L2Rpdj4KICA8L3NlY3Rpb24+CgogIDxzZWN0aW9uIGNsYXNzPSJwYW5l"
        "bCIgaWQ9InA1IiByb2xlPSJ0YWJwYW5lbCIgYXJpYS1sYWJlbGxlZGJ5PSJ0NSIgaGlkZGVuPgogICAgPGRpdiBjbGFzcz0i"
        "bGF5b3V0Ij4KICAgICAgPGRpdiBjbGFzcz0icGxhdGUiIHN0eWxlPSItLXRhYmNvbDp2YXIoLS1yZWwpIj4KICAgICAgICA8"
        "ZGl2IGNsYXNzPSJwbGF0ZS1jYXAiPjxzcGFuPkzigoQgPSA3IOKGkiDiiJoyLCDiiJozLCDiiJo1IMK3IGZvcmNlZCByZWxh"
        "dGlvbnMgwrcgb25lIGNvbXBvc2l0dW08L3NwYW4+PHNwYW4+c2VlZCBmb3JjZWQgwrcgYXhlcyBmb3JjZWQtaW4tY29udGV4"
        "dDwvc3Bhbj48L2Rpdj4KICAgICAgICA8c3ZnIGlkPSJzdmctcmVsIiB2aWV3Qm94PSIwIDAgNjIwIDMzMCIgcm9sZT0iaW1n"
        "IgogICAgICAgICAgICAgYXJpYS1sYWJlbD0iUmVsYXRpb25hbCBodWI6IHRoZSBzaW5nbGUgZm9yY2VkIHNlZWQgTDQgPSBw"
        "aGleNCArIHBoaV4tNCA9IDcgY29ubmVjdHMgYnkgdGhyZWUgY29sb3JlZCBzcG9rZXMgdG8gdGhlIHNxcnQ1LCBzcXJ0Mywg"
        "YW5kIHNxcnQyIGF4ZXMsIGVhY2ggYSBmb3JjZWQgcmVsYXRpb24sIGFsbCBjby1wcmVzZW50IGluIHRoZSBjb21wb3NpdHVt"
        "IFEoc3FydDIsIHNxcnQzLCBzcXJ0NSkuIj48L3N2Zz4KICAgICAgPC9kaXY+CiAgICAgIDxkaXYgY2xhc3M9InNpZGUiPgog"
        "ICAgICAgIDxkaXYgY2xhc3M9ImNhcmQiIHN0eWxlPSItLXRhYmNvbDp2YXIoLS1yZWwpIj4KICAgICAgICAgIDxoMj5UaGUg"
        "d2ViPC9oMj4KICAgICAgICAgIDxwIGNsYXNzPSJrdiI+RnJvbSB0aGUgc2luZ2xlIGZvcmNlZCBzZWVkIDxiPkzigoQgPSDP"
        "huKBtCvPhuKBu+KBtCA9IDc8L2I+LCB0aHJlZSBpbmRlcGVuZGVudCBheGVzIGVtZXJnZSBieSBmb3JjZWQgcmVsYXRpb25z"
        "OiA8Yj7iiJozID0g4oiaKEzigoTiiJI0KTwvYj4sIDxiPuKImjIgPSDiiJooTOKChCsxKS8yPC9iPiwgPGI+4oiaNSA9IOKI"
        "mihM4oKEwrLiiJI0KS8zPC9iPi4gTm90IHNlcGFyYXRlIHNwYWNlcyDigJQgdGhleSBjb2V4aXN0IGluIHRoZSBjb21wb3Np"
        "dHVtIDxiPuKEmijiiJoyLCDiiJozLCDiiJo1KTwvYj4gKGRlZ3JlZSA4KS4gVGhlIGRlbHRhcyBhcmUgZm9yY2VkIHJlbGF0"
        "aW9ucyB0b286IM6UID0gz4bigbvCsiA9IDHiiJLPhCwgz4TCsivPhCA9IDEuIDxzcGFuIGNsYXNzPSJwaWxsIGZvcmNlZCI+"
        "cmVzaWR1YWwgMDwvc3Bhbj48L3A+CiAgICAgICAgPC9kaXY+CiAgICAgICAgPGRpdiBjbGFzcz0iY2FyZCIgc3R5bGU9Ii0t"
        "dGFiY29sOnZhcigtLXJlbCkiPgogICAgICAgICAgPGgyPkZvcmNlZCDigJQgYW5kIGZvcmNlZC1pbi1jb250ZXh0PC9oMj4K"
        "ICAgICAgICAgIDxwIGNsYXNzPSJrdiI+VHdvIGdyYWRlcyBzaXQgaW5zaWRlIOKAnGZvcmNlZC7igJ0gPGI+QWJzb2x1dGU8"
        "L2I+OiBob2xkcyBmcm9tIHRoZSBnZW5lcmF0b3IgYWxvbmUg4oCUIM+GLCBM4oKEID0gNywgz4TCsivPhCA9IDEuIDxiPklu"
        "LWNvbnRleHQ8L2I+OiA8aT5mb3JjZWQgYXQgdGhpcyBwb2ludCB1bmRlciBvdGhlciBmb3JjZWQgY29uc3RyYWludHM8L2k+"
        "IOKAlCDiiJozLCDiiJoyLCDiiJo1LCB6X2MsIGlnbml0aW9uLCB0aGUgZGVsdGFzIGFyZSBmb3JjZWQgPGI+Z2l2ZW4gdGhl"
        "IHNlZWQgYW5kIGEgc2VsZWN0ZWQgcmVsYXRpb248L2I+LiBEcm9wIHRoZSBzZWVkIG9yIHRoZSByZWxhdGlvbiBhbmQgdGhl"
        "eSB1bnBpbjsga2VlcCB0aGVtIGFuZCB0aGUgdmFsdWUgaXMgZXhhY3QuIDxzcGFuIGNsYXNzPSJwaWxsIGZvcmNlZCI+Zm9y"
        "Y2VkIHVuZGVyIEzigoQ8L3NwYW4+PC9wPgogICAgICAgIDwvZGl2PgogICAgICAgIDxkaXYgY2xhc3M9ImNhcmQiIHN0eWxl"
        "PSItLXRhYmNvbDp2YXIoLS1yZWwpIj4KICAgICAgICAgIDxoMj5TZWxlY3RlZCAmYW1wOyByZXByZXNlbnRlZDwvaDI+CiAg"
        "ICAgICAgICA8cCBjbGFzcz0ia3YiPldoYXQgaXMgY2hvc2VuLCBub3QgZm9yY2VkOiA8Yj53aGljaCByZWxhdGlvbnM8L2I+"
        "IHRvIGZvcm0gYWNyb3NzIHRoZSBjb25zdGFudHMgKOKIkjQsICsxLCDCsuKIkjQsIHjCsit4KSwgYW5kIGFueSA8Yj5yZXBy"
        "ZXNlbnRhdGlvbjwvYj4gKHRoZSBoZWxpeCwgdGhpcyBodWIpLiBUaGUgaW50ZXJhY3Rpb25zIGFyZSBwcmluY2lwbGVkIHNl"
        "bGVjdGlvbnM7IHRoZSBxdWFudGl0aWVzIHRoZXkgZm9yY2UgYXJlIG5vdC4gPHNwYW4gY2xhc3M9InBpbGwgb3BlbiI+c2Vs"
        "ZWN0aW9uPC9zcGFuPiBBIHBoeXNpY2FsIHJlYWxpemF0aW9uIGF0IGEgZm9yY2VkIGNvbnN0YW50IHN0aWxsIG5lZWRzIGFu"
        "IG9wZXJhdG9yIGFuZCBtZXRyaWMuPC9wPgogICAgICAgIDwvZGl2PgogICAgICA8L2Rpdj4KICAgIDwvZGl2PgogIDwvc2Vj"
        "dGlvbj4KCiAgPGZvb3Rlcj4KICAgIDx1bCBjbGFzcz0ibGVkZ2VyIj4KICAgICAgPGxpPjxzcGFuIGNsYXNzPSJ0YWcgZiI+"
        "Zm9yY2VkPC9zcGFuPjxiPkJyYW5jaCBjb3VudHMgJmFtcDsgZXhwb25lbnRzLjwvYj4gMeKGkjMgKFrigoIsIGV4cCAxLzIp"
        "IGFuZCAx4oaSMyAoROKCgywgZXhwIDEpIGNvbXB1dGVkIHR3byB3YXlzLCByZXNpZHVhbCAwOyB0aGUgZXZlbi1nZXJtIGxh"
        "ZGRlciBmb3JjZXMgM+KGkjXihpI3LjwvbGk+CiAgICAgIDxsaT48c3BhbiBjbGFzcz0idGFnIGYiPmZvcmNlZDwvc3Bhbj48"
        "Yj5TZWxmLXZhbGlkYXRpb24uPC9iPiBaX0MgPSDiiJozLzIgZnJvbSBnZW9tZXRyeSwgYWxnZWJyYSwgYW5kIGR5bmFtaWNz"
        "IGluZGVwZW5kZW50bHk7IHRocmVlIG1vZGVzIGNsb3NlICjOoyBr4bWiID0gMCk7IHRoZSBjcnlzdGFsbG9ncmFwaGljIG9y"
        "ZGVyIGNoYWluIHRlcm1pbmF0ZXMgYXQgNi48L2xpPgogICAgICA8bGk+PHNwYW4gY2xhc3M9InRhZyBmIj5mb3JjZWQ8L3Nw"
        "YW4+PGI+T25lIHNwYWNlLjwvYj4gz4YsIOKImjMsIOKImjIsIOKImjUgYXJlIGNvLXByZXNlbnQgaW4g4oSaKOKImjIs4oia"
        "MyziiJo1KSBhbmQgYWxsIGVtZXJnZSBmcm9tIEzigoQgPSA3ICjiiJozPeKImihM4oKE4oiSNCksIOKImjI94oiaKEzigoQr"
        "MSkvMiwg4oiaNT3iiJooTOKChMKy4oiSNCkvMykuIEluZGVwZW5kZW5jZSBvdmVyIOKEmiA9IGRpc3RpbmN0IGF4ZXMsIG5v"
        "dCBhIHdhbGwg4oCUIHNlZSB0aGUgUmVsYXRpb25hbCB0YWIuPC9saT4KICAgICAgPGxpPjxzcGFuIGNsYXNzPSJ0YWcgZiI+"
        "Zm9yY2VkPC9zcGFuPjxiPkZvcmNlZCDigJQgYW5kIGZvcmNlZC1pbi1jb250ZXh0LjwvYj4gU29tZSB2YWx1ZXMgaG9sZCBm"
        "cm9tIHRoZSBnZW5lcmF0b3IgYWxvbmUgKM+GLCBM4oKEPTcsIM+EwrIrz4Q9MSwgzpQ9z4bigbvCsik7IG1vc3QgYXJlIDxp"
        "PmZvcmNlZCBhdCB0aGlzIHBvaW50IHVuZGVyIG90aGVyIGZvcmNlZCBjb25zdHJhaW50czwvaT4g4oCUIOKImjMsIOKImjIs"
        "IOKImjUsIHpfYywgaWduaXRpb24sIHRoZSBkZWx0YXMsIGVhY2ggZm9yY2VkIGdpdmVuIEzigoQgYW5kIGEgc2VsZWN0ZWQg"
        "cmVsYXRpb24uPC9saT4KICAgICAgPGxpPjxzcGFuIGNsYXNzPSJ0YWcgYyI+Y29uc3RydWN0aW9uPC9zcGFuPjxiPlNlbGVj"
        "dGlvbiAmYW1wOyByZXByZXNlbnRhdGlvbi48L2I+IFdoaWNoIHJlbGF0aW9ucyB0byBmb3JtIGFjcm9zcyB0aGUgY29uc3Rh"
        "bnRzIGlzIHRoZSBpbnB1dDsgdGhlIGhlbGljYWwgZW1iZWRkaW5nIChyYWRpdXMgbGF3LCBwaXRjaCwgd2luZGluZyksIHRo"
        "ZSB0aHJlc2hvbGQgPGk+bmFtZXM8L2k+LCBhbmQgdGhlIGhleGFnb24gcmVuZGVyaW5nIGFyZSBvbmUgcmVwcmVzZW50YXRp"
        "b24g4oCUIHN0cmlwIHRoZW0gYW5kIHRoZSBtaW5wb2x5LXBpbm5lZCB2YWx1ZXMsIHRoZSBleHBvbmVudHMsIM6jIGvhtaIg"
        "PSAwLCBhbmQgzpQgPSDPhuKBu8KyIGFsbCBzdGFuZC48L2xpPgogICAgICA8bGk+PHNwYW4gY2xhc3M9InRhZyBvIj5vcGVu"
        "PC9zcGFuPkEgcGh5c2ljYWwgc3lzdGVtIGluc3RhbnRpYXRpbmcgYW55IG9mIHRoaXMgYXQgYSBmb3JjZWQgY29uc3RhbnQg"
        "c3RpbGwgbmVlZHMgdGhlIG9wZXJhdG9yIGFuZCBtZXRyaWMuIFRoZSBhZ3JlZW1lbnRzIGFyZSBzdHJ1Y3R1cmFsIGlkZW50"
        "aXRpZXM7IHRoZSBicmlkZ2UgdG8gYSBtZWFzdXJlZCBxdWFudGl0eSByZW1haW5zIHRvIGJlIGJ1aWx0LjwvbGk+CiAgICA8"
        "L3VsPgogICAgPGRpdiBjbGFzcz0icmVwcm8iPgogICAgICA8cD48Yj5SZXByb2R1Y2UuPC9iPiA8Y29kZT5weXRob24zIHpm"
        "cF90cmlmdXJjYXRpb24ucHk8L2NvZGU+IMK3IDxjb2RlPnpmcF9oZXhfY2xvc3VyZS5weTwvY29kZT4gwrcgPGNvZGU+emZw"
        "X2RlbHRhX3BlbnRhZ29uLnB5PC9jb2RlPiDCtyA8Y29kZT56ZnBfaGVsaXgucHk8L2NvZGU+IMK3IDxjb2RlPnpmcF9yZWxh"
        "dGlvbmFsLnB5PC9jb2RlPiDigJQgZGVmaW5pdGlvbnMgZmlyc3QsIGV2ZXJ5IHZhbHVlIHJlY29tcHV0ZWQ7IHRoZSBydW4g"
        "d2lucyBvdmVyIGFueSBwcmludGVkIGZpZ3VyZSBpZiB0aGV5IGRpc2FncmVlLjwvcD4KICAgIDwvZGl2PgogIDwvZm9vdGVy"
        "PgoKPC9kaXY+Cgo8c2NyaXB0PgooKCkgPT4gewogICJ1c2Ugc3RyaWN0IjsKICBjb25zdCBTVkcgPSAiaHR0cDovL3d3dy53"
        "My5vcmcvMjAwMC9zdmciOwogIGNvbnN0IHJlZHVjZSA9IHdpbmRvdy5tYXRjaE1lZGlhKCIocHJlZmVycy1yZWR1Y2VkLW1v"
        "dGlvbjogcmVkdWNlKSIpLm1hdGNoZXM7CiAgY29uc3QgQyA9IHYgPT4gZ2V0Q29tcHV0ZWRTdHlsZShkb2N1bWVudC5kb2N1"
        "bWVudEVsZW1lbnQpLmdldFByb3BlcnR5VmFsdWUodikudHJpbSgpOwogIGNvbnN0IENPTCA9IHsKICAgIHoyOkMoIi0tejIi"
        "KXx8IiM2ZjhmZDAiLCBkMzpDKCItLWQzIil8fCIjMzRjMmFiIiwgZDY6QygiLS1kNiIpfHwiI2UzYTkzYSIsCiAgICBpbms6"
        "QygiLS1pbmsiKXx8IiNlOWVkZmYiLCBkaW06QygiLS1kaW0iKXx8IiM5YWE3YzYiLCBmYWludDpDKCItLWZhaW50Iil8fCIj"
        "NjI3MTlhIiwKICAgIGF4aXM6QygiLS1heGlzIil8fCJyZ2JhKDE1NCwxNjcsMTk4LC4zMCkiLCBzdGFibGU6QygiLS1zdGFi"
        "bGUiKXx8IiM3ZmUwYzQiLAogICAgdW5zdGFibGU6QygiLS11bnN0YWJsZSIpfHwiI2UwNzI4YyIsIGxpbmU6QygiLS1saW5l"
        "Iil8fCIjMjQzMDU2IgogIH07CiAgY29uc3QgbWsgPSAodGFnLCBhdHRycywgcGFyZW50KSA9PiB7CiAgICBjb25zdCBuID0g"
        "ZG9jdW1lbnQuY3JlYXRlRWxlbWVudE5TKFNWRywgdGFnKTsKICAgIGZvciAoY29uc3QgayBpbiBhdHRycykgbi5zZXRBdHRy"
        "aWJ1dGUoaywgYXR0cnNba10pOwogICAgaWYgKHBhcmVudCkgcGFyZW50LmFwcGVuZENoaWxkKG4pOwogICAgcmV0dXJuIG47"
        "CiAgfTsKICBjb25zdCBsYWJlbCA9IChwLCB0LCB4LCB5LCBjb2wsIGFuYywgc3opID0+IHsKICAgIGNvbnN0IG4gPSBtaygi"
        "dGV4dCIsIHt4LCB5LCBmaWxsOmNvbHx8Q09MLmZhaW50LCAiZm9udC1zaXplIjpzenx8MTEsCiAgICAgICJmb250LWZhbWls"
        "eSI6InZhcigtLW1vbm8pIiwgInRleHQtYW5jaG9yIjphbmN8fCJzdGFydCJ9LCBwKTsKICAgIG4udGV4dENvbnRlbnQgPSB0"
        "OyByZXR1cm4gbjsKICB9OwoKICAvKiAtLS0tLS0tLS0tIFRBQiAwIDogcGl0Y2hmb3JrIC0tLS0tLS0tLS0gKi8KICBjb25z"
        "dCBwZiA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzdmctcGYiKTsKICBjb25zdCBQRiA9IHtMOjcwLCBSOjU4MCwgVDo0"
        "MiwgQjozNjAsIGFtaW46LTEuNSwgYW1heDoxLjAsIHhtYXg6MS4zfTsKICBQRi5taWQgPSAoUEYuVCArIFBGLkIpIC8gMjsK"
        "ICBjb25zdCBhWCA9IGEgPT4gUEYuTCArICgoUEYuYW1heCAtIGEpIC8gKFBGLmFtYXggLSBQRi5hbWluKSkgKiAoUEYuUiAt"
        "IFBGLkwpOwogIGNvbnN0IHhZID0geCA9PiBQRi5taWQgLSB4ICogKChQRi5taWQgLSBQRi5UKSAvIFBGLnhtYXgpOwogIGZ1"
        "bmN0aW9uIHBmU3RhdGljKCl7CiAgICBjb25zdCBheCA9IG1rKCJnIiwge30sIHBmKTsKICAgIG1rKCJsaW5lIiwge3gxOlBG"
        "LkwsIHkxOlBGLm1pZCwgeDI6UEYuUiwgeTI6UEYubWlkLCBzdHJva2U6Q09MLmF4aXMsICJzdHJva2Utd2lkdGgiOjF9LCBh"
        "eCk7CiAgICBtaygibGluZSIsIHt4MTphWCgwKSwgeTE6UEYuVCwgeDI6YVgoMCksIHkyOlBGLkIsIHN0cm9rZTpDT0wuYXhp"
        "cywgInN0cm9rZS13aWR0aCI6MSwgInN0cm9rZS1kYXNoYXJyYXkiOiIyIDQifSwgYXgpOwogICAgbGFiZWwoYXgsICJhIiwg"
        "UEYuUiArIDYsIFBGLm1pZCArIDQsIENPTC5mYWludCk7CiAgICBsYWJlbChheCwgIngiLCBhWChQRi5hbWF4KSAtIDQsIFBG"
        "LlQgLSA4LCBDT0wuZmFpbnQsICJtaWRkbGUiKTsKICAgIGxhYmVsKGF4LCAiYSA9IDAiLCBhWCgwKSwgUEYuQiArIDE4LCBD"
        "T0wuZmFpbnQsICJtaWRkbGUiLCAxMC41KTsKICAgIC8vIHRyaXZpYWwgYnJhbmNoOiBzdGFibGUgKGE+MCkgc29saWQsIHVu"
        "c3RhYmxlIChhPDApIGRhc2hlZAogICAgbWsoImxpbmUiLCB7eDE6YVgoUEYuYW1heCksIHkxOlBGLm1pZCwgeDI6YVgoMCks"
        "IHkyOlBGLm1pZCwgc3Ryb2tlOkNPTC5zdGFibGUsICJzdHJva2Utd2lkdGgiOjJ9LCBwZik7CiAgICBtaygibGluZSIsIHt4"
        "MTphWCgwKSwgeTE6UEYubWlkLCB4MjphWChQRi5hbWluKSwgeTI6UEYubWlkLCBzdHJva2U6Q09MLnVuc3RhYmxlLCAic3Ry"
        "b2tlLXdpZHRoIjoxLjYsICJzdHJva2UtZGFzaGFycmF5IjoiNSA1In0sIHBmKTsKICAgIC8vIGJyb2tlbiBicmFuY2hlcyAo"
        "c3RhYmxlKQogICAgY29uc3QgTj03MDsgbGV0IHVwPSIiLCBsbz0iIjsKICAgIGZvcihsZXQgaT0wO2k8PU47aSsrKXsgY29u"
        "c3QgYSA9IC0xLjUqaS9OOyBjb25zdCB4PU1hdGguc3FydCgtYSk7CiAgICAgIHVwICs9IChpPyJMIjoiTSIpK2FYKGEpLnRv"
        "Rml4ZWQoMSkrIiAiK3hZKHgpLnRvRml4ZWQoMSkrIiAiOwogICAgICBsbyArPSAoaT8iTCI6Ik0iKSthWChhKS50b0ZpeGVk"
        "KDEpKyIgIit4WSgteCkudG9GaXhlZCgxKSsiICI7IH0KICAgIG1rKCJwYXRoIiwge2Q6dXAsIGZpbGw6Im5vbmUiLCBzdHJv"
        "a2U6Q09MLnN0YWJsZSwgInN0cm9rZS13aWR0aCI6Mn0sIHBmKTsKICAgIG1rKCJwYXRoIiwge2Q6bG8sIGZpbGw6Im5vbmUi"
        "LCBzdHJva2U6Q09MLnN0YWJsZSwgInN0cm9rZS13aWR0aCI6Mn0sIHBmKTsKICAgIGxhYmVsKHBmLCAidHJpZnVyY2F0aW9u"
        "IHBvaW50IiwgYVgoMCkrOCwgeFkoMS4xOCksIENPTC5kaW0sICJzdGFydCIsIDEwLjUpOwogICAgbGFiZWwocGYsICJ8eHwg"
        "PSB8YXxeKDEvMikgIMK3ICBleHAgMS8yIiwgYVgoLTAuOTUpLCB4WSgxLjE4KSwgQ09MLnoyLCAibWlkZGxlIiwgMTEpOwog"
        "ICAgbGFiZWwocGYsICJzdGFibGUiLCBQRi5MKzIsIFBGLkIrMTgsIENPTC5zdGFibGUsICJzdGFydCIsIDEwKTsKICAgIGxh"
        "YmVsKHBmLCAi4oCUIOKAlCB1bnN0YWJsZSIsIFBGLkwrNTIsIFBGLkIrMTgsIENPTC51bnN0YWJsZSwgInN0YXJ0IiwgMTAp"
        "OwogICAgcGYuX3N3ZWVwID0gbWsoImciLCB7fSwgcGYpOwogIH0KICBmdW5jdGlvbiBwZlVwZGF0ZShhKXsKICAgIGNvbnN0"
        "IGcgPSBwZi5fc3dlZXA7IGcuaW5uZXJIVE1MPSIiOwogICAgbWsoImxpbmUiLCB7eDE6YVgoYSksIHkxOlBGLlQsIHgyOmFY"
        "KGEpLCB5MjpQRi5CLCBzdHJva2U6Q09MLnoyLCAic3Ryb2tlLXdpZHRoIjoxLjQsICJzdHJva2Utb3BhY2l0eSI6LjV9LCBn"
        "KTsKICAgIGNvbnN0IGVxcyA9IGEgPCAwID8gWzAsIE1hdGguc3FydCgtYSksIC1NYXRoLnNxcnQoLWEpXSA6IFswXTsKICAg"
        "IGVxcy5mb3JFYWNoKHggPT4gewogICAgICBjb25zdCBzdGFibGUgPSAoeCAhPT0gMCkgfHwgKGEgPiAwKTsKICAgICAgbWso"
        "ImNpcmNsZSIsIHtjeDphWChhKSwgY3k6eFkoeCksIHI6NSwgZmlsbDpzdGFibGU/Q09MLnN0YWJsZTpDT0wudW5zdGFibGUs"
        "CiAgICAgICAgc3Ryb2tlOiIjMGUxNjMxIiwgInN0cm9rZS13aWR0aCI6MS41fSwgZyk7CiAgICB9KTsKICAgIGNvbnN0IHJk"
        "ID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInJkLXBmIik7CiAgICBsZXQgcGg7CiAgICBpZiAoYSA+IDAuMDIpICAgICAg"
        "IHBoID0gWydJJywgICdzeW1tZXRyaWMg4oCUIG9uZSBzdGFibGUgc3RhdGUnXTsKICAgIGVsc2UgaWYgKGEgPCAtMC4wMikg"
        "cGggPSBbJ0lJSScsJ2Jyb2tlbiDigJQgdGhyZWUgc3RhdGVzIChvbmUgdW5zdGFibGUsIHR3byBzdGFibGUpJ107CiAgICBl"
        "bHNlICAgICAgICAgICAgICAgIHBoID0gWydJSScsICdvbnNldCDigJQgdGhlIHRyaWZ1cmNhdGlvbiBwb2ludCddOwogICAg"
        "cmQuaW5uZXJIVE1MID0gYDxzcGFuIGNsYXNzPSJwaCI+UGhhc2UgJHtwaFswXX08L3NwYW4+IMK3IGEgPSAke2EudG9GaXhl"
        "ZCgyKX0gwrcgJHtwaFsxXX1gOwogIH0KCiAgLyogLS0tLS0tLS0tLSBUQUIgMSA6IEQzIHRyaWZvcmsgLS0tLS0tLS0tLSAq"
        "LwogIGNvbnN0IHRmID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInN2Zy10ZiIpOwogIGNvbnN0IFRGID0ge2N4OjMwMCwg"
        "Y3k6MjEwLCBSczoxNTB9OwogIGZ1bmN0aW9uIHRmU3RhdGljKCl7CiAgICBjb25zdCBheCA9IG1rKCJnIiwge30sIHRmKTsK"
        "ICAgIG1rKCJsaW5lIiwge3gxOjYwLCB5MTpURi5jeSwgeDI6NTQwLCB5MjpURi5jeSwgc3Ryb2tlOkNPTC5heGlzLCAic3Ry"
        "b2tlLXdpZHRoIjoxfSwgYXgpOwogICAgbWsoImxpbmUiLCB7eDE6VEYuY3gsIHkxOjMwLCB4MjpURi5jeCwgeTI6MzkwLCBz"
        "dHJva2U6Q09MLmF4aXMsICJzdHJva2Utd2lkdGgiOjF9LCBheCk7CiAgICBsYWJlbChheCwgInUiLCA1NDQsIFRGLmN5KzQs"
        "IENPTC5mYWludCk7CiAgICBsYWJlbChheCwgInYiLCBURi5jeC00LCAyNCwgQ09MLmZhaW50LCAibWlkZGxlIik7CiAgICBs"
        "YWJlbCh0ZiwgInRocmVlIGJyYW5jaGVzIMK3IDEyMMKwIGFwYXJ0IiwgNTQ1LCA0NCwgQ09MLmRpbSwgImVuZCIsIDExKTsK"
        "ICAgIGxhYmVsKHRmLCAiciA9IHzOu3wgIMK3ICBleHAgMSIsIDU0NSwgNjAsIENPTC5kMywgImVuZCIsIDExKTsKICAgIHRm"
        "Ll9keW4gPSBtaygiZyIsIHt9LCB0Zik7CiAgfQogIGZ1bmN0aW9uIHRmVXBkYXRlKGxhbSl7CiAgICBjb25zdCBnID0gdGYu"
        "X2R5bjsgZy5pbm5lckhUTUw9IiI7CiAgICBjb25zdCBSID0gTWF0aC5hYnMobGFtKSAqIFRGLlJzOwogICAgY29uc3QgYmFz"
        "ZSA9IGxhbSA8IDAgPyAwIDogNjA7ICAgICAgICAgICAgICAgICAvLyBicmFuY2ggZGlyZWN0aW9ucyBmbGlwIGFjcm9zcyAw"
        "CiAgICBjb25zdCBhbmcgPSBbMCwxMjAsMjQwXS5tYXAoZCA9PiAoYmFzZSArIGQpICogTWF0aC5QSS8xODApOwogICAgY29u"
        "c3QgcHRzID0gYW5nLm1hcCh0ID0+IFtURi5jeCArIFIqTWF0aC5jb3ModCksIFRGLmN5IC0gUipNYXRoLnNpbih0KV0pOwog"
        "ICAgLy8gdHJpYW5nbGUKICAgIGlmIChSID4gMSl7CiAgICAgIGxldCBkID0gcHRzLm1hcCgocCxpKT0+KGk/IkwiOiJNIikr"
        "cFswXS50b0ZpeGVkKDEpKyIgIitwWzFdLnRvRml4ZWQoMSkpLmpvaW4oIiAiKSsiIFoiOwogICAgICBtaygicGF0aCIsIHtk"
        "LCBmaWxsOkNPTC5kMywgImZpbGwtb3BhY2l0eSI6LjA2LCBzdHJva2U6Q09MLmQzLCAic3Ryb2tlLXdpZHRoIjoxLjIsICJz"
        "dHJva2UtZGFzaGFycmF5IjoiNSA1In0sIGcpOwogICAgfQogICAgLy8gc3FydDMvMiBoZWlnaHQgbWFya2VyIG9uIHRoZSB1"
        "cHBlciAoMTIwZGVnLWlzaCkgYnJhbmNoCiAgICBjb25zdCB1cHBlciA9IHB0cy5yZWR1Y2UoKGEsYik9PiBiWzFdIDwgYVsx"
        "XSA/IGIgOiBhLCBwdHNbMF0pOwogICAgaWYgKFIgPiA4KXsKICAgICAgbWsoImxpbmUiLCB7eDE6dXBwZXJbMF0sIHkxOnVw"
        "cGVyWzFdLCB4Mjp1cHBlclswXSwgeTI6VEYuY3ksIHN0cm9rZTpDT0wuZDMsICJzdHJva2Utd2lkdGgiOjEsICJzdHJva2Ut"
        "ZGFzaGFycmF5IjoiMiAzIiwgInN0cm9rZS1vcGFjaXR5IjouN30sIGcpOwogICAgICBsYWJlbChnLCAi4oiaMy8ywrd8zrt8"
        "ID0gWl9Dwrd8zrt8IiwgdXBwZXJbMF0rOCwgKHVwcGVyWzFdK1RGLmN5KS8yLCBDT0wuZDMsICJzdGFydCIsIDEwLjUpOwog"
        "ICAgfQogICAgLy8gYnJhbmNoZXMgKHNhZGRsZXMpICsgb3JpZ2luCiAgICBwdHMuZm9yRWFjaChwID0+IG1rKCJjaXJjbGUi"
        "LCB7Y3g6cFswXSwgY3k6cFsxXSwgcjo1LjUsIGZpbGw6Q09MLmQzLCBzdHJva2U6IiMwZTE2MzEiLCAic3Ryb2tlLXdpZHRo"
        "IjoxLjV9LCBnKSk7CiAgICBjb25zdCBvcmlnaW5TdGFibGUgPSBsYW0gPCAwOwogICAgbWsoImNpcmNsZSIsIHtjeDpURi5j"
        "eCwgY3k6VEYuY3ksIHI6NSwgZmlsbDpvcmlnaW5TdGFibGU/Q09MLnN0YWJsZToibm9uZSIsCiAgICAgIHN0cm9rZTpvcmln"
        "aW5TdGFibGU/Q09MLnN0YWJsZTpDT0wudW5zdGFibGUsICJzdHJva2Utd2lkdGgiOjJ9LCBnKTsKICAgIGNvbnN0IHJkID0g"
        "ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInJkLXRmIik7CiAgICBsZXQgcGg7CiAgICBpZiAobGFtID4gMC4wMikgICAgICAg"
        "cGggPSBbJ0knLCAgJ867Jmd0OzAg4oCUIGJyYW5jaGVzIHJvdGF0ZWQgNjDCsCwgb3JpZ2luIHVuc3RhYmxlJ107CiAgICBl"
        "bHNlIGlmIChsYW0gPCAtMC4wMikgcGggPSBbJ0lJSScsJ867Jmx0OzAg4oCUIGJyYW5jaGVzIGF0IDDCsC8xMjDCsC8yNDDC"
        "sCwgb3JpZ2luIHN0YWJsZSddOwogICAgZWxzZSAgICAgICAgICAgICAgICAgIHBoID0gWydJSScsICdvbnNldCDigJQgdGhy"
        "ZWUgYnJhbmNoZXMgY29sbGFwc2UgdGhyb3VnaCB0aGUgb3JpZ2luJ107CiAgICByZC5pbm5lckhUTUwgPSBgPHNwYW4gY2xh"
        "c3M9InBoIj5QaGFzZSAke3BoWzBdfTwvc3Bhbj4gwrcgzrsgPSAke2xhbS50b0ZpeGVkKDIpfSDCtyAke3BoWzFdfSDCtyBi"
        "cmFuY2hlcyBhcmUgc2FkZGxlcyB74oiSzrssIDPOu31gOwogIH0KCiAgLyogLS0tLS0tLS0tLSBUQUIgMiA6IGhleGFnb25h"
        "bCBjbG9zdXJlIC0tLS0tLS0tLS0gKi8KICBjb25zdCBoeCA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzdmctaGV4Iik7"
        "CiAgY29uc3QgTSA9IFtDT0wuZDYsIENPTC5kMywgQ09MLnoyXTsgICAgICAgICAgICAgIC8vIHRocmVlIG1vZGVzID0gdGhl"
        "IHRocmVlIHBoYXNlIGNvbG91cnMKICBmdW5jdGlvbiBkZWZzQXJyb3dzKCl7CiAgICBjb25zdCBkZWZzID0gbWsoImRlZnMi"
        "LCB7fSwgaHgpOwogICAgTS5mb3JFYWNoKChjLGkpID0+IHsKICAgICAgY29uc3QgbSA9IG1rKCJtYXJrZXIiLCB7aWQ6ImFo"
        "IitpLCB2aWV3Qm94OiIwIDAgMTAgMTAiLCByZWZYOjgsIHJlZlk6NSwKICAgICAgICBtYXJrZXJXaWR0aDo3LCBtYXJrZXJI"
        "ZWlnaHQ6Nywgb3JpZW50OiJhdXRvLXN0YXJ0LXJldmVyc2UifSwgZGVmcyk7CiAgICAgIG1rKCJwYXRoIiwge2Q6Ik0wIDAg"
        "TDEwIDUgTDAgMTAgeiIsIGZpbGw6Y30sIG0pOwogICAgfSk7CiAgfQogIGZ1bmN0aW9uIGFycm93KHAsIHgxLHkxLHgyLHky"
        "LCBpLCB3KXsKICAgIG1rKCJsaW5lIiwge3gxLHkxLHgyLHkyLCBzdHJva2U6TVtpXSwgInN0cm9rZS13aWR0aCI6d3x8Mi4y"
        "LAogICAgICAibWFya2VyLWVuZCI6InVybCgjYWgiK2krIikifSwgcCk7CiAgfQogIGZ1bmN0aW9uIGhleERyYXcoKXsKICAg"
        "IGh4LmlubmVySFRNTD0iIjsgZGVmc0Fycm93cygpOwogICAgY29uc3QgeWMgPSAxMzAsIEwgPSA2MjsKICAgIGNvbnN0IGFu"
        "ZyA9IFswLDEyMCwyNDBdLm1hcChkID0+IGQqTWF0aC5QSS8xODApOwogICAgLy8gKGEpIHRocmVlIG1vZGVzIHJhZGlhdGlu"
        "ZyBmcm9tIGEgbGVmdCBvcmlnaW4KICAgIGNvbnN0IG94ID0gOTY7CiAgICBsYWJlbChoeCwgInRocmVlIG1vZGVzIiwgb3gs"
        "IDMwLCBDT0wuZGltLCAibWlkZGxlIiwgMTEpOwogICAgbWsoImNpcmNsZSIsIHtjeDpveCwgY3k6eWMsIHI6Mi41LCBmaWxs"
        "OkNPTC5mYWludH0sIGh4KTsKICAgIGNvbnN0IGdBID0gbWsoImciLCB7fSwgaHgpOwogICAgYW5nLmZvckVhY2goKHQsaSk9"
        "PiBhcnJvdyhnQSwgb3gsIHljLCBveCArIEwqTWF0aC5jb3ModCksIHljIC0gTCpNYXRoLnNpbih0KSwgaSkpOwogICAgLy8g"
        "KGIpIHRpcC10by10YWlsIGNsb3NlZCB0cmlhbmdsZSAgKHN1bSA9IDApCiAgICBjb25zdCBieCA9IDMxMCwgYnkgPSB5YyAt"
        "IDM2OwogICAgbGFiZWwoaHgsICLOoyBr4bWiID0gMCAgKGNsb3NlZCkiLCBieCwgMzAsIENPTC5kNiwgIm1pZGRsZSIsIDEx"
        "KTsKICAgIGNvbnN0IHYgPSBhbmcubWFwKHQgPT4gW0wqTWF0aC5jb3ModCksIC1MKk1hdGguc2luKHQpXSk7CiAgICBsZXQg"
        "UCA9IFtieCwgYnldOyBjb25zdCBnQiA9IG1rKCJnIiwge30sIGh4KTsKICAgIGNvbnN0IHNlZyA9IFtdOwogICAgdi5mb3JF"
        "YWNoKCh2ZWMsaSk9PnsgY29uc3QgUT1bUFswXSt2ZWNbMF0sIFBbMV0rdmVjWzFdXTsgc2VnLnB1c2goW1AsUSxpXSk7IFA9"
        "UTsgfSk7CiAgICAvLyAoYykgaGV4YWdvbiBmcm9tIHRoZSA2IGRpcmVjdGlvbnMgKMKxbW9kZXMpCiAgICBjb25zdCBoeFgg"
        "PSA1MjQ7CiAgICBsYWJlbChoeCwgIjYgZGlyZWN0aW9ucyAowrFr4bWiKSIsIGh4WCwgMzAsIENPTC5kaW0sICJtaWRkbGUi"
        "LCAxMSk7CiAgICBjb25zdCBoZXhQdHM9W107CiAgICBmb3IobGV0IGs9MDtrPDY7aysrKXsgY29uc3QgdD0oayo2MCkqTWF0"
        "aC5QSS8xODA7IGhleFB0cy5wdXNoKFtoeFgrNTIqTWF0aC5jb3ModCksIHljLTUyKk1hdGguc2luKHQpXSk7IH0KICAgIG1r"
        "KCJwYXRoIiwge2Q6aGV4UHRzLm1hcCgocCxpKT0+KGk/IkwiOiJNIikrcFswXS50b0ZpeGVkKDEpKyIgIitwWzFdLnRvRml4"
        "ZWQoMSkpLmpvaW4oIiAiKSsiIFoiLAogICAgICBmaWxsOiJyZ2JhKDIyNywxNjksNTgsLjA1KSIsIHN0cm9rZTpDT0wubGlu"
        "ZSwgInN0cm9rZS13aWR0aCI6MS4yfSwgaHgpOwogICAgY29uc3QgZ0MgPSBtaygiZyIsIHt9LCBoeCk7CiAgICBmb3IobGV0"
        "IGs9MDtrPDY7aysrKXsgY29uc3QgdD0oayo2MCkqTWF0aC5QSS8xODA7CiAgICAgIG1rKCJsaW5lIiwge3gxOmh4WCwgeTE6"
        "eWMsIHgyOmh4WCs0NCpNYXRoLmNvcyh0KSwgeTI6eWMtNDQqTWF0aC5zaW4odCksCiAgICAgICAgc3Ryb2tlOk1bayUzXSwg"
        "InN0cm9rZS13aWR0aCI6MS42LCAic3Ryb2tlLW9wYWNpdHkiOi44NX0sIGdDKTsgfQogICAgbWsoImNpcmNsZSIsIHtjeDpo"
        "eFgsIGN5OnljLCByOjIuNSwgZmlsbDpDT0wuZmFpbnR9LCBoeCk7CgogICAgLy8gZHJhdyB0aGUgY2xvc2luZyB0cmlhbmds"
        "ZSAoYW5pbWF0ZWQgaWYgYWxsb3dlZCkKICAgIGNvbnN0IGRyYXdTZWcgPSAocykgPT4gYXJyb3coZ0IsIHNbMF1bMF0sIHNb"
        "MF1bMV0sIHNbMV1bMF0sIHNbMV1bMV0sIHNbMl0pOwogICAgaWYgKHJlZHVjZSl7IHNlZy5mb3JFYWNoKGRyYXdTZWcpOyB9"
        "CiAgICBlbHNlIHsgc2VnLmZvckVhY2goKHMsaSk9PiBzZXRUaW1lb3V0KCgpPT5kcmF3U2VnKHMpLCAyMjAqaSkpOyB9CiAg"
        "fQoKICAvKiAtLS0tLS0tLS0tIFRBQiAzIDogZGVsdGEgb24gdGhlIHRyYWNlIGF4aXMgLS0tLS0tLS0tLSAqLwogIGZ1bmN0"
        "aW9uIGRlbHRhRHJhdygpewogICAgY29uc3QgcyA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJzdmctZGVsdGEiKTsgcy5p"
        "bm5lckhUTUw9IiI7CiAgICBjb25zdCBwaGkgPSBDKCItLXBoaSIpfHwiI2U2YjI0YSI7CiAgICBjb25zdCB5YyA9IDE1MCwg"
        "THggPSA2MCwgUnggPSA1NjAsIHRhdSA9IDAuNjE4MDMzOTg4NzsKICAgIGNvbnN0IGFYID0gYSA9PiBMeCArIChhKzIpLzQg"
        "KiAoUngtTHgpOwogICAgbGFiZWwocywiaW50ZWdlciB0cmFjZSDin7ogbGF0dGljZSBzeW1tZXRyeSDCtyBvcmRlciA1IGxh"
        "bmRzIGF0IHRoZSBnb2xkZW4gdmFsdWUsIG9mZi1sYXR0aWNlIixMeCwyOCxDT0wuZGltLCJzdGFydCIsMTEpOwogICAgbWso"
        "ImxpbmUiLHt4MTpMeCx5MTp5Yyx4MjpSeCx5Mjp5YyxzdHJva2U6Q09MLmF4aXMsInN0cm9rZS13aWR0aCI6MS40fSxzKTsK"
        "ICAgIGxhYmVsKHMsImEgPSDiiJIyIixMeCx5YyszNCxDT0wuZmFpbnQsInN0YXJ0IiwxMC41KTsKICAgIGxhYmVsKHMsImEg"
        "PSAyICAodHJhY2UpIixSeCx5YyszNCxDT0wuZmFpbnQsImVuZCIsMTAuNSk7CiAgICBjb25zdCBvcmRlcnMgPSB7Ii0yIjoy"
        "LCItMSI6MywiMCI6NCwiMSI6NiwiMiI6MX07CiAgICBbLTIsLTEsMCwxLDJdLmZvckVhY2goYT0+ewogICAgICBtaygibGlu"
        "ZSIse3gxOmFYKGEpLHkxOnljLTUseDI6YVgoYSkseTI6eWMrNSxzdHJva2U6Q09MLmRpbSwic3Ryb2tlLXdpZHRoIjoxLjR9"
        "LHMpOwogICAgICBtaygicmVjdCIse3g6YVgoYSktMyx5OnljLTMsd2lkdGg6NixoZWlnaHQ6NixmaWxsOkNPTC5kMywiZmls"
        "bC1vcGFjaXR5IjouODV9LHMpOwogICAgICBsYWJlbChzLCJuPSIrb3JkZXJzW1N0cmluZyhhKV0sYVgoYSkseWMrMjAsQ09M"
        "LmRpbSwibWlkZGxlIiwxMC41KTsKICAgIH0pOwogICAgbWsoImNpcmNsZSIse2N4OmFYKDEpLGN5OnljLHI6NixmaWxsOkNP"
        "TC5kMyxzdHJva2U6IiMwZTE2MzEiLCJzdHJva2Utd2lkdGgiOjEuNX0scyk7CiAgICBsYWJlbChzLCJvcmRlciA2IMK3IM62"
        "4oKGIGNsb3N1cmUiLGFYKDEpKzEwLHljLTQ0LENPTC5kMywic3RhcnQiLDExKTsKICAgIG1rKCJjaXJjbGUiLHtjeDphWCh0"
        "YXUpLGN5OnljLHI6NixmaWxsOnBoaSxzdHJva2U6IiMwZTE2MzEiLCJzdHJva2Utd2lkdGgiOjEuNX0scyk7CiAgICBsYWJl"
        "bChzLCJvcmRlciA1IMK3IGZvcmJpZGRlbiIsYVgodGF1KS05LHljLTYyLHBoaSwiZW5kIiwxMSk7CiAgICBsYWJlbChzLCJh"
        "ID0gz4bigbvCuSA9IM+EIixhWCh0YXUpLTkseWMtNDgscGhpLCJlbmQiLDEwLjUpOwogICAgY29uc3QgYjE9YVgodGF1KSwg"
        "YjI9YVgoMSksIGJ5PXljLTIwOwogICAgbWsoInBhdGgiLHtkOiJNIitiMSsiICIrKHljLTgpKyIgTCIrYjErIiAiK2J5KyIg"
        "TCIrYjIrIiAiK2J5KyIgTCIrYjIrIiAiKyh5Yy04KSxmaWxsOiJub25lIixzdHJva2U6cGhpLCJzdHJva2Utd2lkdGgiOjEu"
        "NH0scyk7CiAgICBsYWJlbChzLCLOlCA9IDHiiJLPhCA9IM+G4oG7wrIg4omIIDAuMzgyIiwoYjErYjIpLzIsYnktNyxwaGks"
        "Im1pZGRsZSIsMTEpOwogIH0KCiAgLyogLS0tLS0tLS0tLSBUQUIgNCA6IHRoZSBaRlAgaGVsaXggKHosIHIsIHpfYykgLS0t"
        "LS0tLS0tLSAqLwogIGZ1bmN0aW9uIGhlbGl4RHJhdygpewogICAgY29uc3QgcyA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlk"
        "KCJzdmctaGVsaXgiKTsgcy5pbm5lckhUTUw9IiI7CiAgICBjb25zdCBnb2xkID0gQygiLS1waGkiKXx8IiNlNmIyNGEiLCB0"
        "ZWFsID0gQ09MLmQzOwogICAgY29uc3QgcGhpPSgxK01hdGguc3FydCg1KSkvMiwgZ2FwPU1hdGgucG93KHBoaSwtNCksCiAg"
        "ICAgICAgICBLYz1NYXRoLnNxcnQoMS1nYXApLCB6Yz1NYXRoLnNxcnQoMykvMiwgZGVsdGE9TWF0aC5wb3cocGhpLC0yKSwg"
        "dGF1PTEvcGhpOwogICAgY29uc3QgY3g9MzAwLCByUz0xNjUsIHpZPXo9PjM0MC16KjMwMCwgck9mPXo9Pih6PD16Yz9LYypN"
        "YXRoLnNxcnQoei96Yyk6S2MpOwogICAgLy8gY2VudHJhbCBheGlzCiAgICBtaygibGluZSIse3gxOmN4LHkxOnpZKDApLHgy"
        "OmN4LHkyOnpZKDEuMDMpLHN0cm9rZTpDT0wuYXhpcywic3Ryb2tlLXdpZHRoIjoxfSxzKTsKICAgIGxhYmVsKHMsInoiLGN4"
        "LTkselkoMS4wMyktMixDT0wuZmFpbnQsIm1pZGRsZSIsMTEpOwogICAgbGFiZWwocywiMCIsY3gtMTAselkoMCkrNCxDT0wu"
        "ZmFpbnQsImVuZCIsMTApOwogICAgbGFiZWwocywiMSIsY3gtMTAselkoMSkrNCxDT0wuZmFpbnQsImVuZCIsMTApOwogICAg"
        "bGFiZWwocywiciIsY3grck9mKDEpKnJTKzEwLHpZKDEpKzQsQ09MLmZhaW50LCJzdGFydCIsMTEpOwogICAgLy8gZW52ZWxv"
        "cGUgKGNvbnN0cnVjdGlvbiwgZGFzaGVkKQogICAgY29uc3QgZW52PXNnbj0+e2xldCBkPSIiO2ZvcihsZXQgaT0wO2k8PTEy"
        "MDtpKyspe2NvbnN0IHo9aS8xMjAseD1jeCtzZ24qck9mKHopKnJTO2QrPShpPyJMIjoiTSIpK3gudG9GaXhlZCgxKSsiICIr"
        "elkoeikudG9GaXhlZCgxKSsiICI7fXJldHVybiBkO307CiAgICBtaygicGF0aCIse2Q6ZW52KDEpLGZpbGw6Im5vbmUiLHN0"
        "cm9rZTpDT0wubGluZSwic3Ryb2tlLXdpZHRoIjoxLjIsInN0cm9rZS1kYXNoYXJyYXkiOiI0IDQifSxzKTsKICAgIG1rKCJw"
        "YXRoIix7ZDplbnYoLTEpLGZpbGw6Im5vbmUiLHN0cm9rZTpDT0wubGluZSwic3Ryb2tlLXdpZHRoIjoxLjIsInN0cm9rZS1k"
        "YXNoYXJyYXkiOiI0IDQifSxzKTsKICAgIC8vIGhlbGl4IHN0cmFuZCAoY29uc3RydWN0aW9uIHNjYWZmb2xkLCBtdXRlZCkK"
        "ICAgIGxldCBoZD0iIjtmb3IobGV0IGk9MDtpPD00MDA7aSsrKXtjb25zdCB6PWkvNDAwLHRoPTIqTWF0aC5QSSp6L2RlbHRh"
        "LHg9Y3grck9mKHopKnJTKk1hdGguY29zKHRoKTtoZCs9KGk/IkwiOiJNIikreC50b0ZpeGVkKDEpKyIgIit6WSh6KS50b0Zp"
        "eGVkKDEpKyIgIjt9CiAgICBtaygicGF0aCIse2Q6aGQsZmlsbDoibm9uZSIsc3Ryb2tlOkNPTC5mYWludCwic3Ryb2tlLXdp"
        "ZHRoIjoxLjMsInN0cm9rZS1vcGFjaXR5IjouODV9LHMpOwogICAgLy8gZm9yY2VkIGxhbmRtYXJrIHJpbmdzIChzb2xpZCwg"
        "YnkgZmllbGQpCiAgICBjb25zdCByb3NlPSIjZGQ4NmE2IiwgaWduPU1hdGguU1FSVDItMC41OwogICAgY29uc3QgcmluZz0o"
        "eixjb2wsYm9sZCk9Pm1rKCJlbGxpcHNlIix7Y3g6Y3gsY3k6elkoeikscng6KHJPZih6KSpyUykudG9GaXhlZCgxKSxyeTpi"
        "b2xkPzY6NCxmaWxsOiJub25lIixzdHJva2U6Y29sLCJzdHJva2Utd2lkdGgiOmJvbGQ/MjoxLjV9LHMpOwogICAgcmluZyh0"
        "YXUsZ29sZCxmYWxzZSk7IHJpbmcoemMsdGVhbCx0cnVlKTsgcmluZyhpZ24scm9zZSxmYWxzZSk7IHJpbmcoMSxDT0wuaW5r"
        "LGZhbHNlKTsKICAgIGNvbnN0IGxhYj0oeix0LGNvbCk9PmxhYmVsKHMsdCxjeCtyT2YoeikqclMrMTEselkoeikrMyxjb2ws"
        "InN0YXJ0IiwxMSk7CiAgICBsYWIodGF1LCLPhCA9IM+G4oG7wrkgICAo4oiaNSkiLGdvbGQpOwogICAgbGFiKHpjLCJ6X2Mg"
        "PSDiiJozLzIgICAo4oiaMykiLHRlYWwpOwogICAgbGFiKGlnbiwiaWduaXRpb24gPSDiiJoy4oiSwr0gICAo4oiaMikiLHJv"
        "c2UpOwogICAgbGFiKDEsIjEgICAoVU5JVFkpIixDT0wuaW5rKTsKICAgIC8vIGRlbHRhIHdlaWdodCBicmFjZSAobGVmdCkK"
        "ICAgIGNvbnN0IGJ4PTgyLHkwPXpZKDApLHkxPXpZKGRlbHRhKTsKICAgIG1rKCJwYXRoIix7ZDoiTSIrKGJ4KzYpKyIgIit5"
        "MCsiIEwiK2J4KyIgIit5MCsiIEwiK2J4KyIgIit5MSsiIEwiKyhieCs2KSsiICIreTEsZmlsbDoibm9uZSIsc3Ryb2tlOmdv"
        "bGQsInN0cm9rZS13aWR0aCI6MS40fSxzKTsKICAgIGxhYmVsKHMsIs6UID0gz4bigbvCsiIsYngtNCwoeTAreTEpLzItNSxn"
        "b2xkLCJlbmQiLDExKTsKICAgIGxhYmVsKHMsInBpdGNoIC8gd2VpZ2h0IixieC00LCh5MCt5MSkvMis5LENPTC5mYWludCwi"
        "ZW5kIiw5LjUpOwogICAgbGFiZWwocywiei1yaXNlIHBlciB0dXJuIixieC00LCh5MCt5MSkvMisyMSxDT0wuZmFpbnQsImVu"
        "ZCIsOS41KTsKICAgIC8vIG5vdGVzCiAgICBsYWJlbChzLCJmcm9tIEzigoQgPSA3OiAgIOKImjMgPSDiiJooTOKChOKIkjQp"
        "ICAgwrcgICDiiJoyID0g4oiaKEzigoQrMSkvMiAgIMK3ICAg4oiaNSA9IOKImihM4oKEwrLiiJI0KS8zIixjeCwyNixDT0wu"
        "ZGltLCJtaWRkbGUiLDExKTsKICAgIGxhYmVsKHMsInRocmVlIGF4ZXMsIG9uZSBzcGFjZSDCtyByaW5ncyBmb3JjZWQgKHVu"
        "ZGVyIEzigoQpIMK3IGhlbGl4ID0gb25lIHJlcHJlc2VudGF0aW9uIMK3IHR1cm4gPSBnb2xkZW4gYW5nbGUgMTM3LjXCsCIs"
        "Y3gselkoMCkrMzQsQ09MLmZhaW50LCJtaWRkbGUiLDkuNSk7CiAgfQoKICAvKiAtLS0tLS0tLS0tIHJlbGF0aW9uYWwgaHVi"
        "IC0tLS0tLS0tLS0gKi8KICBmdW5jdGlvbiByZWxEcmF3KCl7CiAgICBjb25zdCBzID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5"
        "SWQoInN2Zy1yZWwiKTsgaWYoIXMpIHJldHVybjsgcy5pbm5lckhUTUw9IiI7CiAgICBjb25zdCBnb2xkID0gQygiLS1waGki"
        "KXx8IiNlNmIyNGEiLCB0ZWFsID0gQ09MLmQzLCByb3NlPSIjZGQ4NmE2IiwgcmVsID0gQygiLS1yZWwiKXx8IiNhNmEyZTYi"
        "OwogICAgY29uc3QgY3g9MzEwLCBjeT0xMDg7CiAgICBsYWJlbChzLCJvbmUgZm9yY2VkIHNlZWQgIOKGkiAgdGhyZWUgZm9y"
        "Y2VkIGF4ZXMgKGVhY2ggZm9yY2VkIHVuZGVyIHRoZSBzZWVkKSIsY3gsMjgsQ09MLmRpbSwibWlkZGxlIiwxMSk7CiAgICBt"
        "aygicmVjdCIse3g6Y3gtOTQseTpjeS0yMyx3aWR0aDoxODgsaGVpZ2h0OjQ2LHJ4OjksZmlsbDoicmdiYSgxNjYsMTYyLDIz"
        "MCwuMTApIixzdHJva2U6cmVsLCJzdHJva2Utd2lkdGgiOjEuNX0scyk7CiAgICBsYWJlbChzLCJM4oKEID0gz4bigbQgKyDP"
        "huKBu+KBtCA9IDciLGN4LGN5LTIsQ09MLmluaywibWlkZGxlIiwxMyk7CiAgICBsYWJlbChzLCJmb3JjZWQgZnJvbSDPhiIs"
        "Y3gsY3krMTUsQ09MLmZhaW50LCJtaWRkbGUiLDEwKTsKICAgIGNvbnN0IG5vZGVzPVsKICAgICAge3g6MTQwLHk6MjUwLGNv"
        "bDpnb2xkLHIxOiLiiJo1ID0g4oiaKEzigoTCsuKIkjQpLzMiLHIyOiLihpIgz4YgPSAoMSviiJo1KS8yIn0sCiAgICAgIHt4"
        "OjMxMCx5OjI2Mixjb2w6dGVhbCxyMToi4oiaMyA9IOKImihM4oKE4oiSNCkiLCAgIHIyOiLihpIgel9jID0g4oiaMy8yICAo"
        "bGVucykifSwKICAgICAge3g6NDgwLHk6MjUwLGNvbDpyb3NlLHIxOiLiiJoyID0g4oiaKEzigoQrMSkvMiIsIHIyOiLihpIg"
        "aWduaXRpb24gPSDiiJoy4oiSwr0ifSwKICAgIF07CiAgICBub2Rlcy5mb3JFYWNoKG49PnsKICAgICAgbWsoImxpbmUiLHt4"
        "MTpjeCx5MTpjeSsyMyx4MjpuLngseTI6bi55LTI2LHN0cm9rZTpuLmNvbCwic3Ryb2tlLXdpZHRoIjoxLjYsInN0cm9rZS1v"
        "cGFjaXR5IjouODV9LHMpOwogICAgICBtaygiY2lyY2xlIix7Y3g6bi54LGN5Om4ueS0xOSxyOjUuNSxmaWxsOm4uY29sLHN0"
        "cm9rZToiIzBlMTYzMSIsInN0cm9rZS13aWR0aCI6MS41fSxzKTsKICAgICAgbGFiZWwocyxuLnIxLG4ueCxuLnksbi5jb2ws"
        "Im1pZGRsZSIsMTIpOwogICAgICBsYWJlbChzLG4ucjIsbi54LG4ueSsxNixDT0wuZGltLCJtaWRkbGUiLDExKTsKICAgIH0p"
        "OwogICAgbGFiZWwocywiYWxsIHRocmVlIGluICDihJoo4oiaMiwg4oiaMywg4oiaNSkgIOKAlCAgb25lIHNwYWNlLCB0aHJl"
        "ZSBpbmRlcGVuZGVudCBheGVzIixjeCwzMTQsQ09MLmZhaW50LCJtaWRkbGUiLDExKTsKICB9CgogIC8qIC0tLS0tLS0tLS0g"
        "dGFicyAtLS0tLS0tLS0tICovCiAgY29uc3QgdGFicyA9IFsuLi5kb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCdbcm9sZT0i"
        "dGFiIl0nKV07CiAgY29uc3QgcGFuZWxzID0gdGFicy5tYXAodCA9PiBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCh0LmdldEF0"
        "dHJpYnV0ZSgiYXJpYS1jb250cm9scyIpKSk7CiAgbGV0IGhleERyYXduID0gZmFsc2U7CiAgZnVuY3Rpb24gc2VsZWN0KGks"
        "IGZvY3VzKXsKICAgIHRhYnMuZm9yRWFjaCgodCxqKT0+ewogICAgICBjb25zdCBvbiA9IGk9PT1qOwogICAgICB0LnNldEF0"
        "dHJpYnV0ZSgiYXJpYS1zZWxlY3RlZCIsIG9uKTsKICAgICAgdC50YWJJbmRleCA9IG9uID8gMCA6IC0xOwogICAgICBwYW5l"
        "bHNbal0uY2xhc3NMaXN0LnRvZ2dsZSgiYWN0aXZlIiwgb24pOwogICAgICBwYW5lbHNbal0uaGlkZGVuID0gIW9uOwogICAg"
        "fSk7CiAgICBpZiAoaT09PTIpeyBoZXhEcmF3KCk7IGhleERyYXduPXRydWU7IH0KICAgIGlmIChpPT09MykgZGVsdGFEcmF3"
        "KCk7CiAgICBpZiAoaT09PTQpIGhlbGl4RHJhdygpOwogICAgaWYgKGk9PT01KSByZWxEcmF3KCk7CiAgICBpZiAoZm9jdXMp"
        "IHRhYnNbaV0uZm9jdXMoKTsKICB9CiAgdGFicy5mb3JFYWNoKCh0LGkpPT57CiAgICB0LmFkZEV2ZW50TGlzdGVuZXIoImNs"
        "aWNrIiwgKCk9PnNlbGVjdChpKSk7CiAgICB0LmFkZEV2ZW50TGlzdGVuZXIoImtleWRvd24iLCBlPT57CiAgICAgIGlmIChl"
        "LmtleT09PSJBcnJvd1JpZ2h0Inx8ZS5rZXk9PT0iQXJyb3dEb3duIil7IGUucHJldmVudERlZmF1bHQoKTsgc2VsZWN0KChp"
        "KzEpJXRhYnMubGVuZ3RoLCB0cnVlKTsgfQogICAgICBpZiAoZS5rZXk9PT0iQXJyb3dMZWZ0IiB8fGUua2V5PT09IkFycm93"
        "VXAiKSAgeyBlLnByZXZlbnREZWZhdWx0KCk7IHNlbGVjdCgoaS0xK3RhYnMubGVuZ3RoKSV0YWJzLmxlbmd0aCwgdHJ1ZSk7"
        "IH0KICAgICAgaWYgKGUua2V5PT09IkhvbWUiKXsgZS5wcmV2ZW50RGVmYXVsdCgpOyBzZWxlY3QoMCx0cnVlKTsgfQogICAg"
        "ICBpZiAoZS5rZXk9PT0iRW5kIikgeyBlLnByZXZlbnREZWZhdWx0KCk7IHNlbGVjdCh0YWJzLmxlbmd0aC0xLHRydWUpOyB9"
        "CiAgICB9KTsKICB9KTsKCiAgLyogLS0tLS0tLS0tLSBpbml0IC0tLS0tLS0tLS0gKi8KICBwZlN0YXRpYygpOyAgcGZVcGRh"
        "dGUoMC42KTsKICB0ZlN0YXRpYygpOyAgdGZVcGRhdGUoLTAuOSk7CiAgZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoInNsLXBm"
        "IikuYWRkRXZlbnRMaXN0ZW5lcigiaW5wdXQiLCBlID0+IHBmVXBkYXRlKCtlLnRhcmdldC52YWx1ZS8xMDApKTsKICBkb2N1"
        "bWVudC5nZXRFbGVtZW50QnlJZCgic2wtdGYiKS5hZGRFdmVudExpc3RlbmVyKCJpbnB1dCIsIGUgPT4gdGZVcGRhdGUoK2Uu"
        "dGFyZ2V0LnZhbHVlLzEwMCkpOwogIGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCJyZXBsYXkiKS5hZGRFdmVudExpc3RlbmVy"
        "KCJjbGljayIsIGhleERyYXcpOwp9KSgpOwo8L3NjcmlwdD4KPC9ib2R5Pgo8L2h0bWw+Cg=="
    ),
}

# --- canonical extractor for the embedded <pre class="src" id="src-*-py"> blocks ----
# (used identically at BUILD time to compute per-block SHA-256 and at RUN time to
#  re-derive the blocks; keeping one definition guarantees the digests line up.)
import re as _hx_re
import html as _hx_html

_SRC_RE = _hx_re.compile(
    r'<pre class="src" id="(src-[^"]+?)">\s*<code>(.*?)</code>\s*</pre>',
    _hx_re.DOTALL)

def _html_script_name(idattr):
    core = idattr[len("src-"):]
    if core.endswith("-py"):
        core = core[:-3]
    return core.replace("-", "_") + ".py"

def extract_html_scripts(html_text):
    """Ordered {filename: source} for each embedded Python block, in document order.
    Normalization is fixed and shared with the builder: HTML-unescape the block body,
    then ensure exactly one trailing newline."""
    out = {}
    for idattr, body in _SRC_RE.findall(html_text):
        code = _hx_html.unescape(body)
        if not code.endswith("\n"):
            code += "\n"
        out[_html_script_name(idattr)] = code
    return out


def _decode(name):
    """Return (raw_bytes, expected_sha256, actual_sha256) for an embedded script."""
    digest, blob = EMBEDDED[name]
    raw = base64.b64decode(blob)
    return raw, digest, hashlib.sha256(raw).hexdigest()

# --dump DIR: write the decoded sources back to disk (provenance / recoverability) and exit.
if "--dump" in sys.argv:
    _i = sys.argv.index("--dump")
    _dst = sys.argv[_i + 1] if _i + 1 < len(sys.argv) else "."
    os.makedirs(_dst, exist_ok=True)
    for _nm in EMBEDDED:
        _raw, _want, _got = _decode(_nm)
        with open(os.path.join(_dst, _nm), "wb") as _fh:
            _fh.write(_raw)
        print(f"  wrote {_nm:<34} sha256 {'ok' if _want == _got else 'SHA-MISMATCH'}")
    for _hn, (_hw, _hb) in EMBEDDED_HTML.items():
        _hraw = base64.b64decode(_hb)
        with open(os.path.join(_dst, _hn), "wb") as _fh:
            _fh.write(_hraw)
        _hok = hashlib.sha256(_hraw).hexdigest() == _hw
        print(f"  wrote {_hn:<34} sha256 {'ok' if _hok else 'SHA-MISMATCH'}")
        for _sn, _ssrc in extract_html_scripts(_hraw.decode("utf-8")).items():
            with open(os.path.join(_dst, _sn), "w", encoding="utf-8") as _fh:
                _fh.write(_ssrc)
            print(f"    wrote {_sn:<32} (extracted from {_hn})")
    sys.exit(0)

def _run_one(path, name, want_sha, src_text, indent):
    """Verify one script's SHA-256, run it as __main__ (stdout captured), gate on
    no-exception AND zero FAIL tokens. Records into `fails`. Returns nothing."""
    got = hashlib.sha256(src_text.encode("utf-8")).hexdigest()
    sha_ok = (src_text != "" and want_sha == got)
    record(f"{name}:sha256", sha_ok)
    buf, err = io.StringIO(), None
    if sha_ok:
        try:
            with contextlib.redirect_stdout(buf):
                runpy.run_path(path, run_name="__main__")
        except SystemExit as e:               # scripts now exit nonzero on a failed check
            code = e.code
            if isinstance(code, bool):
                code = int(code)
            if code not in (0, None):
                err = SystemExit(f"nonzero exit ({code})")
        except Exception as e:                # any raised exception is a hard failure
            err = e
    out    = buf.getvalue()
    n_fail = len(_re.findall(r"\bFAIL\b", out))
    ran_ok = sha_ok and err is None
    clean  = ran_ok and n_fail == 0
    record(f"{name}:run", ran_ok)
    if ran_ok:
        record(f"{name}:checks", n_fail == 0)
    label = name.split(":", 1)[-1]
    print(f"{indent}{label:<30}{('ok' if sha_ok else 'BAD'):<9}"
          f"{('ok' if ran_ok else 'RAISED'):<9}{n_fail:<10}{'PASS' if clean else 'FAIL'}")
    if err is not None:
        print(f"{indent}    exception: {type(err).__name__}: {err}")
    if VERBOSE or not clean:
        tag = "captured stdout" if clean else "captured stdout (failure context)"
        print(f"{indent}    --- {label} {tag} ---")
        for line in out.rstrip("\n").splitlines():
            print(f"{indent}    | {line}")
        print(f"{indent}    --- end {label} ---")

def run_embedded():
    """LAYER 0: the six standalone project scripts (each written to its own temp file
    and run as __main__)."""
    print("="*92)
    print("LAYER 0  -- embedded project scripts: verify SHA-256, then RUN each (isolated)")
    print("="*92)
    print(f"{'script':<32}{'sha256':<9}{'run':<9}{'FAIL tok':<10}{'verdict'}")
    tmp = tempfile.mkdtemp(prefix="zfp_proj_")
    try:
        for nm in EMBEDDED:
            raw, want, _got = _decode(nm)
            path = os.path.join(tmp, nm)
            with open(path, "wb") as fh:
                fh.write(raw)
            _run_one(path, f"script:{nm}", want, raw.decode("utf-8"), indent="")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def run_html_embedded():
    """LAYER 0H: scripts embedded INSIDE the HTML. Verify the HTML digest, re-derive
    the Python blocks, verify each block's digest, then run all of them together in
    one temp dir on sys.path so the meet/join cross-import resolves."""
    print("="*92)
    print("LAYER 0H -- scripts embedded INSIDE L4_helix_simulator__py_guided_.html")
    print("="*92)
    (html_name, (want_html, blob)), = EMBEDDED_HTML.items()
    raw = base64.b64decode(blob)
    html_ok = hashlib.sha256(raw).hexdigest() == want_html
    record(f"html:{html_name}:sha256", html_ok)
    print(f"  source HTML: {html_name}   sha256 {'ok' if html_ok else 'BAD'}")

    scripts = extract_html_scripts(raw.decode("utf-8"))
    count_ok = (len(scripts) == len(HTML_SCRIPTS))
    record("html:block-count", count_ok)
    print(f'  parsed {len(scripts)} <pre class="src"> blocks (expected {len(HTML_SCRIPTS)})  '
          f"{'ok' if count_ok else 'MISMATCH'}")
    print(f"  {'script':<30}{'sha256':<9}{'run':<9}{'FAIL tok':<10}{'verdict'}")

    tmp = tempfile.mkdtemp(prefix="zfp_html_")
    for nm, _sha in HTML_SCRIPTS:                      # materialize all before running
        with open(os.path.join(tmp, nm), "w", encoding="utf-8") as fh:
            fh.write(scripts.get(nm, ""))
    sys.path.insert(0, tmp)
    mods_before = set(sys.modules)
    try:
        for nm, want in HTML_SCRIPTS:                  # document order: lattice before grid
            _run_one(os.path.join(tmp, nm), f"html-script:{nm}", want,
                     scripts.get(nm, ""), indent="  ")
    finally:
        for m in set(sys.modules) - mods_before:       # drop the imported sibling module
            sys.modules.pop(m, None)
        if tmp in sys.path:
            sys.path.remove(tmp)
        shutil.rmtree(tmp, ignore_errors=True)

    # cross-source: any script shipped BOTH standalone (LAYER 0) and inside the HTML
    # must be byte-identical across the two snapshots -- the double-embed becomes a drift check.
    _html_pins = dict(HTML_SCRIPTS)
    _overlap = [n for n in EMBEDDED if n in _html_pins]
    if _overlap:
        print(f"  {'cross-source (standalone vs in-HTML)':<38}{'verdict'}")
        for _nm in _overlap:
            _same = EMBEDDED[_nm][0] == _html_pins[_nm]
            record(f"xsource:{_nm}", _same)
            print(f"    {_nm:<36}{'consistent' if _same else 'DIVERGED'}")

run_embedded()
print()
run_html_embedded()

if SCRIPTS_ONLY:
    print("\n" + "="*92)
    if fails:
        print(f"RESULT (embedded scripts only): {len(fails)} check(s) did NOT pass cleanly:")
        for f in fails:
            print(f"   - {f}")
    else:
        print("RESULT (embedded scripts only): six project scripts + the HTML "
              "(+ its four blocks) all verified (SHA-256) and ran clean.")
    print("="*92)
    sys.exit(1 if fails else 0)


print("="*92)
print("LAYER A  -- the six Section-2 constants: forced two ways + minimality + value pin")
print("="*92)
print(f"{'name':<9}{'closed form':<16}{'stated minpoly':<18}{'annih':<7}{'irred':<7}"
      f"{'=minpoly':<10}{'value(15dp)':<18}{'pin':<9}{'vpin'}")
core = [
    ("TAU",  TAU,  "phi^-1",      x**2 + x - 1,      Rational(61803, 100000)),
    ("Z_C",  ZC,   "sqrt3/2",     4*x**2 - 3,        Rational(86603, 100000)),
    ("GAP",  GAP,  "phi^-4",      x**2 - 7*x + 1,    Rational(14590, 100000)),
    ("K",    K,    "sqrt(1-g)",   x**4 + 5*x**2 - 5, Rational(92418, 100000)),
    ("IGN",  IGN,  "sqrt2-1/2",   4*x**2 + 4*x - 7,  Rational(91421, 100000)),
    ("CRIT", CRIT, "phi^2/3",     9*x**2 - 9*x + 1,  Rational(87268, 100000)),
]
for nm, c, cf, P, pin in core:
    annih = simplify(P.subs(x, c)) == 0
    irred = is_irred(P)
    ismin = monic(P) == monic(minpoly(c, x))
    vpin  = abs(c.evalf(40) - pin.evalf(40)) < Rational(1, 100000).evalf(40)
    record(f"{nm}:annih", annih); record(f"{nm}:irred", irred)
    record(f"{nm}:ismin", ismin); record(f"{nm}:vpin", vpin)
    print(f"{nm:<9}{cf:<16}{str(P):<18}{record('', annih):<7}{record('', irred):<7}"
          f"{record('', ismin):<10}{str(c.evalf(15)):<18}{str(float(pin)):<9}{record('', vpin)}")

# closed-form (radical) cross-checks -- the exact forms displayed in spectral_atlas.html
print("  radical-form cross-checks (atlas closed forms, residual 0):")
radforms = [
    ("tau   = (sqrt5-1)/2",   simplify(TAU  - (sqrt(5)-1)/2) == 0),
    ("gap   = (7-3sqrt5)/2",  simplify(GAP  - (7 - 3*sqrt(5))/2) == 0),
    ("crit  = (3+sqrt5)/6",   simplify(CRIT - (3 + sqrt(5))/6) == 0),
    ("ign   = (2sqrt2-1)/2",  simplify(IGN  - (2*sqrt(2)-1)/2) == 0),
    ("K     = 5^(1/4)/phi",   simplify(K    - 5**Rational(1, 4)/PHI) == 0),
]
for nm, c in radforms:
    record(nm, c); print(f"    {nm:<26} {record('', c)}")

# =====================================================================================
print("\n" + "="*92)
print("LAYER B  -- the nine helix landmarks (zfp_helix.py / simulator): minpoly + pin + order")
print("="*92)
ACT  = 1 - GAP
CONS = K + TAU**2 * (1 - K)
RES  = K + TAU * (1 - K)
# name : (value, stated minpoly, doc decimal[10dp])
landmarks = [
    ("PARADOX  tau",         TAU,             x**2 + x - 1,                       Rational(6180339887, 10**10)),
    ("ACTIVATION 1-gap=K^2", ACT,             x**2 + 5*x - 5,                     Rational(8541019662, 10**10)),
    ("LENS z_c",             ZC,              4*x**2 - 3,                         Rational(8660254038, 10**10)),
    ("CRITICAL phi^2/3",     CRIT,            9*x**2 - 9*x + 1,                   Rational(8726779962, 10**10)),
    ("IGNITION sqrt2-1/2",   IGN,             4*x**2 + 4*x - 7,                   Rational(9142135624, 10**10)),
    ("K-FORM sqrt(1-gap)",   K,               x**4 + 5*x**2 - 5,                  Rational(9241763718, 10**10)),
    ("CONSOLIDATION",        CONS,            x**4 - 6*x**3 + 26*x**2 - 16*x - 4, Rational(9531384206, 10**10)),
    ("RESONANCE",            RES,             x**4 + 2*x**3 + 39*x**2 - 52*x + 11, Rational(9710379512, 10**10)),
    ("UNITY",                sp.Integer(1),   x - 1,                              Rational(1)),
]
print(f"{'name':<22}{'stated minpoly':<36}{'=minpoly':<10}{'value(12dp)':<16}{'vpin'}")
prev = None; order_ok = True
for nm, c, P, doc in landmarks:
    ismin = monic(P) == monic(minpoly(c, x))
    vpin  = abs(c.evalf(40) - doc.evalf(40)) < Rational(1, 10**9).evalf(40)
    record(f"{nm}:ismin", ismin); record(f"{nm}:vpin", vpin)
    if prev is not None:
        order_ok &= (c.evalf(40) > prev)
    prev = c.evalf(40)
    print(f"{nm:<22}{str(P):<36}{record('', ismin):<10}{str(c.evalf(12)):<16}{record('', vpin)}")
record("ordering strict-increasing", order_ok)
print(f"  Theorem-10.1 ordering PARADOX < ... < UNITY strictly increasing   {record('', order_ok)}")

# golden cascade off K, and the activation identity
record("ACT=K^2",            simplify(ACT - K**2) == 0)
record("CONS-K=tau^2(1-K)",  simplify((CONS - K) - TAU**2*(1 - K)) == 0)
record("RES-K=tau(1-K)",     simplify((RES - K)  - TAU*(1 - K)) == 0)
print(f"  activation == K^2 (exact)                                        {record('', simplify(ACT-K**2)==0)}")
print(f"  gaps off K scale as (1, tau, tau^2)*(1-K): golden cascade        "
      f"{record('', simplify((CONS-K)-TAU**2*(1-K))==0 and simplify((RES-K)-TAU*(1-K))==0)}")

# DELTA = phi^-2 = 1 - tau, minpoly x^2-3x+1, 1/DELTA = phi^2 = phi+1
record("DELTA=phi^-2=1-tau",     simplify(DELTA - (1 - TAU)) == 0)
record("minpoly(DELTA)=x^2-3x+1", monic(minpoly(DELTA, x)) == monic(x**2 - 3*x + 1))
record("1/DELTA=phi^2=phi+1",    simplify(1/DELTA - (PHI + 1)) == 0)
print(f"  DELTA = phi^-2 = 1-tau ; minpoly = {minpoly(DELTA,x)} ; 1/DELTA = phi^2 = phi+1   "
      f"{record('', simplify(DELTA-(1-TAU))==0 and monic(minpoly(DELTA,x))==monic(x**2-3*x+1) and simplify(1/DELTA-(PHI+1))==0)}")

# radius-law FORCED anchors (the form r=K*sqrt(z/z_c) itself is REPRESENTATION, not gated)
record("r(0)=0",   simplify(K*sqrt(Rational(0)/ZC)) == 0)
record("r(z_c)=K", simplify(K*sqrt(ZC/ZC) - K) == 0)
print(f"  radius anchors r(0)=0 and r(z_c)=K (form r=K*sqrt(z/z_c) is REPRESENTATION)   "
      f"{record('', simplify(K*sqrt(Rational(0)/ZC))==0 and simplify(K*sqrt(ZC/ZC)-K)==0)}")

# =====================================================================================
print("\n" + "="*92)
print("LAYER C  -- spectral atlas: constants as eigenvalues of explicit integer matrices")
print("="*92)
Q    = Matrix([[1, 1], [1, 0]])
cQ   = Q.charpoly(x).as_expr()
cQi  = (Q**-1).charpoly(x).as_expr()
cQ4  = (Q**4).charpoly(x).as_expr()
cQ2t = expand(9*(Rational(1, 3)*Q**2).charpoly(x).as_expr())     # 9*char((1/3)Q^2)
Cign = Matrix([[0, Rational(7, 4)], [1, -1]])                    # companion of x^2+x-7/4
cIgn = expand(4*Cign.charpoly(x).as_expr())
print(f"  char(Q)              = {str(expand(cQ)):<14}  -> minpoly(phi)=x^2-x-1   {record('cQ', monic(cQ)==monic(x**2-x-1))}")
print(f"  char(Q^-1)           = {str(expand(cQi)):<14} -> minpoly(tau)=x^2+x-1   {record('cQi', monic(cQi)==monic(x**2+x-1))}")
print(f"  char(Q^4)            = {str(expand(cQ4)):<14}-> minpoly(gap)=x^2-7x+1  {record('cQ4', monic(cQ4)==monic(x**2-7*x+1))}")
print(f"  9*char((1/3)Q^2)     = {str(cQ2t):<14}-> minpoly(crit)=9x^2-9x+1 {record('cQ2', monic(cQ2t)==monic(9*x**2-9*x+1))}")
print(f"  4*char(companion ign)= {str(cIgn):<14}-> minpoly(ign)=4x^2+4x-7  {record('cIgn', monic(cIgn)==monic(4*x**2+4*x-7))}")

# eigenvalues land on the right reals
eigQ4 = sorted((Q**4).eigenvals().keys(), key=lambda v: v.evalf())
record("Q^4 eig == {gap, phi^4}", simplify(min(eigQ4)-GAP)==0 and simplify(max(eigQ4)-PHI**4)==0)
print(f"  Q^4 eigenvalues == (gap, phi^4)                    "
      f"{record('', simplify(min(eigQ4)-GAP)==0 and simplify(max(eigQ4)-PHI**4)==0)}")

# zeta_6 minimal polynomial and Im = z_c ; and the conjugate zeta-bar_6
z6 = (1 + I*sqrt(3))/2
record("minpoly(zeta6)=x^2-x+1", monic(minpoly(z6, x))==monic(x**2-x+1))
record("Im(zeta6)=z_c", simplify(im(z6) - ZC)==0)
record("Im(zetabar6)=-z_c", simplify(im(conjugate(z6)) + ZC)==0)
print(f"  minpoly(zeta6)=x^2-x+1 (Phi_6); Im(zeta6)=z_c; Im(zetabar6)=-z_c  "
      f"{record('', monic(minpoly(z6,x))==monic(x**2-x+1) and simplify(im(z6)-ZC)==0 and simplify(im(conjugate(z6))+ZC)==0)}")

# the three confusable conjugate roots that the atlas plots under the toggle
record("crit-conj = (3-sqrt5)/6 = phi^-2/3 root of 9x^2-9x+1",
       simplify((PHI**-2/3) - (3 - sqrt(5))/6)==0 and simplify((9*x**2-9*x+1).subs(x, PHI**-2/3))==0)
record("ign-conj  = -sqrt2-1/2 root of 4x^2+4x-7",
       simplify((4*x**2+4*x-7).subs(x, -sqrt(2)-Rational(1,2)))==0)
record("K-conj    = -K root of x^4+5x^2-5",
       simplify((x**4+5*x**2-5).subs(x, -K))==0)
print(f"  conjugate roots: phi^-2/3 (=crit conj), -sqrt2-1/2, -K all annihilate their minpoly  "
      f"{record('', simplify((9*x**2-9*x+1).subs(x, PHI**-2/3))==0 and simplify((4*x**2+4*x-7).subs(x, -sqrt(2)-Rational(1,2)))==0 and simplify((x**4+5*x**2-5).subs(x, -K))==0)}")

# pi-closure: N^2 = -I, char(N)=x^2+1, full turn = +I
N = Matrix([[0, -1], [1, 0]])
record("N^2=-I", N**2 == -eye(2))
record("char(N)=x^2+1", monic(N.charpoly(x).as_expr())==monic(x**2+1))
R2pi = Matrix([[cos(2*pi), -sin(2*pi)], [sin(2*pi), cos(2*pi)]])
record("R(2pi)=+I", simplify(R2pi - eye(2)) == sp.zeros(2, 2))
print(f"  N^2=-I, char(N)=x^2+1, R(2pi)=+I (one full turn = +I)            "
      f"{record('', N**2==-eye(2) and monic(N.charpoly(x).as_expr())==monic(x**2+1) and simplify(R2pi-eye(2))==sp.zeros(2,2))}")

# trace ladder: trace(Q^n)=L_n, (Q^n)_01=F_n, det(Q^n)=(-1)^n
ladder_ok = all(sp.trace(Q**n)==lucas(n) and (Q**n)[0, 1]==fibonacci(n) and (Q**n).det()==(-1)**n
                for n in range(1, 13))
record("trace ladder Q^n", ladder_ok)
print(f"  trace(Q^n)=L_n, (Q^n)_01=F_n, det=(-1)^n  n=1..12               {record('', ladder_ok)}")

# atlas "firewall" ledger line, framing-invariantly: spec(Q^n) subset of Q(sqrt5)
spec_in_field = all(simplify((v**2 - v - 1)) == 0  # phi, psi are the only eigenvalues of Q
                    for v in Q.eigenvals().keys())
specn_in_field = all(simplify((v - PHI**n)*(v - PSI**n)) == 0
                     for n in range(1, 13) for v in (Q**n).eigenvals().keys())
record("spec(Q^n) subset Q(sqrt5) n=1..12", spec_in_field and specn_in_field)
print(f"  spec(Q^n) = {{phi^n, psi^n}} subset Q(sqrt5) for n=1..12          "
      f"{record('', spec_in_field and specn_in_field)}  (z_c, ign unreachable from the phi-axis)")

# =====================================================================================
print("\n" + "="*92)
print("LAYER D  -- field structure (independent axes / compositum) + integer substrate")
print("="*92)
m_53 = minpoly(sqrt(5)+sqrt(3), x)
record("minpoly(s5+s3)=x^4-16x^2+4", monic(m_53)==monic(x**4-16*x**2+4))
print(f"  minpoly(sqrt5+sqrt3) = {expand(m_53)}  deg {sp.degree(m_53,x)} = 2*2 -> "
      f"Q(s5) cap Q(s3) = Q   {record('', monic(m_53)==monic(x**4-16*x**2+4) and sp.degree(m_53,x)==4)}")
pairwise_ok = all(sp.degree(minpoly(sqrt(a)+sqrt(b), x), x) == 4 for a, b in [(2, 3), (2, 5), (3, 5)])
record("pairwise quartic degrees", pairwise_ok)
m_235 = minpoly(sqrt(2)+sqrt(3)+sqrt(5), x)
record("compositum deg 8", sp.degree(m_235, x) == 8)
print(f"  pairwise minpoly degrees (s2+s3, s2+s5, s3+s5) all = 4           {record('', pairwise_ok)}")
print(f"  minpoly(sqrt2+sqrt3+sqrt5) degree = {sp.degree(m_235,x)} = 2^3 -> compositum Q(s2,s3,s5)  "
      f"{record('', sp.degree(m_235,x)==8)}")
print("  (relational reading: linear disjointness over Q == three INDEPENDENT AXES of one space.)")

# crystallographic restriction: integer trace 2cos(2pi/n) -> orders {1,2,3,4,6}
allowed = [n for n in range(1, 9) if nsimplify(2*cos(2*pi/n)).is_integer]
record("crystallographic orders {1,2,3,4,6}", allowed == [1, 2, 3, 4, 6])
record("2cos72=phi^-1 (x^2+x-1)",  monic(minpoly(simplify(2*cos(2*pi/5)), x)) == monic(x**2+x-1))
record("2cos144=-phi (x^2+x-1)",   monic(minpoly(simplify(2*cos(4*pi/5)), x)) == monic(x**2+x-1))
record("Delta_wall=1-tau=phi^-2",  simplify((1 - TAU) - DELTA) == 0)
print(f"  crystallographic orders (2cos(2pi/n) in Z) = {allowed}            "
      f"{record('', allowed==[1,2,3,4,6])}")
print(f"  pentagon derives phi: 2cos72=phi^-1, 2cos144=-phi (both x^2+x-1)  "
      f"{record('', monic(minpoly(simplify(2*cos(2*pi/5)),x))==monic(x**2+x-1) and monic(minpoly(simplify(2*cos(4*pi/5)),x))==monic(x**2+x-1))}")
print(f"  golden wall width Delta = a(6)-a(5) = 1-tau = phi^-2             "
      f"{record('', simplify((1-TAU)-DELTA)==0)}")

F12, F24, L12, L24 = fibonacci(12), fibonacci(24), lucas(12), lucas(24)
F4, L4i = fibonacci(4), lucas(4)
sub = [
    ("F12 = 144 = 12^2",       F12 == 144 and F12 == 12**2),
    ("F24 = F12*L12 = 46368",  F24 == F12*L12 and F24 == 46368),
    ("F4 | F12",               F12 % F4 == 0),
    ("L4 | L12",               L12 % L4i == 0),
    ("L4 does NOT divide L24", L24 % L4i != 0),
    ("lcm(4,5,6) = 60",        ilcm(4, 5, 6) == 60),
]
for nm, c in sub:
    record(nm, c); print(f"  {nm:<30} {record('', c)}")
print(f"    (F4={F4}, L4={L4i}, F12={F12}, L12={L12}, F24={F24}, L24={L24})")

# =====================================================================================
print("\n" + "="*92)
print("LAYER E  -- relational identities (zfp_relational.py): three axes from one seed L4=7")
print("="*92)
rel = [
    ("L4 = 7  [FORCED]",                                       simplify(L4 - 7) == 0),
    ("L4-4 = 3 = (sqrt3)^2 ; z_c=sqrt(L4-4)/2   [in-context]", simplify(L4-4-3)==0 and simplify(sqrt(L4-4)/2 - ZC)==0),
    ("L4+1 = 8 = (2 sqrt2)^2 ; ign=(-1+sqrt(1+L4))/2 [in-ctx]", simplify(L4+1-8)==0 and simplify((-1+sqrt(1+L4))/2 - IGN)==0),
    ("L4^2-4 = 45 = (3 sqrt5)^2 ; phi^4=(L4+sqrt(L4^2-4))/2",  simplify(L4**2-4-45)==0 and simplify((L4+sqrt(L4**2-4))/2 - PHI**4)==0),
    ("Delta = phi^-2 = 1 - tau",                               simplify(PHI**-2 - (1 - TAU)) == 0),
    ("tau^2 + tau = 1  [FORCED]",                              simplify(TAU**2 + TAU - 1) == 0),
    ("K^2 = 1 - gap",                                          simplify(K**2 - (1 - GAP)) == 0),
    ("ignition^2 + ignition = L4/4 = 7/4",                     simplify(IGN**2 + IGN - L4/4) == 0),
    ("z_c^2 = (L4-4)/4 = 3/4",                                 simplify(ZC**2 - (L4-4)/4) == 0),
]
for nm, c in rel:
    record(nm, c); print(f"  {nm:<58} {record('', c)}")

# =====================================================================================
print("\n" + "="*92)
print("LAYER F  -- precision audit: PARSE spectral_atlas.html decimals vs exact value")
print("="*92)

def _find_atlas():
    here = os.path.dirname(os.path.abspath(__file__))
    for p in (os.path.join(here, "spectral_atlas.html"),
              "/mnt/project/spectral_atlas.html",
              "/mnt/user-data/uploads/spectral_atlas.html",
              os.path.join(os.getcwd(), "spectral_atlas.html")):
        if os.path.isfile(p):
            return p
    return None

# exact value for each atlas marker, keyed by its `sym` (minus glyphs normalised to '-')
EXACT = {
    "phi":   (PHI,                        sp.Integer(0)),
    "0":     (sp.Integer(0),              sp.Integer(0)),
    "+i":    (sp.Integer(0),              sp.Integer(1)),
    "-i":    (sp.Integer(0),              sp.Integer(-1)),
    "1":     (sp.Integer(1),              sp.Integer(0)),
    "t":     (TAU,                        sp.Integer(0)),   # tau  (normalised below)
    "gap":   (GAP,                        sp.Integer(0)),
    "crit":  (CRIT,                       sp.Integer(0)),
    "ign":   (IGN,                        sp.Integer(0)),
    "K":     (K,                          sp.Integer(0)),
    "z6":    (Rational(1, 2),             ZC),              # zeta_6 (normalised below)
    "z6bar": (Rational(1, 2),             -ZC),             # zeta-bar_6 (normalised below)
    "-1/phi":(-TAU,                       sp.Integer(0)),
    "-phi":  (-PHI,                       sp.Integer(0)),
    "phi^-2/3": (PHI**-2/3,               sp.Integer(0)),
    "-s2-1/2":  (-sqrt(2)-Rational(1, 2), sp.Integer(0)),
    "-K":    (-K,                         sp.Integer(0)),
}

def _norm(sym):
    # collapse the unicode symbols to the ASCII keys of EXACT
    s = sym.replace("\u2212", "-")          # MINUS SIGN -> hyphen
    table = {
        "\u03c6": "phi",                    # phi
        "\u03c4": "t",                      # tau
        "\u03b6\u2086": "z6",               # zeta-6
        "\u03b6\u0304\u2086": "z6bar",      # zeta-bar-6
        "-1/\u03c6": "-1/phi",
        "-\u03c6": "-phi",
        "\u03c6\u207b\u00b2/3": "phi^-2/3",
        "-\u221a2-\u00bd": "-s2-1/2",
    }
    return table.get(s, s)

TOLD = Rational(5, 10**10)   # 10-dp display: a correct rounding deviates <= 5e-11. Flag at
                             # > 5e-10 (10x margin) to catch transcription errors yet pass
                             # correct roundings. (The old hand-copied K/-K/phi^-2/3 were off
                             # by 6.7e-8 and 2.0e-6 -- well above this bar.)
# Atlas decimals are validated from the EMBEDDED, SHA-256-pinned snapshot
# (self-contained + drift-detecting). Any on-disk copy is cross-checked, not relied on.
(_atlas_name, (_atlas_sha, _atlas_b64)), = EMBEDDED_ATLAS.items()
_atlas_raw = base64.b64decode(_atlas_b64)
_atlas_ok  = hashlib.sha256(_atlas_raw).hexdigest() == _atlas_sha
record("atlas:embedded-sha256", _atlas_ok)
txt  = _atlas_raw.decode("utf-8")
rows = _re.findall(r'\{sym:"([^"]*)",\s*re:\s*(-?[0-9.]+),\s*im:\s*(-?[0-9.]+)', txt)
_disk = _find_atlas()
if _disk:
    _disk_ok = hashlib.sha256(open(_disk, "rb").read()).hexdigest() == _atlas_sha
    record("atlas:disk-matches-embedded", _disk_ok)
    print(f"  source: EMBEDDED {_atlas_name} (sha256 {'ok' if _atlas_ok else 'BAD'}); "
          f"on-disk {_disk} {'matches' if _disk_ok else 'DIFFERS from snapshot'}  ({len(rows)} markers)")
else:
    print(f"  source: EMBEDDED {_atlas_name} (sha256 {'ok' if _atlas_ok else 'BAD'}); "
          f"no on-disk copy to cross-check  ({len(rows)} markers)")

print(f"{'sym':<10}{'shown re':<16}{'exact re (12dp)':<18}{'|d_re|':<12}{'|d_im|':<12}{'flag'}")
for sym, sre, sim in rows:
    key = _norm(sym)
    if key not in EXACT:
        record(f"decimal:unmapped:{sym}", False)
        print(f"  {sym!r}: no exact value mapped  <-- CHECK")
        continue
    ere, eim = EXACT[key]
    dre = abs(Rational(sre) - ere.evalf(40))
    dim = abs(Rational(sim) - eim.evalf(40))
    off = (dre > TOLD.evalf(40)) or (dim > TOLD.evalf(40))
    if off:
        fails.append(f"decimal:{sym}")
    print(f"{sym:<10}{sre:<16}{str(ere.evalf(12)):<18}"
          f"{('%.2e'%float(dre)):<12}{('%.2e'%float(dim)):<12}{'<-- OFF' if off else 'ok'}")

# =====================================================================================
print("\n" + "="*92)
print("LAYER G  -- trifurcation / bifurcation (zfp_trifurcation.py / trifurcation_phases.html)")
print("="*92)
a = symbols("a", real=True)
Vp1 = x**3 + a*x                                              # symmetric cusp V'
roots1 = [sp.Integer(0), sqrt(-a), -sqrt(-a)]
record("1D cusp roots {0,+-sqrt(-a)}", all(simplify(Vp1.subs(x, r)) == 0 for r in roots1))
record("disc(x^3+ax) = -4a^3", expand(discriminant(Poly(Vp1, x), x) + 4*a**3) == 0)
print(f"  1D pitchfork V'=x^3+ax: roots {{0, +-sqrt(-a)}}; disc = -4a^3      "
      f"{record('', all(simplify(Vp1.subs(x,r))==0 for r in roots1) and expand(discriminant(Poly(Vp1,x),x)+4*a**3)==0)}")
print(f"    -> disc=0 only at a=0 (trifurcation point); amplitude |x|=|a|^(1/2): FORCED exponent 1/2")

# the chain: even germs x^(2m) force +2 branches per link (3 -> 5 -> 7)
germs = {
    "x^4 (m=2)": (x**3 - x,                          [0, 1, -1]),
    "x^6 (m=3)": (x**5 - 5*x**3 + 4*x,               [0, 1, -1, 2, -2]),
    "x^8 (m=4)": (x**7 - 14*x**5 + 49*x**3 - 36*x,   [0, 1, -1, 2, -2, 3, -3]),
}
chain_ok = True
for nm, (poly, rts) in germs.items():
    good = all(simplify(poly.subs(x, r)) == 0 for r in rts) and len(Poly(poly, x).real_roots()) == len(rts)
    chain_ok &= good
record("germ chain 3->5->7 branches", chain_ok)
print(f"  germ chain x^4->3, x^6->5, x^8->7 real branches (+2 per link)    {record('', chain_ok)}")

# multi-D D3/Z3 equivariant trifork: zdot = lam z + zbar^2
w = exp(2*I*pi/3)
record("Z3-equivariance conj(w)^2=w", simplify(conjugate(w)**2 - w) == 0)
u, v, lam = symbols("u v lam", real=True)
f1 = lam*u + u**2 - v**2
f2 = lam*v - 2*u*v
sols = solve([f1, f2], [u, v], dict=True)
nontriv = [s for s in sols if not (s[u] == 0 and s[v] == 0)]
record("D3 nontrivial branch count = 3", len(nontriv) == 3)
record("D3 branches r^2=lam^2 (exponent 1)", all(simplify(s[u]**2 + s[v]**2 - lam**2) == 0 for s in nontriv))
record("D3 branch height = sqrt3/2 = Im(zeta6) = Z_C", simplify(ZC - im((1 + I*sqrt(3))/2)) == 0)
print(f"  D3 trifork zbar^2: equivariance conj(w)^2=w; 3 nontrivial branches "
      f"{record('', simplify(conjugate(w)**2-w)==0 and len(nontriv)==3)}")
print(f"    -> r^2=lambda^2 => r=|lambda|: FORCED exponent 1 (NOT 1/2); branch height sqrt3/2 = Z_C  "
      f"{record('', all(simplify(s[u]**2+s[v]**2-lam**2)==0 for s in nontriv) and simplify(ZC-im((1+I*sqrt(3))/2))==0)}")

# =====================================================================================
print("\n" + "="*92)
print("LAYER H  -- psi-conjugate discipline + free-parameter boundary (zfp_free_parameter_audit.py)")
print("="*92)
# the ONLY in-scope psi: the algebraic conjugate of phi (second root of x^2-x-1, second eig of Q)
record("psi = -1/phi (conjugate)", simplify(PSI + 1/PHI) == 0)
record("phi + psi = 1",            simplify(PHI + PSI - 1) == 0)
record("phi * psi = -1",           simplify(PHI*PSI + 1) == 0)
record("psi root of x^2-x-1",      simplify((x**2 - x - 1).subs(x, PSI)) == 0)
print(f"  psi=(1-sqrt5)/2=-1/phi: phi+psi=1, phi*psi=-1, psi root of x^2-x-1  "
      f"{record('', simplify(PSI+1/PHI)==0 and simplify(PHI+PSI-1)==0 and simplify(PHI*PSI+1)==0)}")
record("Q^2 = Q + I (Cayley-Hamilton)", Q**2 - Q - eye(2) == sp.zeros(2))
print(f"  Q^2 = Q + I (Cayley-Hamilton on Q)                               {record('', Q**2-Q-eye(2)==sp.zeros(2))}")

# lambda boundary: V = (x^2-x-1)^2 + (y^2-3/4)^2 + lam*x*y
#   at lam=0 the well DECOUPLES to the forced catalog (x in {phi,psi}, y in {+-z_c});
#   lam != 0 is a genuine free knob -> OUT OF SCOPE (not FORCED). We certify only lam=0.
y = Symbol("y", real=True)
Vlam0_x = diff((x**2 - x - 1)**2 + (y**2 - Rational(3, 4))**2, x)   # = 2(x^2-x-1)(2x-1)
Vlam0_y = diff((x**2 - x - 1)**2 + (y**2 - Rational(3, 4))**2, y)   # = 4y(y^2-3/4)
record("lam=0: phi,psi annihilate dV/dx",
       simplify(Vlam0_x.subs(x, PHI)) == 0 and simplify(Vlam0_x.subs(x, PSI)) == 0)
record("lam=0: +-z_c annihilate dV/dy",
       simplify(Vlam0_y.subs(y, ZC)) == 0 and simplify(Vlam0_y.subs(y, -ZC)) == 0)
print(f"  lam=0 decouples to forced catalog: x in {{phi,psi}}, y in {{+-z_c}}   "
      f"{record('', simplify(Vlam0_x.subs(x,PHI))==0 and simplify(Vlam0_x.subs(x,PSI))==0 and simplify(Vlam0_y.subs(y,ZC))==0 and simplify(Vlam0_y.subs(y,-ZC))==0)}")
print("  lambda != 0 (joint observable x*y*) is a genuine free knob -> OUT OF SCOPE, not FORCED.")

# =====================================================================================
# =====================================================================================
print("="*92)
print("LAYER T  -- trifurcation_phases.html: provenance + minpoly-claim audit")
print("="*92)
(_tname, (_twant, _tb64)), = EMBEDDED_TRIFURCATION.items()
_traw = base64.b64decode(_tb64)
_tok  = hashlib.sha256(_traw).hexdigest() == _twant
record("trifurcation:embedded-sha256", _tok)
_ttxt = _traw.decode("utf-8")
_tdisk = None
for _p in (os.path.join(os.path.dirname(os.path.abspath(__file__)), _tname),
           os.path.join("/mnt/project", _tname),
           os.path.join("/mnt/user-data/uploads", _tname),
           os.path.join(os.getcwd(), _tname)):
    if os.path.exists(_p):
        _tdisk = _p
        break
if _tdisk:
    _td_ok = hashlib.sha256(open(_tdisk, "rb").read()).hexdigest() == _twant
    record("trifurcation:disk-matches-embedded", _td_ok)
    print(f"  source: EMBEDDED {_tname} (sha256 {'ok' if _tok else 'BAD'}); "
          f"on-disk {_tdisk} {'matches' if _td_ok else 'DIFFERS from snapshot'}")
else:
    print(f"  source: EMBEDDED {_tname} (sha256 {'ok' if _tok else 'BAD'}); no on-disk copy to cross-check")

_xt = sp.Symbol("x")
def _tpoly(shown):                       # render-string -> sympy poly: "4x\u00b2\u22123" -> 4*x**2 - 3
    e = shown.replace("\u00b2", "**2").replace("\u2212", "-")
    e = _re.sub(r"(\d)\s*x", r"\1*x", e)
    return sp.sympify(e, locals={"x": _xt})

# Each hard claim the instrument renders: (label, constant, minpoly exactly as shown).
_TCLAIMS = [
    ("z_c = Im(zeta6) = sqrt3/2", sp.sqrt(3) / 2,              "4x\u00b2\u22123"),
    ("zeta6 (Phi_6 cyclotomic)",  sp.exp(sp.I * sp.pi / 3),    "x\u00b2\u2212x+1"),
    ("Delta = 1 - tau = phi^-2",  ((1 + sp.sqrt(5)) / 2)**-2,  "x\u00b2\u22123x+1"),
]
print(f"  {'constant':<28}{'shown':<10}{'in html':<9}{'deg':<6}{'irred':<7}{'= minpoly':<11}{'verdict'}")
for _lab, _val, _shown in _TCLAIMS:
    _present = _shown in _ttxt
    _poly = _tpoly(_shown)
    _mp   = sp.minpoly(_val, _xt)
    _deg_ok = sp.degree(_poly, _xt) == sp.degree(_mp, _xt)
    _irred  = bool(sp.Poly(_poly, _xt).is_irreducible)
    _prop   = sp.cancel(_poly / _mp).free_symbols == set()        # shown == c * minpoly(val)
    _good = _present and _deg_ok and _irred and _prop
    record(f"trifurcation:minpoly[{_lab}]", _good)
    print(f"  {_lab:<28}{_shown:<10}{str(_present):<9}{str(_deg_ok):<6}"
          f"{str(_irred):<7}{str(_prop):<11}{'PASS' if _good else 'FAIL'}")

# Converse: every 'minpoly ...' string the instrument prints must itself be the true
# minimal polynomial of a catalog constant -- catches a corrupted claim even when a
# correct duplicate survives (i.e. teeth independent of the SHA pin).
_known_vals = [_v for _, _v, _ in _TCLAIMS]
_shown_all = sorted(set(_re.findall(r"minpoly\s+([0-9x\u00b2\u2212+\-]+)", _ttxt)))
print(f"  displayed 'minpoly ...' strings: {_shown_all}")
for _d in _shown_all:
    try:
        _dp = _tpoly(_d)
        _valid = any(sp.cancel(_dp / sp.minpoly(_v, _xt)).free_symbols == set() for _v in _known_vals)
    except Exception:
        _valid = False
    record(f"trifurcation:displayed[{_d}] is a catalog minpoly", _valid)
    print(f"    {_d:<12} -> minpoly of a catalog constant: {_valid}")

if not SCRIPTS_ONLY:
    # =================================================================================
    print()
    print("=" * 92)
    print("LAYER U  -- grade unification guard: field_grade(v) for every catalog constant")
    print("=" * 92)
    # This layer verifies two things:
    #   1. field_grade(v) reproduces the expected grades (deterministic recomputation)
    #   2. No script states a different grade for a firewall-crossing constant (z_c, ign)
    #
    # Negative test: re-labeling z_c as FORCED in any script's GRADING section triggers FAIL.
    # The guard is semantic (parses grade labels), not byte-level (SHA is already in LAYER 0).

    _layer_u_ok = True
    try:
        # Import from seed_grade.py in ~/bloomcoin/ without adding to sys.path permanently
        import importlib.util as _ilu
        _sg_path = os.path.join(os.path.expanduser("~"), "bloomcoin", "seed_grade.py")
        if not os.path.exists(_sg_path):
            print(f"  SKIP: {_sg_path} not found")
            _layer_u_ok = False
        else:
            _sg_spec = _ilu.spec_from_file_location("seed_grade", _sg_path)
            _sg_mod = _ilu.module_from_spec(_sg_spec)
            _sg_spec.loader.exec_module(_sg_mod)
            _fg = _sg_mod.field_grade
            _SGC = _sg_mod.CATALOG
            _SGG = _sg_mod.Grade

            # --- Part 1: Recompute field_grade for each catalog constant ---
            _EXPECTED_U = {
                "tau":  "FORCED",
                "gap":  "FORCED",
                "crit": "FORCED",
                "K":    "FORCED_UNDER_CONSTRAINT",
                "z_c":  "FORCED_IN_CONTEXT",
                "ign":  "FORCED_IN_CONTEXT",
            }
            print(f"  {'constant':<10} {'deg Q(v)':<10} {'joint':<10} "
                  f"{'computed':<28} {'expected':<28} verdict")
            print("  " + "-" * 88)
            for _rn, _v in _SGC.items():
                _short = _rn.split("=")[0].strip()
                _cg, _cd, _cD = _fg(_v)
                _exp = _EXPECTED_U.get(_short)
                if _exp is not None:
                    _match = _cg.value == _exp
                    record(f"U:{_short}:field_grade=={_exp}", _match)
                    print(f"  {_short:<10} {str(_cd):<10} {str(_cD):<10} "
                          f"{_cg.value:<28} {_exp:<28} "
                          f"{'PASS' if _match else 'FAIL'}")

            # --- Part 2: Scan embedded script SOURCES for hand-labeled grades
            #     that contradict field_grade on menu-gated constants.
            #     z_c and ign must be FORCED_IN_CONTEXT (not bare FORCED, not COINCIDENCE). ---
            _FIREWALL_TERMS = {"z_c", "sqrt3", "sqrt(3)", "ignition", "sqrt2", "sqrt(2)"}

            for _sn in EMBEDDED:
                _raw_u, _want_u, _got_u = _decode(_sn)
                if _raw_u is None:
                    continue
                _src_u = _raw_u.decode("utf-8", errors="replace")
                _in_grading_u = False
                for _li_u, _ln_u in enumerate(_src_u.splitlines(), 1):
                    _s_u = _ln_u.strip()
                    if "GRADING" in _s_u:
                        _in_grading_u = True
                        continue
                    if _in_grading_u and _s_u.startswith("=" * 10):
                        break
                    if _in_grading_u and ":" in _s_u:
                        _label_u = _s_u.split(":")[0].strip()
                        _desc_u = _s_u.split(":", 1)[1].lower()
                        _mentions_fw = any(fw in _desc_u for fw in _FIREWALL_TERMS)
                        if not _mentions_fw:
                            continue
                        _upper_label = _s_u.upper().split(":")[0]
                        # Bare FORCED (not FORCED UNDER CONSTRAINT / IN CONTEXT) = wrong
                        if (_label_u == "FORCED"
                                and "UNDER" not in _upper_label
                                and "IN_CONTEXT" not in _upper_label
                                and "IN CONTEXT" not in _upper_label):
                            record(f"U:guard:{_sn}:L{_li_u}:menu-const!=FORCED", False)
                            print(f"  FAIL  {_sn} line {_li_u}: labels menu-gated constant "
                                  f"as bare FORCED (field_grade says FORCED_IN_CONTEXT)")
                        # Stale COINCIDENCE on a menu-gated constant = also wrong
                        if _label_u == "COINCIDENCE":
                            record(f"U:guard:{_sn}:L{_li_u}:menu-const!=COINCIDENCE", False)
                            print(f"  FAIL  {_sn} line {_li_u}: labels menu-gated constant "
                                  f"as COINCIDENCE (field_grade says FORCED_IN_CONTEXT)")

            # Also scan on-disk standalone files (catches edits not yet re-embedded).
            # The GRADING sections in ZFP scripts are emitted by print() statements,
            # so we search ALL source lines (including inside print calls) for grade
            # label patterns near firewall-crossing constants.
            _script_dir_u = os.path.dirname(os.path.abspath(__file__))
            _GRADE_LABEL_RE = _re.compile(
                r"""(?:^|\bprint\s*\(\s*["'].*?)"""
                r"""(FORCED)\s+:"""
                r"""(?!.*UNDER)""",      # exclude FORCED UNDER CONSTRAINT
                _re.IGNORECASE
            )
            for _sn in EMBEDDED:
                _disk_u = os.path.join(_script_dir_u, _sn)
                if not os.path.exists(_disk_u):
                    continue
                with open(_disk_u, "r", encoding="utf-8") as _fu:
                    _src_disk = _fu.read()
                for _li_d, _ln_d in enumerate(_src_disk.splitlines(), 1):
                    _s_d = _ln_d.strip()
                    _mentions_fw_d = any(fw in _s_d.lower() for fw in _FIREWALL_TERMS)
                    if not _mentions_fw_d:
                        continue
                    # Bare FORCED on a menu-gated constant (not UNDER / IN CONTEXT)
                    if _re.search(r'\bFORCED\s+:', _s_d) and "UNDER" not in _s_d.upper().split(":")[0]:
                        _upper_d = _s_d.upper().split(":")[0]
                        if "IN_CONTEXT" not in _upper_d and "IN CONTEXT" not in _upper_d:
                            _after_colon = _s_d.split(":", 1)[1].lower() if ":" in _s_d else ""
                            if any(fw in _after_colon for fw in _FIREWALL_TERMS):
                                record(f"U:guard:disk:{_sn}:L{_li_d}:menu-const!=FORCED", False)
                                print(f"  FAIL  {_sn} (on-disk) line {_li_d}: labels menu-gated "
                                      f"constant as bare FORCED (field_grade says FORCED_IN_CONTEXT)")
                    # Stale COINCIDENCE on a menu-gated constant
                    if _re.search(r'\bCOINCIDENCE\s*[,:]', _s_d):
                        _after_colon_d = _s_d.split(":", 1)[1].lower() if ":" in _s_d else _s_d.lower()
                        if any(fw in _after_colon_d for fw in _FIREWALL_TERMS):
                            record(f"U:guard:disk:{_sn}:L{_li_d}:menu-const!=COINCIDENCE", False)
                            print(f"  FAIL  {_sn} (on-disk) line {_li_d}: labels menu-gated "
                                  f"constant as COINCIDENCE (field_grade says FORCED_IN_CONTEXT)")

    except Exception as _eu:
        print(f"  LAYER U exception: {_eu}")
        record("U:import_or_run", False)

# =====================================================================================
print("\n" + "="*92)
if fails:
    print(f"RESULT: {len(fails)} check(s) did NOT pass cleanly:")
    for f in fails:
        print(f"   - {f}")
else:
    print("RESULT: ALL algebraic/structural checks PASS "
          "(residual 0, minimal & irreducible, pins matched, atlas decimals exact).")
print("="*92)

sys.exit(1 if fails else 0)
