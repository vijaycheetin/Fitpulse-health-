"""
=============================================================
 FitPulse — Custom Runner (Your Own Dataset)
=============================================================
Runs your analysis pipeline on your own 5-row dataset.

Usage:
    python main.py
=============================================================
"""

import pandas as pd
from analysis import process_full_analysis   # your previous code
import os


def generate_my_data():
    """Creates your personal 5-row dataset."""
    data = {
        "timestamp": [
            "2024-03-01 10:00",
            "2024-03-01 10:05",
            "2024-03-01 10:10",
            "2024-03-01 10:15",
            "2024-03-01 10:20"
        ],
        "heart_rate_bpm": [78, 140, 42, 150, 90],
        "spo2_pct": [98, 96, 92, 95, 97],
        "steps": [30, 60, 20, 100, 10]
    }
    df = pd.DataFrame(data)

    os.makedirs("data", exist_ok=True)
    df.to_csv("data/my_fitness_data.csv", index=False)
    return df


def main():
    print("\n╔══════════════════════════════════════════════╗")
    print("║        FitPulse — Custom Analysis Runner     ║")
    print("╚══════════════════════════════════════════════╝")

    # -------------------------------------------------
    # STEP 1 — Create My Own Small Dataset
    # -------------------------------------------------
    print("\n📦 Creating personal 5-row dataset...")
    df = generate_my_data()
    print("   ✅ Saved: data/my_fitness_data.csv")
    print(df)

    # -------------------------------------------------
    # STEP 2 — Run My Own Analysis Pipeline
    # -------------------------------------------------
    print("\n🔍 Running anomaly detection pipeline...")
    results = process_full_analysis(df)

    os.makedirs("outputs", exist_ok=True)
    results.to_csv("outputs/my_results.csv", index=False)

    print("   ✅ Analysis complete!")
    print("\n----- FINAL RESULTS -----\n")
    print(results)

    # -------------------------------------------------
    # DONE
    # -------------------------------------------------
    print("\n╔══════════════════════════════════════════════╗")
    print("║            ✔ All Done — Outputs Saved        ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  Output File: outputs/my_results.csv         ║")
    print("╚══════════════════════════════════════════════╝\n")


if __name__ == "__main__":
    main()
