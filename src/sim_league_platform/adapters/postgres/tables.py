"""SQLAlchemy table definitions for the PostgreSQL warehouse.

Tables are defined in Core style (not ORM) because:
- ETL workloads benefit from explicit SQL over ORM abstractions.
- Alembic's autogenerate works against the MetaData object built here.
- Ports-and-adapters keeps domain code free of SQLAlchemy types;
  this module is pure adapter concern.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Index,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

metadata = MetaData()

# Allowed values for raw_events.parse_status. Kept as a module-level
# constant so it can be referenced by domain code if needed without
# importing SQLAlchemy.
PARSE_STATUSES = ("pending", "ok", "failed")

raw_events = Table(
    "raw_events",
    metadata,
    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="Internal surrogate key.",
    ),
    Column(
        "source",
        Text,
        nullable=False,
        comment="Origin of the event, e.g. 'ocr_bot', 'manual'.",
    ),
    Column(
        "source_event_id",
        Text,
        nullable=False,
        comment="Natural ID assigned by the source system.",
    ),
    Column(
        "received_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this row was inserted into the warehouse.",
    ),
    Column(
        "occurred_at",
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When the underlying real-world event happened, if known.",
    ),
    Column(
        "payload",
        JSONB,
        nullable=False,
        comment="Verbatim payload from the source.",
    ),
    Column(
        "parsed",
        JSONB,
        nullable=True,
        comment="Structured representation produced by the parse step.",
    ),
    Column(
        "parse_status",
        Text,
        nullable=False,
        server_default=text("'pending'"),
        comment="Lifecycle: pending -> ok | failed.",
    ),
    Column(
        "parse_error",
        Text,
        nullable=True,
        comment="Error message if parse_status = 'failed'.",
    ),
    UniqueConstraint(
        "source",
        "source_event_id",
        name="uq_raw_events_source_natural_key",
    ),
    CheckConstraint(
        "parse_status IN ('pending', 'ok', 'failed')",
        name="ck_raw_events_parse_status",
    ),
)

# Index for operational queries: "show me recent events from this source".
Index(
    "ix_raw_events_source_received_at",
    raw_events.c.source,
    raw_events.c.received_at.desc(),
)

# Partial index so the parse worker can find pending rows cheaply
# without scanning rows that are already 'ok' or 'failed'.
Index(
    "ix_raw_events_pending",
    raw_events.c.id,
    postgresql_where=text("parse_status = 'pending'"),
)
