from datetime import datetime
import logging

from flask import json, Response
from flask_restplus import Resource, abort
from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app, response_dashboard_api
from rm_reporting.common.validators import parse_uuid
from rm_reporting.exceptions import NoDataException

logger = wrap_logger(logging.getLogger(__name__))


def get_case_report_figures(collection_exercise_id, engine):
    case_query = text('SELECT COUNT(id) AS "Sample Size", '
                      'COUNT(CASE '
                      'WHEN status = \'NOTSTARTED\' THEN 1 '
                      'ELSE NULL '
                      'END) AS "Not Started", '
                      'COUNT(CASE '
                      'WHEN status = \'INPROGRESS\' THEN 1 '
                      'ELSE NULL '
                      'END) AS "In Progress", '
                      'COUNT(CASE '
                      'WHEN status = \'COMPLETE\' THEN 1 '
                      'ELSE NULL '
                      'END) AS "Complete" '
                      'FROM casesvc.casegroup '
                      'WHERE collectionexerciseid = :collection_exercise_id')

    return engine.execute(case_query, collection_exercise_id=collection_exercise_id).first()


def get_party_report(collection_exercise_id, engine):
    party_query = text('SELECT COUNT(CASE enrolment.status WHEN \'ENABLED\' THEN 1 ELSE NULL END) AS "Total Enrolled", '
                       'COUNT(CASE enrolment.status WHEN \'PENDING\' THEN 1 ELSE NULL END) AS "Total Pending" '
                       'FROM partysvc.enrolment enrolment '
                       'INNER JOIN partysvc.business_attributes business_attributes '
                       'ON business_attributes.business_id = enrolment.business_id '
                       'WHERE business_attributes.collection_exercise = :collection_exercise_id')

    return engine.execute(party_query, collection_exercise_id=collection_exercise_id).first()


def get_report_figures(collection_exercise_id, engine):
    case_report_figures = get_case_report_figures(collection_exercise_id, engine)
    party_report_figures = get_party_report(collection_exercise_id, engine)

    if any(column is None for column in list(case_report_figures.values()) + list(party_report_figures.values())):
        raise NoDataException

    return case_report_figures, party_report_figures


def get_seft_report(collection_exercise_id, engine):
    case_report_figures, party_report_figures = get_report_figures(collection_exercise_id, engine)

    total_downloaded = case_report_figures['In Progress'] + case_report_figures['Complete']

    return {
        'sampleSize': case_report_figures['Sample Size'],
        'accountsPending': party_report_figures['Total Pending'],
        'accountsEnrolled': party_report_figures['Total Enrolled'],
        'downloads': total_downloaded,
        'uploads': case_report_figures['Complete']
    }


def get_eq_report(collection_exercise_id, engine):
    case_report_figures, party_report_figures = get_report_figures(collection_exercise_id, engine)

    return {
        'inProgress': case_report_figures['In Progress'],
        'accountsPending': party_report_figures['Total Pending'],
        'accountsEnrolled': party_report_figures['Total Enrolled'],
        'notStarted': case_report_figures['Not Started'],
        'completed': case_report_figures['Complete'],
        'sampleSize': case_report_figures['Sample Size']
    }


def get_report(collection_instrument_type, collection_exercise_id, engine):
    report_for_type = {
        'SEFT': get_seft_report,
        'EQ': get_eq_report
    }
    return report_for_type[collection_instrument_type](collection_exercise_id, engine)


@response_dashboard_api.route('/<collection_instrument_type>/collection-exercise/<collection_exercise_id>')
class ResponseDashboard(Resource):

    @staticmethod
    def get(collection_instrument_type, collection_exercise_id):

        engine = app.db.engine

        collection_exercise_id = parse_uuid(collection_exercise_id)
        if not collection_exercise_id:
            logger.debug('Malformed collection exercise ID', invalid_id=collection_exercise_id)
            abort(400, 'Malformed collection exercise ID')

        try:
            report = get_report(collection_instrument_type.upper(), collection_exercise_id, engine)
        except KeyError:
            abort(404, 'Invalid collection instrument type')
        except NoDataException:
            abort(404, 'Invalid collection exercise ID')

        response = {
            'metadata': {
                'timeUpdated': datetime.now().timestamp(),
                'collectionExerciseId': collection_exercise_id
            },
            'report': report
        }

        return Response(json.dumps(response), content_type='application/json')
