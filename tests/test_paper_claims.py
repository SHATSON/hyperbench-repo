"""
test_paper_claims.py -- Regression tests binding the paper's claims to the code.

Every assertion below corresponds to a specific numerical statement in the
manuscript. If a refactor changes a result, the corresponding test fails and
the paper must be updated. Run with:

    python -m pytest tests/ -v

or without pytest:

    python tests/test_paper_claims.py
"""

from __future__ import annotations

import os
import sys

import numpy as np
import sympy as sp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hyperbench'))

import exp_a_energy_audit as A          # noqa: E402
import exp_b_viq as B                   # noqa: E402
import exp_c_warp_scaling as C          # noqa: E402
import exp_d_control as D               # noqa: E402
from exp_d_control import (             # noqa: E402
    lqr_design, delay_margin_closed_form, vpp_closed_form,
)


# ---------------------------------------------------------------------------
# Experiment A -- symbolic audit
# ---------------------------------------------------------------------------

def test_a_reproduces_morris_thorne():
    """Engine-derived rho and p_r match the published Morris-Thorne forms."""
    out = A.general_formulas()
    assert out['matches_morris_thorne_rho'] is True
    assert out['matches_morris_thorne_pr'] is True


def test_a_throat_nec_identity():
    """(rho + p_r)|_{b0} == (b' - 1) / (8 pi b0^2)."""
    out = A.throat_limit()
    b0 = sp.Symbol('b_0', positive=True)
    bp = sp.Symbol('bprime', real=True)
    expected = (bp - 1) / (8 * sp.pi * b0 ** 2)
    got = sp.sympify(out['nec_at_throat'], locals={'b_0': b0, 'bprime': bp})
    assert sp.simplify(got - expected) == 0
    assert out['all_negative'] is True


def test_a_family_engine_matches_analytic():
    for row in A.family_sweep():
        assert row['engine_matches_analytic'] is True
        assert row['flare_out_satisfied'] is True


# ---------------------------------------------------------------------------
# Experiment B -- Proposition 1 and optimisation
# ---------------------------------------------------------------------------

def test_b_proposition_1_lower_bound():
    """|I_V| >= b0/2 for every admissible shape function tested."""
    for row in B.b1_bound_approach():
        assert abs(row['viq_analytic']) >= 0.5 - 1e-12
        assert row['rel_err'] < 1e-5
        assert row['satisfies_bound'] is True


def test_b_bound_is_approached_but_not_attained():
    rows = B.b1_bound_approach()
    ratios = [abs(r['viq_analytic']) for r in rows]
    assert min(ratios) > 0.5           # never attained
    assert min(ratios) < 0.51          # but approached closely


def test_b_optimiser_recovers_analytic_optimum():
    """SLSQP, given no closed form, matches the ramp optimum."""
    for row in B.b2_sweep():
        assert row['optimizer_success'] is True
        assert row['rel_err'] < 1e-3
        assert row['ratio_to_bound'] >= 1.0


# ---------------------------------------------------------------------------
# Experiment C -- warp scaling
# ---------------------------------------------------------------------------

def test_c_scaling_exponents():
    """E ~ -v^2 R^2 sigma."""
    s = C.scaling_study()
    assert abs(s['exponent_v']['fitted'] - 2.0) < 1e-3
    assert abs(s['exponent_R']['fitted'] - 2.0) < 1e-2
    assert abs(s['exponent_sigma']['fitted'] - 1.0) < 1e-3


def test_c_thin_wall_asymptotics():
    """Quadrature converges to -v^2 R^2 sigma / 36 as sigma*R -> infinity."""
    rows = C.asymptotic_check()
    errs = [r['rel_err'] for r in rows]
    assert errs[-1] < 1e-9
    assert all(e2 <= e1 for e1, e2 in zip(errs[:-1], errs[1:]))   # monotone


def test_c_energy_is_negative_definite():
    for row in C.physical_budget():
        assert row['mass_equivalent_kg'] < 0


# ---------------------------------------------------------------------------
# Experiment D -- stability and the causal obstruction
# ---------------------------------------------------------------------------

def test_d_static_junction_conditions():
    """V(a0) = V'(a0) = 0 identically at the static radius."""
    for row in D.stability_scan():
        assert abs(row['V_at_a0']) < 1e-12
        assert abs(row['Vprime_at_a0']) < 1e-6


def test_d_two_routes_to_vpp_agree():
    """Closed-form and finite-difference V'' agree."""
    for row in D.stability_scan():
        assert row['agreement_rel'] < 1e-4


def test_d_lambda_tau_is_scale_invariant():
    """sup over the LQR family of lambda*tau is a constant ~0.6046."""
    values = []
    for a0 in [2.2, 2.5, 4.0, 10.0]:
        lam = float(np.sqrt(-vpp_closed_form(a0, 0.0) / 2.0))
        best = 0.0
        for qp in np.logspace(-8, 6, 40):
            for qv in np.logspace(-8, 4, 25):
                K, _ = lqr_design(lam, qp, qv, 1.0)
                tau, _ = delay_margin_closed_form(lam, K)
                if tau and tau > best:
                    best = tau
        values.append(lam * best)
    assert max(values) - min(values) < 1e-3
    assert abs(np.mean(values) - 0.6046) < 5e-3


def test_d_causal_obstruction():
    """Max LQR delay margin is below the throat light-crossing time."""
    for a0 in [2.2, 2.5, 4.0, 10.0]:
        lam = float(np.sqrt(-vpp_closed_form(a0, 0.0) / 2.0))
        best = 0.0
        for qp in np.logspace(-8, 6, 40):
            for qv in np.logspace(-8, 4, 25):
                K, _ = lqr_design(lam, qp, qv, 1.0)
                tau, _ = delay_margin_closed_form(lam, K)
                if tau and tau > best:
                    best = tau
        assert best < a0, f'obstruction fails at a0={a0}'


def test_d_lambda_a0_infimum():
    """lambda*a0 >= 0.9306, with the minimum at a0 = (3+sqrt 3) M."""
    from scipy.optimize import minimize_scalar

    def lam_a0(a0):
        v = vpp_closed_form(a0, 0.0)
        return np.nan if v >= 0 else np.sqrt(-v / 2) * a0

    r = minimize_scalar(lam_a0, bounds=(3.01, 200.0), method='bounded',
                        options={'xatol': 1e-10})
    assert abs(r.fun - 0.9306) < 1e-3
    assert abs(r.x - (3 + np.sqrt(3))) < 1e-4


def test_d_delay_margin_verified_by_simulation():
    """Closed-form margin agrees with direct DDE integration."""
    lam = float(np.sqrt(-vpp_closed_form(2.5, 0.0) / 2.0))
    K, _ = lqr_design(lam, 1.0, 1.0, 1.0)
    tau, _ = delay_margin_closed_form(lam, K)
    _, stable_half = D.simulate_delayed(lam, K, 0.5 * tau)
    _, stable_double = D.simulate_delayed(lam, K, 2.0 * tau)
    assert stable_half is True
    assert stable_double is False


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f'PASS  {fn.__name__}')
        except AssertionError as exc:
            failed += 1
            print(f'FAIL  {fn.__name__}: {exc}')
    print(f'\n{len(fns) - failed}/{len(fns)} tests passed')
    sys.exit(1 if failed else 0)
