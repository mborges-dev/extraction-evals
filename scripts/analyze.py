"""Read results/*.csv and produce a comparison chart per metric.

Usage:
    uv run python scripts/analyze.py results/2026-06-09.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

OUT_DIR = Path(__file__).resolve().parent.parent / "results" / "charts"


def main(csv_path: str) -> None:
    df = pd.read_csv(csv_path)
    if df.empty:
        print(f"No rows in {csv_path}", file=sys.stderr)
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_stem = Path(csv_path).stem

    # Aggregate per (model, prompt_version)
    agg = (
        df.groupby(["model", "prompt_version"])
        .agg(
            macro_f1=("macro_f1", "mean"),
            field_accuracy=("field_accuracy", "mean"),
            exact_match=("exact_match", "mean"),
            cost_usd=("cost_usd", "sum"),
            latency_ms=("latency_ms", "mean"),
        )
        .reset_index()
    )

    # Chart 1: macro F1 by model × prompt
    fig, ax = plt.subplots(figsize=(10, 5))
    pivot_f1 = agg.pivot(index="prompt_version", columns="model", values="macro_f1")
    pivot_f1.plot(kind="bar", ax=ax)
    ax.set_title("Macro F1 by prompt version × model")
    ax.set_ylabel("Macro F1")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="lower right")
    plt.tight_layout()
    out1 = OUT_DIR / f"{out_stem}-macro-f1.png"
    plt.savefig(out1, dpi=120)
    print(f"→ {out1}")

    # Chart 2: cost vs F1 (cost effectiveness)
    fig, ax = plt.subplots(figsize=(10, 5))
    for model in agg["model"].unique():
        sub = agg[agg["model"] == model]
        ax.scatter(sub["cost_usd"], sub["macro_f1"], label=model, s=80)
        for _, row in sub.iterrows():
            ax.annotate(
                row["prompt_version"],
                (row["cost_usd"], row["macro_f1"]),
                fontsize=8,
                xytext=(5, 5),
                textcoords="offset points",
            )
    ax.set_xlabel("Total cost (USD, this run)")
    ax.set_ylabel("Macro F1")
    ax.set_title("Cost vs accuracy — top-left is the sweet spot")
    ax.legend()
    plt.tight_layout()
    out2 = OUT_DIR / f"{out_stem}-cost-vs-f1.png"
    plt.savefig(out2, dpi=120)
    print(f"→ {out2}")

    # Markdown summary
    out_md = OUT_DIR / f"{out_stem}-summary.md"
    with out_md.open("w") as f:
        f.write(f"# Eval summary — {out_stem}\n\n")
        f.write("| Model | Prompt | F1 | Field Acc | Exact | Cost | Latency (ms) |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|\n")
        for _, row in agg.iterrows():
            f.write(
                f"| {row['model']} | {row['prompt_version']} | "
                f"{row['macro_f1']:.3f} | {row['field_accuracy']:.3f} | "
                f"{row['exact_match']:.3f} | ${row['cost_usd']:.4f} | "
                f"{row['latency_ms']:.0f} |\n"
            )
    print(f"→ {out_md}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: analyze.py <path-to-results.csv>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
