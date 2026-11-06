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
"""HTTP layer of C3-M1: permissions, scope `company`, corrections (README 6.8, 7.1, 7.2, 7.10-7.12, 13).

Tokens come from the in-memory test IAM of the scaffold; permissions are read from the spec there.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from modules.c3_m1 import interface, router as c3_router
from portal_common import http as phttp
from portal_common import problems, standin
from tools import test_iam

from conftest import BASE, bearer, person_token

U1 = "c0000001-0000-4000-8000-000000000001"
U2 = "c0000002-0000-4000-8000-000000000002"
P1, P2, P3, P4 = "erika", "max", "hans", "lieschen"
S1, S2 = "rolf", "otto"


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    problems.install(app)
    app.include_router(test_iam.router)
    app.include_router(c3_router.router)
    app.include_router(standin.fallback_router(c3_router.MODULE, c3_router.router))   # as scaffold/app.py
    phttp.register_local(BASE, app)
    interface.reset()
    return TestClient(app, base_url=BASE)


@pytest.fixture
def active(client: TestClient) -> dict:
    """U1 and U2 ACTIVE with BPN, erika/max bound to U1, hans to U2."""
    from test_c3_m1_steps import A1, A2, seed, step
    seed(A1, U1)
    seed(A2, U2, verification="DOCUMENTS", _attestation=None,
         companyData={"legalName": "Beispiel Logistik GmbH",
                      "address": {"streetName": "Hafenstraße", "streetNumber": "5",
                                  "postalCode": "68159", "city": "Mannheim", "countryCode": "DE"},
                      "identifiers": [{"type": "VAT_ID", "value": "DE987654321",
                                       "source": "APPLICANT"}]},
         consents=[{"agreementKey": "terms-active-participant", "version": "1.0",
                    "language": "en", "givenAt": "2026-11-06T08:05:00+00:00"},
                   {"agreementKey": "security-regulations", "version": "1.0",
                    "language": "en", "givenAt": "2026-11-06T08:05:00+00:00"}])
    for company, application, bpn in ((U1, A1, "BPNLIUK2REMLK3F4"), (U2, A2, "BPNL00000000U2LG")):
        step("create_company", companyId=company, applicationId=application)
        step("assign_identifier", companyId=company, bpn=bpn)
        step("activate_company", companyId=company, applicationId=application)
    iam = test_iam.iam()
    for person, role, company, bpn in ((P1, "Company Admin", U1, "BPNLIUK2REMLK3F4"),
                                       (P2, "Member", U1, "BPNLIUK2REMLK3F4"),
                                       (P3, "Company Admin", U2, "BPNL00000000U2LG")):
        uid = iam.find(person) or ""
        iam.add_portal_roles(uid, [role])
        iam.bind(uid, company, bpn)
    return {"U1": U1, "U2": U2}


def call(client: TestClient, method: str, path: str, person: str | None = None, **kwargs):
    """As a person; `person` = "svc" uses the service account of the module (query_c3_m1)."""
    if person == "svc":
        headers = bearer(test_iam.iam().client_token("svc-c3-m1"))
    else:
        headers = bearer(person_token(person)) if person else {}
    return client.request(method, path, headers=headers, **kwargs)

