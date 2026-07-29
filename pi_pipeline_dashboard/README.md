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

This opens at `http://localhost:5000` (port and bind address are set in
`.streamlit/config.toml`). Data lives in `data/pipeline_data.csv` and is
edited in place from the app (or by hand, since it's a plain CSV).

Running behind a remote Jupyter/JupyterHub server? `localhost` in your
browser never reaches it — see the note at the bottom of this file.

## Client view

A **Client view** selector sits in the top-left corner of the page, above the
title: **Global** plus one entry per client (`Olympus Mons`, `Gaucho`, `Ursa
Major`, `Orion`). It controls what "Client Invested" means everywhere else in
the app — the sidebar filter, the Overview metric, and PPTX footnotes:

- Pick a specific client and "Client Invested" checks whether *that* client
  is in the firm's `Clients Invested` list.
- Pick **Global** and "Client Invested" means *any* client is in the list.

This is a page-level setting, not a per-tab filter — it's meant for building
out one client's view of the pipeline at a time (see Forward Calendar below).

## Tabs

- **Data Entry** — an editable grid of every firm (add rows, edit in place,
  delete rows), with dropdowns for the categorical fields and a tag/chip
  editor for `Clients Invested`. Click **Save changes** to write back to the
  CSV.
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
  fundraising status and a Gantt-style chart once dates are entered. Bars span
  each firm's actual raise window (`Raise Start Date` to `Target Close
  Date`); a firm with only a `Target Close Date` gets a one-day marker
  instead of a real span.
- **Forward Calendar** — a manually curated set of firms, built by
  drag-and-drop rather than by filtering. See below.

A filter panel in the sidebar — stage, asset class, sector, geography, HQ,
source, due diligence status, fundraising status, client-invested, and a
text search — applies to every exhibit tab. Sector, geography, and HQ build
their option lists from whatever's actually in the data; stage, asset
class, source, due diligence, and fundraising status use fixed lists (see
[`CSV_UPLOAD_FORMAT.md`](CSV_UPLOAD_FORMAT.md) for the exact values). The
Data Entry tab always shows the full, unfiltered dataset so nothing is
hidden while editing.

## Forward Calendar

Unlike the other exhibits, which just show whatever the sidebar filters
currently match, the Forward Calendar is a **manually curated** set of firms
that persists independent of the filters:

**Every client view has its own, independent Forward Calendar — Global
included.** The calendar you see and edit is whichever one matches the
top-left **Client view** selector; switching it swaps in that client's
calendar (membership, custom order, and the Gantt chart all change to
match), completely independent of every other client's.

1. Pick a client at top-left, filter the sidebar down to whatever you're
   looking for (e.g. search "US" in Geography, or a Stage), open the
   **Forward Calendar** tab, and drag a few firms from **Filtered results**
   into **Forward Calendar** — this builds *that client's* calendar.
2. Change the sidebar filters to a different search and drag more firms in —
   the calendar keeps everything already added, regardless of what the
   filter currently shows.
3. Switch **Client view** to a different client (or Global) to build *their*
   calendar the same way — it starts from whatever that client already has
   (empty, the first time), completely separate from the one you just built.
4. Drag a firm out of the current client's **Forward Calendar** (back into
   **Filtered results**) to remove it, drag within it to reorder, or use
   **Clear \<Client\>'s Forward Calendar** to empty just that one client's
   calendar.

Membership *and* custom order for each client are stored in that client's
own `Forward Calendar Order: <Client>` column (blank = not on that client's
calendar; `0`, `1`, `2`, … otherwise), so everything survives app restarts
and switching clients back and forth. Each is also directly editable as a
number in Data Entry (one column per client), though dragging is the normal
way to set it.

Below the drag-and-drop board, a **Sort by** toggle controls the order of the
Gantt chart and the table beneath it, for whichever client's calendar is
active: **Custom order** (default — matches however you last arranged that
client's drag board), **Asset Class**, **Conviction**, or **Fundraising
Start Date**. Switching sort modes doesn't touch the underlying custom
order — it's purely a different way to view the same set of firms.

Sorting by **Asset Class** or **Conviction** adds a dashed divider line
between groups on the Gantt chart, and breaks the table below it into one
sub-table per group (`Venture`, `Growth`, …), so it's clear where one group
ends and the next begins. Custom order and Fundraising Start Date show a
single flat table/chart instead, since there's no discrete group to divide.

## Bulk import

See [`CSV_UPLOAD_FORMAT.md`](CSV_UPLOAD_FORMAT.md) for the full column
reference (required/optional fields, allowed values for `Stage`, `Asset
Class`, `Geography`, etc., date/boolean formatting) — useful if you're
generating an upload CSV programmatically rather than filling it in by hand.

Open **📥 Start from a blank template or bulk-upload a CSV** at the top of the
Data Entry tab:

- **Download blank template** — an empty CSV with the correct headers, to fill
  in outside the app (Excel, Google Sheets, etc.).
- **Upload a filled-in CSV** — parses the file, warns about any unrecognized
  columns, and lets you choose to **replace all existing data** or **append**
  it to what's already there. Only a `Firm` column is required; anything else
  missing is left blank. Nothing is written until you click **Apply upload**.

## Export exhibits to PowerPoint

Each chart-based exhibit tab (**By Conviction**, **By Geography**, **By Asset
Class**, **Fundraising Timeline**) has an **⬇️ Export exhibit to PPTX** button.
It produces a single-slide, intentionally unformatted deck (default
PowerPoint template/colors — meant to be pasted into or restyled within your
own deck) containing:

- the exhibit's data as a **native PowerPoint chart backed by an embedded
  Excel worksheet** (double-click the chart in PowerPoint → "Edit Data in
  Excel" to see/edit the underlying numbers, same as any chart built directly
  in PowerPoint), and
- a **footnote** listing the active Client view, whichever sidebar filters
  were active, and the firm count, e.g. `Filters: Client view = Orion; Stage
  = 1. Core idea, 2. Evaluate | n = 12 firms | Generated 2026-07-23`, so the
  export is self-documenting.

The Fundraising Timeline tab's Gantt-style chart isn't exported — a timeline
isn't a standard Excel/PowerPoint chart type, so that tab exports its
fundraising-status bar chart instead.

## Data model

Seeded from the source pipeline workbook (`Firm`, `Stage`, `Asset Class`, `Sub
Asset Class`, `Sector`, `Geography`, `Source`, `Commentary`), plus these
additions:

- `Clients Invested` — a list of zero or more of `Olympus Mons`, `Gaucho`,
  `Ursa Major`, `Orion` (stored as a `;`-joined string in the CSV; edited as
  tags/chips in Data Entry). Replaces the source workbook's single
  `Client Invested` yes/no column now that there's more than one client to
  track — see [`CSV_UPLOAD_FORMAT.md`](CSV_UPLOAD_FORMAT.md) for the exact
  format. Existing firms were migrated to blank, since the source data had no
  way to say *which* client was invested.
- `HQ`, `Access`, `Track Record`, `Type of Risk`, `Execution/Strategy
  Adherence` — columns present as empty headers in the source workbook, kept
  here for the team to fill in as conviction sub-scores.
- `Fundraising Status`, `Raise Start Date`, `Target Close Date`, `Next
  Follow Up Date` — the source workbook had no fundraising-timeline tracking
  at all, so these are new fields, blank for existing firms. Populate them
  going forward to make the Fundraising Timeline tab useful; `Raise Start
  Date` + `Target Close Date` together are what let its Gantt bars show the
  real length of a raise instead of a one-day marker.
- `Forward Calendar Order: Global`, `Forward Calendar Order: Olympus Mons`,
  `Forward Calendar Order: Gaucho`, `Forward Calendar Order: Ursa Major`,
  `Forward Calendar Order: Orion` — one column per client view, each blank
  or an integer giving the firm's position in *that client's* Forward
  Calendar custom drag order. See the Forward Calendar section above.
- `Due Diligence (DD)` — one of `Expected`, `In Progress (GIR)`, `In Progress
  (Team Olympus)`, `Complete`, `Unplanned`. Tracks where DD stands for the
  firm; has its own sidebar filter.
- `Last Updated` — auto-set to today's date whenever a row is edited and
  saved.

## Notes

- `data/pipeline_data.csv` ships preloaded with 350 synthetic, fictionally-named
  sample funds (randomly generated, not real firms) so the app has something
  to demo against out of the box. A blank version of the same schema is
  checked in at `data/pipeline_template_blank.csv` for anyone who wants a
  template without launching the app.
- The CSV is plain text, so it diffs cleanly in git if you want to version
  pipeline changes over time.

## Running on a remote Jupyter/JupyterHub server

`http://localhost:5000` only works if your browser is on the same machine as
the Streamlit process. On a remote JupyterHub, it isn't — so:

1. Launch it **detached**, so closing the browser tab doesn't kill it:
   ```bash
   cd pi_pipeline_dashboard
   nohup streamlit run app.py > streamlit.log 2>&1 &
   disown
   ```
2. Reach it through the hub's proxy (requires the `jupyter-server-proxy`
   package; `pip install jupyter-server-proxy` if `pip show
   jupyter-server-proxy` comes back empty) at:
   ```
   https://<hub-domain>/user/<your-username>/proxy/5000/
   ```
   (trailing slash required). If that's not an option, tunnel instead:
   `ssh -L 5000:localhost:5000 you@the-server`, then use
   `http://localhost:5000` on your own machine.
