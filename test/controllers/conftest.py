from collections import namedtuple

import pytest

BUSINESS_ATTRIBUTE = namedtuple("business_attribute", ["ce_id", "party_id", "business_name"])
CASE = namedtuple("case", ["party_id", "sample_unit_ref", "status", "change_state_timestamp"])
BUSINESS_ENROLMENT = namedtuple("business_enrolment", ["business_id", "respondent_id", "sample_unit_ref", "status"])
RESPONDENT = namedtuple(
    "respondent",
    ["respondent_id", "business_id", "status", "email_address", "first_name", "last_name", "telephone"],
)


@pytest.fixture()
def cases():
    return [
        CASE("20d2eca7-fc2e-408d-88d4-ae841cee728c", "11110000001", "NOTSTARTED", "2024-01-29 14:16:02.105 +0000"),
        CASE("10fbbff8-ec3b-4bdb-bdc4-91a415794fb0", "11110000002", "NOTSTARTED", "2024-01-29 14:16:02.105 +0000"),
        CASE("77e9ee23-6d52-4e63-b581-699afbb4acca", "11110000003", "NOTSTARTED", "2024-01-29 14:16:02.105 +0000"),
    ]


@pytest.fixture()
def business_enrolments():
    return [
        BUSINESS_ENROLMENT(
            "20d2eca7-fc2e-408d-88d4-ae841cee728c", 3, "02b9c366-7397-42f7-942a-76dc5876d86d", "ENABLED"
        ),
        BUSINESS_ENROLMENT(
            "77e9ee23-6d52-4e63-b581-699afbb4acca", 1, "02b9c366-7397-42f7-942a-76dc5876d86d", "ENABLED"
        ),
        BUSINESS_ENROLMENT(
            "77e9ee23-6d52-4e63-b581-699afbb4acca", 2, "02b9c366-7397-42f7-942a-76dc5876d86d", "ENABLED"
        ),
    ]


@pytest.fixture()
def business_attributes():
    return {
        "10fbbff8-ec3b-4bdb-bdc4-91a415794fb0": BUSINESS_ATTRIBUTE(
            "02a883ef-267c-4881-8c37-f5c8068bf740", "10fbbff8-ec3b-4bdb-bdc4-91a415794fb0", "Business 2"
        ),
        "20d2eca7-fc2e-408d-88d4-ae841cee728c": BUSINESS_ATTRIBUTE(
            "02a883ef-267c-4881-8c37-f5c8068bf740", "20d2eca7-fc2e-408d-88d4-ae841cee728c", "Business 3"
        ),
        "77e9ee23-6d52-4e63-b581-699afbb4acca": BUSINESS_ATTRIBUTE(
            "02a883ef-267c-4881-8c37-f5c8068bf740", "77e9ee23-6d52-4e63-b581-699afbb4acca", "Business 1"
        ),
    }


@pytest.fixture()
def respondents():
    return {
        "1": RESPONDENT(
            1,
            "02bbd578-5e9b-40ef-9507-9e398415f6a6",
            "ACTIVE",
            "test1@ons.gov.uk",
            "Respondent 1 first name",
            "Respondent 1 last name",
            "07000000001",
        ),
        "2": RESPONDENT(
            2,
            "f4be71ca-8262-4c56-9d2e-2730b834d6ae",
            "CREATED",
            "test2@ons.gov.uk",
            "Respondent 2 first name",
            "Respondent 2 last name",
            "07000000002",
        ),
        "3": RESPONDENT(
            3,
            "58445f78-3bec-4c83-a8ff-81df471ed214",
            "ACTIVE",
            "test3@ons.gov.uk",
            "Respondent 3 first name",
            "Respondent 3 last name",
            "07000000003",
        ),
    }


@pytest.fixture()
def expected_report_rows():
    return [
        [
            "NOTSTARTED",
            "11110000001",
            "Business 3",
            "ENABLED",
            "Respondent 3 first name Respondent 3 last name",
            "07000000003",
            "test3@ons.gov.uk",
            "ACTIVE",
            "2024-01-29 14:16:02",
        ],
        ["NOTSTARTED", "11110000002", "Business 2"],
        [
            "NOTSTARTED",
            "11110000003",
            "Business 1",
            "ENABLED",
            "Respondent 1 first name Respondent 1 last name",
            "07000000001",
            "test1@ons.gov.uk",
            "ACTIVE",
            "2024-01-29 14:16:02",
        ],
        [
            "NOTSTARTED",
            "11110000003",
            "Business 1",
            "ENABLED",
            "Respondent 2 first name Respondent 2 last name",
            "07000000002",
            "test2@ons.gov.uk",
            "CREATED",
            "2024-01-29 14:16:02",
        ],
    ]
