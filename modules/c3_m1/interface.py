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
"""Public interface of C3-M1 Company Profile: the steps of Process Orchestration (README 8), the
queries of other modules (9) and the read paths.

Names and signatures follow the call convention of AGENTS.md: a step is
`def create_company(input: dict) -> dict` returning `{stepRunId, state, result}`, a query takes its
parameters by their openapi names. No token checks here.

Steps are idempotent (FRAMEWORK 4.4): the business key is looked up first, only what is missing is
created, a repetition returns the stored result and publishes nothing. Every changing operation
writes the audit log of README 5 and FRAMEWORK 4.3 before it publishes.
"""
from __future__ import annotations

import datetime as dt
import json

from portal_common import events, neighbours, standin
from portal_common.problems import Problem
from tools import testdata

from . import attestation, config, store, validation

MODULE = "c3-m1"


def _timestamp(value: str | None) -> dt.datetime | None:
    """Parse a stored ISO timestamp (`Z` or offset) to an instant; `None` when unreadable."""
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def _audit(company_id: str | None, operation: str, input: dict, details: dict | None = None) -> None:
    """Steps carry `processId` and `stepRunId` instead of a `sub` (README 5, 4.3)."""
    store.audit(company_id, None, operation, None,
                (details or {}) | {"processId": input.get("processId"),
                                   "stepRunId": input.get("stepRunId")})


# ------------------------------------------------------------------------ start and seed (README 4)
def reset() -> None:
    """Empty state, then the seed data of the OSP company (README 4). Seed data has no events."""
    try:
        store.reset()
        target = store
    except Problem as error:
        if error.status != 501:
            raise
        # the start survives an unusable database; the seed then lands in memory, calls answer 501
        target = store.backend_memory()
        target.reset()
    attestation.reset()
    seed = config.seed_company()
    if not seed or target.get_company(config.osp_company_id()) is not None:
        return
    address = seed.get("address") or {}
    target.create_company({
        "id": seed["companyId"], "name": seed["name"], "bpn": seed.get("bpn"),
        "street": address.get("street"), "house_number": address.get("houseNumber"),
        "postal_code": address.get("postalCode"), "city": address.get("city"),
        "region": address.get("region"), "country_code": address.get("countryCode"),
        "status": "ACTIVE", "core_data_source": "MANUAL",
    })
    target.set_identifiers(seed["companyId"], seed.get("identifiers") or [])
    for role in seed.get("companyRoles") or []:
        target.add_role(seed["companyId"], role, status="ACTIVE", source_kind="SEED",
                        source_ref="ospCompanyFile")


# ---------------------------------------------------------------------------------- mapping (5)
def get_company(cid: str | None) -> dict:
    row = store.get_company(cid)
    if row is None:
        raise Problem(MODULE, 404, "not-found", retryable=False)
    return row


def _address(row: dict) -> dict:
    return {key: row.get(field) for key, field in
            (("street", "street"), ("houseNumber", "house_number"),
             ("addressAddition", "address_addition"), ("postalCode", "postal_code"),
             ("city", "city"), ("region", "region"), ("countryCode", "country_code"))}


def _identifiers(row: dict) -> list[dict]:
    return [{"type": entry["type"], "value": entry["value"], "source": entry["source"]}
            for entry in store.list_identifiers(row["id"])]


def _active_roles(company: str | None) -> list[str]:
    return sorted(role for role, status in store.list_roles(company).items() if status == "ACTIVE")


def _roles(row: dict) -> list[dict]:
    return [{"companyRole": role, "status": status}
            for role, status in store.list_roles(row["id"]).items()]


def company_view(cid: str | None, *, detail: bool = False) -> dict:
    """`Company` (7.1) and `CompanyDetail` (7.11) in camelCase, with the dataspace name for people."""
    row = get_company(cid)
    view = {"id": row["id"], "name": row["name"], "shortName": row["short_name"],
            "address": _address(row), "identifiers": _identifiers(row),
            "coreDataSource": row["core_data_source"],
            "coreDataVerifiedAt": row["core_data_verified_at"], "bpn": row["bpn"],
            "status": row["status"], "companyRoles": _roles(row),
            "createdAt": row["created_at"], "dataspaceName": config.dataspace_name()}
    if detail:
        view |= {"applicationId": row["application_id"], "verificationRef": row["verification_ref"],
                 "bpnAssignedAt": row["bpn_assigned_at"],
                 "deactivationReason": row["deactivation_reason"],
                 "changedAt": row["changed_at"], "activatedAt": row["activated_at"],
                 "rejectedAt": row["rejected_at"], "deactivatedAt": row["deactivated_at"],
                 "reactivatedAt": row["reactivated_at"],
                 "openChangeRequestId": (store.open_change_request(row["id"]) or {}).get("id")}
    return view


def company_internal(cid: str | None) -> dict:
    """`CompanyInternal` (9.1): address, identifiers, source and active roles for other modules."""
    row = get_company(cid)
    return {"id": row["id"], "name": row["name"], "shortName": row["short_name"],
            "address": {key: row.get(field) for key, field in
                        (("street", "street"), ("houseNumber", "house_number"),
                         ("postalCode", "postal_code"), ("city", "city"),
                         ("region", "region"), ("countryCode", "country_code"))},
            "identifiers": _identifiers(row), "coreDataSource": row["core_data_source"],
            "status": row["status"], "bpn": row["bpn"],
            "companyRoles": [role for role, status in store.list_roles(row["id"]).items()
                             if status == "ACTIVE"],
            "deactivationReason": row["deactivation_reason"], "createdAt": row["created_at"],
            "activatedAt": row["activated_at"], "deactivatedAt": row["deactivated_at"]}


def role_view(cid: str | None) -> dict:
    """`Company` of the paths for people (7.1, 7.7): roles with status, so a role can read REQUESTED."""
    row = get_company(cid)
    view = company_view(cid)
    view["companyRoles"] = [{"companyRole": role, "status": status}
                            for role, status in store.list_roles(row["id"]).items()]
    return view


# ----------------------------------------------------------------------------------- steps (8.1)
def _stub_applications() -> dict[str, dict]:
    """Built-in stand-in for C1-M2 (11.1): `STUB_APPLICATIONS_FILE` in `ApplicationInternal` form."""
    path = config.stub_applications_file()
    if path is None:
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    entries = document.get("applications") if isinstance(document, dict) else document
    return {entry["id"]: entry for entry in entries or []}


def _application(application_id: str | None) -> dict:
    config.apply_registration_url()
    """The application at C1-M2 (11.1); a failed call is an error, not "not found" (skill 5)."""
    if neighbours.is_standin("c1-m2"):
        application = _stub_applications().get(application_id or "")
        if application is None:
            raise Problem(MODULE, 404, "not-found", detail="application unknown", retryable=False)
        return application
    try:
        application = neighbours.query(MODULE, "c1-m2", "get_application_internal",
                                       applicationId=application_id)
    except Problem:
        raise
    if not application:
        raise Problem(MODULE, 404, "not-found", detail="application unknown", retryable=False)
    return application


def create_company(input: dict) -> dict:
    """8.1: create the company `REQUESTED` from a submitted application of kind ONBOARDING/TRANSFER."""
    cid, application_id = input.get("companyId"), input.get("applicationId")
    existing = store.get_company(cid)
    if existing is not None:
        if existing["application_id"] == application_id:
            return standin.step_reply(input, {"companyId": cid, "status": existing["status"],
                                              "bpn": existing["bpn"],
                                              "coreDataSource": existing["core_data_source"]})
        raise Problem(MODULE, 409, "conflict", detail="company belongs to another application",
                      retryable=False)

    application = _application(application_id)
    if application.get("companyId") != cid:
        raise Problem(MODULE, 409, "conflict", detail="application has another companyId",
                      retryable=False)
    if application.get("kind") == "REACTIVATION":
        raise Problem(MODULE, 409, "conflict", detail="reactivation uses reactivate-company",
                      retryable=False)
    if application.get("status") not in ("SUBMITTED", "APPROVED"):
        raise Problem(MODULE, 409, "invalid-state",
                      detail=f"application {application.get('status')}", retryable=False)

    data = application.get("companyData") or {}
    source_address = data.get("address") or {}
    verification = application.get("verification")
    row = {"name": data.get("legalName"), "short_name": data.get("shortName"),
           "street": source_address.get("streetName"), "house_number": source_address.get("streetNumber"),
           "postal_code": source_address.get("postalCode"), "city": source_address.get("city"),
           "region": source_address.get("region"), "country_code": source_address.get("countryCode")}
    identifiers = [{"type": entry["type"], "value": entry["value"],
                    "source": "BUSINESS_WALLET" if entry.get("source") == "ATTESTATION" else "DECLARED"}
                   for entry in data.get("identifiers") or []]
    roles = [role for role in application.get("companyRoles") or []
             if config.assignable_by(role) == "COMPANY"]

    errors = validation.validate_company(row)
    errors += validation.validate_identifiers(identifiers, row["country_code"])
    for role in application.get("companyRoles") or []:
        errors += validation.validate_company_role(role, config.role_catalogue())
    if verification == "EBW" and not any(entry["type"] == "EBWOID" for entry in identifiers):
        errors.append({"field": "identifiers", "reason": "EBWOID required with a verification"})
    if errors:
        raise Problem(MODULE, 400, "validation", errors=errors, retryable=False)

    attestation = application.get("attestation") or {}
    with store.lock(cid):
        store.create_company(row | {
            "id": cid, "status": "REQUESTED",
            "core_data_source": "EBW" if verification == "EBW" else "MANUAL",
            "core_data_verified_at": attestation.get("verifiedAt") if verification == "EBW" else None,
            "verification_ref": attestation.get("attestationId") if verification == "EBW" else None,
            "application_id": application_id,
        })
        store.set_identifiers(cid, identifiers)
        for role in roles:
            store.add_role(cid, role, status="REQUESTED", source_kind="APPLICATION",
                           source_ref=application_id)
        _audit(cid, "stepCreateCompany", input, {"applicationId": application_id})
        created = get_company(cid)
        events.publish(MODULE, "CompanyCreated", {"companyId": cid, "applicationId": application_id,
                                                  "coreDataSource": created["core_data_source"]})
    return standin.step_reply(input, {"companyId": cid, "status": created["status"],
                                      "bpn": created["bpn"],
                                      "coreDataSource": created["core_data_source"]})


# ----------------------------------------------------------------------------------- steps (8.2)
def assign_identifier(input: dict) -> dict:
    """8.2: take over the BPN from `CompanyRegisteredAtCsp`."""
    cid, raw = input.get("companyId"), input.get("bpn") or ""
    with store.lock(cid):
        row = get_company(cid)
        errors = validation.validate_bpn(raw)
        if errors:
            raise Problem(MODULE, 400, "validation", errors=errors, retryable=False)
        bpn = raw.strip().upper()
        if row["bpn"]:
            if row["bpn"] == bpn:
                return standin.step_reply(input, {"companyId": cid, "status": row["status"], "bpn": bpn})
            raise Problem(MODULE, 409, "bpn-mismatch", detail=f"company has {row['bpn']}",
                          retryable=False)
        if row["status"] != "REQUESTED":
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"], retryable=False)
        taken = next((other for other in store.find_companies(bpn=bpn, size=5)[0]
                      if other["id"] != cid and other["status"] != "REJECTED"), None)
        if taken is not None:
            raise Problem(MODULE, 409, "bpn-taken", detail=taken["id"], retryable=False)
        store.update_company(cid, bpn=bpn, bpn_assigned_at=_now())
        _audit(cid, "stepAssignIdentifier", input, {"bpn": bpn})
        events.publish(MODULE, "CompanyIdentifierAssigned", {"companyId": cid, "bpn": bpn})
    return standin.step_reply(input, {"companyId": cid, "status": row["status"], "bpn": bpn})


# ----------------------------------------------------------------------------------- steps (8.3)
def _terms_of_roles() -> dict[str, set[str]]:
    config.apply_registration_url()
    """agreementKey -> roles it belongs to, from the terms of C1-M2 (11.1).

    Without an address for C1-M2 the built-in stand-in answers with the initial values of 14.3.
    """
    if neighbours.is_standin("c1-m2"):
        agreements = testdata.agreements()
    else:
        agreements = neighbours.query(MODULE, "c1-m2", "list_agreements_internal") or []
    terms: dict[str, set[str]] = {}
    for agreement in agreements:
        if agreement.get("scope") != "COMPANY_ROLE":
            continue
        for role in agreement.get("companyRoles") or []:
            terms.setdefault(agreement["agreementKey"], set()).add(role)
    return terms


def activate_company(input: dict) -> dict:
    """8.3: activate, taking over the consents of the application."""
    cid, application_id = input.get("companyId"), input.get("applicationId")
    with store.lock(cid):
        row = get_company(cid)
        if row["status"] == "ACTIVE":
            return standin.step_reply(input, {"companyId": cid, "status": row["status"],
                                              "bpn": row["bpn"],
                                              "companyRoles": _active_roles(cid),
                                              "pendingCompanyRoles": []})
        if row["status"] in ("REJECTED", "INACTIVE"):
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"], retryable=False)
        if not row["bpn"]:
            raise Problem(MODULE, 409, "identifier-missing", retryable=False)
        if application_id != row["application_id"]:
            raise Problem(MODULE, 409, "conflict", detail="application does not match",
                          retryable=False)

        application = _application(application_id)
        terms = _terms_of_roles()
        given = {consent.get("agreementKey"): consent for consent in application.get("consents") or []}
        active, pending = [], []
        for role, status in store.list_roles(cid).items():
            if status != "REQUESTED":
                continue
            needed = {key for key, roles in terms.items() if role in roles}
            if needed <= set(given):
                active.append(role)
            else:
                pending.append(role)
        if not active:
            raise Problem(MODULE, 409, "roles-without-consent", missing=sorted(pending),
                          retryable=False)

        applicant = (application.get("applicant") or {}).get("sub")
        for role in active:
            store.add_role(cid, role, status="ACTIVE", source_kind="APPLICATION",
                           source_ref=application_id)
            for key in (key for key, roles in terms.items() if role in roles):
                store.set_consent(cid, key, version=given[key].get("version"), status="ACTIVE",
                                  source_kind="APPLICATION", source_ref=application_id,
                                  consented_by=applicant, consented_at=given[key].get("givenAt"))
        fields = {"status": "ACTIVE", "activated_at": _now()}
        if row["core_data_source"] == "MANUAL" and not row["core_data_verified_at"]:
            fields["core_data_verified_at"] = _now()
        store.update_company(cid, **fields)
        _audit(cid, "stepActivateCompany", input, {"applicationId": application_id,
                                                   "companyRoles": sorted(active)})
        events.publish(MODULE, "CompanyActivated", {"companyId": cid, "bpn": row["bpn"],
                                                    "companyRoles": sorted(active)})
    return standin.step_reply(input, {"companyId": cid, "status": "ACTIVE", "bpn": row["bpn"],
                                      "companyRoles": sorted(active), "pendingCompanyRoles": pending})


# ----------------------------------------------------------------------------------- steps (8.4)
def reject_company(input: dict) -> dict:
    """8.4: `REJECTED`, final; an assigned BPN becomes free."""
    cid = input.get("companyId")
    with store.lock(cid):
        row = get_company(cid)
        if row["status"] == "REJECTED":
            return standin.step_reply(input, {"companyId": cid, "status": row["status"]})
        if row["status"] in ("ACTIVE", "INACTIVE"):
            raise Problem(MODULE, 409, "invalid-state", detail=row["status"], retryable=False)
        store.update_company(cid, status="REJECTED", rejected_at=_now())
        _audit(cid, "stepRejectCompany", input)
        events.publish(MODULE, "CompanyRejected", {"companyId": cid})
    return standin.step_reply(input, {"companyId": cid, "status": "REJECTED"})


# ------------------------------------------------------------------------ change by people (7.2)
CORE_TEXT_FIELDS = ("name", "street", "house_number", "address_addition", "postal_code", "city",
                    "region", "country_code")
CAMEL = {snake: camel for camel, snake in validation.ALIASES.items()}


def _changed_fields(row: dict, body: dict, identifiers: list[dict] | None) -> list[str]:
    """Names of the fields the body really changes, camelCase, for the event (README 7.2, 7.12)."""
    changed = []
    for key, value in body.items():
        field = validation.field_name(key)
        if field in CORE_TEXT_FIELDS or field == "short_name":
            before, after = row.get(field), value
            if (before or "") != (after or "") and not (
                    before and after and validation.same_value(before, after)):
                changed.append(CAMEL.get(field, field))
    if identifiers is not None:
        before = {(entry["type"], entry["value_normalized"]) for entry in store.list_identifiers(row["id"])}
