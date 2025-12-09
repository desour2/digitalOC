# Extract essential data from specific plays 
# Testing using pbp_2024_0.csv file right now

# Import necessary libraries
import pandas as pd


# Open the 2024 Play-by-Play CSV file (First Part)
df = pd.read_csv("Data/pbp_2024_0.csv")
print(df.head())


'''
Inputs for model:
Down (down)
Distance (ydstogo)
Time (quarter_seconds_remaining, half_seconds_remaining, game_seconds_remaining)
Quarter (qtr)
Yard line (yardline_100)
Difference of score between posteam and defteam (score_differential) -> (- if losing, + if winning)
Possessing team (posteam)
Defending team (defteam)
Timeouts remaining (posteam_timeouts_remaining)

Run Outcome / Run Called
Yards gained
Touchdown? (rush_touchdown) (1, 0)
First down (first_down_run) (1, 0)
Formation
Run play? (rush_attempt) (1 if run, 0 if not)
Type of run play (dive, sweep, etc)
run_location (left, middle, right)
run_gap (end, guard, tackle)
tackled_for_loss (1,0)
wpa	Win probability added (WPA) for the posteam.
epa	Expected points added (EPA) by the posteam for the given play.
'''



# Select relevant columns for analysis
relevant_columns = [
    'game_id', 'play_id', 'home_team', 'away_team', 'game_date', 'down',
    'ydstogo', 'quarter_seconds_remaining', 'half_seconds_remaining',
    'game_seconds_remaining', 'qtr', 'yardline_100', 'posteam_timeouts_remaining', 
    'score_differential', 'posteam', 'defteam', 'posteam_timeouts_remaining',
    'run_location', 'yards_after', 'rush_touchdown', 'first_down_rush', 'shotgun',
    'rush_attempt', 'run_location', 'run_gap', 'tackled_for_loss', 
]
df_relevant = df[relevant_columns]

'''
Couldn't find data types for: Formation (replaced with shotgun), Type of Run Play
'''

print(type(df_relevant))
print(type(df))


# Print the first 50 rows of the relevant data
print(df_relevant.head(50))