import logging
from datetime import datetime

from flask import Response, json
from flask_restplus import Resource, abort
from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app, response_dashboard_api
from rm_reporting.common.validators import parse_uuid
from rm_reporting.exceptions import NoDataException

logger = wrap_logger(logging.getLogger(__name__))


def get_report_figures(survey_id, collection_exercise_id, engine):
    case_query = text('WITH cases AS'
                      '(SELECT cg.status, cg.sampleunitref, c.sampleunit_id '
                      'FROM casesvc.casegroup cg '
                      'INNER JOIN casesvc."case" c ON cg.casegrouppk = c.casegroupfk '
                      'WHERE cg.collectionexerciseid = :collection_exercise_id '
                      'AND cg.sampleunitref NOT LIKE \'1%\'), '
                      'survey_enrolments AS '
                      '(SELECT e.business_id, e.status, ba.attributes '
                      'FROM partysvc.enrolment e '
                      'INNER JOIN partysvc.business_attributes ba ON e.business_id = ba.business_id '
                      'WHERE survey_id = :survey_id '
                      'AND collection_exercise = :collection_exercise_id) '
                      'SELECT COUNT(*) '
                      'AS "Sample Size", '
                      'COUNT(CASE WHEN cases.status = \'NOTSTARTED\' THEN 1 ELSE NULL END) '
                      'AS "Not Started", '
                      'COUNT(CASE WHEN cases.status = \'INPROGRESS\' THEN 1 ELSE NULL END) '
                      'AS "In Progress", '
                      'COUNT(CASE WHEN cases.status = \'COMPLETE\' THEN 1 ELSE NULL END) '
                      'AS "Complete", '
                      'COUNT(CASE WHEN survey_enrolments.status = \'ENABLED\' THEN 1 ELSE NULL END) '
                      'AS "Total Enrolled", '
                      'COUNT(CASE WHEN survey_enrolments.status = \'PENDING\' THEN 1 ELSE NULL END) '
                      'AS "Total Pending" '
                      'FROM cases '
                      'LEFT JOIN survey_enrolments '
                      'ON survey_enrolments.attributes ->> \'sampleUnitId\' = cases.sampleunit_id::text')

    report_figures = engine.execute(case_query,
                                    survey_id=survey_id,
                                    collection_exercise_id=collection_exercise_id).first()

    if any(column is None for column in report_figures.values()):
        raise NoDataException

    return report_figures


def get_report(survey_id, collection_exercise_id, engine):
    report_figures = get_report_figures(survey_id, collection_exercise_id, engine)

    return {
        'inProgress': report_figures['In Progress'],
        'accountsPending': report_figures['Total Pending'],
        'accountsEnrolled': report_figures['Total Enrolled'],
        'notStarted': report_figures['Not Started'],
        'completed': report_figures['Complete'],
        'sampleSize': report_figures['Sample Size']
    }


@response_dashboard_api.route('/survey/<survey_id>/collection-exercise/<collection_exercise_id>')
class ResponseDashboard(Resource):

    @staticmethod
    def get(survey_id, collection_exercise_id):

        engine = app.db.engine

        parsed_survey_id = parse_uuid(survey_id)
        if not parsed_survey_id:
            logger.debug('Responses dashboard endpoint received malformed survey ID',
                         invalid_survey_id=survey_id)
            abort(400, 'Malformed survey ID')

        parsed_collection_exercise_id = parse_uuid(collection_exercise_id)
        if not parsed_collection_exercise_id:
            logger.debug('Responses dashboard endpoint received malformed collection exercise ID',
                         invalid_collection_exercise_id=collection_exercise_id)
            abort(400, 'Malformed collection exercise ID')

        try:
            report = get_report(parsed_survey_id, parsed_collection_exercise_id, engine)
        except NoDataException:
            abort(404, 'Invalid collection exercise or survey ID')

        response = {
            'metadata': {
                'timeUpdated': datetime.now().timestamp(),
                'collectionExerciseId': collection_exercise_id
            },
            'report': report
        }

        return Response(json.dumps(response), content_type='application/json')
