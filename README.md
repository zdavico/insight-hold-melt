# InSight Hold Melt Dashboard

A React + Recharts interactive dashboard for tracking PERC registration hold placement and clearance patterns across academic years at Champlain College.

Built for the InSight Program at the Career Collaborative.

---

## What It Does

Every semester, the InSight program places PERC registration holds on students who haven't met their milestone requirements. This dashboard visualizes how those holds "melt" over time as students complete their milestones and have their holds lifted.

### Key Views

- **Historical Melt Comparison** - A Mansfield snow-stake-style overlay showing every academic year's hold clearance curve on the same axis. A prior-year average line and range band provide instant context for whether the current year is ahead or behind.

- **Daily Clearance** - Bar chart showing holds cleared per day, with toggles for aggregate, stacked by class, or individual class standing. Spikes correspond to coaching pushes, email reminders, or events like FastPass Day.

- **Hold Snapshot** - Time slider that scrubs through the current year day by day, showing a stacked area (or bar) chart of remaining holds by class standing (First Year, Sophomore, Junior). The "Play Melt" button animates the full sequence.

### Features

- **Dark / Light mode** (dark default, Champlain Colors theme)
- **Hold release delay setting** to account for the practice of backdating hold removal dates
- **Font size scaling** (Small / Medium / Large)
- **Toggleable cohorts** on the melt overlay (prior-year average recalculates reactively)
- **Days-to-50% badges** for quick cross-year comparison
- **Percentage or absolute count** views on the melt chart

---

## Project Structure

```
insight-hold-melt/
├── README.md                 # This file
├── package.json              # Dependencies and scripts
├── vite.config.js            # Vite build config
├── index.html                # HTML entry point
│
├── data/                     # ← Drop your CSV exports here
│   └── *.csv                 # PERC Hold Tags export from the student system
│
├── scripts/
│   └── build-data.py         # CSV → JSON pipeline
│
├── src/
│   ├── main.jsx              # React entry point
│   ├── App.jsx               # Main dashboard component (all logic + UI)
│   └── data/
│       └── holds.json        # Pipeline output (generated, not hand-edited)
│
└── public/                   # Static assets (currently empty)
```

---

## Data Pipeline

The dashboard uses a two-step data flow:

### Step 1: Export the CSV

Run the PERC Hold Tags report from the student system. The report should filter for restrictions starting with `INS` (e.g., `INS26`, `INS25`).

Expected CSV columns:
- `Str Student` - Student ID
- `Restriction` - Hold code (e.g., `INS26`)
- `Start Date` - When the hold was placed (YYYY-MM-DD)
- `End Date` - When the hold was lifted (YYYY-MM-DD, or empty if still active)
- `Class` - Class standing (FY, SO, JR, SR, ALUM)
- `Credits - Current Registered Credits + Completed Credits`
- `Credits - Completed Credits Undergrad ONLY`
- `Active Programs` - Degree program code
- `Student Restrictions Id`

Place the CSV file in the `data/` folder.

### Step 2: Run the pipeline

```bash
python3 scripts/build-data.py
```

The pipeline will:
1. Find the most recent CSV in `data/`
2. Filter to INS-prefixed restrictions only
3. Exclude Senior (SR) and Alumni (ALUM) records
4. Output clean JSON to `src/data/holds.json`
5. Print a summary of processed records

**To update the dashboard with fresh data**, just drop a new CSV in `data/` and re-run the pipeline. Then restart the dev server (or rebuild).

### Future: Wildcard Export

The pipeline is designed to be forward-compatible with a wildcard PERC export (all students, all restriction types). The filters in `build-data.py` are clearly marked. When you switch to the wildcard export, you'll adjust the filters and potentially add a "cohort penetration" view showing what percentage of each class standing received a hold.

---

## Hold Release Delay

When holds are lifted, the end date in the system is typically backdated by one day. For example, if a hold is actually released on March 28, the system records the end date as March 27. This ensures the student can register immediately rather than waiting until the next day.

The dashboard accounts for this with a configurable **delay** setting (default: 1 day). The delay shifts all logged end dates forward by N days to reflect the actual release date.

You can adjust this in the Settings panel (gear icon in the header). Changing the delay recalculates all melt curves in real time.

---

## Local Development Setup

### Prerequisites

- **Node.js** 18+ and npm (download from https://nodejs.org)
- **Python** 3.8+ (for the data pipeline)

### Install and Run

```bash
# 1. Navigate to the project folder
cd insight-hold-melt

# 2. Install JavaScript dependencies
npm install

# 3. Run the data pipeline (if you haven't already)
python3 scripts/build-data.py

# 4. Start the development server
npm run dev
```

The dev server opens at `http://localhost:5173` with hot reload.

### Build for Production

```bash
npm run build
```

Output goes to the `dist/` folder. This can be deployed to GitHub Pages or any static host.

---

## PyCharm Setup

1. **Open the project**: File → Open → select the `insight-hold-melt` folder
2. **Install Node.js plugin** (if not already): File → Settings → Plugins → search "Node.js"
3. **Run npm install**: Open Terminal (bottom panel) → `npm install`
4. **Run the pipeline**: In Terminal → `python3 scripts/build-data.py`
5. **Start dev server**: In Terminal → `npm run dev`
6. Alternatively, create a Run Configuration:
   - Run → Edit Configurations → + → npm
   - Command: `run`, Scripts: `dev`
   - Click Run (green play button)

---

## Tech Stack

- **React 18** - UI framework
- **Recharts** - Chart library (LineChart, BarChart, AreaChart, ComposedChart)
- **Vite** - Build tool and dev server
- **Python** - Data pipeline (no dependencies beyond stdlib)
- **DM Sans / DM Mono** - Typography (loaded via Google Fonts)

---

## Adding a New Academic Year

When a new hold cycle begins (e.g., INS27 for 2026-27):

1. **In `scripts/build-data.py`**: Add the new code to the `YEAR_LABELS` dictionary
2. **In `src/App.jsx`**: Add the new code to:
   - `YEAR_LABELS` object
   - `COHORT_ORDER` array (at the front)
   - `PRIOR_COHORTS` array (add the previous current year)
   - `COHORT_COLORS` object (pick a new color)
   - Update `CURRENT_COHORT` to the new code
3. Run the pipeline with a CSV that includes the new restriction code
4. The dashboard handles everything else automatically

---

## Credits

InSight Program, Champlain College Career Collaborative, Burlington VT.
