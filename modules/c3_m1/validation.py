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

