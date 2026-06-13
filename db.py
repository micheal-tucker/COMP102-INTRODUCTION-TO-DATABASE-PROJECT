import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

import mysql.connector
from mysql.connector import pooling


LOG_FILE = Path(os.getenv("CLINIC_LOG_FILE", Path(__file__).with_name("clinic_system.log")))
LOG_LEVEL = os.getenv("CLINIC_LOG_LEVEL", "INFO").upper()
LOGGER_NAME = "clinic_records"

_connection_pool = None


def configure_logging():
    """Configure app-wide file and console logging once."""
    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


logger = configure_logging()


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("CLINIC_DB_HOST", "localhost")
    user: str = os.getenv("CLINIC_DB_USER", "root")
    password: str = os.getenv("CLINIC_DB_PASSWORD", "")
    database: str = os.getenv("CLINIC_DB_NAME", "public_health_clinic_db")
    port: int = int(os.getenv("CLINIC_DB_PORT", "3306"))
    pool_name: str = os.getenv("CLINIC_DB_POOL_NAME", "clinic_records_pool")
    pool_size: int = int(os.getenv("CLINIC_DB_POOL_SIZE", "5"))
    connection_timeout: int = int(os.getenv("CLINIC_DB_CONNECTION_TIMEOUT", "10"))

    def connection_args(self):
        return {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "port": self.port,
            "connection_timeout": self.connection_timeout,
        }


def compact_sql(query):
    return " ".join(query.split())


def get_pool(config: DatabaseConfig | None = None):
    """Create or reuse a MySQL/MariaDB connection pool for XAMPP."""
    global _connection_pool

    config = config or DatabaseConfig()
    if _connection_pool is None:
        logger.info(
            "Creating database connection pool '%s' for %s:%s/%s",
            config.pool_name,
            config.host,
            config.port,
            config.database,
        )
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name=config.pool_name,
            pool_size=config.pool_size,
            pool_reset_session=True,
            **config.connection_args(),
        )

    return _connection_pool


def get_connection(config: DatabaseConfig | None = None):
    """Return a pooled XAMPP-compatible database connection."""
    try:
        return get_pool(config).get_connection()
    except mysql.connector.Error:
        logger.exception("Failed to get a database connection from the pool")
        raise


@contextmanager
def connection_context(config: DatabaseConfig | None = None):
    """Context manager that returns pooled connections and always releases them."""
    conn = get_connection(config)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def cursor_context(commit=False, dictionary=False):
    """Context manager for cursor lifecycle, commits, rollbacks, and logging."""
    with connection_context() as conn:
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            if commit:
                conn.rollback()
            logger.exception("Database operation failed")
            raise
        finally:
            cursor.close()


def fetch_all(query, params=None, dictionary=False):
    """Run a SELECT query and return all rows."""
    logger.debug("Fetching rows: %s", compact_sql(query))
    with cursor_context(dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        logger.debug("Fetched %s rows", len(rows))
        return rows


def fetch_one(query, params=None, dictionary=False):
    """Run a SELECT query and return a single row."""
    logger.debug("Fetching one row: %s", compact_sql(query))
    with cursor_context(dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        logger.debug("Fetched one row: %s", "yes" if row else "no")
        return row


def execute(query, params=None):
    """Run an INSERT, UPDATE, or DELETE statement and commit the change."""
    logger.info("Executing write statement: %s", compact_sql(query))
    with cursor_context(commit=True) as cursor:
        cursor.execute(query, params or ())
        result = {
            "lastrowid": cursor.lastrowid,
            "rowcount": cursor.rowcount,
        }
        logger.info(
            "Write committed: rowcount=%s lastrowid=%s",
            result["rowcount"],
            result["lastrowid"],
        )
        return result


def execute_many(query, rows):
    """Run one INSERT, UPDATE, or DELETE statement for many parameter rows."""
    logger.info("Executing bulk write statement: %s", compact_sql(query))
    with cursor_context(commit=True) as cursor:
        cursor.executemany(query, rows)
        result = {
            "lastrowid": cursor.lastrowid,
            "rowcount": cursor.rowcount,
        }
        logger.info(
            "Bulk write committed: rowcount=%s lastrowid=%s",
            result["rowcount"],
            result["lastrowid"],
        )
        return result


def execute_write(query, params=None):
    """Backward-compatible alias for execute()."""
    return execute(query, params)
