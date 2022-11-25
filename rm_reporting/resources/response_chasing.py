import csv
import io
import logging
from datetime import datetime

from flask import make_response
from flask_restx import Resource
from openpyxl import Workbook
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from structlog import wrap_logger

from rm_reporting import app, response_chasing_api
from rm_reporting.controllers import case_controller, party_controller

logger = wrap_logger(logging.getLogger(__name__))


@response_chasing_api.route("/download-report/<collection_exercise_id>/<survey_id>")
class ResponseChasingDownload(Resource):
    @staticmethod
    def get(collection_exercise_id, survey_id):

        output = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Response Chasing Report"

        # Set headers
        headers = {
            "A1": "Survey Status",
            "B1": "Reporting Unit Ref",
            "C1": "Reporting Unit Name",
            "D1": "Enrolment Status",
            "E1": "Respondent Name",
            "F1": "Respondent Telephone",
            "G1": "Respondent Email",
            "H1": "Respondent Account Status",
        }

        for cell, header in headers.items():
            ws[cell] = header
            ws.column_dimensions[cell[0]].width = len(header)

        # Way to create spreadsheet
        # Get case data (and list of ru_refs and business_ids)
        case_result = case_controller.get_case_data(collection_exercise_id)

        # Get all the party_ids for all the businesses that are part of the collection exercise
        # TODO get the values in a list in a tidier way...
        business_ids_string = ""
        for row in case_result:
            business_ids_string += f"'{str(getattr(row, 'party_id'))}', "

        # slice off the tailing ', '
        business_ids_string = business_ids_string[:-2]

        attributes_result = party_controller.get_attribute_data(collection_exercise_id)

        enrolment_details_result, respondent_ids_string = party_controller.get_enrolment_data(survey_id,
                                                                                              business_ids_string)

        respondent_details_result = party_controller.get_respondent_data(respondent_ids_string)

        # Loop over all the cases, filling in the blanks along the way and add each row to the spreadsheet
        logger.info("About to loop over all the data")
        for row in case_result:
            logger.info("Dealing with ru", ru_ref=getattr(row, "sample_unit_ref"))
            survey_status = getattr(row, "status")
            ru_ref = getattr(row, "sample_unit_ref")
            ru_name = ""
            for business in attributes_result:
                if getattr(business, "business_party_uuid") == getattr(row, "party_id"):
                    ru_name = getattr(business, "business_name")
                    break

            # Create a row in the spreadsheet for each enrolment for this survey in the business
            business_enrolments = enrolment_details_result.get(str(getattr(row, 'party_id')), [])
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

        wb.active = 1
        wb.save(output)
        wb.close()
        logger.info("Finished putting together spreadsheet")

        response = make_response(output.getvalue(), 200)
        response.headers["Content-Disposition"] = f"attachment; filename=response_chasing_{collection_exercise_id}.xlsx"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response


@response_chasing_api.route("/download-social-mi/<collection_exercise_id>")
class SocialMIDownload(Resource):
    @staticmethod
    def get(collection_exercise_id):
        output = io.StringIO()

        # Set headers
        headers = [
            "Sample Reference",
            "Status",
            "Status Event",
            "Address Line 1",
            "Address Line 2",
            "Locality",
            "Town Name",
            "Postcode",
            "Country",
        ]

        datestr = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        engine = app.db.engine

        case_status = text(
            "SELECT cg.sampleunitref, cg.status, "
            "(SELECT cat.shortdescription "
            "FROM casesvc.caseevent ce "
            "JOIN casesvc.category cat "
            "ON ce.categoryfk = cat.categorypk "
            "WHERE ce.casefk = c.casepk "
            "AND cat.shortdescription ~ '^[[:digit:]]*$' "
            "ORDER BY ce.createddatetime DESC LIMIT 1), "
            "attributes->> 'ADDRESS_LINE1' AS address_line_1, "
            "attributes->> 'ADDRESS_LINE2' AS address_line_2, "
            "attributes->> 'LOCALITY' AS locality, "
            "attributes->> 'TOWN_NAME' AS town_name, "
            "attributes->> 'POSTCODE' AS postcode, "
            "attributes->> 'COUNTRY' AS country "
            "FROM casesvc.case c "
            "JOIN casesvc.casegroup cg "
            "ON c.casegroupfk = cg.casegrouppk "
            "JOIN samplesvc.sampleattributes sa "
            "ON CONCAT(attributes->> 'TLA', '' , attributes->> 'REFERENCE') = cg.sampleunitref "
            "WHERE c.sampleunittype = 'H' AND cg.collectionexerciseid = :collection_exercise_id"
        )

        try:
            case_details = engine.execute(case_status, collection_exercise_id=collection_exercise_id)
        except SQLAlchemyError:
            logger.exception("SQL Alchemy query failed")
            raise

        my_data = [headers]
        my_data.extend(case_details)

        writer = csv.writer(output)
        writer.writerows(my_data)

        response = make_response(output.getvalue(), 200)
        response.headers["Content-Disposition"] = (
            f"attachment; filename=social_mi_report_{collection_exercise_id}" f"_{datestr}.csv"
        )
        response.headers["Content-type"] = "text/csv"
        return response
