import pandas as pd
import os
import sys

# script that combines personnel files with nextgen files to get position of rusher/receiver
# position is necessary for drawing play

# 1. PBP (Play-by-Play) file

PBP_FILES = [
    'personnelData/personnel2024.csv'
]

# Columns to load from the PBP file
PBP_COLS = [
    'game_id', 
    'play_id',   
    'air_yards', 
    'yards_after_catch', 
    'epa', 
    'complete_pass',
    'touchdown',
    'pass_attempt',
    'pass_length',
    'pass_location',
    'run_location',
    'run_gap',
    'yards_gained',
    'rusher',    
    'receiver', 
    'offense_formation', 
    'offense_personnel', 
    'route',
    'defense_coverage_type',
    'yardline_100',
    'down',
    'ydstogo'
]

# 2. Player Info (Roster) files
PLAYER_INFO_FILE_1 = '../data/nextgen_receiving_2024.csv'
PLAYER_INFO_COLS_1 = [
    'player_short_name',  
    'player_position'    
]

PLAYER_INFO_FILE_2 = '../data/nextgen_rushing_2024.csv'
PLAYER_INFO_COLS_2 = [
    'player_short_name', 
    'player_position'   
]

OUTPUT_FILENAME = 'personnelData/FULLpersonnel2024.csv'


def load_roster_file(filepath, columns):
    print(f"\nLoading Player Info (Roster) data from {filepath}...")
    try:
        player_info_df = pd.read_csv(
            filepath, 
            usecols=columns
        )
        print(f"Total Player Info rows loaded: {len(player_info_df)}")
        
        original_rows = len(player_info_df)
        player_info_df = player_info_df.drop_duplicates(subset=['player_short_name'])
        dropped_rows = original_rows - len(player_info_df)
        if dropped_rows > 0:
            print(f"Removed {dropped_rows} duplicate player names from Player Info file.")
        
        return player_info_df

    except FileNotFoundError:
        print(f"Error: Player Info file not found: {filepath}")
        return None
    except ValueError as e:
        print(f"Error: Columns missing from {filepath}.")
        print(f"Please make sure it contains: {columns}")
        print(f"Details: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading player info data: {e}")
        return None

def merge_pbp_with_player_info():
    pbp_dataframes = []
    
    try:
        cols_to_load = list(set(PBP_COLS))
    except TypeError as e:
        print(f"Error: There might be an unhashable item (like a list) in your PBP_COLS: {e}")
        return

    print(f"Loading PBP data from {len(PBP_FILES)} file(s)...")
    try:
        for file_path in PBP_FILES:
            if not os.path.exists(file_path):
                print(f"  Warning: PBP file not found, skipping: {file_path}")
                continue
            
            print(f"  Reading {file_path}...")
            df = pd.read_csv(file_path, usecols=cols_to_load, low_memory=False)
            pbp_dataframes.append(df)
        
        if not pbp_dataframes:
            print("Error: No PBP files were successfully loaded.")
            print(f"Please check your file paths in PBP_FILES. Did Step 1 run correctly and create {PBP_FILES[0]}?")
            return

        pbp_df = pd.concat(pbp_dataframes, ignore_index=True)
        print(f"Total PBP rows loaded: {len(pbp_df)}")

    except FileNotFoundError as e:
        print(f"Error: File not found. {e}")
        return
    except ValueError as e:
        print(f"Error loading PBP data: A column in PBP_COLS might be missing from {PBP_FILES[0]}.")
        print(f"Details: {e}")
        print("\n--- PLEASE CHECK YOUR PBP_COLS LIST! ---")
        return
    except Exception as e:
        print(f"An unexpected error occurred loading PBP data: {e}")
        return

    print("\nCreating helper column 'player_name_key' from 'rusher' and 'receiver'...")
    
    pbp_df['player_name_key'] = pbp_df['rusher'].fillna(pbp_df['receiver'])
    
    valid_keys_found = pbp_df['player_name_key'].notna().sum()
    print(f"Found {valid_keys_found} plays with an identified rusher or receiver.")

    player_info_df_1 = load_roster_file(PLAYER_INFO_FILE_1, PLAYER_INFO_COLS_1)
    if player_info_df_1 is None:
        print("Could not load primary roster file. Exiting.")
        return

    print(f"\nMerging PBP data with Roster File 1 ({PLAYER_INFO_FILE_1})...")
    print("  Left key (from PBP):   'player_name_key'")
    print("  Right key (from Roster): 'player_short_name'")
    
    merged_df = pd.merge(
        pbp_df, 
        player_info_df_1, 
        left_on='player_name_key',
        right_on='player_short_name', 
        how='left'
    )
    
    # Rename the new position column
    merged_df = merged_df.rename(columns={'player_position': 'involved_player_position'})
    # Drop the key we merged on
    if 'player_short_name' in merged_df.columns:
         merged_df = merged_df.drop(columns=['player_short_name'])

    missing_count = merged_df['involved_player_position'].isna().sum()
    print(f"Merge 1 complete. Found {len(merged_df) - missing_count} positions.")
    print(f"There are {missing_count} positions still missing.")


    player_info_df_2 = load_roster_file(PLAYER_INFO_FILE_2, PLAYER_INFO_COLS_2)
    if player_info_df_2 is None:
        print("Could not load secondary roster file. Skipping fill-in step.")
    else:

        player_info_df_2 = player_info_df_2.rename(
            columns={'player_position': 'player_position_fill'}
        )

        print(f"\nMerging with Roster File 2 ({PLAYER_INFO_FILE_2}) to fill missing values...")

        merged_df = pd.merge(
            merged_df, 
            player_info_df_2, 
            left_on='player_name_key',
            right_on='player_short_name', 
            how='left'
        )
        
        merged_df['involved_player_position'] = merged_df['involved_player_position'].fillna(
            merged_df['player_position_fill']
        )
        
        new_missing_count = merged_df['involved_player_position'].isna().sum()
        filled_count = missing_count - new_missing_count
        print(f"Fill-in complete. Found {filled_count} new positions.")
        print(f"There are {new_missing_count} positions still missing.")

    
    print("\nDropping rows where 'involved_player_position' is still missing...")
    rows_before_drop = len(merged_df)
    merged_df = merged_df.dropna(subset=['involved_player_position'])
    rows_after_drop = len(merged_df)
    rows_dropped = rows_before_drop - rows_after_drop
    print(f"Dropped {rows_dropped} rows. New total rows: {rows_after_drop}")

    print("\nCleaning up final columns...")
    
    # List of all temporary columns to drop
    cols_to_drop = ['player_name_key', 'player_short_name', 'player_position_fill']
    for col in cols_to_drop:
        if col in merged_df.columns:
            merged_df = merged_df.drop(columns=[col])
    
    print("Cleaned up columns. Final columns:")
    print(merged_df.columns.to_list())
    
    try:
        output_dir = os.path.dirname(OUTPUT_FILENAME)
        if output_dir and not os.path.exists(output_dir):
            print(f"\nCreating output directory: {output_dir}")
            os.makedirs(output_dir)
            
        print(f"\nSaving merged data to {OUTPUT_FILENAME}...")
        merged_df.to_csv(OUTPUT_FILENAME, index=False)
        print("Merge complete! File saved successfully.")

    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    merge_pbp_with_player_info()

