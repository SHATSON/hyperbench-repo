"""
Experiment D -- Dynamic throat stabilisation as a control problem.

Model. A Poisson-Visser thin-shell wormhole is built by gluing two Schwarzschild
exteriors of mass M at a radius a. The shell obeys

    adot^2 = -V(a),     V(a) = f(a) - (2 pi a sigma(a))^2,   f(a) = 1 - 2M/a

with the static junction values

    sigma_0 = -(1/(2 pi a0)) sqrt(f0)
    p_0     =  (1/(4 pi a0)) (1 - M/a0)/sqrt(f0)

and the conservation law  dsigma/da = -(2/a)(sigma + p). Closing the system with
a linearised equation of state p(sigma) = p0 + beta^2 (sigma - sigma_0) yields a
one-parameter stability problem. Expanding about a0 (where V = V' = 0) gives the
linear normal form

    xddot = -(1/2) V''(a0) x   ==>   unstable with rate lambda = sqrt(-V''/2)
                                      when V''(a0) < 0.

Two independent evaluations of V''(a0) are performed -- a closed form derived by
hand and a finite-difference of the numerically integrated V -- and cross-checked.

Control. A lumped control input u (modulation of the shell's surface stress,
normalised to a radial acceleration) gives xddot = lambda^2 x + u. An
infinite-horizon LQR is synthesised, and its *delay margin* is computed in closed
form and verified by direct integration of the delay differential equation. The
delay margin is then compared against the throat light-crossing time a0/c, which
lower-bounds the latency of any causal sensor-actuator loop spanning the throat.

Outputs results_d.json.
"""

from __future__ import annotations

import json
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import solve_continuous_are
from scipy.optimize import brentq

# Geometric units G = c = 1, masses in units of M.
G_NEWTON = 6.67430e-11
C_LIGHT = 2.99792458e8
M_SUN = 1.98892e30
SEC_PER_SOLAR_MASS = G_NEWTON * M_SUN / C_LIGHT ** 3   # ~4.93e-6 s


# ---------------------------------------------------------------------------
# Static shell quantities
# ---------------------------------------------------------------------------

def f_metric(a, M=1.0):
    return 1.0 - 2.0 * M / a


def sigma_static(a, M=1.0):
    return -np.sqrt(f_metric(a, M)) / (2.0 * np.pi * a)


def p_static(a, M=1.0):
    return (1.0 - M / a) / (4.0 * np.pi * a * np.sqrt(f_metric(a, M)))


# ---------------------------------------------------------------------------
# V'' by two independent routes
# ---------------------------------------------------------------------------

def vpp_closed_form(a0, beta2, M=1.0):
    """Hand-derived second derivative of the effective potential at a0.

        V''(a0) = -4M/a0^3 - 2M^2/(a0^4 f0) + 2(1+2 beta^2)(3M/a0 - 1)/a0^2
    """
    f0 = f_metric(a0, M)
    return (-4.0 * M / a0 ** 3
            - 2.0 * M ** 2 / (a0 ** 4 * f0)
            + 2.0 * (1.0 + 2.0 * beta2) * (3.0 * M / a0 - 1.0) / a0 ** 2)


def vpp_numeric(a0, beta2, M=1.0, h=1e-4):
    """Finite-difference V'' from integrating the shell conservation law."""
    s0, pr0 = sigma_static(a0, M), p_static(a0, M)

    def rhs(a, y):
        sig = y[0]
        p = pr0 + beta2 * (sig - s0)
        return [-(2.0 / a) * (sig + p)]

    def V_at(a_target):
        if abs(a_target - a0) < 1e-15:
            return f_metric(a0, M) - (2 * np.pi * a0 * s0) ** 2
        sol = solve_ivp(rhs, (a0, a_target), [s0], rtol=1e-12, atol=1e-14,
                        dense_output=True)
        sig = float(sol.y[0, -1])
        return f_metric(a_target, M) - (2 * np.pi * a_target * sig) ** 2

    Vm, V0, Vp = V_at(a0 - h), V_at(a0), V_at(a0 + h)
    vpp = (Vp - 2 * V0 + Vm) / h ** 2
    vp = (Vp - Vm) / (2 * h)
    return vpp, V0, vp


def stability_scan():
    rows = []
    for a0 in [2.2, 2.5, 3.0, 4.0, 6.0, 10.0]:
        for beta2 in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            cf = vpp_closed_form(a0, beta2)
            nm, V0, Vp = vpp_numeric(a0, beta2)
            rows.append({
                'a0_over_M': a0, 'beta2': beta2,
                'Vpp_closed_form': float(cf),
                'Vpp_numeric': float(nm),
                'agreement_rel': float(abs(cf - nm) / max(abs(cf), 1e-30)),
                'V_at_a0': float(V0),
                'Vprime_at_a0': float(Vp),
                'stable': bool(cf > 0.0),
            })
    return rows


def critical_beta2(a0, M=1.0):
    """beta^2 at which V''(a0) changes sign, if it exists."""
    try:
        return float(brentq(lambda b2: vpp_closed_form(a0, b2, M), -50.0, 50.0))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# LQR synthesis and delay margin
# ---------------------------------------------------------------------------

def lqr_design(lam, q_pos=1.0, q_vel=1.0, r_ctrl=1.0):
    A = np.array([[0.0, 1.0], [lam ** 2, 0.0]])
    B = np.array([[0.0], [1.0]])
    Q = np.diag([q_pos, q_vel])
    R = np.array([[r_ctrl]])
    P = solve_continuous_are(A, B, Q, R)
    K = np.linalg.solve(R, B.T @ P)          # u = -K x
    Acl = A - B @ K
    return K.flatten(), np.linalg.eigvals(Acl)


def delay_margin_closed_form(lam, K):
    """Smallest tau > 0 admitting a root of s^2 - lam^2 + (K1 + K2 s)e^{-s tau}
    on the imaginary axis.

    Setting s = i w and eliminating tau gives sqrt(K1^2 + K2^2 w^2) = w^2 + lam^2.
    """
    K1, K2 = K

    def g(w):
        return np.sqrt(K1 ** 2 + K2 ** 2 * w ** 2) - (w ** 2 + lam ** 2)

    # bracket the positive root
    ws = np.linspace(1e-6, 50.0, 200000)
    vals = g(ws)
    sign_changes = np.where(np.sign(vals[:-1]) != np.sign(vals[1:]))[0]
    if len(sign_changes) == 0:
        return None, None
    taus = []
    for idx in sign_changes:
        w = brentq(g, ws[idx], ws[idx + 1])
        phi = np.arctan2(K2 * w, K1)
        if phi < 0:
            phi += 2 * np.pi
        taus.append((phi / w, w))
    tau, w = min(taus, key=lambda t: t[0])
    return float(tau), float(w)


def simulate_delayed(lam, K, tau, t_end=200.0, dt=1e-3, x0=(1e-3, 0.0)):
    """Fixed-step RK4 on the delay differential equation, ring-buffer history."""
    K1, K2 = K
    n = int(t_end / dt)
    nd = max(int(round(tau / dt)), 0)
    hist = np.zeros((n + 1, 2))
    hist[0] = x0

    def deriv(i, state):
        j = max(i - nd, 0)
        xd, vd = hist[j]
        u = -(K1 * xd + K2 * vd)
        return np.array([state[1], lam ** 2 * state[0] + u])

    for i in range(n):
        s = hist[i]
        k1 = deriv(i, s)
        k2 = deriv(i, s + 0.5 * dt * k1)
        k3 = deriv(i, s + 0.5 * dt * k2)
        k4 = deriv(i, s + dt * k3)
        hist[i + 1] = s + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        if not np.isfinite(hist[i + 1]).all() or np.abs(hist[i + 1]).max() > 1e6:
            return hist[:i + 2], False
    peak_late = np.abs(hist[int(0.8 * n):, 0]).max()
    return hist, bool(peak_late < abs(x0[0]))


def control_study(a0=2.5, beta2=0.0):
    vpp = vpp_closed_form(a0, beta2)
    assert vpp < 0, 'configuration is already stable; no control needed'
    lam = float(np.sqrt(-vpp / 2.0))

    results = {}
    results['a0_over_M'] = a0
    results['beta2'] = beta2
    results['Vpp'] = float(vpp)
    results['lambda_geometric'] = lam
    results['open_loop_efold_time_M'] = float(1.0 / lam)
    results['throat_light_crossing_M'] = float(a0)

    designs = {}
    for label, (qp, qv, rc) in {
        'cheap_control':   (1.0, 1.0, 1.0),
        'moderate':        (100.0, 10.0, 1.0),
        'aggressive':      (1e4, 1e2, 1.0),
    }.items():
        K, poles = lqr_design(lam, qp, qv, rc)
        tau, w = delay_margin_closed_form(lam, K)
        _, stable_at_half = simulate_delayed(lam, K, 0.5 * tau) if tau else (None, None)
        _, stable_at_double = simulate_delayed(lam, K, 2.0 * tau) if tau else (None, None)
        designs[label] = {
            'K_position': float(K[0]), 'K_velocity': float(K[1]),
            'closed_loop_poles_real': [float(np.real(p)) for p in poles],
            'settling_rate': float(-max(np.real(poles))),
            'delay_margin_M': tau,
            'crossover_freq': w,
            'delay_margin_over_light_crossing': float(tau / a0) if tau else None,
            'sim_stable_at_half_margin': stable_at_half,
            'sim_stable_at_double_margin': stable_at_double,
        }
    results['designs'] = designs

    # Physical timescales for a solar-mass shell.
    results['solar_mass_case'] = {
        'M_seconds': SEC_PER_SOLAR_MASS,
        'efold_time_s': float(SEC_PER_SOLAR_MASS / lam),
        'required_control_bandwidth_Hz': float(lam / SEC_PER_SOLAR_MASS / (2 * np.pi)),
        'light_crossing_s': float(a0 * SEC_PER_SOLAR_MASS),
    }
    return results


if __name__ == '__main__':
    out = {
        'stability_scan': stability_scan(),
        'critical_beta2': {str(a): critical_beta2(a)
                           for a in [2.2, 2.5, 3.0, 4.0, 6.0, 10.0]},
        'control_study': control_study(),
    }
    with open('results_d.json', 'w') as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps(out['control_study'], indent=2))
    print('\ncritical beta^2:', json.dumps(out['critical_beta2'], indent=2))
