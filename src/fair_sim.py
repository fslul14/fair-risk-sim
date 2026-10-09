"""FAIR-style Monte Carlo risk simulation.

Reads a JSON file of calibrated (min / most likely / max) estimates, simulates
many possible years, and reports annualized loss exposure as a distribution.

Model (one simulated year per iteration)
    TEF   threat events per year                     ~ PERT(min, mode, max)
    Vuln  P(threat event becomes a loss event)       ~ PERT
    LEF   loss event frequency = TEF * Vuln
    N     loss events this year                      ~ Poisson(LEF)
    PL    primary loss per event (USD)               ~ PERT
    SLP   P(a loss event also has secondary loss)    ~ PERT
    SL    secondary loss when it occurs (USD)        ~ PERT
    S     events with secondary loss                 ~ Binomial(N, SLP)
    Annual loss = N * PL + S * SL

Simplification (v1): epistemic draws (TEF, Vuln, PL, SLP, SL) are made once per
simulated year, so every event in the same year shares the same PL and SL.

Usage
    python src/fair_sim.py inputs.json --out output
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

PERT_LAMBDA = 4.0  # standard PERT weighting of the most likely value

# Chart tokens (single-series charts: one categorical slot, recessive chrome)
SURFACE = "#fcfcfb"
SERIES = "#2a78d6"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

REQUIRED = [
    "threat_event_frequency",
    "vulnerability",
    "primary_loss",
    "secondary_loss_probability",
    "secondary_loss",
]
PROBABILITIES = {"vulnerability", "secondary_loss_probability"}
SHORT_NAMES = {
    "threat_event_frequency": "Threat event frequency",
    "vulnerability": "Vulnerability",
    "primary_loss": "Primary loss per event",
    "secondary_loss_probability": "Secondary loss probability",
    "secondary_loss": "Secondary loss amount",
}


# ----------------------------------------------------------------------------
# Inputs
# ----------------------------------------------------------------------------
def load_inputs(path: Path) -> dict:
    cfg = json.loads(path.read_text())
    est = cfg.get("estimates", {})
    for key in REQUIRED:
        if key not in est:
            sys.exit(f"inputs missing estimate: {key}")
        e = est[key]
        lo, mode, hi = e["min"], e["most_likely"], e["max"]
        if not (lo <= mode <= hi):
            sys.exit(f"{key}: need min <= most_likely <= max (got {lo}, {mode}, {hi})")
        if lo < 0:
            sys.exit(f"{key}: negative values are not allowed")
        if key in PROBABILITIES and hi > 1:
            sys.exit(f"{key}: probabilities must be between 0 and 1")
    return cfg


def pert(rng: np.random.Generator, spec: dict, size: int) -> np.ndarray:
    """Sample a PERT (modified beta) distribution from min / most_likely / max."""
    lo, mode, hi = spec["min"], spec["most_likely"], spec["max"]
    if hi == lo:
        return np.full(size, float(lo))
    a = 1 + PERT_LAMBDA * (mode - lo) / (hi - lo)
    b = 1 + PERT_LAMBDA * (hi - mode) / (hi - lo)
    return lo + (hi - lo) * rng.beta(a, b, size)


# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------
def simulate(est: dict, n: int, seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    draws = {k: pert(rng, est[k], n) for k in REQUIRED}
    lef = draws["threat_event_frequency"] * draws["vulnerability"]
    events = rng.poisson(lef)
    with_secondary = rng.binomial(events, draws["secondary_loss_probability"])
    annual = events * draws["primary_loss"] + with_secondary * draws["secondary_loss"]
    return {"annual_loss": annual, "events": events, **draws}


def summarize(sim: dict, tolerance: float | None) -> dict:
    loss = sim["annual_loss"]
    out = {
        "iterations": int(loss.size),
        "mean": float(loss.mean()),
        "median": float(np.median(loss)),
        "p90": float(np.percentile(loss, 90)),
        "p95": float(np.percentile(loss, 95)),
        "p99": float(np.percentile(loss, 99)),
        "prob_any_loss": float((loss > 0).mean()),
    }
    if tolerance is not None:
        out["risk_tolerance_usd"] = float(tolerance)
        out["prob_exceeds_tolerance"] = float((loss > tolerance).mean())
    return out


def expected_loss(v: dict) -> float:
    """Expected annual loss for one set of point values: LEF * (primary + P(secondary) * secondary)."""
    return (v["threat_event_frequency"] * v["vulnerability"]
            * (v["primary_loss"] + v["secondary_loss_probability"] * v["secondary_loss"]))


def sensitivity(est: dict) -> tuple[float, dict[str, float]]:
    """One-at-a-time swing in expected annual loss as each input moves from its min to its max,
    with every other input held at its most likely value. Returns (base, swings sorted high to low).
    """
    base = {k: est[k]["most_likely"] for k in REQUIRED}
    swings = {}
    for k in REQUIRED:
        low, high = dict(base, **{k: est[k]["min"]}), dict(base, **{k: est[k]["max"]})
        swings[k] = expected_loss(high) - expected_loss(low)
    return expected_loss(base), dict(sorted(swings.items(), key=lambda kv: kv[1], reverse=True))


# ----------------------------------------------------------------------------
# Charts
# ----------------------------------------------------------------------------
def usd(x: float, _pos=None) -> str:
    if x >= 1e6:
        return f"${x / 1e6:.3g}M"
    if x >= 1e3:
        return f"${x / 1e3:.3g}K"
    return f"${x:.3g}"


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, length=0, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def header(fig, title: str, subtitle: str) -> None:
    fig.text(0.07, 0.95, title, ha="left", va="top", fontsize=13, color=INK, fontweight="bold")
    fig.text(0.07, 0.895, subtitle, ha="left", va="top", fontsize=9.5, color=INK_2)


def plot_exceedance(sim: dict, stats: dict, path: Path, tolerance: float | None) -> None:
    loss = np.sort(sim["annual_loss"])
    positive = loss[loss > 0]
    if positive.size == 0:
        return
    n = loss.size
    # P(annual loss >= x) for each positive x
    exceed = 1 - (np.searchsorted(loss, positive, side="left") / n)

    fig, ax = plt.subplots(figsize=(8, 4.6), facecolor=SURFACE)
    fig.subplots_adjust(left=0.1, right=0.95, top=0.78, bottom=0.14)
    style_axes(ax)
    ax.plot(positive, exceed, color=SERIES, linewidth=2)
    ax.set_xscale("log")
    ymax = min(1.0, stats["prob_any_loss"] * 1.25)  # most years can be zero-loss; zoom to where the curve lives
    ax.set_ylim(0, ymax)
    ax.set_xlim(positive.min(), positive.max())
    ax.xaxis.set_major_formatter(FuncFormatter(usd))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("Annual loss (log scale)", color=MUTED, fontsize=9)

    for label, key in (("median", "median"), ("90th pct", "p90")):
        if stats[key] > 0:
            ax.axvline(stats[key], color=AXIS, linewidth=1, linestyle=(0, (3, 3)))
            ax.text(stats[key], ymax * 0.97, f" {label}\n {usd(stats[key])}", color=INK_2,
                    fontsize=8.5, va="top", ha="left")
    if tolerance:
        ax.axvline(tolerance, color=INK_2, linewidth=1.2)
        ax.text(tolerance, ymax * 0.55, f" tolerance {usd(tolerance)}\n P(exceed) {stats['prob_exceeds_tolerance']:.1%}",
                color=INK, fontsize=8.5, va="center", ha="left")

    header(fig, "Loss exceedance curve",
           f"Chance that annual loss reaches at least X. P(any loss in a year) = {stats['prob_any_loss']:.0%}")
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)


def plot_sensitivity(base: float, swings: dict[str, float], path: Path) -> None:
    names = [SHORT_NAMES[k] for k in swings][::-1]
    values = list(swings.values())[::-1]
    fig, ax = plt.subplots(figsize=(8, 3.6), facecolor=SURFACE)
    fig.subplots_adjust(left=0.27, right=0.9, top=0.72, bottom=0.08)
    style_axes(ax)
    ax.grid(visible=False)
    ax.barh(names, values, color=SERIES, height=0.5)
    ax.set_xlim(0, max(values) * 1.2 if max(values) > 0 else 1)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", colors=INK_2, labelsize=9.5)
    ax.tick_params(axis="x", labelbottom=False)
    for i, v in enumerate(values):
        ax.text(v, i, f"  {usd(v)}", va="center", ha="left", color=INK_2, fontsize=9)
    header(fig, "What moves the expected loss most",
           f"Change in expected annual loss when one input goes from min to max (base case {usd(base)}/yr)")
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", type=Path, help="JSON file of estimates (see inputs.example.json)")
    ap.add_argument("--out", type=Path, default=Path("output"))
    ap.add_argument("--iterations", type=int, help="override iterations from the inputs file")
    ap.add_argument("--seed", type=int, help="override seed from the inputs file")
    args = ap.parse_args()

    cfg = load_inputs(args.inputs)
    n = args.iterations or cfg.get("iterations", 100_000)
    seed = args.seed if args.seed is not None else cfg.get("seed", 42)
    tolerance = cfg.get("risk_tolerance_usd")

    if cfg.get("example_only"):
        print("NOTE: these are illustrative example inputs. Replace them with your own "
              "calibrated estimates before publishing results.\n")

    sim = simulate(cfg["estimates"], n, seed)
    stats = summarize(sim, tolerance)
    base_el, swings = sensitivity(cfg["estimates"])

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "results.json").write_text(json.dumps({
        "scenario": cfg.get("scenario"), "seed": seed, "summary": stats,
        "base_case_expected_annual_loss": base_el, "expected_loss_swing_by_input": swings}, indent=2))
    plot_exceedance(sim, stats, args.out / "loss_exceedance.png", tolerance)
    plot_sensitivity(base_el, swings, args.out / "sensitivity.png")

    print(f"Scenario: {cfg.get('scenario')}")
    print(f"Iterations: {n:,}  seed: {seed}")
    print(f"P(any loss in a year): {stats['prob_any_loss']:.1%}")
    for label, key in (("Mean", "mean"), ("Median", "median"), ("90th percentile", "p90"),
                       ("95th percentile", "p95"), ("99th percentile", "p99")):
        print(f"{label:<16} {usd(stats[key])}")
    if tolerance:
        print(f"P(annual loss > {usd(tolerance)}): {stats['prob_exceeds_tolerance']:.1%}")
    print("Biggest driver of expected loss:", SHORT_NAMES[next(iter(swings))])
    print(f"Wrote results and charts to {args.out}/")


if __name__ == "__main__":
    main()
