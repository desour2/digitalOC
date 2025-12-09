import nflreadpy as nfl
import pandas as pd

#load_nextgen_stats function: ("passing/rushing/receiving", year)
pbp = nfl.load_nextgen_stats(stat_type="receiving", seasons=2020)
pbp_pd = pbp.to_pandas()
pbp_pd.to_csv("../data/nextgen_receiving_2020.csv", index=False)

print("Data downloaded and saved to /data folder")
