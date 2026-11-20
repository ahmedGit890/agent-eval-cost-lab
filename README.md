# Agent Eval and Cost Lab

A small evaluation harness for LLM agents. It runs the same task suite under
different configurations and compares **success rate, cost per run, cost per
successful task, input tokens, cache hit rate and latency**.

It tests four cost-cutting techniques and their combinations:

| Technique | Idea | Risk it can introduce |
|---|---|---|
| Prompt caching | Reuse the stable prompt prefix at a discount | Needs a stable prefix |
| Context trimming | Keep only the latest N tool results | Loses early info; breaks the cache prefix |
| Model routing | Try a cheap model first, escalate if a verifier rejects | Pays for both attempts on failures |
| Retry (control) | A second attempt on the same model | Separates "two tries" from "cheap first" |

> **All numbers are SIMULATED.** Prices, model skill and token sizes are
> illustrative assumptions in `costlab/models.py`, not measurements of any real
> model. The project demonstrates the *method*; the conclusions only transfer to
> real systems once the simulator is replaced by measured data.

## Run

```
python -m unittest discover -s tests -t .
python run.py            # prints the table and writes docs/results.md
```

No dependencies, no API key.

## Results (simulated, 40 tasks x 5 trials, seed 0)

| Strategy | Success | Cost/run | Cost/success | vs baseline | Input tok/run | Cache hit | Latency (s) |
|---|---|---|---|---|---|---|---|
| baseline (large) | 66% | $0.0734 | $0.1120 | +0% | 19,510 | 0% | 12.9 |
| small only | 28% | $0.0061 | $0.0222 | -80% | 19,510 | 0% | 12.9 |
| caching | 66% | $0.0313 | $0.0478 | -57% | 19,510 | 80% | 12.2 |
| trim context (keep 2) | 52% | $0.0607 | $0.1168 | +4% | 15,300 | 0% | 12.6 |
| retry (large->large) | 86% | $0.1003 | $0.1166 | +4% | 26,684 | 0% | 17.5 |
| routing (small->large) | 73% | $0.0630 | $0.0863 | -23% | 34,686 | 0% | 22.7 |
| caching + routing | 73% | $0.0265 | $0.0363 | -68% | 34,686 | 80% | 21.4 |
| caching + trim + routing | 61% | $0.0304 | $0.0499 | -55% | 27,770 | 65% | 22.1 |

## What the simulation shows (under its assumptions)

- **Caching saves the most without hurting quality** (same success, -57% per
  success) because agent prompts re-send a long, growing prefix every step.
- **Trimming looks cheaper in tokens but is not cheaper per success**: success
  drops on tasks that need early context, and trimming shifts the history so
  the cache can reuse only the stable prefix (cache hit 80% -> 65% when combined).
- **Routing gains partly come from the second attempt.** The retry control
  reaches 86% success but costs more; routing is cheaper per success
  because the first attempt is cheap, at the price of higher latency.
- **"Small only" has the lowest cost per success but only 28% success.**
  Always read cost next to success rate.

## Limitations (read before citing any number)

- The verifier used for routing is perfect. A real verifier makes errors.
- Cache writes carry no premium, and there is no cache expiry.
- Steps are independent; real failures are correlated and recoverable.
- The default parameters were adjusted once after seeing a first run (task
  difficulty was too punishing) and a control strategy was added when a
  confound appeared. Parameters, not the code, drive the conclusions.
- Latency is a crude linear model.

## Roadmap (my next steps)

- [ ] Replace the simulator with a real LLM backend and record true token usage
- [ ] Use project 2's test-case agent as the real task suite
- [ ] Sensitivity analysis: how do conclusions change with price ratio and skill?
- [ ] Confidence intervals across seeds instead of a single seed
- [ ] Add a realistic imperfect verifier and measure its effect on routing
