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
