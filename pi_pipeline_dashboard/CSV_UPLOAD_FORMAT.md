# PI Pipeline CSV Upload Format

This describes the exact CSV schema the dashboard's **Data Entry → Upload a
filled-in CSV** feature expects. Use this if you're generating or transforming
a CSV programmatically (e.g. an agent producing a pipeline export) for import
into the dashboard.

A blank, correctly-headed starting point is checked in at
`data/pipeline_template_blank.csv`.

## Ground rules

- **File type:** `.csv`, UTF-8, comma-delimited, one header row.
- **Only `Firm` is required.** Every other column is optional — if it's
  missing from your CSV entirely, it's created blank for every row. If a cell
  within an included column is blank, that's fine too.
- **Column names must match exactly** (case and spacing), including the `/`
  in `Execution/Strategy Adherence`. See the table below.
- **Extra columns are tolerated, not rejected.** Anything not in the schema
  is silently dropped, and the app shows a one-line warning naming what it
  ignored. It does not stop the upload.
- **Row order doesn't matter.** The app sorts on demand per exhibit.
- Uploading offers **Replace all existing data** or **Append to existing
  data** — this doc only covers the shape of the file itself.

## Column reference

| Column | Required | Type | Allowed values | Notes |
|---|---|---|---|---|
| `Firm` | **Yes** | text | free text | The only required field. Rows with a blank `Firm` are dropped silently. |
| `Stage` | No | text (pick one) | `1. Top emerging idea`, `1. Core idea`, `2. Evaluate`, `3. Follow passively`, `4. Pass` | This is the **conviction ranking** — `1. Top emerging idea` and `1. Core idea` are both top conviction, tied; `4. Pass` is lowest. Must match one of these strings exactly to sort/filter/edit correctly (see "Values outside the list" below). |
| `Asset Class` | No | text (pick one) | `Venture`, `Growth`, `Buyout`, `Credit`, `Venture secondaries` | |
| `Sub Asset Class` | No | free text | e.g. `Multi Stage`, `Early Stage`, `Direct lending`, `Megacap`, `Seed` | Not constrained to a fixed list — existing data has ~19 distinct values with inconsistent casing (e.g. both `Multi Stage` and `Multi stage` appear). Pick one casing convention for new rows. |
| `Sector` | No | free text | e.g. `Generalist`, `Biotech`, `Tech`, `Healthcare` | Free text, can be a comma-separated combination like `Consumer, Tech`. |
| `Geography` | No | text (pick one) | `US`, `Europe`, `Global`, `LatAm`, `US, Europe`, `US, Israel` | This is the **conviction/geo exhibit's** grouping field — sidebar geography filter is built dynamically from whatever's in the data, so off-list values still show up as their own filter option (unlike `Stage`/`Asset Class`/`Source`/`Fundraising Status`, whose filters are fixed lists). |
| `Client Invested` | No | boolean | `True`/`False`, `Y`/`N`, `Yes`/`No`, `1`/`0` (case-insensitive) | Anything not recognized as true (see values above) is treated as `False`, including a blank cell. |
| `Source` | No | text (pick one) | `GIR`, `GIR/Client`, `GIR/Prospect`, `Client`, `Prospect`, `Manager`, `Spin out`, `Portfolio company`, `Internal Contact` | How the firm entered the pipeline. |
| `HQ` | No | free text | — | Not populated in the seed data; free text. |
| `Fundraising Status` | No | text (pick one) | `Unknown`, `Not Currently Raising`, `Raising - Early Stage`, `Raising - Final Close`, `Recently Closed` | Drives the Fundraising Timeline exhibit's status breakdown. |
| `Raise Start Date` | No | date | `YYYY-MM-DD` recommended | When the raise began. Together with `Target Close Date`, this sets how long the bar spans on the Fundraising Timeline / Forward Calendar Gantt charts. If left blank, that firm's chart bar falls back to a one-day marker at `Target Close Date` instead of a real span. |
| `Target Close Date` | No | date | `YYYY-MM-DD` recommended | Pandas will parse most common date formats, but ISO (`2026-09-01`) is the only one guaranteed unambiguous. Blank = no date. Drives the Fundraising Timeline sort/chart. |
| `Next Follow Up Date` | No | date | `YYYY-MM-DD` recommended | Same format rules as `Target Close Date`. |
| `On Forward Calendar` | No | boolean | `True`/`False`, `Y`/`N`, `Yes`/`No`, `1`/`0` (case-insensitive) | Whether the firm is on the manually-curated Forward Calendar exhibit. Normally set by dragging in the Forward Calendar tab, not by CSV — but settable here too if pre-populating a calendar. |
| `Access` | No | free text | e.g. `Strong`, `Medium`, `Weak`, or blank | Conviction sub-score; not populated in the seed data. |
| `Track Record` | No | free text | e.g. `Strong`, `Medium`, `Weak`, or blank | Conviction sub-score; not populated in the seed data. |
| `Type of Risk` | No | free text | — | Conviction sub-score; not populated in the seed data. |
| `Execution/Strategy Adherence` | No | free text | — | Conviction sub-score; not populated in the seed data. |
| `Commentary` | No | free text | — | Free-form notes. Commas/quotes are fine — just make sure the CSV is properly quoted (standard `csv` writers handle this automatically). |
| `Last Updated` | No | date | `YYYY-MM-DD` | If left blank, the app stamps it with today's date the next time that row is saved via the in-app editor — you don't need to set it yourself on upload. |

## Values outside the fixed lists

`Stage`, `Asset Class`, `Source`, and `Fundraising Status` populate their
sidebar filter dropdowns from a **fixed list** (the "Allowed values" above),
not from whatever's actually in the data. A row with a value outside that
list won't crash anything and will still display in unfiltered views, but:

- it can't be selected via that field's sidebar filter,
- it won't necessarily line up with the color/order conventions the charts
  use (e.g. the conviction ordering and colors are keyed off the exact
  `Stage` strings).

`Geography` is the exception — its sidebar filter is built from whatever
values are present in the data, so off-list geographies still work fully.

**Recommendation for an agent generating this CSV:** always emit the exact
strings from the "Allowed values" column above for `Stage`, `Asset Class`,
`Source`, and `Fundraising Status`. Free-text columns (`Sub Asset Class`,
`Sector`, `HQ`, `Commentary`, the conviction sub-scores) have no such
constraint.

## Example row

```csv
Firm,Stage,Asset Class,Sub Asset Class,Sector,Geography,Client Invested,Source,HQ,Fundraising Status,Raise Start Date,Target Close Date,Next Follow Up Date,On Forward Calendar,Access,Track Record,Type of Risk,Execution/Strategy Adherence,Commentary,Last Updated
Example Capital Partners,1. Core idea,Venture,Multi Stage,Generalist,US,Y,GIR,New York,Raising - Early Stage,2026-07-01,2026-11-15,2026-09-01,N,Strong,Strong,,,"Top idea, strong partnership, no near-term concerns",2026-07-23
```

Minimal valid row (only the required column):

```csv
Firm
Example Capital Partners
```
