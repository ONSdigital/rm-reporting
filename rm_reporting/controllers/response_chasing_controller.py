import csv
import io
import logging
from typing import IO, Callable
from uuid import UUID

from openpyxl import Workbook
from structlog import wrap_logger

from rm_reporting.controllers.case_controller import (
    get_business_ids_from_case_data,
    get_case_data,
)
from rm_reporting.controllers.party_controller import (
    format_enrolment_data,
    get_business_attributes,
    get_enrolment_data,
    get_respondent_data,
    get_respondent_ids_from_enrolment_data,
)

logger = wrap_logger(logging.getLogger(__name__))


COLUMN_TITLES = [
    "Survey Status",
    "Reporting Unit Ref",
    "Reporting Unit Name",
    "Enrolment Status",
    "Respondent Name",
    "Respondent Telephone",
    "Respondent Email",
    "Respondent Account Status",
    "Respondent Account Status Change Time",
]


def create_xslx_report(ce_id: UUID, survey_id: UUID) -> IO[bytes]:
    output = io.BytesIO()
    work_book = Workbook(write_only=True)
    work_sheet = work_book.create_sheet()
    work_sheet.title = "Response Chasing Report"
    work_sheet.append(COLUMN_TITLES)
    _add_report_data(ce_id, survey_id, work_sheet, _work_sheet_append)
    work_book.active = 1
    work_book.save(output)
    work_book.close()
    return output


def create_csv_report(ce_id: UUID, survey_id: UUID) -> IO[str]:
    output = io.StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow(COLUMN_TITLES)
    _add_report_data(ce_id, survey_id, csv_writer, _csv_write_writerow)
    return output


def _add_report_data(ce_id: UUID, survey_id: UUID, document_object, append_function: Callable) -> None:
    cases_in_ce = get_case_data(ce_id)
    respondents_enrolled_map, businesses_enrolled_map = _get_enrollments(cases_in_ce, survey_id)
    business_attributes_map = get_business_attributes(ce_id)

    for case in cases_in_ce:
        status = getattr(case, "status")
        sample_unit_ref = getattr(case, "sample_unit_ref")
        business_attributes = business_attributes_map[str(getattr(case, "party_id"))]
        business_name = getattr(business_attributes, "business_name")
        status_change_time = getattr(case, "change_state_timestamp")

        respondents_enrolled_for_business = businesses_enrolled_map.get(str(getattr(case, "party_id")), [])

        if respondents_enrolled_for_business:
            for enrolment in respondents_enrolled_for_business:
                enrolment_status = getattr(enrolment, "status")
                respondent_details = respondents_enrolled_map[str(getattr(enrolment, "respondent_id"))]
                respondent_name = (
                    f"{getattr(respondent_details, 'first_name')} {getattr(respondent_details, 'last_name')}"
                )
                respondent_telephone = getattr(respondent_details, "telephone")
                respondent_email = getattr(respondent_details, "email_address")
                respondent_account_status = getattr(respondent_details, "status")

                row = [
                    status,
                    sample_unit_ref,
                    business_name,
                    enrolment_status,
                    respondent_name,
                    respondent_telephone,
                    respondent_email,
                    respondent_account_status,
                    status_change_time,
                ]
                append_function(document_object, row)
        else:
            row = [status, sample_unit_ref, business_name]
            append_function(document_object, row)


def _get_enrollments(cases_in_ce: list, survey_id: UUID) -> tuple[dict, dict]:
    business_ids_in_cases = get_business_ids_from_case_data(cases_in_ce)
    businesses_enrolled = get_enrolment_data(survey_id, business_ids_in_cases)
    respondents_ids = get_respondent_ids_from_enrolment_data(businesses_enrolled)
    respondents_enrolled_map = get_respondent_data(respondents_ids)
    return respondents_enrolled_map, format_enrolment_data(businesses_enrolled)


def _work_sheet_append(work_sheet, row: list) -> None:
    work_sheet.append(row)


def _csv_write_writerow(csv_writer, row: list) -> None:
    csv_writer.writerow(row)
