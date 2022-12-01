import logging

from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app

logger = wrap_logger(logging.getLogger(__name__))


def get_case_data(collection_exercise_id: str) -> list:
    """
    Gets the party_id (for the business), ru_ref and submission status for every case for a
    given collection_exercise_id

    :param collection_exercise_id: A uuid for a collection exercise
    :return: A list with all the rows found in the query
    """
    logger.info("About to get case data", collection_exercise_id=collection_exercise_id)
    case_engine = app.case_db.engine
    case_business_ids_query = text(
        "SELECT party_id, sample_unit_ref, status "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id "
        "ORDER BY sample_unit_ref, status"
    )

    return case_engine.execute(case_business_ids_query, collection_exercise_id=collection_exercise_id).all()


def get_business_ids_from_case_data(case_result: list) -> str:
    """
    Takes a list of case results and returns a comma separated list of business_ids.

    :param case_result: A list of rows from a sqlAlchemy .all() result.
    :return: A string with all the party_ids comma separated
    """
    business_ids_string = ""
    for row in case_result:
        business_ids_string += f"'{str(getattr(row, 'party_id'))}', "
    # slice off the tailing ', '
    return business_ids_string[:-2]


def get_exercise_completion_stats(collection_exercise_id: str) -> list:
    """
    Gets the case completion stats for a given collection exercise.  The fields in the single returned row in the list
    are: "Sample Size", "Not Started", "In Progress" and "Complete"

    :param collection_exercise_id: A uuid for a collection exercise
    :return: A list with a single row of data with the various counts
    """
    logger.info("About to get exercise completion stats", collection_exercise_id=collection_exercise_id)
    case_engine = app.case_db.engine
    case_query = text(
        'SELECT COUNT(*) AS "Sample Size", '
        "COUNT(CASE WHEN status = 'NOTSTARTED' THEN 1 ELSE NULL END) AS \"Not Started\", "
        "COUNT(CASE WHEN status = 'INPROGRESS' THEN 1 ELSE NULL END) AS \"In Progress\", "
        "COUNT(CASE WHEN status = 'COMPLETE' THEN 1 ELSE NULL END) AS \"Complete\" "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id "
        "AND sample_unit_ref NOT LIKE '1111%'"
    )

    return case_engine.execute(case_query, collection_exercise_id=collection_exercise_id).all()


def get_all_business_ids_for_collection_exercise(collection_exercise_id: str) -> str:
    logger.info("About to get all business  ids for collection exercise", collection_exercise_id=collection_exercise_id)
    case_engine = app.case_db.engine
    case_business_ids_query = text(
        "SELECT party_id "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id and "
        "sample_unit_ref NOT LIKE '1111%'"
    )

    business_id_result = case_engine.execute(
        case_business_ids_query, collection_exercise_id=collection_exercise_id
    ).all()

    # Ideally we'd use ','.join(business_id_result) but as it's not free to create a list of the ids, this is the
    # next best thing.
    business_ids_string = ""
    for row in business_id_result:
        business_ids_string += f"'{str(getattr(row, 'party_id'))}', "

    # slice off the tailing ', '
    return business_ids_string[:-2]
