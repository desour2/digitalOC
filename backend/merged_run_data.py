import pandas as pd
import glob 
import os


# column and value that identify a run play
# 'rush_attempt (1 if run, 0 if not)'
RUN_ATTEMPT_COLUMN = 'rush_attempt'
RUN_ATTEMPT_VALUE = 1

# columns needed from each file type
PLAYS_COLUMNS = [
    'old_game_id', 
    'play_id',
    'game_id',
    'play_type',

    RUN_ATTEMPT_COLUMN,
    'yards_gained',
    'run_location',
    'run_gap',
    'epa'
]

PARTICIPATION_COLUMNS = [
    'old_game_id',
    'play_id',
    'offense_formation',
    'offense_personnel',
    'defense_personnel',      # new
    'defenders_in_box',       # new
]

def load_and_process_files(file_pattern: str, required_columns: list) -> pd.DataFrame:
    all_files = glob.glob(file_pattern)
    
    if not all_files:
        return pd.DataFrame(columns=required_columns)

    df_list = []
    for filename in all_files:
        try:
            required_cols_set = set(required_columns)
            df = pd.read_csv(
                filename, 
                usecols = lambda col: col in required_cols_set,
                dtype = str
            )
            
            if 'old_game_id' in df.columns:
                df['old_game_id'] = df['old_game_id'].astype(str)
            if 'play_id' in df.columns:
                df['play_id'] = pd.to_numeric(df['play_id'], errors='coerce').fillna(0).astype(int)
                df['play_id'] = df['play_id'].astype(str)

            df_list.append(df)
        except ValueError as ve:
            # This common error happens if a file is missing one of the 'required_columns'
            print(f"Skipping {filename}. It might be missing columns. Error: {ve}")
        except Exception as e:
            print(f"Error reading {filename}: {e}. Skipping file.")

    if not df_list:
        return pd.DataFrame(columns=required_columns)

    # combine all individual DataFrames into one
    full_df = pd.concat(df_list, ignore_index=True)
    return full_df

def main_func(modyear, year):

    # Using glob patterns to find files.
    filepath = f'data/pbp_{modyear}.csv'
    participation_filepath = f'data/pbp_participation_{year}.csv'
    # output file
    output_file = f'data/merged_rush_model_data_{modyear}.csv'

    plays_df = load_and_process_files(filepath, PLAYS_COLUMNS)

    if plays_df.empty:
        print("Stopping script: Plays data couldnt be loaded.")
        return
        
    plays_df[RUN_ATTEMPT_COLUMN] = pd.to_numeric(plays_df[RUN_ATTEMPT_COLUMN], errors='coerce').fillna(0)
    filtered_plays_df = plays_df[plays_df[RUN_ATTEMPT_COLUMN] == RUN_ATTEMPT_VALUE].copy()
    
    participation_df = load_and_process_files(participation_filepath, PARTICIPATION_COLUMNS)

    if participation_df.empty:
        print("Stopping script: Participation data couldnt be loaded.")
        return
    
    key_cols = ['old_game_id', 'play_id']
    info_cols = ['offense_formation', 'offense_personnel',  'defense_personnel',     # new
    'defenders_in_box',      # new
    ]
    
    # make  all columns exist before trying to drop duplicates
    valid_info_cols = [col for col in info_cols if col in participation_df.columns]
    
    # keep only the first record for each play
    filtered_participation_df = participation_df.drop_duplicates(subset=key_cols + valid_info_cols)

    # merge dataFrames
    merge_keys = ['old_game_id', 'play_id']

    merged_df = pd.merge(
        filtered_plays_df,
        filtered_participation_df,
        on=merge_keys,
        how='inner'
    )
    
    try:
        merged_df.to_csv(output_file, index=False)
        print(f"\ncombined data saved to: {os.path.abspath(output_file)}")
        
        print("\nFirst 5 rows of the new data:")
        print(merged_df.head())

    except Exception as e:
        print(f"\nerror saving file to {output_file}: {e}")

if __name__ == "__main__":
    years = [
        "2020_0",
        "2020_1",
        "2021_0",
        "2021_1",
        "2022_0",
        "2022_1",
        "2023_0",
        "2023_1",
        "2024_0",
        "2024_1"
    ]
    for year in years:
        main_func(year, year[:-2])
