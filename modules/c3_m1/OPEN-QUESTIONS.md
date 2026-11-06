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

# C3-M1 open questions

Points the spec leaves open, contradicts or that the scaffold does not carry yet. Each names the
spec section, the reading implemented here and who can decide. Nothing here is a silent guess: the
reading is in the code, marked as such.

| No. | Question | Spec | Reading implemented | To be decided by |
|---|---|---|---|---|
| 1 | The README makes the own database `c3_m1` (PostgreSQL, own user) obligatory, but the scaffold has no database driver, no `DATABASE_URL` reader and no database service in `docker-compose.yml`. How does the module run without them? | C3-M1 4, 5 (`DATABASE_URL`); FRAMEWORK 1; FRAMEWORK 4.8 (a value without an empty-value meaning is required) | `DATABASE_URL` **empty = in-memory transport** (`store_memory.py`), set = the PostgreSQL transport (`store_postgres.py`, schema `schema.sql`). Both answer the same functions and the same invariants, so the module runs at the hackathon without a server and switches over without a code change. If `DATABASE_URL` is set but the driver is missing, the module answers `501 not-implemented` and names the package — the same answer every unimplemented operation gives. | Maintainers (dependency and compose service), spec authors |
| 2 | The driver `psycopg[binary]` is missing from `pyproject.toml`, so the PostgreSQL transport only runs when the installation adds it. | — (consequence of 1) | Legitimate later feature. The transport is imported lazily, the whole store suite passes against a real PostgreSQL (`TEST_DATABASE_URL`), and until the dependency is added the path answers `501 not-implemented`. | Maintainers |
| 3 | README 4 gives `STUB_APPLICATIONS_FILE` for the built-in stand-in of C1-M2: applications in the `ApplicationInternal` format. The file ships nowhere, and the C1-M2 stand-in of the scaffold keeps applications created through its own steps instead of reading it. | C3-M1 4, 11.1 | Both readings are built: with no address for C1-M2 the module answers from `STUB_APPLICATIONS_FILE` (case 28 tests this), and in-process it uses the live C1-M2 stand-in. A shipped file would only replace the test's own. | C1-M2 team, maintainers |
| 4 | 7.8 requires consent "with its active version"; 6.5 says "to any version of the key". Which rule wins when a consent names an older version? | C3-M1 6.5, 7.8 | 7.8 is the operation-level rule and wins: a consent with another version counts as missing (`400 consent-missing`, key in `missing`). | Spec authors |
| 5 | The `bpn` of the OSP company comes from the seed file, while 6.2 says the BPN is only ever assigned by the CSP. | C3-M1 4 (seed data), 6.2, FRAMEWORK 4.8, 7a | The seed data wins for the OSP company; it is created `ACTIVE` without an `assign-identifier` call and its BPN counts as taken. | Spec authors (OP-36) |
| 6 | README 4 declares `DATABASE_URL` without an example, while FRAMEWORK 4.8 treats addresses of other systems as mandatory. | FRAMEWORK 4.8 | Both readings are kept compatible (see 1): no error on an empty value, so tests and `demo.py` need no server. | Spec authors |
| 7 | `stub-ebw-jwks.json` is named in 4 and 14 as the test JWKS, but the file ships neither in the spec folder nor in `testdata/`. | C3-M1 4, 14; C1-M2 14 (same variable, file `test-ebw-jwks.json`) | Minted in the module as a real EC P-256 key pair: `stub-ebw-jwks.json` (public JWK) and `stub-ebw-key.json` (private JWK), kid `ebw-test-2026-1`. T4 uses a second, foreign key generated in the test. | Maintainers (may move the files to `testdata/`) |
| 8 | 14 says the private part is "only in the test data", without naming a place; C1-M2 14 generates the key pair at start instead of shipping anything. | C3-M1 14; C1-M2 14 | Follows C1-M2: the private JWK sits next to the module and the tests sign with it, so no key is shared with `testdata/`. | Spec authors (C1-M2 does the same differently) |
| 9 | The scaffold calls every module's `reset()` at each start; with `DATABASE_URL` set, the PostgreSQL transport drops and recreates its tables there, so a restart empties the module's own database. | C3-M1 4 (seed data), FRAMEWORK 1 | `reset()` keeps its scaffold meaning (empty state, for tests and boot). The seed is written only when the OSP company does not exist yet, so a restart does not duplicate it; the tables still start empty on every boot. Without the driver the start degrades to the in-memory transport, and the calls answer 501. Durable data across restarts is later work. | Maintainers (scaffold lifecycle) |
| 10 | README 4 writes `ATTESTATION_JWKS_FILE` and `STUB_APPLICATIONS_FILE` as bare names; FRAMEWORK 4.8 only defines relative paths for installation settings, not for configuration variables. | C3-M1 4, 14; FRAMEWORK 4.8 | A bare name counts from this module folder (where the two files live), an absolute path as given. | Spec authors |
| 11 | 8.6 point 3 asks for the address "as in 6.3", but the application of C1-M2 carries `streetName` and `streetNumber` separately, while 6.3 maps a single `street_address` claim and leaves the house number empty. | C3-M1 6.3, 8.6, 11.1 | For a reactivation the split application fields are taken over as they are (`streetName` → `street`, `streetNumber` → `houseNumber`); 6.3's "house number empty" applies only to an attestation claim. | C1-M2, spec authors |
| 12 | 8.6 names "Application approved" as the precondition, but `ApplicationStatus` of C1-M2 has no `APPROVED`, and `flows.yaml` (`reactivation`, `return`) runs `reactivate-company` while the application is still `SUBMITTED` (the approval is the C1-M3 decision, `complete-application` follows later). | C3-M1 8.6; C1-M2 openapi (`ApplicationStatus`); C12-M1 flows.yaml | Only `CREATED`, `WITHDRAWN` and `DECLINED` are refused (`409 invalid-state`); `SUBMITTED` and `COMPLETED` are accepted. So the flows run and an unsubmitted or withdrawn application is still caught. | Spec authors (an `APPROVED` status for C1-M2) |
| 13 | The registration address has to reach `portal_common.neighbours`, which reads `<MODULE>_URL` / `MODULE_URLS` (AGENTS 6), while README 4 names `REGISTRATION_URL`. | C3-M1 4, 11.1; AGENTS 6; FRAMEWORK 4.7 | `config.apply_registration_url()` copies `REGISTRATION_URL` into `C1_M2_URL` once per `reset()`. When the variable is empty the copy leaves `C1_M2_URL` alone, so `MODULE_URLS` and in-process mode keep working. | Maintainers, once `neighbours` reads the section-4 names |
| 14 | FRAMEWORK 4.8 makes the Example column of section 4 the default, but README 4 marks the JWKS file "tests only"; with a default, an installation would trust a key committed to the repository. | C3-M1 4; FRAMEWORK 4.8 | No default for `ATTESTATION_JWKS_FILE`: empty means `ATTESTATION_JWKS_URL` or no check at all. Tests and `demo.py` set the file. `STUB_APPLICATIONS_FILE` keeps its default, as it is the documented stand-in data. | Spec authors |
| 15 | README 12 lists a `reason` for `attestation-invalid`, but the openapi `Error` items require `{field, message}` for `validation`. | C3-M1 12; openapi `Error` | Follows the openapi: `errors[]` carries `field` and `message`. `attestation-invalid` keeps `reason` at the top level, as section 12 names it there. | Spec authors |
