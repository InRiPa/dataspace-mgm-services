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
"""Configuration of C3-M1: the variables of README 4, read at call time and never at import.

FRAMEWORK 4.8 makes the example column the default, so a module starts without any setting. Values
that differ per installation (the seed company, the dataspace, the reference data) come from the
installation settings through `portal_common.settings`; the module keeps no installation data.

Paths in the settings count from the settings file (FRAMEWORK 4.8); the path of a configuration
variable (`COMPANY_ROLES_FILE`) counts from the repository root.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from portal_common import settings
from portal_common.spec import ROOT

MODULE = "c3-m1"

