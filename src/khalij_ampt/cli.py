"""Command line: simulate data, train/evaluate the twin, plan a month."""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

from .grades import UNITS, grades_of
from .optimizer import baselines, optimize_unit
from .simulator import random_campaigns, random_demand, simulate_unit
from .twin import QualityCatalystTwin


def train_twin(unit: str, n_campaigns: int = 60, seed: int = 1) -> tuple[QualityCatalystTwin, dict]:
    df = simulate_unit(unit, random_campaigns(unit, n_campaigns, seed), seed=seed)
    cut = int(len(df) * 0.7)
    # split on a campaign boundary so test data starts from a clean grade block
    boundary = (df["current_grade"] != df["current_grade"].shift()).to_numpy().nonzero()[0]
    cut = int(boundary[boundary <= cut][-1])
    train, test = df.iloc[:cut], df.iloc[cut:].reset_index(drop=True)
    twin = QualityCatalystTwin(unit).fit(train)
    return twin, twin.evaluate(test)


def cmd_simulate(a: argparse.Namespace) -> None:
    frames = [simulate_unit(u, random_campaigns(u, a.campaigns, a.seed), overshoot=a.overshoot,
                            seed=a.seed) for u in UNITS]
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(a.out, index=False)
    print(f"saved {len(out):,} rows -> {a.out}")


def cmd_train(a: argparse.Namespace) -> None:
    for u in UNITS:
        twin, m = train_twin(u, a.campaigns)
        print(u, {k: round(v, 4) for k, v in m.items()})
        twin.save(Path(a.out_dir) / f"twin_{u}.joblib") if a.out_dir else None
        s, df = twin.stream(), simulate_unit(u, random_campaigns(u, 2, 9), seed=9).head(300)
        t0 = time.perf_counter()
        for h, c in zip(df["hydrogen_ratio"], df["comonomer_ratio"]):
            s.update(h, c)
        print(f"  streaming latency: {(time.perf_counter() - t0) / len(df) * 1e3:.2f} ms/sample")


def cmd_plan(a: argparse.Namespace) -> None:
    tot = {"opt": 0.0, "step": 0.0, "rand": 0.0}
    for i, u in enumerate(UNITS):
        demand = random_demand(u, seed=a.seed + i)
        start = grades_of(u)[0].id
        plan = optimize_unit(u, start, demand, a.horizon)
        step = optimize_unit(u, start, demand, a.horizon, overshoot=False)
        base = baselines(u, start, demand, a.horizon, overshoot=False)
        print(f"\n== {u}: {len(plan.sequence)} grades, horizon {a.horizon:.0f} h ==")
        print(" -> ".join(plan.sequence))
        print(f"optimized sequence + overshoot path : {plan.waste_t:8.1f} t off-grade, "
              f"{plan.transition_h:6.1f} h in transition, feasible={plan.feasible}")
        print(f"optimized sequence, step changes    : {step.waste_t:8.1f} t")
        print(f"demand-order, step changes          : {base['by_demand_waste_t']:8.1f} t")
        print(f"random order (mean), step changes   : {base['random_mean_waste_t']:8.1f} t")
        tot["opt"] += plan.waste_t
        tot["step"] += base["random_mean_waste_t"]
    print(f"\nportfolio off-grade: {tot['opt']:.0f} t vs {tot['step']:.0f} t "
          f"(random order, step) = {100 * (1 - tot['opt'] / tot['step']):.0f}% reduction")
    print("NOTE: grade specs and dynamics are placeholders, not plant-identified values.")


def main() -> None:
    p = argparse.ArgumentParser(prog="khalij-ampt")
    sub = p.add_subparsers(required=True)
    s = sub.add_parser("simulate", help="generate synthetic DCS data for both units")
    s.add_argument("--campaigns", type=int, default=20)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--overshoot", action="store_true")
    s.add_argument("--out", default="aryasasol_grade_transition_data.csv")
    s.set_defaults(fn=cmd_simulate)
    t = sub.add_parser("train", help="train and evaluate the virtual sensor per unit")
    t.add_argument("--campaigns", type=int, default=60)
    t.add_argument("--out-dir", default=None)
    t.set_defaults(fn=cmd_train)
    q = sub.add_parser("plan", help="optimize a monthly changeover sequence")
    q.add_argument("--horizon", type=float, default=720.0)
    q.add_argument("--seed", type=int, default=0)
    q.set_defaults(fn=cmd_plan)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
