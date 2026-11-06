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
"""In-memory transport of the C3-M1 repository (README 5), used while `DATABASE_URL` is empty.

One function per table, rows are dicts with the snake_case field names of README 5; the router and
the interface map them to camelCase. The shape mirrors the tables one-to-one, so the PostgreSQL
transport in `store_postgres.py` answers the same functions: `lock()` is the placeholder for
`SELECT ... FOR UPDATE` (README 6.9), and every constraint that the database carries (enums, one
identifier per type, one OPEN change request per company, BPN unique among companies that are not
`REJECTED`) is enforced here as well.

Reads return copies: a caller changes rows through `update_company` and the other write functions,
never by mutating a returned dict. No FastAPI, no HTTP, no events.
"""
from __future__ import annotations

import contextlib
import copy
import datetime as dt
import hashlib
import uuid

from .store import (CORE_DATA_SOURCES, CHANGE_REQUEST_STATUSES, COMPANY_FIELDS, CONSENT_SOURCE_KINDS,
                    CONSENT_STATUSES, DEACTIVATION_REASONS, IDENTIFIER_SOURCES, IDENTIFIER_TYPES,
                    MEDIA_TYPES, ROLE_SOURCE_KINDS, ROLE_STATUSES, STATUSES)
from .validation import value_normalized

companies: dict[str, dict] = {}
_identifiers: dict[str, dict[str, dict]] = {}
_roles: dict[str, dict[str, dict]] = {}
_consents: dict[tuple[str, str], dict] = {}
_change_requests: dict[str, dict] = {}
_documents: dict[str, dict] = {}
_used_attestations: dict[str, dict] = {}
_audit: list[dict] = []


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _copy(row: dict | None) -> dict | None:
    return copy.deepcopy(row) if row is not None else None


def _check_enum(value, allowed: tuple[str, ...], field: str) -> None:
    if value is not None and value not in allowed:
        raise ValueError(f"{field}: {value!r} is not one of {', '.join(allowed)}")


def _check_known(company_id: str) -> dict:
    if company_id not in companies:
        raise ValueError(f"unknown company: {company_id}")
    return companies[company_id]


def _checked_bpn(bpn, *, company_id: str | None, status: str) -> str | None:
    """Upper case and unique among the companies whose status is not `REJECTED` (README 5)."""
    if bpn in (None, ""):
        return None
    if not isinstance(bpn, str):
        raise ValueError("bpn: not a string")
    bpn = bpn.strip().upper()
    if status != "REJECTED":
        for other_id, other in companies.items():
            if other_id != company_id and other["status"] != "REJECTED" and other.get("bpn") == bpn:
                raise ValueError(f"bpn: {bpn} belongs to company {other_id}")
    return bpn


def reset() -> None:
    """Empty every table (test helper; the PostgreSQL transport drops and recreates the schema)."""
    companies.clear()
    _identifiers.clear()
    _roles.clear()
    _consents.clear()
    _change_requests.clear()
    _documents.clear()
    _used_attestations.clear()
    _audit.clear()


@contextlib.contextmanager
def lock(company_id: str | None = None):
    """Placeholder for the row lock of README 6.9 (`SELECT ... FOR UPDATE`).

    In memory there is no concurrency; the context manager only documents where the later
    database transport takes the lock. It yields the `companyId` and never looks the company up.
    """
    yield company_id


# ------------------------------------------------------------------ company (README 5)
def get_company(company_id: str | None) -> dict | None:
    return _copy(companies.get(company_id)) if company_id else None


def create_company(row: dict) -> dict:
    unknown = set(row) - set(COMPANY_FIELDS)
    if unknown:
        raise ValueError(f"unknown company fields: {', '.join(sorted(unknown))}")
    if not row.get("id"):
        raise ValueError("id: required")
    if row["id"] in companies:
        raise ValueError(f"id: company {row['id']} exists")
    status = row.get("status") or "REQUESTED"
    core_data_source = row.get("core_data_source") or "MANUAL"
    _check_enum(status, STATUSES, "status")
    _check_enum(core_data_source, CORE_DATA_SOURCES, "core_data_source")
    _check_enum(row.get("deactivation_reason"), DEACTIVATION_REASONS, "deactivation_reason")
    if row.get("deactivation_reason") and status != "INACTIVE":
        raise ValueError("deactivation_reason: only with status INACTIVE")
    now = _now()
    created: dict = {field: None for field in COMPANY_FIELDS}
    created.update({key: value for key, value in row.items() if value is not None})
    created.update({
        "id": row["id"], "status": status, "core_data_source": core_data_source,
        "bpn": _checked_bpn(row.get("bpn"), company_id=row["id"], status=status),
        "created_at": row.get("created_at") or now, "changed_at": row.get("changed_at") or now,
    })
    companies[str(created["id"])] = created
    return _copy(created)  # type: ignore[return-value]


def update_company(company_id: str, **fields) -> dict | None:
    row = companies.get(company_id)
    if row is None:
        return None
    unknown = set(fields) - set(COMPANY_FIELDS) - {"id"}
