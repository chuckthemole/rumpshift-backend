# arduino_client/utils.py

import logging
import binascii

logger = logging.getLogger("arduino")


def setup_logger():
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s [%(levelname)s] %(message)s")


def hexdump(data: bytes) -> str:
    return binascii.hexlify(data).decode()


def retry(times, exceptions):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(f"Retry {i + 1}/{times} after error: {e}")
            raise e
        return wrapper
    return decorator
