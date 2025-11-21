import pandas as pd
import os

#Load the file you want to clean
input_path = "digitalOC/data/pbp_2024_0.csv"
df = pd.read_csv(input_path, low_memory=False)

useful_cols =[
    #Game context
    "game_id", "season_type", "home_team", "away_team", "posteam", "defteam", "location", "stadium", "roof", 
    "surface", "temp", "wind",

    #Situations
    "qtr", "down", "ydstogo", "yardline_100", "time", "quarter_seconds_remaining", "half_seconds_remaining", "game_seconds_remaining",
    "score_differential", "goal_to_go","posteam_timeouts_remaining", "defteam_timeouts_remaining",

    #Play details
    "play_type", "rush_attempt", "pass_attempt", "field_goal_attempt", "shotgun", "no_huddle", "qb_dropback",
    "run_location", "run_gap", "pass_length", "pass_location", "air_yards", "yards_after_catch",

    #Outcomes
    "yards_gained", "first_down_run", "first_down_pass", "success", "wp", "ep", "epa", "touchdown", "turnover"
]

# Keep only the columns that exist in your dataset

useful_cols = [col for col in useful_cols if col in df.columns]
df = df[useful_cols]

# Drop plays that aren’t meaningful decisions
df = df[df["play_type"].isin(["run", "pass", "field_goal", "punt"])]

# Drop rows missing critical info
df = df.dropna(subset=["down", "ydstogo", "yardline_100"])


# Automatically make the new filename
base, ext = os.path.splitext(input_path)
output_path = f"{base}_cleaned{ext}"
# Save cleaned version
df.to_csv(output_path, index=False)

print(f"Cleaned data saved to {output_path}")