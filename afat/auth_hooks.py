# -*- coding: utf-8 -*-
from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from django.utils.translation import ugettext_lazy as _

from . import urls


@hooks.register("menu_item_hook")
def register_menu():
    return MenuItemHook(
        _("Fleet Activity Tracking"),
        "fas fa-space-shuttle fa-fw",
        "afat:afat_view",
        navactive=["afat:"],
    )


@hooks.register("url_hook")
def register_url():
    return UrlHook(urls, "afat", r"^afat/")
