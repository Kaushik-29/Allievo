import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import os
import sys

from alembic import context

# Add backend directory to sys.path so app modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import setup
from app.core.config import settings
from app.core.database import Base

# Import all models so Alembic can read them
from app.models.worker import Worker
from app.models.device_fingerprint import DeviceFingerprint
from app.models.earnings_snapshot import EarningsSnapshot
from app.models.zone_score import ZoneScore
from app.models.policy import Policy
from app.models.gps_ping import GpsPing
from app.models.trigger_event import TriggerEvent
from app.models.claim import Claim
from app.models.fraud_score import FraudScore
from app.models.payout import Payout
from app.models.ring_alert import RingAlert
from app.models.referral_graph import ReferralGraph
from app.models.upi_graph import UpiGraph

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the SQLAlchemy URL from Settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("postgres://", "postgresql://"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    # Ignore postgis spatial_ref_sys table
    if name == 'spatial_ref_sys':
        return False
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
