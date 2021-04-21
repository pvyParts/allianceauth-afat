"""
statistics related views
"""

import calendar
from collections import OrderedDict
from datetime import datetime

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import redirect, render

from allianceauth.authentication.decorators import permissions_required
from allianceauth.authentication.models import CharacterOwnership
from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger

from afat import __title__
from afat.helper.views_helper import characters_with_permission, get_random_rgba_color
from afat.models import AFat
from afat.utils import LoggerAddTag, get_or_create_alliance_info

logger = LoggerAddTag(get_extension_logger(__name__), __title__)


@login_required()
@permission_required("afat.basic_access")
def overview(request: WSGIRequest, year: int = None) -> HttpResponse:
    """
    statistics main view
    :param request:
    :type request:
    :param year:
    :type year:
    :return:
    :rtype:
    """

    if year is None:
        year = datetime.now().year

    if request.user.has_perm("afat.stats_corporation_other"):
        basic_access_permission = Permission.objects.select_related("content_type").get(
            content_type__app_label="afat", codename="basic_access"
        )

        characters_with_access = characters_with_permission(basic_access_permission)

        data = {"No Alliance": [1]}
        sanity_check = dict()

        # first create the alliance keys in our dict
        for character_with_access in characters_with_access:
            if character_with_access.alliance_name is not None:
                data[character_with_access.alliance_name] = [
                    character_with_access.alliance_id
                ]

        # now append the alliance keys
        for character_with_access in characters_with_access:
            corp_id = character_with_access.corporation_id
            corp_name = character_with_access.corporation_name

            if corp_id not in sanity_check.keys():
                if character_with_access.alliance_name is None:
                    data["No Alliance"].append((corp_id, corp_name))
                else:
                    data[character_with_access.alliance_name].append(
                        (corp_id, corp_name)
                    )

            sanity_check[corp_id] = corp_id

    elif request.user.has_perm("afat.stats_corporation_own"):
        data = [
            (
                request.user.profile.main_character.corporation_id,
                request.user.profile.main_character.corporation_name,
            )
        ]
    else:
        data = None

    chars = CharacterOwnership.objects.filter(user=request.user)
    months = list()

    for char in chars:
        char_fats = AFat.objects.filter(afatlink__afattime__year=year)
        char_stats = {}

        char_has_fats = False

        for i in range(1, 13):
            char_fat_count = (
                char_fats.filter(afatlink__afattime__month=i)
                .filter(character__id=char.character.id)
                .count()
            )

            if char_fat_count > 0:
                char_stats[str(i)] = char_fat_count
                char_has_fats = True

        if char_has_fats is True:
            char_l = [
                char.character.character_name,
                char_stats,
                char.character.character_id,
            ]
            months.append(char_l)

    context = {
        "data": data,
        "charstats": months,
        "year": year,
        "year_current": datetime.now().year,
        "year_prev": int(year) - 1,
        "year_next": int(year) + 1,
    }

    logger.info("Statistics overview called by {user}".format(user=request.user))

    return render(request, "afat/statistics_overview.html", context)


@login_required()
@permission_required("afat.basic_access")
def character(
    request: WSGIRequest, charid: int, year: int = None, month: int = None
) -> HttpResponse:
    """
    character statistics view
    :param request:
    :type request:
    :param charid:
    :type charid:
    :param year:
    :type year:
    :param month:
    :type month:
    :return:
    :rtype:
    """

    eve_character = EveCharacter.objects.get(character_id=charid)
    valid = [
        char.character for char in CharacterOwnership.objects.filter(user=request.user)
    ]

    if eve_character not in valid and not request.user.has_perm(
        "afat.stats_char_other"
    ):
        request.session["msg"] = (
            "warning",
            "You do not have permission to view statistics for this character.",
        )

        return redirect("afat:dashboard")

    if not month or not year:
        request.session["msg"] = ("danger", "Date information not complete!")

        return redirect("afat:dashboard")

    fats = AFat.objects.filter(
        character__character_id=charid,
        afatlink__afattime__month=month,
        afatlink__afattime__year=year,
    )

    # Data for Ship Type Pie Chart
    data_ship_type = {}

    for fat in fats:
        if fat.shiptype in data_ship_type.keys():
            continue

        data_ship_type[fat.shiptype] = fats.filter(shiptype=fat.shiptype).count()

    colors = []

    for _ in data_ship_type.keys():
        bg_color_str = get_random_rgba_color()
        colors.append(bg_color_str)

    data_ship_type = [
        # ship type can be None, so we need to convert to string here
        list(str(key) for key in data_ship_type.keys()),
        list(data_ship_type.values()),
        colors,
    ]

    # Data for by Time Line Chart
    data_time = {}

    for i in range(0, 24):
        data_time[i] = fats.filter(afatlink__afattime__hour=i).count()

    data_time = [
        list(data_time.keys()),
        list(data_time.values()),
        [get_random_rgba_color()],
    ]

    context = {
        "character": eve_character,
        "month": month,
        "month_current": datetime.now().month,
        "month_prev": int(month) - 1,
        "month_next": int(month) + 1,
        "year": year,
        "year_current": datetime.now().year,
        "year_prev": int(year) - 1,
        "year_next": int(year) + 1,
        "data_ship_type": data_ship_type,
        "data_time": data_time,
        "fats": fats,
    }

    logger.info(
        "Character statistics for {character} ({month} {year}) called by {user}".format(
            character=eve_character,
            month=calendar.month_name[int(month)],
            year=year,
            user=request.user,
        )
    )

    return render(request, "afat/statistics_character.html", context)


@login_required()
@permissions_required(("afat.stats_corporation_other", "afat.stats_corporation_own"))
def corporation(
    request: WSGIRequest, corpid: int = 0000, year: int = None, month: int = None
) -> HttpResponse:
    """
    corp statistics view
    :param request:
    :type request:
    :param corpid:
    :type corpid:
    :param year:
    :type year:
    :param month:
    :type month:
    :return:
    :rtype:
    """

    if not year:
        year = datetime.now().year

    # Check character has permission to view other corp stats
    if int(request.user.profile.main_character.corporation_id) != int(corpid):
        if not request.user.has_perm("afat.stats_corporation_other"):
            request.session["msg"] = (
                "warning",
                "You do not have permission to view statistics for that corporation.",
            )

            return redirect("afat:dashboard")

    corp = EveCorporationInfo.objects.get(corporation_id=corpid)
    corp_name = corp.corporation_name

    if not month:
        months = []

        for i in range(1, 13):
            corp_fats = AFat.objects.filter(
                character__corporation_id=corpid,
                afatlink__afattime__month=i,
                afatlink__afattime__year=year,
            ).count()

            avg_fats = corp_fats / corp.member_count

            if corp_fats > 0:
                months.append((i, corp_fats, round(avg_fats, 2)))

        context = {
            "corporation": corp.corporation_name,
            "months": months,
            "corpid": corpid,
            "year": year,
            "year_current": datetime.now().year,
            "year_prev": int(year) - 1,
            "year_next": int(year) + 1,
            "type": 0,
        }

        return render(request, "afat/date_select.html", context)

    fats = AFat.objects.filter(
        afatlink__afattime__month=month,
        afatlink__afattime__year=year,
        character__corporation_id=corpid,
    )

    characters = EveCharacter.objects.filter(corporation_id=corpid)

    # Data for Stacked Bar Graph
    # (label, color, [list of data for stack])
    data = {}

    for fat in fats:
        if fat.shiptype in data.keys():
            continue

        data[fat.shiptype] = {}

    chars = []

    for fat in fats:
        if fat.character.character_name in chars:
            continue

        chars.append(fat.character.character_name)

    for key, ship_type in data.items():
        for char in chars:
            ship_type[char] = 0

    for fat in fats:
        data[fat.shiptype][fat.character.character_name] += 1

    data_stacked = []

    for key, value in data.items():
        stack = list()
        stack.append(key)
        stack.append(get_random_rgba_color())
        stack.append([])

        data_ = stack[2]

        for char in chars:
            data_.append(value[char])

        stack.append(data_)
        data_stacked.append(tuple(stack))

    data_stacked = [chars, data_stacked]

    # Data for By Time
    data_time = {}

    for i in range(0, 24):
        data_time[i] = fats.filter(afatlink__afattime__hour=i).count()

    data_time = [
        list(data_time.keys()),
        list(data_time.values()),
        [get_random_rgba_color()],
    ]

    # Data for By Weekday
    data_weekday = []

    for i in range(1, 8):
        data_weekday.append(fats.filter(afatlink__afattime__week_day=i).count())

    data_weekday = [
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        data_weekday,
        [get_random_rgba_color()],
    ]

    chars = {}

    for char in characters:
        fat_c = fats.filter(character_id=char.id).count()
        chars[char.character_name] = (fat_c, char.character_id)

    context = {
        "corp": corp,
        "corporation": corp.corporation_name,
        "month": month,
        "month_current": datetime.now().month,
        "month_prev": int(month) - 1,
        "month_next": int(month) + 1,
        "year": year,
        "year_current": datetime.now().year,
        "year_prev": int(year) - 1,
        "year_next": int(year) + 1,
        "data_stacked": data_stacked,
        "data_time": data_time,
        "data_weekday": data_weekday,
        "chars": chars,
    }

    logger.info(
        (
            "Corporation statistics for {corp_name} ({month} {year}) called by {user}"
        ).format(
            corp_name=corp_name,
            month=calendar.month_name[int(month)],
            year=year,
            user=request.user,
        )
    )

    return render(request, "afat/statistics_corporation.html", context)


@login_required()
@permission_required("afat.stats_corporation_other")
def alliance(
    request: WSGIRequest, allianceid: int, year: int = None, month: int = None
) -> HttpResponse:
    """
    alliance statistics view
    :param request:
    :type request:
    :param allianceid:
    :type allianceid:
    :param year:
    :type year:
    :param month:
    :type month:
    :return:
    :rtype:
    """

    if not year:
        year = datetime.now().year

    if allianceid == "000":
        allianceid = None

    if allianceid is not None:
        ally = get_or_create_alliance_info(alliance_id=allianceid)
        alliance_name = ally.alliance_name
    else:
        ally = None
        alliance_name = "No Alliance"

    if not month:
        months = []

        for i in range(1, 13):
            ally_fats = AFat.objects.filter(
                character__alliance_id=allianceid,
                afatlink__afattime__month=i,
                afatlink__afattime__year=year,
            ).count()

            if ally_fats > 0:
                months.append((i, ally_fats))

        context = {
            "corporation": alliance_name,
            "months": months,
            "corpid": allianceid,
            "year": year,
            "year_current": datetime.now().year,
            "year_prev": int(year) - 1,
            "year_next": int(year) + 1,
            "type": 1,
        }

        return render(request, "afat/date_select.html", context)

    if not month or not year:
        request.session["msg"] = ("danger", "Date information incomplete.")

        return redirect("afat:dashboard")

    fats = AFat.objects.filter(
        character__alliance_id=allianceid,
        afatlink__afattime__month=month,
        afatlink__afattime__year=year,
    )

    corporations = EveCorporationInfo.objects.filter(alliance=ally)

    # Data for Ship Type Pie Chart
    data_ship_type = {}

    for fat in fats:
        if fat.shiptype in data_ship_type.keys():
            continue

        data_ship_type[fat.shiptype] = fats.filter(shiptype=fat.shiptype).count()

    colors = []

    for _ in data_ship_type.keys():
        bg_color_str = get_random_rgba_color()
        colors.append(bg_color_str)

    data_ship_type = [
        # ship type can be None, so we need to convert to string here
        list(str(key) for key in data_ship_type.keys()),
        list(data_ship_type.values()),
        colors,
    ]

    # Fats by corp and ship type?
    data = {}

    for fat in fats:
        if fat.shiptype in data.keys():
            continue

        data[fat.shiptype] = {}

    corps = []

    for fat in fats:
        if fat.character.corporation_name in corps:
            continue

        corps.append(fat.character.corporation_name)

    for key, ship_type in data.items():
        for corp in corps:
            ship_type[corp] = 0

    for fat in fats:
        data[fat.shiptype][fat.character.corporation_name] += 1

    if None in data.keys():
        data["Unknown"] = data[None]
        data.pop(None)

    data_stacked = []

    for key, value in data.items():
        stack = list()
        stack.append(key)
        stack.append(get_random_rgba_color())
        stack.append([])

        data_ = stack[2]

        for corp in corps:
            data_.append(value[corp])

        stack.append(data_)
        data_stacked.append(tuple(stack))

    data_stacked = [corps, data_stacked]

    # Avg fats by corp
    data_avgs = {}

    for corp in corporations:
        c_fats = fats.filter(character__corporation_id=corp.corporation_id).count()
        avg = c_fats / corp.member_count
        data_avgs[corp.corporation_name] = round(avg, 2)

    data_avgs = OrderedDict(sorted(data_avgs.items(), key=lambda x: x[1], reverse=True))
    data_avgs = [
        list(data_avgs.keys()),
        list(data_avgs.values()),
        get_random_rgba_color(),
    ]

    # Fats by Time
    data_time = {}

    for i in range(0, 24):
        data_time[i] = fats.filter(afatlink__afattime__hour=i).count()

    data_time = [
        list(data_time.keys()),
        list(data_time.values()),
        [get_random_rgba_color()],
    ]

    # Fats by weekday
    data_weekday = []

    for i in range(1, 8):
        data_weekday.append(fats.filter(afatlink__afattime__week_day=i).count())

    data_weekday = [
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        data_weekday,
        [get_random_rgba_color()],
    ]

    # Corp list
    corps = {}

    for corp in corporations:
        c_fats = fats.filter(character__corporation_id=corp.corporation_id).count()
        avg = c_fats / corp.member_count
        corps[corp] = (corp.corporation_id, c_fats, round(avg, 2))

    corps = OrderedDict(sorted(corps.items(), key=lambda x: x[1][2], reverse=True))

    context = {
        "alliance": alliance_name,
        "ally": ally,
        "month": month,
        "month_current": datetime.now().month,
        "month_prev": int(month) - 1,
        "month_next": int(month) + 1,
        "year": year,
        "year_current": datetime.now().year,
        "year_prev": int(year) - 1,
        "year_next": int(year) + 1,
        "data_stacked": data_stacked,
        "data_avgs": data_avgs,
        "data_time": data_time,
        "data_weekday": data_weekday,
        "corps": corps,
        "data_ship_type": data_ship_type,
    }

    logger.info(
        (
            "Alliance statistics for {alliance_name} ({month} {year}) called by {user}"
        ).format(
            alliance_name=alliance_name,
            month=calendar.month_name[int(month)],
            year=year,
            user=request.user,
        )
    )

    return render(request, "afat/statistics_alliance.html", context)
