"""Load/save helpers for the pipeline CSV, plus normalization shared with CSV upload."""

import os
import pandas as pd

from constants import COLUMNS, DATE_COLUMNS, DATA_PATH


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["Client Invested"] = df["Client Invested"].apply(_to_bool)

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df[COLUMNS]


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    if not os.path.exists(path):
        df = pd.DataFrame(columns=COLUMNS)
    else:
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return _normalize(df)


def parse_uploaded_csv(file) -> tuple[pd.DataFrame, list[str]]:
    """Parse a user-uploaded CSV into the pipeline schema.

    Returns (normalized_df, warnings). Raises ValueError if the file has no
    'Firm' column, since that's the only truly required field.
    """
    raw = pd.read_csv(file, dtype=str, keep_default_na=False)
    if "Firm" not in raw.columns:
        raise ValueError("The uploaded CSV needs a 'Firm' column.")

    warnings = []
    unknown_cols = [c for c in raw.columns if c not in COLUMNS]
    if unknown_cols:
        warnings.append(f"Ignoring unrecognized columns: {', '.join(unknown_cols)}")

    return _normalize(raw), warnings


def blank_template() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


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
