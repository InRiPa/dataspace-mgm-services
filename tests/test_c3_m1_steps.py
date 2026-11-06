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
"""C3-M1 steps and queries against the built-in stand-in of C1-M2 (README 8, 9, 13).

The applications of README 14 (A1, A2, A3, A5) are seeded into the C1-M2 stand-in, which is what
`create-company` and `activate-company` read over the neighbour call (11.1).
"""
import json

import pytest

from modules.c1_m2 import interface as c1_m2
from modules.c3_m1 import interface, store
from portal_common import events
from portal_common.problems import Problem

U1 = "c0000001-0000-4000-8000-000000000001"
U2 = "c0000002-0000-4000-8000-000000000002"
U3 = "c0000003-0000-4000-8000-000000000003"
A1 = "a0000001-0000-4000-8000-000000000001"
A2 = "a0000002-0000-4000-8000-000000000002"
A3 = "a0000003-0000-4000-8000-000000000003"
A5 = "a0000005-0000-4000-8000-000000000005"
P1 = "5a1c0001-0000-4000-8000-000000000001"

ATTESTATION = {"attestationId": "3f6c1e2a-7b4d-4e8f-9a51-2c0d6b8e4f17",
               "verifiedAt": "2026-11-06T08:00:00+00:00"}
CONSENTS = [{"agreementKey": "terms-active-participant", "version": "1.0", "language": "en",
             "givenAt": "2026-11-06T08:05:00+00:00"},
            {"agreementKey": "security-regulations", "version": "1.0", "language": "en",
             "givenAt": "2026-11-06T08:05:00+00:00"}]
ADDRESS = {"streetName": "Musterstraße", "streetNumber": "1", "postalCode": "70569",
           "city": "Stuttgart", "region": "BW", "countryCode": "DE"}


@pytest.fixture(autouse=True)
def _state():
    interface.reset()
    yield


def seed(application: str = A1, company: str = U1, **over) -> dict:
    """Seed an application of README 14 into the C1-M2 stand-in."""
    entry = {
        "id": application, "companyId": company, "kind": "ONBOARDING", "existingCompany": False,
        "status": "SUBMITTED", "verification": "EBW", "_attestation": ATTESTATION,
        "applicant": {"sub": P1},
        "companyData": {"legalName": "Beispiel Maschinenbau GmbH", "address": ADDRESS,
                        "identifiers": [{"type": "EBWOID", "value": "EBWOID-DE-0000000001",
                                         "source": "ATTESTATION"},
                                        {"type": "EUID", "value": "DEXX001T.HRB100001",
                                         "source": "ATTESTATION"},
                                        {"type": "VAT_ID", "value": "DE123456789",
                                         "source": "APPLICANT"}]},
        "companyRoles": ["ACTIVE_PARTICIPANT"], "consents": CONSENTS,
    }
    entry.update(over)
    c1_m2.applications[entry["id"]] = entry
    return entry


def step(name: str, **payload) -> dict:
    payload.setdefault("processId", "p-1")
    payload.setdefault("stepRunId", "s-1")
    return getattr(interface, name)(payload)


def published(name: str) -> list[dict]:
    return [event for event in events.RELAY.log if event["type"] == name]

