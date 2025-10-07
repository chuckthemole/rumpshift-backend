from shared.logger import get_logger

logger = get_logger(__name__)


def fetch_data():
    logger.info("Fetching data from API", endpoint="/counter", retries=3)
    try:
        # do something
        logger.debug("Request successful", response_time_ms=120)
    except Exception as e:
        logger.error("Error fetching data", error=str(e))
