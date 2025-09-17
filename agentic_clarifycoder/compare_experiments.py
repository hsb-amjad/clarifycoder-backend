"""
compare_experiments.py
----------------------
Experiment runner for ClarifyCoder-Agent.

Runs baseline-only, LLM-only, and hybrid settings on the same prompts.
Logs results to JSON files and prints side-by-side metrics.
Also generates bar charts, trend plots, and exports results for papers.

Usage:
    python compare_experiments.py --n_prompts 10 --runs 3 --answer_mode auto
    python compare_experiments.py --n_prompts 10 --runs 3 --answer_mode human
    -> run from root agentic_clarifycoder
"""

import argparse
import json
import os
import subprocess
from statistics import mean
import csv

# Optional extras
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
import pandas as pd


DEMO_MODULE = "agentic_clarifycoder.core.demo.demo"


def run_mode(mode_name: str, n_prompts: int, seed: int, run_id: int, answer_mode: str):
    """
    Run ClarifyCoder-Agent in a given mode via demo.py and save logs.
    """
    if mode_name == "baseline":
        clarify, code, evalm, refine = "baseline", "baseline", "baseline", "baseline"
    elif mode_name == "llm":
        clarify, code, evalm, refine = "llm", "llm", "baseline", "llm"
    elif mode_name == "hybrid":
        clarify, code, evalm, refine = "llm", "baseline", "baseline", "llm"
    else:
        raise ValueError(f"Unknown mode {mode_name}")

    os.makedirs("logs", exist_ok=True)
    out_file = f"logs/{mode_name}_run{run_id}.json"

    print(f"\n=== Running {mode_name.upper()} (run {run_id}) ===")

    cmd = [
        "python", "-m", DEMO_MODULE,
        f"--clarify_mode={clarify}",
        f"--code_mode={code}",
        f"--eval_mode={evalm}",
        f"--refine_mode={refine}",
        f"--answer_mode={answer_mode}",   # 🔥 pass answer mode
        "--num_prompts", str(n_prompts),
        "--seed", str(seed),
        "--log_file", out_file
    ]

    subprocess.run(cmd, check=True)


def collect_metrics(mode_name: str):
    """
    Collect metrics from all runs for a given mode.
    """
    files = [f for f in os.listdir("logs") if f.startswith(mode_name)]
    metrics = {
        "CRR": [], "CSR": [], "ARSR": [], "RFR": [], "USR": [], "Coverage": []
    }

    for fpath in files:
        try:
            with open(os.path.join("logs", fpath), "r", encoding="utf-8") as f:
                entry = json.load(f)
                if "metrics" in entry:
                    m = entry["metrics"]
                    for k in metrics.keys():
                        if k in m:
                            metrics[k].append(m[k])
        except Exception as e:
            print(f"Warning: could not read {fpath}: {e}")

    return {k: round(mean(v), 2) if v else 0 for k, v in metrics.items()}


def export_results(all_results, csv_file="results.csv", excel_file="results.xlsx"):
    """
    Export metrics to CSV and Excel.
    """
    df = pd.DataFrame(all_results).set_index("Mode")
    df.to_csv(csv_file)
    df.to_excel(excel_file)
    print(f"\n[+] Results exported to {csv_file} and {excel_file}")


def plot_bar_chart(all_results, save_path="results_bar.png"):
    """
    Side-by-side bar chart for metrics across modes.
    """
    df = pd.DataFrame(all_results).set_index("Mode")
    df.plot(kind="bar", figsize=(10, 6))
    plt.title("ClarifyCoder-Agent Metrics Comparison")
    plt.ylabel("Score")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()
    print(f"[+] Bar chart saved to {save_path}")


def plot_trends(mode_name, save_path=None):
    """
    Plot trend over runs for a single mode.
    """
    files = sorted([f for f in os.listdir("logs") if f.startswith(mode_name)])
    if not files:
        return
    run_ids, arsrs = [], []
    for idx, fpath in enumerate(files, 1):
        with open(os.path.join("logs", fpath), "r", encoding="utf-8") as f:
            entry = json.load(f)
            if "metrics" in entry and "ARSR" in entry["metrics"]:
                run_ids.append(idx)
                arsrs.append(entry["metrics"]["ARSR"])

    if run_ids:
        plt.figure(figsize=(6, 4))
        plt.plot(run_ids, arsrs, marker="o")
        plt.title(f"Trend of ARSR over runs ({mode_name})")
        plt.xlabel("Run ID")
        plt.ylabel("ARSR")
        plt.grid(True)
        if save_path:
            plt.savefig(save_path)
        plt.show()


def print_rich_table(all_results):
    """
    Pretty-print metrics in terminal using rich.
    """
    console = Console()
    table = Table(title="ClarifyCoder-Agent Metrics Summary")
    metrics = list(all_results[0].keys())
    for m in metrics:
        table.add_column(m, justify="center")

    for row in all_results:
        table.add_row(*[str(row[m]) for m in metrics])

    console.print(table)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_prompts", type=int, default=10)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--skip_run", action="store_true",
                        help="Skip running experiments, just aggregate logs")
    parser.add_argument("--answer_mode", choices=["human", "auto"], default="human",
                        help="Answer mode: human (interactive) or auto (LLM)")
    args = parser.parse_args()

    modes = ["baseline", "llm", "hybrid"]

    if not args.skip_run:
        for mode in modes:
            for r in range(1, args.runs + 1):
                run_mode(mode, args.n_prompts, args.seed + r, r, args.answer_mode)

    print("\n=== Metrics Summary ===")
    all_results = []
    for mode in modes:
        m = collect_metrics(mode)
        row = {"Mode": mode}
        row.update(m)
        all_results.append(row)

    # Console outputs
    print_rich_table(all_results)

    # Save results
    export_results(all_results)

    # Plots
    plot_bar_chart(all_results)
    for mode in modes:
        plot_trends(mode, save_path=f"{mode}_trend.png")


if __name__ == "__main__":
    main()
