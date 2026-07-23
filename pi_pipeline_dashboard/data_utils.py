"""Load/save helpers for the pipeline CSV, plus normalization shared with CSV upload."""

import os
import pandas as pd

from constants import (
    CLIENT_LIST_DELIMITER,
    CLIENT_OPTIONS,
    COLUMNS,
    DATA_PATH,
    DATE_COLUMNS,
    FORWARD_CAL_ORDER_COLUMNS,
    LIST_COLUMNS,
)


def _parse_client_list(v) -> list[str]:
    if isinstance(v, list):
        return v
    if not v or not str(v).strip():
        return []
    return [p.strip() for p in str(v).split(CLIENT_LIST_DELIMITER) if p.strip()]


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""

    for col in LIST_COLUMNS:
        df[col] = df[col].apply(_parse_client_list)

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in FORWARD_CAL_ORDER_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

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

    if "Clients Invested" in raw.columns:
        rogue = set()
        for v in raw["Clients Invested"]:
            rogue.update(c for c in _parse_client_list(v) if c not in CLIENT_OPTIONS)
        if rogue:
            warnings.append(
                f"'Clients Invested' has values outside {CLIENT_OPTIONS}: "
                f"{sorted(rogue)} (kept as-is, but won't match any client view)"
            )

    return _normalize(raw), warnings


def blank_template() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def save_data(df: pd.DataFrame, path: str = DATA_PATH) -> None:
    out = df.copy()
    out = out[out["Firm"].astype(str).str.strip() != ""]
    for col in DATE_COLUMNS:
        out[col] = pd.to_datetime(out[col], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")
    for col in LIST_COLUMNS:
        out[col] = out[col].apply(
            lambda lst: CLIENT_LIST_DELIMITER.join(lst) if isinstance(lst, list) else (lst or "")
        )
    for col in FORWARD_CAL_ORDER_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out[col] = out[col].apply(lambda v: "" if pd.isna(v) else str(int(v)))
    out.to_csv(path, index=False)


def stage_sort_key(df: pd.DataFrame) -> pd.Series:
    from constants import STAGE_RANK

    return df["Stage"].map(lambda s: STAGE_RANK.get(s, 99))


def client_invested_mask(df: pd.DataFrame, client: str, global_client: str) -> pd.Series:
    """True where `client` counts as invested for the current client view.

    Global view: True if ANY client is invested. A specific client view:
    True only if that exact client is in the firm's Clients Invested list.
    """
    if client == global_client:
        return df["Clients Invested"].apply(len) > 0
    return df["Clients Invested"].apply(lambda lst: client in lst)
