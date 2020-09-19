# -*- coding: utf-8 -*-
from django.apps import AppConfig

from . import __version__


class AfatConfig(AppConfig):
    name = "afat"
    label = "afat"
    verbose_name = f"AFAT - Another Fleet Activity Tracker v{__version__}"
