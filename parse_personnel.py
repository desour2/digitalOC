# personnel_features.py

from typing import Dict, Tuple, Optional
import re
from collections import Counter
import pandas as pd

_POS_OFF: Tuple[str, ...] = ("RB", "TE", "WR")
_POS_DEF: Tuple[str, ...] = ("DL", "LB", "DB")

_OFF_REGEX: re.Pattern[str] = re.compile(r"(\d+)\s*(RB|TE|WR)", flags=re.IGNORECASE)
_DEF_REGEX: re.Pattern[str] = re.compile(r"(\d+)\s*(DL|LB|DB)", flags=re.IGNORECASE)
_TOKEN_RE: re.Pattern[str] = re.compile(r"(\d+)\s*([A-Z]+)")

_DEF_POS_MAP: Dict[str, str] = {
    "DE": "DL", "DT": "DL", "NT": "DL", "EDGE": "DL",
    "LB": "LB", "ILB": "LB", "MLB": "LB", "OLB": "LB",
    "DB": "DB", "CB": "DB", "FS": "DB", "SS": "DB", "NB": "DB", "SAF": "DB",
}
_MISC_BAD: set[str] = {"K", "P", "LS", "QB", "RB", "WR", "FB", "TE"}


def _parse_counts(
    s: Optional[str],
    pat: re.Pattern[str],
    keys: Tuple[str, ...],
) -> Dict[str, int]:
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
    counts: Dict[str, int] = _parse_counts(s, _OFF_REGEX, _POS_OFF)
    rb: int = counts["RB"]
    te: int = counts["TE"]
    wr: int = counts["WR"]
    grp: str = f"{rb}{te}" if (rb or te) else "UNK"
    return rb, te, wr, grp


def parse_def_personnel_simple(s: Optional[str]) -> Tuple[int, int, int, str]:
    counts: Dict[str, int] = _parse_counts(s, _DEF_REGEX, _POS_DEF)
    dl: int = counts["DL"]
    lb: int = counts["LB"]
    db: int = counts["DB"]
    grp: str = f"{dl}-{lb}-{db}" if (dl or lb or db) else "UNK"
    return dl, lb, db, grp


def normalize_def_personnel_to_buckets(s: Optional[str]) -> Optional[str]:
    """
    Normalize verbose defensive personnel strings
    (e.g., '3 CB, 2 DE...') into '4 DL, 2 LB, 5 DB'.
    """
    if not isinstance(s, str) or not s:
        return None
    parts = _TOKEN_RE.findall(s.upper())
    if not parts:
        return None

    c: Counter[str] = Counter()
    for n_str, pos in parts:
        if pos in _MISC_BAD:
            continue
        bucket: Optional[str] = _DEF_POS_MAP.get(pos)
        if not bucket:
            continue
        try:
            c[bucket] += int(n_str)
        except ValueError:
            continue

    if sum(c.values()) == 0:
        return None

    dl: int = c.get("DL", 0)
    lb: int = c.get("LB", 0)
    db: int = c.get("DB", 0)
    return f"{dl} DL, {lb} LB, {db} DB"


def simplify_off_group(g: str) -> str:
    if g in {"10", "11"}:
        return "spread"
    if g in {"12", "13", "22"}:
        return "heavy"
    if g == "00":
        return "empty"
    return "other"


def simplify_def_group(g: str) -> str:
    if g in {"4-3-4", "3-4-4"}:
        return "base"
    if g in {"4-2-5", "3-3-5"}:
        return "nickel"
    if g in {"2-3-6", "3-2-6", "4-1-6"}:
        return "dime"
    return "other"


def add_personnel_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add parsed and engineered offensive/defensive personnel features.

    Assumes df has:
      - 'personnel_off' (or you renamed offense_personnel to this)
      - 'personnel_def' (or you renamed defense_personnel to this)
    """
    out: pd.DataFrame = df.copy()

    out["personnel_off"] = out.get("personnel_off", None)
    out["personnel_def"] = out.get("personnel_def", None)

    needs_norm = out["personnel_def"].astype("string").str.contains(
        r"(?:CB|FS|SS|DE|DT|NT|ILB|MLB|OLB|EDGE|NB|SAF)",
        na=False,
        regex=True,
    )
    out.loc[needs_norm, "personnel_def"] = out.loc[needs_norm, "personnel_def"].map(
        normalize_def_personnel_to_buckets
    )

    off_cols: pd.DataFrame = out["personnel_off"].apply(parse_off_personnel).apply(pd.Series)
    off_cols.columns = ["off_rb", "off_te", "off_wr", "off_group"]

    def_cols: pd.DataFrame = out["personnel_def"].apply(parse_def_personnel_simple).apply(pd.Series)
    def_cols.columns = ["def_dl", "def_lb", "def_db", "def_group"]

    out = pd.concat([out, off_cols, def_cols], axis=1)

    out["off_empty"] = (out["off_rb"] == 0).astype(int)
    out["off_heavy"] = (
        (out["off_te"] >= 2) | (out["off_rb"] >= 2) | (out["off_wr"] <= 2)
    ).astype(int)
    out["def_nickel"] = (out["def_db"] == 5).astype(int)
    out["def_dime"] = (out["def_db"] >= 6).astype(int)

    out["off_group_bucket"] = out["off_group"].astype("string").apply(simplify_off_group)
    out["def_group_bucket"] = out["def_group"].astype("string").apply(simplify_def_group)

    return out
