"""Database connection settings are supplied through environment variables.

Local development can use a .env file loaded by your shell or environment.
Never commit database credentials to source control.
"""
import os
import mysql.connector


def get_db_connection():
    required = ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError(
            "Missing database environment variable(s): " + ", ".join(missing)
        )

    config = {
        "host": os.environ["DB_HOST"],
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"],
        "database": os.environ["DB_NAME"],
        "connection_timeout": 10,
    }
    # Most managed MySQL-compatible cloud databases require TLS.
    if os.environ.get("DB_SSL", "true").strip().lower() in ("1", "true", "yes", "on"):
        config["ssl_disabled"] = False

    return mysql.connector.connect(**config)
