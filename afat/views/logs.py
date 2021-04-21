"""
logs related views
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from allianceauth.services.hooks import get_extension_logger

from afat import __title__
from afat.app_settings import AFAT_DEFAULT_LOG_DURATION
from afat.helper.views_helper import convert_logs_to_dict
from afat.models import AFatLog
from afat.utils import LoggerAddTag

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required()
@permission_required("afat.log_view")
def overview(request: WSGIRequest) -> HttpResponse:
    """
    logs view
    :param request:
    :type request:
    :return:
    :rtype:
    """
    logger.info(f"Log view called by {request.user}")

    context = {"log_duration": AFAT_DEFAULT_LOG_DURATION}

    return render(request, "afat/logs_overview.html", context=context)


@login_required()
@permission_required("afat.log_view")
def ajax_get_logs(request: WSGIRequest) -> JsonResponse:
    """
    ajax call :: get all log entries
    :param request:
    :type request:
    :return:
    :rtype:
    """

    logs = AFatLog.objects.all()

    log_rows = [convert_logs_to_dict(log=log) for log in logs]

    return JsonResponse(log_rows, safe=False)
