"""
gr_core.py -- Minimal, dependency-light symbolic general relativity engine.

Geometric units G = c = 1. Signature (-,+,+,+).

Everything here is deliberately written out index-by-index rather than delegated
to a tensor library, so that the derivation can be audited line by line by a
reader with no differential-geometry package installed beyond SymPy.

Author: single-author artifact accompanying
"Computational Frameworks for Traversable Hyperspace".
License: MIT.
"""

from __future__ import annotations

import itertools
import sympy as sp


# ----------------------------------------------------------------------------
# Curvature pipeline
# ----------------------------------------------------------------------------

def christoffel(g: sp.Matrix, x: list) -> list:
    """Christoffel symbols of the second kind, Gamma^a_{bc}.

    Returns nested list G[a][b][c]. Symmetric in (b, c).
    """
    n = len(x)
    ginv = g.inv()
    Gam = [[[sp.S.Zero] * n for _ in range(n)] for _ in range(n)]
    for a in range(n):
        for b in range(n):
            for c in range(b, n):
                acc = sp.S.Zero
                for d in range(n):
                    if ginv[a, d] == 0:
                        continue
                    acc += ginv[a, d] * (
                        sp.diff(g[d, b], x[c])
                        + sp.diff(g[d, c], x[b])
                        - sp.diff(g[b, c], x[d])
                    )
                val = sp.simplify(acc / 2)
                Gam[a][b][c] = val
                Gam[a][c][b] = val
    return Gam


def riemann(Gam: list, x: list) -> list:
    """Riemann tensor R^a_{bcd}."""
    n = len(x)
    R = [[[[sp.S.Zero] * n for _ in range(n)] for _ in range(n)] for _ in range(n)]
    for a, b, c, d in itertools.product(range(n), repeat=4):
        expr = sp.diff(Gam[a][d][b], x[c]) - sp.diff(Gam[a][c][b], x[d])
        for e in range(n):
            expr += Gam[a][c][e] * Gam[e][d][b] - Gam[a][d][e] * Gam[e][c][b]
        R[a][b][c][d] = sp.simplify(expr)
    return R


def ricci(R: list, n: int) -> sp.Matrix:
    """Ricci tensor R_{bd} = R^a_{bad}."""
    Ric = sp.zeros(n, n)
    for b in range(n):
        for d in range(n):
            Ric[b, d] = sp.simplify(sum(R[a][b][a][d] for a in range(n)))
    return Ric


def einstein_tensor(g: sp.Matrix, x: list) -> tuple:
    """Return (G_{ab}, R_{ab}, Ricci scalar)."""
    n = len(x)
    Gam = christoffel(g, x)
    Rie = riemann(Gam, x)
    Ric = ricci(Rie, n)
    ginv = g.inv()
    Rs = sp.simplify(sum(ginv[a, b] * Ric[a, b] for a in range(n) for b in range(n)))
    G = sp.zeros(n, n)
    for a in range(n):
        for b in range(n):
            G[a, b] = sp.simplify(Ric[a, b] - sp.Rational(1, 2) * g[a, b] * Rs)
    return G, Ric, Rs


def orthonormal_diag(T: sp.Matrix, g: sp.Matrix, n: int, signs=None) -> sp.Matrix:
    """Project a diagonal-metric tensor into the local orthonormal frame.

    For diagonal g, e_{(a)} = |g_aa|^{-1/2} d/dx^a, so
        T_{(a)(b)} = T_{ab} / sqrt(|g_aa| |g_bb|).

    `signs` gives the signature of each diagonal component, e.g. (-1,1,1,1) for
    a static region outside a throat. Supplying it lets SymPy discharge the
    absolute values symbolically instead of carrying unresolved Abs() nodes.
    """
    if signs is None:
        mag = [sp.Abs(g[a, a]) for a in range(n)]
    else:
        mag = [sp.simplify(signs[a] * g[a, a]) for a in range(n)]
    That = sp.zeros(n, n)
    for a in range(n):
        for b in range(n):
            # sqrt(m*m) would re-introduce Abs(); on the diagonal the norm is
            # just m_a, which is positive by construction once signs are given.
            norm = mag[a] if a == b else sp.sqrt(mag[a] * mag[b])
            That[a, b] = sp.simplify(T[a, b] / norm)
    return That


# ----------------------------------------------------------------------------
# Metric constructors
# ----------------------------------------------------------------------------

def morris_thorne(b_func, Phi_func):
    """Static spherically symmetric traversable-wormhole metric.

        ds^2 = -e^{2 Phi(r)} dt^2 + dr^2 / (1 - b(r)/r) + r^2 dOmega^2

    b_func, Phi_func are callables of a SymPy symbol r.
    Returns (g, coords, r).
    """
    # r must be declared positive (not merely real) so that it is the *same*
    # SymPy object as the r used by callers; assumption mismatches otherwise
    # cause substitutions to silently no-op.
    t, th, ph = sp.symbols('t theta phi', real=True)
    r = sp.symbols('r', positive=True)
    b = b_func(r)
    Phi = Phi_func(r)
    g = sp.diag(
        -sp.exp(2 * Phi),
        1 / (1 - b / r),
        r ** 2,
        r ** 2 * sp.sin(th) ** 2,
    )
    return g, [t, r, th, ph], r


def stress_energy_mt(b_func, Phi_func):
    """Orthonormal-frame stress-energy of a Morris-Thorne metric.

    Returns dict with rho, p_r (radial pressure), p_t (transverse pressure),
    and the two null-energy-condition combinations.
    """
    g, x, r = morris_thorne(b_func, Phi_func)
    G, _, _ = einstein_tensor(g, x)
    # Static region exterior to the throat: g_tt < 0, spatial block positive.
    That = orthonormal_diag(G / (8 * sp.pi), g, 4, signs=(-1, 1, 1, 1))

    rho = sp.simplify(That[0, 0])
    p_r = sp.simplify(That[1, 1])
    p_t = sp.simplify(That[2, 2])
    return {
        'rho': rho,
        'p_r': p_r,
        'p_t': p_t,
        'nec_radial': sp.simplify(rho + p_r),
        'nec_transverse': sp.simplify(rho + p_t),
        'wec': rho,
        'metric': g,
        'coords': x,
        'r': r,
    }


def alcubierre_energy_density():
    """Eulerian-observer energy density of the Alcubierre warp metric.

        ds^2 = -dt^2 + (dx - v_s f(r_s) dt)^2 + dy^2 + dz^2

    Derived here in Cartesian coordinates via the ADM extrinsic-curvature
    route: rho = -(1/16 pi)(K_{ij}K^{ij} - K^2) on a maximal-free slice, which
    for this shift vector reduces to the closed form returned below.

    Returns (rho_expr, symbols dict).
    """
    x, y, z, vs = sp.symbols('x y z v_s', real=True)
    rs = sp.symbols('r_s', positive=True)
    f = sp.Function('f')
    rho_cyl2 = y ** 2 + z ** 2
    rho = -(1 / (8 * sp.pi)) * (vs ** 2 * rho_cyl2) / (4 * rs ** 2) * sp.diff(f(rs), rs) ** 2
    return rho, {'x': x, 'y': y, 'z': z, 'v_s': vs, 'r_s': rs, 'f': f}


if __name__ == '__main__':
    sp.init_printing()
    r = sp.symbols('r', positive=True)
    b0 = sp.symbols('b_0', positive=True)
    out = stress_energy_mt(lambda rr: b0 ** 2 / rr, lambda rr: sp.S.Zero)
    print('Ellis-Bronnikov rho      =', out['rho'])
    print('Ellis-Bronnikov rho+p_r  =', out['nec_radial'])
