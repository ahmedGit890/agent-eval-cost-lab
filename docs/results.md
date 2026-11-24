> SIMULATED results: prices, model skill and token sizes are illustrative assumptions (see costlab/models.py). 40 tasks x 5 trials per run.

## One run (seed 0)

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

## Mean of 20 seeds, with 95% bootstrap intervals

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
