from typing import Dict, Tuple, List, Optional
import pandas as pd
import re
from collections import Counter

# ---------- Parsing helpers ----------

_POS_OFF: Tuple[str, ...] = ("RB", "TE", "WR")
_POS_DEF: Tuple[str, ...] = ("DL", "LB", "DB")

_OFF_REGEX: re.Pattern[str] = re.compile(r"(\d+)\s*(RB|TE|WR)", flags=re.IGNORECASE)
_DEF_REGEX: re.Pattern[str] = re.compile(r"(\d+)\s*(DL|LB|DB)", flags=re.IGNORECASE)

def _parse_counts(s: Optional[str], pat: re.Pattern[str], keys: Tuple[str, ...]) -> Dict[str, int]:
    counts: Dict[str, int] = {k: 0 for k in keys}
    if not isinstance(s, str) or not s:
        return counts
    for num_str, label in pat.findall(s.upper()):
        try:
            counts[label] += int(num_str)
        except ValueError:
            continue
    return counts

def parse_off_personnel(s: Optional[str]) -> Tuple[int, int, int, str]:
    """
    Returns (rb, te, wr, off_group), off_group like '11','12','21', or 'UNK'.
    Expects strings like '1 RB, 1 TE, 3 WR'.
    """
    counts = _parse_counts(s, _OFF_REGEX, _POS_OFF)
    rb: int = counts["RB"]
    te: int = counts["TE"]
    wr: int = counts["WR"]
    grp: str = f"{rb}{te}" if (rb or te) else "UNK"
    return rb, te, wr, grp

def parse_def_personnel_simple(s: Optional[str]) -> Tuple[int, int, int, str]:
    """
    Returns (dl, lb, db, def_group), def_group like '4-2-5' or 'UNK'.
    Expects strings already collapsed to 'DL/LB/DB' buckets.
    """
    counts = _parse_counts(s, _DEF_REGEX, _POS_DEF)
    dl: int = counts["DL"]
    lb: int = counts["LB"]
    db: int = counts["DB"]
    grp: str = f"{dl}-{lb}-{db}" if (dl or lb or db) else "UNK"
    return dl, lb, db, grp

# ---------- 2023+ defensive normalization ----------
# Map granular positions to DL/LB/DB buckets
_DEF_POS_MAP: Dict[str, str] = {
    # DL
    "DE": "DL", "DT": "DL", "NT": "DL", "EDGE": "DL",
    # LB
    "LB": "LB", "ILB": "LB", "MLB": "LB", "OLB": "LB",
    # DB
    "DB": "DB", "CB": "DB", "FS": "DB", "SS": "DB", "NB": "DB", "SAF": "DB",
}

_MISC_BAD = {"K", "P", "LS", "QB", "RB", "WR", "FB", "TE"}  # filter ST/offense weirdness

_TOKEN_RE: re.Pattern[str] = re.compile(r"(\d+)\s*([A-Z]+)")

def normalize_def_personnel_to_buckets(s: Optional[str]) -> Optional[str]:
    """
    Convert verbose strings like '3 CB, 2 DE, 2 DT, 1 FS, 1 ILB, 1 MLB, 1 SS'
    into '4 DL, 2 LB, 5 DB'. Returns None if cannot parse.
    """
    if not isinstance(s, str) or not s:
        return None
    parts = _TOKEN_RE.findall(s.upper())
    if not parts:
        return None

    c: Counter[str] = Counter()
    for n_str, pos in parts:
        if pos in _MISC_BAD:
            # skip special teams / offensive players that leak into defense_personnel
            continue
        bucket = _DEF_POS_MAP.get(pos)
        if not bucket:
            # Unknown label; skip it rather than crashing
            continue
        c[bucket] += int(n_str)

    if sum(c.values()) == 0:
        return None

    dl = c.get("DL", 0)
    lb = c.get("LB", 0)
    db = c.get("DB", 0)
    return f"{dl} DL, {lb} LB, {db} DB"


def add_personnel_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Requires columns:
      - 'personnel_off'  (e.g., '1 RB, 1 TE, 3 WR')
      - 'personnel_def'  (either already 'DL/LB/DB' or verbose we'll normalize)
    Produces:
      off_rb, off_te, off_wr, off_group,
      def_dl, def_lb, def_db, def_group,
      off_empty, off_heavy, def_nickel, def_dime
    """
    out = df.copy()

    if "personnel_off" not in out.columns:
        out["personnel_off"] = None
    if "personnel_def" not in out.columns:
        out["personnel_def"] = None

    # Normalize defense personnel if it looks verbose (CB/FS/DE/etc.)
    needs_norm = out["personnel_def"].astype("string").str.contains(r"\b(CB|FS|SS|DE|DT|NT|ILB|MLB|OLB|EDGE|NB|SAF)\b", na=False)
    out.loc[needs_norm, "personnel_def"] = out.loc[needs_norm, "personnel_def"].map(normalize_def_personnel_to_buckets)

    # Offense parse
    off_cols = out["personnel_off"].apply(parse_off_personnel).apply(pd.Series)
    off_cols.columns = ["off_rb", "off_te", "off_wr", "off_group"]

    # Defense parse (simple DL/LB/DB)
    def_cols = out["personnel_def"].apply(parse_def_personnel_simple).apply(pd.Series)
    def_cols.columns = ["def_dl", "def_lb", "def_db", "def_group"]

    out = pd.concat([out, off_cols, def_cols], axis=1)

    # Derived flags
    out["off_empty"] = (out["off_rb"] == 0).astype(int)
    out["off_heavy"] = ((out["off_te"] >= 2) | (out["off_rb"] >= 2) | (out["off_wr"] <= 2)).astype(int)
    out["def_nickel"] = (out["def_db"] == 5).astype(int)
    out["def_dime"] = (out["def_db"] >= 6).astype(int)

    out["off_group"] = out["off_group"].astype("string")
    out["def_group"] = out["def_group"].astype("string")

    return out


if __name__ == "__main__":
    pbp: pd.DataFrame = pd.read_csv("data/pbp_2024_0.csv")
    part: pd.DataFrame = pd.read_csv("data/pbp_participation_2024.csv")

    key_cols = ["old_game_id", "play_id"]
    keep_cols = key_cols + [
        "posteam","defteam","down","ydstogo","yards_gained","play_type"
    ]
    pbp_small = pbp[keep_cols].copy()

    part_renamed = part.rename(columns={
        "offense_personnel": "personnel_off",
        "defense_personnel": "personnel_def"
    })

    merged = pd.merge(
        part_renamed,
        pbp_small,
        on=key_cols,
        how="left"
    )

    merged = merged[merged["play_type"].isin(["run", "pass"])]

    feats = add_personnel_features(merged)

    cols_to_show: List[str] = [
        "posteam","defteam",
        "personnel_off","off_group","off_rb","off_te","off_wr","off_heavy","off_empty",
        "personnel_def","def_group","def_dl","def_lb","def_db","def_nickel","def_dime",
        "down","ydstogo","yards_gained","play_type"
    ]
    print(feats[cols_to_show].head(10))
