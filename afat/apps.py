"""
app config
"""

from django.apps import AppConfig

from afat import __version__


class AfatConfig(AppConfig):
    """
    general config
    """

    name = "afat"
    label = "afat"
    verbose_name = f"AFAT - Another Fleet Activity Tracker v{__version__}"
