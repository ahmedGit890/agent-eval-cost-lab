"""Small statistics helpers (standard library only)."""
import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    mean: float
    low: float
    high: float


def mean_ci(values, level=0.95, n_boot=2000, seed=0):
    """Mean with a bootstrap percentile confidence interval.

    Resamples the values with replacement `n_boot` times. The fixed seed makes the
    interval repeatable. With very few values the interval is wide and unreliable.
    """
    values = [v for v in values if math.isfinite(v)]
    if not values:
        return Interval(math.nan, math.nan, math.nan)
    n = len(values)
    mean = sum(values) / n
    if n == 1:
        return Interval(mean, mean, mean)
    rng = random.Random(seed)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    low = means[int((1 - level) / 2 * n_boot)]
    high = means[int((1 + level) / 2 * n_boot) - 1]
    return Interval(mean, low, high)
