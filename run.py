import argparse
from utils import logger
from processor import process_store_date
from store_config import load_all_stores


def main():
    parser = argparse.ArgumentParser(
        description="IRIS YOLO — S3 relevance detection pipeline"
    )
    parser.add_argument("--store", type=str, help="Store name (must match stores.store_name in DB)")
    parser.add_argument("--date", type=str, required=True, help="Date to scan (YYYY-MM-DD)")
    parser.add_argument(
        "--all-stores", action="store_true",
        help="Run all active stores for the given date"
    )
    args = parser.parse_args()

    if args.all_stores:
        stores = load_all_stores()
        logger.info(f"Running {len(stores)} active stores for {args.date}")
        for store in stores:
            try:
                process_store_date(store["store_name"], args.date)
            except Exception as e:
                logger.error(f"Store '{store['store_name']}' failed: {e}")
    elif args.store:
        process_store_date(args.store, args.date)
    else:
        parser.error("Provide --store <name> or --all-stores")


if __name__ == "__main__":
    main()
