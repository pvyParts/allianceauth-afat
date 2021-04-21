"""
fatlinks related views
"""

from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string

from allianceauth.authentication.decorators import permissions_required
from allianceauth.eveonline.models import EveCharacter
from allianceauth.eveonline.providers import provider
from allianceauth.services.hooks import get_extension_logger
from esi.decorators import token_required
from esi.models import Token

from afat import __title__
from afat.app_settings import (
    AFAT_DEFAULT_FATLINK_EXPIRY_TIME,
    AFAT_DEFAULT_FATLINK_REOPEN_DURATION,
    AFAT_DEFAULT_FATLINK_REOPEN_GRACE_TIME,
)
from afat.forms import (  # ExtendFatLinkDuration,
    AFatClickFatForm,
    AFatEsiFatForm,
    AFatManualFatForm,
    FatLinkEditForm,
)
from afat.helper.fatlinks import get_esi_fleet_information_by_user
from afat.helper.time import get_time_delta
from afat.helper.views_helper import convert_fatlinks_to_dict, convert_fats_to_dict
from afat.models import AFat, AFatLink, AFatLinkType, AFatLogEvent, ClickAFatDuration
from afat.providers import esi
from afat.tasks import get_or_create_character, process_fats
from afat.utils import LoggerAddTag, write_log

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required()
@permission_required("afat.basic_access")
def overview(request: WSGIRequest, year: int = None) -> HttpResponse:
    """
    fatlinks view
    :param request:
    :type request:
    :param year:
    :type year:
    :return:
    :rtype:
    """

    if year is None:
        year = datetime.now().year

    msg = None

    if "msg" in request.session:
        msg = request.session.pop("msg")

    context = {
        "msg": msg,
        "year": year,
        "year_current": datetime.now().year,
        "year_prev": int(year) - 1,
        "year_next": int(year) + 1,
    }

    logger.info(f"FAT link list called by {request.user}")

    return render(request, "afat/fatlinks_overview.html", context)


@login_required()
@permission_required("afat.basic_access")
def ajax_get_fatlinks_by_year(request: WSGIRequest, year: int = None) -> JsonResponse:
    """
    ajax call :: get all FAT links for a given year
    :param request:
    :type request:
    :param year:
    :type year:
    :return:
    :rtype:
    """

    if year is None:
        year = datetime.now().year

    fatlinks = AFatLink.objects.filter(afattime__year=year).order_by("-afattime")

    fatlink_rows = [
        convert_fatlinks_to_dict(request=request, fatlink=fatlink)
        for fatlink in fatlinks
    ]

    return JsonResponse(fatlink_rows, safe=False)


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def add_fatlink(request: WSGIRequest) -> HttpResponse:
    """
    add fatlink view
    :param request:
    :type request:
    :return:
    :rtype:
    """

    msg = None

    if "msg" in request.session:
        msg = request.session.pop("msg")

    link_types_configured = False
    link_types_count = AFatLinkType.objects.all().count()

    if link_types_count > 0:
        link_types_configured = True

    context = {
        "link_types_configured": link_types_configured,
        "msg": msg,
        "default_expiry_time": AFAT_DEFAULT_FATLINK_EXPIRY_TIME,
        "esi_fleet": get_esi_fleet_information_by_user(request.user),
        "esi_fatlink_form": AFatEsiFatForm(),
        "manual_fatlink_form": AFatClickFatForm(),
    }

    logger.info(f"Add FAT link view called by {request.user}")

    return render(request, "afat/fatlinks_add_fatlink.html", context)


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def create_clickable_fatlink(request: WSGIRequest):
    """
    create clickable fat link
    :param request:
    :type request:
    :return:
    :rtype:
    """

    if request.method == "POST":
        form = AFatClickFatForm(request.POST)

        if form.is_valid():
            fatlink_hash = get_random_string(length=30)

            fatlink = AFatLink()
            fatlink.fleet = form.cleaned_data["name"]

            if form.cleaned_data["type"] is not None:
                fatlink.link_type = form.cleaned_data["type"]

            fatlink.creator = request.user
            fatlink.hash = fatlink_hash
            fatlink.afattime = timezone.now()
            fatlink.save()

            dur = ClickAFatDuration()
            dur.fleet = AFatLink.objects.get(hash=fatlink_hash)
            dur.duration = form.cleaned_data["duration"]
            dur.save()

            request.session[
                "{fatlink_hash}-creation-code".format(fatlink_hash=fatlink_hash)
            ] = 202

            # writing DB log
            fleet_type = ""
            if fatlink.link_type:
                fleet_type = f" (Fleet Type: {fatlink.link_type.name})"

            write_log(
                request=request,
                log_event=AFatLogEvent.CREATE_FATLINK,
                log_text=(
                    f'FAT link with name "{form.cleaned_data["name"]}"{fleet_type} and '
                    f'a duration of {form.cleaned_data["duration"]} minutes was created'
                ),
                fatlink_hash=fatlink.hash,
            )

            logger.info(
                (
                    f'FAT link "{fatlink_hash}" with name '
                    f'"{form.cleaned_data["name"]}"{fleet_type} and a duration '
                    f'of {form.cleaned_data["duration"]} minutes was created '
                    f"by {request.user}"
                )
            )

            return redirect("afat:fatlinks_details_fatlink", fatlink_hash=fatlink_hash)

        request.session["msg"] = [
            "danger",
            "Something went wrong when attempting to submit yourclickable FAT Link.",
        ]
        return redirect("afat:dashboard")

    request.session["msg"] = [
        "warning",
        (
            'You must fill out the form on the "Add FAT Link" '
            "page to create a clickable FAT Link"
        ),
    ]

    return redirect("afat:dashboard")


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
@token_required(scopes=["esi-fleets.read_fleet.v1"])
def create_esi_fatlink_callback(request: WSGIRequest, token, fatlink_hash: str):
    """
    helper: create ESI link (callback, used when coming back from character selection)
    :param request:
    :type request:
    :param token:
    :type token:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    # check if there is a fleet
    try:
        required_scopes = ["esi-fleets.read_fleet.v1"]
        esi_token = Token.get_token(token.character_id, required_scopes)

        fleet_from_esi = esi.client.Fleets.get_characters_character_id_fleet(
            character_id=token.character_id, token=esi_token.valid_access_token()
        ).result()
    except Exception:
        # not in a fleet
        request.session["msg"] = [
            "warning",
            "To use the ESI function, you neeed to be in fleet and you need to be "
            "the fleet boss! You can create a clickable FAT link and share it, "
            "if you like.",
        ]

        # return to "Add FAT Link" view
        return redirect("afat:fatlinks_add_fatlink")

    # check if this character already has a fleet
    creator_character = EveCharacter.objects.get(character_id=token.character_id)
    registered_fleets_for_creator = AFatLink.objects.filter(
        is_esilink=True,
        is_registered_on_esi=True,
        character__character_name=creator_character.character_name,
    )

    fleet_already_registered = False
    character_has_registered_fleets = False
    registered_fleets_to_close = list()

    if registered_fleets_for_creator.count() > 0:
        character_has_registered_fleets = True

        for registered_fleet in registered_fleets_for_creator:
            if registered_fleet.esi_fleet_id == fleet_from_esi["fleet_id"]:
                # Character already has a fleet
                fleet_already_registered = True
            else:
                registered_fleets_to_close.append(
                    {"registered_fleet": registered_fleet}
                )

    # if the FC already has a fleet and it is the same as already registered,
    # just throw a warning
    if fleet_already_registered is True:
        request.session["msg"] = [
            "warning",
            "Fleet with ID {fleet_id} for your character {character_name} "
            "has already been registered and pilots joining this "
            "fleet are automatically tracked.".format(
                fleet_id=fleet_from_esi["fleet_id"],
                character_name=creator_character.character_name,
            ),
        ]

        # return to "Add FAT Link" view
        return redirect("afat:fatlinks_add_fatlink")

    # if it's a new fleet, remove all former registered fleets if there are any
    if (
        character_has_registered_fleets is True
        and fleet_already_registered is False
        and len(registered_fleets_to_close) > 0
    ):
        for registered_fleet_to_close in registered_fleets_to_close:
            reason = (
                f"FC has opened a new fleet with the "
                f"character {creator_character.character_name}"
            )

            logger.info(
                (
                    f"Closing ESI FAT link with hash "
                    f'"{registered_fleet_to_close["registered_fleet"].hash}". '
                    f"Reason: {reason}"
                )
            )

            registered_fleet_to_close["registered_fleet"].is_registered_on_esi = False
            registered_fleet_to_close["registered_fleet"].save()

    # check if we deal with the fleet boss here
    try:
        esi_fleet_member = esi.client.Fleets.get_fleets_fleet_id_members(
            fleet_id=fleet_from_esi["fleet_id"],
            token=esi_token.valid_access_token(),
        ).result()
    except Exception:
        request.session["msg"] = [
            "warning",
            "Not Fleet Boss! Only the fleet boss can utilize the ESI function. "
            "You can create a clickable FAT link and share it, if you like.",
        ]

        # return to "Add FAT Link" view
        return redirect("afat:fatlinks_add_fatlink")

    creator_character = EveCharacter.objects.get(character_id=token.character_id)

    # create the fatlink
    fatlink = AFatLink(
        afattime=timezone.now(),
        fleet=request.session["fatlink_form__name"],
        creator=request.user,
        character=creator_character,
        hash=fatlink_hash,
        is_esilink=True,
        is_registered_on_esi=True,
        esi_fleet_id=fleet_from_esi["fleet_id"],
    )

    # add fleet type if there is any
    if request.session["fatlink_form__type"] is not None:
        fatlink.link_type_id = request.session["fatlink_form__type"]

    # save it
    fatlink.save()

    # writing DB log
    fleet_type = ""
    if fatlink.link_type:
        fleet_type = f" (Fleet Type: {fatlink.link_type.name})"

    write_log(
        request=request,
        log_event=AFatLogEvent.CREATE_FATLINK,
        log_text=(
            f'ESI FAT link with name "{request.session["fatlink_form__name"]}"'
            f"{fleet_type} was created by {request.user}"
        ),
        fatlink_hash=fatlink.hash,
    )

    logger.info(
        (
            f'ESI FAT link "{fatlink_hash}" with name '
            f'"{request.session["fatlink_form__name"]}"{fleet_type} '
            f"was created by {request.user}"
        )
    )

    # clear session
    del request.session["fatlink_form__name"]
    del request.session["fatlink_form__type"]

    # process fleet members in the background
    process_fats.delay(
        data_list=esi_fleet_member, data_source="esi", fatlink_hash=fatlink_hash
    )

    request.session[
        "{fatlink_hash}-creation-code".format(fatlink_hash=fatlink_hash)
    ] = 200

    return redirect("afat:fatlinks_details_fatlink", fatlink_hash=fatlink_hash)


@login_required()
def create_esi_fatlink(request: WSGIRequest):
    """
    create ESI fat link
    :param request:
    :type request:
    :return:
    :rtype:
    """

    fatlink_form = AFatEsiFatForm(request.POST)

    if fatlink_form.is_valid():
        fatlink_hash = get_random_string(length=30)

        fatlink_type = None
        if fatlink_form.cleaned_data["type_esi"]:
            fatlink_type_from_form = fatlink_form.cleaned_data["type_esi"]
            fatlink_type = fatlink_type_from_form.pk

        request.session["fatlink_form__name"] = fatlink_form.cleaned_data["name_esi"]
        request.session["fatlink_form__type"] = fatlink_type

        return redirect(
            "afat:fatlinks_create_esi_fatlink_callback", fatlink_hash=fatlink_hash
        )

    request.session["msg"] = [
        "danger",
        "Something went wrong when attempting to submit your ESI FAT Link.",
    ]

    return redirect("afat:dashboard")


@login_required()
@permission_required("afat.basic_access")
@token_required(
    scopes=[
        "esi-location.read_location.v1",
        "esi-location.read_ship_type.v1",
        "esi-location.read_online.v1",
    ]
)
def add_fat(request: WSGIRequest, token, fatlink_hash: str = None):
    """
    click fatlink helper
    :param request:
    :type request:
    :param token:
    :type token:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    if fatlink_hash is None:
        request.session["msg"] = ["warning", "No FAT link hash provided."]

        return redirect("afat:dashboard")

    try:
        try:
            fleet = AFatLink.objects.get(hash=fatlink_hash)
        except AFatLink.DoesNotExist:
            request.session["msg"] = ["warning", "The hash provided is not valid."]

            return redirect("afat:dashboard")

        dur = ClickAFatDuration.objects.get(fleet=fleet)
        now = timezone.now() - timedelta(minutes=dur.duration)

        if now >= fleet.afattime:
            request.session["msg"] = [
                "warning",
                (
                    "Sorry, that FAT Link is expired. If you were on that fleet, "
                    "contact your FC about having your FAT manually added."
                ),
            ]

            return redirect("afat:dashboard")

        character = EveCharacter.objects.get(character_id=token.character_id)

        try:
            required_scopes = [
                "esi-location.read_location.v1",
                "esi-location.read_online.v1",
                "esi-location.read_ship_type.v1",
            ]
            esi_token = Token.get_token(token.character_id, required_scopes)

            # check if character is online
            character_online = esi.client.Location.get_characters_character_id_online(
                character_id=token.character_id, token=esi_token.valid_access_token()
            ).result()

            if character_online["online"] is True:
                # character location
                location = esi.client.Location.get_characters_character_id_location(
                    character_id=token.character_id,
                    token=esi_token.valid_access_token(),
                ).result()

                # current ship
                ship = esi.client.Location.get_characters_character_id_ship(
                    character_id=token.character_id,
                    token=esi_token.valid_access_token(),
                ).result()

                # system information
                system = esi.client.Universe.get_universe_systems_system_id(
                    system_id=location["solar_system_id"]
                ).result()["name"]

                ship_name = provider.get_itemtype(ship["ship_type_id"]).name

                try:
                    fat = AFat(
                        afatlink=fleet,
                        character=character,
                        system=system,
                        shiptype=ship_name,
                    )
                    fat.save()

                    if fleet.fleet is not None:
                        name = fleet.fleet
                    else:
                        name = fleet.hash

                    request.session["msg"] = [
                        "success",
                        f"FAT registered for {character.character_name} at {name}",
                    ]

                    logger.info(
                        f'Participation for fleet "{name}" registered '
                        f"for pilot {character.character_name}"
                    )

                    return redirect("afat:dashboard")
                except Exception:
                    request.session["msg"] = [
                        "warning",
                        (
                            "A FAT already exists for the selected character "
                            f"({character.character_name}) and fleet combination."
                        ),
                    ]

                    return redirect("afat:dashboard")
            else:
                request.session["msg"] = [
                    "warning",
                    (
                        "Cannot register the fleet participation for "
                        f"{character.character_name}. The character needs to be online."
                    ),
                ]

                return redirect("afat:dashboard")
        except Exception:
            request.session["msg"] = [
                "warning",
                (
                    "There was an issue with the token for "
                    f"{character.character_name}. Please try again."
                ),
            ]

            return redirect("afat:dashboard")
    except Exception:
        request.session["msg"] = [
            "warning",
            "The hash provided is not for a clickable FAT Link.",
        ]

        return redirect("afat:dashboard")


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def details_fatlink(request: WSGIRequest, fatlink_hash: str = None) -> HttpResponse:
    """
    fatlink view
    :param request:
    :type request:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    if fatlink_hash is None:
        request.session["msg"] = ["warning", "No FAT Link hash provided."]

        return redirect("afat:dashboard")

    try:
        link = AFatLink.objects.get(hash=fatlink_hash)
    except AFatLink.DoesNotExist:
        request.session["msg"] = ["warning", "The hash provided is not valid."]

        return redirect("afat:dashboard")

    if request.method == "POST":
        fatlink_edit_form = FatLinkEditForm(request.POST)
        manual_fat_form = AFatManualFatForm(request.POST)

        if fatlink_edit_form.is_valid():
            link.fleet = fatlink_edit_form.cleaned_data["fleet"]
            link.save()

            # writing DB log
            write_log(
                request=request,
                log_event=AFatLogEvent.CHANGE_FATLINK,
                log_text=(
                    'FAT link changed. Fleet name was set to "{fleet_name}"'
                ).format(fleet_name=link.fleet),
                fatlink_hash=link.hash,
            )

            logger.info(
                (
                    'FAT link with hash "{fatlink_hash}" changed. '
                    'Fleet name was set to "{fleet_name}" by {user}'
                ).format(
                    fatlink_hash=link.hash, fleet_name=link.fleet, user=request.user
                )
            )

            request.session[
                "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
            ] = 1
        elif manual_fat_form.is_valid():
            character_name = manual_fat_form.cleaned_data["character"]
            system = manual_fat_form.cleaned_data["system"]
            shiptype = manual_fat_form.cleaned_data["shiptype"]
            character = get_or_create_character(name=character_name)

            if character is not None:
                AFat(
                    afatlink_id=link.pk,
                    character=character,
                    system=system,
                    shiptype=shiptype,
                ).save()

                request.session[
                    "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
                ] = 3

                # writing DB log
                write_log(
                    request=request,
                    log_event=AFatLogEvent.MANUAL_FAT,
                    log_text=(
                        "Pilot {pilot_name} flying a {ship_type} was manually added"
                    ).format(
                        pilot_name=character.character_name,
                        ship_type=shiptype,
                    ),
                    fatlink_hash=link.hash,
                )

                logger.info(
                    (
                        "Pilot {pilot_name} flying a {ship_type} was manually added to "
                        'FAT link with hash "{fatlink_hash}" by {user}'
                    ).format(
                        fatlink_hash=link.hash,
                        pilot_name=character.character_name,
                        ship_type=shiptype,
                        user=request.user,
                    )
                )
            else:
                request.session[
                    "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
                ] = 4
        else:
            request.session[
                "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
            ] = 0

    logger.info(
        'FAT link "{fatlink_hash}" details view called by {user}'.format(
            fatlink_hash=fatlink_hash, user=request.user
        )
    )

    msg_code = None
    message = None

    if "msg" in request.session:
        msg_code = 999
        message = request.session.pop("msg")
    elif (
        "{fatlink_hash}-creation-code".format(fatlink_hash=fatlink_hash)
        in request.session
    ):
        msg_code = request.session.pop(
            "{fatlink_hash}-creation-code".format(fatlink_hash=fatlink_hash)
        )
    elif (
        "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash) in request.session
    ):
        msg_code = request.session.pop(
            "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
        )

    # let's see if the link is still valid or has expired already and can be re-opened
    link_ongoing = True
    link_can_be_reopened = False
    link_expires = None

    try:
        dur = ClickAFatDuration.objects.get(fleet=link)
        link_expires = link.afattime + timedelta(minutes=dur.duration)
        now = timezone.now()

        if link_expires <= now:
            # link expired
            link_ongoing = False

            if (
                link.reopened is False
                and get_time_delta(link_expires, now, "minutes")
                < AFAT_DEFAULT_FATLINK_REOPEN_GRACE_TIME
            ):
                link_can_be_reopened = True
    except ClickAFatDuration.DoesNotExist:
        # ESI link
        link_ongoing = False

    context = {
        "msg_code": msg_code,
        "message": message,
        "link": link,
        # "flatlist": flatlist,
        "link_expires": link_expires,
        "link_ongoing": link_ongoing,
        "link_can_be_reopened": link_can_be_reopened,
        "reopen_grace_time": AFAT_DEFAULT_FATLINK_REOPEN_GRACE_TIME,
        "reopen_duration": AFAT_DEFAULT_FATLINK_REOPEN_DURATION,
    }

    return render(request, "afat/fatlinks_details_fatlink.html", context)


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def ajax_get_fats_by_fatlink(request: WSGIRequest, fatlink_hash):
    """
    ajax call :: get all FATs for a given FAT link hash
    :param request:
    :type request:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    fats = AFat.objects.filter(afatlink__hash=fatlink_hash)

    fat_rows = [convert_fats_to_dict(request=request, fat=fat) for fat in fats]

    return JsonResponse(fat_rows, safe=False)


@login_required()
@permission_required("afat.manage_afat")
def delete_fatlink(request: WSGIRequest, fatlink_hash: str = None):
    """
    delete fatlink helper
    :param request:
    :type request:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    if fatlink_hash is None:
        request.session["msg"] = ["warning", "No FAT Link hash provided."]

        return redirect("afat:dashboard")

    try:
        link = AFatLink.objects.get(hash=fatlink_hash)
    except AFatLink.DoesNotExist:
        request.session["msg"] = [
            "danger",
            "The fatlink hash provided is either invalid or "
            "the fatlink has already been deleted.",
        ]

        return redirect("afat:dashboard")

    AFat.objects.filter(afatlink_id=link.pk).delete()

    link.delete()

    write_log(
        request=request,
        log_event=AFatLogEvent.DELETE_FATLINK,
        log_text="FAT link deleted.",
        fatlink_hash=link.hash,
    )

    request.session["msg"] = [
        "success",
        'The FAT Link "{fatlink_hash}" and all associated FATs '
        "have been successfully deleted.".format(fatlink_hash=fatlink_hash),
    ]

    logger.info(
        (
            'Fat link "{fatlink_hash}" and all associated '
            "FATs have been deleted by {user}"
        ).format(fatlink_hash=fatlink_hash, user=request.user)
    )

    return redirect("afat:links")


@login_required()
@permissions_required(("afat.manage_afat", "afat.delete_afat"))
def delete_fat(request: WSGIRequest, fatlink_hash: str, fat):
    """
    delete fat helper
    :param request:
    :type request:
    :param fatlink_hash:
    :type fatlink_hash:
    :param fat:
    :type fat:
    :return:
    :rtype:
    """

    try:
        link = AFatLink.objects.get(hash=fatlink_hash)
    except AFatLink.DoesNotExist:
        request.session["msg"] = [
            "danger",
            "The hash provided is either invalid or has been deleted.",
        ]

        return redirect("afat:dashboard")

    try:
        fat_details = AFat.objects.get(pk=fat, afatlink_id=link.pk)
    except AFat.DoesNotExist:
        request.session["msg"] = [
            "danger",
            "The hash and FAT ID do not match.",
        ]

        return redirect("afat:dashboard")

    fat_details.delete()

    write_log(
        request=request,
        log_event=AFatLogEvent.DELETE_FAT,
        log_text="The FAT for {character_name} has been deleted".format(
            character_name=fat_details.character.character_name,
        ),
        fatlink_hash=link.hash,
    )

    request.session["msg"] = [
        "success",
        (
            "The FAT for {character_name} has been successfully "
            'deleted from FAT link "{fatlink_hash}".'
        ).format(
            character_name=fat_details.character.character_name,
            fatlink_hash=fatlink_hash,
        ),
    ]

    logger.info(
        (
            "The FAT for {character_name} has been deleted "
            'from FAT link "{fatlink_hash}" by {user}.'
        ).format(
            character_name=fat_details.character.character_name,
            fatlink_hash=fatlink_hash,
            user=request.user,
        )
    )

    return redirect("afat:fatlinks_details_fatlink", fatlink_hash=fatlink_hash)


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def close_esi_fatlink(request: WSGIRequest, fatlink_hash: str) -> JsonResponse:
    """
    ajax call to close an ESI fat link
    :param request:
    :type request:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    try:
        fatlink = AFatLink.objects.get(hash=fatlink_hash)

        logger.info(
            'Closing ESI FAT link with hash "{fatlink_hash}". Reason: {reason}'.format(
                fatlink_hash=fatlink_hash, reason="Closed by manual request"
            )
        )

        fatlink.is_registered_on_esi = False
        fatlink.save()
    except AFatLink.DoesNotExist:
        logger.info(
            'ESI FAT link with hash "{fatlink_hash}" does not exist'.format(
                fatlink_hash=fatlink_hash
            )
        )

    return redirect("afat:fatlinks_add_fatlink")


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def reopen_fatlink(request: WSGIRequest, fatlink_hash: str):
    """
    re-open fat link
    :param request:
    :type request:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    # if request.method == "POST":
    #     fatlink_reopen_form = ExtendFatLinkDuration(request.POST)
    #
    #     if fatlink_reopen_form.is_valid():
    #         duration = ClickAFatDuration.objects.get(fleet__hash=fatlink_hash)
    #         reopen_for = fatlink_reopen_form.cleaned_data["duration"]
    #
    #         # get minutes already passed since fatlink creation
    #         created_at = duration.fleet.afattime
    #         now = datetime.now()
    #
    #         time_difference_in_minutes = get_time_delta(created_at, now, "minutes")
    #         new_duration = (
    #             time_difference_in_minutes
    #             + fatlink_reopen_form.cleaned_data["duration"]
    #         )
    #
    #         duration.duration = new_duration
    #         duration.save()

    try:
        fatlink_duration = ClickAFatDuration.objects.get(fleet__hash=fatlink_hash)

        if fatlink_duration.fleet.reopened is False:
            created_at = fatlink_duration.fleet.afattime
            now = datetime.now()

            time_difference_in_minutes = get_time_delta(created_at, now, "minutes")
            new_duration = (
                time_difference_in_minutes + AFAT_DEFAULT_FATLINK_REOPEN_DURATION
            )

            fatlink_duration.duration = new_duration
            fatlink_duration.save()

            fatlink_duration.fleet.reopened = True
            fatlink_duration.fleet.save()

            # writing DB log
            write_log(
                request=request,
                # log_event=AFatLogEvent.REOPEN_FATLINK,
                log_event=AFatLogEvent.REOPEN_FATLINK,
                log_text=(
                    f"FAT link re-opened for a "
                    f"duration of {AFAT_DEFAULT_FATLINK_REOPEN_DURATION} minutes"
                ),
                fatlink_hash=fatlink_duration.fleet.hash,
            )

            logger.info(
                (
                    f'FAT link with hash "{fatlink_hash}" '
                    f"re-opened by {request.user} for a "
                    f"duration of {AFAT_DEFAULT_FATLINK_REOPEN_DURATION} minutes"
                )
            )

            request.session[
                "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
            ] = 5
        else:
            request.session[
                "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
            ] = 7
    except ClickAFatDuration.DoesNotExist:
        request.session[
            "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
        ] = 6

    return redirect("afat:fatlinks_details_fatlink", fatlink_hash=fatlink_hash)
