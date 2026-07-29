# Handoff notes for the next Claude session

Written at the end of a long build session. Read this before diving into
`app.py` cold — it'll save you from re-deriving a few things the hard way.

## What this is

A Streamlit dashboard (`pi_pipeline_dashboard/`) for tracking a private
investments pipeline: a data-entry grid plus several exhibit tabs (By
Conviction, By Geography, By Asset Class, Fundraising Timeline, Forward
Calendar). Built this session from scratch against an uploaded, scrubbed
Excel workbook. `README.md` is the user-facing doc — it's kept up to date
and is the first thing to read for *what the app does*. This file is about
*how it got built* and what to watch out for.

## Where things stand

- **Branch:** `claude/pi-pipeline-dashboard-1lfo4b`
- **PR:** #1 on `xalbertson/studious-disco` — **open, not merged**. The repo
  had zero commits when this started, so `main` had to be created fresh and
  the feature branch rebased onto it to give them common history (see the
  early commits if that history looks odd — it's intentional, not a mistake).
- All work is committed and pushed. Nothing in-flight, nothing uncommitted.
- The user hasn't asked for a merge — don't merge the PR or push further
  changes to `main` without being asked.

## Architecture, briefly

- `app.py` — the whole app, one file, organized by tab (`with tab_x:` blocks).
  It's gotten long; if you're adding a tab, follow the existing pattern
  rather than introducing a new structure.
- `constants.py` — every option list (Stage, Asset Class, Source, Due
  Diligence, client roster, etc.) and the canonical `COLUMNS` list that
  defines the CSV schema. **This is the single source of truth for the
  schema** — `data_utils.py` and `app.py` both key off `COLUMNS`,
  `DATE_COLUMNS`, `LIST_COLUMNS`, `FORWARD_CAL_ORDER_COLUMNS`.
- `data_utils.py` — `load_data`/`save_data`/`parse_uploaded_csv`, plus
  `_normalize()` which is what makes schema migrations painless (see below).
- `pptx_export.py` — builds the "export exhibit to PPTX" files (native
  PowerPoint charts backed by a real embedded Excel workbook, intentionally
  unformatted/default-styled per the user's request).
- `data/pipeline_data.csv` — the live dataset. Currently **350 synthetic,
  fictionally-named sample funds** (generated this session, not real firms).
  `data/pipeline_template_blank.csv` is the same schema with zero rows.
- `CSV_UPLOAD_FORMAT.md` — the schema reference aimed at whoever (or
  whatever agent) generates a CSV to upload. Keep it in sync with
  `constants.py` if you change the schema.

## The schema migration pattern (use this, don't hand-roll a migration)

Every time a column was added or renamed this session, the fix was:
1. Edit `COLUMNS` (and `DATE_COLUMNS`/`LIST_COLUMNS`/etc. if relevant) in
   `constants.py`.
2. Run `load_data()` then `save_data()` on the real CSV — `_normalize()`
   adds new columns as blank and silently drops columns no longer in
   `COLUMNS`, so this "just migrates" the file in place. No manual CSV
   surgery needed.
3. Regenerate `data/pipeline_template_blank.csv` the same way
   (`blank_template().to_csv(...)`).

## Forward Calendar: per-client, not shared

This took two iterations to get right, so don't reintroduce a shared
calendar by accident. Each client view — `Global`, `Olympus Mons`, `Gaucho`,
`Ursa Major`, `Orion` — has its **own** Forward Calendar, stored in its own
`Forward Calendar Order: <Client>` column (blank = not on that client's
calendar, otherwise its drag position). The top-left **Client view**
selector picks which one you're looking at/editing. `forward_cal_order_col(client)`
in `constants.py` builds the column name; don't hardcode it elsewhere.

## A real Plotly bug we hit and fixed (know this before touching Gantt charts)

Combining an **explicit `category_orders` override** for a categorical axis
with `fig.update_yaxes(autorange="reversed")` renders every bar in the
**opposite** of the intended order, and a raw numeric `y` value passed to
`add_hline`/`add_annotation` resolves to the *mirrored* position on top of
that. This is not intuitive and cost real time to track down — verified with
isolated minimal repros (see the conversation history / commit message on
`33ab717` if you need the receipts) rather than guessing.

The fix, now in place on the Forward Calendar's Gantt:
- **Don't reverse.** If you're passing an explicit `category_orders={"Firm": my_order}`
  with `my_order[0]` meant to render at the top, that already happens
  without `autorange="reversed"` — adding the reversal is what breaks it.
- **Use the actual category name** (e.g. the firm name) as the `y` for
  annotations, not a numeric index — that resolves correctly regardless of
  axis settings. Numeric `y` values are only safe for a line that needs to
  sit *between* two categories, and even then need the
  `N - 0.5 - position` compensation documented inline in `app.py`.

The Fundraising Timeline tab's Gantt chart does **not** pass an explicit
`category_orders` for `Firm` (it relies on the dataframe's own row order),
so it was never affected and still uses `autorange="reversed"` correctly —
don't "fix" that one, it isn't broken.

## Things that will bite you if you skip them

- **New Python dependency → `pip install -r requirements.txt` again.** This
  environment doesn't auto-install; the user hit this twice this session
  (`python-pptx`, `streamlit-sortables`) after pulling new commits.
- **Always reset test data before finishing.** Any time you populate
  `Clients Invested`, `Forward Calendar Order: *`, or dates to test a
  feature interactively, either restore with `git restore
  pi_pipeline_dashboard/data/pipeline_data.csv` (safest — use this if you're
  not 100% sure what was there before) or carefully diff against git before
  hand-editing back to "blank." Don't assume a field was blank before your
  test without checking; the 350-fund generator already populated a
  realistic subset of dates/clients, and a careless reset can silently wipe
  legitimate generated data (this happened once this session and was caught
  via `git diff` before it got committed).
- **Testing approach that's worked well:** `streamlit.testing.v1.AppTest`
  for fast smoke tests and interactive widget checks (selectbox/radio
  clicks, exception-free reruns) — no browser needed. For anything
  genuinely visual or drag-and-drop (the Forward Calendar's
  `streamlit-sortables` board), spin up the real app
  (`nohup streamlit run app.py & disown`, it's on port 5000 per
  `.streamlit/config.toml`) and drive it with Playwright
  (`executable_path="/opt/pw-browsers/chromium"`) — plain
  `page.mouse` drag sequences work for the sortable board; native `<select>`
  dropdowns often need a direct coordinate click rather than fighting
  Streamlit's BaseWeb widget internals with text locators.
- **Client roster is a hardcoded list** (`CLIENT_OPTIONS` in
  `constants.py`): Olympus Mons, Gaucho, Ursa Major, Orion. If the user adds
  a fifth client, that's the one place to add it — everything else
  (per-client Forward Calendar columns, the top-left selector, the sidebar
  filter label) derives from that list and `ALL_CLIENT_VIEWS`.

## Not done / possible next asks

Nothing is currently broken or half-finished, but these are natural
next-ask candidates given the conversation arc, not commitments:
- PPTX export exists for the four bar-chart exhibits but not for Forward
  Calendar.
- The 350 sample funds are synthetic placeholders — the user may eventually
  want to load real fund data via the CSV upload flow.
- No automated test suite beyond the manual `AppTest`/Playwright passes run
  ad hoc each session — if this app keeps growing, a `tests/` directory
  might be worth proposing.
