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
"""Repository of C3-M1 (README 5) with two transports behind one function list.

`DATABASE_URL` selects the transport, read at call time and never at import (AGENTS.md 6):

- empty: `store_memory`, the in-memory transport. Every state is in the process, so the module
  runs without a database (tests, `demo.py`, the hackathon installation).
- set: `store_postgres`, the module's own database `c3_m1` (README 4) with the tables of
  `schema.sql`. The database user of the module owns that schema; nothing else reads it.

Both transports answer the same functions and the same invariants; only the storage differs. A
caller therefore never learns which one runs, except through `backend_name()`. Field names are the
snake_case ones of README 5 — the interface and router map them to camelCase.

Nothing here is FastAPI, HTTP or events, and nothing is cached across a `reset()`.
"""
from __future__ import annotations

import importlib
import os
from types import ModuleType

from portal_common.problems import Problem

MODULE = "c3-m1"
