"""
fatlinks related views
"""

from datetime import datetime, timedelta

from afat import __title__
from afat.app_settings import AFAT_DEFAULT_FATLINK_EXPIRY_TIME
from afat.forms import (
    AFatClickFatForm,
    AFatLinkForm,
    AFatManualFatForm,
    FatLinkEditForm,
)
from afat.helper.views_helper import convert_fatlinks_to_dict, convert_fats_to_dict
from afat.models import (
    AFat,
    AFatDelLog,
    AFatLink,
    AFatLinkType,
    ClickAFatDuration,
    ManualAFat,
)
from afat.providers import esi
from afat.tasks import get_or_create_char, process_fats
from afat.utils import LoggerAddTag

from django.contrib.auth.decorators import login_required, permission_required
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import get_random_string

from esi.decorators import token_required
from esi.models import Token

from allianceauth.authentication.decorators import permissions_required
from allianceauth.eveonline.models import EveCharacter
from allianceauth.eveonline.providers import provider
from allianceauth.services.hooks import get_extension_logger

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required()
@permission_required("afat.basic_access")
def links(request: WSGIRequest, year: int = None) -> HttpResponse:
    """
    fatlinks view
    :param year:
    :param request:
    :return:
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

    logger.info("FAT link list called by {user}".format(user=request.user))

    return render(request, "afat/fat_list.html", context)


@login_required()
@permission_required("afat.basic_access")
def links_data(request: WSGIRequest, year: int = None) -> JsonResponse:
    """
    fatlinks view
    :param year:
    :param request:
    :return:
    """

    if year is None:
        year = datetime.now().year

    fatlinks = (
        AFatLink.objects.filter(afattime__year=year)
        .order_by("-afattime")
        .annotate(number_of_fats=Count("afat", filter=Q(afat__deleted_at__isnull=True)))
    )

    fatlink_rows = [
        convert_fatlinks_to_dict(request=request, fatlink=fatlink)
        for fatlink in fatlinks
    ]

    return JsonResponse(fatlink_rows, safe=False)


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def link_add(request: WSGIRequest) -> HttpResponse:
    """
    add fatlink view
    :param request:
    :return:
    """

    msg = None

    if "msg" in request.session:
        msg = request.session.pop("msg")

    link_types = AFatLinkType.objects.filter(
        is_enabled=True,
    ).order_by("name")

    context = {
        "link_types": link_types,
        "msg": msg,
        "default_expiry_time": AFAT_DEFAULT_FATLINK_EXPIRY_TIME,
    }

    logger.info("Add FAT link view called by {user}".format(user=request.user))

    return render(request, "afat/addlink.html", context)


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def link_create_click(request: WSGIRequest):
    """
    create fatlink helper
    :param request:
    :return:
    """

    if request.method == "POST":
        form = AFatClickFatForm(request.POST)

        if form.is_valid():
            fatlink_hash = get_random_string(length=30)

            link = AFatLink()
            link.fleet = form.cleaned_data["name"]

            if (
                form.cleaned_data["type"] is not None
                and form.cleaned_data["type"] != -1
            ):
                link.link_type = AFatLinkType.objects.get(id=form.cleaned_data["type"])

            link.creator = request.user
            link.hash = fatlink_hash
            link.afattime = timezone.now()
            link.save()

            dur = ClickAFatDuration()
            dur.fleet = AFatLink.objects.get(hash=fatlink_hash)
            dur.duration = form.cleaned_data["duration"]
            dur.save()

            request.session[
                "{fatlink_hash}-creation-code".format(fatlink_hash=fatlink_hash)
            ] = 202

            logger.info(
                "FAT link {fatlink_hash} with name {name} and a "
                "duration of {duration} minutes was created by {user}".format(
                    fatlink_hash=fatlink_hash,
                    name=form.cleaned_data["name"],
                    duration=form.cleaned_data["duration"],
                    user=request.user,
                )
            )

            return redirect("afat:link_edit", fatlink_hash=fatlink_hash)

        request.session["msg"] = [
            "danger",
            (
                "Something went wrong when attempting to submit your"
                " clickable FAT Link."
            ),
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
def link_create_esi(request: WSGIRequest, token, fatlink_hash: str):
    """
    helper: create ESI link
    :param request:
    :param token:
    :param fatlink_hash:
    :return:
    """

    # Check if there is a fleet
    try:
        required_scopes = ["esi-fleets.read_fleet.v1"]
        esi_token = Token.get_token(token.character_id, required_scopes)

        fleet_from_esi = esi.client.Fleets.get_characters_character_id_fleet(
            character_id=token.character_id, token=esi_token.valid_access_token()
        ).result()
    except Exception:
        # Not in a fleet
        request.session["msg"] = [
            "warning",
            "To use the ESI function, you neeed to be in fleet and you need to be "
            "the fleet boss! You can create a clickable FAT link and share it, "
            "if you like.",
        ]

        # return to "Add FAT Link" view
        return redirect("afat:link_add")

    # Check if this character already has a fleet
    try:
        esi_fatlink = AFatLink.objects.filter(
            is_esilink=True,
            is_registered_on_esi=True,
            esi_fleet_id=fleet_from_esi["fleet_id"],
        )

        if esi_fatlink.count() > 0:
            creator_character = EveCharacter.objects.get(
                character_id=token.character_id
            )

            # Character already has a fleet
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
            return redirect("afat:link_add")
    except AFatLink.DoesNotExist:
        pass

    # Check if we deal with the fleet boss here
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
        return redirect("afat:link_add")

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
    if (
        request.session["fatlink_form__type"] is not None
        and request.session["fatlink_form__type"] != -1
    ):
        fatlink.link_type = AFatLinkType.objects.get(
            id=request.session["fatlink_form__type"]
        )

    # save it
    fatlink.save()

    # clear session
    # request.session["fatlink_form__name"] = None
    # request.session["fatlink_form__type"] = None
    del request.session["fatlink_form__name"]
    del request.session["fatlink_form__type"]

    # process fleet members
    process_fats.delay(
        data_list=esi_fleet_member, data_source="esi", fatlink_hash=fatlink_hash
    )

    request.session[
        "{fatlink_hash}-creation-code".format(fatlink_hash=fatlink_hash)
    ] = 200

    logger.info(
        "ESI FAT link {fatlink_hash} created by {user}".format(
            fatlink_hash=fatlink_hash, user=request.user
        )
    )

    return redirect("afat:link_edit", fatlink_hash=fatlink_hash)


@login_required()
def create_esi_fat(request: WSGIRequest):
    """
    create ESI fat helper
    :param request:
    :return:
    """

    fatlink_form = AFatLinkForm(request.POST)

    if fatlink_form.is_valid():
        fatlink_hash = get_random_string(length=30)

        request.session["fatlink_form__name"] = fatlink_form.cleaned_data["name_esi"]
        request.session["fatlink_form__type"] = fatlink_form.cleaned_data["type_esi"]

        return redirect("afat:link_create_esi", fatlink_hash=fatlink_hash)

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
def click_link(request: WSGIRequest, token, fatlink_hash: str = None):
    """
    click fatlink helper
    :param request:
    :param token:
    :param fatlink_hash:
    :return:
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
                        (
                            "FAT registered for {character_name} "
                            "at {fleet_name}".format(
                                character_name=character.character_name, fleet_name=name
                            )
                        ),
                    ]

                    logger.info(
                        "Fleetparticipation for fleet {fleet_name} "
                        "registered for pilot {character_name}".format(
                            fleet_name=name, character_name=character.character_name
                        )
                    )

                    return redirect("afat:dashboard")
                except Exception:
                    request.session["msg"] = [
                        "warning",
                        (
                            "A FAT already exists for the selected character "
                            "({character_name}) and fleet combination.".format(
                                character_name=character.character_name
                            )
                        ),
                    ]

                    return redirect("afat:dashboard")
            else:
                request.session["msg"] = [
                    "warning",
                    (
                        "Cannot register the fleet participation for {character_name}. "
                        "The character needs to be online.".format(
                            character_name=character.character_name
                        )
                    ),
                ]

                return redirect("afat:dashboard")
        except Exception:
            request.session["msg"] = [
                "warning",
                (
                    "There was an issue with the token for {character_name}. "
                    "Please try again.".format(character_name=character.character_name)
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
def link_edit(request: WSGIRequest, fatlink_hash: str = None) -> HttpResponse:
    """
    edit fatlink view
    :param request:
    :param fatlink_hash:
    :return:
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
            request.session[
                "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
            ] = 1
        elif manual_fat_form.is_valid():
            character_name = manual_fat_form.cleaned_data["character"]
            system = manual_fat_form.cleaned_data["system"]
            shiptype = manual_fat_form.cleaned_data["shiptype"]
            creator = request.user
            character = get_or_create_char(name=character_name)
            created_at = timezone.now()

            if character is not None:
                AFat(
                    afatlink_id=link.pk,
                    character=character,
                    system=system,
                    shiptype=shiptype,
                ).save()

                ManualAFat(
                    afatlink_id=link.pk,
                    creator=creator,
                    character=character,
                    created_at=created_at,
                ).save()

                request.session[
                    "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
                ] = 3
            else:
                request.session[
                    "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
                ] = 4
        else:
            request.session[
                "{fatlink_hash}-task-code".format(fatlink_hash=fatlink_hash)
            ] = 0

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

    # Flatlist / Raw Data Tab (deactivated as of 2020-12-26)
    # fats = AFat.objects.filter(afatlink=link)
    # flatlist = None
    # if len(fats) > 0:
    #     flatlist = []
    #
    #     for fat in fats:
    #         fatinfo = [fat.character.character_name, str(fat.system), str(fat.shiptype)]
    #         flatlist.append("\t".join(fatinfo))
    #
    #     flatlist = "\r\n".join(flatlist)

    # let's see if the link is still valid or has expired already
    link_ongoing = True
    try:
        dur = ClickAFatDuration.objects.get(fleet=link)
        now = timezone.now() - timedelta(minutes=dur.duration)

        if now >= link.afattime:
            # link expired
            link_ongoing = False
    except ClickAFatDuration.DoesNotExist:
        # ESI lnk
        link_ongoing = False

    context = {
        "form": AFatLinkForm,
        "msg_code": msg_code,
        "message": message,
        "link": link,
        # "flatlist": flatlist,
        "link_ongoing": link_ongoing,
    }

    logger.info(
        "FAT link {fatlink_hash} edited by {user}".format(
            fatlink_hash=fatlink_hash, user=request.user
        )
    )

    return render(request, "afat/fleet_edit.html", context)


@login_required()
@permissions_required(("afat.manage_afat", "afat.add_fatlink"))
def link_edit_fat_data(request: WSGIRequest, fatlink_hash):
    """
    ajax call
    fat list in link edit view
    :param request:
    :param fatlink_hash:
    """

    fats = AFat.objects.filter(afatlink__hash=fatlink_hash)

    fat_rows = [convert_fats_to_dict(request=request, fat=fat) for fat in fats]

    return JsonResponse(fat_rows, safe=False)


@login_required()
@permissions_required(("afat.manage_afat"))
def del_link(request: WSGIRequest, fatlink_hash: str = None):
    """
    delete fatlink helper
    :param request:
    :param fatlink_hash:
    :return:
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

    AFatDelLog(remover=request.user, deltype=0, string=link.__str__()).save()

    request.session["msg"] = [
        "success",
        "The FAT Link ({fatlink_hash}) and all associated FATs "
        "have been successfully deleted.".format(fatlink_hash=fatlink_hash),
    ]

    logger.info("FAT link %s deleted by %s", fatlink_hash, request.user)

    return redirect("afat:links")


@login_required()
@permissions_required(("afat.manage_afat", "afat.delete_afat"))
def del_fat(request: WSGIRequest, fatlink_hash: str, fat):
    """
    delete fat helper
    :param request:
    :param fatlink_hash:
    :param fat:
    :return:
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
    AFatDelLog(remover=request.user, deltype=1, string=fat_details.__str__()).save()

    request.session["msg"] = [
        "success",
        "The FAT for {character_name} has been successfully "
        "deleted from link {fatlink_hash}.".format(
            character_name=fat_details.character.character_name,
            fatlink_hash=fatlink_hash,
        ),
    ]

    logger.info("FAT %s deleted by %s", fat_details, request.user)

    return redirect("afat:link_edit", fatlink_hash=fatlink_hash)
