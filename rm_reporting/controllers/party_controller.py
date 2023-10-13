import logging

from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app

logger = wrap_logger(logging.getLogger(__name__))


def get_business_attributes(collection_exercise_id: str) -> dict[str, list]:
    """
    Queries the attributes table in party to get all the business information for that specific collection exercise

    :param collection_exercise_id: A uuid for a collection exercise
    :return: A dictionary, keyed by business_id with all the attribute data for the business for that exercise
    """
    logger.info("Getting party attribute data", collection_exercise_id=collection_exercise_id)
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
    logger.info("About to get party attributes", collection_exercise_id=collection_exercise_id)
    with party_engine.begin() as conn:
        attributes_result = conn.execute(text(attributes), {"collection_exercise_id": collection_exercise_id}).all()
    result_dict = {str(getattr(item, "business_party_uuid")): item for item in attributes_result}
    logger.info("Got party attributes", collection_exercise_id=collection_exercise_id)
    return result_dict


def get_enrolment_data(survey_id: str, business_ids: str) -> list:
    """
    Gets all the enrolment data from the enrolment table in party for all the businesses in a given survey

    :param survey_id: A uuid for a survey
    :param business_ids: A string with all the business_ids that are comma separated
    :return: A list of rows containing the enrolment data
    """
    # It shouldn't be possible for this to be empty as the download link only appears on live exercises.  But we
    # don't want it to go bang if we say, hit the api directly for a not ready exercise
    if business_ids == "":
        return []
    party_engine = app.party_db.engine
    # Get list of respondents for all those businesses for this survey (via enrolment table)
    # Get all the enrolments for the survey the exercise is for but only for the businesses
    enrolment_details_query_text = (
        f"SELECT * "
        f"FROM partysvc.enrolment e "
        f"WHERE "
        f"e.survey_id = :survey_id AND e.business_id IN ({business_ids}) "
    )

    enrolment_details_query = text(enrolment_details_query_text)
    logger.info("About to get enrolment details", survey_id=survey_id)
    with party_engine.begin() as conn:
        enrolment_details_result = conn.execute(enrolment_details_query, {"survey_id": survey_id}).all()
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
        '<business_id1>': [{'respondent_id': 1, 'status': 'active'}, {'respondent_id': 2, 'status': 'active'}]
        '<business_id2>': [{'respondent_id': 1, 'status': 'active'}, {'respondent_id': 3, 'status': 'active'}]
    }

    :param enrolment_details_result:
    :return: A dictionary, keyed by the ru_ref
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
    with party_engine.begin() as conn:
        respondent_details_result = conn.execute(respondent_details_query).all()
    results_dict = {str(getattr(item, "id")): item for item in respondent_details_result}
    logger.info("Got respondent data")
    return results_dict
