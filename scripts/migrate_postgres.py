"""Copy the local SQLite snapshot into PostgreSQL."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storage.postgres import DEFAULT_DATABASE_URL  # noqa: E402
from storage.postgres import init_db as init_postgres  # noqa: E402
from storage.postgres import save as save_postgres  # noqa: E402
from storage.sqlite import load_all as load_sqlite  # noqa: E402

DB_PATH = ROOT / "data" / "auctionote.db"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqlite-db", type=Path, default=DB_PATH)
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    args = parser.parse_args()

    items = load_sqlite(args.sqlite_db)
    try:
        init_postgres(args.database_url)
        save_postgres(items, args.database_url)
    except SQLAlchemyError as exc:
        raise SystemExit(f"PostgreSQL migration failed: {exc}") from exc
    print(f"migrated {len(items)} auction items into PostgreSQL")


if __name__ == "__main__":
    main()
