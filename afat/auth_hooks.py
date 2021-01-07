# -*- coding: utf-8 -*-

"""
auth hooks
"""

from django.utils.translation import ugettext_lazy as _

from afat import urls

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook


class AaAfatMenuItem(MenuItemHook):  # pylint: disable=too-few-public-methods
    """ This class ensures only authorized users will see the menu entry """

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _("Fleet Activity Tracking"),
            "fas fa-space-shuttle fa-fw",
            "afat:dashboard",
            navactive=["afat:"],
        )

    def render(self, request):
        """
        only if the user has access to this app
        :param request:
        :return:
        """

        if request.user.has_perm("afat.basic_access"):
            return MenuItemHook.render(self, request)

        return ""


@hooks.register("menu_item_hook")
def register_menu():
    """
    register our menu
    :return:
    """

    return AaAfatMenuItem()


@hooks.register("url_hook")
def register_url():
    """
    register our menu link
    :return:
    """

    return UrlHook(urls, "afat", r"^fleetactivitytracking/")
