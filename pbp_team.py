# Extract essential data from specific plays 
# Testing using pbp_2024_0.csv file right now

# Import necessary libraries
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from typing import Dict, Any, Tuple
import re
'''
x variables include:
1. Game Situation Variables (Critical)
down - Current down (1st, 2nd, 3rd, 4th)
ydstogo - Yards to go for first down
yardline_100 - Distance to opponent's end zone (field position)
goal_to_go - Binary flag if in goal-to-go situation
quarter_seconds_remaining - Time left in current quarter
game_seconds_remaining - Total time left in game
game_half - Half1 or Half2

2. Score and Win Probability Variables (Critical)
score_differential - Current point differential (positive = leading)
wp - Win probability (0-1)
vegas_wp - Vegas-adjusted win probability
ep - Expected points for current situation
posteam_timeouts_remaining - Timeouts left for offensive team
defteam_timeouts_remaining - Timeouts left for defensive team

3. Team and Matchup Variables (Important)
posteam - Possession team (offensive team)
defteam - Defensive team
posteam_type - Home or away team on offense
div_game - Divisional game flag

4. Formation and Personnel Variables (Important)
shotgun - Binary flag for shotgun formation
no_huddle - Binary flag for no-huddle offense
qb_dropback - Binary flag indicating QB dropped back

5. Environmental Variables (Moderately Important)
roof - Stadium type (outdoors, dome, retractable)
surface - Field surface (grass, turf)
temp - Temperature in Fahrenheit
wind - Wind speed in mph
weather - Weather description

6. Drive Context Variables (Moderately Important)
drive_play_count - Number of plays in current drive
drive_time_of_possession - Time of possession for current drive
drive_start_yard_line - Starting field position of drive
ydsnet - Net yards gained on current drive

7. Historical Performance Variables (Advanced)
total_home_rush_epa / total_away_rush_epa - Cumulative rushing EPA
total_home_pass_epa / total_away_pass_epa - Cumulative passing EPA
series_success - Success rate in current series
cp - Completion probability (for pass plays)
cpoe - Completion percentage over expected

8. Coaching and Personnel Variables (Useful)
home_coach / away_coach - Head coaches
passer_player_name - Starting QB
season_type - Regular season, playoffs, etc.
week - Week of the season

9. Betting Market Variables (Contextual)
spread_line - Point spread
total_line - Over/under total
vegas_home_wp - Vegas home team win probability
'''

'''
y variables include:
play_type, run_location, pass_length, pass_type
'''

def successful_play(situation): 
    ''' Determines if a play was successful based on the outcome of the play '''

    is_successful = 0










    return is_successful


def train_model(X, y):
    # Split the data between X and y
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Handle categorical columns for the X values (non-numeric data)
    # (E.g. posteam="KC" becomes posteam_KC=1, all other team columns = 0)
    categorical_cols = ['posteam', 'defteam', 'posteam_type', 'game_half']
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
    print()

    # Create and train the model 
    model = RandomForestClassifier(n_estimators=100, random_state=42) # Initialize the classifier
    model.fit(X_train_clean, y_train_clean) # Train the model
    y_pred = model.predict(X_test_clean) # Make predictions on test set
    accuracy = accuracy_score(y_test_clean, y_pred) # Calculate accuracy
    
    # Print accuracy
    print(f"Model accuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test_clean, y_pred))
    print()
    
    # Return the trained model for later use
    return model, X_train_clean.columns.tolist()  # Also return column names for later predictions


def predict_play(situation, trained_model, feature_columns):
    ''' Use the situation to determine the most optimal play type '''

    # Print the current situation
    print(f"Down: {situation[0]}")
    print(f"Yards to go: {situation[1]}")
    print(f"Distance to end zone: {situation[2]}")
    print(f"Goal to go: {situation[3]}")
    print(f"Quarter seconds remaining: {situation[4]}")
    print(f"Half seconds remaining: {situation[5]}")
    print(f"Game seconds remaining: {situation[6]}")
    print(f"Game half: {situation[7]}")
    print(f"Score differential: {situation[8]}")
    print(f"Win probability: {situation[9]}")
    print(f"Vegas win probability: {situation[10]}")
    print(f"Expected points: {situation[11]}")
    print(f"Offensive team timeouts remaining: {situation[12]}")
    print(f"Defensive team timeouts remaining: {situation[13]}")
    print(f"Offensive team: {situation[14]}")
    print(f"Defensive team: {situation[15]}")
    print(f"Offensive team type: {situation[16]}")
    print(f"Divisional game: {situation[17]}")
    print(f"Shotgun formation: {situation[18]}")
    # print(f"Quarterback dropback: {situation[19]}")
    print()

    # Convert input to DataFrame with correct column names
    situation_df = pd.DataFrame([situation], columns=['down', 'ydstogo', 'yardline_100', 'goal_to_go', 
                                                        'quarter_seconds_remaining', 'half_seconds_remaining', 'game_seconds_remaining', 
                                                        'game_half', 'score_differential', 'wp', 'vegas_wp',
                                                        'ep', 'posteam_timeouts_remaining', 'defteam_timeouts_remaining', 
                                                        'posteam', 'defteam', 'posteam_type', 'div_game', 
                                                        'shotgun'])

    # Apply same categorical encoding as training
    categorical_cols = ['posteam', 'defteam', 'posteam_type', 'game_half']
    situation_encoded = pd.get_dummies(situation_df, columns=categorical_cols, drop_first=True)
    
    # Make sure it has all the same columns as training data
    for col in feature_columns:
        if col not in situation_encoded.columns:
            situation_encoded[col] = 0
    
    # Reorder columns to match training data
    situation_encoded = situation_encoded[feature_columns]

    # Predict the most optimal play type
    prediction = trained_model.predict(situation_encoded)
    prediction_proba = trained_model.predict_proba(situation_encoded)

    print("======================================")
    print(f"Predicted Play Type: {prediction}")
    print(f"Confidence {prediction_proba}")
    print()
    
    return prediction[0], prediction_proba[0]  # Return prediction and confidence


if __name__ == "__main__":
    ''' Eventually will replace 'if name == main' with a function that will be called via a Flask endpoint ''' 

    # Open the 2024 Play-by-Play CSV file (First Part)
    df = pd.read_csv("Data/pbp_2024_0.csv")
    print(df.columns.to_list())
    print(df.head())
    
    # Filter columns that only contain "run" or "pass" for play_type
    df_filtered = df[df['play_type'].isin(['run', 'pass'])]

    #TODO: Determine if a play was successful (for the y-variables)

    # (game situation) x variables using categories 1-3 for now
    X = df_filtered[['down', 'ydstogo', 'yardline_100', 'goal_to_go', 'quarter_seconds_remaining',
            'half_seconds_remaining', 'game_seconds_remaining', 'game_half', 'score_differential', 'wp', 'vegas_wp',
            'ep', 'posteam_timeouts_remaining', 'defteam_timeouts_remaining', 'posteam', 'defteam',
            'posteam_type', 'div_game', 'shotgun']]
    print(X.head(10))

    # y variable, play type will be "run" or "pass" for now
    y = df_filtered['play_type']
    print(y.head(10))

    ''' HOLDING OFF RUN/PASS SPECIFICS FOR NOW '''
    # # running plays (if 'play_type' is 'run')
    # df_run_plays = df_play_type[(df_play_type['play_type'] == 'run') & (df_play_type['run_location'].notna())][df_situation.columns.tolist() + ['run_location']]
    # print(df_run_plays.head(10))

    # # passing plays (if 'play_type' is 'pass')
    # df_pass_plays = df_play_type[(df_play_type['play_type'] == 'pass') & (df_play_type['pass_length'].notna()) & (df_play_type['pass_location'].notna())][df_situation.columns.tolist() + ['pass_length', 'pass_location']]
    # print(df_pass_plays.head(10))

    trained_model, feature_columns = train_model(X, y)
    print(feature_columns)
    print()

    # FOR LATER: Test the model with random x variables
    test_case_1 = [2, 5, 30, 0, 300, 300, 2100, 'Half1', -3, 0.45, 0.5, 1.2, 2, 2, 'NE', 'NYG', 'home', 0, 1] # 2nd & 5 from OPP 30
    test_case_2 = [3, 15, 50, 0, 120, 120, 120, 'Half2', 7, 0.65, 0.6, 3.5, 1, 1, 'KC', 'DEN', 'away', 1, 0] # 3rd & 15 from midfield
    test_case_3 = [1, 10, 80, 0, 900, 900, 2700, 'Half1', 0, 0.5, 0.55, 0.0, 3, 3, 'DET', 'BUF', 'home', 0, 0] # 1st & 10 from OWN 20
    test_case_4 = [1, 7, 7, 1, 60, 60, 60, 'Half2', 4, 0.4, 0.45, -1.0, 0, 1, 'SF', 'SEA', 'away', 1, 1] # 1st & Goal from 7 yards out
    test_case_5 = [4, 1, 5, 0, 120, 120, 120, 'Half2', -10, 0.2, 0.3, -2.5, 0, 0, 'PHI', 'DAL', 'away', 1, 0] # 4th & 1 from OPP 5 - PHI would presumably run the "tush-push" play in this situation

    predict_play(test_case_1, trained_model, feature_columns)
    predict_play(test_case_2, trained_model, feature_columns)
    predict_play(test_case_3, trained_model, feature_columns)
    predict_play(test_case_4, trained_model, feature_columns)
    predict_play(test_case_5, trained_model, feature_columns)