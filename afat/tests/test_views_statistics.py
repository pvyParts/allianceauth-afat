import datetime as dt

from pytz import utc

from django.test import TestCase

from allianceauth.eveonline.models import EveCharacter
from app_utils.testing import add_character_to_user, create_user_from_evecharacter

from ..models import AFat, AFatLink
from ..views.statistics import _calculate_year_stats
from .fixtures.load_allianceauth import load_allianceauth
from .fixtures.utils import RequestStub

MODULE_PATH = "afat.views.statistics"


def response_content_to_str(response) -> str:
    return response.content.decode(response.charset)


class TestStatistics(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        load_allianceauth()
        # given
        cls.character_1001 = EveCharacter.objects.get(character_id=1001)
        cls.character_1002 = EveCharacter.objects.get(character_id=1002)
        cls.character_1101 = EveCharacter.objects.get(character_id=1101)
        cls.user, _ = create_user_from_evecharacter(
            cls.character_1001.character_id, permissions=["afat.basic_access"]
        )
        add_character_to_user(cls.user, cls.character_1101)
        create_user_from_evecharacter(cls.character_1002.character_id)

    def test_should_only_show_my_chars_and_only_those_with_fat_links(self):
        # given
        afat_link_april_1 = AFatLink.objects.create(
            fleet="April Fleet 1",
            hash="1231",
            creator=self.user,
            character=self.character_1001,
            afattime=dt.datetime(2020, 4, 1, tzinfo=utc),
        )
        afat_link_april_2 = AFatLink.objects.create(
            fleet="April Fleet 2",
            hash="1232",
            creator=self.user,
            character=self.character_1001,
            afattime=dt.datetime(2020, 4, 15, tzinfo=utc),
        )
        afat_link_september = AFatLink.objects.create(
            fleet="September Fleet",
            hash="1233",
            creator=self.user,
            character=self.character_1001,
            afattime=dt.datetime(2020, 9, 1, tzinfo=utc),
        )
        AFat.objects.create(character=self.character_1101, afatlink=afat_link_april_1)
        AFat.objects.create(character=self.character_1101, afatlink=afat_link_april_2)
        AFat.objects.create(character=self.character_1001, afatlink=afat_link_april_1)
        AFat.objects.create(character=self.character_1001, afatlink=afat_link_september)
        # when
        result = _calculate_year_stats(RequestStub(self.user), 2020)
        # then
        self.assertListEqual(
            result,
            [("Bruce Wayne", {"4": 1, "9": 1}, 1001), ("Lex Luther", {"4": 2}, 1101)],
        )
