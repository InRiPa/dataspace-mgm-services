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
"""Store and validation of C3-M1 without HTTP: README 5 tables, the constraints the database
would carry, the field rules of 5, the identifier rules of 6.4 and the comparison of 6.3."""
import itertools
import json

import pytest

from modules.c3_m1 import store
from modules.c3_m1 import validation as v
from portal_common import settings

_ids = itertools.count(1)


@pytest.fixture(autouse=True)
def _empty_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def make():
    """A company row in the shape of README 5 (id assigned here, the store validates it)."""
    def _make(**fields) -> dict:
        n = next(_ids)
        row = {"id": f"c00000{n:02d}-0000-4000-8000-{n:012d}", "name": f"Beispiel Firma {n}",
               "street": "Musterstraße 1", "city": "Stuttgart", "country_code": "DE",
               "status": "ACTIVE"}
        row.update(fields)
        return store.create_company(row)
    return _make


# ------------------------------------------------------------------------------- company (5)
def test_get_company_returns_a_copy(make):
    company = make()
    fetched = store.get_company(company["id"])
    fetched["name"] = "geändert"
    assert store.get_company(company["id"])["name"] == company["name"]
    assert store.get_company("unknown") is None


def test_create_company_fills_defaults_and_timestamps(make):
    company = store.create_company({"id": "c0000001-0000-4000-8000-000000000001", "name": "A",
                                    "street": "Weg 1", "city": "Stadt", "country_code": "DE"})
    assert company["status"] == "REQUESTED"
    assert company["core_data_source"] == "MANUAL"
    assert company["bpn"] is None
    assert company["created_at"] and company["changed_at"]
    assert set(company) == set(store.COMPANY_FIELDS)


def test_create_company_rejects_unknown_field(make):
    with pytest.raises(ValueError):
        make(payload="x")


def test_update_company_sets_changed_at_and_returns_none_for_unknown(make):
    company = make()
    changed = store.update_company(company["id"], short_name="Kurz")
    assert changed["short_name"] == "Kurz"
    assert changed["changed_at"] >= company["changed_at"]
    assert store.update_company("unknown", short_name="x") is None


def test_bpn_is_stored_in_upper_case(make):
    assert make(bpn="bpnl00000000aaaa")["bpn"] == "BPNL00000000AAAA"


def test_bpn_is_unique_among_companies_that_are_not_rejected(make):
    make(bpn="BPNL00000000AAAA")
    with pytest.raises(ValueError):
        make(bpn="BPNL00000000AAAA")


def test_bpn_of_a_rejected_company_frees_it(make):
    rejected = make(bpn="BPNL00000000AAAA", status="REJECTED")
    assert make(bpn="BPNL00000000AAAA")["bpn"] == "BPNL00000000AAAA"
    assert store.get_company(rejected["id"])["bpn"] == "BPNL00000000AAAA"


def test_reactivating_a_rejected_company_takes_a_free_bpn(make):
    rejected = make(bpn="BPNL00000000AAAA", status="REJECTED")
    other = make()
    assert store.update_company(rejected["id"], status="ACTIVE", bpn="BPNL00000000AAAA")
    with pytest.raises(ValueError):
        store.update_company(other["id"], bpn="BPNL00000000AAAA")


def test_rejecting_a_company_keeps_its_bpn(make):
