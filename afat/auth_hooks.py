# -*- coding: utf-8 -*-

"""
auth hooks
"""

from afat import urls
from afat.app_settings import AFAT_APP_NAME, AFAT_BASE_URL

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook


class AaAfatMenuItem(MenuItemHook):  # pylint: disable=too-few-public-methods
    """ This class ensures only authorized users will see the menu entry """

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            AFAT_APP_NAME,
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

    return UrlHook(urls, "afat", r"^{base_url}/".format(base_url=AFAT_BASE_URL))
