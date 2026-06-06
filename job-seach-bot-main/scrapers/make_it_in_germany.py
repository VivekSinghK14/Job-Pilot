"""
scrapers/make_it_in_germany.py
Uses the Bundesagentur für Arbeit public API
"""
from datetime import datetime, timedelta

import base64, hashlib, requests, urllib3
from config import SEARCH_CRITERIA, MAX_JOBS_PER_RUN, TITLE_BLOCKERS, REQUIRED_TITLE_KEYWORDS, MAX_JOB_AGE_DAYS
from utils.helpers import analyse_job, score_by_date


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
SITE_NAME  = "MakeItInGermany (BA API)"
HEADERS    = {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "Jobsuche/2.9.2 (de.arbeitsagentur.jobboerse; build:1077; iOS 15.1.0) Alamofire/5.4.4"}
SEARCH_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/app/jobs"
DETAIL_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails/{}"
JOB_URL    = "https://www.arbeitsagentur.de/jobsuche/jobdetail/{}"

def _encode_refnr(refnr): return base64.b64encode(refnr.encode()).decode()
def _make_id(refnr): return hashlib.md5(refnr.encode()).hexdigest()

def _get_job_detail(refnr):
    try:
        r = requests.get(DETAIL_URL.format(_encode_refnr(refnr)), headers=HEADERS, verify=False, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return " ".join(p for p in [d.get("stellenangebotsBeschreibung",""), d.get("stellenangebotsTitel","")] if p)
    except Exception as e:
        print(f"  [detail] Error: {e}")
    return ""

def scrape(page, seen_jobs):
    print(f"[{SITE_NAME}] Starting scrape…")
    results, seen_this_run = [], set()
    for entry in SEARCH_CRITERIA.get("keywords", []):
        keyword, days = entry if isinstance(entry, tuple) else (entry, 3)
        print(f"[{SITE_NAME}] Searching: '{keyword}' (last {days} days)")
        try:
            r = requests.get(SEARCH_URL, headers=HEADERS, verify=False, timeout=15,
                params={"was": keyword, "wo": "Deutschland", "page": 1, "size": MAX_JOBS_PER_RUN, "veroeffentlichtSeit": days})
            if r.status_code != 200:
                print(f"  [!] API returned {r.status_code}"); continue
            jobs = r.json().get("stellenangebote", [])
            print(f"  Found {len(jobs)} listing(s)")
            for job in jobs:
                refnr  = job.get("refnr", "")
                job_id = _make_id(refnr)
                if not refnr or job_id in seen_jobs or job_id in seen_this_run: continue
                title   = job.get("titel", "").strip()
                company = job.get("arbeitgeber", "").strip()
                ort     = job.get("arbeitsort", {}).get("ort", "")
                url     = JOB_URL.format(refnr)
                # ── Date filter ───────────────────────────────────────────────────────
                pub_date_str = job.get("aktuelleVeroeffentlichungsdatum", "")
                if pub_date_str:
                    try:
                        pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
                        if datetime.now() - pub_date > timedelta(days=days):
                            print(f"  ✗ OLD '{title}' — posted {pub_date_str}")
                            seen_jobs[job_id] = datetime.now().strftime("%Y-%m-%d")
                            seen_this_run.add(job_id)
                            continue
                    except Exception:
                        pass
                if not pub_date_str:
                    print(f"  [warn] Missing date for '{title}'")
                if any(b.lower() in title.lower() for b in TITLE_BLOCKERS):
                    print(f"  ✗ TITLE    '{title}'"); seen_jobs[job_id] = datetime.now().strftime("%Y-%m-%d"); seen_this_run.add(job_id); continue
                if not any(kw.lower() in title.lower() for kw in REQUIRED_TITLE_KEYWORDS):
                    print(f"  ✗ NOT-TECH '{title}'"); seen_jobs[job_id] = datetime.now().strftime("%Y-%m-%d"); seen_this_run.add(job_id); continue

                description = _get_job_detail(refnr)
                if not description:
                    print(f"  [warn] No description for '{title}'")
                    description = title

                analysis = analyse_job(title, description)

                if analysis["blocked"]:
                    print(f"  ✗ SKIP     '{title}' — {analysis['blocker_phrase']}")
                    seen_jobs[job_id] = datetime.now().strftime("%Y-%m-%d")
                    seen_this_run.add(job_id)
                    continue

                # ── Recency bonus (only for jobs that passed German filter) ────────
                recency_bonus = score_by_date(pub_date_str)
                analysis["score"] += recency_bonus
                if recency_bonus > 0:
                    analysis["positives"].append(f"📅 +{recency_bonus} (posted {pub_date_str})")

                blockers = analysis.get("blocker_hits", [])
                plus = analysis.get("plus_hits", [])
                print(
                    f"  ✓ MATCH  '{title}' @ {company}, {ort} | score={analysis['score']} | -{len(blockers) * 10} +{len(plus) * 10} +{len(analysis['positives']) - len(plus)}kw")
                results.append({
                    "site": SITE_NAME,
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "url": url,
                    "description": description,
                    "positives": analysis["positives"],
                    "score": analysis["score"],
                })
                seen_jobs[job_id] = datetime.now().strftime("%Y-%m-%d")
                seen_this_run.add(job_id)
        except Exception as e:
            print(f"  [!] Error: {e}")
    print(f"[{SITE_NAME}] Done — {len(results)} match(es) found")
    return results