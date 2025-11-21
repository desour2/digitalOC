import pandas as pd
import numpy as np
from typing import Dict, Any, List

def add_additional_pbp_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add extra situational / contextual features for PBP data.
    All ops are guarded so missing columns won't break anything.
    Returns a copy with new columns added.
    """
    df_out: pd.DataFrame = df.copy()

    # --- Time-pressure style features ---
    if "quarter_seconds_remaining" in df_out.columns:
        df_out["time_left_fraction_qtr"] = (
            df_out["quarter_seconds_remaining"] / 900.0
        )

    if "half_seconds_remaining" in df_out.columns:
        df_out["time_left_fraction_half"] = (
            df_out["half_seconds_remaining"] / 1800.0
        )

    if "game_seconds_remaining" in df_out.columns:
        df_out["time_left_fraction_game"] = (
            df_out["game_seconds_remaining"] / 3600.0
        )

    # --- Score / game state enhancements ---
    if "score_differential" in df_out.columns:
        df_out["score_diff_sign"] = np.sign(df_out["score_differential"])
        df_out["pos_team_ahead"] = (df_out["score_differential"] > 0).astype(int)
        df_out["one_score_game_flag"] = (
            df_out["score_differential"].abs() <= 8
        ).astype(int)

    if (
        "score_differential_post" in df_out.columns
        and "score_differential" in df_out.columns
    ):
        df_out["score_diff_change"] = (
            df_out["score_differential_post"] - df_out["score_differential"]
        )

    # --- Field + distance interactions ---
    if "ydstogo" in df_out.columns and "yardline_100" in df_out.columns:
        df_out["short_and_redzone"] = (
            (df_out["ydstogo"] <= 2) & (df_out["yardline_100"] <= 20)
        ).astype(int)

        df_out["long_and_backed_up"] = (
            (df_out["ydstogo"] >= 10) & (df_out["yardline_100"] >= 80)
        ).astype(int)

    # --- Late & close combo flag ---
    if (
        "qtr" in df_out.columns
        and "game_seconds_remaining" in df_out.columns
        and "score_differential" in df_out.columns
    ):
        late_mask: pd.Series = df_out["game_seconds_remaining"] <= 600
        q4_plus_mask: pd.Series = df_out["qtr"] >= 4
        close_mask: pd.Series = df_out["score_differential"].abs() <= 8

        df_out["late_and_close"] = (
            late_mask & q4_plus_mask & close_mask
        ).astype(int)

    # --- Motion / play-action / RPO style indicators ---
    # These columns show up in some pbp datasets; we turn them into clean 0/1 flags.
    motion_like_cols: List[str] = [
        "play_action",
        "motion",
        "qb_dropback",
        "run_pass_option",
    ]

    for col in motion_like_cols:
        if col in df_out.columns:
            series = df_out[col]

            # Handle bool vs numeric vs object safely
            if pd.api.types.is_bool_dtype(series):
                df_out[f"{col}_flag"] = series.fillna(False).astype(int)
            else:
                # convert non-null values to 1 if non-zero / non-empty, else 0
                df_out[f"{col}_flag"] = (
                    series.fillna(0)
                    .astype(float)
                    .ne(0.0)
                    .astype(int)
                )

    # --- Drive-based context ---
    # nflfastR uses 'drive_play_number'; if present, reuse it.
    if "drive_play_number" in df_out.columns:
        df_out["drive_play_count"] = df_out["drive_play_number"]

    if "drive_play_count" in df_out.columns:
        df_out["first_play_of_drive"] = (df_out["drive_play_count"] == 1).astype(int)
        df_out["early_drive"] = (df_out["drive_play_count"] <= 3).astype(int)
        df_out["long_drive_flag"] = (df_out["drive_play_count"] >= 8).astype(int)

    # --- Win probability buckets if available ---
    if "wp" in df_out.columns:
        # Keep wp numeric, but also bucketed for non-linear effects
        df_out["wp_bucket"] = pd.cut(
            df_out["wp"],
            bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0000001],
            labels=[
                "very_low_wp",
                "low_wp",
                "mid_wp",
                "high_wp",
                "very_high_wp",
            ],
            include_lowest=True,
        )

    return df_out