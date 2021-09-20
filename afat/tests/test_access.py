"""
Test access to the afat module
"""

from django.test import TestCase
from django.urls import reverse

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from .fixtures.load_allianceauth import load_allianceauth

MODULE_PATH = "afat.views.statistics"


class TestAccesss(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        # given
        cls.character_1001 = EveCharacter.objects.get(character_id=1001)
        cls.character_1002 = EveCharacter.objects.get(character_id=1002)
        cls.character_1003 = EveCharacter.objects.get(character_id=1003)
        cls.character_1101 = EveCharacter.objects.get(character_id=1101)

        cls.user_without_access, _ = create_user_from_evecharacter(
            cls.character_1001.character_id
        )

        cls.user_with_basic_access, _ = create_user_from_evecharacter(
            cls.character_1002.character_id, permissions=["afat.basic_access"]
        )

        add_character_to_user(cls.user_with_basic_access, cls.character_1101)

        cls.user_with_manage_afat, _ = create_user_from_evecharacter(
            cls.character_1003.character_id,
            permissions=["afat.basic_access", "afat.manage_afat"],
        )

    def test_should_show_afat_dashboard_for_user_with_basic_access(self):
        # given
        self.client.force_login(self.user_with_basic_access)

        # when
        res = self.client.get(reverse("afat:dashboard"))

        # then
        self.assertEqual(res.status_code, 200)

    def test_should_not_show_afat_dashboard_for_user_without_access(self):
        # given
        self.client.force_login(self.user_without_access)

        # when
        res = self.client.get(reverse("afat:dashboard"))

        # then
        self.assertNotEqual(res.status_code, 200)
        self.assertEqual(res.status_code, 302)
