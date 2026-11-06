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
"""Calls of the core services API of the CSP (README 11.1).

With `CSP_URL` set, the call goes over HTTP through `portal_common.csp` (client credentials with
`private_key_jwt`, README 4; timeout 10 s from `portal_common.http`). With an empty `CSP_URL`,
the built-in stand-in of README 11.3 answers in memory, with the companies of `CSP_STUB_FILE`.
Every call writes an audit entry (README 5) with the HTTP status and the CSP's error type only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from portal_common import csp, settings
from tools.csp_standin.core import CoreServices

from . import errors, store

_builtin: CoreServices | None = None


def reset() -> None:
    global _builtin
    _builtin = None


def _stub_companies() -> list[dict]:
    """`CSP_STUB_FILE` (README 4, 14): a list of companies, or an object with `companies`."""
    path = os.environ.get("CSP_STUB_FILE", "")
    if not path:
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return list(data.get("companies", [])) if isinstance(data, dict) else list(data)


def _osp_company() -> list[dict]:
    """The OSP company of `ospCompanyFile`: the CSP knows it from the admission of the OSP
    (README 4 "Seed data", FRAMEWORK 5.1), so the built-in stand-in knows it as well."""
    path = settings.resolve_path(settings.get("ospCompanyFile"))
    if path is None or not path.exists():
        return []
    c = json.loads(path.read_text(encoding="utf-8"))
    if not c.get("bpn"):
        return []
    return [{"bpn": c["bpn"], "legalName": c.get("name"), "country": (c.get("address") or {}).get("countryCode"),
             "identifiers": c.get("identifiers") or [], "homeOspId": settings.get("ospId"), "memberActive": True}]


def _builtin_core() -> CoreServices:
    global _builtin
    if _builtin is None:
        stub = _stub_companies()
        stub += [c for c in _osp_company() if c["bpn"] not in {s["bpn"] for s in stub}]
        osps: dict[str, dict] = {settings.get("ospId"): {"name": settings.get("ospName")}}
        for c in stub:
            osps.setdefault(c["homeOspId"], {"name": c.get("homeOspName")})
        _builtin = CoreServices(osps, stub)
    return _builtin


def csp_type(answer: Any) -> str | None:
    """`type` of a Problem Details answer of the CSP, if any."""
    return answer.get("type") if isinstance(answer, dict) and isinstance(answer.get("type"), str) else None


def call(operation: str, method: str, path: str, body: dict | None = None, params: dict | None = None, *,
         company_id: str | None = None, bpn: str | None = None) -> tuple[int, Any]:
    """One call of the core services API; returns (HTTP status, JSON body or None).
    No answer from the CSP (timeout, connection, token endpoint): 502 `upstream-error`, retryable."""
    base = os.environ.get("CSP_URL", "")
    try:
        if base:
            status, answer = csp.request(base, method, path, body, params)
        else:
            status, answer = _builtin_core().dispatch(settings.get("ospId"), method, path, body, params)
    except csp.CspUnavailable as e:
        store.record_audit(operation, company_id, bpn, None, "unavailable")
        raise errors.upstream_error(f"CSP not reachable: {e}") from e
    except (OSError, ValueError) as e:   # OSP_SIGNING_KEY_FILE missing or not a JWK: no token for the CSP
        store.record_audit(operation, company_id, bpn, None, "signing-key")
        raise errors.upstream_error("the signing key of the OSP (OSP_SIGNING_KEY_FILE) is not readable") from e
    store.record_audit(operation, company_id, bpn, status, csp_type(answer))
    return status, answer


def is_business_rejection(status: int) -> bool:
    """README 12: a 4xx of the CSP is a business rejection, except a token problem (401) and
    temporary answers (408, 429)."""
    return 400 <= status < 500 and status not in (401, 408, 429)


def raise_for(status: int, answer: Any, ok: tuple[int, ...] = (200, 201, 204)) -> None:
    """Maps an unexpected answer of the CSP to README 12: business rejection -> `csp-rejected`
    (not retryable); everything else (5xx, 401, 408, 429) -> `upstream-error` (retryable)."""
    if status in ok:
        return
    if is_business_rejection(status):
        raise errors.csp_rejected(f"the CSP rejected the call with {status}", csp_type(answer))
    raise errors.upstream_error(f"the CSP answered {status}")
