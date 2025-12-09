# script that downloads pbp data from desired year into a csv file
import nflreadpy as nfl
import pandas as pd

pbp = nfl.load_pbp(2024)

pbp_pd = pbp.to_pandas()
pbp_pd.to_csv("data/pbp_2024.csv", index=False)

print("Data downloaded and saved to /data folder")
