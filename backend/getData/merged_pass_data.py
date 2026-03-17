import os
import glob
import pandas as pd
from typing import List

DATA_DIR = "../data"

# relevant pbp columns for pass model
PBP_COLS = [
    # ids
    "play_id", "nflverse_game_id", "game_id",
    # situation
    "down", "ydstogo", "yardline_100", "goal_to_go",
    "qtr", "quarter_seconds_remaining", "half_seconds_remaining", "game_seconds_remaining",
    "score_differential", "posteam_timeouts_remaining", "defteam_timeouts_remaining",
    "posteam", "defteam",
    # pre-snap
    "shotgun", "no_huddle", "qb_dropback",
    # pass details
    "pass_length", "pass_location", "air_yards", "receiver",
    "receiver_id", "receiver_player_id",  # <-- important for ID-based merge
    # post-play
    "yards_after_catch", "yards_gained", "epa", "success", "wpa", "complete_pass", "air_epa",
    # filters (will be dropped later)
    "pass_attempt", "play_type", "penalty", "no_play"
]

# relevant participation columns for pass model
PART_COLS = [
    "nflverse_game_id", "play_id",
    "possession_team", "offense_formation", "offense_personnel", "route"
]

def to_int_play_id(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")

# Ensure df has 'nflverse_game_id' (rename from 'game_id' if needed) and 'play_id'
def norm_keys_on_both(df: pd.DataFrame, must_have_nflverse: bool = True) -> pd.DataFrame:
    out = df.copy()

    if "nflverse_game_id" not in out.columns and "game_id" in out.columns:
        out = out.rename(columns={"game_id": "nflverse_game_id"})

    if must_have_nflverse and "nflverse_game_id" not in out.columns:
        raise KeyError("Missing 'nflverse_game_id' after normalization.")

    if "nflverse_game_id" in out.columns:
        out["nflverse_game_id"] = out["nflverse_game_id"].astype(str).str.strip()

    if "play_id" in out.columns:
        out["play_id"] = to_int_play_id(out["play_id"])

    return out

def load_pbp_year(year: str) -> pd.DataFrame:
    # Read both pbp parts for a year, filter to passes, normalize keys.
    pattern = os.path.join(DATA_DIR, f"pbp_{year}_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No PBP files found at {pattern}")

    dfs = []
    for f in files:
        df = pd.read_csv(f, dtype=str)
        # keep only relevant columns that exist in this file
        df = df[[c for c in PBP_COLS if c in df.columns]]
        dfs.append(df)

    pbp = pd.concat(dfs, ignore_index=True)

    # normalize keys (allow deriving nflverse from game_id if necessary)
    pbp = norm_keys_on_both(pbp, must_have_nflverse=False)
    if "nflverse_game_id" not in pbp.columns:
        raise KeyError("PBP lacks 'nflverse_game_id' and couldn't derive it from 'game_id'.")

    # strict-ish pass filter
    pbp["pass_attempt"] = pd.to_numeric(pbp.get("pass_attempt", 0), errors="coerce").fillna(0).astype(int)
    pbp["qb_dropback"] = pd.to_numeric(pbp.get("qb_dropback", 0), errors="coerce").fillna(0).astype(int)
    pbp["play_type"] = pbp.get("play_type", "").astype(str).str.lower()
    pbp["down"] = pd.to_numeric(pbp.get("down"), errors="coerce")

    is_pass = (pbp["pass_attempt"] == 1) | (pbp["qb_dropback"] == 1) | (pbp["play_type"] == "pass")

    # exclude penalties/no-plays/interceptions if present
    if "penalty" in pbp.columns:
        pbp["penalty"] = pd.to_numeric(pbp["penalty"], errors="coerce").fillna(0).astype(int)
        is_pass &= pbp["penalty"] == 0
    if "no_play" in pbp.columns:
        pbp["no_play"] = pd.to_numeric(pbp["no_play"], errors="coerce").fillna(0).astype(int)
        is_pass &= pbp["no_play"] == 0
    if "interception" in pbp.columns:
        pbp["interception"] = pd.to_numeric(pbp["interception"], errors="coerce").fillna(0).astype(int)
        is_pass &= pbp["interception"] == 0


    # require basic context (down not NA)
    pbp = pbp[is_pass & pbp["down"].notna()].copy()

    # drop helper cols
    pbp = pbp.drop(columns=["pass_attempt", "play_type", "penalty", "no_play"], errors="ignore")

    # final key cleanup
    pbp = pbp.dropna(subset=["nflverse_game_id", "play_id"])
    return pbp

def load_participation_year(year: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"pbp_participation_{year}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Participation file not found: {path}")
    part = pd.read_csv(path, dtype=str)
    part = part[[c for c in PART_COLS if c in part.columns]]
    part = norm_keys_on_both(part, must_have_nflverse=True)
    part = part.dropna(subset=["nflverse_game_id", "play_id"]).drop_duplicates(subset=["nflverse_game_id", "play_id"])
    return part


def load_players_positions() -> pd.DataFrame:
    # Load players.csv from nflverse and return gsis_id, short_name, receiver_position

    # receiver_position is primarily players.position, but uses position_group if position is missing.
    path = os.path.join(DATA_DIR, "players.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"players.csv not found at {path}")

    players = pd.read_csv(path, dtype=str)

    keep_cols = ["gsis_id", "short_name", "position_group", "position"]
    players = players[[c for c in keep_cols if c in players.columns]].copy()

    players["short_name"] = players["short_name"].astype(str).str.strip()
    players["gsis_id"] = players["gsis_id"].astype(str).str.strip()

    # drop rows with no ID or no short_name
    players = players.dropna(subset=["gsis_id", "short_name"])

    # position mapped to receiver_position, using position_group when receiver_position is missing
    players = players.rename(columns={"position": "receiver_position"})
    if "position_group" in players.columns:
        players["receiver_position"] = players["receiver_position"].fillna(players["position_group"])

    # remove duplicates based on ID (ID is primary key)
    players = players.drop_duplicates(subset=["gsis_id"], keep="first")

    return players[["gsis_id", "short_name", "receiver_position"]]


def build_pass_frame(year: str) -> pd.DataFrame:
    pbp = load_pbp_year(year)
    part = load_participation_year(year)
    players = load_players_positions()

    # re-normalize defensively (strip, types)
    for df in (pbp, part):
        df["nflverse_game_id"] = df["nflverse_game_id"].astype(str).str.strip()
        df["play_id"] = to_int_play_id(df["play_id"])

    merged = pbp.merge(part, on=["nflverse_game_id", "play_id"], how="left")

    # season (might still be useful)
    merged["season"] = pd.to_numeric(
        merged["nflverse_game_id"].str.split("_", n=1).str[0],
        errors="coerce"
    ).astype("Int64")

    # clean receiver name and IDs
    merged["receiver"] = merged.get("receiver", "").astype(str).str.strip()

    if "receiver_id" in merged.columns:
        merged["receiver_id"] = merged["receiver_id"].astype(str).str.strip()
    if "receiver_player_id" in merged.columns:
        merged["receiver_player_id"] = merged["receiver_player_id"].astype(str).str.strip()

    # Primary attempt: Merge on ID
    id_col = None
    if "receiver_id" in merged.columns:
        id_col = "receiver_id"
    elif "receiver_player_id" in merged.columns:
        id_col = "receiver_player_id"

    if id_col is not None:
        merged = merged.merge(
            players[["gsis_id", "receiver_position"]],
            left_on=id_col,
            right_on="gsis_id",
            how="left"
        )
        merged = merged.drop(columns=["gsis_id"], errors="ignore")
    else:
        # if there is no ID, create an empty receiver_position column
        merged["receiver_position"] = pd.NA

    # fill remaining gaps after name-based merge
    still_missing = (
        merged["receiver_position"].isna()
        & merged["receiver"].notna()
        & (merged["receiver"].str.strip() != "")
    )

    if still_missing.any():
        name_map = players[["short_name", "receiver_position"]].drop_duplicates(subset=["short_name"])
        merged = merged.merge(
            name_map,
            left_on="receiver",
            right_on="short_name",
            how="left",
            suffixes=("", "_by_name")
        )
        merged["receiver_position"] = merged["receiver_position"].fillna(merged["receiver_position_by_name"])
        merged = merged.drop(columns=["short_name", "receiver_position_by_name"], errors="ignore")

        # Drop plays where receiver is a defensive position (interceptions that slipped through)
        OFFENSIVE_RECEIVER_POS = ["WR", "TE", "RB", "FB"]
        merged = merged[merged["receiver_position"].isin(OFFENSIVE_RECEIVER_POS)]


    # simple match-rate report
    if "offense_personnel" in merged.columns:
        match_rate = merged["offense_personnel"].notna().mean()
    else:
        part_cols_present = [
            c for c in ["possession_team", "offense_formation", "offense_personnel", "route"]
            if c in merged.columns
        ]
        match_rate = merged[part_cols_present].notna().any(axis=1).mean() if part_cols_present else 0.0

    pos_cov = merged["receiver_position"].notna().mean()
    print(f"[{year}] rows: {len(merged):,}  participation match: {match_rate:.1%}  receiver_position coverage: {pos_cov:.1%}")

    # looking for any remaining missing positions
    missing_with_name = (
        merged["receiver"].notna()
        & (merged["receiver"].str.strip() != "")
        & merged["receiver_position"].isna()
    )
    if missing_with_name.any():
        print("Rows with named receiver but missing position:", missing_with_name.sum())
        print("Sample of receivers with missing position:")
        print(merged.loc[missing_with_name, "receiver"].value_counts().head(20))

    return merged

def build_and_save(years: List[str], out_name: str = "merged_pass_model_data.csv") -> pd.DataFrame:
    frames = []
    for y in years:
        frames.append(build_pass_frame(y))
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    out_path = os.path.join(DATA_DIR, out_name)
    out.to_csv(out_path, index=False)
    print(f"Saved → {os.path.abspath(out_path)}")
    print(out.head())
    return out

if __name__ == "__main__":
    # change the list if you only want 2024, etc.
    YEARS = ["2020"]  # or ["2020","2021","2022","2023","2024"]
    build_and_save(YEARS, out_name="merged_pass_model_data_2020.csv")

    # returns giant dataframe in csv stored in data folder.