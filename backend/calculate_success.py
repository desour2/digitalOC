import pandas as pd
import numpy as np
import os

def calculate_success(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds success column to pbp dataframe.

    1. Automatic Successes: First downs or touchdowns.
    2. Automatic Failures: Turnovers.
    3. Down-based Success:
        - 1st down: 40% of yards to go gained.
        - 2nd down: 60% of yards to go gained.
        - 3rd/4th down: 100% of yards to go gained.

    Args (required columns): 'down', 'ydstogo', 'yards_gained',
                            'first_down_rush', 'touchdown', 'turnover'.

    Returns: Original DataFrame with an added 'success' column (1 = success, 0 = failure).
    """
    # copies of columns
    down = df['down']
    ydstogo = df['ydstogo']
    yards_gained = df['yards_gained']
    interception = df['interception']
    fumble_lost = df['fumble_lost']

    # conditions for np.select:
    # order of steps is important!
    # check for automatic failures first, then automatic successes, then down-based logic.

    conditions = [
    # automatic successes (touchdowns or first downs)
        (df['touchdown'] == 1),
        (df['first_down_rush'] == 1),
        (df['interception'] == 0),
        (df['fumble_lost'] == 0),

    # down-based success logic
        (down == 1) & (yards_gained >= 0.40 * ydstogo),
        (down == 2) & (yards_gained >= 0.60 * ydstogo),
        (down == 3) & (yards_gained >= 1.00 * ydstogo),
        (down == 4) & (yards_gained >= 1.00 * ydstogo),
    ]

    # outcomes for each condition:
    # 1 corresponds to success, 0 to failure.
    outcomes = [
        0,  # Interception = Failure
        0,  # Fumble = Failure
        1,  # Touchdown = Success
        1,  # First Down by Rushing = Success
        1,  # First Down by Passing = Success
        1,  # 1st down success
        1,  # 2nd down success
        1,  # 3rd down success
        1,  # 4th down success
    ]

    # np.select goes through conditions and picks the first one that is True.
    # If none of the conditions are met, it uses the 'default' value, which is 0 (failure).
    df['success'] = np.select(conditions, outcomes, default=0)

    return df

# example
if __name__ == "__main__":

    dataFolder = 'data'
    fileName = 'pbp_2020_0.csv'
    filePath = os.path.join(dataFolder, fileName)
    pbp_df = pd.read_csv(f"../{filePath}")
    print("First five rows of data:")
    print(pbp_df.head())
    print("\n")

    pbp_df_with_success = calculate_success(pbp_df.copy())

    print("Data frame with success column:")

    # display relevant columns to check the logic
    result_cols = ['down', 'ydstogo', 'yards_gained', 'first_down_rush', 'touchdown', 'interception', 'fumble_lost', 'success']
    display_cols = [col for col in result_cols if col in pbp_df_with_success.columns]
    print(pbp_df_with_success[display_cols].head())



    # created sample DataFrame to test
    data = {
        'play_description': [
            '1st and 10, 4-yard run',
            '2nd and 6, 5-yard pass',
            '3rd and 1, 0-yard run, No gain',
            '1st and 10, 50-yard TD pass',
            '2nd and 15, 5-yard run',
            '3rd and 10, INTERCEPTION',
            '4th and 2, 2-yard run for 1st',
            '1st and 10, 3-yard run'
        ],
        'down': [1, 2, 3, 1, 2, 3, 4, 1],
        'ydstogo': [10, 6, 1, 10, 15, 10, 2, 10],
        'yards_gained': [4, 5, 0, 50, 5, -2, 2, 3],
        'first_down_rush': [0, 0, 0, 1, 0, 0, 1, 0],
        'touchdown': [0, 0, 0, 1, 0, 0, 0, 0],
        'turnover': [0, 0, 0, 0, 0, 1, 0, 0],
    }
    pbp_df = pd.DataFrame(data)

    print("--- Original DataFrame ---")
    print(pbp_df.drop(columns=['play_description']))
    print("\n")

    
    # calculate the success column
    pbp_df_with_success = calculate_success(pbp_df.copy())

    print("--- DataFrame with 'success' column ---")
    # display relevant columns to check the logic
    result_cols = ['down', 'ydstogo', 'yards_gained', 'first_down_rush', 'touchdown', 'turnover', 'success']
    print(pbp_df_with_success[result_cols])
    
    print("\n--- Explanation of Results ---")
    for index, row in pbp_df_with_success.iterrows():
        print(f"Play {index+1}: {row['play_description']} -> Success: {row['success']}")