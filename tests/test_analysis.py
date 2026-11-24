import math
import random
import unittest

from costlab.agent import run_task, verifier_rejects
from costlab.harness import compare_with_ci, evaluate, markdown_table_ci
from costlab.models import LARGE, SMALL, STRATEGIES, Strategy, Task, make_tasks
from costlab.sensitivity import (cache_discount_grid, grid_markdown, price_skill_grid,
                                 verifier_grid)
from costlab.stats import mean_ci

TASKS = make_tasks(20)
TASK = Task(0, 5, 0.0, False)


class StatsTests(unittest.TestCase):
    def test_interval_brackets_the_mean(self):
        i = mean_ci([1.0, 2.0, 3.0, 4.0, 5.0, 2.5, 3.5])
        self.assertLessEqual(i.low, i.mean)
        self.assertLessEqual(i.mean, i.high)

    def test_mean_is_the_plain_average(self):
        self.assertAlmostEqual(mean_ci([1.0, 2.0, 3.0]).mean, 2.0)

    def test_same_seed_gives_same_interval(self):
        values = [0.2, 0.4, 0.3, 0.9, 0.1, 0.5]
        self.assertEqual(mean_ci(values, seed=1), mean_ci(values, seed=1))

    def test_identical_values_have_zero_width(self):
        i = mean_ci([0.7] * 10)
        self.assertEqual((i.low, i.mean, i.high), (0.7, 0.7, 0.7))

    def test_single_value(self):
        i = mean_ci([3.0])
        self.assertEqual((i.low, i.mean, i.high), (3.0, 3.0, 3.0))

    def test_empty_input_gives_nan(self):
        self.assertTrue(math.isnan(mean_ci([]).mean))

    def test_infinite_values_are_ignored(self):
        self.assertAlmostEqual(mean_ci([1.0, 3.0, math.inf]).mean, 2.0)

    def test_more_spread_gives_a_wider_interval(self):
        narrow = mean_ci([5, 5.1, 4.9, 5, 5.05, 4.95])
        wide = mean_ci([1, 9, 2, 8, 3, 7])
        self.assertGreater(wide.high - wide.low, narrow.high - narrow.low)


class VerifierTests(unittest.TestCase):
    def test_perfect_verifier_rejects_exactly_the_wrong_answers(self):
        s = Strategy("r", SMALL, escalate_to=LARGE)
        rng = random.Random(0)
        for _ in range(50):
            self.assertFalse(verifier_rejects(s, True, rng))
            self.assertTrue(verifier_rejects(s, False, rng))

    def test_false_accept_one_never_rejects_a_wrong_answer(self):
        s = Strategy("r", SMALL, escalate_to=LARGE, false_accept=1.0)
        rng = random.Random(0)
        self.assertFalse(any(verifier_rejects(s, False, rng) for _ in range(50)))

    def test_false_reject_one_always_rejects_a_correct_answer(self):
        s = Strategy("r", SMALL, escalate_to=LARGE, false_reject=1.0)
        rng = random.Random(0)
        self.assertTrue(all(verifier_rejects(s, True, rng) for _ in range(50)))

    def test_a_verifier_that_accepts_everything_never_escalates(self):
        s = Strategy("r", SMALL, escalate_to=LARGE, false_accept=1.0)
        for trial in range(30):
            usage = run_task(TASK, s, 0, trial)
            self.assertFalse(usage.escalated)
            self.assertEqual(usage.calls, TASK.steps)

    def test_a_verifier_that_rejects_everything_always_escalates_and_pays_twice(self):
        s = Strategy("r", SMALL, escalate_to=LARGE, false_reject=1.0)
        for trial in range(30):
            usage = run_task(TASK, s, 0, trial)
            self.assertTrue(usage.escalated)
            self.assertEqual(usage.calls, 2 * TASK.steps)

    def test_perfect_verifier_escalation_rate_equals_first_attempt_failure_rate(self):
        routed = evaluate(Strategy("r", SMALL, escalate_to=LARGE), TASKS, 4, 0)
        small_only = evaluate(Strategy("s", SMALL), TASKS, 4, 0)  # same first-attempt draws
        self.assertAlmostEqual(routed.escalation_rate, 1 - small_only.success_rate)

    def test_wrong_accepts_lower_the_success_rate(self):
        perfect = evaluate(Strategy("p", SMALL, escalate_to=LARGE), TASKS, 4, 0)
        leaky = evaluate(Strategy("l", SMALL, escalate_to=LARGE, false_accept=0.5), TASKS, 4, 0)
        self.assertLess(leaky.success_rate, perfect.success_rate)

    def test_wrong_rejects_raise_the_cost(self):
        perfect = evaluate(Strategy("p", SMALL, escalate_to=LARGE), TASKS, 4, 0)
        jumpy = evaluate(Strategy("j", SMALL, escalate_to=LARGE, false_reject=0.5), TASKS, 4, 0)
        self.assertGreater(jumpy.avg_cost, perfect.avg_cost)


class CacheDiscountTests(unittest.TestCase):
    def test_no_discount_costs_the_same_as_no_cache(self):
        plain = evaluate(Strategy("a", LARGE), TASKS, 3, 0)
        full_price = evaluate(Strategy("b", LARGE, cache=True, cache_discount=1.0), TASKS, 3, 0)
        self.assertAlmostEqual(plain.avg_cost, full_price.avg_cost)

    def test_a_bigger_discount_costs_less(self):
        small = evaluate(Strategy("a", LARGE, cache=True, cache_discount=0.5), TASKS, 3, 0)
        big = evaluate(Strategy("b", LARGE, cache=True, cache_discount=0.1), TASKS, 3, 0)
        self.assertLess(big.avg_cost, small.avg_cost)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.rows = compare_with_ci(STRATEGIES[:3], TASKS, range(5), trials=2)

    def test_baseline_saving_is_exactly_zero(self):
        s = self.rows[0].saving
        self.assertEqual((s.low, s.mean, s.high), (0.0, 0.0, 0.0))

    def test_every_interval_brackets_its_mean(self):
        for r in self.rows:
            for i in (r.success, r.cost_per_success, r.saving):
                self.assertLessEqual(i.low, i.mean)
                self.assertLessEqual(i.mean, i.high)

    def test_results_are_repeatable(self):
        again = compare_with_ci(STRATEGIES[:3], TASKS, range(5), trials=2)
        self.assertEqual(self.rows, again)

    def test_caching_saves_money_in_every_seed_so_the_interval_excludes_zero(self):
        caching = self.rows[2].saving
        self.assertGreater(caching.low, 0.0)

    def test_table_has_one_row_per_strategy(self):
        table = markdown_table_ci(self.rows).splitlines()
        self.assertEqual(len(table), 2 + len(self.rows))


class SensitivityTests(unittest.TestCase):
    seeds = range(3)

    def test_routing_saves_more_when_the_large_model_is_pricier(self):
        cells = price_skill_grid(ratios=(2, 30), skills=(0.85,), tasks=TASKS,
                                 seeds=self.seeds, trials=2)
        self.assertGreater(cells[(30, 0.85)][0].mean, cells[(2, 0.85)][0].mean)

    def test_routing_saves_more_when_the_small_model_is_better(self):
        cells = price_skill_grid(ratios=(12,), skills=(0.7, 0.95), tasks=TASKS,
                                 seeds=self.seeds, trials=2)
        self.assertGreater(cells[(12, 0.95)][0].mean, cells[(12, 0.7)][0].mean)

    def test_a_leaky_verifier_lowers_success(self):
        cells = verifier_grid(false_accepts=(0.0, 0.4), false_rejects=(0.0,), tasks=TASKS,
                              seeds=self.seeds, trials=2)
        self.assertLess(cells[(0.4, 0.0)][1].mean, cells[(0.0, 0.0)][1].mean)

    def test_caching_saving_shrinks_as_the_discount_shrinks(self):
        cells = cache_discount_grid(discounts=(0.1, 0.5, 1.0), tasks=TASKS,
                                    seeds=self.seeds, trials=2)
        savings = [cells[d][0].mean for d in (0.1, 0.5, 1.0)]
        self.assertGreater(savings[0], savings[1])
        self.assertGreater(savings[1], savings[2])
        self.assertAlmostEqual(savings[2], 0.0)

    def test_grid_markdown_has_the_right_shape(self):
        cells = {(r, c): (r, c) for r in (1, 2) for c in (10, 20, 30)}
        text = grid_markdown("row", "col", (1, 2), (10, 20, 30), cells, lambda cell: str(cell))
        lines = text.splitlines()
        self.assertEqual(len(lines), 2 + 2)
        self.assertIn("row \\ col", lines[0])
        self.assertIn("(2, 30)", lines[-1])


if __name__ == "__main__":
    unittest.main()
