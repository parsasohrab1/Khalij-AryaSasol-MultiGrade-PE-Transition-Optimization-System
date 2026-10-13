"""Portfolio changeover sequence optimizer (Phase 4, FR-SEQ-01/02).

Per unit the monthly plan is a minimum-waste Hamiltonian path over the demanded
grades starting from the grade currently running: exact Held-Karp DP up to
`EXACT_LIMIT` nodes, nearest-neighbour + 2-opt beyond. The two units are
independent, so the portfolio plan is the pair of unit plans.
"""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field

import numpy as np

from .dynamics import TransitionPlan, plan_transition
from .grades import UNITS

EXACT_LIMIT = 13


def cost_matrix(grade_ids: list[str], overshoot: bool = True) -> np.ndarray:
    n = len(grade_ids)
    w = np.zeros((n, n))
    for i, a in enumerate(grade_ids):
        for j, b in enumerate(grade_ids):
            if i != j:
                w[i, j] = plan_transition(a, b, overshoot).waste_t
    return w


def path_cost(order: list[int], w: np.ndarray) -> float:
    return float(sum(w[a, b] for a, b in zip(order, order[1:])))


def _held_karp(w: np.ndarray) -> list[int]:
    """Min-cost path from node 0 visiting all nodes, free end."""
    n = len(w)
    if n == 1:
        return [0]
    full = (1 << (n - 1)) - 1  # subsets of nodes 1..n-1
    dp = np.full((full + 1, n - 1), np.inf)
    par = np.full((full + 1, n - 1), -1, dtype=int)
    for j in range(n - 1):
        dp[1 << j, j] = w[0, j + 1]
    for mask in range(1, full + 1):
        for j in range(n - 1):
            if not mask & (1 << j) or dp[mask, j] == np.inf:
                continue
            for k in range(n - 1):
                if mask & (1 << k):
                    continue
                nm, c = mask | (1 << k), dp[mask, j] + w[j + 1, k + 1]
                if c < dp[nm, k]:
                    dp[nm, k], par[nm, k] = c, j
    j = int(np.argmin(dp[full]))
    order, mask = [], full
    while j != -1:
        order.append(j + 1)
        pj = int(par[mask, j])
        mask ^= 1 << j
        j = pj
    return [0] + order[::-1]


def _heuristic(w: np.ndarray) -> list[int]:
    n = len(w)
    order, left = [0], set(range(1, n))
    while left:
        nxt = min(left, key=lambda j: w[order[-1], j])
        order.append(nxt)
        left.remove(nxt)
    improved = True
    while improved:
        improved = False
        for i, j in itertools.combinations(range(1, n), 2):
            cand = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
            if path_cost(cand, w) < path_cost(order, w) - 1e-9:
                order, improved = cand, True
    return order


def best_order(w: np.ndarray) -> list[int]:
    return _held_karp(w) if len(w) <= EXACT_LIMIT else _heuristic(w)


@dataclass
class UnitPlan:
    unit: str
    sequence: list[str]
    campaign_h: dict[str, float]
    transitions: list[TransitionPlan]
    waste_t: float
    transition_h: float
    campaign_total_h: float
    horizon_h: float
    feasible: bool = field(init=False)

    def __post_init__(self) -> None:
        self.feasible = self.campaign_total_h + self.transition_h <= self.horizon_h


def evaluate_sequence(unit: str, seq: list[str], demand: dict[str, float],
                      horizon_h: float = 720.0, overshoot: bool = True) -> UnitPlan:
    rate = UNITS[unit].rate_tph
    camp = {g: demand.get(g, 0.0) / rate for g in seq}
    trs = [plan_transition(a, b, overshoot) for a, b in zip(seq, seq[1:])]
    return UnitPlan(unit, seq, camp, trs, sum(t.waste_t for t in trs),
                    sum(t.time_h for t in trs), sum(camp.values()), horizon_h)


def optimize_unit(unit: str, start_grade: str, demand: dict[str, float],
                  horizon_h: float = 720.0, overshoot: bool = True) -> UnitPlan:
    """Optimal order of the demanded grades, starting from `start_grade`."""
    ids = [start_grade] + [g for g, t in demand.items() if t > 0 and g != start_grade]
    seq = [ids[i] for i in best_order(cost_matrix(ids, overshoot))]
    return evaluate_sequence(unit, seq, demand, horizon_h, overshoot)


def baselines(unit: str, start_grade: str, demand: dict[str, float], horizon_h: float = 720.0,
              overshoot: bool = False, n_random: int = 200, seed: int = 0) -> dict[str, float]:
    """Reference waste (t): demand-descending order, and the mean of random orders."""
    rest = [g for g, t in sorted(demand.items(), key=lambda kv: -kv[1])
            if t > 0 and g != start_grade]
    by_demand = evaluate_sequence(unit, [start_grade] + rest, demand, horizon_h, overshoot)
    rng, waste = random.Random(seed), []
    for _ in range(n_random):
        r = rest[:]
        rng.shuffle(r)
        waste.append(evaluate_sequence(unit, [start_grade] + r, demand, horizon_h,
                                       overshoot).waste_t)
    return {"by_demand_waste_t": by_demand.waste_t, "random_mean_waste_t": float(np.mean(waste))}


def optimize_portfolio(start: dict[str, str], demand: dict[str, dict[str, float]],
                       horizon_h: float = 720.0, overshoot: bool = True) -> dict[str, UnitPlan]:
    return {u: optimize_unit(u, start[u], demand[u], horizon_h, overshoot) for u in start}
