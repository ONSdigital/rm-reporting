import csv
import io

from openpyxl import Workbook

from rm_reporting.controllers.response_chasing_controller import (
    COLUMN_TITLES,
    create_csv_report,
    create_xslx_report,
)

COLLECTION_EXERCISE_ID = "33db9feb-bed0-46e8-bcb1-3a0373224cd3"
SURVEY_ID = "57586798-74e3-49fd-93da-a782ec5f5129"


def test_create_csv_report(cases, business_enrolments, business_attributes, respondents, expected_report_rows, mocker):
    _patch_report_data(business_attributes, business_enrolments, cases, mocker, respondents)

    csv_report = create_csv_report(COLLECTION_EXERCISE_ID, SURVEY_ID)

    expected_report = io.StringIO()
    csv_writer = csv.writer(expected_report)
    csv_writer.writerow(COLUMN_TITLES)
    for row in expected_report_rows:
        csv_writer.writerow(row)
    assert expected_report.getvalue() == csv_report.getvalue()


def test_create_xslx_report(cases, business_enrolments, business_attributes, respondents, expected_report_rows, mocker):
    _patch_report_data(business_attributes, business_enrolments, cases, mocker, respondents)

    xslx_report = create_xslx_report(COLLECTION_EXERCISE_ID, SURVEY_ID)

    expected_report = io.BytesIO()
    wb = Workbook(write_only=True)
    ws = wb.create_sheet()
    ws.title = "Response Chasing Report"
    ws.append(COLUMN_TITLES)
    for row in expected_report_rows:
        ws.append(row)
    wb.active = 1
    wb.save(expected_report)
    assert expected_report.getvalue() == xslx_report.getvalue()


def _patch_report_data(business_attributes, business_enrolments, cases, mocker, respondents):
    mocker.patch("rm_reporting.controllers.response_chasing_controller.get_case_data", return_value=cases)
    mocker.patch("rm_reporting.controllers.response_chasing_controller.get_respondent_data", return_value=respondents)
    mocker.patch(
        "rm_reporting.controllers.response_chasing_controller.get_enrolment_data", return_value=business_enrolments
    )
    mocker.patch(
        "rm_reporting.controllers.response_chasing_controller.get_business_attributes", return_value=business_attributes
    )
