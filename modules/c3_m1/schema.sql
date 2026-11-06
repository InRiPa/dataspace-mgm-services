-- #################################################################################
-- #  Copyright (c) 2026 Contributors to the Eclipse Foundation
-- #
-- #  See the NOTICE file(s) distributed with this work for additional
-- #  information regarding copyright ownership.
-- #
-- #  This program and the accompanying materials are made available under the
-- #  terms of the Apache License, Version 2.0 which is available at
-- #  https://www.apache.org/licenses/LICENSE-2.0.
-- #
-- #  Unless required by applicable law or agreed to in writing, software
-- #  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
-- #  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
-- #  License for the specific language governing permissions and limitations
-- #  under the License.
-- #
-- #  AI Disclosure: This file was entirely AI-generated.
-- #  The AI-generated portions are made available under CC0-1.0 and not subject
-- #  to the project's license. The human contributor has reviewed and verified
-- #  that the code is correct.
-- #
-- #  SPDX-License-Identifier: Apache-2.0 AND CC0-1.0
-- #  Assisted-By: Hermes Agent (deepseek-v4.1-flash)
-- #################################################################################
-- C3-M1 Company Profile, own database `c3_m1` (README 4, 5). Field names, types, NOT NULLs,
-- enums and indexes are the ones of README 5; the comments name the section of every block.
-- Not executed by the tests: `modules/c3_m1/store.py` keeps the same shape in memory.

-- C3-M1 5 Table company
CREATE TABLE company (
    id                     uuid                     PRIMARY KEY,
    name                   text                     NOT NULL,
    short_name             text,
    street                 text                     NOT NULL,
    house_number           text,
    address_addition       text,
    postal_code            text,
    city                   text                     NOT NULL,
    region                 text,
    country_code           char(2)                  NOT NULL,
    status                 text                     NOT NULL,
    bpn                    text,
    bpn_assigned_at        timestamptz,
    core_data_source       text                     NOT NULL,
    core_data_verified_at  timestamptz,
    verification_ref       text,
    application_id         uuid,
    deactivation_reason    text,
