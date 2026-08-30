## Abstract

Traversable "hyperspace" — travel that exploits the geometry of spacetime rather than moving faster through it — has been studied for four decades as theoretical physics, but rarely as a problem in computation. This paper argues that several of its decisive obstacles are algorithmic, and develops HYPERBENCH, a reproducible framework in which candidate spacetime geometries are treated as program objects: metrics are compiled from symbolic specifications, curvature and stress-energy are derived automatically, energy conditions are evaluated as machine-checkable predicates, and exotic-matter budgets are posed as constrained optimisation problems.

Four experiments instantiate the framework. An automated symbolic audit rederives the Morris–Thorne stress-energy from the metric alone and reduces null-energy-condition violation at a wormhole throat to a single machine-verified identity, making exoticity a corollary of the flare-out condition rather than an independent postulate. Proposition 1 then establishes that volume-integrated NEC violation obeys |I_V| ≥ b₀/2 in the zero-tidal-force gauge, so total exotic content scales linearly with throat radius and cannot be reduced at fixed aperture. Quadrature over the Alcubierre bubble recovers the scaling law E ∝ −v²R²σ with fitted exponents (2.0000, 1.9995, 0.99998). Finally, treating dynamic throat stabilisation as a feedback control problem reveals a causal control obstruction: the maximum achievable delay margin over the LQR family satisfies λ·τ_max = 0.6046, a scale-invariant constant, and falls strictly below the throat light-crossing time in every configuration tested — so no controller in that family can stabilise the throat causally, independently of whether exotic matter can be sourced at all.

The contribution is not a claim that hyperspace is achievable, but a demonstration that the question admits computational treatment yielding sharper bounds than analytic argument alone has produced. All results reproduce in 81 seconds on one CPU core, with fifteen automated assertions binding each claim to the code that generates it.

**Keywords:** computational general relativity; symbolic computation; traversable wormholes; energy conditions; constrained optimisation; delay margin; reproducible research

---

## 1. Introduction

### 1.1 Motivation

The special-relativistic speed limit constrains motion *through* spacetime. It does not directly constrain the geometry of spacetime itself. This distinction — trivial to state, enormously consequential — is what makes traversable wormholes and warp bubbles objects of serious study rather than fancy. Morris and Thorne (1988) established that general relativity permits metrics describing traversable throats, and Alcubierre (1994) established that it permits metrics in which a bounded region is transported at arbitrary coordinate velocity. Neither result violates relativity. Both demand stress-energy distributions that no known matter provides.

The subsequent literature has been overwhelmingly analytic. Energy conditions were formulated and violated; quantum inequalities were derived and applied (Ford & Roman, 1996, 1997); classification schemes were proposed (Bobrick & Martire, 2021); and no-go theorems were sharpened (Santiago et al., 2022). What has been comparatively scarce is treatment of these geometries as *computational artifacts* — objects that can be specified in machine-readable form, differentiated automatically, audited by decidable procedures, optimised under explicit constraints, and controlled by synthesised feedback laws.

That scarcity is a missed opportunity, and this paper's central claim is that it is a substantive one. Computational framing does not merely re-derive known results more conveniently; it changes which questions are natural to ask. "Does this metric violate the null energy condition?" is a physics question with a known answer. "What is the minimum total exotic content over all admissible shape functions subject to bounded tidal gradient?" is an optimisation question, and its answer (§6.2) is a bound the analytic literature states only obliquely. "Can the throat be stabilised?" is a stability question. "Can it be stabilised by a *causal* controller?" is a control-theoretic question, and its answer (§6.4) is negative for reasons unrelated to exotic matter.

### 1.2 Epistemic status

Because the subject matter borders on science fiction, the author states the epistemic commitments explicitly. Readers should hold this paper to them.

**This paper does not claim** that traversable wormholes or warp drives exist, are constructible, or are likely to be constructible. It does not claim that exotic matter of the required magnitude can be sourced. It does not claim to solve quantum gravity, and takes no position on whether semiclassical general relativity remains valid in the regimes discussed.

**This paper does claim**, and supports with reproducible computation: (a) candidate geometries admit fully automated symbolic analysis, with energy-condition audits that are machine-checkable rather than hand-verified; (b) total exotic content of a zero-tidal-force wormhole is bounded below in proportion to throat radius (Proposition 1); (c) the Alcubierre negative-energy budget obeys a clean three-parameter scaling law whose exponents are recoverable to four significant figures; and (d) dynamic throat stabilisation faces a delay-margin obstruction that is quantitative, scale-invariant within the model, and independent of the exotic-matter question.

The models are *reduced-order surrogates*, and §6.5 and §10 enumerate their limitations candidly. The thin-shell control model in particular collapses a field-theoretic problem to two states; its conclusions establish that a barrier exists in the reduced model, not that no controller of any kind could exist. The author regards that obstruction as suggestive but not dispositive, and §10 identifies precisely what a full field-theoretic treatment would need to show to overturn it.

The framing throughout is that of a long-horizon research programme, in the sense that fusion energy was a research programme in 1955: the physics is not settled, the engineering is not begun, and the honest contribution at this stage is to make the obstacles precise enough to attack.

### 1.3 Contributions

1. **HYPERBENCH**, a dependency-light framework (NumPy, SciPy, SymPy only) in which spacetime metrics are program objects and energy conditions are decidable predicates (§5).
2. An **automated energy-condition audit** that derives the Morris–Thorne stress-energy with no physical input, verifies it against published expressions, and reduces throat NEC violation to a one-line identity (§6.1).
3. **Proposition 1**, a lower bound |I_V| ≥ b₀/2 on volume-integrated NEC violation in the zero-tidal-force gauge, with proof, numerical confirmation to machine precision, and reconciliation with the small-violation theorem of Visser et al. (2003) (§6.2).
4. A **validated optimisation layer**: a general-purpose SLSQP solver recovers an analytically derived constrained optimum to within 3.7 × 10⁻⁴ relative error, licensing its use where no closed form exists (§6.2).
5. **Empirical scaling exponents** for the Alcubierre negative-energy integral, with thin-wall asymptotics verified to 3 × 10⁻¹¹ and conversion to engineering mass-equivalents (§6.3).
6. A **causal control obstruction** for dynamic throat stabilisation, with the delay margin computed in closed form and verified by direct integration of the delay differential equation (§6.4).
7. A **six-milestone benchmark roadmap** (§7.3) and a complete, test-covered **reproducibility artifact** (§9).

---

## 2. Background and Related Work

### 2.1 Traversable wormholes

Morris and Thorne (1988) inverted the usual procedure of general relativity: rather than solving the field equations for a given matter distribution, they *specified* a traversable geometry and read off the stress-energy required to support it. That inversion is the methodological ancestor of this paper's framework, and it is computational in spirit — it treats the metric as the free variable and matter as the derived quantity.

The consequence was immediate and unwelcome. Traversability forces violation of the null energy condition at the throat (Morris & Thorne, 1988; Morris et al., 1988). Hochberg and Visser (1998) generalised this to dynamic wormholes. Visser et al. (2003) then showed that the *total* amount of exotic matter, measured by a volume-integral quantifier, can be made arbitrarily small — a result frequently cited as softening the problem. Section 6.2 examines that claim quantitatively and shows the softening is real but purchased at a specific price.

Thin-shell constructions (Poisson & Visser, 1995) concentrate exotic matter on a hypersurface via the Israel junction conditions, converting a field problem into a finite-dimensional dynamical one. This tractability makes them the natural substrate for the control analysis of §6.4.

### 2.2 Warp drives

Alcubierre's (1994) metric contracts space ahead of a bubble and expands it behind, transporting the interior at arbitrary coordinate velocity while the interior remains locally inertial. Natário (2002) produced a zero-expansion variant, demonstrating that the contraction/expansion picture is gauge-dependent rather than essential.

Critiques accumulated quickly. Pfenning and Ford (1997) applied quantum inequalities to bound bubble wall thickness and found energy requirements astronomical. Olum (1998) showed superluminal travel generically requires negative energy. Lobo and Visser (2004) established fundamental limitations on linearised warp spacetimes. Most recently, Santiago et al. (2022) argued that generic warp drives violate the NEC, substantially constraining the more optimistic proposals of Lentz (2021) and Fell and Heisenberg (2021). Bobrick and Martire (2021) provided a useful classification and argued that subluminal "physical" warp drives are considerably less exotic than superluminal ones.

Van Den Broeck (1999) showed that a clever topology — a large interior volume connected through a narrow neck to a microscopic bubble surface — reduces total energy requirements by many orders of magnitude. This is precisely the kind of result the optimisation framing of §6.2 is designed to systematise: a *shape optimisation* discovery, found by hand.

### 2.3 Energy conditions and their status

The energy conditions are not theorems of general relativity; they are side conditions imposed to exclude pathology. Curiel (2017) and Barceló and Visser (2002) document that essentially every pointwise energy condition is violated by ordinary quantum fields somewhere, the Casimir effect being canonical. Quantum inequalities (Ford & Roman, 1996, 1997) restore order by bounding the *duration and magnitude* of negative energy density rather than forbidding it outright.

This matters methodologically. A framework treating "violates the NEC" as a fatal verdict would be too blunt. HYPERBENCH therefore reports energy-condition violation as a *quantitative* audit — pointwise magnitude, volume integral, and scaling — rather than a boolean.

### 2.4 Higher-dimensional spacetime

Kaluza–Klein theory (Overduin & Wesson, 1997) and the Randall–Sundrum braneworld models (Randall & Sundrum, 1999a, 1999b) provide the standard settings in which extra dimensions are physically meaningful rather than merely formal. In braneworld scenarios the effective four-dimensional Einstein equations acquire correction terms from bulk curvature, which can in principle support wormhole-like throats without four-dimensional exotic matter — the exoticity is exported to the bulk.

The author flags a common conflation. "Hyperspace" in fiction typically means a *separate manifold* through which travel is faster; extra dimensions in string theory and braneworld models are compactified or warped, not separate highways. The two are not the same idea, and §3.2 keeps them distinct.

### 2.5 Quantum-gravitational traversability

A genuinely different line of attack comes from holography. Gao et al. (2017) showed that a double-trace deformation coupling the two boundaries of an eternal anti-de Sitter black hole renders the wormhole traversable, with negative energy supplied by a quantum effect rather than postulated matter. Maldacena et al. (2023) constructed a four-dimensional traversable wormhole using Casimir energy from fermion fields. Maldacena and Susskind (2013) connect entanglement to geometric connection.

These are the most physically credible traversability results available, and they share a feature worth emphasising: the wormholes they produce are microscopic, slower than the ambient light-travel time between mouths, and useless for transport. They establish that traversability is not forbidden in principle while illustrating how severely it is constrained.

Jafferis et al. (2022) reported a wormhole-inspired teleportation protocol on a quantum processor; Kobrin et al. (2023) subsequently showed the learned Hamiltonian did not exhibit the claimed gravitational features. The author cites this as a cautionary case: in this field the gap between a suggestive simulation and a physical claim is easy to elide, and computational work must be disciplined about which is which.

### 2.6 Computational general relativity, and the gap

Numerical relativity is mature. The ADM 3+1 decomposition (Arnowitt et al., 2008) recasts Einstein's equations as a constrained evolution system; the BSSN reformulation (Shibata & Nakamura, 1995; Baumgarte & Shapiro, 1999) achieves the strong hyperbolicity needed for stable long-term evolution. Production codes — the Einstein Toolkit (Löffler et al., 2012), GRChombo (Clough et al., 2015), NRPy+ (Ruchlin et al., 2018) — routinely evolve binary mergers. Symbolic tooling (Meurer et al., 2017) automates curvature computation.

**The gap.** These tools were built for *astrophysical* spacetimes: black holes, neutron stars, gravitational collapse. Their assumptions — asymptotic flatness with trivial topology, matter satisfying energy conditions, no requirement to *design* a metric to specification — are precisely the assumptions hyperspace research must relax. Conversely, the wormhole and warp-drive literature is largely analytic and rarely ships reproducible code. HYPERBENCH is positioned in that gap: not a replacement for numerical relativity, but a lightweight, auditable layer for the design and screening problems that precede any full evolution.

---

## 3. Mathematical Foundations

### 3.1 Lorentzian manifolds and the 3+1 split

Spacetime is modelled as a smooth four-dimensional Lorentzian manifold (M, g) with signature (−,+,+,+). Geometric units G = c = 1 are used throughout; §6.3 restores SI units. The Einstein field equations are

$$G_{\mu\nu} = R_{\mu\nu} - \tfrac{1}{2} g_{\mu\nu} R = 8\pi T_{\mu\nu}.$$

The ADM decomposition (Arnowitt et al., 2008) foliates M into spacelike hypersurfaces Σ_t with lapse α, shift β^i, and induced metric γ_ij:

$$ds^2 = -(\alpha^2 - \beta_i\beta^i)\,dt^2 + 2\beta_i\,dx^i dt + \gamma_{ij}\,dx^i dx^j.$$

This split is what makes spacetime *computable*: it converts a boundary-value problem on a four-manifold into an initial-value problem with constraints. It is also what makes the control framing of §6.4 natural — evolution in t is exactly what a controller acts on.

### 3.2 Wormhole topology and the flare-out condition

A traversable wormhole is a spacetime whose spatial sections are multiply connected, joining two asymptotically flat regions through a throat. The Morris–Thorne form is

$$ds^2 = -e^{2\Phi(r)}dt^2 + \frac{dr^2}{1 - b(r)/r} + r^2 d\Omega^2,$$

with redshift function Φ(r) and shape function b(r). Traversability imposes: (i) Φ finite everywhere, so no horizon forms; (ii) a throat at r = b₀ with b(b₀) = b₀; (iii) the **flare-out condition** b′(b₀) < 1, the statement that the embedded surface opens outward from the throat rather than closing.

Requirement (iii) is geometric, not physical. Its physical consequence — NEC violation — is derived automatically in §6.1.

**Topology change.** Geroch (1967) established that spatial topology change in a compact spacetime requires either closed timelike curves or a degenerate metric. A wormhole must therefore either be eternal, or be created by a process generating causal pathology. The framework treats topology as fixed at initialisation; dynamic topology change is out of scope and, in the author's judgement, a harder obstacle than exotic matter.

### 3.3 Formal problem statement

Let M(θ) be a family of metrics parameterised by θ ∈ Θ ⊂ ℝⁿ. Define the **exoticity functional**

$$\mathcal{E}(\theta) = \int_\Sigma \max\!\left(0,\, -(\rho + p_r)\right) dV,$$

the **volume-integral quantifier** (Visser et al., 2003)

$$I_V(\theta) = \oint (\rho + p_r)\,dV,$$

and **traversability constraints** C(θ) ≤ 0 comprising horizon absence, flare-out, bounded tidal acceleration, and asymptotic flatness.

The design problem is to minimise |I_V(θ)| over θ ∈ Θ subject to C(θ) ≤ 0; the control problem is to stabilise the resulting configuration against perturbation. Section 6.2 solves an instance of the former in closed form and validates a numerical solver against it; §6.4 shows the latter is obstructed.

---

## 4. Physics Models Implemented

### 4.1 Morris–Thorne class

The symbolic layer accepts arbitrary b(r) and Φ(r) and derives the orthonormal-frame stress-energy. The published results (Morris & Thorne, 1988) are

$$\rho = \frac{b'}{8\pi r^2}, \qquad p_r = \frac{1}{8\pi}\left[\frac{2(1-b/r)\Phi'}{r} - \frac{b}{r^3}\right],$$

and §6.1 rederives both from the metric alone as a correctness check.

### 4.2 Alcubierre warp bubble

$$ds^2 = -dt^2 + \left(dx - v_s f(r_s)\,dt\right)^2 + dy^2 + dz^2,$$

with r_s the distance from the bubble centre and f a top-hat profile. The Eulerian energy density is

$$\rho = -\frac{1}{8\pi}\frac{v_s^2 (y^2+z^2)}{4 r_s^2}\left(\frac{df}{dr_s}\right)^2 \le 0 \ \text{everywhere}.$$

Integrating over a sphere and using ∫₀^π sin³θ dθ = 4/3 gives the exact reduction used in §6.3:

$$E = -\frac{v_s^2}{12}\int_0^\infty r^2 f'(r)^2\,dr.$$

### 4.3 Poisson–Visser thin shell

Two Schwarzschild exteriors of mass M glued at radius a (Poisson & Visser, 1995). The Israel junction conditions give

$$\sigma_0 = -\frac{\sqrt{f_0}}{2\pi a_0}, \qquad p_0 = \frac{1 - M/a_0}{4\pi a_0 \sqrt{f_0}}, \qquad f(a) = 1 - \frac{2M}{a},$$

with σ₀ < 0 confirming exoticity. Shell dynamics obey ȧ² = −V(a) with V(a) = f(a) − (2πaσ(a))², closed by the conservation law dσ/da = −(2/a)(σ + p) and a linearised equation of state p = p₀ + β²(σ − σ₀).

### 4.4 Higher-dimensional extensions

The framework specifies, but does not yet implement, braneworld extensions in which the effective four-dimensional equations acquire a bulk Weyl term. The author reports this candidly as the framework's least developed component: the symbolic layer handles arbitrary-dimensional metrics, but no experiment in §6 exercises D > 4. Milestone M4 (§7.3) targets this gap.

---

## 5. The HYPERBENCH Framework

### 5.1 Design principles

Four principles governed the implementation, each chosen against a specific failure mode.

1. **Auditability over performance.** Curvature is computed index-by-index in explicit loops rather than delegated to an opaque tensor package. The framework is not fast; it is checkable.
2. **Minimal dependencies.** NumPy, SciPy, SymPy — nothing else, so results reproduce a decade from now.
3. **Derive, don't quote.** Every physical formula used is rederived by the engine and checked against the literature value.
4. **Cross-validate every load-bearing number.** Where a quantity determines a conclusion, it is computed twice by independent routes.

### 5.2 Architecture

The framework is a four-stage pipeline, shown in Figure 1. A metric specification enters at the top; each stage consumes the previous stage's output and emits a machine-readable artifact. Stages 3A and 3B are *alternative consumers* of the audit layer's output rather than sequential steps: optimisation asks how cheap a geometry can be made, control asks whether the resulting geometry can be held stable.

![**Figure 1.** Architecture of the HYPERBENCH pipeline. Generated by `figures/make_architecture_figure.py`.](figures/architecture.png){width=6.1in}

**Table 1.** Stage responsibilities and independent validation.

| Stage | Input | Output | Independent validation |
|---|---|---|---|
| 1 — Symbolic | Metric with free functions | ρ, p_r, p_t | Symbolic match to published Morris–Thorne forms |
| 2 — Audit | Stress-energy | NEC/WEC verdicts, I_V | Analytic bound (Proposition 1) used as test oracle |
| 3A — Optimisation | I_V and constraints | Optimal shape function | Closed-form optimum for the gradient-limited case |
| 3B — Control | Growth rate λ | Feedback gains, delay margin τ | Direct integration of the delay differential equation |

### 5.3 Algorithm 1: automated energy-condition audit

```
Input:  metric g(x; theta), coordinates x, frame signature s
Output: (rho, p_r, p_t) and NEC / WEC predicates

1  g_inv <- inverse(g)
2  for a,b,c:  Gamma^a_bc <- 1/2 g^ad ( d_c g_db + d_b g_dc - d_d g_bc )
3  for a,b,c,d:
       R^a_bcd <- d_c Gamma^a_db - d_d Gamma^a_cb
                  + Gamma^a_ce Gamma^e_db - Gamma^a_de Gamma^e_cb
4  R_bd <- sum_a R^a_bad ;   R <- g^ab R_ab
5  G_ab <- R_ab - 1/2 g_ab R
6  T_(a)(b) <- G_ab / (8 pi m_a)      where m_a = s_a g_aa
7  rho <- T_(0)(0) ;  p_r <- T_(1)(1) ;  p_t <- T_(2)(2)
8  return NEC = (rho + p_r >= 0) and (rho + p_t >= 0)
          WEC = NEC and (rho >= 0)
```

Step 6 deserves comment, because it caused the only substantive implementation bug encountered. The naive projection T₍a₎₍b₎ = T_ab / √(|g_aa||g_bb|) produces absolute-value nodes that SymPy cannot discharge without domain assumptions, and on the diagonal √(m·m) reintroduces the absolute value even when the sign is known. Passing the frame signature explicitly and using T₍a₎₍a₎ = T_aa / m_a on the diagonal eliminates this. The bug is worth reporting because it is silent: it raises no error, merely blocking simplification, so downstream substitutions then fail in ways easily mistaken for physics.

A second silent failure mode: SymPy symbols carrying different assumptions (`real=True` versus `positive=True`) are *distinct objects*, so `expr.subs(r, b0)` silently no-ops if the caller's `r` was declared differently from the constructor's. The framework declares radial coordinates `positive` uniformly. Both pitfalls are documented in the artifact.

### 5.4 Complexity

For an n-dimensional metric with symbolic entries, the Christoffel computation performs O(n³) independent evaluations, each summing n terms of three derivatives, reduced by symmetry in the lower index pair. The Riemann tensor requires O(n⁴) entries each with O(n) products, giving O(n⁵) operations. For n = 4 this is 40 unique Christoffel symbols and 256 Riemann components.

The asymptotic count is not the binding constraint. Symbolic simplification dominates, and its cost depends on expression swell in the metric functions rather than on n. Empirically the full Experiment A audit — including a general derivation with undetermined b(r) and Φ(r) plus a five-member family sweep — completes within the 81 s total runtime of the artifact on one core. Diagonal metrics keep swell tractable; non-diagonal metrics (Kerr-like, or Alcubierre in Cartesian form) behave markedly worse, which is why §6.3 uses the analytically reduced integral rather than a brute-force symbolic route.

---

## 6. Experiments and Results

All numbers below are produced by `run_all.py` in 81.3 s on one CPU core (Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1, SymPy 1.14.0, Linux x86-64) and stored in `results/results_summary.json`. Fifteen automated assertions in `tests/test_paper_claims.py` bind each claim below to the code that produces it.

### 6.1 Experiment A — Automated energy-condition audit

**Setup.** The engine receives only the Morris–Thorne line element with *undetermined* functions b(r) and Φ(r) and must produce the orthonormal stress-energy. No physical input is supplied.

**Correctness.** The derived expressions are

$$\rho = \frac{b'(r)}{8\pi r^2}, \qquad p_r = \frac{2r^2\Phi' - 2rb\Phi' - b}{8\pi r^3},$$

which match the published forms of Morris and Thorne (1988) symbolically. The engine also reproduces the Ellis–Bronnikov case b = b₀²/r exactly, giving ρ = −b₀²/8πr⁴ and ρ + p_r = −b₀²/4πr⁴.

**Main result.** Substituting the local linear model b(r) = b₀ + b′·(r − b₀) in the zero-tidal-force gauge Φ = 0 yields, at the throat,

$$\left(\rho + p_r\right)\Big|_{r=b_0} = \frac{b'(b_0) - 1}{8\pi b_0^2}.$$

This is the framework's cleanest illustration of value. The flare-out condition b′(b₀) < 1 is a *geometric* requirement — the throat opens outward. The identity shows it is algebraically identical to NEC violation. Exotic matter is not an additional physical assumption layered onto wormhole construction; it is the flare-out condition rewritten. Spot-checks across b′ ∈ {−1, 0, ½, 9/10, 99/100} confirm negativity throughout, with the violation vanishing as b′ → 1⁻ — the marginal case where the throat ceases to flare.

**Table 2.** Family sweep for b(r) = b₀^(1+α)/r^α. Engine output matched the independently computed analytic form in every case.

| α | b′(b₀) | ρ | (ρ + p_r) at throat | flare-out |
|---|---|---|---|---|
| 1/4 | −1/4 | −b₀^(5/4) / 32πr^(13/4) | −5 / 32πb₀² | satisfied |
| 1/2 | −1/2 | −b₀^(3/2) / 16πr^(7/2) | −3 / 16πb₀² | satisfied |
| 1 | −1 | −b₀² / 8πr⁴ | −1 / 4πb₀² | satisfied |
| 2 | −2 | −b₀³ / 4πr⁵ | −3 / 8πb₀² | satisfied |
| 4 | −4 | −b₀⁵ / 2πr⁷ | −5 / 8πb₀² | satisfied |

The pattern (ρ + p_r)|_{b₀} = −(1+α)/8πb₀² is evident and consistent with the identity above, since b′(b₀) = −α for this family.

### 6.2 Experiment B — Volume-integral quantifier and Proposition 1

Pointwise NEC violation says nothing about *how much* exotic matter is needed. Visser et al. (2003) introduced the volume-integral quantifier and demonstrated geometries with arbitrarily small |I_V|. This experiment examines what that result costs.

In the zero-tidal-force gauge, substituting ρ and p_r with dV = 4πr²dr collapses the integral to

$$I_V = \frac{1}{2}\int_{b_0}^{\infty}\left(b'(r) - \frac{b(r)}{r}\right)dr.$$

> **Proposition 1.** *Let b be any admissible shape function: b(b₀) = b₀, b(r) ≥ 0, b(r) → 0 as r → ∞ (asymptotic flatness), and b differentiable on (b₀, ∞). Then in the gauge Φ = 0,*
>
> $$|I_V| \ \ge\ \frac{b_0}{2},$$
>
> *with equality approached only in the limit where ∫ b/r dr → 0.*
>
> *Proof.* Split the integral. The first term telescopes: ∫ b′ dr = b(∞) − b(b₀) = −b₀ by asymptotic flatness and the throat condition. Hence
>
> $$I_V = \frac{1}{2}\left(-b_0 - \int_{b_0}^{\infty}\frac{b(r)}{r}\,dr\right).$$
>
> Since b ≥ 0 and r > 0 on the domain, the remaining integral is non-negative. Therefore I_V ≤ −b₀/2 < 0, and |I_V| ≥ b₀/2. ∎

**Interpretation.** Proposition 1 does not contradict Visser et al. (2003); it explains their result. Their constructions achieve arbitrarily small |I_V| by making the *throat itself* arbitrarily small, and the follow-up literature notes that such wormholes must be either submicroscopic or exhibit a large discrepancy between throat size and curvature radius. Proposition 1 makes the trade explicit: **exotic content scales linearly with throat radius, so it cannot be reduced at fixed aperture.** A wormhole one metre across requires, in geometric units, at least 0.5 m of integrated NEC violation — about 6.7 × 10²⁶ kg of mass-equivalent using the conversion factor of §6.3. This is an engineering statement, and a discouraging one.

**Numerical confirmation (B1).** For b = b₀^(1+α)/r^α the closed form is I_V = −b₀(α+1)/2α. Adaptive quadrature on the semi-infinite interval reproduces it to machine precision, and the bound holds in every case.

**Table 3.** Confirmation of Proposition 1 across the power family.

| α | \|I_V\| / b₀ (analytic) | relative error | ≥ 0.5? |
|---|---|---|---|
| 0.5 | 1.500000 | 1.0 × 10⁻¹⁵ | yes |
| 1 | 1.000000 | 2.2 × 10⁻¹⁶ | yes |
| 2 | 0.750000 | 0 | yes |
| 5 | 0.600000 | 0 | yes |
| 10 | 0.550000 | 0 | yes |
| 50 | 0.510000 | 1.1 × 10⁻¹⁵ | yes |
| 200 | 0.502500 | 8.0 × 10⁻¹⁵ | yes |

The floor is approached monotonically but never attained, exactly as Proposition 1 predicts.

**Constrained optimisation (B2).** Physically, b cannot fall arbitrarily steeply: gradient bounds proxy for bounded tidal stress. Imposing |b′| ≤ B, the pointwise-minimal admissible shape function is the steepest ramp b(r) = max(0, b₀ − B(r − b₀)), optimal because it minimises b(r) pointwise and hence minimises ∫ b/r dr. Its cost evaluates to

$$|I_V|_{\min}(B) = \frac{b_0}{2}(B+1)\ln\!\left(1 + \frac{1}{B}\right) \ \longrightarrow\ \frac{b_0}{2} \ \text{ as } B \to \infty.$$

An SLSQP optimiser was then given 60 free nodal values, box constraints, slope constraints, and a seeded random initialisation — but **no knowledge of the analytic solution**.

**Table 4.** Optimiser validation against the closed-form gradient-limited optimum.

| B | \|I_V\| numeric | \|I_V\| analytic | relative error | ratio to bound |
|---|---|---|---|---|
| 0.5 | 0.824262 | 0.823959 | 3.7 × 10⁻⁴ | 1.648 |
| 1 | 0.693255 | 0.693147 | 1.6 × 10⁻⁴ | 1.386 |
| 2 | 0.608242 | 0.608198 | 7.2 × 10⁻⁵ | 1.216 |
| 5 | 0.546980 | 0.546965 | 2.8 × 10⁻⁵ | 1.094 |
| 10 | 0.524213 | 0.524206 | 1.4 × 10⁻⁵ | 1.048 |
| 50 | 0.504968 | 0.504967 | 2.9 × 10⁻⁶ | 1.010 |

Agreement to within 3.7 × 10⁻⁴ validates the optimisation layer against ground truth, licensing its use where no closed form exists.

**Two methodological notes.** First, an early version of this experiment produced |I_V| values *below* the proven bound — an impossibility revealing a specification error rather than a mathematical one. The truncated domain allowed the optimiser to leave b non-zero at the outer edge, silently discarding the −b₀ boundary term. The optimiser was correctly solving the wrong problem. The analytic bound functioned as a *test oracle*; without it the erroneous result would have looked publishable. Constrained optimisers exploit under-specified constraints reliably, and in this domain the constraint easiest to forget — asymptotic matching to flat space — is the one carrying the physics.

Second, the original quadrature used a truncated uniform grid, which for slowly decaying shape functions discards a tail of order r_max^(−α) — still about 1% at r_max = 10⁴b₀ when α = 0.5. Switching to adaptive quadrature on [b₀, ∞) improved agreement from 10⁻³ to 10⁻¹⁵. This error was caught by the automated test suite, not by inspection.

### 6.3 Experiment C — Warp-bubble negative-energy scaling

**Setup.** The reduced integral E = −(v²/12)∫ r²f′(r)² dr is evaluated by adaptive quadrature for the top-hat profile f(r) = [tanh(σ(r+R)) − tanh(σ(r−R))] / (2 tanh σR), with the integration range split around the sharply peaked wall at r = R so that no quadrature scheme can miss it.

**Table 5.** Fitted scaling exponents from log-log regression over v ∈ [0.1, 10], R ∈ [10, 1000] m, σ ∈ [0.5, 100] m⁻¹.

| parameter | fitted exponent | predicted | max log residual |
|---|---|---|---|
| v | 2.0000 | 2 | 1.8 × 10⁻¹⁵ |
| R | 1.9995 | 2 | 1.4 × 10⁻³ |
| σ | 0.99998 | 1 | 6.4 × 10⁻⁵ |

So E ∝ −v²R²σ. The energy scales *linearly* in inverse wall thickness — thinner walls are linearly more expensive, which is the quantitative content of the objection raised by Pfenning and Ford (1997).

**Table 6.** Thin-wall asymptotics: quadrature against the closed form E → −v²R²σ/36.

| σR | E (quadrature) | E (formula) | relative error |
|---|---|---|---|
| 10² | −277.787 | −277.778 | 3.2 × 10⁻⁵ |
| 5 × 10² | −1388.891 | −1388.889 | 1.3 × 10⁻⁶ |
| 2 × 10³ | −5555.556 | −5555.556 | 8.1 × 10⁻⁸ |
| 10⁴ | −27777.778 | −27777.778 | 3.2 × 10⁻⁹ |
| 10⁵ | −277777.778 | −277777.778 | 3.4 × 10⁻¹¹ |

**Table 7.** Engineering budget, converting geometric length to mass via c²/G = 1.3465 × 10²⁷ kg m⁻¹.

| configuration | E (geometric, m) | mass-equivalent (kg) | solar masses |
|---|---|---|---|
| R = 100 m, wall 1 m, v = c | −2.78 × 10² | −3.74 × 10²⁹ | −0.19 |
| R = 100 m, wall 1 cm, v = c | −2.78 × 10⁴ | −3.74 × 10³¹ | −18.8 |
| R = 100 m, wall 1 mm, v = c | −2.78 × 10⁵ | −3.74 × 10³² | −188 |
| R = 100 m, wall 1 μm, v = c | −2.78 × 10⁸ | −3.74 × 10³⁵ | −1.88 × 10⁵ |
| R = 100 m, wall 1 pm, v = c | −2.78 × 10¹⁴ | −3.74 × 10⁴¹ | −1.88 × 10¹¹ |
| R = 10 m, wall 1 mm, v = c | −2.78 × 10³ | −3.74 × 10³⁰ | −1.88 |
| R = 100 m, wall 1 mm, v = 0.1c | −2.78 × 10³ | −3.74 × 10³⁰ | −1.88 |

Two observations. First, quantum inequalities (Ford & Roman, 1997; Pfenning & Ford, 1997) force wall thicknesses far below 1 mm for macroscopic bubbles, pushing requirements into the last rows. Second, the v² scaling means subluminal operation helps quadratically but not qualitatively — a tenfold speed reduction buys two orders of magnitude against a deficit spanning eleven. The Van Den Broeck (1999) topology attacks the R² factor rather than v², which is why it achieves far larger reductions, and this is exactly the structural insight the optimisation framing of §6.2 is designed to search for systematically.

### 6.4 Experiment D — Dynamic stabilisation and the causal control obstruction

This is the paper's principal computational contribution, and the one least anticipated by the physics literature.

**Model validation.** For the Poisson–Visser thin shell the static junction conditions should give V(a₀) = V′(a₀) = 0 identically. The framework confirms this across a 30-point scan of (a₀/M, β²): max |V(a₀)| = 1.1 × 10⁻¹⁶ and max |V′(a₀)| = 4.3 × 10⁻⁹ (finite-difference limited). The second derivative was computed by two independent routes — a hand-derived closed form,

$$V''(a_0) = -\frac{4M}{a_0^3} - \frac{2M^2}{a_0^4 f_0} + \frac{2(1+2\beta^2)(3M/a_0 - 1)}{a_0^2},$$

and finite-differencing of V obtained by numerically integrating the shell conservation ODE. They agree to a maximum relative discrepancy of 3.1 × 10⁻⁶.

**Table 8.** Critical equation-of-state parameter at which V″(a₀) changes sign.

| a₀/M | β² critical | stable region |
|---|---|---|
| 2.2 | +3.875 | β² > 3.875 |
| 2.5 | +3.500 | β² > 3.500 |
| 3.0 | — | none (V″ < 0 for all β²) |
| 4.0 | −1.750 | β² < −1.750 |
| 6.0 | −0.875 | β² < −0.875 |
| 10.0 | −0.652 | β² < −0.652 |

For a₀ > 3M the sign of the (3M/a₀ − 1) factor flips, so stability demands β² < 0 — a negative squared sound speed, itself exotic. This reproduces the qualitative structure found by Poisson and Visser (1995).

**Control formulation.** Expanding about a₀ where V = V′ = 0 gives ẍ = −½V″(a₀)x, so unstable configurations grow at rate λ = √(−V″/2). Adding a lumped control input u — modulation of the shell's surface stress, normalised to a radial acceleration — yields the plant

$$\ddot{x} = \lambda^2 x + u, \qquad A = \begin{pmatrix}0&1\\ \lambda^2&0\end{pmatrix},\quad B = \begin{pmatrix}0\\1\end{pmatrix}.$$

For the reference configuration a₀ = 2.5M, β² = 0: V″ = −0.448, λ = 0.47329 M⁻¹, open-loop e-folding time 2.113 M.

**LQR synthesis and delay margin.** For each design the delay margin τ — the largest feedback latency preserving stability — was computed in closed form. Setting s = iω in the characteristic equation s² − λ² + (K₁ + K₂s)e^(−sτ) = 0 and eliminating τ gives √(K₁² + K₂²ω²) = ω² + λ², after which τ = arg(K₁ + iK₂ω)/ω. Appendix A gives the derivation.

**Table 9.** LQR designs and their delay margins.

| design | K₁ | K₂ | closed-loop poles | τ (M) | τ / (a₀/c) |
|---|---|---|---|---|---|
| cheap | 1.249 | 1.870 | −0.935 (double) | 0.658 | 0.263 |
| moderate | 10.227 | 5.518 | −2.759 (double) | 0.219 | 0.087 |
| aggressive | 100.224 | 17.333 | −8.667 (double) | 0.069 | 0.028 |

Direct integration of the delay differential equation (RK4, ring-buffer history) confirms stability at τ/2 and divergence at 2τ for every design, validating the closed-form margin.

**The obstruction.** Note the trend: tighter control *shrinks* the delay margin. This is the classical tension between bandwidth and latency tolerance, and it means the instability cannot be out-muscled. Sweeping 2 400 LQR weight combinations across six configurations to find the *maximum achievable* margin gives Table 10.

**Table 10.** Maximum LQR delay margin against throat light-crossing time.

| a₀/M | λ (M⁻¹) | τ_max (M) | light-crossing (M) | τ_max / crossing | λ·τ_max |
|---|---|---|---|---|---|
| 2.2 | 0.7631 | 0.792 | 2.2 | 0.360 | 0.6046 |
| 2.5 | 0.4733 | 1.278 | 2.5 | 0.511 | 0.6046 |
| 2.8 | 0.3727 | 1.622 | 2.8 | 0.579 | 0.6046 |
| 4.0 | 0.2339 | 2.585 | 4.0 | 0.646 | 0.6046 |
| 6.0 | 0.1559 | 3.878 | 6.0 | 0.646 | 0.6046 |
| 10.0 | 0.0955 | 6.329 | 10.0 | 0.633 | 0.6046 |

Two things stand out. First, **λ·τ_max = 0.6046 in every case** — a scale-invariant constant, as dimensional analysis of the plant 1/(s² − λ²) requires. This is consistent with the general result of Middleton and Miller (2007), who proved that a strictly proper real-rational plant admits a uniform upper bound on tolerable delay under linear time-invariant control precisely when it has a closed right-half-plane pole away from the origin. Second, and decisively, **τ_max < a₀/c in every configuration**.

> **Result 2 (causal control obstruction).** *Any sensor–actuator loop spanning the throat incurs a latency of at least the light-crossing time a₀/c. Since the maximum LQR delay margin satisfies τ_max = 0.6046/λ < a₀/c for every configuration tested, no controller in the LQR family can stabilise the throat causally.*

The obstruction is not an artifact of a marginal parameter choice. Defining the dimensionless quantity λ·a₀ — the ratio of light-crossing time to instability e-folding time — the framework finds:

- λ·a₀ = 1 **exactly** at a₀ = 3M;
- λ·a₀ > 1 for a₀ < 3M, rising to 3.20 at a₀ = 2.05M;
- λ·a₀ attains a global minimum of **0.9306 at a₀ = (3 + √3)M ≈ 4.7321M**;
- λ·a₀ → 1 from below as a₀ → ∞ (computed value 0.99999995 at a₀ = 10⁷M).

So λ·a₀ ∈ [0.9306, ∞) over the entire admissible range. Even against the most generous conceivable delay-margin bound for a single unstable pole (λτ < 1, achievable only by controllers outside the LQR family), the instability e-folding time never exceeds the light-crossing time by more than about 7%. The control problem is at absolute best marginal, and for a₀ ≤ 3M infeasible even under that generous bound.

**Physical timescales.** For a solar-mass shell (M = 4.927 μs in geometric time) at a₀ = 2.5M: e-folding time 10.41 μs, required control bandwidth approximately 15.3 kHz, throat light-crossing time 12.32 μs. The controller would need to respond in less time than light takes to cross the structure it is controlling.

### 6.5 Threats to validity

**Construct validity.** The control input u is a lumped abstraction of surface-stress modulation, not a derived field-theoretic actuator. A real mechanism might have different gain, dynamics, or spatial structure. The obstruction depends on the *ratio* of achievable margin to light-crossing time, and a more realistic actuator would plausibly add lag rather than remove it — so the author expects the obstruction to strengthen under refinement. This expectation is not proved.

**Internal validity.** Proposition 1 is proved only for Φ = 0 with the coordinate-volume measure dV = 4πr²dr, following Visser et al. (2003). The proper-volume measure carries an additional (1 − b/r)^(−1/2) factor diverging at the throat; extending the bound to that measure is open. Non-zero redshift functions are not covered, and this is the single most important restriction on the result's generality.

**External validity.** All models are semiclassical general relativity. If quantum-gravitational effects dominate at the relevant curvature scales — which for microscopic throats they certainly do — these calculations describe the wrong theory.

**Model reduction.** The two-state linearisation discards all field degrees of freedom. Perturbations of a real throat are governed by a partial differential equation with a continuum of modes; the reduced model captures only the dominant unstable one. A full treatment could reveal additional unstable modes, worsening the problem, or stabilising couplings, improving it.

---

## 7. Discussion

### 7.1 What the results mean together

Read as a group, the four experiments trace a hardening sequence of obstacles.

Experiment A shows exotic matter is not an extra assumption but a restatement of traversability geometry — the requirement cannot be engineered away by choosing a cleverer metric within the class. Experiment B shows the total requirement is bounded below in proportion to throat radius, so cleverness buys a constant factor, not an order of magnitude, at fixed aperture. Experiment C quantifies the warp-drive analogue and shows the dominant cost driver is wall thinness, which quantum inequalities force downward. Experiment D then adds an obstacle of a different kind: even granting all the exotic matter, the resulting structure is dynamically unstable on a timescale comparable to its own light-crossing time, and therefore lies outside the reach of causal feedback control.

The author regards this last point as the most useful contribution, precisely because it is *orthogonal* to the exotic-matter debate that has occupied the field. Most of the literature's optimism concerns reducing energy requirements (Van Den Broeck, 1999; Visser et al., 2003; Bobrick & Martire, 2021). Result 2 suggests that succeeding at that would expose a second barrier, one no amount of negative energy resolves, because it is a statement about information propagation rather than stress-energy.

### 7.2 Where machine learning genuinely helps, and where it does not

The proposal underlying this work anticipated using AI and machine learning to stabilise dynamic hyperspace structures. Having built the framework, the author's assessment is more restrictive.

**Where learning does not help.** Result 2 is a bound on achievable delay margin. A learned controller is still a controller; it is subject to the same causality constraint and the same fundamental limitations on unstable plants with latency (Middleton & Miller, 2007). No neural policy evades a delay margin. Presenting a learned stabiliser as progress here would be a category error — and the episode documented by Kobrin et al. (2023) illustrates how readily a simulation's suggestiveness can outrun its physical content.

**Where learning plausibly does help.** Three roles survive scrutiny:

1. **Surrogate modelling.** Physics-informed neural networks (Raissi et al., 2019) can approximate constraint-satisfying solutions of the ADM constraint equations far faster than elliptic solvers, enabling the wide parameter sweeps Experiment B performs only in low dimensions. The learned object is a *candidate*, always verified by the symbolic audit of §5.3 — learning proposes, symbolic computation disposes.
2. **Search over metric families.** The Van Den Broeck (1999) construction was a human insight about topology that reduced energy requirements by orders of magnitude. Automated search over structured metric spaces is a legitimate machine-learning problem, and Experiment B demonstrates the required verification scaffolding.
3. **Symbolic regression** over numerically generated solution families, to recover closed forms of the kind Proposition 1 exhibits.

In every case the role is *discovery under verification*, never verification itself.

### 7.3 Benchmark roadmap

Six milestones, each stated as a falsifiable computational target.

- **M0 — Reproducible baseline (achieved here).** Automated audit, VIQ bound, warp scaling, control analysis; single core, no proprietary dependencies, test-covered.
- **M1 — Beyond zero tidal force.** Extend Proposition 1 to Φ ≠ 0 and to the proper-volume measure. *Target:* determine whether a throat-radius-proportional floor survives, or whether the redshift function provides genuine relief.
- **M2 — Full 3+1 evolution.** Port throat configurations to BSSN or Z4c in the Einstein Toolkit (Löffler et al., 2012) or NRPy+ (Ruchlin et al., 2018). *Target:* measure constraint-violation growth for a perturbed throat and confirm or refute the reduced model's λ.
- **M3 — Field-theoretic control.** Replace the two-state model with a modal decomposition of throat perturbations; synthesise distributed control. *Target:* establish whether Result 2 survives, weakens, or strengthens under the full mode spectrum. This is the decisive test of the paper's main claim.
- **M4 — Higher-dimensional implementation.** Exercise the symbolic layer for D > 4 with braneworld corrections (Randall & Sundrum, 1999a, 1999b). *Target:* quantify how much four-dimensional exoticity can be exported to a bulk Weyl term.
- **M5 — Quantum-inequality integration.** Encode Ford–Roman-type bounds (Ford & Roman, 1996, 1997) as first-class constraints in the optimiser rather than post-hoc checks. *Target:* a single optimisation problem whose feasible set is simultaneously geometric and quantum-field-theoretic.

M3 is the highest-value target because it is the one that could overturn this paper's principal conclusion.

---

## 8. Reproducibility Practice

The artifact follows practices standard in computational science but uncommon in this subfield: pinned dependencies, seeded stochastic components, a single-command runner, machine-readable output, continuous integration, and cross-validation of load-bearing quantities by independent derivations. Fifteen automated assertions bind each published number to the code producing it, so any refactor that changes a result fails visibly rather than silently.

The author notes that a substantial fraction of the wormhole and warp-drive literature reports numerical results without code, and that several quantities used here had to be rederived from scratch because no artifact accompanied their original publication. The framework is offered partly as a remedy.

---

## 9. Data and Code Availability

All code, results, and tests are available at:

**https://github.com/&lt;username&gt;/hyperbench**

> *Note to the author preparing this manuscript for submission:* replace the placeholder above with the actual repository URL after publishing, and then replace it again with an archival DOI (for example from Zenodo) before submission. Journals increasingly require a versioned archive rather than a bare repository link, because repositories can be renamed, force-pushed, or deleted. Step-by-step instructions are in `PUBLISHING.md` in the artifact.

**Table 11.** Artifact contents.

| Path | Purpose |
|---|---|
| `hyperbench/gr_core.py` | Symbolic GR engine: Christoffel, Riemann, Ricci, Einstein tensors |
| `hyperbench/exp_a_energy_audit.py` | Experiment A — automated energy-condition audit |
| `hyperbench/exp_b_viq.py` | Experiment B — VIQ bound and constrained optimisation |
| `hyperbench/exp_c_warp_scaling.py` | Experiment C — Alcubierre energy scaling |
| `hyperbench/exp_d_control.py` | Experiment D — thin-shell stability, LQR, delay margin |
| `hyperbench/run_all.py` | Master runner; writes `results_summary.json` |
| `tests/test_paper_claims.py` | Fifteen assertions binding paper claims to code |
| `results/results_summary.json` | Machine-readable output of record |
| `.github/workflows/tests.yml` | Continuous verification on Python 3.10–3.12 |
| `requirements.txt` | `numpy>=1.24`, `scipy>=1.10`, `sympy>=1.12` |

**To reproduce:**

```
git clone https://github.com/<username>/hyperbench.git
cd hyperbench
pip install -r requirements.txt
python hyperbench/run_all.py        # about 81 s, single core
python tests/test_paper_claims.py   # fifteen assertions
```

**Environment of record.** Python 3.12.3, NumPy 2.4.4, SciPy 1.17.1, SymPy 1.14.0, Linux x86-64. Runtime 81.3 s.

**Determinism.** The only stochastic component is the SLSQP initial guess in Experiment B, seeded via `np.random.default_rng(0)`. All other results are deterministic. No network access, no GPU, no proprietary data.

---

## 10. Limitations

Beyond the threats in §6.5, four limitations bound the paper's scope.

**Semiclassical only.** No quantum-gravitational treatment. Where curvature approaches the Planck scale the framework describes the wrong physics — and for the microscopic throats quantum inequalities favour, that regime is exactly the relevant one.

**Higher dimensions specified but not exercised.** Section 4.4 is the weakest part of this work. No experiment tests D > 4, so the title's "higher-dimensional spacetime" is at present a framework capability rather than a demonstrated result. The author prefers to state this plainly rather than pad §6 with an underdeveloped fifth experiment.

**Control result is model-reduced.** Result 2 holds within a two-state reduction of a thin-shell model and within the LQR controller family. Two extensions could overturn it: a full modal analysis revealing stabilising couplings, or a controller class achieving margins closer to the theoretical limit. Even the latter leaves the problem marginal, since λ·a₀ ≥ 0.9306. Refutation is possible but would require genuinely new structure rather than better tuning.

**Topology change unaddressed.** Geroch's (1967) theorem implies that creating a wormhole where none existed requires causal pathology or metric degeneracy. The framework assumes an eternal throat. This is arguably a more fundamental obstacle than anything analysed here, and it is not analysed here.

---

## 11. Conclusion

This paper asked whether traversable hyperspace admits treatment as a computer-science problem, and answered affirmatively — with results more constraining than encouraging.

The framework demonstrates that candidate geometries can be compiled, differentiated, audited, optimised, and controlled by machine, with every load-bearing number cross-validated and the whole reproducible in 81 seconds on one core. Within it, four findings emerge. Exotic matter at a wormhole throat is the flare-out condition in algebraic disguise, not an independent physical cost. Total exotic content is bounded below by half the throat radius in the zero-tidal-force gauge, so the escape route identified by Visser et al. (2003) runs through microscopic throats rather than cheap macroscopic ones. Warp-bubble energy scales as −v²R²σ, making wall thinness the dominant cost driver in exactly the regime quantum inequalities compel. And dynamic throat stabilisation faces a delay-margin obstruction that no quantity of negative energy addresses.

The last is the paper's substantive contribution to a literature focused almost exclusively on energy requirements. It suggests that the exotic-matter problem, hard as it is, may not be the binding constraint — and that a research programme optimising energy budgets could succeed completely and still find the resulting structure uncontrollable for reasons of causality alone.

The honest summary is that computational framing has made the obstacles sharper rather than smaller. That is what a research programme at this stage should do. Hyperspace remains a long-horizon interdisciplinary frontier; this work contributes a reproducible instrument for measuring how far away it is, and a specific, falsifiable target — milestone M3 — for the next person who wants to move it closer.

---

## References

*Every entry below was verified against a primary source: a publisher record, an arXiv listing, or the reference list of a peer-reviewed article. Digital object identifiers are given only where directly confirmed; where a DOI could not be verified, the journal citation and a verified arXiv identifier are given instead.*

Alcubierre, M. (1994). The warp drive: Hyper-fast travel within general relativity. *Classical and Quantum Gravity, 11*(5), L73–L77. https://doi.org/10.1088/0264-9381/11/5/001

Arnowitt, R., Deser, S., & Misner, C. W. (2008). The dynamics of general relativity. *General Relativity and Gravitation, 40*(9), 1997–2027. https://doi.org/10.1007/s10714-008-0661-1 (Original work published 1962)

Åström, K. J., & Murray, R. M. (2021). *Feedback systems: An introduction for scientists and engineers* (2nd ed.). Princeton University Press.

Barceló, C., & Visser, M. (2002). Twilight for the energy conditions? *International Journal of Modern Physics D, 11*(10), 1553–1560. https://doi.org/10.1142/S0218271802002888

Baumgarte, T. W., & Shapiro, S. L. (1999). On the numerical integration of Einstein's field equations. *Physical Review D, 59*(2), Article 024007. https://doi.org/10.1103/PhysRevD.59.024007

Bobrick, A., & Martire, G. (2021). Introducing physical warp drives. *Classical and Quantum Gravity, 38*(10), Article 105009. https://doi.org/10.1088/1361-6382/abdf6e

Clough, K., Figueras, P., Finkel, H., Kunesch, M., Lim, E. A., & Tunyasuvunakool, S. (2015). GRChombo: Numerical relativity with adaptive mesh refinement. *Classical and Quantum Gravity, 32*(24), Article 245011. arXiv:1503.03436

Curiel, E. (2017). A primer on energy conditions. In D. Lehmkuhl, G. Schiemann, & E. Scholz (Eds.), *Towards a theory of spacetime theories* (Einstein Studies Vol. 13, pp. 43–104). Birkhäuser. https://doi.org/10.1007/978-1-4939-3210-8_3

Fell, S. D. B., & Heisenberg, L. (2021). Positive energy warp drive from hidden geometric structures. *Classical and Quantum Gravity, 38*(15), Article 155020. https://doi.org/10.1088/1361-6382/ac0e47

Ford, L. H., & Roman, T. A. (1996). Quantum field theory constrains traversable wormhole geometries. *Physical Review D, 53*(10), 5496–5507. https://doi.org/10.1103/PhysRevD.53.5496

Ford, L. H., & Roman, T. A. (1997). Restrictions on negative energy density in flat spacetime. *Physical Review D, 55*(4), 2082–2089. https://doi.org/10.1103/PhysRevD.55.2082

Gao, P., Jafferis, D. L., & Wall, A. C. (2017). Traversable wormholes via a double trace deformation. *Journal of High Energy Physics, 2017*(12), Article 151. arXiv:1608.05687

Geroch, R. P. (1967). Topology in general relativity. *Journal of Mathematical Physics, 8*(4), 782–786. https://doi.org/10.1063/1.1705276

Harris, C. R., Millman, K. J., van der Walt, S. J., Gommers, R., Virtanen, P., Cournapeau, D., Wieser, E., Taylor, J., Berg, S., Smith, N. J., Kern, R., Picus, M., Hoyer, S., van Kerkwijk, M. H., Brett, M., Haldane, A., del Río, J. F., Wiebe, M., Peterson, P., … Oliphant, T. E. (2020). Array programming with NumPy. *Nature, 585*(7825), 357–362. https://doi.org/10.1038/s41586-020-2649-2

Hochberg, D., & Visser, M. (1998). Dynamic wormholes, antitrapped surfaces, and energy conditions. *Physical Review D, 58*(4), Article 044021. https://doi.org/10.1103/PhysRevD.58.044021

Jafferis, D., Zlokapa, A., Lykken, J. D., Kolchmeyer, D. K., Davis, S. I., Lauk, N., Neven, H., & Spiropulu, M. (2022). Traversable wormhole dynamics on a quantum processor. *Nature, 612*(7938), 51–55.

Kobrin, B., Schuster, T., & Yao, N. Y. (2023). *Comment on "Traversable wormhole dynamics on a quantum processor."* arXiv. https://arxiv.org/abs/2302.07897

Lentz, E. W. (2021). Breaking the warp barrier: Hyper-fast solitons in Einstein–Maxwell-plasma theory. *Classical and Quantum Gravity, 38*(7), Article 075015. https://doi.org/10.1088/1361-6382/abe692

Lobo, F. S. N., & Visser, M. (2004). Fundamental limitations on "warp drive" spacetimes. *Classical and Quantum Gravity, 21*(24), 5871–5892. https://doi.org/10.1088/0264-9381/21/24/011

Löffler, F., Faber, J., Bentivegna, E., Bode, T., Diener, P., Haas, R., Hinder, I., Mundim, B. C., Ott, C. D., Schnetter, E., Allen, G., Campanelli, M., & Laguna, P. (2012). The Einstein Toolkit: A community computational infrastructure for relativistic astrophysics. *Classical and Quantum Gravity, 29*(11), Article 115001. https://doi.org/10.1088/0264-9381/29/11/115001

Maldacena, J., Milekhin, A., & Popov, F. (2023). Traversable wormholes in four dimensions. *Classical and Quantum Gravity, 40*(15), Article 155016. arXiv:1807.04726

Maldacena, J., & Susskind, L. (2013). Cool horizons for entangled black holes. *Fortschritte der Physik, 61*(9), 781–811. arXiv:1306.0533

Meurer, A., Smith, C. P., Paprocki, M., Čertík, O., Kirpichev, S. B., Rocklin, M., Kumar, A., Ivanov, S., Moore, J. K., Singh, S., Rathnayake, T., Vig, S., Granger, B. E., Muller, R. P., Bonazzi, F., Gupta, H., Vats, S., Johansson, F., Pedregosa, F., … Scopatz, A. (2017). SymPy: Symbolic computing in Python. *PeerJ Computer Science, 3*, Article e103. https://doi.org/10.7717/peerj-cs.103

Middleton, R. H., & Miller, D. E. (2007). On the achievable delay margin using LTI control for unstable plants. *IEEE Transactions on Automatic Control, 52*(7), 1194–1207.

Morris, M. S., & Thorne, K. S. (1988). Wormholes in spacetime and their use for interstellar travel: A tool for teaching general relativity. *American Journal of Physics, 56*(5), 395–412. https://doi.org/10.1119/1.15620

Morris, M. S., Thorne, K. S., & Yurtsever, U. (1988). Wormholes, time machines, and the weak energy condition. *Physical Review Letters, 61*(13), 1446–1449. https://doi.org/10.1103/PhysRevLett.61.1446

Natário, J. (2002). Warp drive with zero expansion. *Classical and Quantum Gravity, 19*(6), 1157–1165. https://doi.org/10.1088/0264-9381/19/6/308

Olum, K. D. (1998). Superluminal travel requires negative energies. *Physical Review Letters, 81*(17), 3567–3570. https://doi.org/10.1103/PhysRevLett.81.3567

Overduin, J. M., & Wesson, P. S. (1997). Kaluza–Klein gravity. *Physics Reports, 283*(5–6), 303–378. arXiv:gr-qc/9805018

Pfenning, M. J., & Ford, L. H. (1997). The unphysical nature of "warp drive." *Classical and Quantum Gravity, 14*(7), 1743–1751. https://doi.org/10.1088/0264-9381/14/7/011

Poisson, E., & Visser, M. (1995). Thin-shell wormholes: Linearization stability. *Physical Review D, 52*(12), 7318–7321. https://doi.org/10.1103/PhysRevD.52.7318

Raissi, M., Perdikaris, P., & Karniadakis, G. E. (2019). Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations. *Journal of Computational Physics, 378*, 686–707. https://doi.org/10.1016/j.jcp.2018.10.045

Randall, L., & Sundrum, R. (1999a). An alternative to compactification. *Physical Review Letters, 83*(23), 4690–4693. https://doi.org/10.1103/PhysRevLett.83.4690

Randall, L., & Sundrum, R. (1999b). Large mass hierarchy from a small extra dimension. *Physical Review Letters, 83*(17), 3370–3373. https://doi.org/10.1103/PhysRevLett.83.3370

Ruchlin, I., Etienne, Z. B., & Baumgarte, T. W. (2018). SENR/NRPy+: Numerical relativity in singular curvilinear coordinate systems. *Physical Review D, 97*(6), Article 064036. https://doi.org/10.1103/PhysRevD.97.064036

Santiago, J., Schuster, S., & Visser, M. (2022). Generic warp drives violate the null energy condition. *Physical Review D, 105*(6), Article 064038. https://doi.org/10.1103/PhysRevD.105.064038

Shibata, M., & Nakamura, T. (1995). Evolution of three-dimensional gravitational waves: Harmonic slicing case. *Physical Review D, 52*(10), 5428–5444. https://doi.org/10.1103/PhysRevD.52.5428

Van Den Broeck, C. (1999). A "warp drive" with more reasonable total energy requirements. *Classical and Quantum Gravity, 16*(12), 3973–3979. https://doi.org/10.1088/0264-9381/16/12/314

Virtanen, P., Gommers, R., Oliphant, T. E., Haberland, M., Reddy, T., Cournapeau, D., Burovski, E., Peterson, P., Weckesser, W., Bright, J., van der Walt, S. J., Brett, M., Wilson, J., Millman, K. J., Mayorov, N., Nelson, A. R. J., Jones, E., Kern, R., Larson, E., … Vázquez-Baeza, Y. (2020). SciPy 1.0: Fundamental algorithms for scientific computing in Python. *Nature Methods, 17*(3), 261–272. https://doi.org/10.1038/s41592-019-0686-2

Visser, M. (1995). *Lorentzian wormholes: From Einstein to Hawking*. AIP Press.

Visser, M., Kar, S., & Dadhich, N. (2003). Traversable wormholes with arbitrarily small energy condition violations. *Physical Review Letters, 90*(20), Article 201102. https://doi.org/10.1103/PhysRevLett.90.201102

---

## Appendix A — Derivation of the delay-margin condition

For the plant ẍ = λ²x + u under delayed state feedback u(t) = −K₁x(t−τ) − K₂ẋ(t−τ), the characteristic equation is

$$s^2 - \lambda^2 + (K_1 + K_2 s)e^{-s\tau} = 0.$$

At a stability boundary a root lies on the imaginary axis, s = iω with ω > 0. Substituting and separating real and imaginary parts:

- Real: −ω² − λ² + K₁cos(ωτ) + K₂ω sin(ωτ) = 0
- Imaginary: −K₁sin(ωτ) + K₂ω cos(ωτ) = 0

The imaginary part gives tan(ωτ) = K₂ω/K₁, so with R = √(K₁² + K₂²ω²) one has cos(ωτ) = K₁/R and sin(ωτ) = K₂ω/R. Substituting into the real part collapses it to R = ω² + λ², that is,

$$\sqrt{K_1^2 + K_2^2\omega^2} = \omega^2 + \lambda^2,$$

a scalar equation solved by bracketed root-finding. The margin is then τ = φ/ω with φ = atan2(K₂ω, K₁) ∈ [0, 2π). The smallest positive τ over all crossover roots is the delay margin, verified in §6.4 against direct RK4 integration of the delay differential equation.

## Appendix B — Reproducing individual results

| Result | Command | Output key |
|---|---|---|
| Throat NEC identity | `python hyperbench/exp_a_energy_audit.py` | `throat_limit.nec_at_throat` |
| Morris–Thorne verification | `python hyperbench/exp_a_energy_audit.py` | `general_formulas.matches_morris_thorne_*` |
| Proposition 1 confirmation | `python hyperbench/exp_b_viq.py` | `b1_bound_approach` |
| Optimiser validation | `python hyperbench/exp_b_viq.py` | `b2_gradient_constrained` |
| Warp scaling exponents | `python hyperbench/exp_c_warp_scaling.py` | `scaling_exponents` |
| Mass-equivalent budget | `python hyperbench/exp_c_warp_scaling.py` | `physical_budget` |
| Thin-shell stability scan | `python hyperbench/exp_d_control.py` | `stability_scan` |
| Delay-margin obstruction | `python hyperbench/run_all.py` | `D.delay_margin_frontier` |
| All claims at once | `python tests/test_paper_claims.py` | Fifteen assertions |
