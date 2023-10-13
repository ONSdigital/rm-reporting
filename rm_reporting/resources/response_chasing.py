import logging

from flask import make_response
from flask_restx import Resource, abort
from structlog import wrap_logger

from rm_reporting import response_chasing_api
from rm_reporting.common.validators import parse_uuid
from rm_reporting.controllers.response_chasing_controller import (
    create_csv_report,
    create_xslx_report,
)

logger = wrap_logger(logging.getLogger(__name__))


@response_chasing_api.route("/download-report/<document_type>/<collection_exercise_id>/<survey_id>")
class ResponseChasingDownload(Resource):
    @staticmethod
    def get(document_type, collection_exercise_id, survey_id):
        if not parse_uuid(survey_id):
            logger.info("Responses dashboard endpoint received malformed survey ID", survey_id=survey_id)
            abort(400, "Malformed survey ID")

        if not parse_uuid(collection_exercise_id):
            logger.info(
                "Responses dashboard endpoint received malformed collection exercise ID",
                collection_exercise_id=collection_exercise_id,
            )
            abort(400, "Malformed collection exercise ID")

        if document_type == "xslx":
            response = make_response(create_xslx_report(collection_exercise_id, survey_id).getvalue(), 200)
            response.headers[
                "Content-Disposition"
            ] = f"attachment; filename=response_chasing_{collection_exercise_id}.xlsx"
            response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif document_type == "csv":
            response = make_response(create_csv_report(collection_exercise_id, survey_id).getvalue())
            response.headers[
                "Content-Disposition"
            ] = f"attachment; filename=response_chasing_{collection_exercise_id}.csv"
            response.headers["Content-type"] = "text/csv"
        else:
            abort(400, "Document type not supported")

        return response
