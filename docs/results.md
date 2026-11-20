> SIMULATED results: prices, model skill and token sizes are illustrative assumptions (see costlab/models.py), 40 tasks x 5 trials, seed 0.

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
