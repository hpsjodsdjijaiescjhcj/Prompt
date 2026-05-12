from __future__ import annotations

from infrastructure.db import init_mysql_schema, mysql_available


def main():
    if not mysql_available():
        raise SystemExit(
            "MySQL is not configured or SQLAlchemy driver is unavailable. "
            "Please set MYSQL_URL and install dependencies first."
        )

    ok = init_mysql_schema()
    if not ok:
        raise SystemExit("Failed to initialize MySQL schema.")

    print("MySQL schema initialized successfully.")


if __name__ == "__main__":
    main()
