"""Unit specifications and the 19-grade portfolio.

All numeric values here are ILLUSTRATIVE PLACEHOLDERS (the README gives only the
grade counts and licensors). Replace them with the real datasheet targets and
plant-identified dynamics before any operational use.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UnitSpec:
    name: str
    rate_tph: float            # nominal production rate, t/h
    tau_h: float               # property response time constant, hours
    slow_factor: float         # tau multiplier for the slow direction (MFI down, density up)
    k_mfi: float               # steady state: MFI = k_mfi * hydrogen_ratio
    rho0: float                # steady state: density = rho0 - k_c * comonomer_ratio
    k_c: float
    tol_ln_mfi: float = 0.095  # ~ +/-10 % on MFI
    tol_rho: float = 0.002     # g/cm3
    max_overshoot: float = 0.6 # max setpoint overshoot as a fraction of the step
    fixed_loss_t: float = 5.0  # purge/sampling loss per changeover, t
    act_base: float = 5.0      # catalyst activity dip model (percent points)
    act_k_mfi: float = 4.0
    act_k_c: float = 600.0
    act_tau_h: float = 0.5


UNITS: dict[str, UnitSpec] = {
    "LDPE": UnitSpec("LDPE", rate_tph=47.0, tau_h=0.6, slow_factor=1.5,
                     k_mfi=3000.0, rho0=0.935, k_c=1.0),
    "HDPE": UnitSpec("HDPE", rate_tph=47.0, tau_h=2.0, slow_factor=1.5,
                     k_mfi=1500.0, rho0=0.968, k_c=1.5, act_tau_h=1.0),
}


@dataclass(frozen=True)
class Grade:
    id: str
    unit: str
    mfi: float       # g/10 min
    density: float   # g/cm3

    def recipe(self) -> tuple[float, float]:
        """Steady-state (hydrogen_ratio, comonomer_ratio) producing this grade."""
        u = UNITS[self.unit]
        return self.mfi / u.k_mfi, (u.rho0 - self.density) / u.k_c


_LDPE = [(0.3, 0.9195), (0.8, 0.9205), (2.0, 0.9185), (4.0, 0.9215), (7.0, 0.9225),
         (20.0, 0.9195), (30.0, 0.9235), (50.0, 0.9245), (70.0, 0.9255)]
_HDPE = [(0.05, 0.9400), (0.2, 0.9450), (0.3, 0.9500), (0.7, 0.9550), (1.0, 0.9580),
         (2.0, 0.9600), (5.0, 0.9620), (8.0, 0.9420), (12.0, 0.9530), (20.0, 0.9640)]

GRADES: dict[str, Grade] = {}
for i, (m, d) in enumerate(_LDPE, 1):
    GRADES[f"LDPE-G{i}"] = Grade(f"LDPE-G{i}", "LDPE", m, d)
for i, (m, d) in enumerate(_HDPE, 1):
    GRADES[f"HDPE-G{i}"] = Grade(f"HDPE-G{i}", "HDPE", m, d)


def grades_of(unit: str) -> list[Grade]:
    return [g for g in GRADES.values() if g.unit == unit]
