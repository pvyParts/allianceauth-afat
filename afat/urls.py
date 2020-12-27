# -*- coding: utf-8 -*-

"""
url configuration
"""

from django.conf.urls import url

from afat import views

app_name: str = "afat"

urlpatterns = [
    # dashboard
    url(r"^$", views.dashboard.dashboard, name="dashboard"),
    # stats main page
    url(r"^statistics/$", views.statistics.stats, name="stats"),
    url(r"^statistics/(?P<year>[0-9]+)/$", views.statistics.stats, name="stats"),
    # stats corp
    url(r"^statistics/corporation/$", views.statistics.stats_corp, name="stats_corp"),
    url(
        r"^statistics/corporation/(?P<corpid>[0-9]+)/$",
        views.statistics.stats_corp,
        name="stats_corp",
    ),
    url(
        r"^statistics/corporation/(?P<corpid>[0-9]+)/(?P<year>[0-9]+)/$",
        views.statistics.stats_corp,
        name="stats_corp",
    ),
    url(
        r"^statistics/corporation/(?P<corpid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        views.statistics.stats_corp,
        name="stats_corp",
    ),
    # stats char
    url(r"^statistics/character/$", views.statistics.stats_char, name="stats_char"),
    url(
        r"^statistics/character/(?P<charid>[0-9]+)/$",
        views.statistics.stats_char,
        name="stats_char",
    ),
    url(
        r"^statistics/character/(?P<charid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        views.statistics.stats_char,
        name="stats_char",
    ),
    # stats alliance
    url(r"^statistics/alliance/$", views.statistics.stats_alliance, name="stats_ally"),
    url(
        r"^statistics/alliance/(?P<allianceid>[0-9]+)/$",
        views.statistics.stats_alliance,
        name="stats_ally",
    ),
    url(
        r"^statistics/alliance/(?P<allianceid>[0-9]+)/(?P<year>[0-9]+)/$",
        views.statistics.stats_alliance,
        name="stats_ally",
    ),
    url(
        r"^statistics/alliance/(?P<allianceid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        views.statistics.stats_alliance,
        name="stats_ally",
    ),
    # fatlinks
    url(r"^fatlinks/$", views.fatlinks.links, name="links"),
    url(r"^fatlinks/(?P<year>[0-9]+)/$", views.fatlinks.links, name="links"),
    url(
        r"^fatlinks/create/esi/(?P<fatlink_hash>[a-zA-Z0-9]+)/$",
        views.fatlinks.link_create_esi,
        name="link_create_esi",
    ),
    url(
        r"^fatlinks/create/esifat/$",
        views.fatlinks.create_esi_fat,
        name="create_esi_fat",
    ),
    url(
        r"^fatlinks/create/click/$",
        views.fatlinks.link_create_click,
        name="link_create_click",
    ),
    url(r"^fatlinks/add/$", views.fatlinks.link_add, name="link_add"),
    url(r"^fatlinks/edit/$", views.fatlinks.link_edit, name="link_edit"),
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/edit/$",
        views.fatlinks.link_edit,
        name="link_edit",
    ),
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/click/$",
        views.fatlinks.click_link,
        name="link_click",
    ),
    url(r"^fatlinks/del/$", views.fatlinks.del_link, name="link_delete"),
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/del/$",
        views.fatlinks.del_link,
        name="link_delete",
    ),
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/(?P<fat>[0-9]+)/del/$",
        views.fatlinks.del_fat,
        name="fat_delete",
    ),
    # ajax calls :: dashboard
    url(
        r"^ajax/dashboard/get_fats/(?P<charid>[0-9]+)/$",
        views.dashboard.dashboard_fats_data,
        name="dashboard_fats_data",
    ),
    url(
        r"^ajax/dashboard/get_fatlinks/$",
        views.dashboard.dashboard_links_data,
        name="dashboard_links_data",
    ),
    # ajax calls :: fatlinks
    url(r"^ajax/fatlinks/get_fatlinks/$", views.fatlinks.links_data, name="links_data"),
    url(
        r"^ajax/fatlinks/get_fatlinks/(?P<year>[0-9]+)/$",
        views.fatlinks.links_data,
        name="links_data",
    ),
    url(
        r"^ajax/fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/edit/$",
        views.fatlinks.link_edit_fat_data,
        name="link_edit_fat_data",
    ),
]
