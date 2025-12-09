import pandas as pd
import os

# Open the CSV file
df = pd.read_csv("data/pbp_2024_0.csv", low_memory=False)

relevant_columns = [
    "old_game_id", "play_id",
    "posteam", "defteam",
    "play_type", "pass_attempt", "rush_attempt", "air_yards", "run_gap",
    "qb_kneel", "qb_spike", "qb_scramble", "sack",
    "down", "yards_gained", "ydstogo",
    "epa"
]

# Pull relevant data
df_relevant = df[relevant_columns]

# Only remove rows where ESSENTIAL columns are NaN
essential_columns = ["old_game_id", "play_id", "posteam", "defteam", "play_type", "down"]
df_cleaned = df_relevant.dropna(subset=essential_columns).copy()  # ADD .copy() HERE

# Now safely fill NaN values without warnings
df_cleaned['air_yards'] = df_cleaned['air_yards'].fillna(0)
df_cleaned['run_gap'] = df_cleaned['run_gap'].fillna('none')
df_cleaned['qb_kneel'] = df_cleaned['qb_kneel'].fillna(0)
df_cleaned['qb_spike'] = df_cleaned['qb_spike'].fillna(0)
df_cleaned['qb_scramble'] = df_cleaned['qb_scramble'].fillna(0)
df_cleaned['sack'] = df_cleaned['sack'].fillna(0)

# Save your DataFrame to a new CSV file
df_cleaned.to_csv("data/2024_0_EloData.csv", index=False)

# Verification
file_path = "data/2024_0_EloData.csv"
if os.path.exists(file_path):
    file_size = os.path.getsize(file_path)
    print(f"✓ File created: {file_path}")
    print(f"✓ File size: {file_size} bytes")
    
    saved_df = pd.read_csv(file_path)
    print(f"✓ Saved file has {len(saved_df)} rows and {len(saved_df.columns)} columns")
    print("\nFirst 5 rows:")
    print(saved_df.head())
else:
    print("✗ File was not created!")

print("\nSize of dataframe before cleaning: ", df_relevant.shape)
print("Size of dataframe after cleaning: ", df_cleaned.shape)