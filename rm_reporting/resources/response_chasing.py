import csv
import io
import logging
from datetime import datetime

from flask import make_response
from flask_restx import Resource
from openpyxl import Workbook
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from structlog import wrap_logger

from rm_reporting import app, response_chasing_api

logger = wrap_logger(logging.getLogger(__name__))


@response_chasing_api.route("/download-report/<collection_exercise_id>/<survey_id>")
class ResponseChasingDownload(Resource):
    @staticmethod
    def get(collection_exercise_id, survey_id):

        output = io.BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Response Chasing Report"

        # Set headers
        headers = {
            "A1": "Survey Status",
            "B1": "Reporting Unit Ref",
            "C1": "Reporting Unit Name",
            "D1": "Enrolment Status",
            "E1": "Respondent Name",
            "F1": "Respondent Telephone",
            "G1": "Respondent Email",
            "H1": "Respondent Account Status",
        }

        for cell, header in headers.items():
            ws[cell] = header
            ws.column_dimensions[cell[0]].width = len(header)

        case_engine = app.case_db.engine
        party_engine = app.party_db.engine

        # Way to create spreadsheet
        # Get case data (and list of ru_refs and business_ids)
        case_business_ids_query = text(
            "SELECT party_id, sample_unit_ref, status "
            "FROM casesvc.casegroup "
            "WHERE collection_exercise_id = :collection_exercise_id and "
            "sample_unit_ref NOT LIKE '1111%'"
        )
        logger.info("About to get case data")
        case_result = case_engine.execute(case_business_ids_query, collection_exercise_id=collection_exercise_id).all()
        logger.info("Got case data")
        # Get all the party_ids for all the businesses that are part of the collection exercise
        # TODO get the values in a list in a tidier way...
        business_ids_list = []
        business_ids_string = ""
        for row in case_result:
            business_ids_list.append(str(getattr(row, "party_id")))
            business_ids_string += f"'{str(getattr(row, 'party_id'))}', "

        # slice off the tailing ', '
        business_ids_string = business_ids_string[:-2]

        # Get party attribute data for all those ru_refs (business_attributes table)
        attributes = (
            f"SELECT DISTINCT "
            f"ba.collection_exercise As collection_exercise_uuid, "
            f"ba.business_id AS business_party_uuid, "
            f"ba.attributes->> 'name' AS business_name "
            f"FROM partysvc.business_attributes ba "
            f"WHERE "
            f"ba.collection_exercise = '{collection_exercise_id}'"
        )
        logger.info("About to get party attributes")
        attributes_result = party_engine.execute(attributes, collection_exercise_id=collection_exercise_id).all()
        logger.info("Got party attributes")

        # TODO maybe loop over it, converting it into a dict keyed by the ru_ref for easy access later on
        # Get list of respondents for all those businesses for this survey (via enrolment table)
        # Get all the enrolments for the survey the exercise is for but only for the businesses
        enrolment_details_query_text = (
            f"SELECT * "
            f"FROM partysvc.enrolment e "
            f"WHERE "
            f"e.survey_id = :survey_id AND e.business_id IN ({business_ids_string}) "
        )

        enrolment_details_query = text(enrolment_details_query_text)
        # TODO maybe loop over it, converting it into a dict keyed by the ru_ref for easy access later on as theres a
        # lot of wasted work looping over all the results again and again
        logger.info("About to get enrolment details")
        enrolment_details_result = party_engine.execute(enrolment_details_query, survey_id=survey_id).all()
        logger.info("Got enrolment details")
        respondent_ids_string = ""
        for row in enrolment_details_result:
            respondent_ids_string += f"'{str(getattr(row, 'respondent_id'))}', "

            # slice off the tailing ', '
        respondent_ids_string = respondent_ids_string[:-2]

        # Resolve details of all those respondents (respondent table)
        respondent_details_query_text = f"SELECT * FROM partysvc.respondent r WHERE r.id IN ({respondent_ids_string}) "

        respondent_details_query = text(respondent_details_query_text)
        respondent_details_result = party_engine.execute(respondent_details_query).all()

        # Loop over all the cases, filling in the blanks along the way and add each row to the spreadsheet
        logger.info("About to loop over all the data")
        for row in case_result:
            logger.info("Dealing with ru", ru_ref=getattr(row, "sample_unit_ref"))
            survey_status = getattr(row, "status")
            ru_ref = getattr(row, "sample_unit_ref")
            ru_name = ""
            for business in attributes_result:
                if getattr(business, "business_party_uuid") == getattr(row, "party_id"):
                    ru_name = getattr(business, "business_name")
                    break

            # Create a row in the spreadsheet for each enrolment for this survey in the business
            enrolment_count_for_business = 0
            for enrolment in enrolment_details_result:
                logger.info("Dealing with enrolments for business", business_id=getattr(enrolment, "business_id"))
                if getattr(enrolment, "business_id") == getattr(row, "party_id"):

                    # Get the resolved respondent details from the earlier result.  For now, we have to loop over the
                    # list to find the right one, but we can reorganise it for easier access
                    respondent_details = None
                    for respondent in respondent_details_result:
                        # We need to handle the possibility of the respondent being deleted
                        if getattr(respondent, "id") == getattr(enrolment, "respondent_id"):
                            respondent_details = respondent
                            break

                    enrolment_status = getattr(enrolment, "status")
                    respondent_name = (
                        getattr(respondent_details, "first_name") + " " + getattr(respondent_details, "last_name")
                    )
                    respondent_telephone = getattr(respondent_details, "telephone")
                    respondent_email = getattr(respondent_details, "email_address")
                    respondent_account_status = getattr(respondent_details, "status")

                    business = [
                        survey_status,
                        ru_ref,
                        ru_name,
                        enrolment_status,
                        respondent_name,
                        respondent_telephone,
                        respondent_email,
                        respondent_account_status,
                    ]
                    ws.append(business)
                    enrolment_count_for_business += 1
                    logger.info("Added row to the table")

            # If there are no enrolments for the business, we still need to report on it
            if enrolment_count_for_business == 0:
                business = [
                    survey_status,
                    ru_ref,
                    ru_name,
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
                ws.append(business)
                logger.info("Added empty row to the table")

        wb.active = 1
        wb.save(output)
        wb.close()
        logger.info("Finished putting together spreadsheet")

        response = make_response(output.getvalue(), 200)
        response.headers["Content-Disposition"] = f"attachment; filename=response_chasing_{collection_exercise_id}.xlsx"
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response


@response_chasing_api.route("/download-social-mi/<collection_exercise_id>")
class SocialMIDownload(Resource):
    @staticmethod
    def get(collection_exercise_id):
        output = io.StringIO()

        # Set headers
        headers = [
            "Sample Reference",
            "Status",
            "Status Event",
            "Address Line 1",
            "Address Line 2",
            "Locality",
            "Town Name",
            "Postcode",
            "Country",
        ]

        datestr = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        engine = app.db.engine

        case_status = text(
            "SELECT cg.sampleunitref, cg.status, "
            "(SELECT cat.shortdescription "
            "FROM casesvc.caseevent ce "
            "JOIN casesvc.category cat "
            "ON ce.categoryfk = cat.categorypk "
            "WHERE ce.casefk = c.casepk "
            "AND cat.shortdescription ~ '^[[:digit:]]*$' "
            "ORDER BY ce.createddatetime DESC LIMIT 1), "
            "attributes->> 'ADDRESS_LINE1' AS address_line_1, "
            "attributes->> 'ADDRESS_LINE2' AS address_line_2, "
            "attributes->> 'LOCALITY' AS locality, "
            "attributes->> 'TOWN_NAME' AS town_name, "
            "attributes->> 'POSTCODE' AS postcode, "
            "attributes->> 'COUNTRY' AS country "
            "FROM casesvc.case c "
            "JOIN casesvc.casegroup cg "
            "ON c.casegroupfk = cg.casegrouppk "
            "JOIN samplesvc.sampleattributes sa "
            "ON CONCAT(attributes->> 'TLA', '' , attributes->> 'REFERENCE') = cg.sampleunitref "
            "WHERE c.sampleunittype = 'H' AND cg.collectionexerciseid = :collection_exercise_id"
        )

        try:
            case_details = engine.execute(case_status, collection_exercise_id=collection_exercise_id)
        except SQLAlchemyError:
            logger.exception("SQL Alchemy query failed")
            raise

        my_data = [headers]
        my_data.extend(case_details)

        writer = csv.writer(output)
        writer.writerows(my_data)

        response = make_response(output.getvalue(), 200)
        response.headers["Content-Disposition"] = (
            f"attachment; filename=social_mi_report_{collection_exercise_id}" f"_{datestr}.csv"
        )
        response.headers["Content-type"] = "text/csv"
        return response
