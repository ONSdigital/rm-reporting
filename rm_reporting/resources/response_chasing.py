import logging
import io
import csv

from datetime import datetime
from flask import make_response
from flask_restx import Resource
from sqlalchemy.exc import SQLAlchemyError
from openpyxl import Workbook
from structlog import wrap_logger

from rm_reporting import response_chasing_api, app

from sqlalchemy import text

logger = wrap_logger(logging.getLogger(__name__))


@response_chasing_api.route('/download-report/<collection_exercise_id>/<survey_id>')
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
            "H1": "Respondent Account Status"
        }

        for cell, header in headers.items():
            ws[cell] = header
            ws.column_dimensions[cell[0]].width = len(header)

        engine = app.db.engine

        collex_status = "WITH " \
                        "business_details AS " \
                        "(SELECT DISTINCT " \
                        "ba.collection_exercise As collection_exercise_uuid, " \
                        "b.business_ref AS sampleunitref, " \
                        "ba.business_id AS business_party_uuid, " \
                        "ba.attributes->> 'name' AS business_name " \
                        "FROM " \
                        "partysvc.business_attributes ba, partysvc.business b " \
                        "WHERE " \
                        f"ba.collection_exercise = '{collection_exercise_id}' and " \
                        "ba.business_id = b.party_uuid), " \
                        "case_details AS " \
                        "(SELECT " \
                        "cg.collectionexerciseid AS collection_exercise_uuid, cg.sampleunitref, " \
                        "cg.status AS case_status " \
                        "FROM casesvc.casegroup cg " \
                        f"WHERE cg.collectionexerciseid = '{collection_exercise_id}' " \
                        "ORDER BY cg.status, cg.sampleunitref), " \
                        "respondent_details AS " \
                        "(SELECT e.survey_id AS survey_uuid, e.business_id AS business_party_uuid, " \
                        "e.status AS enrolment_status, " \
                        "CONCAT(r.first_name, ' ', r.last_name) AS respondent_name, r.telephone, " \
                        "r.email_address, r.status AS respondent_status " \
                        "FROM partysvc.enrolment e " \
                        "LEFT JOIN partysvc.respondent r ON e.respondent_id = r.id " \
                        "WHERE " \
                        f"e.survey_id = '{survey_id}') " \
                        "SELECT cd.case_status, bd.sampleunitref, bd.business_name, " \
                        "rd.enrolment_status, rd.respondent_name, " \
                        "rd.telephone, rd.email_address, rd.respondent_status " \
                        "FROM " \
                        "case_details cd " \
                        "LEFT JOIN business_details bd ON bd.sampleunitref=cd.sampleunitref " \
                        "LEFT JOIN respondent_details rd ON bd.business_party_uuid = rd.business_party_uuid " \
                        "ORDER BY sampleunitref, case_status;"
        try:
            collex_details = engine.execute(text(collex_status))
        except SQLAlchemyError:
            logger.exception("SQL Alchemy query failed")
            raise

        for row in collex_details:
            business = []
            business.append(row[0])
            business.append(row[1])
            business.append(row[2])
            business.append(row[3])
            business.append(row[4])
            business.append(row[5])
            business.append(row[6])
            business.append(row[7])
            ws.append(business)

        wb.save(output)
        wb.close()

        response = make_response(output.getvalue(), 200)
        response.headers["Content-Disposition"] = f"attachment; filename=response_chasing_{collection_exercise_id}.xlsx"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response


@response_chasing_api.route('/download-social-mi/<collection_exercise_id>')
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
            "Country"
        ]

        datestr = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        engine = app.db.engine

        case_status = text("SELECT cg.sampleunitref, cg.status, "
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
                           "WHERE c.sampleunittype = 'H' AND cg.collectionexerciseid = :collection_exercise_id")

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
        response.headers["Content-Disposition"] = f"attachment; filename=social_mi_report_{collection_exercise_id}" \
                                                  f"_{datestr}.csv"
        response.headers["Content-type"] = "text/csv"
        return response
