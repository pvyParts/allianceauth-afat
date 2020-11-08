# -*- coding: utf-8 -*-

"""
tasks
"""

from celery import shared_task

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


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


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

    logger.info("Processing information for character %s", character.pk)

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
    sol_id = char["solar_system_id"]
    ship_id = char["ship_type_id"]

    solar_system = esi.client.Universe.get_universe_systems_system_id(
        system_id=sol_id
    ).result()
    ship = esi.client.Universe.get_universe_types_type_id(type_id=ship_id).result()

    sol_name = solar_system["name"]
    ship_name = ship["name"]
    character = get_or_create_char(character_id=char_id)
    AFat(
        afatlink_id=link.pk, character=character, system=sol_name, shiptype=ship_name
    ).save()

    logger.info("Processing information for character with ID %s", character)
