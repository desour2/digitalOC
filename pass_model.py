import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

def train_pass_model():
    """
    Train a pass success prediction model using pre-snap features only.
    """

    # 1. Load data

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
        # add more files if available
    ]
    df = pd.concat(pbp_files, ignore_index=True)

    # 2. Filter to pass plays
    df_pass = df[df['play_type'] == 'pass'].copy()

    if df_pass.empty:
        print("No pass plays found in the dataset.")
        return None

    # 3. Create pass success label
    is_first_down = (df_pass['yards_gained'] >= df_pass['ydstogo']) & (df_pass['yards_gained'].notna())
    is_touchdown = (df_pass['touchdown'] == 1)
    df_pass['pass_success'] = (is_first_down | is_touchdown).astype(int)

    # 4. One-hot encode categorical team columns
    categorical_cols = ["posteam", "defteam"]
    df_pass = pd.get_dummies(df_pass, columns=categorical_cols, drop_first=True)

    # 5. Fill missing pre-snap indicators
    cols_to_fill = [c for c in ['shotgun', 'no_huddle', 'qb_dropback'] if c in df_pass.columns]
    df_pass[cols_to_fill] = df_pass[cols_to_fill].fillna(0)

    # 6. Define pre-snap features
    pre_snap_info = [
        'down', 'ydstogo', 'yardline_100', 'goal_to_go',
        'qtr', 'quarter_seconds_remaining', 'half_seconds_remaining',
        'game_seconds_remaining', 'score_differential',
        'posteam_timeouts_remaining', 'defteam_timeouts_remaining',
        'shotgun', 'no_huddle'
    ]

    # remove string columns like 'weather', 'roof', 'surface', 'temp', 'wind' OR encode them
    for col in ['weather', 'roof', 'surface', 'temp', 'wind']:
        if col in df_pass.columns:
            # simple: drop them for now
            pre_snap_info = [c for c in pre_snap_info if c != col]

    # add one-hot encoded team columns
    dummy_cols = [col for col in df_pass.columns if col.startswith('posteam_') or col.startswith('defteam_')]
    feature_cols = pre_snap_info + dummy_cols

    X = df_pass[feature_cols]

    # ensure all numeric
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0)

    y = df_pass['pass_success']

    # 8. Ensure all values are numeric
    X = X.fillna(0)

    # 9. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 10. Train model
    pass_success_model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42
    )
    pass_success_model.fit(X_train, y_train)

    # 11. Evaluate
    y_pred = pass_success_model.predict(X_test)
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print(classification_report(y_test, y_pred))

    # 12. Save predicted probabilities for all plays
    df_pass['predicted_pass_success_prob'] = pass_success_model.predict_proba(X)[:, 1]

    # 13. Feature importances
    importances = pd.Series(pass_success_model.feature_importances_, index=X.columns).sort_values(ascending=False)
    print("\nTop 20 important features:")
    print(importances.head(20))

    return pass_success_model, feature_cols, df_pass

if __name__ == "__main__":
    model, features, df_pass_processed = train_pass_model()
