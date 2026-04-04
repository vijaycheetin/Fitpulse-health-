# my_analysis.py
import pandas as pd
import numpy as np
from prophet import Prophet
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import warnings
warnings.filterwarnings("ignore")

# ---------------------------------------
# RANDOM SAMPLE DATA (5 ROWS)
# ---------------------------------------

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

# --- Constants from Milestone 3 ---
THRESHOLDS = {
    "heart_rate_bpm": {"high": 120, "low": 45, "sleep_high": 90},
    "spo2_pct": {"low": 94},
    "steps": {"sleep_active": 50},
}

# ---------------------------------------------------
#            FULL ANALYSIS PIPELINE
# ---------------------------------------------------

def preprocess_data(df):
    if 'timestamp' in df.columns:
        df = df.rename(columns={'timestamp': 'ds'})

    date_cols = ['ds', 'date', 'time', 'entry_time']
    found_col = next((c for c in date_cols if c in df.columns), None)

    if not found_col:
        return df

    df[found_col] = pd.to_datetime(df[found_col], errors='coerce')
    df = df.dropna(subset=[found_col])
    df = df.sort_values(found_col).reset_index(drop=True)
    return df

def rule_based_detection(df):
    df = df.copy()

    for col in ['heart_rate_bpm', 'heart_rate', 'hr']:
        if col in df.columns:
            df['heart_rate_bpm'] = df[col]
            break

    for col in ['steps', 'step_count']:
        if col in df.columns:
            df['steps'] = df[col]
            break

    for col in ['spo2_pct', 'spo2', 'oxygen']:
        if col in df.columns:
            df['spo2_pct'] = df[col]
            break

    # Default values
    if 'heart_rate_bpm' not in df.columns: df['heart_rate_bpm'] = 70
    if 'steps' not in df.columns: df['steps'] = 0
    if 'spo2_pct' not in df.columns: df['spo2_pct'] = 98

    # Rules
    df["rule_tachycardia"] = (df["heart_rate_bpm"] > THRESHOLDS["heart_rate_bpm"]["high"]).astype(int)
    df["rule_bradycardia"] = (df["heart_rate_bpm"] < THRESHOLDS["heart_rate_bpm"]["low"]).astype(int)
    df["rule_low_spo2"] = (df["spo2_pct"] < THRESHOLDS["spo2_pct"]["low"]).astype(int)

    df["rule_sleep_steps"] = 0

    rule_cols = ["rule_tachycardia", "rule_bradycardia", "rule_low_spo2", "rule_sleep_steps"]
    df["rule_anomaly"] = df[rule_cols].any(axis=1).astype(int)

    return df

def run_prophet_anomaly(df, metric='heart_rate_bpm'):
    if metric not in df.columns or len(df) < 10:
        df['prophet_anomaly'] = 0
        return df

    prophet_df = df[[metric]].copy().reset_index()
    prophet_df.columns = ['ds', 'y']
    prophet_df['ds'] = pd.to_datetime(prophet_df['ds'])
    prophet_df = prophet_df.dropna()

    try:
        m = Prophet(daily_seasonality=True).fit(prophet_df)
        future = m.make_future_dataframe(periods=0)
        forecast = m.predict(future)

        forecast = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
        df_temp = prophet_df.merge(forecast, on='ds')
        df_temp['is_anomaly'] = ((df_temp['y'] > df_temp['yhat_upper']) |
                                 (df_temp['y'] < df_temp['yhat_lower'])).astype(int)

        df['prophet_anomaly'] = 0
        df.loc[df_temp['ds'].values, 'prophet_anomaly'] = df_temp['is_anomaly'].values
    except:
        df['prophet_anomaly'] = 0

    return df

def compute_severity(df):
    df = df.copy()

    if 'prophet_anomaly' not in df.columns:
        df['prophet_anomaly'] = 0

    df["anomaly_score"] = df[["rule_anomaly", "prophet_anomaly"]].sum(axis=1)

    def severity(x):
        if x == 0: return "Normal"
        elif x == 1: return "Warning"
        else: return "Critical"

    df["severity"] = df["anomaly_score"].apply(severity)
    return df

def process_full_analysis(df):
    df = preprocess_data(df)
    df = rule_based_detection(df)
    df = run_prophet_anomaly(df, 'heart_rate_bpm')
    df = compute_severity(df)
    return df

# ---------------------------------------
# RUN FULL PIPELINE ON RANDOM DATA
# ---------------------------------------

result = process_full_analysis(df)
print("\n----- FINAL OUTPUT -----\n")
print(result)
