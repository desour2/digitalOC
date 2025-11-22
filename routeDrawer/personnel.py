import pandas as pd
import sys

#script that gathers personnel data:
# formations, personnel, play data, route, etc.

# 1. PBP (Play-by-Play) files and columns
PBP_FILES = [
    '../data/pbp_2021_0.csv', 
    '../data/pbp_2021_1.csv'
]
# We MUST include 'play_type' for filtering.
# We MUST include 'game_id' AND 'play_id' for merging.
PBP_COLS = [
    'game_id', 
    'play_id',  
    'play_type',
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
    'yardline_100',
    'down',
    'ydstogo',
    'interception'
]

# 2. Participation file and columns
PARTICIPATION_FILE = '../data/pbp_participation_2021.csv'
# We MUST include 'nflverse_game_id' AND 'play_id' for merging.
PARTICIPATION_COLS = [
    'nflverse_game_id', 
    'play_id',
    'offense_formation', 
    'offense_personnel', 
    'route', 
    'defense_coverage_type'
]



# 3. Filter query
PBP_FILTER_QUERY = "play_type == 'pass' or play_type == 'run'"

OUTPUT_FILENAME = 'personnelData/personnel2021.csv'

def load_and_concat(files, columns):
    """
    Loads a list of CSV files (using only specified columns)
    and concatenates them into a single DataFrame.
    """
    dfs_to_concat = []
    print(f"Loading and concatenating PBP files...")
    for f in files:
        try:
            # Load only the columns we need
            df = pd.read_csv(f, usecols=columns)
            dfs_to_concat.append(df)
            print(f"  Loaded {f} ({len(df)} rows)")
        except FileNotFoundError:
            print(f"  ERROR: File not found: {f}. Skipping.")
        except ValueError as e:
            print(f"  ERROR: Could not read {f}. Check column names.")
            print(f"  Details: {e}")
            # This can happen if 'play_id' isn't in one of the files
            if 'play_id' in str(e):
                print("  >>> Make sure 'play_id' column exists in all PBP files.")
        except Exception as e:
            print(f"  An unexpected error occurred with {f}: {e}")
            
    if not dfs_to_concat:
        print("No PBP data was loaded. Exiting.")
        return None
        
    # Stack the DataFrames on top of each other
    combined_df = pd.concat(dfs_to_concat, ignore_index=True)
    print(f"Successfully combined PBP files. Total rows: {len(combined_df)}")
    return combined_df

def load_single_file(filename, columns):
    """
    Loads a single CSV file, using only specified columns.
    """
    print(f"Loading participation file: {filename}...")
    try:
        df = pd.read_csv(filename, usecols=columns)
        print(f"  Loaded {filename} ({len(df)} rows)")
        return df
    except FileNotFoundError:
        print(f"  ERROR: File not found: {filename}. Exiting.")
        return None
    except ValueError as e:
        print(f"  ERROR: Could not read {filename}. Check column names.")
        print(f"  Details: {e}")
        if 'play_id' in str(e):
             print("  >>> Make sure 'play_id' column exists in the Participation file.")
        return None
    except Exception as e:
        print(f"  An unexpected error occurred with {filename}: {e}")
        return None

def main():
    """
    Main script logic to load, filter, merge, and save data.
    """
    # 1. Load and Concat PBP files
    pbp_df = load_and_concat(PBP_FILES, PBP_COLS)
    if pbp_df is None:
        sys.exit(1) # Exit the script if loading failed

    # 2. Filter for pass plays
    print(f"Applying filter to PBP data: \"{PBP_FILTER_QUERY}\"")
    original_count = len(pbp_df)
    
    try:
        pbp_df_filtered = pbp_df.query(PBP_FILTER_QUERY).copy()
        new_count = len(pbp_df_filtered)
        print(f"  Filtered down to {new_count} pass plays (from {original_count} total).")
    except pd.errors.UndefinedVariableError:
        print(f"  ERROR: Filter failed. Most likely 'play_type' was not found.")
        print(f"  Please ensure 'play_type' is in the PBP_COLS list.")
        sys.exit(1)
    except Exception as e:
        print(f"  An unexpected error occurred during filtering: {e}")
        sys.exit(1)

    if pbp_df_filtered.empty:
        print("  Warning: The filter resulted in 0 pass plays. No data to merge.")
        
    # 3. Load Participation file
    participation_df = load_single_file(PARTICIPATION_FILE, PARTICIPATION_COLS)
    if participation_df is None:
        sys.exit(1) # Exit the script if loading failed

    # 4. Merge data
    print("Merging filtered PBP data with participation data...")
    print("  Using keys: ('game_id', 'play_id') and ('nflverse_game_id', 'play_id')")

    # Merge on the unique play, not just the game.
    final_df = pd.merge(
        pbp_df_filtered,
        participation_df,
        left_on=['game_id', 'play_id'],         # Key from the left DataFrame (PBP)
        right_on=['nflverse_game_id', 'play_id'], # Key from the right DataFrame (Participation)
        how='left'
    )
    
    print("Merge successful!")
    print(f"  Total rows in final DataFrame: {len(final_df)}")
    if len(final_df) > new_count:
        print("  Warning: Row count increased after merge. Check for duplicate play_ids in participation file.")

    # 5. Clean up and Save
    # We don't need the filter or extra ID columns in the final file.
    columns_to_drop = ['play_type', 'nflverse_game_id']
    final_df = final_df.drop(columns=columns_to_drop, errors='ignore')
    
    print("\n--- First 5 Rows of Combined Data ---")
    print(final_df.head())
    print("\n--- Data Info ---")
    final_df.info()
    
    # Save to CSV
    try:
        final_df.to_csv(OUTPUT_FILENAME, index=False)
        print(f"\nSuccessfully saved combined data to {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"\nERROR: Could not save final file: {e}")

if __name__ == "__main__":
    main()
