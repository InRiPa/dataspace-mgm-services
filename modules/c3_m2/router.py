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
"""HTTP layer of C3-M2 CSP Connection under `/api/c3-m2`: token and permission (`x-permission`
of openapi.yaml, all with scope `osp`, FRAMEWORK 4.3), then the function of `interface.py`."""
from __future__ import annotations

from typing import Any

from fastapi import Body, Query

from portal_common import standin

from . import interface
from .interface import MODULE

router = standin.router(MODULE)


def reset() -> None:
    interface.reset()


# ---------------------------------------------------------------- OSP staff (README 7.1)
@router.get("/companies/{companyId}")
def get_csp_registration(companyId: str,  # noqa: N803 - openapi name
                         _: dict = standin.perm(MODULE, "GET", "/companies/{companyId}")) -> dict:
    return interface.get_csp_registration(companyId=companyId)


# ---------------------------------------------------------------- callback of the CSP (README 7.2)
@router.post("/csp-notifications")
def receive_csp_notification(body: Any = Body(...),
                             _: dict = standin.perm(MODULE, "POST", "/csp-notifications")) -> dict:
    return interface.receive_csp_notification(body)


# ---------------------------------------------------------------- query (README 9)
@router.get("/internal/find-companies")
def find_companies(_: dict = standin.perm(MODULE, "GET", "/internal/find-companies"),
                   ebwoid: str | None = None, euid: str | None = None,
                   identifier: list[str] = Query(default=[]),
                   legalName: str | None = None, country: str | None = None) -> list[dict]:  # noqa: N803
    return interface.find_companies(ebwoid=ebwoid, euid=euid, identifier=identifier, legalName=legalName,
                                    country=country)


# ---------------------------------------------------------------- steps (README 8)
@router.post("/steps/register-company")
def register_company(body: dict = Body(...),
                     _: dict = standin.perm(MODULE, "POST", "/steps/register-company")) -> dict:
    return interface.register_company(body)


@router.post("/steps/transfer-company")
def transfer_company(body: dict = Body(...),
                     _: dict = standin.perm(MODULE, "POST", "/steps/transfer-company")) -> dict:
    return interface.transfer_company(body)


@router.post("/steps/register-did")
def register_did(body: dict = Body(...), _: dict = standin.perm(MODULE, "POST", "/steps/register-did")) -> dict:
    return interface.register_did(body)


@router.post("/steps/update-company")
def update_company(body: dict = Body(...), _: dict = standin.perm(MODULE, "POST", "/steps/update-company")) -> dict:
    return interface.update_company(body)


@router.post("/steps/register-membership")
def register_membership(body: dict = Body(...),
                        _: dict = standin.perm(MODULE, "POST", "/steps/register-membership")) -> dict:
    return interface.register_membership(body)


@router.post("/steps/deregister-membership")
def deregister_membership(body: dict = Body(...),
                          _: dict = standin.perm(MODULE, "POST", "/steps/deregister-membership")) -> dict:
    return interface.deregister_membership(body)


@router.post("/steps/register-connector")
def register_connector(body: dict = Body(...),
                       _: dict = standin.perm(MODULE, "POST", "/steps/register-connector")) -> dict:
    return interface.register_connector(body)


@router.post("/steps/deregister-connector")
def deregister_connector(body: dict = Body(...),
                         _: dict = standin.perm(MODULE, "POST", "/steps/deregister-connector")) -> dict:
    return interface.deregister_connector(body)
