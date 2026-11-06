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
"""Thin HTTP layer of C3-M1: token, permission, scope, then the interface (AGENTS.md 5).

Every route takes its permission from `x-permission` of the spec through `standin.perm`. Paths in
the scope `company` additionally check `company_id` against the path (FRAMEWORK 4.3: another
company's object stays invisible, 404). No business logic here.
"""
from __future__ import annotations

import json

from fastapi import Body, File, Form, Query, Response, UploadFile

from portal_common import standin
from portal_common.problems import Problem

from . import interface
from .interface import MODULE, company_view, role_view

router = standin.router(MODULE)


def reset() -> None:
    interface.reset()


# ---------------------------------------------------------------------------------- steps (8)
@router.post("/steps/create-company")
def create_company(body: dict = Body(...),
