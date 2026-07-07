"""Portable column types.

Use the generic JSON type so the same models run on PostgreSQL (JSONB under the
hood) and on SQLite for local/dev/test.
"""
from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# JSONB on Postgres, plain JSON elsewhere.
JSONType = JSON().with_variant(JSONB(), "postgresql")
