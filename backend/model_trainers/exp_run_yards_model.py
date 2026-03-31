import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, classification_report
import joblib
import json
from pathlib import Path
try:
    from .TeamElo import PlayClassifier, team_elos
except ImportError:
    from TeamElo import PlayClassifier, team_elos


BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
MODEL_DIR = BACKEND_DIR / "models"


def train_exp_yards_model_run():
    ''' This regression model predicts expected yardage for running plays '''

    # Open both 2024 Play-by-Play CSV files and combine them
    pbp_files = [
        pd.read_csv(DATA_DIR / "pbp_2024_0.csv"),
        pd.read_csv(DATA_DIR / "pbp_2024_1.csv")
    ]
    df = pd.concat(pbp_files, ignore_index=True)
    print(df.columns.to_list())
    print(df.head())
    
    # Filter columns that only contain "run" for play_type
    df_filtered = df[df['play_type'].isin(['run'])]
    print(f"Number of rows after filtering for run/pass plays: {df_filtered.shape[0]}")
    df_filtered["play_category"] = df_filtered.apply(PlayClassifier.get_category, axis=1)

    # Create a column in the input variables for the Offense Team's ELO Rating
    def get_elo(row):
        team = row["posteam"]
        category = row["play_category"]
        return team_elos.get(team, {}).get(category, 1000.0)
    df_filtered["elo_score"] = df_filtered.apply(get_elo, axis=1)
    
    # Intergrate the pbp_participation_file to get offense formation and personnel for each play
    pbp_participation_file = pd.read_csv(DATA_DIR / "pbp_participation_2024.csv")
    '''
        Find the row in the pbp_participation_file where the "nflverse_game_id" and "play_id" match the 
        row with "game_id" and "play_id" in df_filtered
    '''
    def get_participation_info(row):
        game_id = row["game_id"]
        play_id = row["play_id"]
        participation_row = pbp_participation_file[(pbp_participation_file["nflverse_game_id"] == game_id) & 
                                                  (pbp_participation_file["play_id"] == play_id)]
        
        if not participation_row.empty:
            return participation_row.iloc[0]["offense_formation"], participation_row.iloc[0]["offense_personnel"]
        else:
            return np.nan, np.nan
    df_filtered["offense_formation"], df_filtered["offense_personnel"] = zip(*df_filtered.apply(get_participation_info, axis=1))
    
    # feature columns
    X = df_filtered[['run_gap', 'run_location', 'posteam', 'defteam', 'elo_score', 'down', 'ydstogo', 'yardline_100', 
                     'goal_to_go', 'quarter_seconds_remaining','half_seconds_remaining', 'game_seconds_remaining', 
                     'score_differential', 'posteam_timeouts_remaining', 'defteam_timeouts_remaining',
                     'offense_formation', 'offense_personnel']]
    df_filtered["is_redzone"] = (df_filtered["yardline_100"] <= 20).astype(int)
    df_filtered["is_goal_line"] = ((df_filtered["goal_to_go"] == 1) & (df_filtered["yardline_100"] <= 10)).astype(int)
    df_filtered["is_short_yardage"] = ((df_filtered["ydstogo"] <= 2) & (df_filtered["down"] >= 3)).astype(int)
    print(df_filtered.shape) # roughly 15k rows, 13 feature columns
    print(X.head(10))

    # target variable
    y = df_filtered['yards_gained'].clip(-5, 20) # Clip extreme values (reduces noise from breakaway runs/big losses)
    print(y.head(10))

    # Split the data between X and y
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # One-hot encode categorical columns for the X values (non-numeric data)
    categorical_cols = ['posteam', 'defteam', 'run_gap', 'run_location', 'offense_formation', 'offense_personnel']
    X_train_encoded = pd.get_dummies(X_train, columns=categorical_cols, drop_first=True) # Using pd.get_dummies (one-hot encoding)
    X_test_encoded = pd.get_dummies(X_test, columns=categorical_cols, drop_first=True)
    X_train_encoded, X_test_encoded = X_train_encoded.align(X_test_encoded, join='left', axis=1, fill_value=0) # Make sure train and test have same columns (important!)
    
    print(f"Training data shape before cleaning: {X_train_encoded.shape}")
    print(f"Test data shape before cleaning: {X_test_encoded.shape}")
    print()

    # Drop rows with missing values 
    train_complete_idx = X_train_encoded.dropna().index.intersection(y_train.dropna().index)
    X_train_clean = X_train_encoded.loc[train_complete_idx]
    y_train_clean = y_train.loc[train_complete_idx]
    test_complete_idx = X_test_encoded.dropna().index.intersection(y_test.dropna().index) # Do the same for test data
    X_test_clean = X_test_encoded.loc[test_complete_idx]
    y_test_clean = y_test.loc[test_complete_idx]
    print(f"Training data shape after cleaning: {X_train_clean.shape}")
    print(f"Test data shape after cleaning: {X_test_clean.shape}")

    # Train a simple linear regression model
    model = Ridge(alpha=1.0)
    model.fit(X_train_clean, y_train_clean)

    # Predict on test data
    y_pred = model.predict(X_test_clean)

    # Calculate metrics
    mse = mean_squared_error(y_test_clean, y_pred)
    r2 = r2_score(y_test_clean, y_pred)
    print(f"Mean Squared Error: {mse}")
    print(f"R-squared: {r2}")

    # Print out the first 10 predicted vs actual values for the test set
    print("\nPredicted vs Actual values for the first 10 test samples:")
    for i in range(10):
        print(f"Predicted: {y_pred[i]:.2f}, Actual: {y_test_clean.iloc[i]}")

    # Save the model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / "exp_yards_model_run.joblib")
    print("Expected yards model for running plays trained and saved successfully.")


def predict_exp_yards_run(input_dict, model):
    ''' Predict expected yards for a running play '''

    # Prepare input data for prediction
    input_df = pd.DataFrame([input_dict])
    
    # One-hot encode categorical columns
    categorical_cols = ['posteam', 'defteam', 'run_gap', 'run_location', 'offense_formation', 'offense_personnel']
    input_df_encoded = pd.get_dummies(input_df, columns=categorical_cols, drop_first=True)

    # Align with training data columns
    model_cols = model.feature_names_in_
    for col in model_cols:
        if col not in input_df_encoded.columns:
            input_df_encoded[col] = 0
    input_df_encoded = input_df_encoded.reindex(columns=model_cols, fill_value=0)

    # Make prediction
    prediction = model.predict(input_df_encoded)
    return prediction[0]







if __name__ == "__main__":
    train_exp_yards_model_run()