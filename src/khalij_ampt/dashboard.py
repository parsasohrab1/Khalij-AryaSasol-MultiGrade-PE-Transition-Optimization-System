"""Grade sequence map dashboard (Phase 5, R-GEN-03): self-contained HTML."""
from __future__ import annotations

from html import escape

from .optimizer import UnitPlan

PALETTE = ["#2a6fdb", "#e07b00", "#2e9e5b", "#b0409a", "#c0392b", "#16a2b8", "#7d6608",
           "#5d6d7e", "#8e44ad", "#d35400"]


def _unit_block(plan: UnitPlan, current: str | None) -> str:
    total = plan.campaign_total_h + plan.transition_h
    parts, t = [], 0.0
    for i, g in enumerate(plan.sequence):
        if i:
            tr = plan.transitions[i - 1]
            parts.append(
                f'<div class="tr" style="width:{100 * tr.time_h / total:.3f}%" '
                f'title="{escape(tr.src)} → {escape(tr.dst)}: {tr.time_h:.1f} h, '
                f'{tr.waste_t:.0f} t off-grade"></div>')
            t += tr.time_h
        w = plan.campaign_h[g]
        cur = " cur" if g == current else ""
        parts.append(
            f'<div class="c{cur}" style="width:{100 * w / total:.3f}%;'
            f'background:{PALETTE[i % len(PALETTE)]}" title="{escape(g)}: {w:.0f} h">'
            f'{escape(g.split("-")[1])}</div>')
        t += w
    rows = "".join(
        f"<tr><td>{escape(x.src)} → {escape(x.dst)}</td><td>{x.time_h:.1f}</td>"
        f"<td>{x.waste_t:.0f}</td><td>{x.dip_pct:.0f}</td></tr>" for x in plan.transitions)
    ok = "feasible" if plan.feasible else "INFEASIBLE (exceeds horizon)"
    return (f"<h2>{escape(plan.unit)}</h2><p>{len(plan.sequence)} grades · off-grade "
            f"<b>{plan.waste_t:.0f} t</b> · transition {plan.transition_h:.1f} h · "
            f"campaigns {plan.campaign_total_h:.0f} h of {plan.horizon_h:.0f} h · {ok}</p>"
            f'<div class="bar">{"".join(parts)}</div>'
            "<table><tr><th>Transition</th><th>Time (h)</th><th>Off-grade (t)</th>"
            f"<th>Catalyst dip (%)</th></tr>{rows}</table>")


def render(plans: dict[str, UnitPlan], current: dict[str, str] | None = None) -> str:
    current = current or {}
    body = "".join(_unit_block(p, current.get(u)) for u, p in plans.items())
    total = sum(p.waste_t for p in plans.values())
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Khalij-AMPT grade sequence map</title><style>
body{{font:14px system-ui,sans-serif;margin:16px;max-width:1100px;background:#fff;color:#1b1f24}}
.bar{{display:flex;height:44px;border:1px solid #ccc;border-radius:4px;overflow:hidden}}
.c{{color:#fff;font-size:12px;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.cur{{outline:3px solid #000;outline-offset:-3px}}
.tr{{background:repeating-linear-gradient(45deg,#999,#999 3px,#ddd 3px,#ddd 6px);min-width:2px}}
table{{border-collapse:collapse;margin:12px 0}}td,th{{border:1px solid #ddd;padding:3px 8px;text-align:right}}
td:first-child,th:first-child{{text-align:left}}
@media(prefers-color-scheme:dark){{body{{background:#14171a;color:#e6e8ea}}td,th{{border-color:#333}}}}
</style></head><body><h1>Grade sequence map</h1>
<p>Portfolio off-grade (planned): <b>{total:.0f} t</b>. Hatched = transition, black outline = running now.
Values from placeholder grade specs unless a grades CSV was loaded.</p>{body}</body></html>"""
