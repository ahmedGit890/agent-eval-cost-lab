# Agent Eval and Cost Lab

![tests](https://github.com/ahmedGit890/agent-eval-cost-lab/actions/workflows/tests.yml/badge.svg)

A small evaluation harness for LLM agents. It runs the same task suite under
different configurations and compares **success rate, cost per run, cost per
successful task, input tokens, cache hit rate and latency**. It reports
results over many random seeds with confidence intervals, and checks which
conclusions survive when its assumptions change.

It tests four cost-cutting techniques and their combinations:

| Technique | Idea | Risk it can introduce |
|---|---|---|
| Prompt caching | Reuse the stable prompt prefix at a discount | Needs a stable prefix |
| Context trimming | Keep only the latest N tool results | Loses early info; breaks the cache prefix |
| Model routing | Try a cheap model first, escalate if a verifier rejects | Pays for both attempts on failures; verifier mistakes |
| Retry (control) | A second attempt on the same model | Separates "two tries" from "cheap first" |

> **All numbers are SIMULATED.** Prices, model skill, verifier quality and
> token sizes are illustrative assumptions in `costlab/models.py`, not
> measurements of any real model. The project demonstrates the *method*; the
> conclusions only transfer to real systems once the simulator is replaced by
> measured data.

## Run

```
python -m unittest discover -s tests -t .
python run.py               # strategy comparison, 20 seeds -> docs/results.md
python run_sensitivity.py   # vary the assumptions        -> docs/sensitivity.md
```

No dependencies, no API key.

## 1. Strategy comparison (20 seeds, 95% bootstrap intervals)

40 tasks x 5 trials per seed. Savings are computed seed by seed against the
baseline, using the same random draws for both, so they measure the strategy
and not luck. A single-run table is in [docs/results.md](docs/results.md).

| Strategy | Success | Cost per success | Saving vs baseline |
|---|---|---|---|
| baseline (large) | 63% (62% to 65%) | $0.1166 ($0.1140 to $0.1194) | +0% (+0% to +0%) |
| small only | 25% (23% to 26%) | $0.0252 ($0.0240 to $0.0264) | +78% (+77% to +79%) |
| caching | 63% (62% to 65%) | $0.0498 ($0.0487 to $0.0510) | +57% (+57% to +57%) |
| trim context (keep 2) | 52% (50% to 53%) | $0.1181 ($0.1154 to $0.1209) | -1% (-3% to +0%) |
| retry (large->large) | 84% (83% to 85%) | $0.1226 ($0.1200 to $0.1253) | -5% (-6% to -4%) |
| routing (small->large) | 71% (70% to 72%) | $0.0912 ($0.0896 to $0.0929) | +22% (+20% to +23%) |
| caching + routing | 71% (70% to 72%) | $0.0385 ($0.0378 to $0.0392) | +67% (+66% to +68%) |
| caching + trim + routing | 58% (56% to 59%) | $0.0539 ($0.0528 to $0.0551) | +54% (+52% to +55%) |

What it shows under these assumptions:

- **Caching saves the most with no loss of quality**, because an agent re-sends
  a long, growing prefix at every step.
- **Trimming does not pay.** It cuts input tokens but loses information on tasks
  that need early context (success 63% to 52%) and breaks the cache prefix.
  In one run (seed 0) it looked 4% more expensive; over 20 seeds it is about
  break-even. A single run hides that.
- **Part of routing's benefit is just "two tries".** Retrying on the same large
  model raises success to 84% but costs 5% more per success; routing is cheaper
  than baseline because the first attempt is cheap.
- **"Small only" is the cheapest per success but succeeds on only 25% of runs.**
  Always read cost next to success rate.

## 2. Sensitivity analysis

Each cell is the mean over 8 seeds. "Saving" is how much cheaper per successful
task than the large model alone (negative = more expensive); dSuccess is the
change in success rate in percentage points. Full output in
[docs/sensitivity.md](docs/sensitivity.md).

**Routing: how pricier the large model is (rows) and how good the small model is (columns)**

| price ratio \ small skill | 0.7 | 0.8 | 0.85 | 0.9 | 0.95 |
|---|---|---|---|---|---|
| 2 | -43% / +2pp | -29% / +5pp | -17% / +7pp | +0% / +12pp | +20% / +17pp |
| 5 | -14% / +2pp | -1% / +5pp | +10% / +7pp | +25% / +12pp | +44% / +17pp |
| 12 | -2% / +2pp | +10% / +5pp | +21% / +7pp | +35% / +12pp | +53% / +17pp |
| 30 | +3% / +2pp | +15% / +5pp | +25% / +7pp | +40% / +12pp | +57% / +17pp |

The "+22% saving" for routing in section 1 holds only around price ratio 12 and
small-model skill 0.85. When the models are closer in price, or the small model
is weaker, **routing costs more than using the large model alone.**

**Routing with an imperfect verifier**

| wrongly accepted (rows) \ wrongly rejected (cols) | 0% | 10% | 20% | 40% |
|---|---|---|---|---|
| 0% | +21% / +7pp | +18% / +6pp | +15% / +6pp | +9% / +4pp |
| 10% | +22% / +2pp | +19% / +1pp | +17% / +0pp | +10% / -1pp |
| 20% | +24% / -3pp | +21% / -4pp | +18% / -4pp | +10% / -6pp |
| 40% | +31% / -13pp | +27% / -14pp | +24% / -14pp | +15% / -16pp |

- **Wrongly accepting bad answers makes the numbers look better while quality
  falls**: at 40% false accepts the saving is the largest (+31%) but success
  drops 13 points. Cost per success alone rewards a sloppy verifier, so it must
  be reported with the success rate.
- **Wrongly rejecting good answers erodes the saving** (+21% to +9% at 40%),
  because correct work is paid for twice.

**Prompt caching: size of the discount**

| cache price (share of normal) | saving |
|---|---|
| 10% | +57% |
| 25% | +48% |
| 50% | +32% |
| 75% | +16% |
| 90% | +6% |
| 100% | +0% |

The caching saving scales almost linearly with the discount, so it depends on
the provider's actual cache pricing.

## Limitations (read before citing any number)

- Everything is simulated. The conclusions are about this simulator's
  assumptions, which the sensitivity analysis tests but cannot make real.
- The confidence intervals reflect **outcome randomness only**. The task suite,
  prices and skill levels are fixed in each table. Narrow intervals do **not**
  mean the real-world saving is certain.
- Only 8 seeds and 3 trials per cell in the sensitivity grids.
- The verifier's error rates are fixed numbers. A real verifier errs more on
  hard tasks.
- A rejected answer is replaced by the retry even when the first was correct,
  so a false reject can lower quality as well as raise cost.
- Cache writes carry no premium and there is no cache expiry.
- Steps are independent; real failures are correlated and recoverable.
- Default parameters were adjusted once after a first run (task difficulty was
  too punishing), and a control strategy was added when a confound appeared.
  The parameters, not the code, drive the conclusions.
- Latency is a crude linear model.

## Roadmap (my next steps)

- [ ] Replace the simulator with a real LLM backend and record true token usage
- [ ] Use the test-case agent project as the real task suite
- [ ] Vary the task suite across seeds, not only the random outcomes
- [ ] Make the verifier's error rate depend on task difficulty
- [x] Confidence intervals across seeds instead of a single seed
- [x] Sensitivity analysis: price ratio, model skill, cache discount
- [x] An imperfect verifier and its effect on routing
