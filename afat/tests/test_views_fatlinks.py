"""
Test fatlinks views
"""

import datetime as dt

from pytz import utc

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import create_user_from_evecharacter

from ..models import AFat, AFatLink, AFatLinkType
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

        cls.user_without_access, _ = create_user_from_evecharacter(
            cls.character_1001.character_id
        )

        cls.user_with_basic_access, _ = create_user_from_evecharacter(
            cls.character_1002.character_id, permissions=["afat.basic_access"]
        )

        cls.user_with_manage_afat, _ = create_user_from_evecharacter(
            cls.character_1003.character_id,
            permissions=["afat.basic_access", "afat.manage_afat"],
        )

        cls.user_with_add_fatlink, _ = create_user_from_evecharacter(
            cls.character_1004.character_id,
            permissions=["afat.basic_access", "afat.add_fatlink"],
        )

        # cls.afat_link_type_cta = AFatLinkType.objects.create(name="CTA")
        # cls.afat_link_type_stratop = AFatLinkType.objects.create(name="Strat OP")

        # Generate some FAT links and FATs
        cls.afat_link_april_1 = AFatLink.objects.create(
            fleet="April Fleet 1",
            hash="1231",
            creator=cls.user_with_basic_access,
            character=cls.character_1001,
            afattime=dt.datetime(2020, 4, 1, tzinfo=utc),
        )
        cls.afat_link_april_2 = AFatLink.objects.create(
            fleet="April Fleet 2",
            hash="1232",
            creator=cls.user_with_basic_access,
            character=cls.character_1001,
            afattime=dt.datetime(2020, 4, 15, tzinfo=utc),
        )
        cls.afat_link_september = AFatLink.objects.create(
            fleet="September Fleet",
            hash="1233",
            creator=cls.user_with_basic_access,
            character=cls.character_1001,
            afattime=dt.datetime(2020, 9, 1, tzinfo=utc),
        )
        cls.afat_link_september_no_fats = AFatLink.objects.create(
            fleet="September Fleet 2",
            hash="1234",
            creator=cls.user_with_basic_access,
            character=cls.character_1001,
            afattime=dt.datetime(2020, 9, 1, tzinfo=utc),
        )

        AFat.objects.create(
            character=cls.character_1101,
            afatlink=cls.afat_link_april_1,
            shiptype="Omen",
        )
        AFat.objects.create(
            character=cls.character_1001,
            afatlink=cls.afat_link_april_1,
            shiptype="Omen",
        )
        AFat.objects.create(
            character=cls.character_1002,
            afatlink=cls.afat_link_april_1,
            shiptype="Omen",
        )
        AFat.objects.create(
            character=cls.character_1003,
            afatlink=cls.afat_link_april_1,
            shiptype="Omen",
        )
        AFat.objects.create(
            character=cls.character_1004,
            afatlink=cls.afat_link_april_1,
            shiptype="Omen",
        )
        AFat.objects.create(
            character=cls.character_1005,
            afatlink=cls.afat_link_april_1,
            shiptype="Omen",
        )

        AFat.objects.create(
            character=cls.character_1001,
            afatlink=cls.afat_link_april_2,
            shiptype="Omen",
        )
        AFat.objects.create(
            character=cls.character_1004,
            afatlink=cls.afat_link_april_2,
            shiptype="Thorax",
        )
        AFat.objects.create(
            character=cls.character_1002,
            afatlink=cls.afat_link_april_2,
            shiptype="Thorax",
        )
        AFat.objects.create(
            character=cls.character_1003,
            afatlink=cls.afat_link_april_2,
            shiptype="Omen",
        )

        AFat.objects.create(
            character=cls.character_1001,
            afatlink=cls.afat_link_september,
            shiptype="Omen",
        )
        AFat.objects.create(
            character=cls.character_1004,
            afatlink=cls.afat_link_september,
            shiptype="Guardian",
        )
        AFat.objects.create(
            character=cls.character_1002,
            afatlink=cls.afat_link_september,
            shiptype="Omen",
        )

    def test_should_show_fatlnks_overview(self):
        # given
        self.client.force_login(self.user_with_basic_access)

        # when
        url = reverse("afat:fatlinks_overview")
        res = self.client.get(url)

        # then
        self.assertEqual(res.status_code, 200)

    def test_should_show_fatlnks_overview_with_year(self):
        # given
        self.client.force_login(self.user_with_basic_access)

        # when
        url = reverse("afat:fatlinks_overview", kwargs={"year": 2020})
        res = self.client.get(url)

        # then
        self.assertEqual(res.status_code, 200)

    def test_should_show_add_fatlink_for_user_with_manage_afat(self):
        # given
        AFatLinkType.objects.create(name="CTA")

        self.client.force_login(self.user_with_manage_afat)

        # when
        url = reverse("afat:fatlinks_add_fatlink")
        res = self.client.get(url)

        # then
        self.assertEqual(res.status_code, 200)

    def test_should_show_add_fatlink_for_user_with_add_fatlinkt(self):
        # given
        self.client.force_login(self.user_with_add_fatlink)

        # when
        url = reverse("afat:fatlinks_add_fatlink")
        res = self.client.get(url)

        # then
        self.assertEqual(res.status_code, 200)

    def test_should_show_fatlink_details_for_user_with_manage_afat(self):
        # given
        self.client.force_login(self.user_with_manage_afat)

        # when
        url = reverse(
            "afat:fatlinks_details_fatlink",
            kwargs={"fatlink_hash": self.afat_link_april_1.hash},
        )
        res = self.client.get(url)

        # then
        self.assertEqual(res.status_code, 200)

    def test_should_show_fatlink_details_for_user_with_add_fatlinkt(self):
        # given
        self.client.force_login(self.user_with_add_fatlink)

        # when
        url = reverse(
            "afat:fatlinks_details_fatlink",
            kwargs={"fatlink_hash": self.afat_link_april_1.hash},
        )
        res = self.client.get(url)

        # then
        self.assertEqual(res.status_code, 200)

    def test_should_not_show_fatlink_details_for_non_existing_fatlink(self):
        # given
        self.client.force_login(self.user_with_manage_afat)

        # when
        url = reverse(
            "afat:fatlinks_details_fatlink",
            kwargs={"fatlink_hash": "foobarsson"},
        )
        res = self.client.get(url)

        # then
        self.assertNotEqual(res.status_code, 200)
        self.assertEqual(res.status_code, 302)

        messages = list(get_messages(res.wsgi_request))

        self.assertRaises(AFatLink.DoesNotExist)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "<h4>Warning!</h4><p>The hash provided is not valid.</p>",
        )

    def test_should_not_show_fatlink_details_and_redirect_to_dashboard(self):
        # given
        self.client.force_login(self.user_with_manage_afat)

        # when
        url = "/fleet-activity-tracking/fatlink/"
        res = self.client.get(url)

        # then
        self.assertNotEqual(res.status_code, 200)
        self.assertEqual(res.status_code, 302)

        messages = list(get_messages(res.wsgi_request))

        self.assertRaises(AFatLink.DoesNotExist)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Page does not exist. If you believe this is in error please contact the "
            "administrators. (404 Page Not Found)",
        )
