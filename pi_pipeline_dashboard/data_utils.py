"""Load/save helpers for the pipeline CSV."""

import os
import pandas as pd

from constants import COLUMNS, DATE_COLUMNS, DATA_PATH


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    if not os.path.exists(path):
        df = pd.DataFrame(columns=COLUMNS)
    else:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""

    df["Client Invested"] = df["Client Invested"].apply(_to_bool)

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df[COLUMNS]


def save_data(df: pd.DataFrame, path: str = DATA_PATH) -> None:
    out = df.copy()
    out = out[out["Firm"].astype(str).str.strip() != ""]
    for col in DATE_COLUMNS:
        out[col] = pd.to_datetime(out[col], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    out["Client Invested"] = out["Client Invested"].apply(lambda v: bool(v))
    out.to_csv(path, index=False)


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "y", "yes")


def stage_sort_key(df: pd.DataFrame) -> pd.Series:
    from constants import STAGE_RANK

    return df["Stage"].map(lambda s: STAGE_RANK.get(s, 99))
