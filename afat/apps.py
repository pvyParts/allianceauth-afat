"""
App config
"""

from django.apps import AppConfig

from afat import __version__


class AfatConfig(AppConfig):
    """
    General config
    """

    name = "afat"
    label = "afat"
    verbose_name = f"AFAT - Another Fleet Activity Tracker v{__version__}"
