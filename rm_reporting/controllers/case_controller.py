import logging

from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app

logger = wrap_logger(logging.getLogger(__name__))


def get_case_data(collection_exercise_id) -> list:
    logger.info("About to get case data")
    case_engine = app.case_db.engine
    case_business_ids_query = text(
        "SELECT party_id, sample_unit_ref, status "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id and "
        "sample_unit_ref NOT LIKE '1111%'"
    )

    case_result = case_engine.execute(case_business_ids_query, collection_exercise_id=collection_exercise_id).all()
    return case_result


def get_exercise_completion_stats(collection_exercise_id) -> list:
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

    case_result = case_engine.execute(case_query, collection_exercise_id=collection_exercise_id).all()
    return case_result


def get_all_business_ids_for_collection_exercise(collection_exercise_id) -> str:
    case_engine = app.case_db.engine
    case_business_ids_query = text(
        "SELECT party_id "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id and "
        "sample_unit_ref NOT LIKE '1111%'"
    )

    case_business_ids_result = case_engine.execute(
        case_business_ids_query, collection_exercise_id=collection_exercise_id
    )

    business_id_result = case_business_ids_result.all()
    # Ideally we'd use ','.join(business_id_result) but as it's not free to create a list of the ids, this is the
    # next best thing.
    business_ids_string = ""
    for row in business_id_result:
        business_ids_string += f"'{str(getattr(row, 'party_id'))}', "

    # slice off the tailing ', '
    business_ids_string = business_ids_string[:-2]
    return business_ids_string
