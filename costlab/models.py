"""Simulated models, tasks and cost-saving strategies.

EVERYTHING HERE IS ILLUSTRATIVE. Prices, skill levels and token counts are
made-up round numbers chosen to show the method. Replace them with measured
values (see README roadmap) before drawing real conclusions.
"""
import random
from dataclasses import dataclass
from typing import Optional

# Token sizes of the pieces that make up an agent's prompt.
SYSTEM_TOKENS = 1500    # system prompt + tool descriptions (stable prefix)
TASK_TOKENS = 200       # the user's task text (stable prefix)
RESULT_TOKENS = 400     # one tool result appended to history per step
OUTPUT_TOKENS = 150     # the model's reply per step
CACHE_READ_DISCOUNT = 0.1   # cached input tokens cost 10% of normal
EARLY_CONTEXT_PENALTY = 0.6  # step success multiplier if needed context was trimmed


@dataclass(frozen=True)
class Model:
    name: str
    price_in: float   # dollars per 1M input tokens
    price_out: float  # dollars per 1M output tokens
    skill: float      # base per-step success probability on an easy step

    def step_success_prob(self, difficulty):
        return max(0.05, min(0.999, self.skill - 0.12 * difficulty))


SMALL = Model("small", price_in=0.25, price_out=1.25, skill=0.85)
LARGE = Model("large", price_in=3.00, price_out=15.00, skill=0.98)


@dataclass(frozen=True)
class Task:
    id: int
    steps: int
    difficulty: float          # 0 (easy) .. 1 (hard)
    needs_early_context: bool  # needs info from the first steps at the end


@dataclass(frozen=True)
class Strategy:
    name: str
    model: Model
    escalate_to: Optional[Model] = None  # routing: retry on this model if the first fails
    cache: bool = False                  # prompt caching of the stable prefix
    keep_last: Optional[int] = None      # context trimming: keep only N latest results
    cache_discount: float = CACHE_READ_DISCOUNT  # share of the normal price paid for cached tokens
    # Routing verifier quality. 0 and 0 is a perfect verifier (the original behaviour).
    false_accept: float = 0.0  # chance a WRONG answer is wrongly accepted (no escalation)
    false_reject: float = 0.0  # chance a CORRECT answer is wrongly rejected (needless escalation)


def make_tasks(n=40, seed=0):
    rng = random.Random(seed)
    return [
        Task(
            id=i,
            steps=rng.randint(3, 10),
            difficulty=round(rng.random() * 0.8, 2),
            needs_early_context=(i % 4 == 0),
        )
        for i in range(n)
    ]


STRATEGIES = [
    Strategy("baseline (large)", LARGE),
    Strategy("small only", SMALL),
    Strategy("caching", LARGE, cache=True),
    Strategy("trim context (keep 2)", LARGE, keep_last=2),
    # Control: a second attempt on the same model. Compare with routing to see how
    # much of routing's gain is just "two tries" rather than "cheap model first".
    Strategy("retry (large->large)", LARGE, escalate_to=LARGE),
    Strategy("routing (small->large)", SMALL, escalate_to=LARGE),
    Strategy("caching + routing", SMALL, escalate_to=LARGE, cache=True),
    Strategy("caching + trim + routing", SMALL, escalate_to=LARGE, cache=True, keep_last=2),
]
