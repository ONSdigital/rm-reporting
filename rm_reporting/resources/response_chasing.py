import logging
import io

from flask import make_response
from flask_restplus import Resource
from openpyxl import Workbook
from structlog import wrap_logger

from rm_reporting import response_chasing_api

logger = wrap_logger(logging.getLogger(__name__))


@response_chasing_api.route('/download-report/<collection_exercise_id>')
class ResponseChasingDownload(Resource):

    @staticmethod
    def get(collection_exercise_id):

        mock_data = [
            ['Live', 4990000001, "company_name", 'Enabled', 'first_name last_name', '0987654321',
             'example@example.com', 'active'],
            ['Live', 4990000002, "company_name", 'Enabled', 'first_name last_name', '0987654321',
             'example@example.com', 'active'],
            ['Live', 4990000003, "company_name", 'Enabled', 'first_name last_name', '0987654321',
             'example@example.com', 'active'],
            ['Live', 4990000004, "company_name", 'Enabled', 'first_name last_name', '0987654321',
             'example@example.com', 'active']
        ]

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

        # Add data
        for row in mock_data:
            ws.append(row)

        wb.save(output)
        wb.close()

        response = make_response(output.getvalue(), 200)
        response.headers["Content-Disposition"] = f"attachment; filename=response_chasing_{collection_exercise_id}.xlsx"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response
