"""
Doubles logging.
"""

import logging
import logging.config
import logging.handlers
import time

import dotsi  # type: ignore

from doubles import app_settings


def setup_logging(name: str) -> None:
    """
    Sets up the logging handle.

    Args:
        name:   Name for logger
    """

    # Load application settings.
    settings = dotsi.Dict(app_settings.load("./doubles/settings.yaml"))

    # Create logger.
    log = logging.getLogger(name)
    # Use default logging level from settings.
    log.setLevel(settings.log.DEF_LEVEL)
    # Setup log handler for rotating files.
    handler = logging.handlers.RotatingFileHandler(
        name + ".log", maxBytes=settings.log.MAX_SIZE, backupCount=settings.log.MAX_FILES
    )
    # Assign formatter to the log handler.
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d [%(name)s] [%(levelname)-s] %(message)s",
            datefmt="%Y%m%d-%H:%M:%S",
            style="%",
        )
    )
    logging.Formatter.converter = time.localtime
    # Add log handler to logger.
    log.addHandler(handler)
