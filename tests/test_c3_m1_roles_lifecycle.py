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
"""Company roles with consents, deactivation, return and transfer (README 7.7-7.9, 7.13, 8.5, 8.6, 13.19-13.22, 13.26, 13.27)."""
import pytest

from modules.c3_m1 import interface, store
from portal_common import events
from portal_common.problems import Problem

from test_c3_m1_api import S2, U1, U2, active, call, client  # noqa: F401
from test_c3_m1_attestation import _keys  # noqa: F401  (fixture: attestation environment)
from test_c3_m1_steps import A1, A3, ADDRESS, CONSENTS, P1, U3, seed, step

A5 = "a0000005-0000-4000-8000-000000000005"
A6 = "a0000006-0000-4000-8000-000000000006"
