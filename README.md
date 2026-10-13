# Khalij-AryaSasol-MultiGrade-PE-Transition-Optimization-System (Khalij-AMPT)

## Intelligent Virtual Sensor System for Melt Flow Index/Density and Optimization of the Changeover Sequence Across 19 Polyethylene Grades (LDPE+MD/HDPE) with Minimum Transition Waste — Proprietary Product of Arya Sasol Polymer Company

> This document describes a **proprietary** product for Arya Sasol Polymer Company (Asaluyeh). Unlike most polyethylene producers in the holding, which have a limited number of grades, Arya Sasol operates with **19 grades** (9 LDPE grades licensed by Stamicarbon of the Netherlands + 10 MD/HDPE grades licensed by Basell of Germany) in two separate units, and needs a dedicated product to manage this complexity.

---

## 0. Understanding Arya Sasol Polymer Company and the Technical Gap

**Sources:** [Persian Wikipedia — Arya Sasol Polymer](https://fa.wikipedia.org/wiki/%D8%B4%D8%B1%DA%A9%D8%AA_%D9%BE%D9%84%DB%8C%D9%85%D8%B1_%D8%A2%D8%B1%DB%8C%D8%A7_%D8%B3%D8%A7%D8%B3%D9%88%D9%84), [Official site aryasasol.com — Medium and heavy polyethylene](https://www.aryasasol.com/fa/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA-%D9%88-%D9%81%D9%86%D8%A7%D9%88%D8%B1%DB%8C-%D9%87%D8%A7/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA/%D9%BE%D9%84%DB%8C-%D8%A7%D8%AA%DB%8C%D9%84%D9%86-%D9%85%D8%AA%D9%88%D8%B3%D8%B7-%D9%88-%D8%B3%D9%86%DA%AF%DB%8C%D9%86/)

### Products and Capacity

| Unit | Capacity | Number of grades | License |
|---|---|---|---|
| Olefin (ethylene) | 1,100,000 tons/year | — | — |
| LDPE | 375,000 tons/year | 9 grades | Stamicarbon (Netherlands) |
| MD/HDPE | 375,000 tons/year | 10 grades | Basell (Germany) — including the automotive fuel tank grade |

A total of **19 different grades** are produced in two separate units with different technologies (autoclave/tubular for LDPE, gas-phase/slurry for HDPE); frequent changeovers between grades to respond to market demand are the largest source of waste and lost effective production capacity in this type of complex.

### Technical Gap Relative to the Holding's Products 1 to 4

| Holding product | Why it is not sufficient for Arya Sasol |
|---|---|
| Product 1 (process parameter optimization) | It sees one unit, not the **optimal changeover sequence across 19 grades in two units** over a planning horizon (e.g., one month) |
| Product 4 (catalyst degradation) | Its model is designed for gradual catalyst degradation, not for **instantaneous catalyst activity during transitions between grades**, which behaves differently (abrupt change in comonomer/hydrogen ratio) |

**Conclusion:** Arya Sasol needs a "grade changeover sequence planning and optimization" layer at the level of the full 19-grade portfolio that is not covered by any other product.

---

## 1. Patent Background and Competitive Analysis

| No. | Existing patent/technology | Main limitation | Difference of this product |
|---|---|---|---|
| 1 | *Deep learning model predictive control of an HDPE reactor with physics-guided sequence-to-sequence model* (ScienceDirect) | Predictive control for **one specific transition** between two grades; does not address optimizing the sequence of multiple transitions over a planning horizon | Optimization of the **complete sequence** of transitions among 19 grades over a monthly horizon with the goal of minimizing cumulative waste |
| 2 | *Predicting polymer melt flow index and catalytic activity using a pretrained transformer-based model* (Polymer Bulletin) | MFI/catalyst activity prediction independent of production planning | Direct link of MFI/activity prediction to the changeover sequence planning engine |
| 3 | **US 10,577,435** – *Ethylene gas phase polymerisation process* | Chemical process of transition between one specific HDPE and one LLDPE; a process solution, not a software one | Generalization to software optimization for **any pair of grades** among the 19 grades, not a specific transition |
| 4 | **US 9,926,390** – *Method for production of polymer* | Catalyst/formulation improvement to reduce transition time; a materials approach | Complementary: software optimization of the scheduling and order of transitions with the existing catalyst |

### Core Patentable Claim

> **"A Multi-Grade Sequencing Optimizer system that, for the first time, combines a real-time virtual sensor of melt flow index (MFI) and density with a catalyst activity prediction model during transitions, and determines the optimal changeover sequence across a large grade portfolio (19 grades in two LDPE/HDPE units) over a monthly planning horizon, with the goal of simultaneously minimizing the number of transitions, transition time, and the total off-spec product of the portfolio."**

The focus on the **level of the complete grade portfolio** (not a single transition) has no precedent in the literature found.

---

## 2. SRS Document – Proprietary Product of Arya Sasol Polymer

### 2-1. Introduction
**Purpose:** Reduce transition-period waste and increase effective production rate through a real-time quality virtual sensor and grade changeover sequence optimization at the full portfolio level.

**Field challenges:**
- Frequent changeovers between 9 LDPE grades and 10 HDPE/MDPE grades to respond to market orders.
- Delay in laboratory measurement of MFI/density, which causes production of a significant amount of intermediate product (Transition/Off-grade).
- No systematic optimization of grade order (e.g., switching from a very low-density grade to a very high-density one takes a longer transition time than a gradual sequence).

**Scope:** Arya Sasol complex, Asaluyeh; connection to the DCS of the LDPE and MD/HDPE units.

### 2-2. General Requirements

| ID | Requirement | Priority |
| :--- | :--- | :--- |
| R-GEN-01 | Receive real-time data from both the LDPE and HDPE units (temperature, pressure, comonomer/hydrogen ratio, catalyst activity) | High |
| R-GEN-02 | Receive the monthly sales plan/demand for each of the 19 grades | High |
| R-GEN-03 | "Grade sequence map" dashboard showing planned transitions and current status | High |

### 2-3. Functional Requirements

| ID | Requirement | Patent capability |
| :--- | :--- | :--- |
| FR-SENSOR-01 | Real-time MFI and density virtual sensor for both LDPE/HDPE units | Dual-unit quality virtual sensor |
| FR-CAT-01 | Catalyst activity prediction during transitions (not only long-term degradation) | Transient activity prediction specific to grade changeover |
| FR-SEQ-01 | Optimize the changeover sequence among 19 grades over a monthly horizon while minimizing cumulative waste | **Portfolio-level sequence optimization (main innovation)** |
| FR-SEQ-02 | Propose the optimal transition path (gradual change rate of comonomer/hydrogen) for each specific grade pair | Optimal transition path for each grade pair |
| FR-ALERT-01 | Alert on deviation from the predicted transition path | Real-time corrective advisor |
| FR-LOOP-01 | Record the actual results of each transition (time and waste amount) for model retraining | Closed-loop learning |

### 2-4. Non-Functional Requirements

| ID | Requirement | Target value |
| :--- | :--- | :--- |
| NFR-PER-01 | MFI/density virtual sensor latency | Less than 15 seconds |
| NFR-PER-02 | MFI prediction accuracy (MAPE) | Less than 10% |
| NFR-AVAIL-01 | System availability | 99.9% |

### 2-5. Technical Architecture

```
┌──────────────────┐
│   API Gateway     │
└─────────┬─────────┘
┌─────────┼───────────────┬───────────────┐
┌───▼────────────┐┌───────▼────────┐┌──────▼──────────┐
│LDPE/HDPE        ││ MFI/Density    ││ Grade Sequencing │
│Ingestion (2     ││ Soft-Sensor +  ││ Optimizer        │
│ units DCS)      ││ Catalyst Model ││ (RL/MPC)         │
└──────┬──────────┘└───────┬────────┘└─────────┬────────┘
       └──────────┬────────┴───────────────────┘
                   ▼
        ┌────────────┐    ┌───────────────┐
        │   Kafka    │    │ TimescaleDB   │
        └────────────┘    └───────────────┘
```

| Suggested path | Description |
| :--- | :--- |
| `services/ldpe-hdpe-ingestion/` | DCS connection for both units |
| `services/quality-catalyst-twin/` | MFI/density virtual sensor + transient catalyst activity |
| `services/grade-sequencing-optimizer/` | Portfolio-level sequence optimizer |
| `shared/` | Reuse of products 1-4 |

---

## 3. Synthetic Data Generation Code

```python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

NUM_RECORDS = 10000
START_TIME = datetime(2026, 9, 14, 8, 0, 0)
timestamps = [START_TIME + timedelta(minutes=i) for i in range(NUM_RECORDS)]

grades_hdpe = [f"HDPE-G{i}" for i in range(1, 11)]
grades_ldpe = [f"LDPE-G{i}" for i in range(1, 10)]
all_grades = grades_hdpe + grades_ldpe

# Simulation of the current grade sequence (changes every ~400 records)
grade_schedule = np.random.choice(all_grades, size=NUM_RECORDS // 400 + 1)
current_grade = np.repeat(grade_schedule, 400)[:NUM_RECORDS]
is_transition = (np.arange(NUM_RECORDS) % 400 < 40).astype(int)  # first 40 records of each grade = transition period

comonomer_ratio = 0.015 + 0.01 * (pd.factorize(current_grade)[0] % 5) + np.random.normal(0, 0.001, NUM_RECORDS)
hydrogen_ratio = 0.002 + 0.0015 * (pd.factorize(current_grade)[0] % 4) + np.random.normal(0, 0.0002, NUM_RECORDS)
catalyst_activity_transient = 100 - 25 * is_transition + np.random.normal(0, 3, NUM_RECORDS)

melt_flow_index = 1.0 + 15 * hydrogen_ratio * 100 + np.random.normal(0, 0.3 + 1.5 * is_transition, NUM_RECORDS)
density_g_cm3 = 0.918 + 0.03 * (1 - comonomer_ratio * 20) + np.random.normal(0, 0.001 + 0.003 * is_transition, NUM_RECORDS)

off_spec_flag = (is_transition & (np.random.random(NUM_RECORDS) < 0.6)).astype(int)

df = pd.DataFrame({
    'timestamp': timestamps,
    'current_grade': current_grade,
    'is_transition': is_transition,
    'comonomer_ratio': np.round(comonomer_ratio, 4),
    'hydrogen_ratio': np.round(hydrogen_ratio, 5),
    'catalyst_activity_transient_percent': np.round(catalyst_activity_transient, 2),
    'melt_flow_index': np.round(melt_flow_index, 3),
    'density_g_cm3': np.round(density_g_cm3, 4),
    'off_spec_flag': off_spec_flag,
})

df.to_csv("aryasasol_grade_transition_data_10k.csv", index=False)
print(f"✅ Saved. Records: {len(df):,} - Variables: {len(df.columns)}")
print(df.describe())
```

---

## 4. Economic Justification

| Indicator | Current state | With Khalij-AMPT | Approximate financial impact |
| :--- | :--- | :--- | :--- |
| Transition-period waste | Independent of sequence, based on operator experience | Sequence optimization to minimize cumulative waste | Significant reduction of off-grade product on the combined 750,000 tons/year capacity of the two units |
| Transition time | Fixed/conservative | Optimal transition path based on catalyst prediction | Increase in effective production rate (uptime on the target grade) |

**Payback:** With 19 grades and frequent changeovers, even a 1-2% reduction in transition-period waste on a 750,000-ton capacity has significant economic value.

---

## 5. Proposed Evolution Roadmap (Phase 1-6)

| Phase | Capability |
| :--- | :--- |
| 1 | Base infrastructure + data simulator |
| 2 | MFI/density virtual sensor for both units |
| 3 | Transient catalyst activity prediction model |
| 4 | 19-grade portfolio-level sequence optimizer |
| 5 | Grade sequence map dashboard |
| 6 | Operational pilot on several real transitions |

---

## 6. Summary of Patentable Innovations

1. **Changeover sequence optimization at the level of the full 19-grade portfolio** (not a single transition).
2. **Virtual sensor of transient catalyst activity** during grade changeover, distinct from the long-term degradation model.
3. **Dedicated optimal transition path for each grade pair** with simultaneous minimization of time and waste.

---

## 7. References

- [Persian Wikipedia — Arya Sasol Polymer](https://fa.wikipedia.org/wiki/%D8%B4%D8%B1%DA%A9%D8%AA_%D9%BE%D9%84%DB%8C%D9%85%D8%B1_%D8%A2%D8%B1%DB%8C%D8%A7_%D8%B3%D8%A7%D8%B3%D9%88%D9%84)
- [Official Arya Sasol site — Medium and heavy polyethylene](https://www.aryasasol.com/fa/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA-%D9%88-%D9%81%D9%86%D8%A7%D9%88%D8%B1%DB%8C-%D9%87%D8%A7/%D9%85%D8%AD%D8%B5%D9%88%D9%84%D8%A7%D8%AA/%D9%BE%D9%84%DB%8C-%D8%A7%D8%AA%DB%8C%D9%84%D9%86-%D9%85%D8%AA%D9%88%D8%B3%D8%B7-%D9%88-%D8%B3%D9%86%DA%AF%DB%8C%D9%86/)
- [Deep learning model predictive control of an HDPE reactor — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0098135424002084)
- [Predicting polymer melt flow index and catalytic activity using a pretrained transformer-based model — Polymer Bulletin](https://link.springer.com/article/10.1007/s00289-026-06341-5)
- [US10577435 — Ethylene gas phase polymerisation process](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10577435)
- [US9926390 — Method for production of polymer](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9926390)
