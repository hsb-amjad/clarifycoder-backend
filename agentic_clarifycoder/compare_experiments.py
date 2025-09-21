"""
compare_experiments.py
----------------------
Experiment runner for ClarifyCoder-Agent.

Runs baseline-only, LLM-only, and hybrid settings on the same prompts.
Logs results to JSON files and prints side-by-side metrics.
Generates 4 professional plots for papers:
  • ARSR trend plots (one per mode: baseline, llm, hybrid)
  • A single grouped bar chart comparing all metrics across modes

Usage:
    python compare_experiments.py --n_prompts 10 --runs 3 --answer_mode auto
    python compare_experiments.py --n_prompts 10 --runs 3 --answer_mode human
    -> run from root agentic_clarifycoder
"""

import argparse
import json
import os
import subprocess
from statistics import mean, stdev
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
import pandas as pd
from datetime import datetime

# 🔧 Global matplotlib style for research-paper-ready plots
plt.rcParams.update({
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "font.size": 14,
    "axes.labelsize": 14,
    "axes.titlesize": 15,
    "legend.fontsize": 12,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--"
})

DEMO_MODULE = "agentic_clarifycoder.core.demo.demo"


def run_mode(mode_name: str, n_prompts: int, seed: int, run_id: int, answer_mode: str, log_dir: str):
    """Run ClarifyCoder-Agent in a given mode via demo.py and save logs."""
    if mode_name == "baseline":
        clarify, code, evalm, refine = "baseline", "baseline", "baseline", "baseline"
    elif mode_name == "llm":
        clarify, code, evalm, refine = "llm", "llm", "llm", "llm"
    elif mode_name == "hybrid":
        clarify, code, evalm, refine = "llm", "baseline", "baseline", "llm"
    else:
        raise ValueError(f"Unknown mode {mode_name}")

    os.makedirs(log_dir, exist_ok=True)
    out_file = os.path.join(log_dir, f"{mode_name}_run{run_id}.json")

    print(f"\n=== Running {mode_name.upper()} (run {run_id}) ===")

    cmd = [
        "python", "-m", DEMO_MODULE,
        f"--clarify_mode={clarify}",
        f"--code_mode={code}",
        f"--eval_mode={evalm}",
        f"--refine_mode={refine}",
        f"--answer_mode={answer_mode}",
        "--num_prompts", str(n_prompts),
        "--seed", str(seed),
        "--log_file", out_file
    ]

    subprocess.run(cmd, check=True)


def collect_metrics(mode_name: str, log_dir: str):
    """Collect metrics from all runs for a given mode."""
    files = [f for f in os.listdir(log_dir) if f.startswith(mode_name)]
    metrics = {
        "CRR": [], "CSR": [], "ARSR": [], "RFR": [], "USR": [], "Coverage": []
    }

    for fpath in files:
        try:
            with open(os.path.join(log_dir, fpath), "r", encoding="utf-8") as f:
                entry = json.load(f)
                if "metrics" in entry:
                    m = entry["metrics"]
                    for k in metrics.keys():
                        if k in m:
                            metrics[k].append(m[k])
        except Exception as e:
            print(f"Warning: could not read {fpath}: {e}")

    return {
        k: (round(mean(v), 2), round(stdev(v), 2) if len(v) > 1 else 0)
        for k, v in metrics.items()
    }


def export_results(all_results, csv_file="results.csv", excel_file="results.xlsx"):
    """Export metrics to CSV and Excel."""
    df = pd.DataFrame(all_results).set_index("Mode")
    df.to_csv(csv_file)
    df.to_excel(excel_file)
    print(f"\n[+] Results exported to {csv_file} and {excel_file}")


def plot_bar_chart(all_results, save_path="plots/metrics_bar.png"):
    """One grouped bar chart comparing all metrics across modes."""
    df = pd.DataFrame(all_results).set_index("Mode")

    # Extract mean values only
    means = df.applymap(lambda x: x[0])

    ax = means.plot.bar(
        figsize=(10, 6),
        rot=0,
        color=["#4C72B0", "#55A868", "#C44E52",
               "#8172B2", "#CCB974", "#64B5CD"]
    )

    # Removed title
    ax.set_ylabel("Score")
    ax.set_xlabel("Mode")
    ax.legend(title="Metric", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"[+] Saved {save_path}")


def plot_trend_arsr(mode_name, log_dir, save_path=None):
    """Plot ARSR trend over runs for a single mode."""
    files = sorted([f for f in os.listdir(log_dir) if f.startswith(mode_name)])
    if not files:
        return

    run_ids, arsrs = [], []
    for idx, fpath in enumerate(files, 1):
        with open(os.path.join(log_dir, fpath), "r", encoding="utf-8") as f:
            entry = json.load(f)
            if "metrics" in entry:
                m = entry["metrics"]
                if "ARSR" in m:
                    try:
                        # Handle dict, tuple, or float
                        val = m["ARSR"]
                        if isinstance(val, (list, tuple)):
                            val = val[0]  # take mean
                        val = float(val)
                        run_ids.append(idx)
                        arsrs.append(val)
                    except Exception as e:
                        print(f"Warning: could not parse ARSR in {fpath}: {e}")

    if run_ids:
        plt.figure(figsize=(6, 4))
        plt.plot(run_ids, arsrs, marker="o", linewidth=2,
                 markersize=6, color="#4C72B0")
        # Removed title
        plt.xlabel("Run ID")
        plt.ylabel("ARSR")
        plt.ylim(0, 100)
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path)
        plt.close()
        print(f"[+] Saved {save_path}")


def print_rich_table(all_results):
    """Pretty-print metrics in terminal using rich."""
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

    # Create timestamped log directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join("logs", timestamp)
    os.makedirs(log_dir, exist_ok=True)

    if not args.skip_run:
        for mode in modes:
            for r in range(1, args.runs + 1):
                run_mode(mode, args.n_prompts, args.seed +
                         r, r, args.answer_mode, log_dir)

    print("\n=== Metrics Summary ===")
    all_results = []
    for mode in modes:
        m = collect_metrics(mode, log_dir)
        row = {"Mode": mode}
        row.update(m)
        all_results.append(row)

    # Console outputs
    print_rich_table(all_results)

    # Save results
    export_results(all_results)

    # Plots
    os.makedirs("plots", exist_ok=True)
    plot_bar_chart(all_results, save_path="plots/metrics_bar.png")
    for mode in modes:
        plot_trend_arsr(mode, log_dir, save_path=f"plots/{mode}_trend.png")


if __name__ == "__main__":
    main()
