"""
Experiment C -- Negative-energy budget of the Alcubierre warp bubble.

For the Alcubierre metric with Eulerian-observer energy density

    rho = -(1/8pi) * (v^2 (y^2+z^2) / (4 r_s^2)) * (df/dr_s)^2

integration over a spherical shell centred on the ship gives the exact
reduction

    E = -(v^2 / 12) * int_0^inf r^2 f'(r)^2 dr

using int_0^pi sin^3 t dt = 4/3. This module evaluates that integral for the
standard top-hat profile

    f(r) = [tanh(sigma (r+R)) - tanh(sigma (r-R))] / (2 tanh(sigma R))

and extracts the empirical scaling exponents in (v, R, sigma) by log-log
regression, then converts to kilogram-equivalents.

Outputs results_c.json.
"""

from __future__ import annotations

import json
import numpy as np
from scipy.integrate import quad

C_LIGHT = 2.99792458e8          # m/s
G_NEWTON = 6.67430e-11          # m^3 kg^-1 s^-2
KG_PER_METRE = C_LIGHT ** 2 / G_NEWTON   # geometric length -> kg
M_SUN = 1.98892e30              # kg


def f_profile(r, R, sigma):
    return (np.tanh(sigma * (r + R)) - np.tanh(sigma * (r - R))) / (2 * np.tanh(sigma * R))


def _sech2(x):
    """sech^2(x) without overflowing cosh for large |x| (thin-wall limit)."""
    ax = np.abs(x)
    small = ax < 350.0
    out = np.zeros_like(np.asarray(x, dtype=float))
    xs = np.where(small, x, 0.0)
    out = np.where(small, 1.0 / np.cosh(xs) ** 2, 0.0)
    return out


def df_profile(r, R, sigma):
    s1 = _sech2(sigma * (np.asarray(r, dtype=float) + R))
    s2 = _sech2(sigma * (np.asarray(r, dtype=float) - R))
    return sigma * (s1 - s2) / (2 * np.tanh(sigma * R))


def warp_energy(v, R, sigma):
    """E in geometric units (length). Negative by construction."""
    integrand = lambda r: r ** 2 * df_profile(r, R, sigma) ** 2
    # The integrand is sharply peaked at r = R with width ~ 1/sigma; split the
    # range so the quadrature never misses the wall.
    w = max(20.0 / sigma, 1e-9)
    pts = [0.0, max(0.0, R - w), R, R + w, R + 10 * w]
    total = 0.0
    for lo, hi in zip(pts[:-1], pts[1:]):
        if hi <= lo:
            continue
        val, _ = quad(integrand, lo, hi, limit=400)
        total += val
    tail, _ = quad(integrand, pts[-1], np.inf, limit=400)
    total += tail
    return -(v ** 2 / 12.0) * total


def warp_energy_asymptotic(v, R, sigma):
    """Thin-wall limit sigma*R >> 1:  E -> -v^2 R^2 sigma / 36."""
    return -(v ** 2) * R ** 2 * sigma / 36.0


def fit_exponent(xs, ys):
    """Slope of log|y| vs log x."""
    lx, ly = np.log(np.asarray(xs)), np.log(np.abs(np.asarray(ys)))
    A = np.vstack([lx, np.ones_like(lx)]).T
    slope, intercept = np.linalg.lstsq(A, ly, rcond=None)[0]
    resid = ly - (slope * lx + intercept)
    return float(slope), float(np.max(np.abs(resid)))


def scaling_study():
    base = dict(v=1.0, R=100.0, sigma=1.0)

    vs = [0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
    Rs = [10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0]
    sgs = [0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0]

    Ev = [warp_energy(v, base['R'], base['sigma']) for v in vs]
    ER = [warp_energy(base['v'], R, base['sigma']) for R in Rs]
    Es = [warp_energy(base['v'], base['R'], s) for s in sgs]

    sv, rv = fit_exponent(vs, Ev)
    sR, rR = fit_exponent(Rs, ER)
    ss, rs_ = fit_exponent(sgs, Es)

    return {
        'exponent_v': {'fitted': sv, 'predicted': 2.0, 'max_log_residual': rv},
        'exponent_R': {'fitted': sR, 'predicted': 2.0, 'max_log_residual': rR},
        'exponent_sigma': {'fitted': ss, 'predicted': 1.0, 'max_log_residual': rs_},
    }


def asymptotic_check():
    rows = []
    for sigma in [1.0, 5.0, 20.0, 100.0, 1000.0]:
        E = warp_energy(1.0, 100.0, sigma)
        Ea = warp_energy_asymptotic(1.0, 100.0, sigma)
        rows.append({
            'sigma': sigma,
            'sigma_times_R': sigma * 100.0,
            'E_quadrature': float(E),
            'E_thin_wall_formula': float(Ea),
            'rel_err': float(abs(E - Ea) / abs(Ea)),
        })
    return rows


def physical_budget():
    """Convert to kilogram-equivalents for engineering-scale bubbles."""
    rows = []
    cases = [
        ('macroscopic wall, 1 m', 100.0, 1.0, 1.0),
        ('wall 1 cm', 100.0, 1.0e2, 1.0),
        ('wall 1 mm', 100.0, 1.0e3, 1.0),
        ('wall 1 micron', 100.0, 1.0e6, 1.0),
        ('wall 1 picometre', 100.0, 1.0e12, 1.0),
        ('small craft R=10 m, wall 1 mm', 10.0, 1.0e3, 1.0),
        ('R=100 m, wall 1 mm, v=0.1c', 100.0, 1.0e3, 0.1),
    ]
    for label, R, sigma, v in cases:
        E = warp_energy_asymptotic(v, R, sigma)     # thin-wall regime
        kg = E * KG_PER_METRE
        rows.append({
            'case': label,
            'R_m': R, 'sigma_inv_m': sigma, 'v_over_c': v,
            'E_geometric_m': float(E),
            'mass_equivalent_kg': float(kg),
            'solar_masses': float(kg / M_SUN),
        })
    return rows


if __name__ == '__main__':
    out = {
        'constants': {'kg_per_geometric_metre': KG_PER_METRE},
        'scaling_exponents': scaling_study(),
        'thin_wall_asymptotics': asymptotic_check(),
        'physical_budget': physical_budget(),
    }
    with open('results_c.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out, indent=2))
