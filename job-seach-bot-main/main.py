"""
main.py  —  Job Bot entry point
Run:  python main.py
      python main.py --once     (single run, no scheduler)
      python main.py --debug    (show browser window)
"""
from dotenv import load_dotenv
load_dotenv()
import sys
import argparse
from datetime import datetime

from playwright.sync_api import sync_playwright
from apscheduler.schedulers.blocking import BlockingScheduler

from config import CHECK_INTERVAL_HOURS, HEADLESS
from utils.helpers import load_seen_jobs, save_seen_jobs, send_email, prune_seen_jobs
from scrapers import make_it_in_germany, jobteaser
from job_tracker import save_jobs_to_excel, clean_old_jobs
from gdrive_upload import upload_to_drive



def run_all_scrapers(headless: bool = HEADLESS) -> None:
    """Launch browser, run all scrapers, filter results, send email."""
    print(f"\n{'='*55}")
    print(f"  Job Bot run started — {datetime.now().strftime('%d %b %Y %H:%M:%S')}")
    print(f"{'='*55}")

    seen_jobs = load_seen_jobs()
    all_matches: list[dict] = []

    with sync_playwright() as pw:
        from playwright_stealth import Stealth

        browser = pw.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="de-DE",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        Stealth().apply_stealth_sync(page)



        # ── Run each scraper ──────────────────────────────────────────────────
        scrapers = [
            jobteaser,
            make_it_in_germany,
        ]

        for scraper in scrapers:
            try:
                matches = scraper.scrape(page, seen_jobs)
                all_matches += matches
            except Exception as e:
                print(f"[ERROR] Scraper {scraper.__name__} failed: {e}")

        browser.close()

    # ── Sort by relevance score ───────────────────────────────────────────────
    # 🔥 Sort ALL jobs by score (highest first)
    all_matches.sort(key=lambda x: x.get("score", 0), reverse=True)

    print(f"\n{'─'*55}")
    print(f"  Total new matches: {len(all_matches)}")
    print(f"{'─'*55}\n")

    # ── Persist seen jobs & send email ────────────────────────────────────────
    seen_jobs = prune_seen_jobs(seen_jobs, days=20)
    save_seen_jobs(seen_jobs)

    if all_matches:
        send_email(all_matches)
        save_jobs_to_excel(all_matches)
        clean_old_jobs(days=30)
        try:
            upload_to_drive()
        except Exception as e:
            print(f"[gdrive] Upload failed: {e}")
    else:
        print("[bot] No new matching jobs this run.")

 

    # ✅ prune + save at VERY END
    seen_jobs = prune_seen_jobs(seen_jobs, days=20)
    save_seen_jobs(seen_jobs)


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Job Bot")
    parser.add_argument("--once",  action="store_true", help="Run once and exit")
    parser.add_argument("--debug", action="store_true", help="Show browser window")
    args = parser.parse_args()

    # If --debug passed, force headless=False, otherwise use config
    if args.debug:
        headless = False
    else:
        headless = HEADLESS  # uses config.py value

    if args.once or args.debug:
        run_all_scrapers(headless=headless)
        return


    # ── Scheduled mode ────────────────────────────────────────────────────────
    print(f"[scheduler] Job Bot starting — will check every {CHECK_INTERVAL_HOURS}h")
    print("[scheduler] Press Ctrl+C to stop\n")

    # Run immediately on start
    run_all_scrapers(headless=headless)

    scheduler = BlockingScheduler()
    scheduler.add_job(
        lambda: run_all_scrapers(headless=headless),
        "interval",
        hours=CHECK_INTERVAL_HOURS,
    )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n[scheduler] Stopped.")


if __name__ == "__main__":
    main()
