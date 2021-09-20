"""
Test afat helpers
"""

from django.test import TestCase
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ..helper.fatlinks import get_esi_fleet_information_by_user
from ..models import AFatLink, get_hash_on_save
from .fixtures.load_allianceauth import load_allianceauth

MODULE_PATH = "afat.views.fatlinks"


class TestFatlinksView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        # given
        cls.character_1001 = EveCharacter.objects.get(character_id=1001)
        cls.character_1002 = EveCharacter.objects.get(character_id=1002)
        cls.character_1003 = EveCharacter.objects.get(character_id=1003)
        cls.character_1004 = EveCharacter.objects.get(character_id=1004)
        cls.character_1005 = EveCharacter.objects.get(character_id=1005)
        cls.character_1101 = EveCharacter.objects.get(character_id=1101)

        cls.user_with_add_fatlink, _ = create_user_from_evecharacter(
            cls.character_1001.character_id,
            permissions=["afat.basic_access", "afat.add_fatlink"],
        )

        add_character_to_user(cls.user_with_add_fatlink, cls.character_1101)

    def test_helper_get_esi_fleet_information_by_user(self):
        fatlink_hash_fleet_1 = get_hash_on_save()
        # given
        fatlink_1 = AFatLink.objects.create(
            afattime=timezone.now(),
            fleet="April Fleet 1",
            creator=self.user_with_add_fatlink,
            character=self.character_1001,
            hash=fatlink_hash_fleet_1,
            is_esilink=True,
            is_registered_on_esi=True,
            esi_fleet_id="3726458287",
        )

        fatlink_hash_fleet_2 = get_hash_on_save()
        fatlink_2 = AFatLink.objects.create(
            afattime=timezone.now(),
            fleet="April Fleet 2",
            creator=self.user_with_add_fatlink,
            character=self.character_1101,
            hash=fatlink_hash_fleet_2,
            is_esilink=True,
            is_registered_on_esi=True,
            esi_fleet_id="372645827",
        )

        self.client.force_login(self.user_with_add_fatlink)

        # when
        response = get_esi_fleet_information_by_user(user=self.user_with_add_fatlink)

        # then
        self.assertDictEqual(
            response,
            {
                "has_open_esi_fleets": True,
                "open_esi_fleets_list": [fatlink_1, fatlink_2],
            },
        )
