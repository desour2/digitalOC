import pandas as pd

'''
how to link pbp_participation and pbp files:
- play_id
- old_game_id

what is needed from the participation files:
- offense_personnel - # of RBs, WRs, TEs
- route - all unique routes
- offense_formation - all unique formations

what is needed from pbp files:
- air_yards
- pass_location
'''

raw0 = pd.read_csv("data/pbp_participation_2020.csv")

#dataframe that contains all rows that have a non-null value in the field in brackets and quotes
routes0 = raw0[raw0['offense_personnel'].notna()]

pbp0 = pd.read_csv("data/pbp_2020_0_cleaned.csv")
pbp1 = pd.read_csv("data/pbp_2020_1_cleaned.csv")

uniqueRoutes0 = routes0['offense_personnel'].unique()
print(uniqueRoutes0)

#['GO' 'FLAT' 'CROSS' 'HITCH' 'SCREEN' 'OUT' 'IN' 'SLANT' 'CORNER' 'ANGLE' 'POST' 'WHEEL']
