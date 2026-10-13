"""Physics-based DCS data simulator (Phase 1).

Replaces the README's random generator with transition dynamics consistent with
the optimizer, so the virtual sensor and the planner can be validated against
the same ground truth.
"""
from __future__ import annotations

import math
from datetime import datetime

import numpy as np
import pandas as pd

from .dynamics import plan_transition
from .grades import GRADES, UNITS, grades_of

DT_H = 1.0 / 60.0  # 1-minute sampling


def simulate_unit(unit: str, campaigns: list[tuple[str, float]], overshoot: bool = False,
                  noise: bool = True, seed: int = 0,
                  start: datetime = datetime(2026, 9, 14, 8, 0, 0)) -> pd.DataFrame:
    """Simulate one unit through a list of (grade, campaign_hours)."""
    spec = UNITS[unit]
    rng = np.random.default_rng(seed)
    g = GRADES[campaigns[0][0]]
    h, c = g.recipe()
    z_m, z_r = math.log(g.mfi), g.density
    prev, act_dip, t_since = g.id, 0.0, 1e9
    rows = []
    t_clock = 0
    for gid, hours in campaigns:
        g = GRADES[gid]
        h_t, c_t = g.recipe()
        plan = plan_transition(prev, gid, overshoot) if gid != prev else plan_transition(gid, gid)
        if gid != prev:
            act_dip, t_since = plan.dip_pct, 0.0
        hold_m, hold_r = math.ceil(plan.hold_mfi_h / DT_H), math.ceil(plan.hold_rho_h / DT_H)
        hold_steps = max(hold_m, hold_r)
        n = max(round(hours / DT_H), hold_steps + 60)
        h0, c0 = GRADES[prev].recipe()
        # overshoot commands (log-hydrogen and comonomer linear in density)
        ln_h_cmd = math.log(h_t) + plan.k_mfi * (math.log(h_t) - math.log(h0))
        c_cmd = c_t + plan.k_rho * (c_t - c0)
        for i in range(n):
            in_hold = i < hold_steps
            ln_h = ln_h_cmd if i < hold_m else math.log(h_t)
            c_in = c_cmd if i < hold_r else c_t
            if noise:
                ln_h += rng.normal(0, 0.01)
                c_in *= 1 + rng.normal(0, 0.01)
            m_ss, r_ss = ln_h + math.log(spec.k_mfi), spec.rho0 - spec.k_c * c_in
            tm = spec.tau_h * (spec.slow_factor if m_ss < z_m else 1.0)
            tr = spec.tau_h * (spec.slow_factor if r_ss > z_r else 1.0)
            z_m += (1 - math.exp(-DT_H / tm)) * (m_ss - z_m)
            z_r += (1 - math.exp(-DT_H / tr)) * (r_ss - z_r)
            dip = act_dip * math.exp(-t_since / spec.act_tau_h)
            t_since += DT_H
            act = 100 - dip + (rng.normal(0, 1.0) if noise else 0.0)
            off = int(abs(z_m - math.log(g.mfi)) > spec.tol_ln_mfi
                      or abs(z_r - g.density) > spec.tol_rho)
            rows.append((t_clock, unit, gid, int(in_hold), math.exp(ln_h), c_in, act,
                         math.exp(z_m) * (math.exp(rng.normal(0, 0.02)) if noise else 1.0),
                         z_r + (rng.normal(0, 0.0005) if noise else 0.0), off,
                         spec.rate_tph * act / 100))
            t_clock += 1
        prev = gid
    df = pd.DataFrame(rows, columns=[
        "minute", "unit", "current_grade", "is_transition", "hydrogen_ratio",
        "comonomer_ratio", "catalyst_activity_pct", "melt_flow_index", "density_g_cm3",
        "off_spec_flag", "production_tph"])
    df.insert(0, "timestamp", pd.to_datetime(start) + pd.to_timedelta(df.pop("minute"), unit="min"))
    return df


def random_campaigns(unit: str, n_campaigns: int, seed: int = 0,
                     mean_hours: float = 60.0) -> list[tuple[str, float]]:
    rng = np.random.default_rng(seed)
    ids = [g.id for g in grades_of(unit)]
    out, prev = [], None
    for _ in range(n_campaigns):
        gid = rng.choice([x for x in ids if x != prev])
        out.append((str(gid), float(max(12.0, rng.gamma(4.0, mean_hours / 4.0)))))
        prev = gid
    return out


def random_demand(unit: str, seed: int = 0, monthly_t: float | None = None) -> dict[str, float]:
    """Random monthly demand (tons) per grade for a unit."""
    spec = UNITS[unit]
    rng = np.random.default_rng(seed)
    total = monthly_t if monthly_t is not None else spec.rate_tph * 720 * 0.9
    ids = [g.id for g in grades_of(unit)]
    w = rng.dirichlet(np.ones(len(ids)) * 3.0)
    return {gid: float(total * wi) for gid, wi in zip(ids, w)}
