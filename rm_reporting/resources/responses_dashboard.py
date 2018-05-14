from datetime import datetime
import logging

from flask import json, Response
from flask_restplus import Resource
from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app, response_dashboard_api

logger = wrap_logger(logging.getLogger(__name__))


@response_dashboard_api.route('/<collection_exercise_id>')
class ResponseDashboard(Resource):

    @staticmethod
    def get(collection_exercise_id):

        engine = app.db.engine

        collex_status = "SELECT COUNT(DISTINCT(sample_unit_ref)) \"Sample Size\", " \
                        "SUM(enrolled) \"Total Enrolled\", SUM(downloaded) \"Total Downloaded\", " \
                        "SUM(uploaded) \"Total Uploaded\" " \
                        "FROM " \
                        "(SELECT " \
                        "events.sampleunitref sample_unit_ref, " \
                        "events.sampleunittype, " \
                        "events.caseref case_ref, " \
                        "events.respondent_enrolled enrolled, " \
                        "events.collection_instrument_downloaded_ind downloaded, " \
                        "events.successful_response_upload_ind uploaded " \
                        "FROM " \
                        "(SELECT cg.sampleunitref, " \
                        "c.sampleunittype, c.caseref, " \
                        "SUM(CASE WHEN ce.categoryFK = 'RESPONDENT_ENROLED' " \
                        "THEN 1 ELSE  0 END) respondent_enrolled, " \
                        "MAX(CASE WHEN ce.categoryFK = 'COLLECTION_INSTRUMENT_DOWNLOADED' " \
                        "THEN 1 ELSE  0 END) collection_instrument_downloaded_ind, " \
                        "MAX(CASE WHEN ce.categoryFK = 'SUCCESSFUL_RESPONSE_UPLOAD' " \
                        "THEN 1 ELSE  0 END) successful_response_upload_ind " \
                        "FROM casesvc.caseevent ce " \
                        "RIGHT OUTER JOIN casesvc.case c  ON c.casePK = ce.caseFK " \
                        "INNER JOIN casesvc.casegroup cg  ON c.casegroupFK = cg.casegroupPK " \
                        "GROUP BY cg.sampleunitref, c.sampleunittype, c.casePK) events) as data_records " \
                        "WHERE case_ref IN " \
                        "(SELECT t.caseref FROM casesvc.\"case\" t " \
                        "WHERE t.casegroupid IN " \
                        "(SELECT t.id \"Group ID\" FROM casesvc.casegroup t " \
                        "WHERE t.collectionexerciseid = :collection_exercise_id))"

        collex_details = engine.execute(text(collex_status), collection_exercise_id=collection_exercise_id).first()

        collex_dict = {'sampleSize': collex_details[0],
                       'accountsEnrolled': int(collex_details[1] or 0),
                       'downloads': collex_details[2],
                       'uploads': collex_details[3]
                       }

        response = {'metadata': {'timeUpdated': datetime.now().timestamp(),
                                 'collectionExerciseId': collection_exercise_id},
                    'report': collex_dict
                    }

        return Response(json.dumps(response), content_type='application/json')
