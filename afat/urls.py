# -*- coding: utf-8 -*-

"""
url configuration
"""

from django.conf.urls import url

from afat import views

app_name: str = "afat"

urlpatterns = [
    # dashboard
    url(r"^$", views.dashboard, name="dashboard"),
    # stats main page
    url(r"^statistic/$", views.stats, name="stats"),
    url(r"^statistic/(?P<year>[0-9]+)/$", views.stats, name="stats"),
    # stats corp
    url(r"^statistic/corporation/$", views.stats_corp, name="stats_corp"),
    url(
        r"^statistic/corporation/(?P<corpid>[0-9]+)/$",
        views.stats_corp,
        name="stats_corp",
    ),
    url(
        r"^statistic/corporation/(?P<corpid>[0-9]+)/(?P<year>[0-9]+)/$",
        views.stats_corp,
        name="stats_corp",
    ),
    url(
        r"^statistic/corporation/(?P<corpid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        views.stats_corp,
        name="stats_corp",
    ),
    # stats char
    url(r"^statistic/character/$", views.stats_char, name="stats_char"),
    url(
        r"^statistic/character/(?P<charid>[0-9]+)/$",
        views.stats_char,
        name="stats_char",
    ),
    url(
        r"^statistic/character/(?P<charid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        views.stats_char,
        name="stats_char",
    ),
    # stats alliance
    url(r"^statistic/alliance/$", views.stats_alliance, name="stats_ally"),
    url(
        r"^statistic/alliance/(?P<allianceid>[0-9]+)/$",
        views.stats_alliance,
        name="stats_ally",
    ),
    url(
        r"^statistic/alliance/(?P<allianceid>[0-9]+)/(?P<year>[0-9]+)/$",
        views.stats_alliance,
        name="stats_ally",
    ),
    url(
        r"^statistic/alliance/(?P<allianceid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        views.stats_alliance,
        name="stats_ally",
    ),
    # fat links
    url(r"^links/$", views.links, name="links"),
    url(r"^links/(?P<year>[0-9]+)/$", views.links, name="links"),
    url(
        r"^links/create/esi/(?P<fatlink_hash>[a-zA-Z0-9]+)/$",
        views.link_create_esi,
        name="link_create_esi",
    ),
    url(r"^links/create/esifat/$", views.create_esi_fat, name="create_esi_fat"),
    url(r"^links/create/click/$", views.link_create_click, name="link_create_click"),
    url(r"^links/add/$", views.link_add, name="link_add"),
    url(r"^links/edit/$", views.edit_link, name="link_edit"),
    url(
        r"^links/(?P<fatlink_hash>[a-zA-Z0-9]+)/edit/$",
        views.edit_link,
        name="link_edit",
    ),
    url(
        r"^links/(?P<fatlink_hash>[a-zA-Z0-9]+)/click/$",
        views.click_link,
        name="link_click",
    ),
    url(r"^links/del/$", views.del_link, name="link_delete"),
    url(
        r"^links/(?P<fatlink_hash>[a-zA-Z0-9]+)/del/$",
        views.del_link,
        name="link_delete",
    ),
    url(
        r"^links/(?P<fatlink_hash>[a-zA-Z0-9]+)/(?P<fat>[0-9]+)/del/$",
        views.del_fat,
        name="fat_delete",
    ),
    # ajax calls
    url(
        r"^ajax/dashboard/get_fatlinks/$",
        views.dashboard_links_data,
        name="dashboard_links_data",
    ),
    url(r"^ajax/links/get_fatlinks/$", views.links_data, name="links_data"),
    url(
        r"^ajax/links/get_fatlinks/(?P<year>[0-9]+)/$",
        views.links_data,
        name="links_data",
    ),
]
