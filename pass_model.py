
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

<<<<<<< HEAD
DATA_FILES = ["Data/merged_pass_model_data_2020.csv"]
OUTPUT_DIR = Path("models")
OUTPUT_DIR.mkdir(exist_ok=True)

TARGETS = [
    "receiver_position",
    "route",
    "offense_personnel",
    "offense_formation",
    "pass_length",
    "pass_location",
]

RANDOM_STATE = 42
TEST_SIZE = 0.2
MIN_SAMPLES_PER_CLASS = 15


def load_first_existing(files: List[str]) -> pd.DataFrame:
    for f in files:
        p = Path(f)
        if p.exists():
            print(f"Loading data from {f}")
            return pd.read_csv(p, low_memory=False)

def add_football_intelligence_features(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    #basic safety for missing columns
    def safe_get(col, default=0):
        return df2[col] if col in df2.columns else pd.Series([default]*len(df2))

    df2["yardline_100"] = safe_get("yardline_100", 50)
    df2["goal_to_go"] = safe_get("goal_to_go", 0)
    df2["down"] = safe_get("down", 1)
    df2["ydstogo"] = safe_get("ydstogo", 10)
    df2["quarter_seconds_remaining"] = safe_get("quarter_seconds_remaining", 900)
    df2["qtr"] = safe_get("qtr", 1)
    df2["score_differential"] = safe_get("score_differential", 0)
    df2["shotgun"] = safe_get("shotgun", 0)
    df2["play_type"] = safe_get("play_type", "pass")

    #Field position
    df2["is_redzone"] = (df2["yardline_100"] <= 20).astype(int)
    df2["is_goal_to_go"] = df2["goal_to_go"].fillna(0).astype(int)
    df2["is_backed_up"] = (df2["yardline_100"] >= 80).astype(int)

    #Down and distance
    df2["is_third_long"] = ((df2["down"] == 3) & (df2["ydstogo"] >= 7)).astype(int)
    df2["is_third_short"] = ((df2["down"] == 3) & (df2["ydstogo"] <= 3)).astype(int)
    df2["is_second_long"] = ((df2["down"] == 2) & (df2["ydstogo"] >= 8)).astype(int)
    df2["is_first_down"] = (df2["down"] == 1).astype(int)

    #Game situation
    df2["is_two_minute"] = (df2["quarter_seconds_remaining"] <= 120).astype(int)
    df2["is_close_game_late"] = ((df2["qtr"] == 4) & (df2["score_differential"].abs() <= 8)).astype(int)
    df2["is_blowout"] = (df2["score_differential"].abs() >= 21).astype(int)

    #Score context
    df2["is_leading"] = (df2["score_differential"] > 0).astype(int)
    df2["is_trailing"] = (df2["score_differential"] < 0).astype(int)
    df2["score_margin_abs"] = df2["score_differential"].abs()

    #Formation flags
    if "offense_formation" in df2.columns:
        df2["is_empty"] = df2["offense_formation"].str.contains("EMPTY", na=False).astype(int)
        df2["is_heavy"] = df2["offense_formation"].str.contains("JUMBO|HEAVY", na=False).astype(int)
        df2["is_shotgun"] = df2["offense_formation"].str.contains("SHOTGUN", na=False).astype(int)
    else:
        if "shotgun" in df2.columns:
            df2["is_shotgun"] = df2["shotgun"].fillna(0).astype(int)

    #Field segments
    if "yardline_100" in df2.columns:
        df2["field_position"] = pd.cut(
            df2["yardline_100"], bins=[0, 20, 40, 60, 80, 100],
            labels=["redzone", "offensive", "midfield", "defensive", "backed_up"]
        )
    else:
        df2["field_position"] = "midfield"

    return df2

def build_global_feature_set(df: pd.DataFrame) -> List[str]:
    """Construct a compact but informative global feature list."""
    core = [
        "down", "ydstogo", "yardline_100", "goal_to_go", "qtr",
        "quarter_seconds_remaining", "game_seconds_remaining", "score_differential",
        "posteam_timeouts_remaining", "defteam_timeouts_remaining",
        "shotgun", "no_huddle", "posteam", "defteam"
    ]
    derived = [
        "is_redzone", "is_goal_to_go", "is_backed_up",
        "is_third_long", "is_third_short", "is_second_long", "is_first_down",
        "is_two_minute", "is_close_game_late", "is_blowout",
        "is_leading", "is_trailing", "score_margin_abs", "is_shotgun",
        "is_empty", "is_heavy", "field_position"
=======

def simplify_coverage(x: str) -> str:
    if pd.isna(x):
        return "Unknown"

    x = x.upper()

    if "0" in x:
        return "C0"
    if "1" in x:
        return "C1"
    if "2" in x:
        return "C2"
    if "3" in x:
        return "C3"
    if "4" in x or "QUARTER" in x:
        return "C4"

    return "Other"


def train_pass_model():
    """
    Train a pass success prediction model using pre-snap + participation + design features.
    """

    # ---------------------------
    # 1. Load ORIGINAL PBP data
    # ---------------------------
    # ---------------------------
    # 1. Load ORIGINAL PBP data
    # ---------------------------
    pbp_files = [
        pd.read_csv("Data/pbp_2024_0.csv", low_memory=False),
        pd.read_csv("Data/pbp_2024_1.csv", low_memory=False),
        pd.read_csv("Data/pbp_2023_0.csv", low_memory=False),
        pd.read_csv("Data/pbp_2023_1.csv", low_memory=False),
        pd.read_csv("Data/pbp_2022_0.csv", low_memory=False),
        pd.read_csv("Data/pbp_2022_1.csv", low_memory=False),
        pd.read_csv("Data/pbp_2021_0.csv", low_memory=False),
        pd.read_csv("Data/pbp_2021_1.csv", low_memory=False),
        pd.read_csv("Data/pbp_2020_0.csv", low_memory=False),
        pd.read_csv("Data/pbp_2020_1.csv", low_memory=False),
    ]

    df_pbp: pd.DataFrame = pd.concat(pbp_files, ignore_index=True)

    # ---------------------------
    # 1a. Merge participation coverage (old_game_id + play_id)
    # ---------------------------
    part_files = [
        pd.read_csv("Data/pbp_participation_2024.csv", low_memory=False),
        pd.read_csv("Data/pbp_participation_2023.csv", low_memory=False),
        pd.read_csv("Data/pbp_participation_2022.csv", low_memory=False),
        pd.read_csv("Data/pbp_participation_2021.csv", low_memory=False),
        pd.read_csv("Data/pbp_participation_2020.csv", low_memory=False),
    ]

    df_part: pd.DataFrame = pd.concat(part_files, ignore_index=True)

    df_pbp["old_game_id"] = df_pbp["old_game_id"].astype(str)
    df_part["old_game_id"] = df_part["old_game_id"].astype(str)
    df_pbp["play_id"] = df_pbp["play_id"].astype(str)
    df_part["play_id"] = df_part["play_id"].astype(str)

    df_part_small: pd.DataFrame = df_part[
        ["old_game_id", "play_id", "defense_coverage_type"]
    ]

    df: pd.DataFrame = df_pbp.merge(
        df_part_small,
        on=["old_game_id", "play_id"],
        how="left",
    )

    # ---------------------------
    # 1b. Merge EXTRA design features from merged_pass_model_data_*.csv
    # ---------------------------
    """
    extra_files = [
        pd.read_csv("Data/merged_pass_model_data_2020.csv", low_memory=False),
        pd.read_csv("Data/merged_pass_model_data_2021.csv", low_memory=False),
        pd.read_csv("Data/merged_pass_model_data_2022.csv", low_memory=False),
        pd.read_csv("Data/merged_pass_model_data_2023.csv", low_memory=False),
        pd.read_csv("Data/merged_pass_model_data_2024.csv", low_memory=False),
    ]

    df_extra: pd.DataFrame = pd.concat(extra_files, ignore_index=True)

    # merged files: game id is nflverse_game_id (per your header)
    df_extra["nflverse_game_id"] = df_extra["nflverse_game_id"].astype(str)
    df_extra["play_id"] = df_extra["play_id"].astype(str)

    # extra columns we care about
    extra_cols = [
        col
        for col in [
            "route",
            "season",
            "receiver_position",
            "offense_formation",
            "offense_personnel",
        ]
        if col in df_extra.columns
    ]

    df_extra_small: pd.DataFrame = df_extra[
        ["nflverse_game_id", "play_id"] + extra_cols
    ]

    # need nflverse_game_id in base df as well
    if "nflverse_game_id" not in df.columns:
        raise KeyError("Expected 'nflverse_game_id' in base PBP dataframe.")
    

    df["nflverse_game_id"] = df["nflverse_game_id"].astype(str)
    df["play_id"] = df["play_id"].astype(str)

    df = df.merge(
        df_extra_small,
        left_on=["nflverse_game_id", "play_id"],
        right_on=["nflverse_game_id", "play_id"],
        how="left",
        validate="m:1",
    ) 
    """

    # ---------------------------
    # 2. Filter to pass plays
    # ---------------------------
    df_pass: pd.DataFrame = df[df["play_type"] == "pass"].copy()
    if df_pass.empty:
        print("No pass plays found in the dataset.")
        return None

    # ---------------------------
    # 2b. Coverage simplification
    # ---------------------------
    if "defense_coverage_type" in df_pass.columns:
        df_pass["coverage_simple"] = df_pass["defense_coverage_type"].apply(
            simplify_coverage
        )
        df_pass = pd.get_dummies(df_pass, columns=["coverage_simple"], drop_first=True)
    else:
        print("WARNING: defense_coverage_type not found; no coverage features used.")

    # ---------------------------
    # 3. Label construction
    # ---------------------------
    is_first_down = (df_pass["yards_gained"] >= df_pass["ydstogo"]) & (
        df_pass["yards_gained"].notna()
    )
    is_touchdown = df_pass["touchdown"] == 1

    df_pass["pass_success"] = (is_first_down | is_touchdown).astype(int)

    # ---------------------------
    # 4. Team category encoding
    # ---------------------------
    df_pass = pd.get_dummies(df_pass, columns=["posteam", "defteam"], drop_first=True)

    # ---------------------------
    # 5. Pre-snap boolean indicators
    # ---------------------------
    fill_cols = ["shotgun", "no_huddle", "qb_dropback"]
    fill_cols = [c for c in fill_cols if c in df_pass.columns]

    df_pass[fill_cols] = df_pass[fill_cols].fillna(0)

    # ---------------------------
    # 6. Pre-snap situational features
    # ---------------------------
    pre_snap_info = [
        "down",
        "ydstogo",
        "yardline_100",
        "goal_to_go",
        "qtr",
        "quarter_seconds_remaining",
        "half_seconds_remaining",
        "game_seconds_remaining",
        "score_differential",
        "posteam_timeouts_remaining",
        "defteam_timeouts_remaining",
        "shotgun",
        "no_huddle",
>>>>>>> 4c11420dad78a842e52daef2ca70d8f6cde7cfc1
    ]
    #include a few contextual cols if present
    context = ["temp", "wind", "roof", "surface"]
    possible = core + derived + context
    available = [c for c in possible if c in df.columns]
    print(f"Global feature set contains {len(available)} available columns")
    return available

<<<<<<< HEAD
def global_encode(df: pd.DataFrame, features: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """Create a single encoded feature matrix used by all targets."""
    X = df[features].copy()
    #fill numeric na with median, categorical with 'NA'
    for col in X.columns:
        if X[col].dtype.kind in "biufc":
            X[col] = X[col].fillna(X[col].median())
        else:
            #Convert categorical columns to plain string dtype first, then fill NAs
            X[col] = X[col].astype("string").fillna("NA")

    #one-hot encode categoricals via pd.get_dummies (drop_first to keep smaller)
    X_encoded = pd.get_dummies(X, drop_first=True)
    feature_cols = X_encoded.columns.tolist()
    print(f"Encoded global feature matrix with {len(feature_cols)} columns")
    return X_encoded, feature_cols

def filter_rare_classes_simple(y: pd.Series, min_samples: int = MIN_SAMPLES_PER_CLASS) -> pd.Series:
    """Combine very rare classes into 'OTHER' or drop if too few samples."""
    counts = y.value_counts()
    rare = counts[counts < min_samples].index
    if len(rare) == 0:
        return y
    y2 = y.copy().astype(str)
    y2[y2.isin(rare)] = "OTHER"
    #if OTHER itself is too small, remove those rows in caller
    return y2

def prepare_for_target(df: pd.DataFrame, X_global: pd.DataFrame, target: str) -> Tuple[pd.DataFrame, pd.Series]:
    if target not in df.columns:
        raise KeyError(target)
    mask = df[target].notna()
    if mask.sum() == 0:
        raise ValueError(f"No rows for target {target}")
    X = X_global.loc[mask].copy()
    y = df.loc[mask, target].copy().astype(str)
    #basic leakage removal (remove target-like columns)
    possible_leaks = ["air_yards", "yards_after_catch", "yards_gained", "epa", "complete_pass"]
    for leak in possible_leaks:
        if leak in X.columns:
            X = X.drop(columns=[leak], errors='ignore')
    #handle rare classes
    y = filter_rare_classes_simple(y)
    #drop rows where target became OTHER but still too rare
    counts = y.value_counts()
    if (counts < MIN_SAMPLES_PER_CLASS).any():
        #drop undersized classes
        keep = y.isin(counts[counts >= MIN_SAMPLES_PER_CLASS].index)
        X = X.loc[keep]
        y = y.loc[keep]
    return X, y

def train_target_model(X: pd.DataFrame, y: pd.Series, target: str) -> Dict[str, Any]:
    print(f"\n ---Training target: {target}")
    print(f"Samples: {len(y)} | Classes: {len(y.unique())}")
    if len(y) < 50 or y.nunique() < 2:
        print(f"Skipping {target}: insufficient data")
        return {}
    #train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    #choose RandomForest (robust for categorical-heavy data)
    clf = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    start = time.time()
    clf.fit(X_train, y_train)
    elapsed = time.time() - start
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy ({target}): {acc:.3f} | Train time: {elapsed:.1f}s")
    #limited classification report for small-class targets
    try:
        labels = np.union1d(y_test.unique(), y_pred)
        print(classification_report(y_test, y_pred, labels=labels, zero_division=0))
    except Exception:
        pass
    return {
        "model": clf,
        "accuracy": float(acc),
        "train_time_s": elapsed,
        "classes": clf.classes_.tolist() if hasattr(clf, "classes_") else [],
    }

def train_all_targets(df: pd.DataFrame, targets: List[str]) -> Dict[str, Dict[str, Any]]:
    models_info: Dict[str, Dict[str, Any]] = {}
    features = build_global_feature_set(df)
    if not features:
        print("No features available.")
        return models_info
    X_global, feature_cols = global_encode(df, features)
    #keep the index aligned with df for slicing per-target
    X_global.index = df.index

    for target in targets:
        if target not in df.columns:
            print(f"Skipping {target}: column missing")
            continue
        try:
            X, y = prepare_for_target(df, X_global, target)
            if X.empty or y.nunique() < 2:
                print(f"Skipping {target}: insufficient cleaned data")
                continue
            info = train_target_model(X, y, target)
            if not info:
                continue
            models_info[target] = info
            #save model and metadata
            out_path = OUTPUT_DIR / f"pass_model_{target}.joblib"
            joblib.dump(
                {
                    "model": info["model"],
                    "feature_columns": X.columns.tolist(),
                    "target": target,
                },
                out_path,
            )
            meta = {
                "target": target,
                "accuracy": info["accuracy"],
                "train_time_s": info["train_time_s"],
                "n_features": len(X.columns),
                "n_samples": len(y),
                "classes": info.get("classes", []),
            }
            meta_path = OUTPUT_DIR / f"pass_model_{target}_meta.json"
            with open(meta_path, "w") as fh:
                json.dump(meta, fh, indent=2)
            print(f"Saved model -> {out_path}, metadata -> {meta_path}")
        except Exception as e:
            print(f"Failed for {target}: {e}")
            continue
    return models_info

def print_summary(trained_models: Dict[str, Dict[str, Any]]):
    print("\n" + "="*50)
    print("Training Summary")
    print("="*50)
    if not trained_models:
        print("No models trained.")
        return
    for t, v in trained_models.items():
        print(f"{t:20} | Acc: {v['accuracy']:.3f} | Time: {v['train_time_s']:.1f}s | Classes: {len(v['classes'])}")

def main():
    start = time.time()
    print("=== Pass Model ===")
    df = load_first_existing(DATA_FILES)
    #filter to pass plays if play_type exists
    if "play_type" in df.columns:
        df = df[df["play_type"] == "pass"].copy()
    print(f"Initial rows (pass plays): {len(df)}")
    df = add_football_intelligence_features(df)
    trained = train_all_targets(df, TARGETS)
    print_summary(trained)
    print(f"\nTotal time: {(time.time() - start)/60:.2f} minutes")
    return trained
=======
    base_cols = [c for c in pre_snap_info if c in df_pass.columns]

    # add season if available
    if "season" in df_pass.columns:
        df_pass["season"] = df_pass["season"].fillna(df_pass["season"].mode().iloc[0])
        base_cols.append("season")

    # ---------------------------
    # 7. Team dummy features, excluding *_score_post leakage
    # ---------------------------
    dummy_team_cols = [
        col
        for col in df_pass.columns
        if (col.startswith("posteam_") or col.startswith("defteam_"))
        and not col.endswith("_score_post")
    ]

    # extra categorical: route, receiver_position
    extra_cat_cols: list[str] = [
        col for col in ["route", "receiver_position"] if col in df_pass.columns
    ]

    if "route" in extra_cat_cols:
        route_counts: pd.Series = df_pass["route"].value_counts()
        top_routes: pd.Index = route_counts.nlargest(20).index
        df_pass["route"] = df_pass["route"].where(
            df_pass["route"].isin(top_routes),
            other="Other",
        )

    for col in extra_cat_cols:
        df_pass[col] = df_pass[col].fillna("Unknown")

    if extra_cat_cols:
        df_pass = pd.get_dummies(
            df_pass,
            columns=extra_cat_cols,
            drop_first=True,
        )

    route_dummy_cols: list[str] = [
        c for c in df_pass.columns if c.startswith("route_")
    ]
    recvpos_dummy_cols: list[str] = [
        c for c in df_pass.columns if c.startswith("receiver_position_")
    ]

    # ---------------------------
    # 8. Coverage dummy columns
    # ---------------------------
    coverage_dummy_cols = [
        col for col in df_pass.columns if col.startswith("coverage_simple_")
    ]

    # ---------------------------
    # Final feature selection
    # ---------------------------
    feature_cols = (
        base_cols
        + dummy_team_cols
        + coverage_dummy_cols
        + route_dummy_cols
        + recvpos_dummy_cols
    )

    print(feature_cols)  # keep this for a sanity check

    X: pd.DataFrame = df_pass[feature_cols].apply(
        pd.to_numeric,
        errors="coerce",
    ).fillna(0)
    y: pd.Series = df_pass["pass_success"]

    # ---------------------------
    # Train/test split
    # ---------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # ---------------------------
    # Random Forest Model
    # ---------------------------
    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    # ---------------------------
    # Evaluation
    # ---------------------------
    y_pred = model.predict(X_test)

    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    df_pass["predicted_pass_success_prob"] = model.predict_proba(X)[:, 1]

    importances = (
        pd.Series(model.feature_importances_, index=X.columns)
        .sort_values(ascending=False)
    )

    print("\nTop 25 important features:")
    print(importances.head(25))

    return model, feature_cols, df_pass

>>>>>>> 4c11420dad78a842e52daef2ca70d8f6cde7cfc1

if __name__ == "__main__":
    main()
