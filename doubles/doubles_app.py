"""
Text analysis to find duplicate questions.
"""

import click
import logging

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

    def __init__(self, ifile, ofile, dry, progress):
        """
        Doubles initialisation.
        Args:
            ifile:          Input file of questions.
            ofile:          Output file for unique questions.
            dry:            Dry run, no export file created.
            progress:       Show progress bar during analysis.
        Returns:
            Returns None.
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
        if ifile is None:
            log.warning("No questions file specified.")
        else:
            log.info(f"Question file to process: {ifile}")

            # Read the questions into the questions store
            self.questions = Question_Store(ifile, self._settings)
            if self.questions.num_q == 0:
                log.warning("No questions in question file, exiting...")
                exit(0)

            # Process the questions.
            self.questions.process(progress)

            # Report statistics for the analysis.
            self.questions.results()

            # Export the results.
            if dry is not True:
                log.info(f"File for results export: {ofile}")
                self.questions.export(ofile)

@click.command()
@click.option("-i", "--ifile", type=click.Path(exists=False), help="Path to the input .xlsx file.")
@click.option("-o", "--ofile", type=click.Path(exists=False), help="Path to the output .xlsx file.")
@click.option("-d", "--dry", is_flag=True, help="Perform dry run, i.e. no export file created.")
@click.option("-p", "--progress", is_flag=True, help="Show a progress bar.")
def run(ifile, ofile, dry, progress) -> None:
    """
    Poetry calls this to get the application up and running.
    Assumes a python script in project.toml as follows:

    [tool.poetry.scripts]
    doubles-go = "doubles.doubles:run"

    Can then run as: poetry run doubles-go
    """

    Doubles(ifile, ofile, dry, progress)


if __name__ == "__main__":
    run()
