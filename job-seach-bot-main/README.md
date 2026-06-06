# Job Bot 🤖

Automatically scrapes **MakeItInGermany** (Bundesagentur für Arbeit API) and **JobTeaser (OVGU)** for new Werkstudent, Praktikum, and internship postings, filters out jobs with high German language requirements, scores them by relevance and recency, and emails you the matches — plus saves everything to an Excel tracker synced to Google Drive.

---

## Features

- 🔍 Searches 30+ keyword/contract-type combinations across both platforms
- 🇩🇪 Filters out jobs requiring fluent/C1/C2 German automatically
- 📊 Scores jobs by role type, tech keywords, English-friendliness, and recency
- 📧 Sends a formatted HTML email with every new match
- 📋 Saves all matches to `job_tracker.xlsx` with Applied/Notes columns
- ☁️ Syncs the Excel tracker to Google Drive after every run
- 🕐 Runs on a schedule (every 6 hours by default)

---

## Setup (one-time)

### 1. Clone the repo and install dependencies

```bash
git clone https://github.com/asifsiddiqui09/job-search-bot.git
cd "job search bot"
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Create your `.env` file

```dotenv
EMAIL_PASSWORD=your_gmail_app_password
EMAIL_SENDER=you@gmail.com
EMAIL_RECIPIENT=you@gmail.com
JOBTEASER_EMAIL=your.name@st.ovgu.de
JOBTEASER_PASSWORD=your_jobteaser_password
GDRIVE_FOLDER_ID=your_google_drive_folder_id
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}  # Railway only
```

### 3. Get a Gmail App Password

1. Go to https://myaccount.google.com/apppasswords
2. Create a new app password (name it "Job Bot")
3. Paste the 16-character code into `EMAIL_PASSWORD` in `.env`

### 4. Set up Google Drive sync (optional)

1. Create a project at https://console.cloud.google.com
2. Enable the **Google Drive API**
3. Create a **Service Account** and download the JSON key as `service_account.json`
4. Create a folder in Google Drive and share it with the service account email
5. Copy the folder ID from the URL into `GDRIVE_FOLDER_ID` in `.env`

---

## Running the bot

```bash
# Run once and exit (good for testing)
python main.py --once

# Show the browser window (good for debugging)
python main.py --debug --once

# Run continuously on a schedule (normal use)
python main.py
```

> **Note:** JobTeaser requires a visible browser to bypass Cloudflare. The bot runs with `HEADLESS = False` by default — just minimize the browser window when it opens.

---

## How filtering works

Each job is scored from 0 upward:

| Signal | Score |
|---|---|
| German blocker phrase found (e.g. "fließende Deutschkenntnisse") | −10 each |
| German plus phrase found (e.g. "Deutsch von Vorteil") | +10 each |
| Positive keyword found (Python, remote, English, etc.) | +1 each |
| Posted today | +5 |
| Posted 1–3 days ago | +3 |
| Posted 4–7 days ago | +1 |

Jobs with a final score below 0 are blocked. The email is sorted highest score first.

**Hard filters** (skip before scoring):
- Title contains blocked terms: PhD, Vertrieb, Warenverräumer, Tax, etc.
- Title has no relevant tech keyword

---

## Project structure

```
job search bot/
├── main.py                     ← entry point + scheduler
├── config.py                   ← all settings, keywords, scoring rules
├── job_tracker.py              ← Excel tracker writer
├── gdrive_upload.py            ← Google Drive sync
├── requirements.txt
├── .env                        ← credentials (never commit)
├── service_account.json        ← Google service account (never commit)
├── seen_jobs.json              ← auto-created, tracks processed jobs
├── job_tracker.xlsx            ← auto-created, local copy of tracker
├── scrapers/
│   ├── make_it_in_germany.py   ← Bundesagentur für Arbeit REST API
│   └── jobteaser.py            ← Playwright + stealth scraper
└── utils/
    └── helpers.py              ← scoring, filtering, email sender
```

---

## Customising

### Add more search keywords
Edit `SEARCH_CRITERIA["keywords"]` in `config.py`:
```python
("Werkstudent React", 3),   # keyword, max age in days
("Internship NLP",    3),
```

### Add more German blocker phrases
Add to `GERMAN_BLOCKER_KEYWORDS` in `config.py` (all lowercase):
```python
"good knowledge of german",
"knowledge of german",
```

### Add more job sites
1. Copy `scrapers/jobteaser.py` to e.g. `scrapers/stepstone.py`
2. Update `BASE_URL`, `SITE_NAME`, and the selectors for that site
3. Import and add it to the `scrapers` list in `main.py`

---

## Deploying to Railway

1. Push your code to GitHub (make sure `.env` and `service_account.json` are in `.gitignore`)
2. Create a new Railway project from your GitHub repo
3. Add all `.env` variables as Railway environment variables
4. For `GOOGLE_SERVICE_ACCOUNT_JSON`, paste the full contents of `service_account.json`
5. Railway will run `python main.py` on a schedule automatically

---

## Requirements

- Python 3.12+
- Gmail account with App Password enabled
- OVGU JobTeaser account (for JobTeaser scraping)
- Google Cloud service account (for Drive sync, optional)
