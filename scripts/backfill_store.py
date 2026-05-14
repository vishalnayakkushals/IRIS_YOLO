import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime, timedelta
from processor import process_store_date
from utils import logger


def main():
    parser = argparse.ArgumentParser(description="Backfill a store for a date range")
    parser.add_argument("--store", required=True, help="Store name")
    parser.add_argument("--from-date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to-date", required=True, help="End date YYYY-MM-DD (inclusive)")
    args = parser.parse_args()

    start = datetime.strptime(args.from_date, "%Y-%m-%d").date()
    end = datetime.strptime(args.to_date, "%Y-%m-%d").date()

    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        logger.info(f"Backfilling {args.store} for {date_str}")
        try:
            process_store_date(args.store, date_str)
        except Exception as e:
            logger.error(f"Failed for {date_str}: {e}")
        current += timedelta(days=1)


if __name__ == "__main__":
    main()
