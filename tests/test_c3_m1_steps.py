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
"""C3-M1 steps and queries against the built-in stand-in of C1-M2 (README 8, 9, 13).

The applications of README 14 (A1, A2, A3, A5) are seeded into the C1-M2 stand-in, which is what
`create-company` and `activate-company` read over the neighbour call (11.1).
"""
import json

import pytest

from modules.c1_m2 import interface as c1_m2
from modules.c3_m1 import interface, store
from portal_common import events
from portal_common.problems import Problem

U1 = "c0000001-0000-4000-8000-000000000001"
U2 = "c0000002-0000-4000-8000-000000000002"
U3 = "c0000003-0000-4000-8000-000000000003"
A1 = "a0000001-0000-4000-8000-000000000001"
