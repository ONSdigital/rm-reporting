import logging

from sqlalchemy import text
from structlog import wrap_logger

from rm_reporting import app

logger = wrap_logger(logging.getLogger(__name__))


def get_case_data(collection_exercise_id):
    case_engine = app.case_db.engine
    case_business_ids_query = text(
        "SELECT party_id, sample_unit_ref, status "
        "FROM casesvc.casegroup "
        "WHERE collection_exercise_id = :collection_exercise_id and "
        "sample_unit_ref NOT LIKE '1111%'"
    )
    logger.info("About to get case data")
    case_result = case_engine.execute(case_business_ids_query, collection_exercise_id=collection_exercise_id).all()
    return case_result
