'''
This model predicts the expected yards gained on a play based on the same situational features as the play type model.

The following feature columns will be used for now: 
    - Type of play: 
        - run/pass

    - For running plays: 
        - run gap
        - run location
        - offensive formation
        - offensive personnel 

    - For passing plays: 
        - receiver position
        - route
        - offensive formation
        - offensive personnel 
        - pass location
        - pass length

    - Additional feature columns required: 
        - team on offense
        - team on defense
        - field position
        - score differential
        - game time remaining

Target variable:
    - Expected yards gained on the play (continuous variable)

'''

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import json
from pathlib import Path
from TeamElo import PlayClassifier, team_elos


def train_exp_yards_model_run():
    # Open both 2024 Play-by-Play CSV files and combine them
    pbp_files = [pd.read_csv("Data/pbp_2024_0.csv"), pd.read_csv("Data/pbp_2024_1.csv")]
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
    
    # feature columns
    df_filtered["elo_score"] = df_filtered.apply(get_elo, axis=1)
    X = df_filtered[['run_gap', 'run_location', 'posteam', 'defteam', 'elo_score', 'ydstogo', 'yardline_100', 
                     'goal_to_go', 'quarter_seconds_remaining','half_seconds_remaining', 'game_seconds_remaining', 
                     'score_differential', 'posteam_timeouts_remaining', 'defteam_timeouts_remaining']]
    print(df_filtered.shape) # roughly 15k rows, 13 feature columns
    print(X.head(10))

    # target variable
    y = df_filtered['yards_gained']
    print(y.head(10))

    #NOTE: For offense_formation and offense_personnel, we need to use the pbp_participation_2024.csv file

    # Split the data between X and y
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Handle categorical columns for the X values (non-numeric data)
    # (E.g. posteam="KC" becomes posteam_KC=1, all other team columns = 0)
    categorical_cols = ['posteam', 'defteam', 'run_gap', 'run_location']
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
    model = LinearRegression()
    model.fit(X_train_clean, y_train_clean)

    # Predict on test data
    y_pred = model.predict(X_test_clean)

    # Calculate metrics
    mse = mean_squared_error(y_test_clean, y_pred)
    r2 = r2_score(y_test_clean, y_pred)

    print(f"Mean Squared Error: {mse}")
    print(f"R-squared: {r2}")

    # # Save the model
    # joblib.dump(model, "Models/exp_yards_model_run.pkl")















def train_exp_yards_model_pass():
    return "Placeholder for expected yards model for passing plays"
















def predict_exp_yards_run():
    pass

















def predict_exp_yards_pass():
    pass















if __name__ == "__main__":
    train_exp_yards_model_run()
    train_exp_yards_model_pass()