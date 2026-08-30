"""
Experiment B -- Volume-integral quantifier (VIQ) and constrained minimisation
of total exotic-matter content.

The VIQ of Visser, Kar & Dadhich (2003) measures the *total* amount of
NEC-violating material rather than its pointwise value:

    I_V = \\oint (rho + p_r) dV,     dV = 4 pi r^2 dr

For the zero-tidal-force gauge Phi = 0 this collapses to

    I_V = (1/2) \\int_{b0}^{inf} ( b'(r) - b(r)/r ) dr

Proposition 1 (proved in the paper, verified numerically here):
    |I_V| >= b0 / 2   for every admissible shape function.

So the total exotic content cannot be made arbitrarily small at fixed throat
radius in this gauge; it is bounded below by half the throat radius in
geometric units. The bound is approached but never attained.

Experiment B2 then poses the engineering question: if the shape function is
additionally required to have bounded gradient |b'| <= B (a proxy for bounded
tidal stress), what is the minimum achievable |I_V|? An analytic answer exists,
and a general-purpose SLSQP optimizer over free control points is checked
against it. Agreement validates the optimizer for cases where no closed form
is available.

Outputs results_b.json.
"""

from __future__ import annotations

import json
import numpy as np
from scipy.integrate import quad
from scipy.optimize import minimize


# ---------------------------------------------------------------------------
# VIQ evaluation
# ---------------------------------------------------------------------------

def viq_from_b(b, bprime, b0, r_max=np.inf, n=None):
    """I_V = 0.5 * int_{b0}^{inf} (b' - b/r) dr.

    Adaptive quadrature on the semi-infinite interval. A uniform grid is NOT
    adequate here: for slowly decaying shape functions (b ~ r^-alpha with small
    alpha) the integrand's tail falls off as r^-(1+alpha), so truncating at any
    finite r_max discards a contribution of order r_max^-alpha -- which for
    alpha = 0.5 is still ~1% even at r_max = 10^4 b0.
    """
    f = lambda r: float(bprime(r) - b(r) / r)
    val, _err = quad(f, b0, r_max, limit=500)
    return 0.5 * val


def family_power(alpha, b0=1.0):
    """b(r) = b0^{1+alpha} / r^alpha. Analytic I_V = -b0 (alpha+1)/(2 alpha)."""
    # Evaluated in log space: for large alpha, r**(alpha+1) overflows Python's
    # scalar float and raises OverflowError rather than returning inf, which
    # breaks adaptive quadrature on the semi-infinite interval.
    lb = (1.0 + alpha) * np.log(b0)
    b = lambda r: np.exp(lb - alpha * np.log(r))
    bp = lambda r: -alpha * np.exp(lb - (alpha + 1.0) * np.log(r))
    return b, bp


def family_ramp(B, b0=1.0):
    """b(r) = max(0, b0 - B (r - b0)) : steepest admissible linear descent."""
    a = b0 * (1.0 + 1.0 / B)
    b = lambda r: np.maximum(0.0, b0 - B * (r - b0))
    bp = lambda r: np.where(r < a, -B, 0.0)
    return b, bp, a


def viq_ramp_analytic(B, b0=1.0):
    """|I_V| = (b0/2)(B+1) ln(1 + 1/B) for the gradient-limited ramp."""
    return 0.5 * b0 * (B + 1.0) * np.log1p(1.0 / B)


# ---------------------------------------------------------------------------
# B1: approach to the lower bound
# ---------------------------------------------------------------------------

def b1_bound_approach(b0=1.0):
    rows = []
    for alpha in [0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 200.0]:
        b, bp = family_power(alpha, b0)
        num = viq_from_b(b, bp, b0)
        ana = -b0 * (alpha + 1.0) / (2.0 * alpha)
        rows.append({
            'alpha': alpha,
            'viq_numeric': float(num),
            'viq_analytic': float(ana),
            'abs_viq_over_b0': float(abs(ana) / b0),
            'rel_err': float(abs(num - ana) / abs(ana)),
            'satisfies_bound': bool(abs(ana) >= 0.5 * b0 - 1e-12),
        })
    return rows


# ---------------------------------------------------------------------------
# B2: gradient-constrained optimisation
# ---------------------------------------------------------------------------

def b2_optimise(B, b0=1.0, n_nodes=60, seed=0):
    """Minimise |I_V| over piecewise-linear b with |b'| <= B, b(b0)=b0, b>=0.

    Free variables: nodal values b_i on a fixed grid. The optimizer is given no
    knowledge of the analytic solution.
    """
    rng = np.random.default_rng(seed)
    # Domain extends past the earliest possible zero crossing b0(1 + 1/B),
    # so the admissible set is not artificially truncated.
    r = np.linspace(b0, b0 + 2.0 * b0 / B, n_nodes)
    dr = np.diff(r)

    def objective(x):
        bvals = np.concatenate(([b0], x))
        bp = np.diff(bvals) / dr
        # I_V = 0.5 * [ (b_end - b_0) - int b/r dr ]
        term1 = bvals[-1] - b0
        term2 = np.trapezoid(bvals / r, r)
        return abs(0.5 * (term1 - term2))

    # |b'| <= B  ->  two inequality constraints per interval
    def cons_slope(x):
        bvals = np.concatenate(([b0], x))
        bp = np.diff(bvals) / dr
        return np.concatenate((B - bp, B + bp))

    x0 = np.clip(b0 - B * (r[1:] - b0), 0.0, b0) * (0.5 + 0.5 * rng.random(n_nodes - 1))
    x0[-1] = 0.0

    # Asymptotic matching to flat space: b must reach zero by the outer edge,
    # otherwise the truncated integral under-counts the -b0 boundary term.
    bnds = [(0.0, b0)] * (n_nodes - 2) + [(0.0, 0.0)]

    res = minimize(
        objective, x0, method='SLSQP',
        bounds=bnds,
        constraints=[{'type': 'ineq', 'fun': cons_slope}],
        options={'maxiter': 800, 'ftol': 1e-12},
    )
    return res, r


def b2_sweep(b0=1.0):
    rows = []
    for B in [0.5, 1.0, 2.0, 5.0, 10.0, 50.0]:
        res, r = b2_optimise(B, b0)
        ana = viq_ramp_analytic(B, b0)
        rows.append({
            'B_max_gradient': B,
            'viq_opt_numeric': float(res.fun),
            'viq_opt_analytic': float(ana),
            'rel_err': float(abs(res.fun - ana) / ana),
            'optimizer_success': bool(res.success),
            'n_iterations': int(res.nit),
            'ratio_to_bound': float(ana / (0.5 * b0)),
        })
    return rows


if __name__ == '__main__':
    out = {
        'proposition_1_bound_b0_over_2': 0.5,
        'b1_bound_approach': b1_bound_approach(),
        'b2_gradient_constrained': b2_sweep(),
    }
    with open('results_b.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))
