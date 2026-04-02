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

- **Hold Recurrence** - Shows how many current-year students are first-time vs repeat hold recipients, segmented by total hold count (1st / 2nd / 3rd hold) rather than class standing (since class is credit-based and doesn't reliably reflect years enrolled). Includes clearance rates per group.

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
├── .gitignore                # Excludes .salt and data/*.csv
├── .salt                     # Salt secret for hashing student IDs (git-ignored)
├── package.json              # Dependencies and scripts
├── vite.config.js            # Vite build config
├── index.html                # HTML entry point
│
├── data/                     # ← Drop your CSV exports here (git-ignored)
│   └── *.csv                 # PERC Hold Tags export from Informer
│
├── scripts/
│   └── build-data.py         # CSV → JSON pipeline (hashes student IDs)
│
├── src/
│   ├── main.jsx              # React entry point
│   ├── App.jsx               # Main dashboard component (all logic + UI)
│   └── data/
│       └── holds.json        # Pipeline output (hashed IDs, safe to commit)
│
└── public/                   # Static assets
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
2. Read the salt from `.salt` for student ID hashing
3. Filter to INS-prefixed restrictions only
4. Include all class standings (FY, SO, JR, SR, ALUM) for accurate melt curves
5. Hash student IDs with a salted SHA-256 (8-character hex) for recurrence tracking
6. Output clean JSON to `src/data/holds.json`
7. Print a summary of processed records and recurrence stats

**To update the dashboard with fresh data:**

```bash
# 1. Drop new CSV in data/
# 2. Rebuild the JSON
npm run build-data
# 3. Commit and push
git add .
git commit -m "Update hold data"
git push
# 4. Deploy to GitHub Pages
npm run deploy
```

### Future: Wildcard Export

The pipeline is designed to be forward-compatible with a wildcard PERC export (all students, all restriction types). The filters in `build-data.py` are clearly marked. When you switch to the wildcard export, you'll adjust the filters and potentially add a "cohort penetration" view showing what percentage of each class received a hold.

### Class Standing Note

The `Class` column in the CSV reflects current class standing (based on credits), not standing at time of hold placement. For prior years, students may show as SR or ALUM even though they were FY/SO/JR when the hold was placed. The dashboard handles this by including all class standings in melt curves (for accurate totals) and only using the FY/SO/JR breakdown for the current cohort's snapshot and daily clearance views, where the data is accurate. Hold recurrence is tracked by student ID hash, not class standing, since class is credit-based and doesn't reliably reflect years enrolled.

---

## Hold Release Delay

When holds are lifted, the end date in the system is typically backdated by one day. For example, if a hold is actually released on March 28, the system records the end date as March 27. This ensures the student can register immediately rather than waiting until the next day.

The dashboard accounts for this with a configurable **delay** setting (default: 1 day). The delay shifts all logged end dates forward by N days to reflect the actual release date.

You can adjust this in the Settings panel (gear icon in the header). Changing the delay recalculates all melt curves in real time.

---

## Privacy and FERPA Compliance

Hold records contain FERPA-protected educational data. The pipeline protects student identity through salted hashing:

- **Student IDs are never stored in the output JSON.** The pipeline reads the raw ID from the CSV, combines it with a secret salt phrase, and writes an 8-character SHA-256 hash (e.g., `2f7b3ddc`). The hash is consistent across records, so the dashboard can track recurrence, but it cannot be reversed to recover the original ID.

- **The salt is stored in `.salt`** in the project root. This file is git-ignored and never leaves your machine. Without the salt, brute-forcing the hashes is infeasible.

- **Raw CSVs are git-ignored** via `data/*.csv` in `.gitignore`. They stay on your machine only.

- **The generated `holds.json` is safe to commit** and deploy publicly. It contains only hashed IDs, dates, restriction codes, and class standings.

### First-Time Setup

Create a `.salt` file in the project root containing your secret phrase (no quotes, no newline):

```bash
echo -n "your-secret-phrase" > .salt
```

If you regenerate the salt, all hashes will change. The dashboard still works, but you lose the ability to compare old and new JSON exports by hash.

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

Output goes to the `dist/` folder.

### Deploy to GitHub Pages

```bash
npm run deploy
```

This runs `npm run build` automatically (via `predeploy`), then pushes the `dist/` folder to the `gh-pages` branch. GitHub Pages serves from that branch.

The dashboard is live at `https://zdavico.github.io/insight-hold-melt/`.

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
4. The dashboard handles everything else automatically (melt curves, daily clearance, snapshot, and recurrence all adapt to the new current cohort)

---

## Credits

InSight Program, Champlain College Career Collaborative, Burlington VT.
