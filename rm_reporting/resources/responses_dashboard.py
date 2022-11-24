import logging
from datetime import datetime

from flask import Response, json
from flask_restx import Resource, abort
from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app, response_dashboard_api
from rm_reporting.common.validators import parse_uuid
from rm_reporting.exceptions import NoDataException

logger = wrap_logger(logging.getLogger(__name__))


def get_report_figures(survey_id, collection_exercise_id):
    result_dict = {
        "inProgress": 0,
        "accountsPending": 0,
        "accountsEnrolled": 0,
        "notStarted": 0,
        "completed": 0,
        "sampleSize": 0,
    }
    case_engine = app.case_db.engine
    party_engine = app.party_db.engine
    # Get all cases for a collection exercise
    case_query = text(
        'SELECT COUNT(*) AS "Sample Size", '
        "COUNT(CASE WHEN status = 'NOTSTARTED' THEN 1 ELSE NULL END) AS \"Not Started\", "
        "COUNT(CASE WHEN status = 'INPROGRESS' THEN 1 ELSE NULL END) AS \"In Progress\", "
        "COUNT(CASE WHEN status = 'COMPLETE' THEN 1 ELSE NULL END) AS \"Complete\" "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id "
        "AND sample_unit_ref NOT LIKE '1111%'"
    )

    case_result = case_engine.execute(
        case_query, survey_id=survey_id, collection_exercise_id=collection_exercise_id
    ).all()

    result_dict["sampleSize"] = getattr(case_result[0], "Sample Size")
    result_dict["inProgress"] = getattr(case_result[0], "In Progress")
    result_dict["notStarted"] = getattr(case_result[0], "Not Started")
    result_dict["completed"] = getattr(case_result[0], "Complete")
    logger.info(case_result)
    # Should we filter out the 1111* ones?  Maybe we get them in the initial search then filter them out and do some
    # logging saying 'filtered out x number of test reporting units to make it obvious'

    # Get all the party_ids for all the businesses that are part of the collection exercise
    case_business_ids_query = text(
        "SELECT party_id "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id and "
        "sample_unit_ref NOT LIKE '1111%'"
    )

    case_business_ids_result = case_engine.execute(
        case_business_ids_query, collection_exercise_id=collection_exercise_id
    )

    # TODO get the values in a list in a tidier way...
    business_id_result = case_business_ids_result.all()
    business_ids_list = []
    business_ids_string = ""
    for row in business_id_result:
        business_ids_list.append(str(getattr(row, "party_id")))
        business_ids_string += f"'{str(getattr(row, 'party_id'))}', "

    # slice off the tailing ', '
    business_ids_string = business_ids_string[:-2]

    # Get all the enrolments for the survey the exercise is for but only for the businesses
    enrolment_details_query_text = (
        f"SELECT * "
        f"FROM partysvc.enrolment e "
        f"WHERE "
        f"e.survey_id = :survey_id AND e.business_id IN ({business_ids_string}) "
    )

    enrolment_details_query = text(enrolment_details_query_text)
    enrolment_details_result = party_engine.execute(enrolment_details_query, survey_id=survey_id)
    blah = enrolment_details_result.all()

    pending = 0
    enabled = 0
    for row in blah:
        if getattr(row, "status") == "ENABLED":
            enabled += 1
        if getattr(row, "status") == "PENDING":
            pending += 1

    result_dict["accountsPending"] = pending
    result_dict["accountsEnrolled"] = enabled

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
