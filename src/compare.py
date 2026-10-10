"""Compare two FAIR scenarios (today vs. with a control) and stress-test the answer.

Usage
    python src/compare.py inputs.json inputs_after.json --out output \
        --annual-cost 140000 --one-time 40000 --years 3

Writes output/comparison.json, output/comparison.png and output/tolerance_sweep.png.

It answers three questions
    1. How much does the control lower expected annual loss and the chance of a bad year?
    2. What is the most any control could save? (the ceiling = today's expected loss)
    3. What if attempts are more frequent than I estimated? The sweep multiplies my whole
       threat-event-frequency range by m and reports (a) the chance of a year above the risk
       tolerance and (b) the expected-loss benefit of the control against its price.

How to read the numbers
    - Expected losses and the break-even multiplier are computed exactly (closed form, see
      fair_sim.py) and checked against the simulation.
    - Inputs that are identical in the two files get identical random draws, but the Poisson and
      Binomial event counts do not line up draw for draw, so the simulated difference is NOT a
      paired comparison. Its standard error is computed as two independent estimates.
    - Scaling the threat-event-frequency range by m scales expected loss by exactly m. The chance
      of exceeding the tolerance does not scale that way, which is why the sweep simulates it.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

import fair_sim as fs

ORANGE = "#eb6834"  # categorical slot 2
TEF = "threat_event_frequency"
SWEEP_POINTS = (1, 2, 3, 4, 5, 10, 20)


def curve(loss: np.ndarray):
    s = np.sort(loss)
    pos = s[s > 0]
    exceed = 1 - np.searchsorted(s, pos, side="left") / s.size
    return pos, exceed


def run(path: Path, iterations: int | None):
    cfg = fs.load_inputs(path)
    n = iterations or cfg.get("iterations", 100_000)
    seed = cfg.get("seed", 42)
    loss = fs.simulate(cfg["estimates"], n, seed)["annual_loss"]
    tol = cfg.get("risk_tolerance_usd")
    return cfg, n, seed, loss, {
        "mean": float(loss.mean()),
        "mean_standard_error": float(loss.std(ddof=1) / np.sqrt(loss.size)),
        "p99": float(np.percentile(loss, 99)),
        "prob_any_loss": float((loss > 0).mean()),
        "prob_exceeds_tolerance": float((loss > tol).mean()) if tol else None,
    }


# ----------------------------------------------------------------------------
# Threat-frequency sweep
# ----------------------------------------------------------------------------
def scaled(est: dict, m: float) -> dict:
    """Copy of the estimates with the whole threat-event-frequency range multiplied by m."""
    out = copy.deepcopy(est)
    for k in ("min", "most_likely", "max"):
        out[TEF][k] *= m
    return out


def p_exceed(est: dict, m: float, tol: float, n: int, seed: int) -> float:
    return float((fs.simulate(scaled(est, m), n, seed)["annual_loss"] > tol).mean())


def crossing(est: dict, tol: float, limit: float, n: int, seed: int, hi: float = 60.0):
    """Smallest multiplier m at which P(annual loss > tol) reaches `limit` (bisection)."""
    lo = 0.1
    if p_exceed(est, lo, tol, n, seed) > limit:
        return None
    if p_exceed(est, hi, tol, n, seed) < limit:
        return None
    for _ in range(14):
        mid = (lo * hi) ** 0.5
        if p_exceed(est, mid, tol, n, seed) < limit:
            lo = mid
        else:
            hi = mid
    return float((lo * hi) ** 0.5)


# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------
def plot(loss_a, loss_b, tol, stats_a, stats_b, path: Path):
    fig, ax = plt.subplots(figsize=(8, 4.8), facecolor=fs.SURFACE)
    fig.subplots_adjust(left=0.1, right=0.95, top=0.78, bottom=0.14)
    fs.style_axes(ax)
    xa, ya = curve(loss_a)
    xb, yb = curve(loss_b)
    ax.plot(xa, ya, color=fs.SERIES, linewidth=2, label="Today (manual offboarding)")
    ax.plot(xb, yb, color=ORANGE, linewidth=2, label="With automated deprovisioning")
    ax.set_xscale("log")
    ymax = min(1.0, max(stats_a["prob_any_loss"], stats_b["prob_any_loss"]) * 1.25)
    ax.set_ylim(0, ymax)
    ax.set_xlim(min(xa.min(), xb.min()), max(xa.max(), xb.max()))
    ax.xaxis.set_major_formatter(FuncFormatter(fs.usd))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1%}"))
    ax.set_xlabel("Annual loss (log scale)", color=fs.MUTED, fontsize=9)
    if tol:
        ax.axvline(tol, color=fs.INK_2, linewidth=1.2)
        ax.text(tol, ymax * 0.62,
                f" tolerance {fs.usd(tol)}\n today {stats_a['prob_exceeds_tolerance']:.1%}"
                f"\n with control {stats_b['prob_exceeds_tolerance']:.1%}",
                color=fs.INK, fontsize=8.5, va="center", ha="left")
    leg = ax.legend(loc="upper right", frameon=False, fontsize=9)
    for t in leg.get_texts():
        t.set_color(fs.INK_2)
    fs.header(fig, "Chance that annual loss reaches at least X",
              f"Same scenario with one input changed. P(any loss) {stats_a['prob_any_loss']:.1%} today vs "
              f"{stats_b['prob_any_loss']:.1%} with the control")
    fig.savefig(path, dpi=200, facecolor=fs.SURFACE)
    plt.close(fig)


def plot_sweep(rows, tol, limit, cross_a, cross_b, breakeven, path: Path):
    ms = [r["multiplier"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4.8), facecolor=fs.SURFACE)
    fig.subplots_adjust(left=0.1, right=0.95, top=0.78, bottom=0.16)
    fs.style_axes(ax)
    ax.plot(ms, [r["prob_exceeds_tolerance_today"] for r in rows], color=fs.SERIES, linewidth=2,
            label="Today (manual offboarding)")
    ax.plot(ms, [r["prob_exceeds_tolerance_with_control"] for r in rows], color=ORANGE, linewidth=2,
            label="With automated deprovisioning")
    ax.set_xscale("log")
    ax.set_xlim(1, max(ms))
    ax.set_ylim(0, 0.7)
    ax.set_xticks([1, 2, 3, 5, 10, 20, 50])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}x"))
    ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("How many times higher than my estimate the attempt rate is (log scale)", color=fs.MUTED, fontsize=9)

    ax.axhline(limit, color=fs.INK_2, linewidth=1.2)
    ax.text(1.03, limit + 0.01, f"limit {limit:.0%}", color=fs.INK, fontsize=8.5, ha="left", va="bottom")
    for m, color in ((cross_a, fs.SERIES), (cross_b, ORANGE)):
        if m:
            ax.plot([m], [limit], marker="o", markersize=7, color=color, markeredgecolor=fs.SURFACE,
                    markeredgewidth=2, zorder=5)
    if cross_a and cross_b:
        ax.text(5.5, limit / 2, f"dots: passes the limit at {cross_a:.1f}x today, {cross_b:.1f}x with control",
                color=fs.INK_2, fontsize=8.5, ha="left", va="center")
    ax.axvline(breakeven, color=fs.AXIS, linewidth=1, linestyle=(0, (3, 3)))
    ax.text(breakeven * 0.96, 0.69, f"control pays for itself\nin expected loss at {breakeven:.0f}x", color=fs.INK_2,
            fontsize=8.5, ha="right", va="top")
    leg = ax.legend(loc="upper left", frameon=False, fontsize=9)
    for t in leg.get_texts():
        t.set_color(fs.INK_2)
    fs.header(fig, f"Chance of a year above {fs.usd(tol)} if attempts are more frequent than I estimated",
              "x multiplies my whole attempt-rate range (0.03 / 0.1 / 0.6 a year). The control moves the limit only a little.")
    fig.savefig(path, dpi=200, facecolor=fs.SURFACE)
    plt.close(fig)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--annual-cost", type=float, required=True, help="recurring yearly cost of the control (USD)")
    ap.add_argument("--one-time", type=float, default=0.0, help="one-time cost (USD)")
    ap.add_argument("--years", type=float, default=3.0, help="years over which to spread the one-time cost")
    ap.add_argument("--iterations", type=int)
    args = ap.parse_args()

    cfg_a, n, seed, loss_a, a = run(args.before, args.iterations)
    cfg_b, _, _, loss_b, b = run(args.after, args.iterations)
    tol = cfg_a.get("risk_tolerance_usd")
    limit = cfg_a.get("tolerance_max_probability", 0.05)

    exact_a = fs.closed_form_expected_loss(cfg_a["estimates"])
    exact_b = fs.closed_form_expected_loss(cfg_b["estimates"])
    benefit = exact_a - exact_b
    annualized_cost = args.annual_cost + args.one_time / args.years
    breakeven = annualized_cost / benefit if benefit > 0 else None
    sim_benefit = a["mean"] - b["mean"]
    sim_benefit_se = float(np.hypot(a["mean_standard_error"], b["mean_standard_error"]))

    out = {
        "before": a, "after": b,
        "exact_expected_loss": {"before": exact_a, "after": exact_b, "reduction_per_year": benefit},
        "simulated_reduction_per_year": {"value": sim_benefit, "standard_error": sim_benefit_se},
        "annualized_control_cost": annualized_cost,
        "net_benefit_per_year": benefit - annualized_cost,
        "ceiling_on_benefit_per_year": exact_a,  # a control cannot save more than today's whole expected loss
        "breakeven_threat_multiplier": breakeven,
        "cost_assumptions": {"annual": args.annual_cost, "one_time": args.one_time, "years": args.years},
    }

    if tol:
        sweep_n = min(n, 400_000)
        grid = sorted({round(float(x), 3) for x in np.geomspace(1, 60, 30)} | set(SWEEP_POINTS)
                      | ({round(breakeven, 3)} if breakeven else set()))
        rows = []
        for m in grid:
            pa = p_exceed(cfg_a["estimates"], m, tol, sweep_n, seed)
            pb = p_exceed(cfg_b["estimates"], m, tol, sweep_n, seed)
            rows.append({"multiplier": m, "prob_exceeds_tolerance_today": pa, "prob_exceeds_tolerance_with_control": pb,
                         "expected_loss_today": exact_a * m, "expected_loss_with_control": exact_b * m,
                         "net_benefit_of_control": benefit * m - annualized_cost})
        cross_a = crossing(cfg_a["estimates"], tol, limit, sweep_n, seed)
        cross_b = crossing(cfg_b["estimates"], tol, limit, sweep_n, seed)
        out["tolerance"] = {"usd": tol, "max_probability": limit,
                            "multiplier_where_limit_is_passed_today": cross_a,
                            "multiplier_where_limit_is_passed_with_control": cross_b}
        out["threat_frequency_sweep"] = rows

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "comparison.json").write_text(json.dumps(out, indent=2))
    plot(loss_a, loss_b, tol, a, b, args.out / "comparison.png")
    if tol:
        plot_sweep(rows, tol, limit, cross_a, cross_b, breakeven, args.out / "tolerance_sweep.png")

    u = fs.usd
    print(f"Expected annual loss (exact)  today {u(exact_a)}  ->  with control {u(exact_b)}")
    print(f"Simulated                     today {u(a['mean'])} +/- {u(a['mean_standard_error'])}  ->  "
          f"{u(b['mean'])} +/- {u(b['mean_standard_error'])}")
    print(f"Reduction per year    {u(benefit)} exact; simulated {u(sim_benefit)} +/- {u(sim_benefit_se)} "
          f"(ceiling for any control: {u(exact_a)})")
    print(f"Control cost per year {u(annualized_cost)}  ({u(args.annual_cost)}/yr + {u(args.one_time)} over {args.years:g} yrs)")
    print(f"Net benefit per year  {'-' if out['net_benefit_per_year'] < 0 else ''}{u(abs(out['net_benefit_per_year']))}")
    if breakeven:
        print(f"Break-even: attempts would need to be {breakeven:.1f}x my estimate for the control to pay for itself")
    if tol:
        print(f"P(annual loss > {u(tol)})  today {a['prob_exceeds_tolerance']:.1%}  ->  with control {b['prob_exceeds_tolerance']:.1%}")
        fmt = lambda x: f"{x:.1f}x" if x else "never"
        print(f"The {limit:.0%} limit on that chance is passed at {fmt(cross_a)} my attempt rate today, "
              f"{fmt(cross_b)} with the control")
        for r in rows:
            if r["multiplier"] in SWEEP_POINTS:
                print(f"  {r['multiplier']:>4g}x attempts: P(> {u(tol)}) {r['prob_exceeds_tolerance_today']:.1%} today, "
                      f"{r['prob_exceeds_tolerance_with_control']:.1%} with control; "
                      f"net benefit of control {'-' if r['net_benefit_of_control'] < 0 else ''}{u(abs(r['net_benefit_of_control']))}/yr")
    print(f"Wrote comparison.json, comparison.png and tolerance_sweep.png to {args.out}/")


if __name__ == "__main__":
    main()
