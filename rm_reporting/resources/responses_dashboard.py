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


def get_seft_report(collection_exercise_id, engine):
    report_query = text('SELECT '
                        'COUNT(DISTINCT(sample_unit_ref)) "Sample Size", '
                        'CAST(SUM(enrolled) as INTEGER) "Total Enrolled", '
                        'SUM(downloaded) "Total Downloaded", '
                        'SUM(uploaded) "Total Uploaded" '
                        'FROM '
                        '(SELECT '
                        'events.sampleunitref sample_unit_ref, '
                        'events.sampleunittype, '
                        'events.caseref case_ref, '
                        'events.respondent_enrolled enrolled, '
                        'events.collection_instrument_downloaded_ind downloaded, '
                        'events.successful_response_upload_ind uploaded '
                        'FROM '
                        '(SELECT '
                        'cg.sampleunitref, '
                        'c.sampleunittype, '
                        'c.caseref, '
                        'SUM(CASE WHEN ce.categoryFK = \'RESPONDENT_ENROLED\' '
                        'THEN 1 ELSE  0 END) respondent_enrolled, '
                        'MAX(CASE WHEN ce.categoryFK = \'COLLECTION_INSTRUMENT_DOWNLOADED\' '
                        'THEN 1 ELSE  0 END) collection_instrument_downloaded_ind, '
                        'MAX(CASE WHEN ce.categoryFK = \'SUCCESSFUL_RESPONSE_UPLOAD\' '
                        'THEN 1 ELSE  0 END) successful_response_upload_ind '
                        'FROM casesvc.caseevent ce '
                        'RIGHT OUTER JOIN casesvc.case c ON c.casePK = ce.caseFK '
                        'INNER JOIN casesvc.casegroup cg ON c.casegroupFK = cg.casegroupPK '
                        'GROUP BY cg.sampleunitref, c.sampleunittype, c.caseref, c.casePK) events) as data_records '
                        'WHERE case_ref IN '
                        '(SELECT c.caseref FROM casesvc.case c '
                        'WHERE c.casegroupid IN '
                        '(SELECT cg.id "Group ID" FROM casesvc.casegroup cg '
                        'WHERE cg.collectionexerciseid = :collection_exercise_id))')

    report_details = engine.execute(report_query, collection_exercise_id=collection_exercise_id).first()

    if any(column is None for column in report_details):
        raise NoDataException

    return {
        'sampleSize': report_details['Sample Size'],
        'accountsEnrolled': report_details['Total Enrolled'],
        'downloads': report_details['Total Downloaded'],
        'uploads': report_details['Total Uploaded']
    }


def get_eq_report(collection_exercise_id, engine):
    report_query = text('SELECT '
                        'COUNT(DISTINCT(sample_unit_ref)) "Sample Size", '
                        'CAST(SUM(account_created) as INTEGER) "Total Accounts Created", '
                        'CAST(SUM(enrolled) as INTEGER) "Total Enrolled", '
                        'SUM(eq_launched) "Total Launched", '
                        'SUM(completed) "Total Completed" '
                        'FROM '
                        '(SELECT '
                        'events.sampleunitref sample_unit_ref, '
                        'events.sampleunittype, '
                        'events.caseref case_ref, '
                        'events.respondent_enrolled enrolled, '
                        'events.respondent_account_created account_created, '
                        'events.eq_launch eq_launched, '
                        'events.offline_response_processed completed '
                        'FROM '
                        '(SELECT '
                        'cg.sampleunitref, '
                        'c.sampleunittype, '
                        'c.caseref, '
                        'SUM(CASE WHEN ce.categoryFK = \'RESPONDENT_ACCOUNT_CREATED\' '
                        'THEN 1 ELSE  0 END) respondent_account_created, '
                        'SUM(CASE WHEN ce.categoryFK = \'RESPONDENT_ENROLED\' '
                        'THEN 1 ELSE  0 END) respondent_enrolled, '
                        'MAX(CASE WHEN ce.categoryFK = \'EQ_LAUNCH\' '
                        'THEN 1 ELSE  0 END) eq_launch, '
                        'MAX(CASE WHEN ce.categoryFK = \'OFFLINE_RESPONSE_PROCESSED\' '
                        'THEN 1 ELSE  0 END) offline_response_processed '
                        'FROM casesvc.caseevent ce '
                        'RIGHT OUTER JOIN casesvc.case c ON c.casePK = ce.caseFK '
                        'INNER JOIN casesvc.casegroup cg ON c.casegroupFK = cg.casegroupPK '
                        'GROUP BY cg.sampleunitref, c.sampleunittype, c.caseref, c.casePK) events) as data_records '
                        'WHERE case_ref IN '
                        '(SELECT c.caseref FROM casesvc.case c '
                        'WHERE c.casegroupid IN '
                        '(SELECT cg.id "Group ID" FROM casesvc.casegroup cg '
                        'WHERE cg.collectionexerciseid = :collection_exercise_id))')

    report_details = engine.execute(report_query, collection_exercise_id=collection_exercise_id).first()

    if any(column is None for column in report_details):
        raise NoDataException

    return {
        'inProgress': report_details['Total Launched'] - report_details['Total Completed'],
        'accountsCreated': report_details['Total Accounts Created'],
        'accountsEnrolled': report_details['Total Enrolled'],
        'notStarted': report_details['Sample Size'] - report_details['Total Launched'],
        'completed': report_details['Total Completed'],
        'sampleSize': report_details['Sample Size']
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
