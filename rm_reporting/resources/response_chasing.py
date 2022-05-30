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
from rm_reporting.controllers import party_controller

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

        engine = app.db.engine

        case_status = (
            "SELECT "
            "sample_unit_ref, status"
            " FROM casesvc.casegroup cg"
            f" WHERE collection_exercise_id = '{collection_exercise_id}' "
            "ORDER BY status, sample_unit_ref"
        )

        try:
            case_status = engine.execute(text(case_status))
        except SQLAlchemyError:
            logger.exception("SQL Alchemy query failed")
            raise

        for row in case_status:
            reporting_unit = party_controller.get_business_by_ru_ref(row[0])
            # Get all respondents for the given ru
            respondent_party_ids = [respondent["partyId"] for respondent in reporting_unit.get("associations")]
            respondents = party_controller.get_respondent_by_party_ids(respondent_party_ids)
            if len(respondents) == 0:
                business = [row[1], row[0], reporting_unit.get("name"), None, None, None, None, None]
                ws.append(business)
                continue

            for respondent in respondents:
                ru_status = next(item for item in respondent.get("associations") if item["sampleUnitRef"] == row[0])
                enrolment_status = next(item for item in ru_status.get("enrolments") if item["surveyId"] == survey_id)
                business = [
                    row[1],
                    row[0],
                    reporting_unit.get("name"),
                    enrolment_status.get("enrolmentStatus"),
                    respondent.get("firstName"),
                    respondent.get("telephone"),
                    respondent.get("emailAddress"),
                    respondent.get("status"),
                ]
                ws.append(business)

        wb.active = 1
        wb.save(output)
        wb.close()

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
