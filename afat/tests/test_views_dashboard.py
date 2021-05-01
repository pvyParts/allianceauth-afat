from django.test import RequestFactory, TestCase
from django.urls import reverse

from allianceauth.tests.auth_utils import AuthUtils

from ..views.dashboard import overview

MODULE_PATH = "afat.views.dashboard"


class TestDashboard(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.factory = RequestFactory()
        cls.user = AuthUtils.create_user("Bruce Wayne")

    def test_should_only_show_valid_characters(self):
        # given
        request = self.factory.get(reverse("moonmining:extractions"))
        request.user = self.user
