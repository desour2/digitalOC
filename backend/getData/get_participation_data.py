# script that downloads pbp participation data from desired year into a csv file
import nflreadpy as nfl
import pandas as pd

pbp = nfl.load_participation(2020)

pbp_pd = pbp.to_pandas()
pbp_pd.to_csv("data/pbp_participation_2020.csv", index=False)

print("Data downloaded and saved to /data folder")
