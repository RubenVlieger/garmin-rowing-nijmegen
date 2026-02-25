"""
Analytics Report Generator
===========================
Reads daily JSONL log files from analytics/ and generates a summary.

Output: analytics/summary.json with daily unique user counts and country distributions.

Usage:
    python analytics_report.py              # Process all days
    python analytics_report.py --days 7     # Process last 7 days only

Add to cron for daily summary updates:
    0 3 * * * /home/ubuntu/garmin-rowing/venv/bin/python /home/ubuntu/garmin-rowing/backend/analytics_report.py --days 30
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ANALYTICS_DIR = Path(__file__).parent.resolve() / "analytics"
SUMMARY_FILE = ANALYTICS_DIR / "summary.json"


def parse_day(log_file: Path) -> dict:
    """Parse a single day's JSONL log file and return summary stats."""
    unique_users = set()
    countries = defaultdict(int)

    with open(log_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                uid = entry.get("uid", "")
                country = entry.get("country", "XX")

                if uid and uid not in unique_users:
                    unique_users.add(uid)
                    countries[country] += 1
            except json.JSONDecodeError:
                continue

    return {
        "unique_users": len(unique_users),
        "countries": dict(sorted(countries.items(), key=lambda x: -x[1])),
    }


def generate_report(max_days: int = None):
    """Generate summary.json from all (or recent) JSONL log files."""
    if not ANALYTICS_DIR.exists():
        print("No analytics directory found. Nothing to report.")
        return

    # Find all JSONL files
    log_files = sorted(ANALYTICS_DIR.glob("*.jsonl"), reverse=True)

    if not log_files:
        print("No log files found. Nothing to report.")
        return

    # Filter to recent days if specified
    if max_days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_days)).strftime("%Y-%m-%d")
        log_files = [f for f in log_files if f.stem >= cutoff]

    # Load existing summary to preserve older data
    summary = {}
    if SUMMARY_FILE.exists():
        try:
            with open(SUMMARY_FILE, "r") as f:
                summary = json.load(f)
        except (json.JSONDecodeError, IOError):
            summary = {}

    # Process each day
    for log_file in log_files:
        date_str = log_file.stem  # e.g., "2026-02-25"
        print(f"Processing {date_str}...")
        day_stats = parse_day(log_file)
        summary[date_str] = day_stats
        print(f"  → {day_stats['unique_users']} unique users, "
              f"{len(day_stats['countries'])} countries")

    # Sort by date (newest first) and save
    summary = dict(sorted(summary.items(), reverse=True))

    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✓ Summary saved to {SUMMARY_FILE}")
    print(f"  Total days: {len(summary)}")

    # Print a quick overview of the most recent days
    print("\nRecent activity:")
    for date_str in list(summary.keys())[:7]:
        stats = summary[date_str]
        top_countries = ", ".join(
            f"{c}: {n}" for c, n in list(stats["countries"].items())[:3]
        )
        print(f"  {date_str}: {stats['unique_users']} users ({top_countries})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate analytics summary report")
    parser.add_argument("--days", type=int, default=None,
                        help="Only process the last N days (default: all)")
    args = parser.parse_args()

    generate_report(max_days=args.days)
