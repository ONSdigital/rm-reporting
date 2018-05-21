import logging
import io

from flask import make_response
from flask_restplus import Resource
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

        # report_query = \
        #     "SELECT bd.status, bd.sampleunitref, bd.name, e.status, r.status, " \
        #     "CONCAT(r.first_name, ' ', r.last_name), r.telephone, r.email_address " \
        #     "FROM ( " \
        #     "SELECT cg.sampleunitref, cg.status, ba.attributes->> 'name' as name, b.party_uuid as business_uuid " \
        #     "from partysvc.business_attributes ba " \
        #     "JOIN casesvc.casegroup cg ON ba.collection_exercise = cast (cg.collectionexerciseid as text) " \
        #     "LEFT JOIN partysvc.business b ON b.business_ref = cg.sampleunitref " \
        #     f"WHERE cg.collectionexerciseid = '{collection_exercise_id}' " \
        #     "AND ba.business_id = b.party_uuid ) AS bd " \
        #     "LEFT JOIN partysvc.enrolment e ON bd.business_uuid = e.business_id " \
        #     f"AND e.survey_id = '{survey_id}' " \
        #     "LEFT JOIN partysvc.respondent r ON e.respondent_id = r.id " \
        #     "ORDER BY bd.sampleunitref "

        collex_status = "WITH business_data AS " \
                        "(SELECT cg.sampleunitref, cg.status, ba.attributes->> 'name' AS name, " \
                        "b.party_uuid AS business_uuid FROM partysvc.business_attributes ba, casesvc.casegroup cg " \
                        "LEFT JOIN partysvc.business b ON b.business_ref = cg.sampleunitref " \
                        f"WHERE cg.collectionexerciseid = '{collection_exercise_id}' AND " \
                        f"ba.collection_exercise = '{collection_exercise_id}' AND " \
                        "ba.business_id = b.party_uuid " \
                        "ORDER BY cg.status, cg.sampleunitref) " \
                        "SELECT bd.status, bd.sampleunitref, bd.name, e.status,  " \
                        "CONCAT(r.first_name, ' ', r.last_name), r.telephone, r.email_address, r.status FROM business_data bd " \
                        "LEFT JOIN partysvc.enrolment e " \
                        f"ON e.business_id = bd.business_uuid AND e.survey_id = '{survey_id}' " \
                        "LEFT JOIN partysvc.respondent r ON e.respondent_id = r.id " \
                        "ORDER BY bd.sampleunitref;"

        try:
          collex_details = engine.execute(text(collex_status))
        except SQLAlchemyError:
            logger.exception("SQL Alchemy query failed")

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
