"""
utils/helpers.py  —  Shared utilities for the job bot
"""

import json
import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    EMAIL_CONFIG,
    GERMAN_BLOCKER_KEYWORDS,
    GERMAN_PLUS_KEYWORDS,
    POSITIVE_KEYWORDS,
    SEEN_JOBS_FILE,
    TITLE_BLOCKERS,
    REQUIRED_TITLE_KEYWORDS,
    SCORING_RULES
)

from datetime import datetime, timedelta

# ── Seen-jobs tracker ────────────────────────────────────────────────────────

def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    return {}


def save_seen_jobs(seen):
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2)


def prune_seen_jobs(seen: dict, days: int = 20) -> dict:
    cutoff = datetime.now() - timedelta(days=days)

    new_seen = {}
    for job_id, date_str in seen.items():
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt >= cutoff:
                new_seen[job_id] = date_str
        except:
            continue

    return new_seen

# ── Keyword analysis ─────────────────────────────────────────────────────────

def is_german_blocker(text: str) -> tuple[bool, str]:
    lower = text.lower().replace("\\-", "-").replace("**", "").replace("###", "")
    for phrase in GERMAN_BLOCKER_KEYWORDS:
        if phrase.lower() in lower:
            return True, phrase
    return False, ""



def score_by_date(pub_date_str: str, date_format: str = "%Y-%m-%d") -> int:
    """Return a recency bonus based on how recently the job was posted."""
    try:
        pub_date = datetime.strptime(pub_date_str, date_format)
        age_days = (datetime.now() - pub_date).days
        if age_days == 0:   return 5
        elif age_days <= 3: return 3
        elif age_days <= 7: return 1
        elif age_days <= 14: return 0
        else:               return -2
    except Exception:
        return 0

def find_german_plus(text: str) -> bool:
    lower = text.lower()
    return any(phrase.lower() in lower for phrase in GERMAN_PLUS_KEYWORDS)

def find_positive_keywords(text: str) -> list[str]:
    """Return a list of attractive keywords found in the job text."""
    lower = text.lower()
    return [kw for kw in POSITIVE_KEYWORDS if kw.lower() in lower]


def analyse_job(title: str, description: str) -> dict:


    full_text = f"{title} {description}"
    title_lower = title.lower()
    full_lower = full_text.lower().replace("\\-", "-").replace("**", "").replace("###", "")

    # ── 1. Title blockers (hard skip, no scoring) ─────────────────────────────
    for blocker in TITLE_BLOCKERS:
        if blocker.lower() in title_lower:
            return {
                "blocked": True,
                "blocker_phrase": f"title:{blocker}",
                "positives": [],
                "score": -99,
            }

    # ── 2. Must have tech keyword in title (hard skip) ────────────────────────
    if not any(kw.lower() in title_lower for kw in REQUIRED_TITLE_KEYWORDS):
        return {
            "blocked": True,
            "blocker_phrase": "not-tech-title",
            "positives": [],
            "score": -99,
        }


    # ── 3. Scoring ────────────────────────────────────────────────────────────
    score = 0
    blocker_phrase = ""
    blocker_hits = []
    plus_hits = []

    rules = SCORING_RULES

    # 🔥 ROLE PRIORITY (INTERNSHIP FIRST)


    # 🔥 ENGLISH BOOST (VERY IMPORTANT FOR YOU)
    for keyword, value in rules["english_keywords"].items():
        if keyword in full_lower:
            score += value
            plus_hits.append(keyword)



    # 🔥 EXISTING GERMAN BLOCKERS (keep your strong system)
    for phrase in GERMAN_BLOCKER_KEYWORDS:
        if phrase.lower() in full_lower:
            score -= 10
            blocker_hits.append(phrase)

    # 🔥 EXISTING REGEX (KEEP THIS — VERY GOOD)
    if re.search(r'deutsch\s*[:\(]\s*[BC][12]', full_lower):
        score -= 10
        blocker_hits.append("Deutsch C1/B2 pattern")

    # 🔥 GERMAN PLUS
    for phrase in GERMAN_PLUS_KEYWORDS:
        if phrase.lower() in full_lower:
            score += 10
            plus_hits.append(phrase)

    # 🔥 EXISTING POSITIVES
    positives = find_positive_keywords(full_text)
    score += len(positives)

    # Add German plus labels
    for p in plus_hits:
        positives.append(f"🇩🇪 {p}")

    # ── 4. Block if score negative ────────────────────────────────────────────
    blocked = score < SCORING_RULES["min_score"]
    if blocker_hits:
        blocker_phrase = blocker_hits[0]

    return {
        "blocked":        blocked,
        "blocker_phrase": blocker_phrase,
        "positives":      positives,
        "score":          score,
        "blocker_hits":   blocker_hits,
        "plus_hits":      plus_hits,
    }


# ── Email sender ─────────────────────────────────────────────────────────────

def build_email_html(jobs: list[dict]) -> str:
    """Render a clean HTML email body from a list of matched job dicts."""

    def job_card(job: dict) -> str:
        positives_html = "".join(
            f'<span style="background:#d1fae5;color:#065f46;padding:2px 8px;'
            f'border-radius:4px;font-size:12px;margin-right:4px;">{kw}</span>'
            for kw in job.get("positives", [])
        )
        return f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;
                    margin-bottom:16px;font-family:sans-serif;">
          <h3 style="margin:0 0 4px;font-size:16px;">
            <a href="{job['url']}" style="color:#1d4ed8;text-decoration:none;">
              {job['title']}
            </a>
          </h3>
          <p style="margin:0 0 8px;color:#6b7280;font-size:13px;">
            {job['company']} &nbsp;·&nbsp; {job['site']}
          </p>
          <div style="margin-bottom:8px;">{positives_html}</div>
          <p style="margin:0;font-size:13px;color:#374151;">
            {job.get('description', '')[:280]}…
          </p>
        </div>
        """

    cards_html = "".join(job_card(j) for j in jobs)
    count = len(jobs)
    timestamp = datetime.now().strftime("%d %b %Y %H:%M")

    return f"""
    <html><body style="font-family:sans-serif;max-width:680px;margin:auto;padding:24px;">
      <h2 style="color:#111827;">🤖 Job Bot By Asif — {count} new match{'es' if count != 1 else ''}</h2>
      <p style="color:#6b7280;font-size:13px;">Checked at {timestamp}</p>
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0;">
      {cards_html}
      <p style="font-size:12px;color:#9ca3af;margin-top:24px;">
        Jobs with high German requirements were automatically filtered out.
      </p>
    </body></html>
    """


def send_email(jobs: list[dict]) -> None:
    if not jobs:
        print("[email] No new jobs to send.")
        return

    cfg = EMAIL_CONFIG

    # Build full recipient list
    all_recipients = [cfg["recipient"]]
    extra = cfg.get("extra_recipients", "")
    if extra:
        all_recipients += [e.strip() for e in extra.split(",") if e.strip()]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Job Bot] {len(jobs)} new job match{'es' if len(jobs) != 1 else ''} 🎯"
    msg["From"] = cfg["sender"]
    msg["To"] = ", ".join(all_recipients)

    html_body = build_email_html(jobs)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["sender"], cfg["password"])
            server.sendmail(cfg["sender"], all_recipients, msg.as_string())
        print(f"[email] ✓ Sent alert for {len(jobs)} job(s) to {len(all_recipients)} recipients")
    except Exception as e:
        print(f"[email] ✗ Failed to send email: {e}")
