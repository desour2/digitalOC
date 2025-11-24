import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import numpy as np


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
    ]

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


if __name__ == "__main__":
    model, features, df_pass_processed = train_pass_model()