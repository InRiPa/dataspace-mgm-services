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
