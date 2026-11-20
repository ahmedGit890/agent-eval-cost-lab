"""Compare all strategies on the simulated task suite and write docs/results.md."""
from costlab.harness import compare, markdown_table
from costlab.models import STRATEGIES, make_tasks

NOTE = (
    "> SIMULATED results: prices, model skill and token sizes are illustrative "
    "assumptions (see costlab/models.py), 40 tasks x 5 trials, seed 0."
)


def main():
    table = markdown_table(compare(STRATEGIES, make_tasks(40), trials=5, seed=0))
    print(table)
    with open("docs/results.md", "w", encoding="utf-8") as f:
        f.write(f"{NOTE}\n\n{table}\n")


if __name__ == "__main__":
    main()
