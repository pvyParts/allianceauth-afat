"""
views helper
"""

import random

from django.contrib.auth.models import Permission, User
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext as _

from allianceauth.eveonline.models import EveCharacter

from afat.models import AFat, AFatLink, AFatLog, AFatLogEvent
from afat.utils import get_main_character_from_user


def convert_fatlinks_to_dict(request: WSGIRequest, fatlink: AFatLink) -> dict:
    """
    converts a AFatLink object into a dictionary
    :param request:
    :type request:
    :param fatlink:
    :type fatlink:
    :return:
    :rtype:
    """

    # fleet name
    fatlink_fleet = fatlink.hash

    if fatlink.fleet:
        fatlink_fleet = fatlink.fleet

    # esi marker
    via_esi = "No"
    esi_fleet_marker = ""

    # check for ESI link
    if fatlink.is_esilink:
        via_esi = "Yes"
        esi_fleet_marker_classes = "label label-default afat-label afat-label-via-esi"

        if fatlink.is_registered_on_esi:
            esi_fleet_marker_classes += " afat-label-active-esi-fleet"

        marker_text = _("via ESI")
        esi_fleet_marker += (
            f'<span class="{esi_fleet_marker_classes}">{marker_text}</span>'
        )

    # fleet type
    fatlink_type = ""

    if fatlink.link_type:
        fatlink_type = fatlink.link_type.name

    # creator name
    creator_main_character = get_main_character_from_user(user=fatlink.creator)

    # fleet time
    fleet_time = fatlink.afattime
    fleet_time_timestamp = fleet_time.timestamp()

    # number of FATs
    fats_number = fatlink.number_of_fats

    # action buttons
    actions = ""
    if request.user.has_perm("afat.manage_afat") or request.user.has_perm(
        "afat.add_fatlink"
    ):
        button_edit_url = reverse("afat:fatlinks_details_fatlink", args=[fatlink.hash])

        actions += (
            '<a class="btn btn-afat-action btn-info btn-sm" '
            f'href="{button_edit_url}"><span class="fas fa-eye"></span></a>'
        )

    if request.user.has_perm("afat.manage_afat"):
        button_delete_url = reverse("afat:fatlinks_delete_fatlink", args=[fatlink.hash])
        button_delete_text = _("Delete")
        modal_body_text = _(
            f"<p>Are you sure you want to delete FAT link {fatlink_fleet}?</p>"
        )

        actions += (
            '<a class="btn btn-afat-action btn-danger btn-sm" data-toggle="modal" '
            f'data-target="#deleteFatLinkModal" data-url="{button_delete_url}" '
            f'data-confirm-text="{button_delete_text}"'
            f'data-body-text="{modal_body_text}">'
            '<span class="glyphicon glyphicon-trash">'
            "</span></a>"
        )

    summary = {
        "pk": fatlink.pk,
        "fleet_name": fatlink_fleet + esi_fleet_marker,
        "creator_name": creator_main_character,
        "fleet_type": fatlink_type,
        "fleet_time": {"time": fleet_time, "timestamp": fleet_time_timestamp},
        "fats_number": fats_number,
        "hash": fatlink.hash,
        "is_esilink": fatlink.is_esilink,
        "esi_fleet_id": fatlink.esi_fleet_id,
        "is_registered_on_esi": fatlink.is_registered_on_esi,
        "actions": actions,
        "via_esi": via_esi,
    }

    return summary


def convert_fats_to_dict(request: WSGIRequest, fat: AFat) -> dict:
    """
    converts a afat object into a dictionary
    :param request:
    :type request:
    :param fat:
    :type fat:
    :return:
    :rtype:
    """

    # fleet type
    fleet_type = ""
    if fat.afatlink.link_type is not None:
        fleet_type = fat.afatlink.link_type.name

    # esi marker
    via_esi = "No"
    esi_fleet_marker = ""

    if fat.afatlink.is_esilink:
        via_esi = "Yes"
        esi_fleet_marker_classes = "label label-default afat-label afat-label-via-esi"

        if fat.afatlink.is_registered_on_esi:
            esi_fleet_marker_classes += " afat-label-active-esi-fleet"

        marker_text = _("via ESI")
        esi_fleet_marker += (
            f'<span class="{esi_fleet_marker_classes}">{marker_text}</span>'
        )

    # actions
    actions = ""
    if request.user.has_perm("afat.manage_afat"):
        button_delete_fat = reverse(
            "afat:fatlinks_delete_fat", args=[fat.afatlink.hash, fat.id]
        )
        button_delete_text = _("Delete")
        modal_body_text = _(
            "<p>Are you sure you want to remove "
            f"{fat.character.character_name} from this FAT link?</p>"
        )

        actions += (
            '<a class="btn btn-danger btn-sm" '
            'data-toggle="modal" '
            'data-target="#deleteFatModal" '
            f'data-url="{button_delete_fat}" '
            f'data-confirm-text="{button_delete_text}"'
            f'data-body-text="{modal_body_text}">'
            '<span class="glyphicon glyphicon-trash"></span>'
            "</a>"
        )

    fleet_time = fat.afatlink.afattime
    fleet_time_timestamp = fleet_time.timestamp()

    summary = {
        "system": fat.system,
        "ship_type": fat.shiptype,
        "character_name": fat.character.character_name,
        "fleet_name": fat.afatlink.fleet + esi_fleet_marker,
        "fleet_time": {"time": fleet_time, "timestamp": fleet_time_timestamp},
        "fleet_type": fleet_type,
        "via_esi": via_esi,
        "actions": actions,
    }

    return summary


def convert_logs_to_dict(log: AFatLog) -> dict:
    """
    convert AFatLog to dict
    :param log:
    :type log:
    :return:
    :rtype:
    """

    log_time = log.log_time
    log_time_timestamp = log_time.timestamp()

    # user name
    user_main_character = get_main_character_from_user(user=log.user)

    summary = {
        "log_time": {"time": log_time, "timestamp": log_time_timestamp},
        "log_event": AFatLogEvent(log.log_event).label,
        "user": user_main_character,
        "fatlink": log.fatlink_hash,
        "description": log.log_text,
    }

    return summary


def get_random_rgba_color():
    """
    get a random RGB(a) color
    :return:
    :rtype:
    """

    return "rgba({red}, {green}, {blue}, 1)".format(
        red=random.randint(0, 255),
        green=random.randint(0, 255),
        blue=random.randint(0, 255),
    )


def users_with_permission(permission: Permission) -> models.QuerySet:
    """
    returns queryset of users that have the given permission in Auth
    :param permission:
    :type permission:
    :return:
    :rtype:
    """

    users_qs = (
        User.objects.prefetch_related(
            "user_permissions", "groups", "profile__state__permissions"
        )
        .filter(
            Q(user_permissions=permission)
            | Q(groups__permissions=permission)
            | Q(profile__state__permissions=permission)
        )
        .distinct()
    )

    return users_qs


def characters_with_permission(permission: Permission) -> models.QuerySet:
    """
    returns queryset of characters that have the given permission
    in Auth through due to their associated user
    :param permission:
    :type permission:
    :return:
    :rtype:
    """

    # first we need the users that have the permission
    users_qs = users_with_permission(permission)

    # now get their characters ...
    charater_qs = EveCharacter.objects.filter(character_ownership__user__in=users_qs)

    return charater_qs
