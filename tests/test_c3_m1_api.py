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
