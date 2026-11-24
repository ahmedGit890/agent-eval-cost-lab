"""Evaluation harness: run strategies over a task suite and compare them."""
import math
from dataclasses import dataclass

from .agent import run_task
from .stats import Interval, mean_ci


@dataclass
class Summary:
    name: str
    runs: int
    success_rate: float
    avg_cost: float
    cost_per_success: float
    avg_input_tokens: float
    cache_hit_rate: float
    avg_latency_s: float
    escalation_rate: float = 0.0


def evaluate(strategy, tasks, trials=5, seed=0):
    runs = [run_task(t, strategy, seed, k) for t in tasks for k in range(trials)]
    n = len(runs)
    wins = sum(r.success for r in runs)
    cost = sum(r.cost for r in runs)
    inp = sum(r.input_tokens for r in runs)
    return Summary(
        name=strategy.name,
        runs=n,
        success_rate=wins / n,
        avg_cost=cost / n,
        cost_per_success=cost / wins if wins else math.inf,
        avg_input_tokens=inp / n,
        cache_hit_rate=(sum(r.cached_tokens for r in runs) / inp) if inp else 0.0,
        avg_latency_s=sum(r.latency_ms for r in runs) / n / 1000,
        escalation_rate=sum(r.escalated for r in runs) / n,
    )


def compare(strategies, tasks, trials=5, seed=0):
    return [evaluate(s, tasks, trials, seed) for s in strategies]


def markdown_table(summaries):
    """Table with savings measured against the first strategy (the baseline)."""
    base = summaries[0]
    rows = [
        "| Strategy | Success | Cost/run | Cost/success | vs baseline | "
        "Input tok/run | Cache hit | Latency (s) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        delta = (s.cost_per_success / base.cost_per_success - 1) * 100
        rows.append(
            f"| {s.name} | {s.success_rate:.0%} | ${s.avg_cost:.4f} | "
            f"${s.cost_per_success:.4f} | {delta:+.0f}% | {s.avg_input_tokens:,.0f} | "
            f"{s.cache_hit_rate:.0%} | {s.avg_latency_s:.1f} |"
        )
    return "\n".join(rows)


# ---- many seeds, with confidence intervals ---------------------------------

@dataclass
class IntervalRow:
    name: str
    success: Interval
    cost_per_success: Interval
    saving: Interval  # 1 - cost_per_success / baseline's, paired by seed (positive = cheaper)


def compare_with_ci(strategies, tasks, seeds, trials=5):
    """Evaluate every strategy under every seed and report means with 95% intervals.

    The first strategy is the baseline. Savings are computed seed by seed (the same
    random draws for both strategies), so the interval reflects the strategy's effect
    rather than luck. Only outcome randomness varies; the task suite is fixed.
    """
    seeds = list(seeds)
    per = [[evaluate(s, tasks, trials, seed) for seed in seeds] for s in strategies]
    baseline = per[0]
    rows = []
    for strategy, summaries in zip(strategies, per):
        savings = [1 - s.cost_per_success / b.cost_per_success
                   for s, b in zip(summaries, baseline)]
        rows.append(IntervalRow(
            name=strategy.name,
            success=mean_ci(s.success_rate for s in summaries),
            cost_per_success=mean_ci(s.cost_per_success for s in summaries),
            saving=mean_ci(savings),
        ))
    return rows


def markdown_table_ci(rows):
    def pct(i):
        return f"{i.mean:.0%} ({i.low:.0%} to {i.high:.0%})"

    def usd(i):
        return f"${i.mean:.4f} (${i.low:.4f} to ${i.high:.4f})"

    def signed(i):
        return f"{i.mean:+.0%} ({i.low:+.0%} to {i.high:+.0%})"

    lines = [
        "| Strategy | Success | Cost per success | Saving vs baseline |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r.name} | {pct(r.success)} | {usd(r.cost_per_success)} | {signed(r.saving)} |")
    return "\n".join(lines)
