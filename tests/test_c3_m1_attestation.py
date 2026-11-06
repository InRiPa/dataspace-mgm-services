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
"""The verification attestation of README 6.7 and its use in 7.3 (acceptance 11, 12).

The key pair lives next to the module: `stub-ebw-jwks.json` holds the public JWK, `stub-ebw-key.json`
the private one (README 14: "private part only in the test data"). T4 is signed with a second key
that is not in the file.
"""
import datetime as dt
import json
from pathlib import Path

import jwt
import pytest

from modules.c3_m1 import interface, store
from portal_common import events
from portal_common.problems import Problem

from test_c3_m1_api import P3, active, call, client  # noqa: F401  (fixtures for the HTTP test)
from test_c3_m1_steps import A1, U1, P1, U2, A2, seed, step

MODULE_DIR = Path(__file__).resolve().parents[1] / "modules" / "c3_m1"
PRIVATE = json.loads((MODULE_DIR / "stub-ebw-key.json").read_text(encoding="utf-8"))["keys"][0]
JWKS = MODULE_DIR / "stub-ebw-jwks.json"


@pytest.fixture(autouse=True)
def _keys(monkeypatch):
    monkeypatch.setenv("ATTESTATION_ISSUER", "https://ebw-connector.example.org")
    monkeypatch.setenv("ATTESTATION_AUDIENCE", "portal-registration")
    monkeypatch.setenv("ATTESTATION_CLIENT_IDS", "demo-osp")
    monkeypatch.setenv("ATTESTATION_JWKS_FILE", str(JWKS))
    interface.reset()
    yield


def now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def sign(claims: dict, key: dict = PRIVATE, *, typ: str = "ebw-attestation+jwt") -> str:
    return jwt.encode(claims, jwt.PyJWK(key).key, algorithm="ES256",
                      headers={"typ": typ, "kid": key["kid"]})
