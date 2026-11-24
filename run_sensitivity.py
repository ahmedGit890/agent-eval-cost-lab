"""Vary the assumptions one pair at a time and write docs/sensitivity.md."""
from costlab.sensitivity import (cache_discount_grid, grid_markdown, price_skill_grid,
                                 verifier_grid)

NOTE = (
    "> SIMULATED. Each cell is the mean over 8 seeds (3 trials of 40 tasks each). "
    "Saving = how much cheaper per successful task a strategy is than the large model "
    "alone (negative = more expensive). dSuccess = change in success rate, in "
    "percentage points."
)


def saving_and_success(cell):
    saving, success = cell
    return f"{saving.mean:+.0%} / {success.mean * 100:+.0f}pp"


def main():
    parts = [NOTE]

    ratios, skills = (2, 5, 12, 30), (0.70, 0.80, 0.85, 0.90, 0.95)
    cells = price_skill_grid(ratios, skills)
    parts += [
        "\n## 1. Routing: price ratio and small-model skill\n",
        "Rows: how many times pricier the large model is. Columns: the small model's "
        "per-step success probability on an easy step. Cell: saving / dSuccess.\n",
        grid_markdown("price ratio", "small skill", ratios, skills, cells, saving_and_success),
    ]

    fas, frs = (0.0, 0.1, 0.2, 0.4), (0.0, 0.1, 0.2, 0.4)
    cells = verifier_grid(fas, frs)
    parts += [
        "\n## 2. Routing: how good must the verifier be?\n",
        "Rows: chance a wrong answer is wrongly accepted. Columns: chance a correct "
        "answer is wrongly rejected. Cell: saving / dSuccess.\n",
        grid_markdown("false accept", "false reject", fas, frs, cells, saving_and_success),
    ]

    discounts = (0.1, 0.25, 0.5, 0.75, 0.9, 1.0)
    cells = cache_discount_grid(discounts)
    lines = ["| cache price (share of normal) | saving | dSuccess |", "|---|---|---|"]
    for d in discounts:
        saving, success = cells[d]
        lines.append(f"| {d:.0%} | {saving.mean:+.0%} | {success.mean * 100:+.0f}pp |")
    parts += ["\n## 3. Prompt caching: size of the discount\n", "\n".join(lines)]

    text = "\n".join(parts) + "\n"
    print(text)
    with open("docs/sensitivity.md", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
