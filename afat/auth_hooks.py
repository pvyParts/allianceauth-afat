# -*- coding: utf-8 -*-

"""
auth hooks
"""

from django.utils.translation import ugettext_lazy as _

from afat import urls

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook


@hooks.register("menu_item_hook")
def register_menu():
    """
    register our menu
    :return:
    """
    return MenuItemHook(
        _("Fleet Activity Tracking"),
        "fas fa-space-shuttle fa-fw",
        "afat:afat_view",
        navactive=["afat:"],
    )


@hooks.register("url_hook")
def register_url():
    """
    register our menu link
    :return:
    """
    return UrlHook(urls, "afat", r"^fleetactivitytracking/")
