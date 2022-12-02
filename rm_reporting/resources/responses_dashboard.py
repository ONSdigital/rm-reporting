import logging
from datetime import datetime

from flask import jsonify
from flask_restx import Resource, abort
from structlog import wrap_logger

from rm_reporting import response_dashboard_api
from rm_reporting.common.validators import parse_uuid
from rm_reporting.controllers import case_controller, party_controller
from rm_reporting.exceptions import NoDataException

logger = wrap_logger(logging.getLogger(__name__))


def get_report_figures(survey_id, collection_exercise_id):
    logger.info("Getting report figures", survey_id=survey_id, collection_exercise_id=collection_exercise_id)
    result_dict = {}

    # Get all cases for a collection exercise
    case_result = case_controller.get_exercise_completion_stats(collection_exercise_id)
    if getattr(case_result[0], "Sample Size") == 0:
        raise NoDataException
    result_dict["sampleSize"] = getattr(case_result[0], "Sample Size")
    result_dict["inProgress"] = getattr(case_result[0], "In Progress")
    result_dict["notStarted"] = getattr(case_result[0], "Not Started")
    result_dict["completed"] = getattr(case_result[0], "Complete")

    # Get all the party_ids for all the businesses that are part of the collection exercise
    business_ids = case_controller.get_all_business_ids_for_collection_exercise(collection_exercise_id)

    # Get all the enrolments for the survey the exercise is for but only for the businesses
    enrolment_details_result = party_controller.get_enrolment_data(survey_id, business_ids)

    pending = 0
    enabled = 0
    for row in enrolment_details_result:
        if getattr(row, "status") == "ENABLED":
            enabled += 1
        if getattr(row, "status") == "PENDING":
            pending += 1

    result_dict["accountsPending"] = pending
    result_dict["accountsEnrolled"] = enabled

    logger.info("Successfully got report figures", survey_id=survey_id, collection_exercise_id=collection_exercise_id)
    return result_dict


@response_dashboard_api.route("/survey/<survey_id>/collection-exercise/<collection_exercise_id>")
class ResponseDashboard(Resource):
    @staticmethod
    def get(survey_id, collection_exercise_id):
        if not parse_uuid(survey_id):
            logger.debug("Responses dashboard endpoint received malformed survey ID", survey_id=survey_id)
            abort(400, "Malformed survey ID")

        if not parse_uuid(collection_exercise_id):
            logger.debug(
                "Responses dashboard endpoint received malformed collection exercise ID",
                collection_exercise_id=collection_exercise_id,
            )
            abort(400, "Malformed collection exercise ID")

        try:
            report = get_report_figures(survey_id, collection_exercise_id)
            response = {
                "metadata": {"timeUpdated": datetime.now().timestamp(), "collectionExerciseId": collection_exercise_id},
                "report": report,
            }
            return jsonify(response)
        except NoDataException:
            abort(404, "Invalid collection exercise or survey ID")
