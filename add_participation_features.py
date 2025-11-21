import pandas as pd

def add_participation_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add extra participation-derived features if they exist.
    """
    df_out = df.copy()

    if "number_of_pass_rushers" in df_out.columns:
        df_out["num_pass_rushers"] = df_out["number_of_pass_rushers"].fillna(0).astype(float)

    if "defense_man_zone_type" in df_out.columns:
        df_out["defense_man_zone_type"] = (
            df_out["defense_man_zone_type"]
            .fillna("UNKNOWN")
            .str.upper()
        )

    if "defense_coverage_type" in df_out.columns:
        df_out["defense_coverage_type"] = (
            df_out["defense_coverage_type"]
            .fillna("UNKNOWN")
            .str.upper()
        )

    if "n_offense" in df_out.columns and "n_defense" in df_out.columns:
        df_out["total_players"] = (
            df_out["n_offense"].fillna(11) + df_out["n_defense"].fillna(11)
        )

    if "time_to_throw" in df_out.columns:
        df_out["time_to_throw"] = df_out["time_to_throw"].fillna(0)

    if "was_pressure" in df_out.columns:
        df_out["pressure_flag"] = df_out["was_pressure"].fillna(False).astype(int)

    return df_out
