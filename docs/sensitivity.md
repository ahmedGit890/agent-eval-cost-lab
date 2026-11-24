> SIMULATED. Each cell is the mean over 8 seeds (3 trials of 40 tasks each). Saving = how much cheaper per successful task a strategy is than the large model alone (negative = more expensive). dSuccess = change in success rate, in percentage points.

## 1. Routing: price ratio and small-model skill

Rows: how many times pricier the large model is. Columns: the small model's per-step success probability on an easy step. Cell: saving / dSuccess.

| price ratio \ small skill | 0.7 | 0.8 | 0.85 | 0.9 | 0.95 |
|---|---|---|---|---|---|
| 2 | -43% / +2pp | -29% / +5pp | -17% / +7pp | +0% / +12pp | +20% / +17pp |
| 5 | -14% / +2pp | -1% / +5pp | +10% / +7pp | +25% / +12pp | +44% / +17pp |
| 12 | -2% / +2pp | +10% / +5pp | +21% / +7pp | +35% / +12pp | +53% / +17pp |
| 30 | +3% / +2pp | +15% / +5pp | +25% / +7pp | +40% / +12pp | +57% / +17pp |

## 2. Routing: how good must the verifier be?

Rows: chance a wrong answer is wrongly accepted. Columns: chance a correct answer is wrongly rejected. Cell: saving / dSuccess.

| false accept \ false reject | 0.0 | 0.1 | 0.2 | 0.4 |
|---|---|---|---|---|
| 0.0 | +21% / +7pp | +18% / +6pp | +15% / +6pp | +9% / +4pp |
| 0.1 | +22% / +2pp | +19% / +1pp | +17% / +0pp | +10% / -1pp |
| 0.2 | +24% / -3pp | +21% / -4pp | +18% / -4pp | +10% / -6pp |
| 0.4 | +31% / -13pp | +27% / -14pp | +24% / -14pp | +15% / -16pp |

## 3. Prompt caching: size of the discount

| cache price (share of normal) | saving | dSuccess |
|---|---|---|
| 10% | +57% | +0pp |
| 25% | +48% | +0pp |
| 50% | +32% | +0pp |
| 75% | +16% | +0pp |
| 90% | +6% | +0pp |
| 100% | +0% | +0pp |
