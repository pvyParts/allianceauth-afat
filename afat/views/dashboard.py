"""
dashboard related views
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

from afat import __title__
from afat.helper.views_helper import convert_fatlinks_to_dict, convert_fats_to_dict
from afat.models import AFat, AFatLink
from afat.utils import LoggerAddTag

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required()
@permission_required("afat.basic_access")
def overview(request: WSGIRequest) -> HttpResponse:
    """
    dashboard view
    :param request:
    :type request:
    :return:
    :rtype:
    """

    msg = None

    if "msg" in request.session:
        msg = request.session.pop("msg")

    characters_by_user = CharacterOwnership.objects.filter(user=request.user)
    characters = list()

    for users_character in characters_by_user:
        character_fat = AFat.objects.filter(character=users_character.character)

        if character_fat.count() > 0:
            characters.append(users_character.character)

    context = {"characters": characters, "msg": msg}

    logger.info("Module called by {user}".format(user=request.user))

    return render(request, "afat/dashboard.html", context)


@login_required
@permission_required("afat.basic_access")
def ajax_recent_get_fats_by_character(
    request: WSGIRequest, charid: int
) -> JsonResponse:
    """
    ajax call :: get all FATs for a given character
    :param request:
    :type request:
    :param charid:
    :type charid:
    :return:
    :rtype:
    """

    character = EveCharacter.objects.get(character_id=charid)

    fats = (
        AFat.objects.filter(character=character)
        .order_by("afatlink__afattime")
        .reverse()[:10]
    )

    character_fat_rows = [
        convert_fats_to_dict(request=request, fat=fat) for fat in fats
    ]

    return JsonResponse(character_fat_rows, safe=False)


@login_required
@permission_required("afat.basic_access")
def ajax_get_recent_fatlinks(request: WSGIRequest) -> JsonResponse:
    """
    ajax call :: get recent fat links for the dashboard datatable
    :param request:
    :type request:
    :return:
    :rtype:
    """

    fatlinks = AFatLink.objects.order_by("-afattime")[:10]

    fatlink_rows = [
        convert_fatlinks_to_dict(request=request, fatlink=fatlink)
        for fatlink in fatlinks
    ]

    return JsonResponse(fatlink_rows, safe=False)
