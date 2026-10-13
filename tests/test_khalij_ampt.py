import itertools

import numpy as np
import pytest

from khalij_ampt.dynamics import plan_transition
from khalij_ampt.grades import GRADES, UNITS, grades_of
from khalij_ampt.optimizer import _heuristic, best_order, cost_matrix, optimize_unit, path_cost
from khalij_ampt.simulator import random_campaigns, random_demand, simulate_unit
from khalij_ampt.twin import QualityCatalystTwin, StreamingFeatures, build_features


def test_portfolio_has_19_grades():
    assert len(grades_of("LDPE")) == 9 and len(grades_of("HDPE")) == 10 and len(GRADES) == 19


def test_recipes_are_physical():
    for g in GRADES.values():
        h, c = g.recipe()
        assert h > 0 and c >= 0, g


def test_overshoot_is_faster_and_cheaper():
    for a, b in [("HDPE-G1", "HDPE-G10"), ("HDPE-G10", "HDPE-G1"), ("LDPE-G1", "LDPE-G9")]:
        step, fast = plan_transition(a, b, False), plan_transition(a, b, True)
        assert fast.time_h < step.time_h and fast.waste_t < step.waste_t


def test_transitions_are_asymmetric():
    assert plan_transition("HDPE-G1", "HDPE-G10", False).time_h != \
        plan_transition("HDPE-G10", "HDPE-G1", False).time_h


@pytest.mark.parametrize("overshoot", [False, True])
def test_simulated_off_spec_time_matches_analytic_plan(overshoot):
    a, b = "HDPE-G10", "HDPE-G1"
    df = simulate_unit("HDPE", [(a, 20.0), (b, 30.0)], overshoot=overshoot, noise=False)
    seg = df[df["current_grade"] == b]
    off_h = seg["off_spec_flag"].sum() / 60
    assert off_h == pytest.approx(plan_transition(a, b, overshoot).time_h, abs=0.05)
    assert seg["off_spec_flag"].iloc[-60:].sum() == 0


def test_held_karp_matches_brute_force():
    ids = ["HDPE-G1", "HDPE-G10", "HDPE-G4", "HDPE-G7", "HDPE-G8", "HDPE-G2"]
    w = cost_matrix(ids)
    brute = min(path_cost([0, *p], w) for p in itertools.permutations(range(1, len(ids))))
    assert path_cost(best_order(w), w) == pytest.approx(brute)


def test_heuristic_close_to_exact():
    ids = [g.id for g in grades_of("HDPE")]
    w = cost_matrix(ids)
    assert path_cost(_heuristic(w), w) <= 1.15 * path_cost(best_order(w), w)


def test_optimized_plan_beats_random_orders():
    demand = random_demand("LDPE", seed=3)
    start = "LDPE-G1"
    plan = optimize_unit("LDPE", start, demand)
    assert set(plan.sequence) == set(demand) and plan.sequence[0] == start
    rng = np.random.default_rng(0)
    rest = [g for g in demand if g != start]
    for _ in range(50):
        rng.shuffle(rest)
        assert plan.waste_t <= path_cost([0, *range(1, len(rest) + 1)],
                                         cost_matrix([start, *rest])) + 1e-9


def test_streaming_features_equal_batch():
    df = simulate_unit("LDPE", random_campaigns("LDPE", 3, 5), seed=5).head(500)
    batch = build_features(df).to_numpy()
    s = StreamingFeatures()
    stream = np.vstack([s.update(h, c) for h, c in zip(df["hydrogen_ratio"], df["comonomer_ratio"])])
    np.testing.assert_allclose(stream, batch, atol=1e-9)


@pytest.mark.parametrize("unit", list(UNITS))
def test_virtual_sensor_meets_nfr_mape(unit):
    df = simulate_unit(unit, random_campaigns(unit, 30, 1), seed=1)
    cut = int(len(df) * 0.7)
    twin = QualityCatalystTwin(unit).fit(df.iloc[:cut])
    m = twin.evaluate(df.iloc[cut:].reset_index(drop=True))
    assert m["mape_mfi_pct"] < 10  # NFR-PER-02
