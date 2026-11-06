<!--
 Copyright (c) 2026 Technovative Solutions
 Copyright (c) 2026 Contributors to the Eclipse Foundation

 See the NOTICE file(s) distributed with this work for additional
 information regarding copyright ownership.

 This program and the accompanying materials are made available under the
 terms of the Apache License, Version 2.0 which is available at
 https://www.apache.org/licenses/LICENSE-2.0.

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.

 AI Disclosure: This file was entirely AI-generated.
 The AI-generated portions are made available under CC0-1.0 and not subject
 to the project's license. The human contributor has reviewed and verified
 that the code is correct.

 SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
 Assisted-By: Claude Code (claude-opus-5-5)
-->

# C3-M2 CSP Connection: open questions

Points where the spec (`spec/C3-M2-CSPConnection`, as of 2026-10-30) is unclear or silent, the
reading this implementation follows, and who could decide. AGENTS.md rule 10.

| No. | Question | Spec | Reading implemented | To decide |
|---|---|---|---|---|
| 1 | Precondition of `register-company`: "no row in `REGISTERED` for another company with the same EBWOID or EUID". The module stores no EBWOID or EUID (README 5 "Not stored"). How is this checked? | README 5, 8.1 | Checked through the BPN: if the CSP confirms a BPN (201) that another company of this installation already holds as `REGISTERED`, the step answers 409 `invalid-state` and changes nothing. | spec authors |
| 2 | Which answers of the CSP to `register-company` / `transfer-company` set status `FAILED`? README 8.1 names only 409. | README 6.1, 8.1, 12 | 409 → `FAILED` with reason `REGISTERED_AT_OTHER_OSP` and `registered-at-other-osp`. Any other business rejection (4xx except 401, 408, 429) → `FAILED` with reason `REJECTED_BY_CSP`, `CompanyRegistrationAtCspFailed`, and `csp-rejected`. 5xx and no answer → `upstream-error`, status unchanged. | spec authors, CSP |
| 3 | Is a 409 of the CSP on calls other than register/transfer a `csp-rejected`? README 12 says "4xx except 409". | README 12 | Only register/transfer treat 409 as `registered-at-other-osp`; on all other calls a 409 is a business rejection → `csp-rejected`. | spec authors |
| 4 | Is a 401 or 403 of the CSP a business rejection? | README 4, 12 | 401 (token rejected) → `upstream-error`, retryable. 403 (for example "not home OSP") → `csp-rejected`, not retryable. 408 and 429 → `upstream-error`. | CSP |
| 5 | `update-company` is idempotent how? The module keeps no core data to compare with. | README 5, 6.4, 8.4, FRAMEWORK 4.4 | A repetition with the same `stepRunId` returns `DONE` without a call and without an event; a new `stepRunId` always calls the CSP (`PATCH` is idempotent at the CSP). | spec authors |
| 6 | `register-company` while the status is `TRANSFERRED_AWAY`. | README 6.1 | 409 `invalid-state`: the way back is `transfer-company` (6.1). | spec authors |
| 7 | `deregister-connector` for a known connector whose company is no longer `REGISTERED` (for example `TRANSFERRED_AWAY`). | README 6.4, 8.6 | 409 `invalid-state` (precondition of 8.6). Unknown or already removed connectors answer `DONE` without a call (6.4). | spec authors, C6-M1 |
| 8 | Result of `deregister-connector` for an unknown connector: README 8.6 asks for `bpn` and `connectorId`. | README 8.6 | `connectorId` always; `bpn` only if the connector or the company is known. | spec authors |
| 9 | `OperationCompleted` with `SUCCEEDED` without `bpn`. | README 7.2 | 400 `validation`: the BPN is needed for `REGISTERED`. The operation id finds the registration; the BPN is a fallback only for a `PENDING` registration, so a late notification cannot revive a `FAILED` or `TRANSFERRED_AWAY` company. A notification for an unknown operation or BPN is 404 `unknown-company` and is not stored, so the CSP may send it again. | CSP |
| 10 | Built-in stand-in (empty `CSP_URL`) and the OSP company: README 13 case 13 expects `register-connector` for the OSP company to reach the CSP. | README 4, 11.3, 13 | The built-in stand-in also knows the OSP company from `ospCompanyFile` (as the CSP knows it from the admission, FRAMEWORK 5.1), so the call succeeds. | – |
| 11 | `OSP_SIGNING_KEY_FILE` missing or unreadable. | README 4 | 502 `upstream-error`, retryable (no token for the CSP), without the path or key content in the answer. | – |
| 12 | Audit log: README 5 asks for one entry per call to the CSP and per notification; FRAMEWORK 4.3 asks for the `sub` of the acting person on every changing operation. | README 5, FRAMEWORK 4.3 | Entries per CSP call and per notification (time, operation, `company_id`, `bpn`, HTTP status, CSP error type). The `sub` is not recorded: steps and callbacks are called by service accounts. | spec authors |
| 13 | Persistence: README 4 asks for an own PostgreSQL database `c3_m2` (`DATABASE_URL`). | README 4, 5 | In memory for the hackathon (allowed by the implement skill); `reset()` empties it and re-creates the seed data. | team, after the hackathon |
| 14 | What does the module still know about a company that moved to another OSP? README 8.5 says the membership value "is no longer known here"; the spec says nothing about the DID and the connectors, which the new home OSP can change at the CSP as well. | README 6.4, 8.3, 8.5, 8.6, FRAMEWORK 5.6 | The same reading for all three: on `CompanyTransferredAway` the DID is forgotten, the membership becomes `NONE` and the company's connectors `DEREGISTERED`, without events. After a return, `register-did`, `register-membership` and `register-connector` call the CSP again even with unchanged values. **Gap in the flows:** the return flow of `flows.yaml` (FRAMEWORK 5.6, company comes back) calls only `transfer-company` and `register-membership`; no step calls `register-did` or `register-connector`, so the CSP's directory BPN → DID and its connector list are not refreshed after a return. The module is ready for those steps; adding them is up to C12-M1 and the spec (issue to raise). | spec authors, C12-M1, CSP |
