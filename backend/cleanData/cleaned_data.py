import pandas as pd
import os

# Path to the file you want to modify
FILE_PATH = "../data/pbp_2023_0.csv"

# Columns you want to DELETE
DELETE_COLUMNS = [
    "fantasy_player_name", "fantasy_player_id", "fantasy", "fantasy_id",
    "passer_player_name", "receiver_player_name", "rusher_player_name",
    "lateral_receiver_player_name", "lateral_rusher_player_name",
    "lateral_interception_player_name", "lateral_punt_returner_player_name",
    "lateral_kickoff_returner_player_name",
    "punter_player_name", "kicker_player_name",
    "passer_jersey_number", "receiver_jersey_number", "rusher_jersey_number",
    "jersey_number",
    "weather",
    "name",
    "player_name",
    "tackle_for_loss_1_player_id", "tackle_for_loss_1_player_name",
    "tackle_for_loss_2_player_id", "tackle_for_loss_2_player_name",
    "qb_hit_1_player_id", "qb_hit_1_player_name",
    "qb_hit_2_player_id", "qb_hit_2_player_name",
    "forced_fumble_player_1_team", "forced_fumble_player_1_player_id",
    "forced_fumble_player_1_player_name",
    "forced_fumble_player_2_team", "forced_fumble_player_2_player_id",
    "forced_fumble_player_2_player_name",
    "solo_tackle_1_team", "solo_tackle_2_team",
    "solo_tackle_1_player_id", "solo_tackle_2_player_id",
    "solo_tackle_1_player_name", "solo_tackle_2_player_name",
    "assist_tackle_1_player_id", "assist_tackle_1_player_name",
    "assist_tackle_1_team",
    "assist_tackle_2_player_id", "assist_tackle_2_player_name",
    "assist_tackle_2_team",
    "assist_tackle_3_player_id", "assist_tackle_3_player_name",
    "assist_tackle_3_team",
    "assist_tackle_4_player_id", "assist_tackle_4_player_name",
    "assist_tackle_4_team",
    "tackle_with_assist",
    "tackle_with_assist_1_player_id", "tackle_with_assist_1_player_name",
    "tackle_with_assist_1_team",
    "tackle_with_assist_2_player_id", "tackle_with_assist_2_player_name",
    "tackle_with_assist_2_team",
    "pass_defense_1_player_id", "pass_defense_1_player_name",
    "pass_defense_2_player_id", "pass_defense_2_player_name",
    "fumbled_1_team", "fumbled_1_player_id", "fumbled_1_player_name",
    "fumbled_2_player_id", "fumbled_2_player_name", "fumbled_2_team",
    "fumble_recovery_1_team", "fumble_recovery_1_yards",
    "fumble_recovery_1_player_id", "fumble_recovery_1_player_name",
    "fumble_recovery_2_team", "fumble_recovery_2_yards",
    "fumble_recovery_2_player_id", "fumble_recovery_2_player_name",
    "sack_player_id", "sack_player_name",
    "half_sack_1_player_id", "half_sack_1_player_name",
    "half_sack_2_player_id", "half_sack_2_player_name",
    "return_team", "return_yards"
]


# Load CSV
df = pd.read_csv(FILE_PATH, low_memory=False)

# Only drop columns that actually exist to avoid errors
cols_to_drop = [c for c in DELETE_COLUMNS if c in df.columns]

print("Dropping these columns:", cols_to_drop)

# Drop
df = df.drop(columns=cols_to_drop)

# Overwrite the same file
df.to_csv(FILE_PATH, index=False)

# Verification
file_size = os.path.getsize(FILE_PATH)
print("\n✓ File updated:", FILE_PATH)
print("✓ New file size:", file_size, "bytes")
print(f"✓ Data now has {len(df.columns)} columns")
print("\nFirst 5 rows:")
print(df.head())
