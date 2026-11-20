import unittest

from costlab.agent import rng_for, run_attempt, run_task
from costlab.harness import evaluate, markdown_table
from costlab.models import (LARGE, OUTPUT_TOKENS, RESULT_TOKENS, SMALL, STRATEGIES,
                            SYSTEM_TOKENS, TASK_TOKENS, Strategy, Task, make_tasks)

STABLE = SYSTEM_TOKENS + TASK_TOKENS


class AlwaysSucceed:
    def random(self):
        return 0.0


def attempt(task, strategy, model=None):
    return run_attempt(task, model or strategy.model, strategy, AlwaysSucceed())


class AccountingTests(unittest.TestCase):
    def test_single_call_cost_matches_hand_calculation(self):
        u = attempt(Task(0, 1, 0.0, False), Strategy("b", LARGE))
        expected = (STABLE * LARGE.price_in + OUTPUT_TOKENS * LARGE.price_out) / 1e6
        self.assertAlmostEqual(u.cost, expected)
        self.assertEqual(u.calls, 1)
        self.assertEqual(u.input_tokens, STABLE)

    def test_context_grows_each_step(self):
        u = attempt(Task(0, 3, 0.0, False), Strategy("b", LARGE))
        self.assertEqual(u.input_tokens, 3 * STABLE + (0 + 1 + 2) * RESULT_TOKENS)

    def test_first_call_is_never_cached(self):
        u = attempt(Task(0, 1, 0.0, False), Strategy("c", LARGE, cache=True))
        self.assertEqual(u.cached_tokens, 0)

    def test_caching_is_cheaper_with_same_tokens(self):
        task = Task(0, 6, 0.0, False)
        plain = attempt(task, Strategy("b", LARGE))
        cached = attempt(task, Strategy("c", LARGE, cache=True))
        self.assertEqual(plain.input_tokens, cached.input_tokens)
        self.assertGreater(cached.cached_tokens, 0)
        self.assertLess(cached.cost, plain.cost)

    def test_trimming_reduces_input_tokens(self):
        task = Task(0, 8, 0.0, False)
        plain = attempt(task, Strategy("b", LARGE))
        trimmed = attempt(task, Strategy("t", LARGE, keep_last=2))
        self.assertLess(trimmed.input_tokens, plain.input_tokens)

    def test_trimming_breaks_cache_beyond_stable_prefix(self):
        task = Task(0, 8, 0.0, False)
        full = attempt(task, Strategy("c", LARGE, cache=True))
        trim = attempt(task, Strategy("ct", LARGE, cache=True, keep_last=2))
        # Per call, the trimmed run can only reuse the stable prefix once history shifts.
        self.assertLess(trim.cached_tokens / trim.input_tokens,
                        full.cached_tokens / full.input_tokens)

    def test_trimming_hurts_tasks_needing_early_context(self):
        class Borderline:  # succeeds only if the success probability is high enough
            def random(self):
                return 0.9

        task = Task(0, 6, 0.0, True)
        strat = Strategy("t", LARGE, keep_last=2)
        ok = run_attempt(task, LARGE, Strategy("b", LARGE), Borderline())
        hurt = run_attempt(task, LARGE, strat, Borderline())
        self.assertTrue(ok.success)
        self.assertFalse(hurt.success)  # 0.98 * 0.6 = 0.588 < 0.9


class RoutingTests(unittest.TestCase):
    def test_escalation_charges_both_attempts(self):
        task = Task(0, 10, 1.0, False)  # hard and long: small model usually fails
        strat = Strategy("r", SMALL, escalate_to=LARGE)
        for trial in range(50):
            first = run_attempt(task, SMALL, strat, rng_for(0, 0, trial, 0))
            if not first.success:
                total = run_task(task, strat, 0, trial)
                self.assertEqual(total.calls, 2 * task.steps)
                self.assertGreater(total.cost, first.cost)
                return
        self.fail("expected at least one small-model failure in 50 trials")

    def test_no_escalation_when_first_attempt_succeeds(self):
        task = Task(0, 1, 0.0, False)
        strat = Strategy("r", LARGE, escalate_to=SMALL)
        for trial in range(50):
            first = run_attempt(task, LARGE, strat, rng_for(0, 0, trial, 0))
            if first.success:
                self.assertEqual(run_task(task, strat, 0, trial).calls, 1)
                return
        self.fail("expected at least one success in 50 trials")


class HarnessTests(unittest.TestCase):
    def test_same_seed_is_deterministic(self):
        tasks = make_tasks(10)
        self.assertEqual(evaluate(STRATEGIES[0], tasks, 3, seed=1),
                         evaluate(STRATEGIES[0], tasks, 3, seed=1))

    def test_different_seed_changes_results(self):
        tasks = make_tasks(30)
        a = evaluate(STRATEGIES[0], tasks, 3, seed=1)
        b = evaluate(STRATEGIES[0], tasks, 3, seed=2)
        self.assertNotEqual(a.success_rate, b.success_rate)

    def test_table_baseline_row_is_zero_delta(self):
        tasks = make_tasks(10)
        table = markdown_table([evaluate(s, tasks, 2) for s in STRATEGIES[:3]])
        self.assertIn("+0%", table.splitlines()[2])

    def test_strategy_names_unique(self):
        names = [s.name for s in STRATEGIES]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
