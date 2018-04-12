import logging
import io

from flask import make_response
from flask_restplus import Resource
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

        collex_status = "with business_data as " \
                        "(select cg.sampleunitref, cg.status, ba.attributes->> 'name' as name, " \
                        "b.party_uuid as business_uuid from partysvc.business_attributes ba, casesvc.casegroup cg " \
                        "left join partysvc.business b on b.business_ref = cg.sampleunitref " \
                        f"where cg.collectionexerciseid = '{collection_exercise_id}' and " \
                        f"ba.collection_exercise = '{collection_exercise_id}' and " \
                        "ba.business_id = b.party_uuid " \
                        "order by cg.status, cg.sampleunitref) " \
                        "select bd.status, bd.sampleunitref, bd.name, e.status, r.status, " \
                        "CONCAT(r.first_name, ' ', r.last_name), r.telephone, r.email_address from business_data bd " \
                        "left join partysvc.enrolment e " \
                        f"on e.business_id = bd.business_uuid and e.survey_id = '{survey_id}' " \
                        "left join partysvc.respondent r on e.respondent_id = r.id " \
                        "order by bd.sampleunitref;"

        collex_details = engine.execute(text(collex_status))

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
