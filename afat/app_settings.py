# -*- coding: utf-8 -*-

"""
our app setting
"""

import re

from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from afat.utils import clean_setting


# set default panels if none are set in local.py
AFAT_DEFAULT_FATLINK_EXPIRY_TIME = clean_setting("AFAT_DEFAULT_FATLINK_EXPIRY_TIME", 60)

# Name of this app as shown in the Auth sidebar and page titles
AFAT_APP_NAME = clean_setting(
    "AFAT_APP_NAME", _("Fleet Activity Tracking"), required_type=str
)

AFAT_BASE_URL = slugify(AFAT_APP_NAME, allow_unicode=True)


def get_site_url():  # regex sso url
    """
    get the site url
    :return: string
    """

    regex = r"^(.+)\/s.+"
    matches = re.finditer(regex, settings.ESI_SSO_CALLBACK_URL, re.MULTILINE)
    url = "http://"

    for match in matches:
        url = match.groups()[0]  # first match

    return url
