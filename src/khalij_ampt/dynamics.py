"""First-order grade-transition physics shared by the simulator and the optimizer.

ln(MFI) follows hydrogen ratio, density follows comonomer ratio, each through a
first-order lag. The slow direction (MFI down, density up) is `slow_factor`
times slower. A setpoint overshoot (FR-SEQ-02) drives the property into the
tolerance band faster, then the setpoint is released to the target recipe.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .grades import GRADES, UNITS, Grade, UnitSpec


@dataclass(frozen=True)
class TransitionPlan:
    src: str
    dst: str
    hold_mfi_h: float    # time the hydrogen overshoot command is held
    hold_rho_h: float    # time the comonomer overshoot command is held
    k_mfi: float         # overshoot fraction applied to ln(hydrogen)
    k_rho: float         # overshoot fraction applied to comonomer (via density)
    waste_t: float       # off-grade product, tons
    dip_pct: float       # initial catalyst activity dip

    @property
    def time_h(self) -> float:
        """Time until both properties are on-spec."""
        return max(self.hold_mfi_h, self.hold_rho_h)


def tau_eff(spec: UnitSpec, delta: float, slow_sign: int) -> float:
    return spec.tau_h * (spec.slow_factor if delta * slow_sign > 0 else 1.0)


def _time_to_band(tau: float, delta: float, eps: float, k: float) -> float:
    a = abs(delta)
    if a <= eps:
        return 0.0
    return tau * math.log((1 + k) * a / (eps + k * a))


def activity_dip(spec: UnitSpec, g0: Grade, g1: Grade) -> float:
    h0, c0 = g0.recipe()
    h1, c1 = g1.recipe()
    d = spec.act_base + spec.act_k_mfi * abs(math.log(h1 / h0)) + spec.act_k_c * abs(c1 - c0)
    return min(d, 45.0)


def plan_transition(src: str, dst: str, overshoot: bool = True) -> TransitionPlan:
    g0, g1 = GRADES[src], GRADES[dst]
    if g0.unit != g1.unit:
        raise ValueError("transitions are defined within a unit")
    spec = UNITS[g0.unit]
    if src == dst:
        return TransitionPlan(src, dst, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    d_m = math.log(g1.mfi / g0.mfi)          # slow when negative
    d_r = g1.density - g0.density            # slow when positive
    tau_m = tau_eff(spec, d_m, -1)
    tau_r = tau_eff(spec, d_r, +1)

    k_m = k_r = 0.0
    if overshoot:
        k_m = spec.max_overshoot
        k_r = spec.max_overshoot
        if d_r > 0:  # comonomer command must stay >= 0  <=>  rho_cmd <= rho0
            k_r = min(k_r, max(0.0, (spec.rho0 - g1.density) / d_r))
    t_m = _time_to_band(tau_m, d_m, spec.tol_ln_mfi, k_m)
    t_r = _time_to_band(tau_r, d_r, spec.tol_rho, k_r)
    t = max(t_m, t_r)

    dip = activity_dip(spec, g0, g1)
    lost_fraction = dip / 100 * spec.act_tau_h * (1 - math.exp(-t / spec.act_tau_h))
    waste = spec.rate_tph * (t - lost_fraction) + spec.fixed_loss_t
    return TransitionPlan(src, dst, t_m, t_r, k_m, k_r, waste, dip)
