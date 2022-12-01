import logging

from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app

logger = wrap_logger(logging.getLogger(__name__))


def get_attribute_data(collection_exercise_id):
    party_engine = app.party_db.engine
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
    result_dict = {str(getattr(item, "business_party_uuid")): item for item in attributes_result}
    logger.info("Got party attributes")
    return result_dict


def get_enrolment_data(survey_id, business_ids_string) -> list:
    # It shouldn't be possible for this to be empty as the download link only appears on live exercises.  But we
    # don't want it to go bang if we say, hit the api directly for a not ready exercise
    if business_ids_string == "":
        return []
    party_engine = app.party_db.engine
    # Get list of respondents for all those businesses for this survey (via enrolment table)
    # Get all the enrolments for the survey the exercise is for but only for the businesses
    enrolment_details_query_text = (
        f"SELECT * "
        f"FROM partysvc.enrolment e "
        f"WHERE "
        f"e.survey_id = :survey_id AND e.business_id IN ({business_ids_string}) "
    )

    enrolment_details_query = text(enrolment_details_query_text)
    logger.info("About to get enrolment details")
    enrolment_details_result = party_engine.execute(enrolment_details_query, survey_id=survey_id).all()
    return enrolment_details_result


def get_respondent_ids_from_enrolment_data(enrolment_details_result: list) -> str:
    respondent_ids_string = ""
    for row in enrolment_details_result:
        respondent_ids_string += f"'{str(getattr(row, 'respondent_id'))}', "

    # slice off the tailing ', '
    respondent_ids_string = respondent_ids_string[:-2]
    return respondent_ids_string


def format_enrolment_data(enrolment_details_result: list) -> dict[str, list]:
    """
    Takes a list of enrolment details and formats them like below

    example = {
        '123': [{'respondent_id': 1, 'status': 'active'}, {'respondent_id': 2, 'status': 'active'}]
        '456': [{'respondent_id': 1, 'status': 'active'}, {'respondent_id': 3, 'status': 'active'}]
    }

    :param enrolment_details_result:
    :return:
    """
    resulting_dict = {}
    for row in enrolment_details_result:
        business_id = str(getattr(row, "business_id"))
        if resulting_dict.get(business_id) is None:
            resulting_dict[business_id] = [row]
        else:
            resulting_dict[business_id].append(row)

    logger.info("Got enrolment details")
    return resulting_dict


def get_respondent_data(respondent_ids_string) -> dict:
    logger.info("About to get respondent data")
    # It's possible for a new survey that there are no respondents yet, so we don't want it to break in that case
    if respondent_ids_string == "":
        logger.info("Returning empty respondent data dict")
        return {}

    party_engine = app.party_db.engine
    respondent_details_query = text(f"SELECT * FROM partysvc.respondent r WHERE r.id IN ({respondent_ids_string}) ")
    respondent_details_result = party_engine.execute(respondent_details_query).all()
    results_dict = {str(getattr(item, "id")): item for item in respondent_details_result}
    logger.info("Got respondent data")
    return results_dict


def get_dashboard_enrolment_details(survey_id, business_ids_string) -> list:
    party_engine = app.party_db.engine
    enrolment_details_query_text = (
        f"SELECT * "
        f"FROM partysvc.enrolment e "
        f"WHERE "
        f"e.survey_id = :survey_id AND e.business_id IN ({business_ids_string}) "
    )

    enrolment_details_query = text(enrolment_details_query_text)
    enrolment_details_result = party_engine.execute(enrolment_details_query, survey_id=survey_id).all()
    return enrolment_details_result
