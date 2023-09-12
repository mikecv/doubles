"""
Doubles application settings.
"""

import dotsi  # type: ignore
import yaml  # type: ignore


def load(settings_file: str) -> dotsi.Dict:
    """
    Load yaml settings file and return settings dictionary.
    Args:
        settings_file:  Name (including path) of yaml settings file.
    Returns:
        Returns dictionary of settings.
    """

    # Read the settings file and return a dictionary of settings.
    with open(settings_file, "r") as sf:
        return yaml.safe_load(sf)