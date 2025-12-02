import pandas as pd
import numpy as np

from typing import Dict, Any, List

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

from parse_personnel import add_personnel_features
from add_participation_features import add_participation_features


def train_run_models() -> Dict[str, Dict[str, Any]]:
    """
    Trains tendency models ('run_gap', 'run_location', 'offense_formation',
    'offense_personnel') using all available situational, personnel, and
    formation features.
    """

    # 1. data loading
    try:
        pbp_files: List[pd.DataFrame] = [
            pd.read_csv("Data/pbp_2024_0.csv", low_memory=False),
            pd.read_csv("Data/pbp_2024_1.csv", low_memory=False),
        ]
        df: pd.DataFrame = pd.concat(pbp_files, ignore_index=True)
    except FileNotFoundError:
        print("Error: Data files not found in 'Data/' directory. Exiting.")
        return {}

    df_filtered: pd.DataFrame = df[df["play_type"] == "run"].copy()

    if df_filtered.empty:
        print("No 'run' plays found. Exiting.")
        return {}

    # 1b. OPTIONAL participation / personnel merge
    try:
        part_df: pd.DataFrame = pd.read_csv(
            "Data/pbp_participation_2024.csv",
            low_memory=False,
        )
    except FileNotFoundError:
        print("Warning: participation file not found, skipping personnel/formation features.")
        part_df = None

    if part_df is not None:
        # figure out shared game key
        if "old_game_id" in df_filtered.columns and "old_game_id" in part_df.columns:
            game_key_col: str = "old_game_id"
        elif "game_id" in df_filtered.columns and "game_id" in part_df.columns:
            game_key_col = "game_id"
        else:
            print("Warning: no shared game id between PBP and participation; skipping personnel/formation.")
            part_df = None

    if part_df is not None:
        keep_cols: List[str] = [game_key_col, "play_id"]

        # only grab what we actually care about right now
        extra_part_cols: List[str] = [
            "offense_personnel",
            "defense_personnel",
            "offense_formation",
            "defenders_in_box",
        ]

        for col in extra_part_cols:
            if col in part_df.columns:
                keep_cols.append(col)

        part_df = part_df[keep_cols].drop_duplicates(subset=[game_key_col, "play_id"])

        df_filtered = pd.merge(
            df_filtered,
            part_df,
            on=[game_key_col, "play_id"],
            how="left",
        )

        # rename into what add_personnel_features expects
        df_filtered = df_filtered.rename(
            columns={
                "offense_personnel": "personnel_off",
                "defense_personnel": "personnel_def",
            }
        )

        # engineer numeric personnel and helper flags
        df_filtered = add_personnel_features(df_filtered)
        df_filtered = add_participation_features(df_filtered)

    # 2. pre-processing (same as group version)
    for col in ["temp", "wind"]:
        if col in df_filtered.columns:
            median_val: float = float(df_filtered[col].median())
            df_filtered[col] = df_filtered[col].fillna(median_val)

    # new situational features
    required_cols: List[str] = [
        "yardline_100",
        "goal_to_go",
        "ydstogo",
        "down",
        "quarter_seconds_remaining",
        "qtr",
        "score_differential",
    ]

    if all(col in df_filtered.columns for col in required_cols):
        df_filtered["is_redzone"] = (df_filtered["yardline_100"] <= 20).astype(int)
        df_filtered["is_goal_line"] = (
            (df_filtered["goal_to_go"] == 1) & (df_filtered["yardline_100"] <= 10)
        ).astype(int)
        df_filtered["is_short_yardage"] = (
            (df_filtered["ydstogo"] <= 2) & (df_filtered["down"] >= 3)
        ).astype(int)
        df_filtered["is_two_minute_drill"] = (
            (df_filtered["quarter_seconds_remaining"] <= 120)
            & (df_filtered["qtr"].isin([2, 4]))
        ).astype(int)
        df_filtered["is_close_game_late"] = (
            (df_filtered["qtr"] == 4)
            & (df_filtered["score_differential"].abs() <= 8)
        ).astype(int)

    # 3. define 'y' (target) for Stage 1: 'run_success'
    # 4. define 'X' (features) for all models

    # original base feature set from your group
    base_feature_columns: List[str] = [
        "down",
        "ydstogo",
        "yardline_100",
        "goal_to_go",
        "qtr",
        "quarter_seconds_remaining",
        "half_seconds_remaining",
        "game_seconds_remaining",
        "half_seconds_remaining", # Added back in
        "score_differential",
        "posteam_timeouts_remaining",
        "defteam_timeouts_remaining",
        "posteam",
        "defteam", 
        "shotgun",
        "no_huddle",
        "roof",
        "surface",
        "temp",
        "wind",
        "is_redzone",
        "is_goal_line",
        "is_short_yardage",
        "is_two_minute_drill",
        "is_close_game_late",
    ]

    personnel_numeric: List[str] = [
        "off_rb",
        "off_te",
        "off_wr",
        "def_dl",
        "def_lb",
        "def_db",
        "defenders_in_box",
    ]

    personnel_categorical: List[str] = [
        "offense_formation",
        "off_group_bucket",
        "def_group_bucket",
    ]

    feature_columns: List[str] = (
        base_feature_columns + personnel_numeric + personnel_categorical
    )

    # fill numeric NaNs for personnel if present
    for num_col in personnel_numeric:
        if num_col in df_filtered.columns:
            df_filtered[num_col] = df_filtered[num_col].fillna(0)

    # #TODO: Temporarily removing the the personnel features and keeping only the base features
    # feature_columns: List[str] = (base_feature_columns)

    existing_features: List[str] = [
        col for col in feature_columns if col in df_filtered.columns
    ]
    X: pd.DataFrame = df_filtered[existing_features].copy()

    if X.empty:
        print("Error: No features found. Exiting.")
        return {}

    # encode categorical features
    categorical_cols: List[str] = [
        "posteam",
        "defteam",
        "roof",
        "surface",
        "qtr",
        "offense_formation",
        "off_group_bucket",
        "def_group_bucket",
    ]

    existing_categorical: List[str] = [
        col for col in categorical_cols if col in X.columns
    ]
    X_processed: pd.DataFrame = pd.get_dummies(
        X,
        columns=existing_categorical,
        drop_first=True,
    )
    
    # the fix for the ValueError: Input X contains NaN
    X_processed = X_processed.fillna(0)
    
    # 5. Stage 1 model: predict run_success
    print("--- Model Pipeline Simplification ---")
    print("Training tendency models directly on all features.")
    print(f"Total features being used: {len(X_processed.columns)}")

    # 6. Stage 2 models: predict tendencies
    trained_models: Dict[str, Dict[str, Any]] = {}
    # NEW: Add the new targets to the list
    target_columns: List[str] = [
        "run_gap",
        "run_location",
        "offense_formation",
        "personnel_off", # CHANGED: Use the renamed column name
    ]

    for target in target_columns:
        print(f"\nStarting model training for: {target}")

        if target not in df_filtered.columns:
            print(f"Target column '{target}' not found.")
            continue

        y_tend: pd.Series = df_filtered[target]

        # Clean NaNs from this *specific* target
        valid_indices = y_tend.dropna().index
        y_clean = y_tend.loc[valid_indices]

        # We must remove features that are derived from the target itself
        X_to_use = X_processed.loc[valid_indices].copy()
        
        # Define leaky columns
        formation_leaks = [col for col in X_to_use.columns if col.startswith('offense_formation_')]
        
        personnel_leaks = [
            'off_rb', 'off_te', 'off_wr'
        ] + [col for col in X_to_use.columns if col.startswith('off_group_bucket_')]
        
        if target == 'offense_formation':
            X_clean = X_to_use.drop(columns=formation_leaks, errors='ignore')
            print(f"  (Dropped {len(formation_leaks)} formation-related features to prevent leakage)")
        elif target == 'personnel_off': # CHANGED: Check for the new name
            X_clean = X_to_use.drop(columns=personnel_leaks, errors='ignore')
            print(f"  (Dropped {len(personnel_leaks)} personnel-related features to prevent leakage)")
        else:
            # For run_gap and run_location, we assume no leakage from these groups
            X_clean = X_to_use

        # Filter out classes that appear fewer than 2 times to prevent stratify error
        class_counts = y_clean.value_counts()
        valid_classes = class_counts[class_counts > 1].index
        
        # Only keep rows where the target is in the valid_classes list
        valid_mask = y_clean.isin(valid_classes)
        X_clean = X_clean.loc[valid_mask]
        y_clean = y_clean.loc[valid_mask]
        # -------------------------------------

        if X_clean.empty or y_clean.nunique() < 2:
            print(
                f"Warning: Not enough data or classes for '{target}' after cleaning. Skipping..."
            )
            continue
        
        # Create a single train/test split for this target
        X_train, X_test, y_train, y_test = train_test_split(
            X_clean,
            y_clean,
            test_size=0.2,
            random_state=42,
            stratify=y_clean
        )
        
        # Logistic Regression performs better when all features are scaled
        scaler = StandardScaler()
        # Use the (potentially modified) X_clean columns
        X_train_scaled = scaler.fit_transform(X_train[X_clean.columns])
        X_test_scaled = scaler.transform(X_test[X_clean.columns])

        model: LogisticRegression = LogisticRegression(
            random_state=42,
            max_iter=1000, # Increase iterations to ensure convergence
            # 'multi_class' is deprecated; removing it uses the new default
        )
        
        model.fit(X_train_scaled, y_train) # Use scaled data

        if not X_test.empty:
            y_pred: np.ndarray = model.predict(X_test_scaled) # Use scaled data
            tend_accuracy: float = accuracy_score(y_test, y_pred)

            print(f"Model accuracy for '{target}': {tend_accuracy:.3f}")
            print(f"Classification report for '{target}':")
            labels: np.ndarray = np.union1d(y_test.unique(), y_pred)
            print(
                classification_report(
                    y_test,
                    y_pred,
                    labels=labels,
                    zero_division=0,
                )
            )

        print(f"Model training complete for: {target}")

        trained_models[target] = {
            "model": model,
            "columns": X_train.columns.tolist(),
            "scaler": scaler 
        }

    return trained_models


def predict_run_metrics(situation, trained_models):
    ''' 
        Function that predicts the most optimal run gap and location 
        with success probability for this specific run play 
        based on the trained run models. 
    '''

    # Convert input to DataFrame with correct column names
    situation_df = pd.DataFrame([situation], columns=['down', 'ydstogo', 'yardline_100', 'goal_to_go', 'quarter_seconds_remaining',
                                                      'half_seconds_remaining', 'game_seconds_remaining', 'score_differential', 
                                                      'posteam_timeouts_remaining', 'defteam_timeouts_remaining', 'posteam', 'defteam'])
    
    # Add the engineered features (same as in training)
    situation_df["is_redzone"] = (situation_df["yardline_100"] <= 20).astype(int)
    situation_df["is_goal_line"] = (
        (situation_df["goal_to_go"] == 1) & (situation_df["yardline_100"] <= 10)
    ).astype(int)
    situation_df["is_short_yardage"] = (
        (situation_df["ydstogo"] <= 2) & (situation_df["down"] >= 3)
    ).astype(int)
    
    # Infer quarter from time remaining (simple heuristic)
    if situation[6] > 2700:  # game_seconds_remaining
        qtr = 1
    elif situation[6] > 1800:
        qtr = 2
    elif situation[6] > 900:
        qtr = 3
    else:
        qtr = 4
    
    situation_df["qtr"] = qtr
    situation_df["is_two_minute_drill"] = (
        (situation_df["quarter_seconds_remaining"] <= 120)
        & (situation_df["qtr"].isin([2, 4]))
    ).astype(int)
    situation_df["is_close_game_late"] = (
        (situation_df["qtr"] == 4)
        & (situation_df["score_differential"].abs() <= 8)
    ).astype(int)
    
    # Add default values for missing columns that were used in training
    situation_df["shotgun"] = 0  # default value
    situation_df["no_huddle"] = 0  # default value
    situation_df["roof"] = "outdoors"  # default value
    situation_df["surface"] = "grass"  # default value
    situation_df["temp"] = 70  # default value
    situation_df["wind"] = 0  # default value
    
    # Apply one-hot encoding to categorical columns (same as training)
    categorical_cols = ["posteam", "defteam", "roof", "surface", "qtr"]
    situation_encoded = pd.get_dummies(
        situation_df,
        columns=categorical_cols,
        drop_first=True,
    )
    
    # Get the situation model to predict success probability first
    sit_model_info = trained_models.get("situation")
    if sit_model_info:
        sit_model = sit_model_info["model"]
        sit_columns = sit_model_info["columns"]
        
        # Align columns with training data
        for col in sit_columns:
            if col not in situation_encoded.columns:
                situation_encoded[col] = 0
        
        situation_encoded = situation_encoded[sit_columns]
        
        # Predict success probability
        success_prob = sit_model.predict_proba(situation_encoded)[0, 1]
        print(f"Predicted run success probability: {success_prob:.3f}")
        
        # Add this as a feature for tendency models
        situation_encoded["predicted_run_success_prob"] = success_prob
    
    # Predict the most optimal metric (gap, location) for the run play 
    run_metrics = {}
    for metric in ["run_gap", "run_location", "offense_formation"]:
        if metric in trained_models:
            model_info = trained_models[metric]
            model = model_info["model"]
            model_columns = model_info["columns"]
            
            # Align columns with training data
            for col in model_columns:
                if col not in situation_encoded.columns:
                    situation_encoded[col] = 0
            
            # Reorder columns to match training
            situation_for_prediction = situation_encoded[model_columns]
            
            # Predict
            prediction = model.predict(situation_for_prediction)[0]
            run_metrics[metric] = prediction
            print(f"Predicted {metric}: {prediction}")

    return run_metrics



if __name__ == "__main__":
    print("Starting all run model training")
    all_models: Dict[str, Dict[str, Any]] = train_run_models()

    if all_models:
        print("\nAll model training complete")
        print(f"Trained {len(all_models)} models: {list(all_models.keys())}")
    else:
        print("\nModel training failed ---")