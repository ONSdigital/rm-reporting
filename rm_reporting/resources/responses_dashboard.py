import logging
from datetime import datetime

from flask import Response, json
from flask_restx import Resource, abort
from structlog import wrap_logger

from rm_reporting import response_dashboard_api
from rm_reporting.common.validators import parse_uuid
from rm_reporting.controllers import case_controller, party_controller
from rm_reporting.exceptions import NoDataException

logger = wrap_logger(logging.getLogger(__name__))


def get_report_figures(survey_id, collection_exercise_id):
    logger.info("Getting report figures", survey_id=survey_id, collection_exercise_id=collection_exercise_id)
    result_dict = {
        "inProgress": 0,
        "accountsPending": 0,
        "accountsEnrolled": 0,
        "notStarted": 0,
        "completed": 0,
        "sampleSize": 0,
    }

    # Get all cases for a collection exercise
    case_result = case_controller.get_exercise_completion_stats(collection_exercise_id)

    result_dict["sampleSize"] = getattr(case_result[0], "Sample Size")
    result_dict["inProgress"] = getattr(case_result[0], "In Progress")
    result_dict["notStarted"] = getattr(case_result[0], "Not Started")
    result_dict["completed"] = getattr(case_result[0], "Complete")
    # Should we filter out the 1111* ones?  Maybe we get them in the initial search then filter them out and do some
    # logging saying 'filtered out x number of test reporting units to make it obvious'

    # Get all the party_ids for all the businesses that are part of the collection exercise
    business_ids_string = case_controller.get_all_business_ids_for_collection_exercise(collection_exercise_id)

    # Get all the enrolments for the survey the exercise is for but only for the businesses
    enrolment_details_result = party_controller.get_dashboard_enrolment_details(survey_id, business_ids_string)

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

        try:
            report = get_report_figures(survey_id, collection_exercise_id)
        except NoDataException:
            abort(404, "Invalid collection exercise or survey ID")

        response = {
            "metadata": {"timeUpdated": datetime.now().timestamp(), "collectionExerciseId": collection_exercise_id},
            "report": report,
        }

        return Response(json.dumps(response), content_type="application/json")
