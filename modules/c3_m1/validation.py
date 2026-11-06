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
"""Field rules of C3-M1 README 5 and the identifier rules of README 6.4.

Every function returns a list of `{"field": ..., "reason": ...}` dicts and never raises, so the
caller can collect all errors into one 400 `validation` Problem (`errors`, README 12). Reason
tokens are short and stable: `required`, `type`, `too-long`, `too-short`, `whitespace`, `format`,
`unknown`, `unknown-country`, `duplicate-type`, `missing`, `business-wallet-source`, `path-parts`,
`media-type`, `too-large`.

Patterns come from the shared reference data (`masterDataFile`, settings key of the same name,
resolved relative to the settings file, OP-13). If the file or a type is missing, the fallback
patterns of README 6.4 apply.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from portal_common import settings

IDENTIFIER_TYPES = ("EUID", "EBWOID", "VAT_ID", "COMMERCIAL_REG_NUMBER", "LEI_CODE", "EORI")
IDENTIFIER_SOURCES = ("BUSINESS_WALLET", "DECLARED")
STATUSES = ("REQUESTED", "ACTIVE", "REJECTED", "INACTIVE")
DEACTIVATION_REASONS = ("MANUAL", "TRANSFERRED")
CORE_DATA_SOURCES = ("EBW", "MANUAL")
MEDIA_TYPES = ("application/pdf", "image/png", "image/jpeg")

NAME_MAX = 160
SHORT_NAME_MAX = 100
STREET_MAX = 255
HOUSE_NUMBER_MAX = 50
ADDRESS_ADDITION_MAX = 255
POSTAL_CODE_MAX = 12
CITY_MAX = 255
REGION_PATTERN = re.compile(r"^[A-Z0-9]{1,3}$")
COUNTRY_PATTERN = re.compile(r"^[A-Z]{2}$")
BPN_PATTERN = re.compile(r"^BPNL[A-Z0-9]{12}$")
COMMENT_MAX = 1000
REASON_MAX = 500
DECISION_REASON_MAX = 1000
FILE_NAME_MAX = 200
NORMALISE_STRIP = re.compile(r"[\s.\-/]")

#: README 6.4 fallbacks, used when the reference data file or the type in it is missing.
FALLBACK_PATTERNS: dict[str, dict[str, str]] = {
    "EUID": {"Worldwide": r"^[A-Za-z0-9.\-]{4,100}$"},
    "EBWOID": {"Worldwide": r"^\S{1,255}$"},
    "VAT_ID": {"Worldwide": r"^(?!.*\s$)([A-Za-z0-9](\.|\s|-|\/)?){5,18}$", "DE": r"^DE\d{9}$"},
    "COMMERCIAL_REG_NUMBER": {
        "Worldwide": r"^(?!.*\s$)([A-Za-zÀ-ÿ0-9.()](\.|\s|-|_)?){4,50}$",
        "DE": r"^(?!.*\s$)([A-Za-zÀ-ÿ])([A-Za-zÀ-ÿ0-9.()](\s|-|_)?){4,50}$",
        "FR": r"^\d{9}$",
    },
    "LEI_CODE": {"Worldwide": r"^[A-Za-z0-9]{20}$"},
    "EORI": {"Worldwide": r"^[A-Z]{2}[A-Za-z0-9]{1,15}$"},
}

#: camelCase of the API -> snake_case of README 5 (`address` is nested, see `flat_fields`).
ALIASES = {
    "shortName": "short_name", "houseNumber": "house_number",
    "addressAddition": "address_addition", "postalCode": "postal_code",
    "countryCode": "country_code", "coreDataSource": "core_data_source",
    "bpnAssignedAt": "bpn_assigned_at", "coreDataVerifiedAt": "core_data_verified_at",
    "verificationRef": "verification_ref", "applicationId": "application_id",
