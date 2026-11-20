"""Simulate one agent attempt and account for tokens, cost and latency."""
import random
from dataclasses import dataclass

from .models import (CACHE_READ_DISCOUNT, EARLY_CONTEXT_PENALTY, OUTPUT_TOKENS,
                     RESULT_TOKENS, SYSTEM_TOKENS, TASK_TOKENS)


@dataclass
class Usage:
    success: bool = False
    calls: int = 0
    input_tokens: int = 0    # all input tokens, cached or not
    cached_tokens: int = 0   # the part of input_tokens served from cache
    output_tokens: int = 0
    cost: float = 0.0        # dollars
    latency_ms: float = 0.0

    def add(self, other):
        self.calls += other.calls
        self.input_tokens += other.input_tokens
        self.cached_tokens += other.cached_tokens
        self.output_tokens += other.output_tokens
        self.cost += other.cost
        self.latency_ms += other.latency_ms


def rng_for(seed, task_id, trial, attempt):
    """Same draws for every strategy => differences come from the strategy, not luck."""
    return random.Random(f"{seed}/{task_id}/{trial}/{attempt}")


def run_attempt(task, model, strategy, rng):
    """One pass over the task's steps with a single model."""
    stable = SYSTEM_TOKENS + TASK_TOKENS
    usage = Usage()
    all_ok = True
    for i in range(task.steps):
        kept = i if strategy.keep_last is None else min(i, strategy.keep_last)
        dropped = i - kept
        context = stable + kept * RESULT_TOKENS

        cached = 0
        if strategy.cache and i > 0:
            if dropped == 0:
                cached = stable + (i - 1) * RESULT_TOKENS  # previous prompt is a prefix
            else:
                cached = stable  # trimming shifted history: only the stable prefix matches

        fresh = context - cached
        usage.calls += 1
        usage.input_tokens += context
        usage.cached_tokens += cached
        usage.output_tokens += OUTPUT_TOKENS
        usage.cost += (
            fresh * model.price_in
            + cached * model.price_in * CACHE_READ_DISCOUNT
            + OUTPUT_TOKENS * model.price_out
        ) / 1_000_000
        usage.latency_ms += 300 + 0.05 * fresh + 0.005 * cached + 10 * OUTPUT_TOKENS

        p = model.step_success_prob(task.difficulty)
        if task.needs_early_context and dropped > 0:
            p *= EARLY_CONTEXT_PENALTY
        if rng.random() >= p:
            all_ok = False  # the agent does not notice; it keeps going
    usage.success = all_ok
    return usage


def run_task(task, strategy, seed, trial):
    """Run with routing: if the (perfect) verifier rejects, retry on the bigger model."""
    total = run_attempt(task, strategy.model, strategy, rng_for(seed, task.id, trial, 0))
    if not total.success and strategy.escalate_to is not None:
        retry = run_attempt(task, strategy.escalate_to, strategy,
                            rng_for(seed, task.id, trial, 1))
        total.add(retry)
        total.success = retry.success
    return total
