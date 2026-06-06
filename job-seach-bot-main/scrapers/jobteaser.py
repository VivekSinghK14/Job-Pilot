"""
scrapers/jobteaser.py
Scraper for https://ovgu.jobteaser.com  (requires OVGU login + stealth)
"""
from datetime import datetime, timedelta
import re
import hashlib
from playwright.sync_api import Page

from config import JOBTEASER_EMAIL, JOBTEASER_PASSWORD,  MAX_JOB_AGE_DAYS, JT_SEARCHES
from utils.helpers import analyse_job, score_by_date


SITE_NAME = "JobTeaser (OVGU)"
BASE_URL  = "https://ovgu.jobteaser.com"


def _parse_relative_age_days(text: str) -> int | None:
    """Convert 'vor X Tagen/Wochen/Monaten' to approximate days. Returns None if unparseable."""
    text = text.strip().lower()
    m = re.search(r'vor\s+(\d+)\s+(tag|woche|monat)', text)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    if unit == 'tag':
        return n
    elif unit == 'woche':
        return n * 7
    elif unit == 'monat':
        return n * 30
    return None


def _wait_for_cloudflare(page: Page, label: str = "") -> None:
    """Wait up to 30s for Cloudflare 'Just a moment...' challenge to pass."""
    for i in range(6):
        title = page.title().lower()
        if "just a moment" not in title:
            return
        print(f"  [CF] Cloudflare detected{' on ' + label if label else ''}, waiting... ({i+1}/6)")
        page.wait_for_timeout(5000)


def _make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _build_url(keyword: str, contracts: list, page_num: int = 1) -> str:
    contract_params = "&".join(f"contract={c}" for c in contracts)
    return (
        f"{BASE_URL}/de/job-offers"
        f"?{contract_params}"
        f"&q={keyword.replace(' ', '+')}"
        f"&abroad_only=false"
        f"&localized_location=Deutschland"
        f"&location=Germany%3A%3A_Y291bnRyeTo6OllBek5HM0ZXa2pMUUhSRUx4ajZRYStxd1RZdz0%3D"
        f"&sort=recency"
        f"&page={page_num}"
    )


def _is_real_job_link(href: str) -> bool:
    """Filter out pagination and nav links, keep only individual job posts."""
    if not href or len(href) < 30:
        return False
    if "job-offer" not in href:
        return False
    if "page=" in href:
        return False
    parts = href.rstrip("/").split("/")
    last = parts[-1]
    return len(last) > 20


def scrape(page: Page, seen_jobs: set) -> list[dict]:
    print(f"[{SITE_NAME}] Starting scrape…")
    results = []

    # ── 1. Login ──────────────────────────────────────────────────────────────
    print(f"[{SITE_NAME}] Logging in...")
    try:
        page.goto(
            f"{BASE_URL}/de/job-offers?contract=part_time&q=data",
            wait_until="domcontentloaded", timeout=30_000
        )
        page.wait_for_timeout(4000)
        _wait_for_cloudflare(page, "login page")

        if "connect.jobteaser.com" in page.url:
            print(f"[{SITE_NAME}] Filling login form...")
            print(f"[{SITE_NAME}] Email: {JOBTEASER_EMAIL}")
            print(f"[{SITE_NAME}] Password set: {'Yes' if JOBTEASER_PASSWORD else 'NO - CHECK .env FILE'}")

            page.locator('input[id="email"]').fill(JOBTEASER_EMAIL)
            page.wait_for_timeout(400)
            page.locator('input[id="passwordInput"]').fill(JOBTEASER_PASSWORD)
            page.wait_for_timeout(400)
            page.locator('button:has-text("Login")').click()
            page.wait_for_timeout(10000)
            _wait_for_cloudflare(page, "post-login")
            print(f"[{SITE_NAME}] After login URL: {page.url}")

        if "connect.jobteaser.com" in page.url:
            print(f"[{SITE_NAME}] Login failed — skipping")
            return results

        print(f"[{SITE_NAME}] Login successful")

    except Exception as e:
        print(f"[{SITE_NAME}] Login error: {e}")
        return results

    # ── 2. Search each keyword + contract type combo ──────────────────────────
    all_links: list[str] = []

    for keyword, contracts in JT_SEARCHES:
        label = f"{keyword} [{','.join(contracts)}]"
        page_num = 1
        keyword_links: list[str] = []

        while True:
            url = _build_url(keyword, contracts, page_num)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                _wait_for_cloudflare(page, label)

                # Wait for React to render job cards
                try:
                    page.wait_for_selector("a[href*='/job-offer']", timeout=15_000)
                except Exception:
                    # No jobs rendered — try scrolling to trigger lazy load
                    page.evaluate("window.scrollTo(0, 300)")
                    page.wait_for_timeout(3000)

                # ── Build age map from <time> tags on this listing page ────────
                age_map: dict[str, int | None] = {}
                time_tags = page.locator("time").all()
                for t in time_tags:
                    age_text = t.inner_text().strip()
                    age_days = _parse_relative_age_days(age_text)
                    try:
                        parent = t.locator(
                            "xpath=ancestor::li | ancestor::article | "
                            "ancestor::div[contains(@class,'card')]"
                        ).last
                        link_el = parent.locator("a[href*='/job-offer']").first
                        href = link_el.get_attribute("href") or ""
                        if _is_real_job_link(href):
                            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                            age_map[full_url] = age_days
                    except Exception:
                        pass

                # ── Collect links, skipping old ones ──────────────────────────
                links: list[str] = []
                for card in page.locator("a").all():
                    href = card.get_attribute("href") or ""
                    if not _is_real_job_link(href):
                        continue
                    full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                    age_days = age_map.get(full_url)
                    if age_days is not None and age_days > MAX_JOB_AGE_DAYS:
                        print(f"  ✗ OLD ({age_days}d)  {full_url[-55:]}")
                        continue
                    links.append(full_url)

                links = list(dict.fromkeys(links))

                if not links:
                    break

                new_links = [l for l in links if l not in all_links]
                keyword_links.extend(new_links)
                all_links.extend(new_links)

                if page_num >= 6:
                    break

                page_num += 1

            except Exception as e:
                print(f"[{SITE_NAME}] Error on '{label}' page {page_num}: {e}")
                break

        print(f"[{SITE_NAME}] '{label}' — {len(keyword_links)} listing(s)")

    all_links = list(dict.fromkeys(all_links))
    print(f"[{SITE_NAME}] Total unique listings after age filter: {len(all_links)}")

    # ── 3. Open each listing and analyse ─────────────────────────────────────
    for url in all_links:
        job_id = _make_id(url)
        if job_id in seen_jobs:
         continue

        # ── Quick URL-based pre-filter ────────────────────────────────────────
        url_lower = url.lower()
        url_skip_terms = [
            "warenver", "verkauf", "aushilfe", "kasse", "saisonkraft",
            "ferienjob", "kuechenhilfe", "zimmerer", "schnupperpraktikum",
            "schulerpraktikum", "referendariat", "transfer-pricing",
            "tax-", "-tax-", "audit-", "-audit",
            "brennstoffzellen", "solarzellen", "lasertechnologie",
            "galvanik", "triebwerk", "aircraft",
            "sustainability-intern", "vaccine",
        ]
        if any(term in url_lower for term in url_skip_terms):
            print(f"  ✗ URL-SKIP {url[-55:]}")
            seen_jobs[job_id] = datetime.now().strftime("%Y-%m-%d")
            continue

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            page.wait_for_timeout(1500)
            _wait_for_cloudflare(page)

            # Title
            title = ""
            try:
                title = page.locator("h1").first.inner_text().strip()
            except Exception:
                pass
            if not title or len(title) < 4:
                title = page.title().split("|")[0].split("-")[0].strip()

            # Company
            company = ""
            try:
                # JobTeaser company name is in CompanySection, after the logo
                for selector in [
                    "[data-testid='jobad-DetailView-CompanySection-company-logo']",
                    "[class*='CompanySection'] h2",
                    "[class*='CompanySection'] a",
                    "[class*='CompanySection'] span",
                    "[class*='CompanySection'] p",
                ]:
                    try:
                        el = page.locator(selector).first
                        # For the logo, get alt text which contains company name
                        if "logo" in selector:
                            alt = el.get_attribute("alt") or ""
                            # alt is "Vector Informatik GmbH logo" — strip " logo"
                            company = alt.replace(" logo", "").strip()
                        else:
                            company = el.inner_text().strip()
                        if company and 2 < len(company) < 100:
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Description
            description = ""
            try:
                description = page.locator(
                    "main, article, [class*='description'], [class*='content']"
                ).first.inner_text()
            except Exception:
                description = page.locator("body").inner_text()

            analysis = analyse_job(title, description)

            if analysis["blocked"]:
                print(f"  ✗ SKIP  '{title}' — {analysis['blocker_phrase']}")
                seen_jobs[job_id] = datetime.now().strftime("%Y-%m-%d")
                continue

            # ── Recency scoring (only for jobs that passed) ───────────────────
            try:
                date_matches = re.findall(r'(\d{2}/\d{2}/\d{4})', description)
                if date_matches:
                    recency_bonus = score_by_date(date_matches[0], "%d/%m/%Y")
                    analysis["score"] += recency_bonus
                    if recency_bonus > 0:
                        analysis["positives"].append(f"📅 +{recency_bonus} (posted {date_matches[0]})")
            except Exception:
                pass

            print(f"  ✓ MATCH '{title}' (score={analysis['score']})")
            results.append({
                "site":      SITE_NAME,
                "job_id":    job_id,
                "title":     title,
                "company":   company,
                "url":       url,
                "description": description,
                "positives": analysis["positives"],
                "score":     analysis["score"],
            })
            seen_jobs[job_id] = datetime.now().strftime("%Y-%m-%d")

        except Exception as e:
            print(f"  ✗ Error opening {url}: {e}")

    print(f"[{SITE_NAME}] Done — {len(results)} match(es) found")
    return results