"""
dashboard.py
------------
Streamlit leaderboard for ClarifyCoder-Agent experiments.

Usage:
    streamlit run dashboard.py
"""

import os
import json
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

LOG_DIR = "logs"

def load_logs():
    """
    Load metrics JSONs from the most recent timestamped folder under LOG_DIR.
    """
    # Find all subfolders with timestamp names
    subdirs = [os.path.join(LOG_DIR, d) for d in os.listdir(LOG_DIR)
               if os.path.isdir(os.path.join(LOG_DIR, d))]

    if not subdirs:
        return pd.DataFrame()

    # Pick the latest folder by modification time
    latest_dir = max(subdirs, key=os.path.getmtime)

    rows = []
    for fname in os.listdir(latest_dir):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(latest_dir, fname), "r", encoding="utf-8") as f:
                entry = json.load(f)
            if "metrics" in entry:
                row = {"Run": fname}
                row.update(entry["metrics"])
                rows.append(row)
        except Exception as e:
            print(f"Warning: could not read {fname}: {e}")

    return pd.DataFrame(rows) if rows else pd.DataFrame()

def main():
    st.title("📊 ClarifyCoder-Agent Leaderboard")
    st.write("Compare Baseline, LLM, and Hybrid runs interactively.")

    df = load_logs()
    if df.empty:
        st.warning("No logs found. Run compare_experiments.py first.")
        return

    # Mode inference
    df["Mode"] = df["Run"].apply(lambda x: x.split("_")[0])

    # Aggregate
    summary = df.groupby("Mode").mean(numeric_only=True).reset_index()

    # Display summary
    st.subheader("Metrics Summary")
    numeric_cols = summary.select_dtypes(include="number").columns
    st.dataframe(summary.style.format("{:.2f}", subset=numeric_cols))

    # Bar chart
    st.subheader("Side-by-Side Metrics")
    fig, ax = plt.subplots(figsize=(8, 5))
    summary.set_index("Mode").plot(kind="bar", ax=ax)
    plt.ylabel("Score")
    plt.title("Average Metrics by Mode")

    # move legend to the right
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.)

    plt.tight_layout()
    st.pyplot(fig)

    # Trend plots
    st.subheader("Trends over Runs")
    metric_choice = st.selectbox(
        "Select metric", ["CRR", "CSR", "ARSR", "RFR", "USR", "Coverage"])
    fig, ax = plt.subplots(figsize=(8, 4))
    for mode, group in df.groupby("Mode"):
        ax.plot(range(1, len(group) + 1),
                group[metric_choice], marker="o", label=mode)
    ax.set_xlabel("Run ID")
    ax.set_ylabel(metric_choice)
    ax.set_title(f"{metric_choice} Trend Across Runs")
    ax.legend()
    st.pyplot(fig)

    # Raw log inspection
    st.subheader("Inspect Raw Logs")
    run_choice = st.selectbox("Select run file", df["Run"].tolist())
    if run_choice:
        with open(os.path.join(LOG_DIR, run_choice), "r", encoding="utf-8") as f:
            st.json(json.load(f))


if __name__ == "__main__":
    main()
