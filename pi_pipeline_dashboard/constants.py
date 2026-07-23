"""Shared constants for the PI pipeline dashboard: schema, option lists, ordering, and colors."""

DATA_PATH = "data/pipeline_data.csv"

# Conviction / pipeline stage, ordered from highest conviction to pass.
# The source pipeline tracks conviction via the "Stage" field.
STAGE_OPTIONS = [
    "1. Top emerging idea",
    "1. Core idea",
    "2. Evaluate",
    "3. Follow passively",
    "4. Pass",
]
# Numeric rank used for sorting (ties broken alphabetically within a rank).
STAGE_RANK = {
    "1. Top emerging idea": 1,
    "1. Core idea": 1,
    "2. Evaluate": 2,
    "3. Follow passively": 3,
    "4. Pass": 4,
}

ASSET_CLASS_OPTIONS = [
    "Venture",
    "Growth",
    "Buyout",
    "Credit",
    "Venture secondaries",
]

GEOGRAPHY_OPTIONS = [
    "US",
    "Europe",
    "Global",
    "LatAm",
    "US, Europe",
    "US, Israel",
]

SOURCE_OPTIONS = [
    "GIR",
    "GIR/Client",
    "GIR/Prospect",
    "Client",
    "Prospect",
    "Manager",
    "Spin out",
    "Portfolio company",
    "Internal Contact",
]

# Fundraising fields did not exist in the source workbook - added so the team
# can start tracking timelines going forward.
FUNDRAISING_STATUS_OPTIONS = [
    "Unknown",
    "Not Currently Raising",
    "Raising - Early Stage",
    "Raising - Final Close",
    "Recently Closed",
]

CONVICTION_SCORE_OPTIONS = ["", "Strong", "Medium", "Weak"]

DD_STATUS_OPTIONS = [
    "Expected",
    "In Progress (GIR)",
    "In Progress (Team Olympus)",
    "Complete",
    "Unplanned",
]

# Which clients can be marked invested in a firm. "Global" is not a real
# client for investment purposes - it's the sentinel for "don't restrict to
# one client" in the top-left client-view selector. It DOES get its own
# Forward Calendar though, same as any named client.
CLIENT_OPTIONS = ["Olympus Mons", "Gaucho", "Ursa Major", "Orion"]
GLOBAL_CLIENT = "Global"
CLIENT_LIST_DELIMITER = ";"

# Every selectable client view, Global included - used to build one Forward
# Calendar order column per view.
ALL_CLIENT_VIEWS = [GLOBAL_CLIENT] + CLIENT_OPTIONS


def forward_cal_order_col(client: str) -> str:
    return f"Forward Calendar Order: {client}"


FORWARD_CAL_ORDER_COLUMNS = [forward_cal_order_col(c) for c in ALL_CLIENT_VIEWS]

FORWARD_CAL_SORT_OPTIONS = ["Custom order", "Asset Class", "Conviction", "Fundraising Start Date"]

COLUMNS = [
    "Firm",
    "Stage",
    "Asset Class",
    "Sub Asset Class",
    "Sector",
    "Geography",
    "Clients Invested",
    "Source",
    "HQ",
    "Fundraising Status",
    "Raise Start Date",
    "Target Close Date",
    "Next Follow Up Date",
    *FORWARD_CAL_ORDER_COLUMNS,
    "Due Diligence (DD)",
    "Access",
    "Track Record",
    "Type of Risk",
    "Execution/Strategy Adherence",
    "Commentary",
    "Last Updated",
]

DATE_COLUMNS = ["Raise Start Date", "Target Close Date", "Next Follow Up Date", "Last Updated"]
LIST_COLUMNS = ["Clients Invested"]

# Validated categorical palette (dataviz skill default), fixed order - never cycled.
PALETTE = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
}
CATEGORICAL_SEQUENCE = list(PALETTE.values())
SEQUENTIAL_BLUE = "#2a78d6"

STAGE_COLOR_MAP = {
    "1. Top emerging idea": PALETTE["blue"],
    "1. Core idea": PALETTE["aqua"],
    "2. Evaluate": PALETTE["yellow"],
    "3. Follow passively": PALETTE["orange"],
    "4. Pass": PALETTE["red"],
}
