# script that downloads snap count data from desired year into a csv file
import nflreadpy as nfl
import pandas as pd

pbp = nfl.load_snap_counts(2020)

pbp_pd = pbp.to_pandas()
pbp_pd.to_csv("data/snapcounts_2020.csv", index=False)

print("Data downloaded and saved to /data folder")
