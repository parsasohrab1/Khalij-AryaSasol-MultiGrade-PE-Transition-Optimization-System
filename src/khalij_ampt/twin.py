"""MFI/density virtual sensor + transient catalyst activity model (Phases 2-3).

Causal features (EMAs of the manipulated variables at several time scales and
their deviation from each EMA) give the model the process memory it needs to
see transitions in flight. `StreamingTwin` computes the identical features
sample-by-sample for the real-time path (NFR-PER-01).
"""
from __future__ import annotations

import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

SPANS_MIN = (10, 30, 90, 240, 600)
RAW = ("ln_h", "c")


def feature_names() -> list[str]:
    names = list(RAW)
    for r in RAW:
        names += [f"{r}_ema{s}" for s in SPANS_MIN]
        names += [f"{r}_dev{s}" for s in SPANS_MIN]
    return names


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Batch causal features for one unit's time-ordered frame."""
    ln_h, c = np.log(df["hydrogen_ratio"]), df["comonomer_ratio"]
    f = {"ln_h": ln_h, "c": c}
    for name, x in (("ln_h", ln_h), ("c", c)):
        for s in SPANS_MIN:
            ema = x.ewm(alpha=1.0 / s, adjust=False).mean()
            f[f"{name}_ema{s}"] = ema
            f[f"{name}_dev{s}"] = x - ema
    return pd.DataFrame(f)[feature_names()]


class StreamingFeatures:
    """Sample-by-sample equivalent of `build_features`."""

    def __init__(self) -> None:
        self._ema: dict[str, list[float]] | None = None

    def update(self, hydrogen_ratio: float, comonomer_ratio: float) -> np.ndarray:
        raw = {"ln_h": math.log(hydrogen_ratio), "c": comonomer_ratio}
        if self._ema is None:
            self._ema = {k: [v] * len(SPANS_MIN) for k, v in raw.items()}
        else:
            for k, v in raw.items():
                self._ema[k] = [e + (v - e) / s for e, s in zip(self._ema[k], SPANS_MIN)]
        out = [raw[n] for n in RAW]
        for name in RAW:
            out += self._ema[name]
            out += [raw[name] - e for e in self._ema[name]]
        return np.array([out])


class _Hybrid:
    """Ridge on the lag features (extrapolates across unseen grade pairs) plus a
    gradient-boosted correction for the nonlinear/asymmetric part."""

    def __init__(self, seed: int) -> None:
        self.lin = Ridge(alpha=1e-6)
        self.gbm = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08,
                                                 random_state=seed)

    def fit(self, X, y) -> "_Hybrid":
        self.lin.fit(X, y)
        self.gbm.fit(X, y - self.lin.predict(X))
        return self

    def predict(self, X) -> np.ndarray:
        return self.lin.predict(X) + self.gbm.predict(X)


class QualityCatalystTwin:
    """One twin per unit (LDPE / HDPE)."""

    def __init__(self, unit: str, seed: int = 0) -> None:
        self.unit = unit

        self.models = {k: _Hybrid(seed) for k in ("ln_mfi", "density", "activity")}

    @staticmethod
    def _targets(df: pd.DataFrame) -> dict[str, pd.Series]:
        return {"ln_mfi": np.log(df["melt_flow_index"]), "density": df["density_g_cm3"],
                "activity": df["catalyst_activity_pct"]}

    def fit(self, df: pd.DataFrame) -> "QualityCatalystTwin":
        X = build_features(df)
        for k, y in self._targets(df).items():
            self.models[k].fit(X, y)
        return self

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        X = build_features(df)
        p = {k: m.predict(X) for k, m in self.models.items()}
        return pd.DataFrame({"mfi_pred": np.exp(p["ln_mfi"]), "density_pred": p["density"],
                             "activity_pred": p["activity"]}, index=df.index)

    def evaluate(self, df: pd.DataFrame) -> dict[str, float]:
        p = self.predict(df)
        ape = (p["mfi_pred"] - df["melt_flow_index"]).abs() / df["melt_flow_index"]
        tr = df["is_transition"] == 1
        return {
            "mape_mfi_pct": float(ape.mean() * 100),
            "mape_mfi_transition_pct": float(ape[tr].mean() * 100) if tr.any() else float("nan"),
            "mae_density": float((p["density_pred"] - df["density_g_cm3"]).abs().mean()),
            "mae_activity_pct": float((p["activity_pred"] - df["catalyst_activity_pct"]).abs().mean()),
        }

    def stream(self) -> "StreamingTwin":
        return StreamingTwin(self)

    def save(self, path: str | Path) -> None:
        joblib.dump(self, path)

    @staticmethod
    def load(path: str | Path) -> "QualityCatalystTwin":
        return joblib.load(path)


class StreamingTwin:
    def __init__(self, twin: QualityCatalystTwin) -> None:
        self.twin, self._feat = twin, StreamingFeatures()

    def update(self, hydrogen_ratio: float, comonomer_ratio: float) -> dict[str, float]:
        x = self._feat.update(hydrogen_ratio, comonomer_ratio)
        p = {k: m.predict(x) for k, m in self.twin.models.items()}
        return {"mfi": float(np.exp(p["ln_mfi"][0])), "density": float(p["density"][0]),
                "activity_pct": float(p["activity"][0])}
