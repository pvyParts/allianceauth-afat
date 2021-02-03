"""
views helper
"""

import random

from afat.models import AFat, AFatLink

from django.contrib.auth.models import User, Permission
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.models import Q
from django.urls import reverse

from allianceauth.eveonline.models import EveCharacter


def convert_fatlinks_to_dict(request: WSGIRequest, fatlink: AFatLink) -> dict:
    """
    converts a AFatLink object into a dictionary
    :param fatlink:
    :param user:
    :return:
    """

    # fleet name
    fatlink_fleet = fatlink.hash

    if fatlink.fleet:
        fatlink_fleet = fatlink.fleet

    # esi marker
    via_esi = "No"
    esi_fleet_marker = ""

    if fatlink.is_esilink:
        via_esi = "Yes"
        esi_fleet_marker_classes = "label label-success afat-label afat-label-via-esi"

        if fatlink.is_registered_on_esi:
            esi_fleet_marker_classes += " afat-label-active-esi-fleet"

        esi_fleet_marker += f'<span class="{esi_fleet_marker_classes}">via ESI</span>'

    # fleet type
    fatlink_type = ""

    if fatlink.link_type:
        fatlink_type = fatlink.link_type.name

    # creator name
    creator_name = fatlink.creator.username
    user_has_no_profile = False

    try:
        creator_profile = fatlink.creator.profile
    except Exception:
        user_has_no_profile = True

    if user_has_no_profile is False:
        if creator_profile.main_character is not None:
            creator_name = creator_profile.main_character.character_name

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
        button_edit_url = reverse("afat:link_edit", args=[fatlink.hash])

        actions += (
            '<a class="btn btn-afat-action btn-info btn-sm" href="'
            + button_edit_url
            + '">'
            '<span class="fas fa-eye"></span>'
            "</a>"
        )

    if request.user.has_perm("afat.manage_afat"):
        button_delete_url = reverse("afat:link_delete", args=[fatlink.hash])

        actions += (
            '<a class="btn btn-afat-action btn-danger btn-sm" data-toggle="modal" '
            'data-target="#deleteModal" data-url="' + button_delete_url + '" '
            'data-name="' + fatlink_fleet + '">'
            '<span class="glyphicon glyphicon-trash"></span>'
            "</a>"
        )

    summary = {
        "pk": fatlink.pk,
        "fleet_name": fatlink_fleet + esi_fleet_marker,
        "creator_name": creator_name,
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
    :param fatlink:
    :param user:
    :return:
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
        esi_fleet_marker_classes = "label label-success afat-label afat-label-via-esi"

        if fat.afatlink.is_registered_on_esi:
            esi_fleet_marker_classes += " afat-label-active-esi-fleet"

        esi_fleet_marker += f'<span class="{esi_fleet_marker_classes}">via ESI</span>'

    # actions
    actions = ""
    if request.user.has_perm("afat.manage_afat"):
        button_delete_fat = reverse("afat:fat_delete", args=[fat.afatlink.hash, fat.id])

        actions += (
            '<a class="btn btn-danger btn-sm" '
            'data-toggle="modal" '
            'data-target="#deleteModal" '
            'data-url="{data_url}" '
            'data-name="{data_name}">'
            '<span class="glyphicon glyphicon-trash"></span>'
            "</a>".format(
                data_url=button_delete_fat,
                data_name=fat.character.character_name,
            )
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


def convert_evecharacter_to_dict(evecharacter: EveCharacter) -> dict:
    """
    converts an EveCharacter object into a dictionary
    :param fatlink:
    """

    summary = {"character_id": "", "character_name": ""}

    return summary


def get_random_rgba_color():
    """
    get a random RGB(a) color
    :return:
    """
    return "rgba({red}, {green}, {blue}, 1)".format(
        red=random.randint(0, 255),
        green=random.randint(0, 255),
        blue=random.randint(0, 255),
    )


def users_with_permission(permission: Permission) -> models.QuerySet:
    """
    returns queryset of users that have the given permission in Auth
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
    """

    # first we need the users that have the permission
    users_qs = users_with_permission(permission)

    # now get their characters ...
    charater_qs = EveCharacter.objects.filter(character_ownership__user__in=users_qs)

    return charater_qs
