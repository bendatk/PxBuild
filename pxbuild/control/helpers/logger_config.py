import logging

def configure_logger(debug=False):
    logger = logging.getLogger("PxBuild")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger

logger = logging.getLogger("PxBuild")