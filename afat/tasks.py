# -*- coding: utf-8 -*-

"""
tasks
"""

from bravado.exception import (
    HTTPBadGateway,
    HTTPGatewayTimeout,
    HTTPNotFound,
    HTTPServiceUnavailable,
)

from celery import shared_task

from django.core.cache import cache

from esi.models import Token

from afat import __title__
from afat.models import AFat, AFatLink
from afat.providers import esi
from afat.utils import LoggerAddTag

from allianceauth.eveonline.models import (
    EveAllianceInfo,
    EveCharacter,
    EveCorporationInfo,
)
from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


DEFAULT_TASK_PRIORITY = 6

ESI_ERROR_LIMIT = 50
ESI_TIMEOUT_ONCE_ERROR_LIMIT_REACHED = 60
ESI_MAX_RETRIES = 3

CACHE_KEY_FLEET_CHANGED_ERROR = (
    "afat_task_update_esi_fatlinks_error_counter_fleet_changed_"
)
CACHE_KEY_NOT_IN_FLEET_ERROR = (
    "afat_task_update_esi_fatlinks_error_counter_not_in_fleet_"
)
CACHE_KEY_NO_FLEET_ERROR = "afat_task_update_esi_fatlinks_error_counter_no_fleet_"
CACHE_KEY_NO_FLEETBOSS_ERROR = (
    "afat_task_update_esi_fatlinks_error_counter_no_fleetboss_"
)
CACHE_MAX_ERROR_COUNT = 3

# params for all tasks
TASK_DEFAULT_KWARGS = {
    "time_limit": 120,  # stop after 2 minutes
}

# params for tasks that make ESI calls
TASK_ESI_KWARGS = {
    **TASK_DEFAULT_KWARGS,
    **{
        "autoretry_for": (
            OSError,
            HTTPBadGateway,
            HTTPGatewayTimeout,
            HTTPServiceUnavailable,
        ),
        "retry_kwargs": {"max_retries": ESI_MAX_RETRIES},
        "retry_backoff": True,
    },
}


class NoDataError(Exception):
    """
    NoDataError
    """

    def __init__(self, msg):
        Exception.__init__(self, msg)


def get_or_create_char(name: str = None, character_id: int = None):
    """
    This function takes a name or id of a character and checks
    to see if the character already exists.
    If the character does not already exist, it will create the
    character object, and if needed the corp/alliance objects as well.
    :param name: str (optional)
    :param character_id: int (optional)
    :returns character: EveCharacter
    """

    if name:
        # If a name is passed we have to check it on ESI
        result = esi.client.Search.get_search(
            categories=["character"], search=name, strict=True
        ).result()

        if "character" not in result:
            return None

        character_id = result["character"][0]
        eve_character = EveCharacter.objects.filter(character_id=character_id)
    elif character_id:
        # If an ID is passed we can just check the db for it.
        eve_character = EveCharacter.objects.filter(character_id=character_id)
    elif not name and not character_id:
        raise NoDataError("No character name or character id provided.")

    if len(eve_character) == 0:
        # Create Character
        character = EveCharacter.objects.create_character(character_id)
        character = EveCharacter.objects.get(pk=character.pk)

        # Make corp and alliance info objects for future sane
        if character.alliance_id is not None:
            test = EveAllianceInfo.objects.filter(alliance_id=character.alliance_id)

            if len(test) == 0:
                EveAllianceInfo.objects.create_alliance(character.alliance_id)
        else:
            test = EveCorporationInfo.objects.filter(
                corporation_id=character.corporation_id
            )

            if len(test) == 0:
                EveCorporationInfo.objects.create_corporation(character.corporation_id)

    else:
        character = eve_character[0]

    logger.info("Processing information for {character}".format(character=character))

    return character


@shared_task
def process_fats(data_list, data_source, fatlink_hash):
    """
    Due to the large possible size of fatlists,
    this process will be scheduled in order to process esi data
    and possible other sources in the future.
    :param data_list: the list of character info to be processed.
    :param data_source: the source type (only "esi" for now)
    :param fatlink_hash: the hash from the fat link.
    :return:
    """

    logger.info("Processing FAT %s", fatlink_hash)

    if data_source == "esi":
        for char in data_list:
            process_character.delay(char, fatlink_hash)


@shared_task
def process_line(line, type_, fatlink_hash):
    """
    process_line
    processing every single character on its own
    :param line:
    :param type_:
    :param fatlink_hash:
    :return:
    """

    link = AFatLink.objects.get(hash=fatlink_hash)

    if type_ == "comp":
        character = get_or_create_char(name=line[0].strip(" "))
        system = line[1].strip(" (Docked)")
        shiptype = line[2]

        if character is not None:
            AFat(
                afatlink_id=link.pk,
                character=character,
                system=system,
                shiptype=shiptype,
            ).save()
    else:
        character = get_or_create_char(name=line.strip(" "))

        if character is not None:
            AFat(afatlink_id=link.pk, character=character).save()


@shared_task
def process_character(char, fatlink_hash):
    """
    process_character
    :param char:
    :param fatlink_hash:
    :return:
    """

    link = AFatLink.objects.get(hash=fatlink_hash)
    char_id = char["character_id"]
    character = get_or_create_char(character_id=char_id)

    # only process if the character is not already registered for this FAT
    if AFat.objects.filter(character=character, afatlink_id=link.pk).exists() is False:
        solar_system_id = char["solar_system_id"]
        ship_type_id = char["ship_type_id"]

        solar_system = esi.client.Universe.get_universe_systems_system_id(
            system_id=solar_system_id
        ).result()
        ship = esi.client.Universe.get_universe_types_type_id(
            type_id=ship_type_id
        ).result()

        solar_system_name = solar_system["name"]
        ship_name = ship["name"]

        logger.info(
            "New Pilot: Adding {character_name} in {system_name} flying a {ship_name} "
            "to FAT link {fatlink_hash}".format(
                character_name=character,
                system_name=solar_system_name,
                ship_name=ship_name,
                fatlink_hash=fatlink_hash,
            )
        )

        AFat(
            afatlink_id=link.pk,
            character=character,
            system=solar_system_name,
            shiptype=ship_name,
        ).save()
    else:
        logger.info(
            "{character} is already registered with FAT link {fatlink_hash}".format(
                character=character, fatlink_hash=fatlink_hash
            )
        )


def close_esi_fleet(fatlink: AFatLink, reason: str) -> None:
    """
    Closing ESI fleet
    :param fatlink:
    :param reason:
    """

    logger.info(
        "Closing ESI FAT with hash {fatlink_hash}. Reason: {reason}".format(
            fatlink_hash=fatlink.hash, reason=reason
        )
    )

    fatlink.is_registered_on_esi = False
    fatlink.save()


def esi_fatlinks_error_handling(
    cache_key: str, fatlink: AFatLink, logger_message: str
) -> None:
    """
    ESI error handling
    :param cache_key:
    :param fatlink:
    :param logger_message:
    """

    if int(cache.get(cache_key + fatlink.hash)) < CACHE_MAX_ERROR_COUNT:
        error_count = int(cache.get(cache_key + fatlink.hash))

        error_count += 1

        logger.info(
            '"{logger_message}" Error Count: {error_count}.'.format(
                logger_message=logger_message, error_count=error_count
            )
        )

        cache.set(
            cache_key + fatlink.hash,
            str(error_count),
            75,
        )
    else:
        close_esi_fleet(fatlink=fatlink, reason=logger_message)


@shared_task(**{**TASK_ESI_KWARGS}, **{"base": QueueOnce})
def update_esi_fatlinks() -> None:
    """
    checking ESI fat links for changes
    """

    required_scopes = ["esi-fleets.read_fleet.v1"]

    try:
        esi_fatlinks = AFatLink.objects.filter(
            is_esilink=True, is_registered_on_esi=True
        )

        for fatlink in esi_fatlinks:
            if cache.get(CACHE_KEY_FLEET_CHANGED_ERROR + fatlink.hash) is None:
                cache.set(CACHE_KEY_FLEET_CHANGED_ERROR + fatlink.hash, "0", 75)

            if cache.get(CACHE_KEY_NO_FLEETBOSS_ERROR + fatlink.hash) is None:
                cache.set(CACHE_KEY_NO_FLEETBOSS_ERROR + fatlink.hash, "0", 75)

            if cache.get(CACHE_KEY_NO_FLEET_ERROR + fatlink.hash) is None:
                cache.set(CACHE_KEY_NO_FLEET_ERROR + fatlink.hash, "0", 75)

            if cache.get(CACHE_KEY_NOT_IN_FLEET_ERROR + fatlink.hash) is None:
                cache.set(CACHE_KEY_NOT_IN_FLEET_ERROR + fatlink.hash, "0", 75)

            logger.info("Processing information for ESI FAT with hash %s", fatlink.hash)

            if fatlink.creator.profile.main_character is not None:
                # Check if there is a fleet
                try:
                    fleet_commander_id = fatlink.character.character_id
                    esi_token = Token.get_token(fleet_commander_id, required_scopes)

                    fleet_from_esi = (
                        esi.client.Fleets.get_characters_character_id_fleet(
                            character_id=fleet_commander_id,
                            token=esi_token.valid_access_token(),
                        ).result()
                    )

                    if fatlink.esi_fleet_id == fleet_from_esi["fleet_id"]:
                        # Check if we deal with the fleet boss here
                        try:
                            esi_fleet_member = (
                                esi.client.Fleets.get_fleets_fleet_id_members(
                                    fleet_id=fleet_from_esi["fleet_id"],
                                    token=esi_token.valid_access_token(),
                                ).result()
                            )

                            # process fleet members
                            process_fats.delay(
                                data_list=esi_fleet_member,
                                data_source="esi",
                                fatlink_hash=fatlink.hash,
                            )
                        except Exception:
                            esi_fatlinks_error_handling(
                                cache_key=CACHE_KEY_NO_FLEETBOSS_ERROR,
                                fatlink=fatlink,
                                logger_message="FC is no longer the fleet boss.",
                            )

                    else:
                        esi_fatlinks_error_handling(
                            cache_key=CACHE_KEY_FLEET_CHANGED_ERROR,
                            fatlink=fatlink,
                            logger_message="FC switched to another fleet",
                        )

                except HTTPNotFound:
                    esi_fatlinks_error_handling(
                        cache_key=CACHE_KEY_NOT_IN_FLEET_ERROR,
                        fatlink=fatlink,
                        logger_message=(
                            "FC is not in the registered fleet anymore or "
                            "fleet is no longer available."
                        ),
                    )

                except Exception:
                    esi_fatlinks_error_handling(
                        cache_key=CACHE_KEY_NO_FLEET_ERROR,
                        fatlink=fatlink,
                        logger_message="Registered fleet is no longer available.",
                    )

            else:
                close_esi_fleet(fatlink=fatlink, reason="No fatlink creator available.")

    except AFatLink.DoesNotExist:
        pass
