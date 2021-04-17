"""
utilities
"""

import logging

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.utils.functional import lazy
from django.utils.html import format_html

from allianceauth.eveonline.models import EveAllianceInfo

# Format for output of datetime for this app
DATETIME_FORMAT = "%Y-%m-%d %H:%M"

format_html_lazy = lazy(format_html, str)


class LoggerAddTag(logging.LoggerAdapter):
    """
    add custom tag to a logger
    """

    def __init__(self, my_logger, prefix):
        super().__init__(my_logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        """
        process log items
        :param msg:
        :param kwargs:
        :return:
        """

        return "[%s] %s" % (self.prefix, msg), kwargs


logger = LoggerAddTag(logging.getLogger(__name__), __package__)


def clean_setting(
    name: str,
    default_value: object,
    min_value: int = None,
    max_value: int = None,
    required_type: type = None,
):
    """
    cleans the input for a custom setting

    Will use `default_value` if settings does not exit or has the wrong type
    or is outside define boundaries (for int only)

    Need to define `required_type` if `default_value` is `None`

    Will assume `min_value` of 0 for int (can be overriden)

    Returns cleaned value for setting
    """

    if default_value is None and not required_type:
        raise ValueError("You must specify a required_type for None defaults")

    if not required_type:
        required_type = type(default_value)

    if min_value is None and required_type == int:
        min_value = 0

    if not hasattr(settings, name):
        cleaned_value = default_value
    else:
        if (
            isinstance(getattr(settings, name), required_type)
            and (min_value is None or getattr(settings, name) >= min_value)
            and (max_value is None or getattr(settings, name) <= max_value)
        ):
            cleaned_value = getattr(settings, name)
        else:
            logger.warning(
                "You setting for {name} is not valid. Please correct it. "
                "Using default for now: {value}".format(name=name, value=default_value)
            )
            cleaned_value = default_value

    return cleaned_value


def write_log(request: WSGIRequest, log_event: str, fatlink_hash: str, log_text: str):
    """
    write the log
    :param fatlink:
    :param request:
    :param log_event:
    :param log_text:
    """

    from afat.models import AFatLog

    afat_log = AFatLog()
    afat_log.user = request.user
    afat_log.log_event = log_event
    afat_log.log_text = log_text
    afat_log.fatlink_hash = fatlink_hash
    afat_log.save()


def get_or_create_alliance_info(alliance_id: int) -> EveAllianceInfo:
    """
    get or create alliance info
    :param alliance_id:
    :return:
    """

    try:
        eve_alliance_info = EveAllianceInfo.objects.get(alliance_id=alliance_id)
    except EveAllianceInfo.DoesNotExist:
        eve_alliance_info = EveAllianceInfo.objects.create_alliance(
            alliance_id=alliance_id
        )

    return eve_alliance_info
