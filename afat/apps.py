# -*- coding: utf-8 -*-
from django.apps import AppConfig

from . import __version__


class AfatConfig(AppConfig):
    name = "afat"
    label = "afat"
    verbose_name = f"AA-FAT Fleet Activity Tracking v{__version__}"
