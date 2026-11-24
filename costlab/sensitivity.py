"""Sensitivity analysis: which conclusions survive when the assumptions change?

Every conclusion in this lab rests on made-up numbers (prices, model skill,
verifier quality, cache discount). Here we vary one pair of assumptions at a
time and report the saving of a strategy against the baseline (the large model
alone), averaged over several seeds. Positive means cheaper per successful task.
"""
from dataclasses import replace

from .harness import evaluate
from .models import LARGE, SMALL, Strategy, make_tasks
from .stats import mean_ci


def paired(baseline, strategy, tasks, seeds, trials):
    """Saving in cost per success and change in success rate, paired by seed."""
    savings, success_changes = [], []
    for seed in seeds:
        base = evaluate(baseline, tasks, trials, seed)
        test = evaluate(strategy, tasks, trials, seed)
        savings.append(1 - test.cost_per_success / base.cost_per_success)
        success_changes.append(test.success_rate - base.success_rate)
    return mean_ci(savings), mean_ci(success_changes)


def price_skill_grid(ratios=(2, 5, 12, 30), skills=(0.70, 0.80, 0.85, 0.90, 0.95),
                     tasks=None, seeds=range(8), trials=3):
    """Routing (small, then large) vs the large model alone.

    ratios: how many times pricier the large model is than the small one.
    skills: the small model's per-step success probability on an easy step.
    """
    tasks = tasks or make_tasks(40)
    cells = {}
    for ratio in ratios:
        large = replace(LARGE, price_in=SMALL.price_in * ratio, price_out=SMALL.price_out * ratio)
        for skill in skills:
            small = replace(SMALL, skill=skill)
            baseline = Strategy("baseline", large)
            routed = Strategy("routing", small, escalate_to=large)
            cells[(ratio, skill)] = paired(baseline, routed, tasks, seeds, trials)
    return cells


def verifier_grid(false_accepts=(0.0, 0.1, 0.2, 0.4), false_rejects=(0.0, 0.1, 0.2, 0.4),
                  tasks=None, seeds=range(8), trials=3):
    """Routing with an imperfect verifier vs the large model alone."""
    tasks = tasks or make_tasks(40)
    baseline = Strategy("baseline", LARGE)
    cells = {}
    for fa in false_accepts:
        for fr in false_rejects:
            routed = Strategy("routing", SMALL, escalate_to=LARGE, false_accept=fa, false_reject=fr)
            cells[(fa, fr)] = paired(baseline, routed, tasks, seeds, trials)
    return cells


def cache_discount_grid(discounts=(0.1, 0.25, 0.5, 0.75, 0.9, 1.0),
                        tasks=None, seeds=range(8), trials=3):
    """Prompt caching vs no caching, as the cache discount shrinks (1.0 = no discount)."""
    tasks = tasks or make_tasks(40)
    baseline = Strategy("baseline", LARGE)
    return {d: paired(baseline, Strategy("caching", LARGE, cache=True, cache_discount=d),
                      tasks, seeds, trials) for d in discounts}


def grid_markdown(row_label, col_label, row_values, col_values, cells, cell_text):
    """A markdown table with one row per row_value and one column per col_value."""
    header = f"| {row_label} \\ {col_label} | " + " | ".join(str(c) for c in col_values) + " |"
    lines = [header, "|---" * (len(col_values) + 1) + "|"]
    for r in row_values:
        lines.append(f"| {r} | " + " | ".join(cell_text(cells[(r, c)]) for c in col_values) + " |")
    return "\n".join(lines)
