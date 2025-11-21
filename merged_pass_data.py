import os
import glob
import pandas as pd
from typing import List

DATA_DIR = "Data"

# relevant pbp columns for pass model
PBP_COLS = [
    # ids
    "play_id", "nflverse_game_id", "game_id",
    # situation
    "down","ydstogo","yardline_100","goal_to_go",
    "qtr","quarter_seconds_remaining","half_seconds_remaining","game_seconds_remaining",
    "score_differential","posteam_timeouts_remaining","defteam_timeouts_remaining",
    "posteam","defteam",
    # pre-snap
    "shotgun","no_huddle","qb_dropback",
    # pass details
    "pass_length","pass_location","air_yards","receiver",
    # post-play
    "yards_after_catch","yards_gained","epa","success","wpa","complete_pass","air_epa",
    # filters (will be dropped later)
    "pass_attempt","play_type","penalty","no_play"
]

#relevant participation columns for pass model
PART_COLS = [
    "nflverse_game_id","play_id",
    "possession_team","offense_formation","offense_personnel","route"
]

def to_int_play_id(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64")

def norm_keys_on_both(df: pd.DataFrame, must_have_nflverse=True) -> pd.DataFrame:
    """Ensure df has 'nflverse_game_id' (rename from 'game_id' if needed) and int-like 'play_id'."""
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
    """Read both pbp parts for a year, filter to passes, normalize keys."""
    pattern = os.path.join(DATA_DIR, f"pbp_{year}_*.csv")
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No PBP files found at {pattern}")
    dfs = []
    for f in files:
        df = pd.read_csv(f, dtype=str)
        df = df[[c for c in PBP_COLS if c in df.columns]]
        dfs.append(df)
    pbp = pd.concat(dfs, ignore_index=True)

    # normalize keys (allow deriving nflverse from game_id if necessary)
    pbp = norm_keys_on_both(pbp, must_have_nflverse=False)
    if "nflverse_game_id" not in pbp.columns:
        raise KeyError("PBP lacks 'nflverse_game_id' and couldn't derive it from 'game_id'.")

    # strict-ish pass filter
    pbp["pass_attempt"] = pd.to_numeric(pbp.get("pass_attempt", 0), errors="coerce").fillna(0).astype(int)
    pbp["qb_dropback"]  = pd.to_numeric(pbp.get("qb_dropback", 0),  errors="coerce").fillna(0).astype(int)
    pbp["play_type"]    = pbp.get("play_type", "").str.lower()
    pbp["down"]         = pd.to_numeric(pbp.get("down"), errors="coerce")

    is_pass = (pbp["pass_attempt"] == 1) | (pbp["qb_dropback"] == 1) | (pbp["play_type"] == "pass")

    # exclude penalties/no-plays if present
    if "penalty" in pbp.columns:
        pbp["penalty"] = pd.to_numeric(pbp["penalty"], errors="coerce").fillna(0).astype(int)
        is_pass &= pbp["penalty"] == 0
    if "no_play" in pbp.columns:
        pbp["no_play"] = pd.to_numeric(pbp["no_play"], errors="coerce").fillna(0).astype(int)
        is_pass &= pbp["no_play"] == 0

    # require basic context (down not NA)
    pbp = pbp[is_pass & pbp["down"].notna()].copy()

    # drop helper cols
    pbp = pbp.drop(columns=["pass_attempt","play_type","penalty","no_play"], errors="ignore")

    # final key cleanup
    pbp = pbp.dropna(subset=["nflverse_game_id","play_id"])
    return pbp

def load_participation_year(year: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"pbp_participation_{year}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Participation file not found: {path}")
    part = pd.read_csv(path, dtype=str)
    part = part[[c for c in PART_COLS if c in part.columns]]
    part = norm_keys_on_both(part, must_have_nflverse=True)
    part = part.dropna(subset=["nflverse_game_id","play_id"]).drop_duplicates(subset=["nflverse_game_id","play_id"])
    return part

# New Gen stats positions. build a (season, player_short_name) -> player_position map
def load_ngs_positions_year(year: str) -> pd.DataFrame:
    """
    Load Next Gen receiving and rushing for the given year and return a map:
    ['season','player_short_name','receiver_position'].
    Receiving takes precedence; rushing fills gaps.
    """
    rec_path = os.path.join(DATA_DIR, f"nextgen_receiving_{year}.csv")
    rush_path = os.path.join(DATA_DIR, f"nextgen_rushing_{year}.csv")

    frames = []
    if os.path.exists(rec_path):
        rec = pd.read_csv(rec_path, dtype=str, usecols=lambda c: c in {"season","player_short_name","player_position"})
        rec = rec.rename(columns={"player_position": "receiver_position"})
        frames.append(rec)
    if os.path.exists(rush_path):
        rush = pd.read_csv(rush_path, dtype=str, usecols=lambda c: c in {"season","player_short_name","player_position"})
        rush = rush.rename(columns={"player_position": "receiver_position"})
        frames.append(rush)

    if not frames:
        # Return empty frame with expected columns; merge will just be NaNs
        return pd.DataFrame(columns=["season","player_short_name","receiver_position"])

    # Concat with RECEIVING FIRST so WR/TE wins; drop duplicates on player_short_name keeping first
    ngs = pd.concat(frames, ignore_index=True)
    # Keep only rows for this season (some files may include season column already correct)
    ngs["season"] = pd.to_numeric(ngs["season"], errors="coerce").astype("Int64")
    ngs = ngs[ngs["season"] == int(year)].copy()
    ngs["player_short_name"] = ngs["player_short_name"].astype(str).str.strip()

    # Prefer first occurrence (receiving) then fill from rushing
    ngs = ngs.dropna(subset=["player_short_name"]).drop_duplicates(subset=["player_short_name"], keep="first")

    return ngs[["season","player_short_name","receiver_position"]]


def build_pass_frame(year: str) -> pd.DataFrame:
    pbp  = load_pbp_year(year)
    part = load_participation_year(year)
    ngs  = load_ngs_positions_year(year)

    # re-normalize defensively (strip, types)
    for df in (pbp, part):
        df["nflverse_game_id"] = df["nflverse_game_id"].astype(str).str.strip()
        df["play_id"] = to_int_play_id(df["play_id"])

    merged = pbp.merge(part, on=["nflverse_game_id","play_id"], how="left")

    # New Gen stats positions: parse season and join receiver position
    merged["season"] = pd.to_numeric(merged["nflverse_game_id"].str.split("_", n=1).str[0], errors="coerce").astype("Int64")
    # receiver in PBP already matches NGS player_short_name format (e.g., 'D.Hopkins', 'R.Mostert')
    merged["receiver"] = merged["receiver"].astype(str).str.strip()

    if not ngs.empty:
        merged = merged.merge(
            ngs,
            left_on=["season","receiver"],
            right_on=["season","player_short_name"],
            how="left"
        ).drop(columns=["player_short_name"], errors="ignore")
        # receiver_position now present (or NaN if unknown)
    else:
        merged["receiver_position"] = pd.NA

    # simple match-rate report
    if "offense_personnel" in merged.columns:
        match_rate = merged["offense_personnel"].notna().mean()
    else:
        # fall back to any participation field that exists
        part_cols_present = [c for c in ["possession_team","offense_formation","offense_personnel","route"] if c in merged.columns]
        match_rate = merged[part_cols_present].notna().any(axis=1).mean() if part_cols_present else 0.0

        # quick receiver-position coverage
    pos_cov = merged["receiver_position"].notna().mean()
    print(f"[{year}] rows: {len(merged):,}  participation match: {match_rate:.1%}  receiver_position coverage: {pos_cov:.1%}")

    missing_with_name = merged["receiver"].notna() & (merged["receiver"].str.strip() != "") & merged["receiver_position"].isna()
    print(f"Dropping {missing_with_name.sum():,} rows because NGS had no receiver_position for those names.")
    merged = merged[~missing_with_name].copy()
    print(f"[{year}] final rows after drop: {len(merged):,}")

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
    YEARS = ["2024"]  # or ["2020","2021","2022","2023","2024"]
    build_and_save(YEARS, out_name="merged_pass_model_data_2024.csv")

    # returns giant dataframe in csv stored in data folder.