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
