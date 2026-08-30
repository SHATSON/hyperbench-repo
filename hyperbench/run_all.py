"""
run_all.py -- Reproduce every numerical claim in the paper.

Usage:  python3 run_all.py
Writes: results_a.json, results_b.json, results_c.json, results_d.json,
        results_summary.json   (pure data -- deterministic, checksummed)
        run_metadata.json      (environment + timing -- varies by machine)

Runtime: ~3-6 minutes on a single modern CPU core. No GPU, no network, no
proprietary data. Deterministic: the only stochastic component is the SLSQP
initial guess in Experiment B, which is seeded.
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import time

import numpy as np
import scipy
import sympy

import exp_a_energy_audit as A
import exp_b_viq as B
import exp_c_warp_scaling as C
import exp_d_control as D
from exp_d_control import lqr_design, delay_margin_closed_form, vpp_closed_form


def environment():
    return {
        'python': sys.version.split()[0],
        'platform': platform.platform(),
        'numpy': np.__version__,
        'scipy': scipy.__version__,
        'sympy': sympy.__version__,
    }


def delay_margin_frontier():
    """Maximum LQR delay margin vs throat light-crossing time."""
    rows = []
    for a0 in [2.2, 2.5, 2.8, 4.0, 6.0, 10.0]:
        vpp = vpp_closed_form(a0, 0.0)
        if vpp >= 0:
            continue
        lam = float(np.sqrt(-vpp / 2.0))
        best, arg = 0.0, None
        for qp in np.logspace(-8, 6, 60):
            for qv in np.logspace(-8, 4, 40):
                K, _ = lqr_design(lam, qp, qv, 1.0)
                tau, _w = delay_margin_closed_form(lam, K)
                if tau and tau > best:
                    best, arg = tau, (float(qp), float(qv))
        rows.append({
            'a0_over_M': a0,
            'lambda': lam,
            'max_delay_margin_M': float(best),
            'light_crossing_M': a0,
            'margin_over_crossing': float(best / a0),
            'lambda_times_tau_max': float(lam * best),
            'argmax_weights': arg,
            'causally_infeasible': bool(best < a0),
        })
    return rows


def main():
    t0 = time.time()
    # Environment and timing are kept OUT of results_summary.json: they differ
    # on every machine, so including them would make the data file impossible
    # to checksum across environments. They go to run_metadata.json instead.
    out = {}

    print('[1/4] Experiment A: symbolic energy-condition audit ...')
    out['A'] = {
        'general_formulas': A.general_formulas(),
        'throat_limit': A.throat_limit(),
        'family_sweep': A.family_sweep(),
    }

    print('[2/4] Experiment B: volume-integral quantifier ...')
    out['B'] = {
        'b1_bound_approach': B.b1_bound_approach(),
        'b2_gradient_constrained': B.b2_sweep(),
    }

    print('[3/4] Experiment C: warp-bubble energy scaling ...')
    out['C'] = {
        'scaling_exponents': C.scaling_study(),
        'thin_wall_asymptotics': C.asymptotic_check(),
        'physical_budget': C.physical_budget(),
    }

    print('[4/4] Experiment D: throat control and delay margin ...')
    out['D'] = {
        'stability_scan': D.stability_scan(),
        'critical_beta2': {str(a): D.critical_beta2(a)
                           for a in [2.2, 2.5, 3.0, 4.0, 6.0, 10.0]},
        'control_study': D.control_study(),
        'delay_margin_frontier': delay_margin_frontier(),
    }

    with open('results_summary.json', 'w') as fh:
        json.dump(out, fh, indent=2, sort_keys=True)

    elapsed = time.time() - t0
    meta = {'environment': environment(), 'wall_clock_seconds': elapsed}
    with open('run_metadata.json', 'w') as fh:
        json.dump(meta, fh, indent=2, sort_keys=True)

    print(f"\nDone in {elapsed:.1f} s")
    print('  results_summary.json  (data of record)')
    print('  run_metadata.json     (environment + timing)')


if __name__ == '__main__':
    main()
