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
"""Regressions from the independent review: source protection, presence vs difference, audit content, DONE answers."""
import datetime as dt
import json

import pytest

from modules.c3_m1 import config, interface, store
from portal_common import events
from portal_common.problems import Problem

from fastapi import FastAPI
from fastapi.testclient import TestClient

from test_c3_m1_api import P1, P3, S1, S2, U1, U2, call
from portal_common import http as phttp
from portal_common import problems
from tools import test_iam
from modules.c3_m1 import router as c3_router
from test_c3_m1_api import BASE
from test_c3_m1_attestation import _keys, claims, sign  # noqa: F401
from test_c3_m1_steps import A1, A2, U3, seed, step

@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    problems.install(app)
    app.include_router(test_iam.router)
    app.include_router(c3_router.router)
    phttp.register_local(BASE, app)
    interface.reset()
    return TestClient(app, base_url=BASE)


@pytest.fixture
def active(client):
    """U1 ACTIVE with BPN, erika as Company Admin, otto as OSP Admin."""
    seed(A1, U1)
    step("create_company", companyId=U1, applicationId=A1)
    step("assign_identifier", companyId=U1, bpn="BPNLIUK2REMLK3F4")
    step("activate_company", companyId=U1, applicationId=A1)
    iam = test_iam.iam()
    for person, role in ((P1, "Company Admin"), (S2, "OSP Admin")):
        uid = iam.find(person) or ""
        iam.add_portal_roles(uid, [role])
    iam.bind(iam.find(P1) or "", U1, "BPNLIUK2REMLK3F4")
    return {"U1": U1}


S1_SUB = "bbede0f3-fbc4-433b-b7ca-1982e8724912"
S2_SUB = "5a1c0012-0000-4000-8000-000000000012"
P1_SUB = "5a1c0001-0000-4000-8000-000000000001"
PDF = ("auszug.pdf", b"%PDF-1.7 Auszug", "application/pdf")


# ------------------------------------------------------- the wallet identifiers are protected (blocker)
def test_a_change_request_may_not_carry_a_wallet_identifier(active):
    with pytest.raises(Problem) as error:
        interface.create_change_request(U1, {"comment": "x", "identifiers": [
            {"type": "EBWOID", "value": "EBWOID-DE-0000000009"},
            {"type": "VAT_ID", "value": "DE123456789"}]}, [PDF], P1_SUB)
    assert error.value.status == 400 and error.value.name == "validation"
    assert "identifiers.EBWOID" in [entry["field"] for entry in error.value.ext["errors"]]


def test_an_approval_keeps_the_wallet_identifiers(active):
    request = interface.create_change_request(U1, {"comment": "x", "identifiers": [
        {"type": "VAT_ID", "value": "DE123456789"}, {"type": "LEI_CODE", "value": "529900T8BM49AURSDO55"}]},
        [PDF], P1_SUB)
    interface.approve_change_request(request["id"], {}, S1_SUB)
    sources = {entry["type"]: entry["source"] for entry in store.list_identifiers(U1)}
    assert sources["EBWOID"] == "BUSINESS_WALLET" and sources["EUID"] == "BUSINESS_WALLET"
    assert sources["LEI_CODE"] == "DECLARED"


def test_an_empty_identifier_list_keeps_the_wallet_identifiers(active):
    request = interface.create_change_request(U1, {"comment": "x", "identifiers": []}, [PDF], P1_SUB)
    assert request["status"] == "OPEN"
    interface.approve_change_request(request["id"], {}, S1_SUB)
    assert {entry["type"] for entry in store.list_identifiers(U1)} == {"EBWOID", "EUID"}


# ------------------------------------------------ attestation-required needs a real difference (high)
def test_an_unchanged_name_does_not_need_an_attestation(active):
    request = interface.create_change_request(U1, {
        "comment": "x", "name": "Beispiel Maschinenbau GmbH",
        "identifiers": [{"type": "VAT_ID", "value": "DE123456789"},
                        {"type": "LEI_CODE", "value": "529900T8BM49AURSDO55"}]}, [PDF], P1_SUB)
    interface.approve_change_request(request["id"], {}, S1_SUB)
    assert store.get_company(U1)["core_data_source"] == "EBW"


def test_a_changed_name_still_needs_the_attestation(active):
