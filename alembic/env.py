"""
Alembic environment file.

Goal:
- Reuse the app's DB URL from `database.py` (which reads .env).
- Ensure all SQLAlchemy models are imported so `autogenerate` sees them.
- Keep secrets out of alembic.ini.
"""

from logging.config import fileConfig
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────────────────────
# 1) Make the project importable from here (alembic/ is a subfolder).
#    This lets us `import database` and `import models`.
# ──────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ──────────────────────────────────────────────────────────────────────────────
# 2) Load environment variables BEFORE importing app modules.
#    Otherwise `database.py` may not see PG* vars when building the URL.
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv(PROJECT_ROOT / ".env")

# ──────────────────────────────────────────────────────────────────────────────
# 3) Import app DB config and models.
#    - POSTGRES_DB_URL: single source of truth for connection string.
#    - Base.metadata: target for autogenerate.
#    - Importing `models` registers all mapped classes with Base.metadata.
# ──────────────────────────────────────────────────────────────────────────────
from database import Base, POSTGRES_DB_URL
import models  # ensure models are imported

# ──────────────────────────────────────────────────────────────────────────────
# 4) Alembic configuration: override alembic.ini URL with our runtime URL.
# ──────────────────────────────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Offline mode: build SQL statements without an active DB connection.
    Useful for generating SQL scripts.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # detect column type changes
        compare_server_default=True,  # detect server default changes
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live DB connection."""
    connectable = create_engine(POSTGRES_DB_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# Pick the mode based on how Alembic was invoked
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
