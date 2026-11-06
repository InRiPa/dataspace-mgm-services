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
"""The transport switch of `modules/c3_m1/store.py`: `DATABASE_URL` empty = in memory, set = the
module's own PostgreSQL database (README 4, 5).

The live tests need a server and are skipped without it:

    docker run --rm -d -p 55432:5432 -e POSTGRES_PASSWORD=pg -e POSTGRES_DB=c3_m1 postgres:16
    TEST_DATABASE_URL=postgresql://postgres:pg@localhost:55432/c3_m1 uv run pytest -q tests/test_c3_m1_store_backend.py
"""
import os

import pytest

from modules.c3_m1 import store

COMPANY = {
    "id": "c0000001-0000-4000-8000-000000000001", "name": "Beispiel Maschinenbau GmbH",
    "street": "Musterstraße 1", "city": "Stuttgart", "country_code": "DE",
    "status": "REQUESTED", "core_data_source": "EBW", "bpn": "BPNLIUK2REMLK3F4",
}


@pytest.fixture
def postgres_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set")
    return url


@pytest.fixture
def postgres(monkeypatch, postgres_url):
    monkeypatch.setenv("DATABASE_URL", postgres_url)
    pytest.importorskip("psycopg", reason="the PostgreSQL transport needs psycopg[binary]")
    assert store.backend_name() == "postgres"
    store.reset()
    yield store
    store.reset()


def test_the_default_transport_is_in_memory(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert store.backend_name() == "memory"
    assert store.backend().__name__ == "modules.c3_m1.store_memory"
