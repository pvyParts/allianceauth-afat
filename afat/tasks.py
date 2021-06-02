"""
Tasks
"""

from datetime import timedelta

from bravado.exception import (
    HTTPBadGateway,
    HTTPGatewayTimeout,
    HTTPNotFound,
    HTTPServiceUnavailable,
)
from celery import shared_task

from django.core.cache import cache
from django.utils import timezone

from allianceauth.services.hooks import get_extension_logger
from allianceauth.services.tasks import QueueOnce
from app_utils.logging import LoggerAddTag
from esi.models import Token

from afat import __title__
from afat.app_settings import AFAT_DEFAULT_LOG_DURATION
from afat.models import AFat, AFatLink, AFatLog
from afat.providers import esi
from afat.utils import get_or_create_character

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

# Params for all tasks
TASK_DEFAULT_KWARGS = {
    "time_limit": 120,  # Stop after 2 minutes
}

# Params for tasks that make ESI calls
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


@shared_task
def process_fats(data_list, data_source, fatlink_hash):
    """
    Due to the large possible size of fatlists,
    this process will be scheduled to process esi data
    and possible other sources in the future.
    :param data_list:
    :type data_list:
    :param data_source:
    :type data_source:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    if data_source == "esi":
        logger.info(
            f'Valid fleet for FAT link hash "{fatlink_hash}" found '
            f"registered via ESI, checking for new pilots"
        )

        for char in data_list:
            process_character.delay(char, fatlink_hash)


@shared_task
def process_character(char, fatlink_hash):
    """
    Process character
    :param char:
    :type char:
    :param fatlink_hash:
    :type fatlink_hash:
    :return:
    :rtype:
    """

    link = AFatLink.objects.get(hash=fatlink_hash)
    char_id = char["character_id"]
    character = get_or_create_character(character_id=char_id)

    # Only process if the character is not already registered for this FAT
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
            'to FAT link "{fatlink_hash}"'.format(
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


def close_esi_fleet(fatlink: AFatLink, reason: str) -> None:
    """
    Closing ESI fleet
    :param fatlink:
    :type fatlink:
    :param reason:
    :type reason:
    :return:
    :rtype:
    """

    logger.info(
        'Closing ESI FAT link with hash "{fatlink_hash}". Reason: {reason}'.format(
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
    :type cache_key:
    :param fatlink:
    :type fatlink:
    :param logger_message:
    :type logger_message:
    :return:
    :rtype:
    """

    if int(cache.get(cache_key + fatlink.hash)) < CACHE_MAX_ERROR_COUNT:
        error_count = int(cache.get(cache_key + fatlink.hash))

        error_count += 1

        logger.info(
            (
                'FAT link "{falink_hash}" Error: "{logger_message}" '
                "({error_count} of {max_count})."
            ).format(
                falink_hash=fatlink.hash,
                logger_message=logger_message,
                error_count=error_count,
                max_count=CACHE_MAX_ERROR_COUNT,
            )
        )

        cache.set(
            cache_key + fatlink.hash,
            str(error_count),
            75,
        )
    else:
        close_esi_fleet(fatlink=fatlink, reason=logger_message)


def initialize_caches(fatlink: AFatLink) -> None:
    """
    Initializing caches
    :param fatlink:
    :type fatlink:
    :return:
    :rtype:
    """

    if cache.get(CACHE_KEY_FLEET_CHANGED_ERROR + fatlink.hash) is None:
        cache.set(CACHE_KEY_FLEET_CHANGED_ERROR + fatlink.hash, "0", 75)

    if cache.get(CACHE_KEY_NO_FLEETBOSS_ERROR + fatlink.hash) is None:
        cache.set(CACHE_KEY_NO_FLEETBOSS_ERROR + fatlink.hash, "0", 75)

    if cache.get(CACHE_KEY_NO_FLEET_ERROR + fatlink.hash) is None:
        cache.set(CACHE_KEY_NO_FLEET_ERROR + fatlink.hash, "0", 75)

    if cache.get(CACHE_KEY_NOT_IN_FLEET_ERROR + fatlink.hash) is None:
        cache.set(CACHE_KEY_NOT_IN_FLEET_ERROR + fatlink.hash, "0", 75)


@shared_task(**{**TASK_ESI_KWARGS}, **{"base": QueueOnce})
def update_esi_fatlinks() -> None:
    """
    Checking ESI fat links for changes
    :return:
    :rtype:
    """

    required_scopes = ["esi-fleets.read_fleet.v1"]

    try:
        esi_fatlinks = AFatLink.objects.select_related_default().filter(
            is_esilink=True, is_registered_on_esi=True
        )

        for fatlink in esi_fatlinks:
            initialize_caches(fatlink=fatlink)

            logger.info(f'Processing ESI FAT link with hash "{fatlink.hash}"')

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

                            # Process fleet members
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


@shared_task
def logrotate():
    """
    Remove logs older than AFAT_DEFAULT_LOG_DURATION
    :return:
    :rtype:
    """

    logger.info(f"Cleaning up logs older than {AFAT_DEFAULT_LOG_DURATION} days")

    AFatLog.objects.filter(
        log_time__lte=timezone.now() - timedelta(days=AFAT_DEFAULT_LOG_DURATION)
    ).delete()
