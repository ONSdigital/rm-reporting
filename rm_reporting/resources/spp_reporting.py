import logging

import logging
from datetime import datetime

from flask import Response, json, make_response
from flask_restx import Resource, abort
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from structlog import wrap_logger

from rm_reporting import app, response_dashboard_api, api
from rm_reporting.common.gcs_gateway import GoogleCloudStorageGateway
from rm_reporting.common.s3_gateway import SimpleStorageServiceGateway
from rm_reporting.common.validators import parse_uuid
from rm_reporting.exceptions import NoDataException
from flask_restx import Resource
from structlog import wrap_logger

from rm_reporting import spp_reporting_api

logger = wrap_logger(logging.getLogger(__name__))


def get_respondents(business_party_id, survey_id, engine):
    respondents = []
    if business_party_id is None:
        return respondents
    respondent_details = get_respondent_details(business_party_id, engine, survey_id)
    for row in respondent_details:
        respondent = {
            'id': row[0],
            'name': row[1],
            'telephone': row[2],
            'email': row[3],
            'accountStatus': row[4],
        }
        respondents.append(respondent)
    return respondents


def get_respondent_details(business_party_id, engine, survey_id):
    respondent_query = "SELECT r.id, " \
                       "CONCAT(r.first_name, ' ', r.last_name) AS respondent_name, " \
                       "r.telephone,  " \
                       "r.email_address,  " \
                       "r.status " \
                       "FROM  " \
                       "partysvc.enrolment e " \
                       "LEFT JOIN partysvc.respondent r ON e.respondent_id = r.id " \
                       "WHERE " \
                       f"e.survey_id = '{survey_id}'  " \
                       "AND " \
                       f"e.business_id = '{business_party_id}'; "
    try:
        respondent_details = engine.execute(text(respondent_query))
    except SQLAlchemyError:
        logger.exception("SQL Alchemy query failed")
        raise
    return respondent_details


def get_collection_exercise_and_survey(engine):
    collex_query = text(
        'SELECT c.survey_uuid AS surveyId, c.id as collectionExerciseId '
        'FROM collectionexercise.collectionexercise c '
        'where survey_uuid = (select id from survey.survey where shortname = \'QBS\') '
        'AND statefk = \'LIVE\''
    )

    collex_survey = engine.execute(collex_query).first()

    if any(column is None for column in collex_survey.values()):
        raise NoDataException
    return collex_survey


def populate_json_record(
        survey_id,
        case_details,
        survey_response_status,
        reporting_unit_respondent_information,
        engine):

    collection_cases = []
    reporting_units = []
    for row in case_details:
        respondents = get_respondents(row[5], survey_id, engine)
        collection_case = {
            'id': row[0],
            'reportingUnitRef': row[1],
            'reportingUnitName': row[2],
            'enrolmentStatus': row[3],
            'surveyReturnStatus': row[4],
            'respondents': respondents
        }
        if row[5] is not None:
            reporting_unit = {
                'id': row[5],
                'respondents': respondents
            }
            reporting_units.append(reporting_unit)
        collection_cases.append(collection_case)
    survey_response_status['collectionCases'] = collection_cases
    reporting_unit_respondent_information['reportingUnitRespondents'] = reporting_units


def get_case_details(survey_id, collection_exercise_id, engine):
    case_query = "WITH business_details AS " \
                 "(SELECT ba.collection_exercise As collection_exercise_uuid, " \
                 "b.business_ref AS sampleunitref,  " \
                 "ba.business_id AS business_party_uuid, " \
                 "ba.attributes->> 'name' AS business_name " \
                 "FROM " \
                 "partysvc.business_attributes ba, partysvc.business b " \
                 "WHERE " \
                 f"ba.collection_exercise = '{collection_exercise_id}'  " \
                 "AND " \
                 "ba.business_id = b.party_uuid),  " \
                 "case_details AS " \
                 "(SELECT cg.sampleunitref, " \
                 "cg.status AS case_status, " \
                 "c.id " \
                 "FROM  " \
                 "casesvc.casegroup cg, casesvc.case c " \
                 "WHERE  " \
                 "c.casegroupfk=cg.casegrouppk  " \
                 "AND  " \
                 f"cg.collectionexerciseid = '{collection_exercise_id}' " \
                 "AND  " \
                 f"cg.surveyid='{survey_id}' " \
                 "ORDER BY  " \
                 "cg.status, cg.sampleunitref),  " \
                 "respondent_details AS " \
                 "(SELECT e.business_id AS business_party_uuid, " \
                 "e.status AS enrolment_status " \
                 "FROM  " \
                 "partysvc.enrolment e " \
                 "LEFT JOIN partysvc.respondent r ON e.respondent_id = r.id " \
                 "WHERE " \
                 f"e.survey_id = '{survey_id}') " \
                 "SELECT " \
                 "DISTINCT cd.id as caseId,  " \
                 "bd.sampleunitref,  " \
                 "bd.business_name,  " \
                 "rd.enrolment_status,  " \
                 "cd.case_status,  " \
                 "rd.business_party_uuid " \
                 "FROM " \
                 "case_details cd " \
                 "LEFT JOIN business_details bd ON bd.sampleunitref=cd.sampleunitref " \
                 "LEFT JOIN respondent_details rd ON bd.business_party_uuid = rd.business_party_uuid " \
                 "ORDER BY  " \
                 "sampleunitref, case_status; "
    try:
        case_details = engine.execute(text(case_query))
    except SQLAlchemyError:
        logger.exception("SQL Alchemy query failed")
        raise
    return case_details


@spp_reporting_api.route('/send-report')
class SppSendReport(Resource):

    @staticmethod
    def post():
        engine = app.db.engine
        collex_survey = get_collection_exercise_and_survey(engine)
        survey_id = collex_survey[0]
        collection_exercise_id = collex_survey[1]
        case_details = get_case_details(survey_id, collection_exercise_id, engine)
        survey_response_status = {'surveyId': survey_id, 'collectionExerciseId': collection_exercise_id}
        reporting_unit_respondent_information = {'surveyId': survey_id}
        populate_json_record(
            survey_id,
            case_details,
            survey_response_status,
            reporting_unit_respondent_information,
            engine)
        day = datetime.today().strftime('%d%m%Y')
        ccsi_file_name = "CCSI" + day + ".json"
        rci_file_name = "RCI" + day + ".json"
        gcs = GoogleCloudStorageGateway(app.config)
        gcs.upload_spp_file_to_gcs(
            file_name=ccsi_file_name, file=survey_response_status)
        gcs.upload_spp_file_to_gcs(
            file_name=rci_file_name, file=reporting_unit_respondent_information)
        if app.config['AWS_ENABLED']:
            s3 = SimpleStorageServiceGateway(app.config)
            s3.upload_spp_file(
                file_name=ccsi_file_name, file=survey_response_status)
            s3.upload_spp_file(
                file_name=rci_file_name, file=reporting_unit_respondent_information)
        return make_response(f'The SPP reporting process has completed. Files {ccsi_file_name} and {rci_file_name} '
                             'been uploaded to S3 successfully.', 200)
