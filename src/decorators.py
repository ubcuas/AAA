import logging

from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        start = datetime.now()
        result = f(*args, **kwds)
        elapsed = datetime.now() - start
        logger.info("%s took %s time to finish", f.__name__, elapsed)
        return result
    return wrapper