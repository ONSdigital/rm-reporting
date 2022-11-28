import io
import logging

from flask import make_response
from flask_restx import Resource, abort
from openpyxl import Workbook
from structlog import wrap_logger

from rm_reporting import response_chasing_api
from rm_reporting.common.validators import parse_uuid
from rm_reporting.controllers import case_controller, party_controller

logger = wrap_logger(logging.getLogger(__name__))


@response_chasing_api.route("/download-report/<collection_exercise_id>/<survey_id>")
class ResponseChasingDownload(Resource):
    @staticmethod
    def get(collection_exercise_id, survey_id):
        parsed_survey_id = parse_uuid(survey_id)
        if not parsed_survey_id:
            logger.debug("Responses dashboard endpoint received malformed survey ID", invalid_survey_id=survey_id)
            abort(400, "Malformed survey ID")

        parsed_collection_exercise_id = parse_uuid(collection_exercise_id)
        if not parsed_collection_exercise_id:
            logger.debug(
                "Responses dashboard endpoint received malformed collection exercise ID",
                invalid_collection_exercise_id=collection_exercise_id,
            )
            abort(400, "Malformed collection exercise ID")

        output = io.BytesIO()
        wb = Workbook(write_only=True)
        ws = wb.create_sheet()
        ws.title = "Response Chasing Report"

        # Set headers
        headers = [
            "Survey Status",
            "Reporting Unit Ref",
            "Reporting Unit Name",
            "Enrolment Status",
            "Respondent Name",
            "Respondent Telephone",
            "Respondent Email",
            "Respondent Account Status",
        ]
        ws.append(headers)

        # Get case data (and list of ru_refs and business_ids)
        case_result = case_controller.get_case_data(collection_exercise_id)

        # Get all the party_ids for all the businesses that are part of the collection exercise
        business_ids_string = ResponseChasingDownload.get_business_ids_from_case_data(case_result)

        # Get the attribute data for all the businesses in this collection exercise
        attributes_result = party_controller.get_attribute_data(collection_exercise_id)

        # Get all the respondents that are enrolled for all the businesses for this survey
        enrolment_details_result, respondent_ids_string = party_controller.get_enrolment_data(
            survey_id, business_ids_string
        )

        # Resolve all the respondent party_ids into useful data (names, email, etc)
        respondent_details_result = party_controller.get_respondent_data(respondent_ids_string)

        # Loop over all the cases, filling in the blanks along the way and add each row to the spreadsheet
        logger.info("About to loop over all the data")
        for row in case_result:
            survey_status = getattr(row, "status")
            ru_ref = getattr(row, "sample_unit_ref")
            attribute_data = attributes_result[str(getattr(row, "party_id"))]
            ru_name = getattr(attribute_data, "business_name")

            # Create a row in the spreadsheet for each enrolment for this survey in the business
            business_enrolments = enrolment_details_result.get(str(getattr(row, "party_id")), [])
            enrolment_count_for_business = 0
            for enrolment in business_enrolments:
                respondent_details = respondent_details_result[str(getattr(enrolment, "respondent_id"))]

                enrolment_status = getattr(enrolment, "status")
                respondent_name = (
                    getattr(respondent_details, "first_name") + " " + getattr(respondent_details, "last_name")
                )
                respondent_telephone = getattr(respondent_details, "telephone")
                respondent_email = getattr(respondent_details, "email_address")
                respondent_account_status = getattr(respondent_details, "status")

                business = [
                    survey_status,
                    ru_ref,
                    ru_name,
                    enrolment_status,
                    respondent_name,
                    respondent_telephone,
                    respondent_email,
                    respondent_account_status,
                ]
                ws.append(business)
                enrolment_count_for_business += 1

            # If there are no enrolments for the business, we still need to report on it
            if enrolment_count_for_business == 0:
                business = [
                    survey_status,
                    ru_ref,
                    ru_name,
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
                ws.append(business)
        logger.info("Finished looping over cases")
        wb.active = 1
        wb.save(output)
        wb.close()
        logger.info("Finished putting together spreadsheet")

        response = make_response(output.getvalue(), 200)
        response.headers["Content-Disposition"] = f"attachment; filename=response_chasing_{collection_exercise_id}.xlsx"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response

    @staticmethod
    def get_business_ids_from_case_data(case_result) -> str:
        """
        Takes a list of case results and returns a comma separated list of business_ids
        Example output (as a string): 8a4bc9b4-1b8e-4c0f-be72-41da20b82f16, 5b3ac08f-8399-4548-b4d8-0bd2df723672
        :param case_result:
        :return:
        """
        # TODO get the values in a list in a tidier way...
        business_ids_string = ""
        for row in case_result:
            business_ids_string += f"'{str(getattr(row, 'party_id'))}', "
        # slice off the tailing ', '
        business_ids_string = business_ids_string[:-2]
        return business_ids_string
