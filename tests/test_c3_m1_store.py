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
    company = make(bpn="BPNL00000000AAAA")
    assert store.update_company(company["id"], status="REJECTED")["bpn"] == "BPNL00000000AAAA"


def test_status_enum_is_enforced(make):
    with pytest.raises(ValueError):
        make(status="DELETED")
    company = make()
    with pytest.raises(ValueError):
        store.update_company(company["id"], status="DELETED")


def test_core_data_source_enum_is_enforced(make):
    with pytest.raises(ValueError):
        make(core_data_source="MASTER_DATA")


def test_deactivation_reason_enum_and_state_are_enforced(make):
    with pytest.raises(ValueError):
        make(status="INACTIVE", deactivation_reason="NO_PSP")
    with pytest.raises(ValueError):
        make(status="ACTIVE", deactivation_reason="MANUAL")
    company = make()
    assert store.update_company(company["id"], status="INACTIVE",
                                deactivation_reason="MANUAL")["deactivation_reason"] == "MANUAL"
    with pytest.raises(ValueError):
        store.update_company(company["id"], status="ACTIVE")


def test_find_companies_filters(make):
    active = make(bpn="BPNL00000000AAAA", core_data_source="EBW")
    make(name="Andere Logistik GmbH", status="REQUESTED")
    make(status="REJECTED")
    assert [c["id"] for c in store.find_companies(status="REQUESTED")[0]] != []
    assert all(c["status"] == "REQUESTED" for c in store.find_companies(status=["REQUESTED"])[0])
    found, total = store.find_companies(name="logistik")
    assert total == 1 and found[0]["name"] == "Andere Logistik GmbH"
    assert [c["id"] for c in store.find_companies(bpn="bpnl00000000aaaa")[0]] == [active["id"]]
    assert all(c["bpn"] for c in store.find_companies(has_bpn=True)[0])
    assert all(not c["bpn"] for c in store.find_companies(has_bpn=False)[0])
    assert all(c["core_data_source"] == "EBW" for c in store.find_companies(core_data_source="EBW")[0])


def test_find_companies_company_role_matches_active_roles_only(make):
    company = make()
    other = make()
    store.add_role(company["id"], "ACTIVE_PARTICIPANT", status="ACTIVE")
    store.add_role(other["id"], "APP_PROVIDER", status="REQUESTED")
    found, total = store.find_companies(company_role="ACTIVE_PARTICIPANT")
    assert total == 1 and found[0]["id"] == company["id"]
    assert store.find_companies(company_role="APP_PROVIDER")[1] == 0


def test_find_companies_is_newest_first_and_paged(make):
    companies = [make() for _ in range(5)]
    items, total = store.find_companies(page=0, size=2)
    assert total == 5 and len(items) == 2
    assert items[0]["id"] == companies[-1]["id"]      # newest first (7.10)
    rest, _ = store.find_companies(page=2, size=2)
    assert len(rest) == 1


# --------------------------------------------------------------------------- identifiers (5, 6.4)
def test_set_identifiers_normalises_and_replaces(make):
    company = make()
    rows = store.set_identifiers(company["id"], [
        {"type": "VAT_ID", "value": "de 123.456.789", "source": "DECLARED"},
        {"type": "EUID", "value": "DEXX001T.HRB100001", "source": "BUSINESS_WALLET"},
    ])
    assert {row["type"] for row in rows} == {"VAT_ID", "EUID"}
    by_type = {row["type"]: row for row in store.list_identifiers(company["id"])}
    assert by_type["VAT_ID"]["value_normalized"] == "DE123456789"
    store.set_identifiers(company["id"], [{"type": "LEI_CODE", "value": "A" * 20}])
    assert [row["type"] for row in store.list_identifiers(company["id"])] == ["LEI_CODE"]


def test_set_identifiers_enforces_one_per_type(make):
    company = make()
    with pytest.raises(ValueError):
        store.set_identifiers(company["id"], [{"type": "VAT_ID", "value": "DE123456789"},
                                             {"type": "VAT_ID", "value": "DE987654321"}])


def test_set_identifiers_enforces_the_enums(make):
    company = make()
    with pytest.raises(ValueError):
        store.set_identifiers(company["id"], [{"type": "VIES", "value": "DE123456789"}])
    with pytest.raises(ValueError):
        store.set_identifiers(company["id"], [{"type": "VAT_ID", "value": "DE123456789",
                                              "source": "ATTESTATION"}])


def test_set_identifiers_needs_a_known_company():
    with pytest.raises(ValueError):
        store.set_identifiers("unknown", [{"type": "VAT_ID", "value": "DE123456789"}])


# --------------------------------------------------------------------------------- roles (6.5)
def test_roles_report_status_and_none(make):
    company = make()
    assert store.role_status(company["id"], "APP_PROVIDER") == "NONE"
    store.add_role(company["id"], "ACTIVE_PARTICIPANT", status="ACTIVE")
    store.add_role(company["id"], "APP_PROVIDER", status="REQUESTED", source_kind="APPLICATION",
                   source_ref="a0000001-0000-4000-8000-000000000001")
    assert store.list_roles(company["id"]) == {"ACTIVE_PARTICIPANT": "ACTIVE",
                                               "APP_PROVIDER": "REQUESTED"}
    store.remove_role(company["id"], "APP_PROVIDER")
    assert store.role_status(company["id"], "APP_PROVIDER") == "INACTIVE"
    assert store.get_role(company["id"], "APP_PROVIDER")["deactivated_at"]
    assert store.remove_role(company["id"], "SERVICE_PROVIDER") is None


def test_add_role_enforces_the_enums(make):
    company = make()
    with pytest.raises(ValueError):
        store.add_role(company["id"], "ACTIVE_PARTICIPANT", status="ADDED")
    with pytest.raises(ValueError):
        store.add_role(company["id"], "ACTIVE_PARTICIPANT", source_kind="FLOW")


# -------------------------------------------------------------------------------- consents (5)
def test_consents_are_keyed_by_company_and_key(make):
    company = make()
    store.set_consent(company["id"], "terms-active-participant", version="1.0",
                      source_kind="COMPANY", consented_by="sub")
    store.set_consent(company["id"], "terms-active-participant", version="1.0", status="INACTIVE")
    store.set_consent(company["id"], "security-regulations", version="1.0")
    consent = store.get_consent(company["id"], "terms-active-participant")
    assert consent["status"] == "INACTIVE" and consent["agreement_version"] == "1.0"
    assert len(store.list_consents(company["id"])) == 2
