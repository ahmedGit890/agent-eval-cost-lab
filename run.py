"""Compare all strategies on the simulated task suite and write docs/results.md.

Two tables: a single run (seed 0), and the mean over 20 seeds with 95% intervals.
"""
from costlab.harness import compare, compare_with_ci, markdown_table, markdown_table_ci
from costlab.models import STRATEGIES, make_tasks

NOTE = (
    "> SIMULATED results: prices, model skill and token sizes are illustrative "
    "assumptions (see costlab/models.py). 40 tasks x 5 trials per run."
)
SEEDS = range(20)


def main():
    tasks = make_tasks(40)
    single = markdown_table(compare(STRATEGIES, tasks, trials=5, seed=0))
    multi = markdown_table_ci(compare_with_ci(STRATEGIES, tasks, SEEDS, trials=5))
    text = (
        f"{NOTE}\n\n## One run (seed 0)\n\n{single}\n\n"
        f"## Mean of {len(SEEDS)} seeds, with 95% bootstrap intervals\n\n{multi}\n"
    )
    print(text)
    with open("docs/results.md", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
