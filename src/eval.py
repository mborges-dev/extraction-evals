"""Eval orchestrator — the entry point.

Usage:
    uv run python -m src.eval --models claude-sonnet-4-5 gpt-4o-2024-11-20 \
                              --prompts v1_baseline v2_structured \
                              --doc-types invoice

Writes results to results/<date>.csv. Prints a summary table to stdout.
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from src.loaders import iter_pairs
from src.metrics import exact_match, field_accuracy, macro_f1
from src.runners import ClaudeRunner, GeminiRunner, OpenAIRunner
from src.runners.base import BaseRunner, RunResult

load_dotenv()

app = typer.Typer(help="LLM extraction eval runner.")
console = Console()

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def _runner_for(model: str) -> BaseRunner:
    """Pick the runner class by model name."""
    if model.startswith("claude"):
        return ClaudeRunner(model=model)
    if model.startswith("gpt") or model.startswith("o1"):
        return OpenAIRunner(model=model)
    if model.startswith("gemini"):
        return GeminiRunner(model=model)
    raise ValueError(f"No runner mapped for model: {model}")


def _load_prompt(version: str) -> str:
    path = PROMPTS_DIR / f"{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def _try_parse_json(raw: str) -> dict | None:
    """Try multiple strategies to extract a JSON object from the response."""
    raw = raw.strip()
    # Direct
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Fenced ```json ... ```
    if "```json" in raw:
        try:
            inner = raw.split("```json", 1)[1].split("```", 1)[0]
            return json.loads(inner)
        except (IndexError, json.JSONDecodeError):
            pass
    # Fenced ``` ... ```
    if "```" in raw:
        try:
            inner = raw.split("```", 1)[1].split("```", 1)[0]
            return json.loads(inner)
        except (IndexError, json.JSONDecodeError):
            pass
    # First {...} block
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            pass
    return None


@app.command()
def run(
    models: Annotated[
        list[str] | None,
        typer.Option("--models", "-m", help="Models to evaluate. Repeatable."),
    ] = None,
    prompts: Annotated[
        list[str] | None,
        typer.Option("--prompts", "-p", help="Prompt versions to use. Repeatable."),
    ] = None,
    doc_types: Annotated[
        list[str] | None,
        typer.Option(
            "--doc-types", "-t", help="Restrict to one or more doc types (invoice/receipt/resume)."
        ),
    ] = None,
) -> None:
    """Run the eval matrix and write results to results/<date>.csv."""
    # Mutable defaults are forbidden by lint (B006), so initialize inside.
    if not models:
        models = ["claude-sonnet-4-5"]
    if not prompts:
        prompts = ["v1_baseline"]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Resolve pairs (cartesian product over doc types if not given)
    if doc_types:
        pairs = []
        for t in doc_types:
            pairs.extend(iter_pairs(t))
    else:
        pairs = list(iter_pairs())

    if not pairs:
        console.print("[red]No document pairs found in dataset/.[/red]")
        sys.exit(1)

    console.print(
        f"[bold cyan]Eval matrix:[/bold cyan]  "
        f"{len(models)} models × {len(prompts)} prompts × {len(pairs)} docs "
        f"= [bold]{len(models) * len(prompts) * len(pairs)}[/bold] calls"
    )

    rows: list[dict] = []
    for model in models:
        try:
            runner = _runner_for(model)
        except (RuntimeError, ValueError) as e:
            console.print(f"[yellow]Skipping {model}: {e}[/yellow]")
            continue

        for prompt_version in prompts:
            try:
                prompt = _load_prompt(prompt_version)
            except FileNotFoundError as e:
                console.print(f"[yellow]Skipping prompt {prompt_version}: {e}[/yellow]")
                continue

            for pair in pairs:
                console.print(f"  → {model} × {prompt_version} × {pair.doc_type}/{pair.doc_id}")
                try:
                    raw, usage = runner._call_model(prompt, pair.text)
                    parsed = _try_parse_json(raw)
                    error = None
                except Exception as e:  # noqa: BLE001
                    raw = ""
                    parsed = None
                    usage = {"input_tokens": 0, "output_tokens": 0}
                    error = str(e)

                gt_dict = json.loads(pair.ground_truth.model_dump_json())
                if parsed is None:
                    em = 0.0
                    fa = 0.0
                    f1 = 0.0
                else:
                    em = exact_match(parsed, gt_dict)
                    fa = field_accuracy(parsed, gt_dict)
                    f1 = macro_f1(parsed, gt_dict)

                result = RunResult(
                    model=model,
                    prompt_version=prompt_version,
                    doc_id=pair.doc_id,
                    doc_type=pair.doc_type,
                    raw_response=raw,
                    parsed_json=parsed,
                    input_tokens=usage.get("input_tokens", 0),
                    output_tokens=usage.get("output_tokens", 0),
                    cache_read_tokens=usage.get("cache_read_tokens", 0),
                    cache_write_tokens=usage.get("cache_write_tokens", 0),
                    latency_ms=usage.get("latency_ms", 0),
                    error=error,
                )
                cost = runner.estimated_cost_usd(usage)
                rows.append(
                    {
                        **asdict(result),
                        "exact_match": em,
                        "field_accuracy": fa,
                        "macro_f1": f1,
                        "cost_usd": cost,
                        # Drop raw_response from CSV — too verbose
                        "raw_response": (raw[:200] + "...") if len(raw) > 200 else raw,
                        "parsed_json": json.dumps(parsed) if parsed else "",
                    }
                )

    # Write CSV
    if not rows:
        console.print("[red]No results to write.[/red]")
        sys.exit(1)

    out_path = RESULTS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    console.print(f"\n[bold green]✓ Wrote {len(rows)} results to {out_path}[/bold green]\n")

    # Summary table
    table = Table(title="Summary (mean across docs)")
    table.add_column("Model", style="cyan")
    table.add_column("Prompt", style="magenta")
    table.add_column("Docs", justify="right")
    table.add_column("Exact %", justify="right")
    table.add_column("Field Acc %", justify="right")
    table.add_column("Macro F1", justify="right")
    table.add_column("Total $", justify="right", style="yellow")

    seen: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r["model"], r["prompt_version"])
        agg = seen.setdefault(
            key,
            {"docs": 0, "em": 0.0, "fa": 0.0, "f1": 0.0, "cost": 0.0},
        )
        agg["docs"] += 1
        agg["em"] += r["exact_match"]
        agg["fa"] += r["field_accuracy"]
        agg["f1"] += r["macro_f1"]
        agg["cost"] += r["cost_usd"]

    for (model, prompt_version), agg in sorted(seen.items()):
        n = agg["docs"]
        table.add_row(
            model,
            prompt_version,
            str(n),
            f"{100 * agg['em'] / n:.1f}",
            f"{100 * agg['fa'] / n:.1f}",
            f"{agg['f1'] / n:.3f}",
            f"${agg['cost']:.4f}",
        )

    console.print(table)


if __name__ == "__main__":
    app()
