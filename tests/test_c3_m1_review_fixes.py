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
from test_c3_m1_steps import A1, A2, A3, U3, _c1_m2, seed, step  # noqa: F401  (_c1_m2: fixture)

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
    with pytest.raises(Problem) as error:
        interface.create_change_request(U1, {"comment": "x", "name": "Neu AG"}, [PDF], P1_SUB)
    assert error.value.status == 409 and error.value.name == "attestation-required"


# ------------------------------------------------------ a declared core identifier is core data (high)
def test_a_changed_euid_counts_as_core_data():
    interface.reset()
    seed(A1, U1, verification="DOCUMENTS", attestation=None, companyData={
        "legalName": "Beispiel Maschinenbau GmbH",
        "address": {"streetName": "Musterstraße", "streetNumber": "1", "postalCode": "70569",
                    "city": "Stuttgart", "countryCode": "DE"},
        "identifiers": [{"type": "EUID", "value": "DEXX001T.HRB100001", "source": "APPLICANT"},
                        {"type": "VAT_ID", "value": "DE123456789", "source": "APPLICANT"}]})
    step("create_company", companyId=U1, applicationId=A1)
    step("assign_identifier", companyId=U1, bpn="BPNLIUK2REMLK3F4")
    step("activate_company", companyId=U1, applicationId=A1)
    request = interface.create_change_request(U1, {"comment": "x", "identifiers": [
        {"type": "EUID", "value": "DEXX001T.HRB200002"},
        {"type": "VAT_ID", "value": "DE123456789"}]}, [PDF], P1_SUB)
    events.RELAY.log.clear()
    interface.approve_change_request(request["id"], {}, S1_SUB)
    changed = [event for event in events.RELAY.log if event["type"] == "CompanyDataChanged"]
    assert changed and changed[0]["data"]["coreDataChanged"] is True


# ------------------------------------------------------------------- the correction path (7.12)
def test_the_correction_reports_wallet_conflicts_as_validation(client, active):
    answer = call(client, "PATCH", f"/api/c3-m1/osp/companies/{U1}", S2,
                  json={"identifiers": [{"type": "EUID", "value": "X"}], "reason": "r"})
    assert answer.status_code == 400 and answer.json()["type"].endswith("validation")


def test_the_correction_keeps_old_values_in_the_audit(client, active):
    call(client, "PATCH", f"/api/c3-m1/osp/companies/{U1}", S2,
         json={"address": {"street": "Neue Straße"}, "reason": "Hinweis"})
    entry = [row for row in store.list_audit(U1) if row["operation"] == "correctCompany"][-1]
    assert entry["details"]["old"]["street"] == "Musterstraße"
    assert entry["details"]["new"]["street"] == "Neue Straße"


def test_the_attestation_update_keeps_old_values_in_the_audit(active):
    interface.update_company_from_attestation(U1, {"attestation": sign(claims())}, P1_SUB)
    entry = [row for row in store.list_audit(U1)
             if row["operation"] == "updateCompanyFromAttestation"][-1]
    assert entry["details"]["old"]["name"] == "Beispiel Maschinenbau GmbH"


# --------------------------------------------------------------- schema shapes (second review)
def test_a_company_answer_uses_id_and_created_at(client, active):
    answer = call(client, "GET", f"/api/c3-m1/companies/{U1}", P1)
    body = answer.json()
    assert body["id"] == U1 and body["createdAt"] and "companyId" not in body
    detail = call(client, "GET", f"/api/c3-m1/osp/companies/{U1}", S1).json()
    assert detail["id"] == U1 and detail["createdAt"]


def test_the_role_terms_carry_name_names_and_document_url(client, active):
    answer = call(client, "GET", f"/api/c3-m1/companies/{U1}/company-roles?lang=en", P1)
    term = answer.json()[0]["agreements"][0]
    assert set(term) >= {"name", "names", "documentUrl", "agreementKey", "version"}


def test_a_bpn_of_a_rejected_company_is_free_again():
    U4 = "c0000004-0000-4000-8000-000000000004"
    interface.reset()
    seed(A1, U1)
    step("create_company", companyId=U1, applicationId=A1)
    step("assign_identifier", companyId=U1, bpn="BPNLIUK2REMLK3F4")
    step("reject_company", companyId=U1)
    seed("a0000008-0000-4000-8000-000000000008", U4, kind="TRANSFER", companyData={
        "legalName": "Andere Beispiel AG",
        "address": {"streetName": "Beispielweg", "streetNumber": "2", "postalCode": "80331",
                    "city": "München", "countryCode": "DE"},
        "identifiers": [{"type": "EBWOID", "value": "EBWOID-DE-0000000002", "source": "ATTESTATION"}]})
    step("create_company", companyId=U4, applicationId="a0000008-0000-4000-8000-000000000008")
    assert step("assign_identifier", companyId=U4,
                bpn="BPNLIUK2REMLK3F4")["result"]["bpn"] == "BPNLIUK2REMLK3F4"


def test_an_attestation_without_a_change_still_stamps_the_verification(active):
    interface.update_company_from_attestation(U1, {"attestation": sign(claims())}, P1_SUB)
    before = store.get_company(U1)["core_data_verified_at"]
    second = interface.update_company_from_attestation(
        U1, {"attestation": sign(claims(jti="jti-spaet", verified_at=int(
            (dt.datetime.now(dt.UTC) + dt.timedelta(minutes=1)).timestamp())))}, P1_SUB)
    assert second["changedFields"] == []
    row = store.get_company(U1)
    assert row["verification_ref"] == "jti-spaet" and row["core_data_verified_at"] != before


def test_the_approval_event_carries_the_resulting_source(active):
    request = interface.create_change_request(U1, {"comment": "x", "identifiers": [
        {"type": "VAT_ID", "value": "DE123456789"}, {"type": "LEI_CODE", "value": "529900T8BM49AURSDO55"}]},
        [PDF], P1_SUB)
    events.RELAY.log.clear()
    interface.approve_change_request(request["id"], {}, S1_SUB)
    changed = [event for event in events.RELAY.log if event["type"] == "CompanyDataChanged"]
    assert changed and changed[0]["data"]["coreDataSource"] == "EBW"


def test_the_reactivation_keeps_the_house_number_of_the_application(active):
    seed("a0000005-0000-4000-8000-000000000009", U1, kind="REACTIVATION", status="SUBMITTED",
         companyData={"legalName": "Beispiel Maschinenbau GmbH",
                      "address": {"streetName": "Musterstraße", "streetNumber": "7",
                                  "postalCode": "70569", "city": "Stuttgart", "countryCode": "DE"},
                      "identifiers": [{"type": "EBWOID", "value": "EBWOID-DE-0000000001",
                                       "source": "ATTESTATION"}]})
    step("deactivate_company", companyId=U1, reason="MANUAL")
    step("reactivate_company", companyId=U1, applicationId="a0000005-0000-4000-8000-000000000009")
    row = store.get_company(U1)
    assert (row["street"], row["house_number"]) == ("Musterstraße", "7")


def test_the_start_survives_a_database_without_a_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://x/y")
    monkeypatch.setattr(interface.store, "_cache", None)
    real_import = interface.store.importlib.import_module

    def fake_import(name, package=None):
        if name == ".store_postgres":
            raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
        return real_import(name, package)

    monkeypatch.setattr(interface.store.importlib, "import_module", fake_import)
    interface.reset()                                    # must not raise
    with pytest.raises(Problem) as error:
        interface.store.get_company("11111111-1111-4111-8111-111111111111")
    assert error.value.status == 501


def test_the_readme_data_files_resolve_without_configuration(monkeypatch):
    from pathlib import Path
    assert config.stub_applications_file() is not None        # README 4: apps come from the stub file
    monkeypatch.delenv("ATTESTATION_JWKS_FILE")
    assert config.attestation_jwks_file() is None             # README 4: JWKS is a test setting only
    monkeypatch.setenv("ATTESTATION_JWKS_FILE", "stub-ebw-jwks.json")
    assert config.attestation_jwks_file() is not None
    assert config.attestation_jwks_file().name == "stub-ebw-jwks.json"
    assert config.attestation_jwks_file().parent == Path(config.__file__).parent


def test_an_address_part_needs_street_and_city(active):
    with pytest.raises(Problem) as error:
        interface.create_change_request(U1, {"comment": "x", "address": {"street": "Nur Straße"}},
                                        [PDF], P1_SUB)
    assert error.value.status == 400 and error.value.name == "validation"


def test_the_activation_calls_neither_the_csp_nor_c3_m2(active, monkeypatch):
    monkeypatch.setenv("C3_M2_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("C3_M1_URL", "http://127.0.0.1:9")
    store.update_company(U1, status="REQUESTED", activated_at=None)
    store.add_role(U1, "ACTIVE_PARTICIPANT", status="REQUESTED", source_kind="APPLICATION")
    answer = step("activate_company", companyId=U1, applicationId=A1)
    assert answer["result"]["status"] == "ACTIVE"


def test_the_document_goes_out_over_http_with_its_content_type(client, active):
    request = interface.create_change_request(U1, {"comment": "x", "identifiers": [
        {"type": "VAT_ID", "value": "DE555444333"}]}, [PDF], P1_SUB)
    answer = call(client, "GET", f"/api/c3-m1/osp/change-requests/{request['id']}/documents/"
                                f"{request['documents'][0]['id']}", S1)
    assert answer.status_code == 200
    assert answer.headers["content-type"] == "application/pdf"
    assert "attachment" in answer.headers["content-disposition"]
    assert answer.content.startswith(b"%PDF")


# ------------------------------------------------------------------------- concurrency (6.9)
def test_two_threads_create_the_same_company_once():
    from concurrent.futures import ThreadPoolExecutor
    interface.reset()
    seed(A1, U1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: step("create_company", companyId=U1,
                                              applicationId=A1), range(2)))
    assert all(reply["state"] == "DONE" for reply in results)
    assert len([event for event in events.RELAY.log if event["type"] == "CompanyCreated"]) == 1
    assert len(store.find_companies(size=100)[0]) == 2          # seed + U1


def test_two_threads_assign_the_same_bpn_once():
    from concurrent.futures import ThreadPoolExecutor
    interface.reset()
    seed(A1, U1)
    step("create_company", companyId=U1, applicationId=A1)
    events.RELAY.log.clear()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: step("assign_identifier", companyId=U1,
                                              bpn="BPNLIUK2REMLK3F4"), range(2)))
    assert all(reply["state"] == "DONE" for reply in results)
    assert len([event for event in events.RELAY.log
                if event["type"] == "CompanyIdentifierAssigned"]) == 1


# ------------------------------------------------------------------- shortName alias and lang
def test_the_snake_case_alias_writes_the_short_name(client, active):
    answer = call(client, "PATCH", f"/api/c3-m1/companies/{U1}", P1, json={"short_name": "Kurz"})
    assert answer.status_code == 200 and answer.json()["shortName"] == "Kurz"


def test_the_role_add_answers_in_the_requested_language(client, active):
    answer = call(client, "POST", f"/api/c3-m1/companies/{U1}/company-roles?lang=de", P1,
                  json={"companyRole": "APP_PROVIDER",
                        "consents": [{"agreementKey": "terms-app-provider", "version": "1.0"}]})
    assert answer.status_code == 200
    assert [entry["description"] for entry in answer.json()
            if entry["companyRole"] == "APP_PROVIDER"] == ["Anbieter von Apps"]


def test_a_malformed_json_part_is_a_validation_error(client, active):
    answer = call(client, "POST", f"/api/c3-m1/companies/{U1}/change-requests", P1,
                  data={"data": "{nope"}, files={"documents": PDF})
    assert answer.status_code == 400 and answer.json()["type"].endswith("validation")


# ------------------------------------------------------------------------- attestation details
def test_an_undecodable_payload_is_a_format_error(active):
    header = sign(claims()).split(".")[0]
    with pytest.raises(Problem) as error:
        interface.update_company_from_attestation(U1, {"attestation": f"{header}.%%%.sig"})
    assert error.value.status == 400 and error.value.ext["reason"] == "format"


def test_client_id_is_optional_without_a_configured_list(active, monkeypatch):
    monkeypatch.delenv("ATTESTATION_CLIENT_IDS")
    payload = claims()
    payload.pop("client_id")
    answer = interface.update_company_from_attestation(U1, {"attestation": sign(payload)}, P1_SUB)
    assert answer["changedFields"]


def test_an_outdated_attestation_is_recognised_across_timestamp_formats(active):
    interface.update_company_from_attestation(U1, {"attestation": sign(claims(jti="j-new"))}, P1_SUB)
    stored = store.get_company(U1)["core_data_verified_at"]
    store.update_company(U1, core_data_verified_at=stored.replace("+00:00", "Z"))
    with pytest.raises(Problem) as error:
        interface.update_company_from_attestation(
            U1, {"attestation": sign(claims(jti="j-old", verified_at=int(
                (dt.datetime.now(dt.UTC) - dt.timedelta(hours=2)).timestamp())))}, P1_SUB)
    assert error.value.status == 409 and error.value.name == "attestation-outdated"


# ------------------------------------------------------------------------ lifecycle answers
def test_the_deactivation_DONE_keeps_the_stored_reason(active):
    step("deactivate_company", companyId=U1, reason="TRANSFERRED")
    answer = step("deactivate_company", companyId=U1, reason="MANUAL")
    assert answer["result"]["deactivationReason"] == "TRANSFERRED"


def test_the_activation_DONE_lists_active_roles_only(active):
    interface.add_company_role(U1, {"companyRole": "APP_PROVIDER",
                                    "consents": [{"agreementKey": "terms-app-provider",
                                                  "version": "1.0"}]}, P1_SUB)
    store.add_role(U1, "SERVICE_PROVIDER", status="REQUESTED", source_kind="APPLICATION")
    answer = step("activate_company", companyId=U1, applicationId="a0000001-0000-4000-8000-000000000001")
    assert answer["result"]["companyRoles"] == ["ACTIVE_PARTICIPANT", "APP_PROVIDER"]


def test_the_reactivation_accepts_a_submitted_application(active):
    """flows.yaml `reactivation` runs this step right after ApplicationSubmitted (review 1)."""
    step("deactivate_company", companyId=U1, reason="MANUAL")
    seed("a0000005-0000-4000-8000-000000000005", U1, kind="REACTIVATION", status="SUBMITTED")
    reply = step("reactivate_company", companyId=U1,
                 applicationId="a0000005-0000-4000-8000-000000000005")
    assert reply["state"] == "DONE" and reply["result"]["status"] == "ACTIVE"


def test_the_reactivation_refuses_a_withdrawn_application(active):
    step("deactivate_company", companyId=U1, reason="MANUAL")
    seed("a0000005-0000-4000-8000-000000000006", U1, kind="REACTIVATION", status="WITHDRAWN")
    with pytest.raises(Problem) as error:
        step("reactivate_company", companyId=U1,
             applicationId="a0000005-0000-4000-8000-000000000006")
    assert error.value.status == 409 and error.value.name == "invalid-state"


def test_the_rejected_bpn_abort_of_the_seed_file(tmp_path, monkeypatch):
    """13.25: a seed file with another companyId aborts the start."""
    seed_file = tmp_path / "osp-company.json"
    seed_file.write_text(json.dumps({"companyId": "c0000009-0000-4000-8000-000000000009",
                                     "name": "X", "bpn": "BPNL00000000OSPA",
                                     "address": {"street": "s", "city": "c", "countryCode": "DE"},
                                     "companyRoles": []}), encoding="utf-8")
    monkeypatch.setenv("OSP_COMPANY_FILE", str(seed_file))
    from portal_common import settings
    monkeypatch.setitem(settings.load(), "ospCompanyFile", str(seed_file))
    with pytest.raises(ValueError):
        config.seed_company()

A8 = "a0000008-0000-4000-8000-000000000008"
U4 = "c0000004-0000-4000-8000-000000000004"


def ebw_company() -> None:
    """An active company with source EBW (application 8 is verified over EBW)."""
    seed(A8, U4)
    step("create_company", companyId=U4, applicationId=A8)
    step("assign_identifier", companyId=U4, bpn="BPNLIUK2REMLK3F5")
    step("activate_company", companyId=U4, applicationId=A8)


# --------------------------------------------------------- review 2: the readings of the second review
def test_a_validation_error_answers_field_and_message():
    """README 12 + openapi `Error`: `errors[]` carries `field` and `message` (review 15)."""
    interface.reset()
    seed(A1, U1)
    step("create_company", companyId=U1, applicationId=A1)
    with pytest.raises(Problem) as error:
        interface.correct_company(U1, {"reason": "x", "name": ""})
    assert error.value.status == 400
    assert error.value.ext["errors"][0]["field"] == "name"
    assert "message" in error.value.ext["errors"][0]


def test_an_ebw_company_may_take_a_declared_identifier_without_attestation(active):
    """6.6: an attestation is needed for name and address, a DECLARED identifier is not (review 4)."""
    ebw_company()
    assert store.get_company(U4)["core_data_source"] == "EBW"
    interface.correct_company(U4, {"reason": "Nachtrag", "identifiers": [
        {"type": "VAT_ID", "value": "DE123456789", "source": "DECLARED"}]}, P1_SUB)
    assert store.get_company(U4)["core_data_source"] == "EBW"      # no name or address changed


def test_correcting_with_the_stored_values_keeps_an_ebw_source(active):
    """7.17: presence is not a change; equal values must not need an attestation or flip the source."""
    ebw_company()
    stored = store.get_company(U4)
    interface.correct_company(U4, {"reason": "Abgleich", "name": stored["name"]}, P1_SUB)
    assert store.get_company(U4)["core_data_source"] == "EBW"


def test_the_review_filter_needs_a_list(client):
    answer = call(client, "POST", "/api/c3-m1/internal/companies/identifier-matches", "svc",
                  json={"statuses": ["ACTIVE"]})
    assert answer.status_code == 400
    assert answer.json()["errors"][0]["field"] == "identifiers"


def test_a_change_request_body_must_be_an_object(client, active):
    response = call(client, "POST", "/api/c3-m1/companies/u1/change-requests".replace("u1", U1), P1,
                    data={"data": "[1, 2]"}, files={"documents": PDF})
    assert response.status_code == 400
    assert response.json()["errors"][0]["field"] == "data"


def test_a_role_the_company_may_not_assign_is_a_validation_error(active):
    seed("a0000009-0000-4000-8000-000000000009", "c0000009-0000-4000-8000-000000000009",
         companyRoles=["OSP_ADMIN"])
    with pytest.raises(Problem) as error:
        step("create_company", companyId="c0000009-0000-4000-8000-000000000009",
             applicationId="a0000009-0000-4000-8000-000000000009")
    assert error.value.status == 400
    assert any(entry["field"] == "companyRole" for entry in error.value.ext["errors"])


def test_a_short_name_of_the_company_survives_the_reactivation(active):
    interface.update_company(U1, {"shortName": "Kurz"}, P1_SUB)
    step("deactivate_company", companyId=U1, reason="MANUAL")
    seed("a0000005-0000-4000-8000-000000000008", U1, kind="REACTIVATION",
         companyData={"legalName": "Anderer Name AG", "address": {
             "streetName": "Neue Straße", "streetNumber": "9", "postalCode": "01067",
             "city": "Dresden", "countryCode": "DE"}}, verification="DOCUMENTS", attestation=None)
    step("reactivate_company", companyId=U1,
         applicationId="a0000005-0000-4000-8000-000000000008")
    assert store.get_company(U1)["short_name"] == "Kurz"


def test_a_change_of_the_source_alone_publishes_data_changed(active):
    """7.3 point 5: a changed source counts, not only changed fields."""
    ebw_company()
    store.update_company(U4, core_data_source="MANUAL", name="Beispiel Maschinenbau GmbH")
    events.RELAY.log.clear()
    interface.update_company_from_attestation(U4, {"attestation": sign(claims())}, P1_SUB)
    assert [event["type"] for event in events.RELAY.log] == ["CompanyDataChanged"]


def test_the_download_file_name_is_escaped(client, active):
    seed(A3, U3, companyData={
        "legalName": "Beispiel Maschinenbau GmbH",
        "address": {"streetName": "Musterstraße", "streetNumber": "1", "postalCode": "70569",
                    "city": "Stuttgart", "countryCode": "DE"},
        "identifiers": [{"type": "VAT_ID", "value": "DE123456789", "source": "APPLICANT"}]},
        verification="DOCUMENTS", attestation=None)
    step("create_company", companyId=U3, applicationId=A3)
    step("assign_identifier", companyId=U3, bpn="BPNLIUK2REMLK3F6")
    step("activate_company", companyId=U3, applicationId=A3)
    request = interface.create_change_request(U3, {"comment": "x", "identifiers": [
        {"type": "EUID", "value": "DEXX001T.HRB100001"}]},
        [("Größe Angabe.pdf", b"%PDF-1.7", "application/pdf")], P1_SUB)
    response = call(client, "GET", f"/api/c3-m1/osp/change-requests/{request['id']}"
                                   f"/documents/{request['documents'][0]['id']}", S1)
    assert response.status_code == 200
    assert "%C3%9F" in response.headers["content-disposition"]
