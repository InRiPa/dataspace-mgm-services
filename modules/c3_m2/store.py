#################################################################################
#  Copyright (c) 2026 Technovative Solutions
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
#  Assisted-By: Claude Code (claude-opus-5-5)
#################################################################################
"""Own data of C3-M2 (README 5), in memory for the hackathon.

The rows keep the column names of the tables `csp_registration`, `csp_connector`,
`csp_notification` and `audit_entry`; `interface.registration_view` maps a row to the camelCase
of the API. Nothing here holds company data beyond the BPN, and
the audit log holds no response content and no tokens (README 5).
"""
from __future__ import annotations

import datetime as dt
import json

from portal_common import settings

registrations: dict[str, dict] = {}    # company_id -> row of csp_registration
connectors: dict[str, dict] = {}       # connector_id -> row of csp_connector
notifications: dict[str, dict] = {}    # notification_id -> row of csp_notification
audit: list[dict] = []                 # rows of audit_entry


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def reset() -> None:
    registrations.clear()
    connectors.clear()
    notifications.clear()
    audit.clear()
    seed()


def seed() -> None:
    """README 4 "Seed data": the OSP company from `ospCompanyFile` as `REGISTERED`, without a call
    to the CSP and without events. A second run changes nothing."""
    path = settings.resolve_path(settings.get("ospCompanyFile"))
    if path is None or not path.exists():
        return
    company = json.loads(path.read_text(encoding="utf-8"))
    company_id, bpn = company.get("companyId"), company.get("bpn")
    if not company_id or not bpn or company_id in registrations:
        return
    row = new_registration(company_id)
    row.update(bpn=bpn, status="REGISTERED", membership="REGISTERED", registered_at=row["updated_at"])
    registrations[company_id] = row


def new_registration(company_id: str) -> dict:
    return {"company_id": company_id, "bpn": None, "status": None, "failure_reason": None,
            "pending_operation_id": None, "did": None, "membership": "NONE", "registered_at": None,
            "updated_at": now(), "last_update_step_run": None}


def registration_row(company_id: str) -> dict:
    """The row of the company; created (without status) if there is none yet."""
    row = registrations.get(company_id)
    if row is None:
        row = registrations[company_id] = new_registration(company_id)
    return row


def touch(row: dict) -> None:
    row["updated_at"] = now()


def find_by_operation(operation_id: str) -> dict | None:
    return next((r for r in registrations.values() if r["pending_operation_id"] == operation_id), None)


def find_by_bpn(bpn: str, *, exclude: str | None = None, status: str | None = None) -> dict | None:
    return next((r for r in registrations.values()
                 if r["bpn"] == bpn and r["company_id"] != exclude and (status is None or r["status"] == status)),
                None)


def record_audit(operation: str, company_id: str | None, bpn: str | None, http_status: int | None,
                 error_type: str | None = None) -> None:
    audit.append({"time": now(), "operation": operation, "company_id": company_id, "bpn": bpn,
                  "http_status": http_status, "error_type": error_type})
