#################################################################################
#  Copyright (c) 2026 Contributors to the Eclipse Foundation
#
#  See the NOTICE file(s) distributed with this work for additional
#  information regarding copyright ownership.
#
#  This program and the accompanying materials are made available under the
#  terms of the Apache License, Version 2.0 which is available at
#  https://www.apache.org/licenses/LICENSE-2.0.
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
#
#  AI Disclosure: This file was entirely AI-generated.
#  The AI-generated portions are made available under CC0-1.0 and not subject
#  to the project's license. The human contributor has reviewed and verified
#  that the code is correct.
#
#  SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
#  Assisted-By: Hermes Agent (deepseek-v4.1-flash)
#################################################################################
"""PostgreSQL transport of the C3-M1 repository: the module's own database `c3_m1` (README 4, 5).

Active when `DATABASE_URL` is set; the schema is `schema.sql` next to this file. The functions,
the field names and the invariants are the ones of `store_memory`, so the caller never learns
which transport runs. Timestamps leave as ISO 8601 strings and bytea as `bytes`, like the memory
transport returns them.

`psycopg` is imported at module load: `DATABASE_URL` set without the driver is an error naming the
package (store.py). Nothing here is FastAPI, HTTP or events.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import json
import os
import zlib
import uuid
from pathlib import Path

import psycopg
from psycopg import errors
from psycopg.rows import dict_row

from .store import (CHANGE_REQUEST_STATUSES, COMPANY_FIELDS, CONSENT_STATUSES, CORE_DATA_SOURCES,
                    DEACTIVATION_REASONS, IDENTIFIER_SOURCES, IDENTIFIER_TYPES, MEDIA_TYPES,
                    ROLE_SOURCE_KINDS, ROLE_STATUSES, STATUSES)
from .validation import value_normalized

SCHEMA = Path(__file__).with_name("schema.sql")
TABLES = ("audit_log", "used_attestation", "change_request_document", "change_request", "consent",
          "company_role_assignment", "company_identifier", "company")

COMPANY_KEYWORDS = (
    "short_name", "house_number", "address_addition", "postal_code", "region", "bpn",
    "bpn_assigned_at", "core_data_verified_at", "verification_ref", "application_id",
    "deactivation_reason", "activated_at", "rejected_at", "deactivated_at", "reactivated_at",
    "changed_at",
)

def _dsn() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is empty; the PostgreSQL transport needs the database `c3_m1`")
    return dsn


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _row(row: dict | None) -> dict | None:
    """Normalise a database row to the shapes the memory transport returns."""
    if row is None:
        return None
    for key, value in row.items():
        if isinstance(value, uuid.UUID):
            row[key] = str(value)
    for key in ("content",):
        if isinstance(row.get(key), memoryview | bytearray):
            row[key] = bytes(row[key])
    for key in ("created_at", "changed_at", "occurred_at", "used_at", "closed_at",
                "activated_at", "deactivated_at", "reactivated_at", "rejected_at",
                "bpn_assigned_at", "core_data_verified_at", "consented_at"):
        if isinstance(row.get(key), dt.datetime):
            row[key] = row[key].isoformat()
    return row


@contextlib.contextmanager
def _connection():
    with psycopg.connect(_dsn(), row_factory=dict_row) as connection:
        yield connection


def _fetch_one(connection, sql: str, params: tuple | dict = ()) -> dict | None:
    return _row(connection.execute(sql, params).fetchone())


def _fetch_all(connection, sql: str, params: tuple | dict = ()) -> list[dict]:
    return [_row(row) for row in connection.execute(sql, params).fetchall()]  # type: ignore[misc]


def _check_enum(value, allowed: tuple[str, ...], field: str) -> None:
    if value is not None and value not in allowed:
        raise ValueError(f"{field}: {value!r} is not one of {', '.join(allowed)}")


def _uuid_ok(value) -> bool:
    """A path parameter may be anything; PostgreSQL refuses a non-UUID instead of answering empty."""
    try:
        uuid.UUID(str(value))
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def _check_known(connection, company_id: str) -> None:
    if not _uuid_ok(company_id) or _fetch_one(
            connection, "SELECT id FROM company WHERE id = %s", (company_id,)) is None:
        raise ValueError(f"unknown company: {company_id}")


def _integrity(error: errors.IntegrityError) -> ValueError:
    """Database constraint -> ValueError, like the memory transport raises it."""
    if isinstance(error, errors.UniqueViolation):
        constraint = getattr(getattr(error, "diag", None), "constraint_name", "") or ""
        if "bpn" in constraint:
            return ValueError("bpn: belongs to another company with a status other than REJECTED")
        if "open_per_company" in constraint:
            return ValueError(f"company already has an open change request ({constraint})")
        return ValueError(f"unique violation: {constraint or error.diag.message_detail}")
    return ValueError(str(error))


def reset() -> None:
    """Drop the module's tables and apply `schema.sql` again."""
    script = SCHEMA.read_text(encoding="utf-8")
    with _connection() as connection:
        for table in TABLES:
            connection.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        connection.execute(script)


@contextlib.contextmanager
def lock(company_id: str | None = None):
    """Lock of README 6.9 for the duration of the block, one caller per company.

    A session advisory lock instead of `SELECT ... FOR UPDATE`: the write functions of this
    transport run in their own transactions, so a row lock held here would block on the very
    UPDATE of the same row the block performs. The advisory key is the company, the unlock is
    guaranteed in `finally`.
    """
    key = zlib.crc32(company_id.encode()) if company_id else 0
    with psycopg.connect(_dsn(), autocommit=True) as connection:
        if company_id:
            connection.execute("SELECT pg_advisory_lock(%s)", (key,))
        try:
            yield company_id
        finally:
            if company_id:
                connection.execute("SELECT pg_advisory_unlock(%s)", (key,))


# ------------------------------------------------------------------ company (README 5)
def get_company(company_id: str | None) -> dict | None:
    if not company_id or not _uuid_ok(company_id):
        return None
    with _connection() as connection:
        return _fetch_one(connection, "SELECT * FROM company WHERE id = %s", (company_id,))


def create_company(row: dict) -> dict:
    unknown = set(row) - set(COMPANY_FIELDS)
    if unknown:
        raise ValueError(f"unknown company fields: {', '.join(sorted(unknown))}")
    if not row.get("id"):
        raise ValueError("id: required")
    status = row.get("status") or "REQUESTED"
    _check_enum(status, STATUSES, "status")
    _check_enum(row.get("core_data_source") or "MANUAL", CORE_DATA_SOURCES, "core_data_source")
    _check_enum(row.get("deactivation_reason"), DEACTIVATION_REASONS, "deactivation_reason")
    now = _now()
    values = {field: row.get(field) for field in COMPANY_FIELDS}
    values.update({"id": row["id"], "status": status,
                   "core_data_source": row.get("core_data_source") or "MANUAL",
                   "bpn": (row.get("bpn") or "").strip().upper() or None,
                   "created_at": row.get("created_at") or now, "changed_at": row.get("changed_at") or now})
    columns = ", ".join(COMPANY_FIELDS)
    placeholders = ", ".join(f"%({field})s" for field in COMPANY_FIELDS)
    with _connection() as connection:
        try:
            created = _fetch_one(connection,
                                 f"INSERT INTO company ({columns}) VALUES ({placeholders}) RETURNING *",
                                 values)
        except errors.IntegrityError as error:
            raise _integrity(error) from None
    return created  # type: ignore[return-value]


def update_company(company_id: str, **fields) -> dict | None:
    if not fields:
        return get_company(company_id)
    if not _uuid_ok(company_id):
        return None
    unknown = set(fields) - set(COMPANY_FIELDS) - {"id", "created_at"}
    if unknown:
        raise ValueError(f"unknown company fields: {', '.join(sorted(unknown))}")
    if "status" in fields:
        _check_enum(fields["status"], STATUSES, "status")
    if "core_data_source" in fields:
        _check_enum(fields["core_data_source"], CORE_DATA_SOURCES, "core_data_source")
    if "deactivation_reason" in fields:
        _check_enum(fields["deactivation_reason"], DEACTIVATION_REASONS, "deactivation_reason")
    if "bpn" in fields:
        fields["bpn"] = (fields["bpn"] or "").strip().upper() or None
    assignments = ", ".join(f"{field} = %({field})s" for field in fields)
