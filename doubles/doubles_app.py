"""
Text analysis to find duplicate questions.
"""

import click
import csv
import logging
import os
import sys

import dotsi  # type: ignore

from collections import defaultdict
from doubles import app_settings
from doubles.app_logging import setup_logging
from doubles.question_store import Question_Store

log = logging.getLogger(__name__)


class Doubles:
    """
    Main class the question analyser application.
    """

    def __init__(self, csv_file):
        """
        Doubles initialisation.
        """

        # Load application settings.
        self._settings = dotsi.Dict(app_settings.load("./doubles/settings.yaml"))

        # Initialise app name and version from settings.
        self._app_name = self._settings.app.APP_NAME
        self._app_version = self._settings.app.APP_VERSION

        # Setup the application logger.
        setup_logging(self._app_name)

        log.info(f"Initialising application: {self._app_name}, version: {self._app_version}")

        # Optional include file.
        if csv_file is None:
            log.warning("No questions file specified.")
        else:
            log.info(f"Question file to process: {csv_file}.")

            # Read the questions into the questions store
            self.questions = Question_Store(csv_file, self._settings)
            if self.questions.num_q == 0:
                log.warning("No questions in CSV file, exiting...")
                exit(0)

            # Process the questions.
            self.questions.process()

            # Report on the results.
            self.questions.results()


@click.command()
@click.option("-q", "--csv-file", type=click.Path(exists=False), help="Path to the CSV file")
def run(csv_file) -> None:
    """
    Poetry calls this to get the application up and running.
    Assumes a python script in project.toml as follows:

    [tool.poetry.scripts]
    doubles-go = "doubles.doubles:run"

    Can then run as: poetry run doubles-go
    """

    Doubles(csv_file)


if __name__ == "__main__":
    run()
