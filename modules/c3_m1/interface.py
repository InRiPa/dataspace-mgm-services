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
"""Public interface of C3-M1 Company Profile: the steps of Process Orchestration (README 8), the
queries of other modules (9) and the read paths.

Names and signatures follow the call convention of AGENTS.md: a step is
`def create_company(input: dict) -> dict` returning `{stepRunId, state, result}`, a query takes its
parameters by their openapi names. No token checks here.

Steps are idempotent (FRAMEWORK 4.4): the business key is looked up first, only what is missing is
created, a repetition returns the stored result and publishes nothing. Every changing operation
writes the audit log of README 5 and FRAMEWORK 4.3 before it publishes.
"""
from __future__ import annotations

import datetime as dt
import json

from portal_common import events, neighbours, standin
from portal_common.problems import Problem
from tools import testdata

from . import attestation, config, store, validation

MODULE = "c3-m1"


def _timestamp(value: str | None) -> dt.datetime | None:
    """Parse a stored ISO timestamp (`Z` or offset) to an instant; `None` when unreadable."""
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _audit(company_id: str | None, operation: str, input: dict, details: dict | None = None) -> None:
    """Steps carry `processId` and `stepRunId` instead of a `sub` (README 5, 4.3)."""
    store.audit(company_id, None, operation, None,
                (details or {}) | {"processId": input.get("processId"),
                                   "stepRunId": input.get("stepRunId")})


# ------------------------------------------------------------------------ start and seed (README 4)
def reset() -> None:
    """Empty state, then the seed data of the OSP company (README 4). Seed data has no events."""
    try:
        store.reset()
        target = store
    except Problem as error:
        if error.status != 501:
            raise
