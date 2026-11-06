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
"""Change requests with supporting documents and the four-eyes decision (README 7.4-7.6, 7.14-7.18, 13.13-13.16)."""
import pytest

from modules.c3_m1 import interface, store
from portal_common import events
from portal_common.problems import Problem

from test_c3_m1_api import P1, P3, S1, S2, U1, U2, active, call, client  # noqa: F401

PDF = ("auszug.pdf", b"%PDF-1.7 Auszug", "application/pdf")
S2_SUB = "5a1c0012-0000-4000-8000-000000000012"
S1_SUB = "bbede0f3-fbc4-433b-b7ca-1982e8724912"
P1_SUB = "5a1c0001-0000-4000-8000-000000000001"


def submit(company: str = U1, person: str = P1_SUB, **data) -> dict:
    payload = data or {"identifiers": [{"type": "VAT_ID", "value": "DE123456789"},
                                       {"type": "LEI_CODE", "value": "529900T8BM49AURSDO55"}]}
    payload.setdefault("comment", "Bitte ändern")
    return interface.create_change_request(company, payload, [PDF], person)


# ------------------------------------------------------------------------------------------ 13.13
def test_a_name_change_of_an_ebw_company_needs_the_attestation(active):
    with pytest.raises(Problem) as error:
        submit(name="Beispiel Maschinenbau AG")
    assert error.value.status == 409 and error.value.name == "attestation-required"


def test_the_event_fields_are_the_ones_c11_reads(active):
    """FRAMEWORK 6 / README 10: `companyId` and `changeRequestId`, closed also `outcome` (C11-M1)."""
    answer = submit()
    assert set(events.RELAY.log[-1]["data"]) == {"companyId", "changeRequestId"}
    interface.withdraw_change_request(U1, answer["id"], P1_SUB)
    closed = events.RELAY.log[-1]
    assert closed["type"] == "CompanyChangeRequestClosed"
    assert set(closed["data"]) == {"companyId", "changeRequestId", "outcome"}
    assert closed["data"]["outcome"] == "WITHDRAWN"


def test_a_request_with_identifiers_is_created(active):
    answer = submit()
    assert answer["status"] == "OPEN" and answer["documents"][0]["fileName"] == "auszug.pdf"
    assert len(events.RELAY.log) >= 1
    assert events.RELAY.log[-1]["type"] == "CompanyChangeRequestSubmitted"
    with pytest.raises(Problem) as error:
        submit()
    assert error.value.status == 409 and error.value.name == "change-request-open"

