"""Evaluation harness: run strategies over a task suite and compare them."""
import math
from dataclasses import dataclass

from .agent import run_task


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
