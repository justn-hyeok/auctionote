"""Rebuild the Elasticsearch index from the local SQLite snapshot."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from search.elastic import (  # noqa: E402
    DEFAULT_ELASTIC_URL,
    INDEX_NAME,
    create_client,
    ensure_index,
    index_items,
    is_available,
)
from storage.sqlite import load_all  # noqa: E402

DB_PATH = ROOT / "data" / "auctionote.db"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--url", default=DEFAULT_ELASTIC_URL)
    parser.add_argument("--index", default=INDEX_NAME)
    parser.add_argument("--no-recreate", action="store_true")
    args = parser.parse_args()

    client = create_client(args.url)
    if not is_available(client):
        raise SystemExit(f"Elasticsearch is not reachable at {args.url}")

    items = load_all(args.db)
    ensure_index(client, index_name=args.index, recreate=not args.no_recreate)
    indexed = index_items(client, items, index_name=args.index)
    print(f"indexed {indexed} auction items into {args.index}")


if __name__ == "__main__":
    main()

