"""
Command line progress bar class.
"""

import dotsi  # type: ignore
import logging

log = logging.getLogger(__name__)


class CLI_PROGRESS:

    """
    CLI Progress Bar Class.
    """

    def __init__(self, settings: dotsi.Dict, action: str):
        """
        CLI progress bar initialisation.
        Args:
            settings:   Application settings.
            action:     Action in progress (string)
        """

        log.info("Initialising CLI progress bar.")

        # Initialise progress bar settings to use.
        self.settings = settings
        self.action = action

        # Print a new line to separate the progress bar from previous text.
        print()

    def show_progress(self, prog: int):

        # Calculate length of progress done and to do.
        left = self.settings.progress.PROG_WIDTH * prog // 100
        right = self.settings.progress.PROG_WIDTH - left

        # Complile strings to show progress.
        # Show progress and remainder.
        progess = "#" * left
        remainging = "-" * right

        # Print the progress bar.
        # Note printing on same line so first action
        # is to return to start of line.
        # Also, don't do new line at the end.
        # Show progress and remaining in different colours.
        print(
            f"\r{self.action} : [\033[1;32m{progess}\033[0;31m{remainging}] \033[0;37m{prog:3d} %",
            sep="",
            end="",
            flush=True,
        )
        # Flush line if complete.
        if (prog == 100):
            print()
