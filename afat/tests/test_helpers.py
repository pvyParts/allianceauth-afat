"""
Test afat helpers
"""
from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ..helper.fatlinks import get_esi_fleet_information_by_user
from ..helper.time import get_time_delta
from ..helper.views_helper import convert_fatlinks_to_dict
from ..models import AFat, AFatLink, AFatLinkType, get_hash_on_save
from ..utils import get_main_character_from_user
from .fixtures.load_allianceauth import load_allianceauth

MODULE_PATH = "afat.views.fatlinks"


class TestHelpers(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()

        cls.factory = RequestFactory()

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

        cls.user_with_manage_afat, _ = create_user_from_evecharacter(
            cls.character_1002.character_id,
            permissions=["afat.basic_access", "afat.manage_afat"],
        )

        add_character_to_user(cls.user_with_add_fatlink, cls.character_1003)

    def test_helper_get_esi_fleet_information_by_user(self):
        # given
        fatlink_hash_fleet_1 = get_hash_on_save()
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

    def test_helper_get_time_delta(self):
        # given
        duration = 1812345
        now = timezone.now()
        expires = timedelta(minutes=duration) + now

        self.client.force_login(self.user_with_add_fatlink)

        # when
        total = get_time_delta(now, expires)
        years = get_time_delta(now, expires, "years")
        days = get_time_delta(now, expires, "days")
        hours = get_time_delta(now, expires, "hours")
        minutes = get_time_delta(now, expires, "minutes")
        seconds = get_time_delta(now, expires, "seconds")

        # then
        self.assertEqual(total, "3 years, 163 days, 13 hours, 45 minutes and 0 seconds")
        self.assertEqual(years, 3)
        self.assertEqual(days, 1258)
        self.assertEqual(hours, 30205)
        self.assertEqual(minutes, 1812345)
        self.assertEqual(seconds, 108740700)

    def test_helper_convert_fatlinks_to_dict(self):
        # given
        self.client.force_login(self.user_with_manage_afat)
        request = self.factory.get(reverse("afat:dashboard_ajax_get_recent_fatlinks"))
        request.user = self.user_with_manage_afat

        fatlink_hash_fleet_1 = get_hash_on_save()
        fatlink_1_created = AFatLink.objects.create(
            afattime=timezone.now(),
            fleet="April Fleet 1",
            creator=self.user_with_manage_afat,
            character=self.character_1001,
            hash=fatlink_hash_fleet_1,
            is_esilink=True,
            is_registered_on_esi=True,
            esi_fleet_id="3726458287",
        )
        AFat.objects.create(
            character=self.character_1101, afatlink=fatlink_1_created, shiptype="Omen"
        )

        fatlink_type_cta = AFatLinkType.objects.create(name="CTA")
        fatlink_hash_fleet_2 = get_hash_on_save()
        fatlink_2_created = AFatLink.objects.create(
            afattime=timezone.now(),
            fleet="April Fleet 2",
            creator=self.user_with_add_fatlink,
            character=self.character_1101,
            hash=fatlink_hash_fleet_2,
            link_type=fatlink_type_cta,
        )
        AFat.objects.create(
            character=self.character_1001, afatlink=fatlink_2_created, shiptype="Omen"
        )

        # when
        fatlink_1 = (
            AFatLink.objects.select_related_default()
            .annotate_afats_count()
            .get(hash=fatlink_hash_fleet_1)
        )

        fatlink_2 = (
            AFatLink.objects.select_related_default()
            .annotate_afats_count()
            .get(hash=fatlink_hash_fleet_2)
        )

        result_1 = convert_fatlinks_to_dict(request=request, fatlink=fatlink_1)
        result_2 = convert_fatlinks_to_dict(request=request, fatlink=fatlink_2)

        # then
        fleet_time_1 = fatlink_1.afattime
        fleet_time_timestamp_1 = fleet_time_1.timestamp()
        creator_main_character_1 = get_main_character_from_user(user=fatlink_1.creator)
        self.assertDictEqual(
            result_1,
            {
                "pk": fatlink_1.pk,
                "fleet_name": (
                    'April Fleet 1<span class="label label-default '
                    "afat-label afat-label-via-esi "
                    'afat-label-active-esi-fleet">via ESI</span>'
                ),
                "creator_name": creator_main_character_1,
                "fleet_type": "",
                "fleet_time": {
                    "time": fleet_time_1,
                    "timestamp": fleet_time_timestamp_1,
                },
                "fats_number": fatlink_1.afats_count,
                "hash": fatlink_1.hash,
                "is_esilink": True,
                "esi_fleet_id": 3726458287,
                "is_registered_on_esi": True,
                "actions": (
                    f'<a class="btn btn-afat-action btn-primary btn-sm" '
                    f'style="margin-left: 0.25rem;" title="Clicking here will '
                    f"stop the automatic tracking through ESI for this fleet "
                    f'and close the associated FAT link." data-toggle="modal" '
                    f'data-target="#cancelEsiFleetModal" '
                    f'data-url="/fleet-activity-tracking/fatlink/'
                    f'{fatlink_1.hash}/stop-esi-tracking/" '
                    f'data-body-text="<p>Are you sure you want to close ESI '
                    f'fleet with ID 3726458287 from Bruce Wayne?</p>" '
                    f'data-confirm-text="Stop Tracking"><i class="fas '
                    f'fa-times"></i></a><a class="btn btn-afat-action btn-info '
                    f'btn-sm" href="/fleet-activity-tracking/fatlink/'
                    f'{fatlink_1.hash}/details/"><span class="fas '
                    f'fa-eye"></span></a><a class="btn btn-afat-action '
                    f'btn-danger btn-sm" data-toggle="modal" '
                    f'data-target="#deleteFatLinkModal" '
                    f'data-url="/fleet-activity-tracking/fatlink/'
                    f'{fatlink_1.hash}/delete/" '
                    f'data-confirm-text="Delete"data-body-text="<p>Are you '
                    f"sure you want to delete FAT link April Fleet "
                    f'1?</p>"><span class="glyphicon '
                    f'glyphicon-trash"></span></a>'
                ),
                "via_esi": "Yes",
            },
        )

        fleet_time_2 = fatlink_2.afattime
        fleet_time_timestamp_2 = fleet_time_2.timestamp()
        creator_main_character_2 = get_main_character_from_user(user=fatlink_2.creator)
        self.assertDictEqual(
            result_2,
            {
                "pk": fatlink_2.pk,
                "fleet_name": "April Fleet 2",
                "creator_name": creator_main_character_2,
                "fleet_type": "CTA",
                "fleet_time": {
                    "time": fleet_time_2,
                    "timestamp": fleet_time_timestamp_2,
                },
                "fats_number": fatlink_2.afats_count,
                "hash": fatlink_2.hash,
                "is_esilink": False,
                "esi_fleet_id": None,
                "is_registered_on_esi": False,
                "actions": (
                    f'<a class="btn btn-afat-action btn-info btn-sm" '
                    f'href="/fleet-activity-tracki'
                    f'ng/fatlink/{fatlink_2.hash}/details/"><span class="fas '
                    f'fa-eye"></span></a><a class="btn btn-afat-action '
                    f'btn-danger btn-sm" data-toggle="modal" '
                    f'data-target="#deleteFatLinkModal" '
                    f'data-url="/fleet-activity-tracking/fatlink/'
                    f'{fatlink_2.hash}/delete/" '
                    f'data-confirm-text="Delete"data-body-text="<p>Are you '
                    f"sure you want to delete FAT link April Fleet "
                    f'2?</p>"><span class="glyphicon '
                    f'glyphicon-trash"></span></a>'
                ),
                "via_esi": "No",
            },
        )
