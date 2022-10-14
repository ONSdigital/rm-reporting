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


def get_report_figures(survey_id, collection_exercise_id, engine):
    result_dict = {
        "inProgress": "0",
        "accountsPending": "0",
        "accountsEnrolled": "0",
        "notStarted": "0",
        "completed": "0",
        "sampleSize": "0",
    }
    case_engine = app.db.get_engine(app, "case_db")
    party_engine = app.db.engine(app, "survey_db")
    # Get all cases for a collection exercise
    case_query = text(
        "WITH "
        "case_figures AS "
        '(SELECT COUNT(*) AS "Sample Size", '
        "COUNT(CASE WHEN status = 'NOTSTARTED' THEN 1 ELSE NULL END) AS \"Not Started\", "
        "COUNT(CASE WHEN status = 'INPROGRESS' THEN 1 ELSE NULL END) AS \"In Progress\", "
        "COUNT(CASE WHEN status = 'COMPLETE' THEN 1 ELSE NULL END) AS \"Complete\" "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id "
        "AND sample_unit_ref NOT LIKE '1111%'), "
    )

    case_result = case_engine.execute(
        case_query, survey_id=survey_id, collection_exercise_id=collection_exercise_id
    ).all()

    result_dict["sampleSize"] = len(case_result)
    logger.info(case_result)
    # Should we filter out the 1111* ones?  Maybe we get them in the initial search then filter them out and do some
    # logging saying 'filtered out x number of test reporting units to make it obvious'

    # Need to get all business parties related to the cases

    party_query = text(
        "business_details AS "
        "(SELECT DISTINCT "
        "b.business_ref AS sample_unit_ref, "
        "ba.business_id AS business_party_uuid "
        "FROM "
        "partysvc.business_attributes ba, partysvc.business b "
        "WHERE "
        "ba.collection_exercise = :collection_exercise_id and "
        "ba.business_id = b.party_uuid and "
        "b.business_ref NOT LIKE '1111%'), "
    )
    party_result = party_engine.execute(party_query, survey_id=survey_id, collection_exercise_id=collection_exercise_id)
    logger.info(party_result)

    extra_query = text(
        "case_details AS "
        "(select sample_unit_ref "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id and "
        "sample_unit_ref NOT LIKE '1111%'), "
        "respondent_details AS "
        "(SELECT e.business_id AS business_party_uuid, "
        "e.status AS enrolment_status "
        "FROM partysvc.enrolment e "
        "LEFT JOIN partysvc.respondent r ON e.respondent_id = r.id "
        "WHERE "
        "e.survey_id = :survey_id), "
        "survey_enrolments AS "
        "(SELECT "
        "rd.enrolment_status as status "
        "FROM "
        "case_details cd "
        "LEFT JOIN business_details bd ON bd.sample_unit_ref=cd.sample_unit_ref "
        "LEFT JOIN respondent_details rd ON bd.business_party_uuid = rd.business_party_uuid), "
        "party_figures AS "
        "(SELECT COUNT(CASE WHEN survey_enrolments.status = 'ENABLED' THEN 1 ELSE NULL END) AS \"Total Enrolled\", "
        "COUNT(CASE WHEN survey_enrolments.status = 'PENDING' THEN 1 ELSE NULL END) AS \"Total Pending\" "
        "FROM survey_enrolments) "
        "SELECT * FROM case_figures, party_figures"
    )
    logger.info(extra_query)

    logger.info(party_query)
    report_figures = engine.execute(
        case_query, survey_id=survey_id, collection_exercise_id=collection_exercise_id
    ).first()

    if any(column is None for column in report_figures.values()):
        raise NoDataException

    return report_figures


def get_report(survey_id, collection_exercise_id, engine):
    report_figures = get_report_figures(survey_id, collection_exercise_id, engine)

    return {
        "inProgress": report_figures["In Progress"],
        "accountsPending": report_figures["Total Pending"],
        "accountsEnrolled": report_figures["Total Enrolled"],
        "notStarted": report_figures["Not Started"],
        "completed": report_figures["Complete"],
        "sampleSize": report_figures["Sample Size"],
    }


@response_dashboard_api.route("/survey/<survey_id>/collection-exercise/<collection_exercise_id>")
class ResponseDashboard(Resource):
    @staticmethod
    def get(survey_id, collection_exercise_id):

        engine = app.db.engine

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
            report = get_report(parsed_survey_id, parsed_collection_exercise_id, engine)
        except NoDataException:
            abort(404, "Invalid collection exercise or survey ID")

        response = {
            "metadata": {"timeUpdated": datetime.now().timestamp(), "collectionExerciseId": collection_exercise_id},
            "report": report,
        }

        return Response(json.dumps(response), content_type="application/json")
