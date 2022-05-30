import logging
from urllib.parse import urlencode

import requests
from flask import current_app as app
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def get_business_by_ru_ref(ru_ref: str):
    """
    Get business by ru_ref

    :param ru_ref: The ru_ref of the business
    :type ru_ref: str
    :return: A dict of data about the business
    :rtype: dict
    :raises ApiError: Raised if party returns a 4XX or 5XX status code.
    """
    logger.info("Retrieving reporting unit", ru_ref=ru_ref)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/businesses/ref/{ru_ref}'
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code in (400, 404) else logger.exception
        log_level("Failed to retrieve reporting unit", ru_ref=ru_ref)
        raise

    logger.info("Successfully retrieved reporting unit", ru_ref=ru_ref)
    return response.json()


def get_respondent_by_party_ids(uuids):
    """
    Gets data for multiple respondents from party.  If the list is empty, returns an empty
    list without going to party.

    This call will return as many parties as it can find.  If some are missing, no error will
    be thrown.

    :param uuids: A list of uuid strings of respondent party ids
    :type uuids: list
    :return: A list of dicts containing party data
    """
    bound_logger = logger.bind(respondent_party_ids=uuids)
    bound_logger.info("Retrieving respondent data for multiple respondents")
    if not uuids:
        bound_logger.info("No party uuids provided.  Returning empty list")
        return []

    params = urlencode([("id", uuid) for uuid in uuids])
    url = f'{app.config["PARTY_URL"]}/party-api/v1/respondents'
    response = requests.get(url, auth=app.config["BASIC_AUTH"], params=params)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        bound_logger.error("Error retrieving respondent data for multiple respondents")
        raise

    bound_logger.info("Successfully retrieved respondent data for multiple respondents")
    return response.json()
