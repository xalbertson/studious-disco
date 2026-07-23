# PI Pipeline Dashboard

A Streamlit app for tracking the private investments pipeline: one tab for data
entry, and exhibit tabs for slicing the pipeline by conviction, geography, asset
class, and fundraising timeline.

## Run it

```bash
cd pi_pipeline_dashboard
pip install -r requirements.txt
streamlit run app.py
```

This opens at `http://localhost:8501`. Data lives in `data/pipeline_data.csv` and
is edited in place from the app (or by hand, since it's a plain CSV).

## Tabs

- **Data Entry** — an editable grid of every firm (add rows, edit in place,
  delete rows), with dropdowns for the categorical fields. Click **Save
  changes** to write back to the CSV.
- **Overview** — headline counts and the full firm list.
- **By Conviction** — firm counts by Stage (the pipeline's conviction ranking:
  `1. Top emerging idea` / `1. Core idea` > `2. Evaluate` > `3. Follow
  passively` > `4. Pass`), broken out by asset class, plus a table sorted by
  conviction.
- **By Geography** — firm counts by geography, plus a table sorted by
  geography.
- **By Asset Class** — firm counts by asset class, plus a table sorted by
  asset class / sub asset class.
- **Fundraising Timeline** — firms sorted by target close date, with a bar of
  fundraising status and a timeline chart once dates are entered.

A filter panel in the sidebar (stage, asset class, geography, fundraising
status, client-invested, and a text search) applies to every exhibit tab.
The Data Entry tab always shows the full, unfiltered dataset so nothing is
hidden while editing.

## Data model

Seeded from the source pipeline workbook (`Firm`, `Stage`, `Asset Class`, `Sub
Asset Class`, `Sector`, `Geography`, `Client Invested`, `Source`,
`Commentary`), plus these additions:

- `HQ`, `Access`, `Track Record`, `Type of Risk`, `Execution/Strategy
  Adherence` — columns present as empty headers in the source workbook, kept
  here for the team to fill in as conviction sub-scores.
- `Fundraising Status`, `Target Close Date`, `Next Follow Up Date` — the
  source workbook had no fundraising-timeline tracking at all, so these are
  new fields, blank for existing firms. Populate them going forward to make
  the Fundraising Timeline tab useful.
- `Last Updated` — auto-set to today's date whenever a row is edited and
  saved.

## Notes

- All 101 firms from the source workbook are preloaded in
  `data/pipeline_data.csv`.
- The CSV is plain text, so it diffs cleanly in git if you want to version
  pipeline changes over time.
