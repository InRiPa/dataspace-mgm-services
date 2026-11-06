#################################################################################
#  Copyright (c) 2026 Technovative Solutions
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
#  Assisted-By: Claude Code (claude-opus-5-5)
#################################################################################
"""C3-M2 CSP Connection against the built-in stand-in (README 11.3): acceptance cases of README 13
called in-process through `interface.py`, as Process Orchestration calls them."""
import json
import uuid
from dataclasses import asdict

import pytest

from modules.c3_m2 import interface, store
from portal_common import events
from portal_common.problems import Problem
from portal_common.standin import derive_bpn

# test data: README 14 and FRAMEWORK 7a
OSP_A, OSP_B = "22222222-2222-4222-8222-222222222222", "99a5685c-7397-402c-88de-b1b3a939ecc9"
OSP_COMPANY, OSP_COMPANY_BPN = "11111111-1111-4111-8111-111111111111", "BPNL00000000OSPA"
EBWOID, EUID = "EBWOID-DE-0000000001", "DEXX001T.HRB100001"
OTHER_EBWOID, OTHER_BPN = "EBWOID-DE-0000000002", "BPNL00000000002B"
CONNECTOR, ENDPOINT = "7c1e5a2b-4d3f-4e6a-9b8c-0d1e2f3a4b5c", "https://edc.beispiel-maschinenbau.example/dsp"
CSP_STUB = [{"bpn": OTHER_BPN, "legalName": "Andere Beispiel AG", "ebwoid": OTHER_EBWOID, "country": "DE",
             "homeOspId": OSP_B, "homeOspName": "OSP B", "memberActive": True}]
COMPANY = "c0000001-0000-4000-8000-000000000001"    # Beispiel Maschinenbau GmbH (FRAMEWORK 7a)
LOGISTIK = "c0000002-0000-4000-8000-000000000002"   # Beispiel Logistik GmbH, without Business Wallet (7a)
MASCHINENBAU_BPN = "BPNLIUK2REMLK3F4"               # its BPN from the CSP stand-in (7a, README 11.3)


@pytest.fixture(autouse=True)
def builtin_csp(tmp_path, monkeypatch):
    stub = tmp_path / "csp-stub.json"
    stub.write_text(json.dumps(CSP_STUB))
    monkeypatch.setenv("CSP_URL", "")
    monkeypatch.setenv("CSP_STUB_FILE", str(stub))
    interface.reset()
    yield
    interface.reset()


def step(**fields) -> dict:
    return {"processId": str(uuid.uuid4()), "stepRunId": str(uuid.uuid4()), "companyId": COMPANY} | fields


def maschinenbau(**fields) -> dict:
    return step(legalName="Beispiel Maschinenbau GmbH", country="DE", ebwoid=EBWOID, euid=EUID,
                address={"streetAddress": "Musterstraße 1", "postalCode": "70569", "locality": "Stuttgart",
                         "country": "DE"}) | fields


def published(type_: str) -> list[dict]:
    return [e["data"] for e in events.RELAY.log if e["type"] == type_ and e["source"] == "urn:c3-m2"]


def csp_calls(operation: str) -> int:
    return sum(1 for a in store.audit if a.operation == operation)


def problem(fn, *args, **kwargs) -> Problem:
    with pytest.raises(Problem) as e:
        fn(*args, **kwargs)
    return e.value


def register() -> str:
    return interface.register_company(maschinenbau())["result"]["bpn"]


# ---------------------------------------------------------------- README 13
def test_1_register_company_is_repeatable():
    first = interface.register_company(maschinenbau())
    assert first["state"] == "DONE"
    bpn = first["result"]["bpn"]
    assert bpn == MASCHINENBAU_BPN == derive_bpn(EBWOID) and bpn.startswith("BPNL") and len(bpn) == 16
    again = interface.register_company(maschinenbau())
    assert again["result"]["bpn"] == bpn
    assert csp_calls("register-company") == 1
    assert published("CompanyRegisteredAtCsp") == [{"companyId": COMPANY, "bpn": bpn}]
    view = interface.get_csp_registration(companyId=COMPANY)
    assert view["status"] == "REGISTERED" and view["bpn"] == bpn and view["membership"] == "NONE"


def test_2_registered_at_other_osp_fails():
    p = problem(interface.register_company, maschinenbau(ebwoid=OTHER_EBWOID, euid=None,
                                                         legalName="Andere Beispiel AG"))
    assert (p.status, p.name, p.ext["retryable"]) == (409, "registered-at-other-osp", False)
    assert interface.get_csp_registration(companyId=COMPANY)["status"] == "FAILED"
    assert interface.get_csp_registration(companyId=COMPANY)["failureReason"] == "REGISTERED_AT_OTHER_OSP"
    assert published("CompanyRegistrationAtCspFailed") == [{"companyId": COMPANY, "reason": "REGISTERED_AT_OTHER_OSP"}]


def test_3_find_companies_home_is_this_osp():
    other = interface.find_companies(ebwoid=OTHER_EBWOID)
    assert [(m["bpn"], m["matchedBy"], m["homeOspId"], m["homeOspName"], m["homeIsThisOsp"]) for m in other] == \
        [(OTHER_BPN, "EBWOID", OSP_B, "OSP B", False)]
    bpn = register()
    own = interface.find_companies(ebwoid=EBWOID)
    assert [(m["bpn"], m["homeIsThisOsp"], m["homeOspId"]) for m in own] == [(bpn, True, OSP_A)]
    assert interface.find_companies(ebwoid="EBWOID-DE-UNKNOWN") == []


def test_find_companies_needs_a_criterion():
    assert problem(interface.find_companies).status == 400
    assert problem(interface.find_companies, legalName="Andere Beispiel AG").status == 400
    assert problem(interface.find_companies, identifier=["VAT_ID"]).name == "validation"
    by_name = interface.find_companies(legalName="andere  beispiel ag", country="DE")
    assert [(m["bpn"], m["matchedBy"]) for m in by_name] == [(OTHER_BPN, "NAME")]


def test_5_register_did():
    p = problem(interface.register_did, step(did="did:web:wallet.example.org:x"))
    assert (p.name, p.ext["retryable"]) == ("invalid-state", False)
    bpn = register()
    did = f"did:web:wallet.example.org:{bpn}"
    r = interface.register_did(step(did=did))
    assert r["result"] == {"bpn": bpn, "did": did}
    assert interface.get_csp_registration(companyId=COMPANY)["did"] == did
    interface.register_did(step(did=did))
    assert csp_calls("register-did") == 1
    assert published("CompanyDidRegistered") == [{"companyId": COMPANY, "bpn": bpn, "did": did}]


def test_6_update_company():
    p = problem(interface.update_company, step(legalName="Beispiel Maschinenbau AG"))
    assert p.name == "invalid-state"
    bpn = register()
    s = step(legalName="Beispiel Maschinenbau AG", euid=EUID)
    assert interface.update_company(s)["state"] == "DONE"
    interface.update_company(s)   # same stepRunId: no second call
    assert csp_calls("update-company") == 1
    assert published("CompanyUpdatedAtCsp") == [{"companyId": COMPANY, "bpn": bpn}]


def test_7_membership_register_and_deregister():
    bpn = register()
    interface.register_membership(step())
    interface.register_membership(step())
    assert interface.get_csp_registration(companyId=COMPANY)["membership"] == "REGISTERED"
    interface.deregister_membership(step())
    interface.deregister_membership(step())
    assert interface.get_csp_registration(companyId=COMPANY)["membership"] == "DEREGISTERED"
    assert csp_calls("register-membership") == 1 and csp_calls("deregister-membership") == 1
    assert published("MembershipRegistered") == [{"companyId": COMPANY, "bpn": bpn}]
    assert published("MembershipDeregistered") == [{"companyId": COMPANY, "bpn": bpn}]


def test_8_and_14_transferred_away_and_return():
    bpn = register()
    interface.register_membership(step())
    note = {"notificationId": "n-away", "type": "CompanyTransferredAway", "bpn": bpn}
    interface.receive_csp_notification(note)
    interface.receive_csp_notification(note)
    assert interface.get_csp_registration(companyId=COMPANY)["status"] == "TRANSFERRED_AWAY"
    assert published("CompanyTransferredAway") == [{"companyId": COMPANY, "bpn": bpn}]
    # 14: deregister-membership after the move: DONE, no call, no event, membership NONE
    calls = csp_calls("deregister-membership")
    assert interface.deregister_membership(step())["state"] == "DONE"
    assert csp_calls("deregister-membership") == calls and published("MembershipDeregistered") == []
    assert interface.get_csp_registration(companyId=COMPANY)["membership"] == "NONE"
    # return: transfer-company, then register-membership calls the CSP again
    r = interface.transfer_company(step(bpn=bpn, ebwoid=EBWOID))
    assert r["result"] == {"bpn": bpn}
    assert interface.get_csp_registration(companyId=COMPANY)["status"] == "REGISTERED"
    interface.register_membership(step())
    assert csp_calls("register-membership") == 2
    assert len(published("MembershipRegistered")) == 2


def test_11_identifier_without_business_wallet():
    reg = [{"type": "COMMERCIAL_REG_NUMBER", "value": "HRB 200002"}]
    r = interface.register_company(step(companyId=LOGISTIK, legalName="Beispiel Logistik GmbH", country="DE",
                                        identifiers=reg))
    assert r["result"]["bpn"] == derive_bpn("COMMERCIAL_REG_NUMBER:HRB 200002")
    p = problem(interface.register_company, step(legalName="Beispiel Logistik GmbH", country="DE",
                                                 companyId=LOGISTIK))
    assert (p.status, p.name, p.ext["retryable"]) == (400, "validation", False)
    found = interface.find_companies(identifier="COMMERCIAL_REG_NUMBER:HRB 200002")
    assert [(m["bpn"], m["matchedBy"]) for m in found] == [(r["result"]["bpn"], "IDENTIFIER")]


def test_12_connector_in_the_discovery():
    p = problem(interface.register_connector, step(connectorId=CONNECTOR, endpointUrl=ENDPOINT))
    assert p.name == "invalid-state"
    bpn = register()
    r = interface.register_connector(step(connectorId=CONNECTOR, endpointUrl=ENDPOINT))
    assert r["result"] == {"bpn": bpn, "connectorId": CONNECTOR}
    assert store.connectors[CONNECTOR].status == "REGISTERED"
    interface.register_connector(step(connectorId=CONNECTOR, endpointUrl=ENDPOINT))
    assert csp_calls("register-connector") == 1 and len(published("ConnectorRegisteredAtCsp")) == 1
    interface.register_connector(step(connectorId=CONNECTOR, endpointUrl=ENDPOINT + "/v2"))
    assert csp_calls("register-connector") == 2 and len(published("ConnectorRegisteredAtCsp")) == 2
    interface.deregister_connector(step(connectorId=CONNECTOR))
    assert store.connectors[CONNECTOR].status == "DEREGISTERED"
    interface.deregister_connector(step(connectorId=CONNECTOR))
    assert published("ConnectorDeregisteredAtCsp") == [{"companyId": COMPANY, "bpn": bpn, "connectorId": CONNECTOR}]
    assert csp_calls("deregister-connector") == 1


def test_register_connector_needs_https():
    register()
    p = problem(interface.register_connector, step(connectorId=CONNECTOR, endpointUrl="http://edc.example/dsp"))
    assert (p.status, p.name) == (400, "validation")


def test_deregister_unknown_connector_is_done_without_a_call():
    r = interface.deregister_connector(step(connectorId=CONNECTOR))
    assert r["state"] == "DONE" and r["result"]["connectorId"] == CONNECTOR
    assert csp_calls("deregister-connector") == 0 and published("ConnectorDeregisteredAtCsp") == []


def test_13_seed_data_of_the_osp_company():
    view = interface.get_csp_registration(companyId=OSP_COMPANY)
    assert (view["status"], view["bpn"], view["membership"]) == ("REGISTERED", OSP_COMPANY_BPN, "REGISTERED")
    assert store.audit == [] and events.RELAY.log == []
    store.seed()   # a second start changes nothing
    assert interface.get_csp_registration(companyId=OSP_COMPANY) == view
    r = interface.register_connector(step(companyId=OSP_COMPANY, connectorId=CONNECTOR, endpointUrl=ENDPOINT))
    assert r["result"] == {"bpn": OSP_COMPANY_BPN, "connectorId": CONNECTOR}
    assert csp_calls("register-connector") == 1
    assert published("ConnectorRegisteredAtCsp") == [{"companyId": OSP_COMPANY, "bpn": OSP_COMPANY_BPN,
                                                      "connectorId": CONNECTOR}]


def test_get_registration_unknown_company_is_404():
    p = problem(interface.get_csp_registration, companyId=str(uuid.uuid4()))
    assert (p.status, p.name) == (404, "not-found")


def test_transfer_needs_a_bpn():
    p = problem(interface.transfer_company, step())
    assert (p.status, p.name) == (400, "validation")


def test_notification_for_unknown_company_is_404():
    p = problem(interface.receive_csp_notification,
                {"notificationId": "n-x", "type": "CompanyTransferredAway", "bpn": "BPNL0000000UNKNW"})
    assert (p.status, p.name) == (404, "unknown-company")
    assert "n-x" not in store.notifications


def test_no_secrets_in_audit_or_events():
    register()
    interface.register_membership(step())
    text = json.dumps([asdict(a) for a in store.audit]) + json.dumps(events.RELAY.log)
    assert "access_token" not in text and "Bearer" not in text and "client_assertion" not in text


# ---------------------------------------------------------------- review findings (review-module, 2026-11-06)
def move_away(bpn: str) -> None:
    interface.receive_csp_notification({"notificationId": str(uuid.uuid4()), "type": "CompanyTransferredAway",
                                        "bpn": bpn})


def test_return_after_a_move_registers_did_membership_and_connector_again():
    """OPEN-QUESTIONS 14: while the company was away, the new home OSP may have changed them at the CSP."""
    bpn = register()
    did = f"did:web:wallet.example.org:{bpn}"
    interface.register_did(step(did=did))
    interface.register_membership(step())
    interface.register_connector(step(connectorId=CONNECTOR, endpointUrl=ENDPOINT))
    move_away(bpn)
    view = interface.get_csp_registration(companyId=COMPANY)
    assert "did" not in view and view["membership"] == "NONE"
    assert store.connectors[CONNECTOR].status == "DEREGISTERED"
    # while away: removing the connector is DONE without a call (the new home OSP owns it)
    interface.deregister_connector(step(connectorId=CONNECTOR))
    assert csp_calls("deregister-connector") == 0
    interface.transfer_company(step(bpn=bpn, ebwoid=EBWOID))
    # same values as before the move: each step calls the CSP again and publishes its event again
    interface.register_did(step(did=did))
    interface.register_membership(step())
    interface.register_connector(step(connectorId=CONNECTOR, endpointUrl=ENDPOINT))
    assert (csp_calls("register-did"), csp_calls("register-membership"), csp_calls("register-connector")) == (2, 2, 2)
    assert len(published("CompanyDidRegistered")) == 2
    assert len(published("MembershipRegistered")) == 2
    assert len(published("ConnectorRegisteredAtCsp")) == 2


def test_late_operation_completed_does_not_revive_a_moved_company():
    """README 6.1: TRANSFERRED_AWAY stays until transfer-company; the BPN fallback is for PENDING only."""
    bpn = register()
    move_away(bpn)
    late = {"notificationId": "n-late", "type": "OperationCompleted", "operationId": "unknown-operation",
            "outcome": "SUCCEEDED", "bpn": bpn}
    p = problem(interface.receive_csp_notification, late)
    assert (p.status, p.name) == (404, "unknown-company")
    assert interface.get_csp_registration(companyId=COMPANY)["status"] == "TRANSFERRED_AWAY"
    assert len(published("CompanyRegisteredAtCsp")) == 1
    assert "n-late" not in store.notifications


def test_operation_completed_falls_back_to_the_bpn_of_a_pending_registration():
    """README 7.2 step 2: a PENDING registration is found by its BPN when the operation id is unknown."""
    row = store.registration_row(COMPANY)
    row.status, row.bpn, row.pending_operation_id = "PENDING", MASCHINENBAU_BPN, "operation-1"
    interface.receive_csp_notification({"notificationId": "n-1", "type": "OperationCompleted",
                                        "operationId": "operation-2", "outcome": "SUCCEEDED",
                                        "bpn": MASCHINENBAU_BPN})
    assert interface.get_csp_registration(companyId=COMPANY)["status"] == "REGISTERED"
    assert published("CompanyRegisteredAtCsp") == [{"companyId": COMPANY, "bpn": MASCHINENBAU_BPN}]


def test_transfer_company_is_repeatable():
    """FRAMEWORK 4.4: the same transfer-company again returns the BPN without a call and without an event."""
    bpn = register()
    move_away(bpn)
    s = step(bpn=bpn, ebwoid=EBWOID)
    first = interface.transfer_company(s)
    again = interface.transfer_company(s)
    assert first == again and again["result"] == {"bpn": bpn} and again["state"] == "DONE"
    assert csp_calls("transfer-company") == 1
    assert len(published("CompanyRegisteredAtCsp")) == 2   # the registration and the return, nothing more


def test_stub_file_entries_must_be_company_objects(tmp_path, monkeypatch):
    bad = tmp_path / "bad-stub.json"
    bad.write_text(json.dumps(CSP_STUB + ["not a company"]))
    monkeypatch.setenv("CSP_STUB_FILE", str(bad))
    interface.reset()
    with pytest.raises(ValueError, match="CSP_STUB_FILE"):
        interface.find_companies(ebwoid=OTHER_EBWOID)


def test_find_companies_rejects_a_malformed_csp_answer(monkeypatch):
    from modules.c3_m2 import csp_client
    monkeypatch.setattr(csp_client, "call", lambda *a, **k: (200, [CSP_STUB[0], "not a match"]))
    p = problem(interface.find_companies, ebwoid=OTHER_EBWOID)
    assert (p.status, p.name, p.ext["retryable"]) == (502, "upstream-error", True)
