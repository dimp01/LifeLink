"""
ML Pipeline for LifeLink AI
Processes the Organ Donation survey CSV to:
1. Forecast organ demand by region
2. Calculate ODII (Organ Demand Instability Index)
3. Generate SHAP explanations
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
import shap
from datetime import datetime
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score
from xgboost import XGBClassifier

# Paths
BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR.parent / "Organ Donation.csv"
MODEL_DIR = BASE_DIR / "ml_models"
MODEL_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# DATA LOADING & PREPROCESSING
# ─────────────────────────────────────────────

def load_and_preprocess():
    df = pd.read_csv(DATA_PATH)

    # Target column (already 0/1 from previous cleaning steps)
    target_col_name = "are_you_willing_to_donate_organs"
    df["willing_to_donate"] = df[target_col_name].astype(int)

    encoders = {}

    # Identify object columns that need encoding
    # Exclude columns that are already target or new index columns
    exclude_cols = [target_col_name, "willing_to_donate", "knowledge_index", "fear_index"]
    object_cols_for_encoding = [
        col for col in df.select_dtypes("object").columns
        if col not in exclude_cols
    ]

    for col in object_cols_for_encoding:
        le = LabelEncoder()
        # Use fillna("Unknown") to handle potential NaNs if they were missed or reintroduced
        df[col + "_enc"] = le.fit_transform(df[col].fillna("Unknown").astype(str))
        encoders[col] = le

    # Knowledge score (already computed as 'knowledge_index')
    df["knowledge_score"] = df["knowledge_index"]

    # Family support score (should be numeric already)
    df["family_support"] = df["how_supportive_are_your_family_and_friends_towards_organ_donation"].astype(float)

    return df, encoders

# Define FEATURE_COLS based on the output of this new function
FEATURE_COLS = [
    "age", # Already numerical from previous steps
    "gender_enc",
    "resident_type_enc",
    "education_enc",
    "occupation_enc",
    "annual_family_income_enc",
    "family_type_enc",
    "marital_status_enc",
    "religion_enc",
    "city_enc",
    "from_where_did_you_learn_about_organ_donation_enc",
    "if_you_havent_registered_yet_what_are_the_reasons_behind_your_decision_enc",
    "knowledge_score",
    "family_support",
    "fear_index"
]

def get_feature_matrix(df):
    available = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available].fillna(0)
    y = df["willing_to_donate"]
    return X, y, available


# ─────────────────────────────────────────────
# MODEL 1: WILLINGNESS / DEMAND PREDICTION
# ─────────────────────────────────────────────

def train_demand_model(df):
    X, y, features = get_feature_matrix(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss",
        use_label_encoder=False,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    joblib.dump(model, MODEL_DIR / "demand_model.pkl")
    joblib.dump(features, MODEL_DIR / "feature_names.pkl")

    metrics = {
        "model": "LifeLink AI",
        "accuracy": float(acc),
        "mae": mae,
        "rmse": rmse,
        "r2_score": r2,
        "training_samples": len(X_train),
        "features": features,
    }
    with open(MODEL_DIR / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return model, metrics, features


# ─────────────────────────────────────────────
# MODEL 2: ORGAN DEMAND INSTABILITY INDEX (ODII)
# ─────────────────────────────────────────────

def compute_odii(df):
    """
    ODII = (Projected Demand − Available Supply) / Registered Donors
    We approximate:
    - Projected Demand = number of people indicating they need info / awareness per region
    - Available Supply = number already registered as donors per region
    - Registered Donors = total willing donors per region
    """
    odii_data = []

    if "city" not in df.columns:
        return odii_data

    organs = [
        "Kidney", "Liver", "Heart", "Lungs", "Eyes", "Cornea",
        "Pancreas", "Intestine", "Skin", "Bone Marrow"
    ]

    for region in df["city"].unique():
        reg_df = df[df["city"] == region]
        total = len(reg_df)
        if total == 0:
            continue

        willing = int(reg_df["willing_to_donate"].sum()) if "willing_to_donate" in reg_df.columns else 0
        registered = int(reg_df.get("Have you registered as  an organ donor with the relevant authorities or a donor registry?", pd.Series()).eq("Yes").sum())
        knowledge_avg = float(reg_df.get("knowledge_score", pd.Series([0])).mean())

        for organ in organs:
            # Simulated demand based on awareness gap and region size
            awareness_gap = 1.0 - (knowledge_avg / 5.0)
            projected_demand = round(total * awareness_gap * 0.3, 2)
            available_supply = max(registered * 0.1, 1)
            registered_donors_count = max(willing, 1)

            odii = round((projected_demand - available_supply) / registered_donors_count, 4)
            confidence = round(min(0.95, 0.5 + knowledge_avg / 10), 2)

            odii_data.append({
                "region": str(region),
                "organ_type": organ,
                "projected_demand": projected_demand,
                "available_supply": available_supply,
                "registered_donors": registered_donors_count,
                "instability_index": odii,
                "confidence_score": confidence,
            })

    with open(MODEL_DIR / "odii.json", "w") as f:
        json.dump(odii_data, f, indent=2)

    return odii_data


# ─────────────────────────────────────────────
# MODEL 3: SHAP EXPLANATIONS
# ─────────────────────────────────────────────

def generate_shap_explanations(model, df, features):
    X, y, _ = get_feature_matrix(df)
    X_sample = X.head(50)

    explainer = shap.Explainer(model, X_sample)
    shap_values = explainer(X_sample)

    mean_shap = np.abs(shap_values.values).mean(axis=0)
    feature_importance = {
        feat: round(float(val), 4)
        for feat, val in zip(features, mean_shap)
    }
    feature_importance = dict(
        sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    )

    shap_output = {
        "feature_importance": feature_importance,
        "top_features": list(feature_importance.keys())[:5],
        "explanation": "Features ranked by mean absolute SHAP value. Higher = more impact on prediction.",
        "sample_count": len(X_sample),
    }

    with open(MODEL_DIR / "shap_results.json", "w") as f:
        json.dump(shap_output, f, indent=2)

    return shap_output


# ─────────────────────────────────────────────
# REGIONAL DEMAND FORECAST (3–6 month)
# ─────────────────────────────────────────────

def get_regional_forecast(df):
    if "city" not in df.columns:
        return []

    forecast = []
    regions = df["city"].value_counts().head(20)

    for region, count in regions.items():
        reg_df = df[df["city"] == region]
        willing = int(reg_df.get("willing_to_donate", pd.Series([0])).sum())
        total = len(reg_df)
        willingness_rate = willing / total if total > 0 else 0

        # Simulate 6-month projection
        monthly_projections = []
        base_demand = total * 0.05
        for month in range(1, 7):
            projected = round(base_demand * (1 + 0.02 * month) * (1 - willingness_rate * 0.5), 2)
            monthly_projections.append({
                "month": month,
                "projected_demand": projected,
            })

        forecast.append({
            "region": str(region),
            "total_surveyed": total,
            "willing_donors": willing,
            "willingness_rate": round(willingness_rate, 3),
            "monthly_projections": monthly_projections,
        })

    with open(MODEL_DIR / "forecast.json", "w") as f:
        json.dump(forecast, f, indent=2)

    return forecast


# ─────────────────────────────────────────────
# MAIN TRAINING ENTRY POINT
# ─────────────────────────────────────────────

def run_full_pipeline():
    print("Loading and preprocessing data...")
    df, encoders = load_and_preprocess()

    print(f"Dataset shape: {df.shape}")
    print("Training LifeLink AI demand prediction model...")
    model, metrics, features = train_demand_model(df)

    print("Computing ODII...")
    odii = compute_odii(df)

    print("Generating SHAP explanations...")
    shap_output = generate_shap_explanations(model, df, features)

    print("Computing regional forecasts...")
    forecast = get_regional_forecast(df)

    print("Computing fairness & bias metrics...")
    fairness = compute_fairness(model, df, features)

    print("Computing calibration...")
    calibration = compute_calibration(model, df)

    print("Recording model version...")
    version = record_model_version(metrics)

    print("Pipeline complete.")
    return {
        "metrics": metrics,
        "odii_samples": odii[:5],
        "shap_summary": shap_output,
        "forecast_regions": len(forecast),
        "fairness_groups": len(fairness.get("by_religion", [])),
        "calibration_error": calibration.get("calibration_error"),
        "model_version": version.get("version_tag"),
    }


def load_saved_results():
    """Load cached results without retraining."""
    result = {}
    for fname, key in [
        ("metrics.json", "metrics"),
        ("odii.json", "odii"),
        ("shap_results.json", "shap"),
        ("forecast.json", "forecast"),
        ("fairness.json", "fairness"),
        ("calibration.json", "calibration"),
        ("model_versions.json", "model_versions"),
    ]:
        path = MODEL_DIR / fname
        if path.exists():
            with open(path) as f:
                result[key] = json.load(f)
    return result


# ─────────────────────────────────────────────
# FAIRNESS & BIAS EVALUATION
# ─────────────────────────────────────────────

def compute_fairness(model, df, features):
    """
    Compute fairness metrics across demographic groups.
    Assesses prediction distribution by religion, age group, and region.
    """
    X, y, feat_cols = get_feature_matrix(df)
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1]
    df = df.copy()
    df["_pred"] = y_pred
    df["_proba"] = y_proba
    df["_actual"] = y.values

    fairness = {}

    # 1. By Religion
    if "religion" in df.columns:
        religion_stats = []
        for grp, gdf in df.groupby("religion"):
            if len(gdf) < 5:
                continue
            tp = int(((gdf["_pred"] == 1) & (gdf["_actual"] == 1)).sum())
            fp = int(((gdf["_pred"] == 1) & (gdf["_actual"] == 0)).sum())
            fn = int(((gdf["_pred"] == 0) & (gdf["_actual"] == 1)).sum())
            tn = int(((gdf["_pred"] == 0) & (gdf["_actual"] == 0)).sum())
            total = len(gdf)
            positive_rate = round(float(gdf["_pred"].mean()), 4)
            avg_proba = round(float(gdf["_proba"].mean()), 4)
            fpr = round(fp / (fp + tn) if (fp + tn) > 0 else 0.0, 4)
            religion_stats.append({
                "group": str(grp),
                "count": total,
                "positive_prediction_rate": positive_rate,
                "avg_confidence": avg_proba,
                "false_positive_rate": fpr,
                "actual_positive_rate": round(float(gdf["_actual"].mean()), 4),
            })
        fairness["by_religion"] = sorted(religion_stats, key=lambda x: x["count"], reverse=True)

    # 2. By Age group
    if "age" in df.columns:
        age_stats = []
        for grp, gdf in df.groupby("age"):
            if len(gdf) < 5:
                continue
            age_stats.append({
                "group": str(grp),
                "count": len(gdf),
                "positive_prediction_rate": round(float(gdf["_pred"].mean()), 4),
                "actual_positive_rate": round(float(gdf["_actual"].mean()), 4),
                "avg_confidence": round(float(gdf["_proba"].mean()), 4),
            })
        fairness["by_age"] = sorted(age_stats, key=lambda x: x["count"], reverse=True)

    # 3. By Region
    if "city" in df.columns:
        region_stats = []
        for grp, gdf in df.groupby("city"):
            if len(gdf) < 5:
                continue
            region_stats.append({
                "group": str(grp),
                "count": len(gdf),
                "positive_prediction_rate": round(float(gdf["_pred"].mean()), 4),
                "actual_positive_rate": round(float(gdf["_actual"].mean()), 4),
                "demand_variance": round(float(gdf["_proba"].var()), 4),
            })
        fairness["by_region"] = sorted(region_stats, key=lambda x: x["count"], reverse=True)[:20]

    # 4. Feature dominance
    importances = {}
    if hasattr(model, "feature_importances_"):
        for feat, imp in zip(feat_cols, model.feature_importances_):
            importances[feat] = round(float(imp), 4)
    fairness["feature_dominance"] = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))

    with open(MODEL_DIR / "fairness.json", "w") as f:
        json.dump(fairness, f, indent=2)

    return fairness


# ─────────────────────────────────────────────
# CALIBRATION
# ─────────────────────────────────────────────

def compute_calibration(model, df):
    """Compute calibration curve and reliability score."""
    from sklearn.calibration import calibration_curve

    X, y, _ = get_feature_matrix(df)
    y_proba = model.predict_proba(X)[:, 1]

    fraction_of_positives, mean_predicted_value = calibration_curve(
        y, y_proba, n_bins=10, strategy="uniform"
    )

    calibration_data = {
        "mean_predicted_probabilities": [round(float(v), 4) for v in mean_predicted_value],
        "fraction_of_positives": [round(float(v), 4) for v in fraction_of_positives],
        "interpretation": "Points near the diagonal indicate a well-calibrated model.",
    }

    # Reliability score: 1 - mean absolute calibration error
    calibration_error = float(np.mean(np.abs(fraction_of_positives - mean_predicted_value)))
    calibration_data["calibration_error"] = round(calibration_error, 4)
    calibration_data["reliability_score"] = round(1.0 - calibration_error, 4)

    # Overall confidence stats
    calibration_data["confidence_stats"] = {
        "mean": round(float(y_proba.mean()), 4),
        "std": round(float(y_proba.std()), 4),
        "min": round(float(y_proba.min()), 4),
        "max": round(float(y_proba.max()), 4),
        "high_confidence_pct": round(float((y_proba > 0.8).mean()), 4),
        "low_confidence_pct": round(float((y_proba < 0.5).mean()), 4),
    }

    with open(MODEL_DIR / "calibration.json", "w") as f:
        json.dump(calibration_data, f, indent=2)

    return calibration_data


# ─────────────────────────────────────────────
# MODEL VERSIONING
# ─────────────────────────────────────────────

def record_model_version(metrics: dict) -> dict:
    """Append a new model version entry to the versions log file."""
    import hashlib
    versions_path = MODEL_DIR / "model_versions.json"
    versions = []
    if versions_path.exists():
        with open(versions_path) as f:
            versions = json.load(f)

    # Compute dataset hash
    dataset_hash = ""
    try:
        with open(BASE_DIR.parent / "Organ Donation.csv", "rb") as f:
            dataset_hash = hashlib.md5(f.read()).hexdigest()
    except Exception:
        pass

    version_entry = {
        "id": len(versions) + 1,
        "training_date": datetime.utcnow().isoformat(),
        "accuracy": metrics.get("accuracy"),
        "hyperparameters": {
            "model": metrics.get("model"),
            "n_estimators": 100,
            "max_depth": 4,
            "learning_rate": 0.1,
        },
        "dataset_hash": dataset_hash,
        "notes": f"Auto-trained run #{len(versions) + 1}",
        "metrics": {
            "mae": metrics.get("mae"),
            "rmse": metrics.get("rmse"),
            "r2_score": metrics.get("r2_score"),
        },
        "version_tag": f"v{len(versions) + 1}.0",
    }
    versions.append(version_entry)

    with open(versions_path, "w") as f:
        json.dump(versions, f, indent=2)

    return version_entry


if __name__ == "__main__":
    results = run_full_pipeline()
    print(json.dumps(results, indent=2, default=str))
