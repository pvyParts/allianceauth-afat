"""
url configuration
"""

from django.conf.urls import url

from afat.views import dashboard, fatlinks, statistics

app_name: str = "afat"

urlpatterns = [
    # dashboard
    url(r"^$", dashboard.overview, name="dashboard"),
    # stats main page
    url(r"^statistics/$", statistics.overview, name="statistics_overview"),
    url(
        r"^statistics/(?P<year>[0-9]+)/$",
        statistics.overview,
        name="statistics_overview",
    ),
    # stats corp
    url(
        r"^statistics/corporation/$",
        statistics.corporation,
        name="statistics_corporation",
    ),
    url(
        r"^statistics/corporation/(?P<corpid>[0-9]+)/$",
        statistics.corporation,
        name="statistics_corporation",
    ),
    url(
        r"^statistics/corporation/(?P<corpid>[0-9]+)/(?P<year>[0-9]+)/$",
        statistics.corporation,
        name="statistics_corporation",
    ),
    url(
        r"^statistics/corporation/(?P<corpid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        statistics.corporation,
        name="statistics_corporation",
    ),
    # stats char
    url(r"^statistics/character/$", statistics.character, name="statistics_character"),
    url(
        r"^statistics/character/(?P<charid>[0-9]+)/$",
        statistics.character,
        name="statistics_character",
    ),
    url(
        r"^statistics/character/(?P<charid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        statistics.character,
        name="statistics_character",
    ),
    # stats alliance
    url(r"^statistics/alliance/$", statistics.alliance, name="statistics_alliance"),
    url(
        r"^statistics/alliance/(?P<allianceid>[0-9]+)/$",
        statistics.alliance,
        name="statistics_alliance",
    ),
    url(
        r"^statistics/alliance/(?P<allianceid>[0-9]+)/(?P<year>[0-9]+)/$",
        statistics.alliance,
        name="statistics_alliance",
    ),
    url(
        r"^statistics/alliance/(?P<allianceid>[0-9]+)/(?P<year>[0-9]+)/(?P<month>[0-9]+)/$",
        statistics.alliance,
        name="statistics_alliance",
    ),
    # fatlinks
    url(r"^fatlinks/$", fatlinks.overview, name="links"),
    url(r"^fatlinks/(?P<year>[0-9]+)/$", fatlinks.overview, name="links"),
    url(
        r"^fatlinks/create/esi-fatlink/$",
        fatlinks.create_esi_fatlink,
        name="fatlinks_create_esi_fatlink",
    ),
    url(
        r"^fatlinks/create/esi-fatlink/callback/(?P<fatlink_hash>[a-zA-Z0-9]+)/$",
        fatlinks.create_esi_fatlink_callback,
        name="fatlinks_create_esi_fatlink_callback",
    ),
    url(
        r"^fatlinks/create/clickable-fatlink/$",
        fatlinks.create_clickable_fatlink,
        name="fatlinks_create_clickable_fatlink",
    ),
    url(r"^fatlinks/add/$", fatlinks.add_fatlink, name="fatlinks_add_fatlink"),
    url(r"^fatlinks/edit/$", fatlinks.edit_fatlink, name="fatlinks_edit_fatlink"),
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/edit/$",
        fatlinks.edit_fatlink,
        name="fatlinks_edit_fatlink",
    ),
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/del/$",
        fatlinks.delete_fatlink,
        name="fatlinks_delete_fatlink",
    ),
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/stop-esi-tracking/$",
        fatlinks.close_esi_fatlink,
        name="fatlinks_close_esi_fatlink",
    ),
    # fats
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/register/$",
        fatlinks.add_fat,
        name="fatlinks_add_fat",
    ),
    url(
        r"^fatlinks/(?P<fatlink_hash>[a-zA-Z0-9]+)/(?P<fat>[0-9]+)/del/$",
        fatlinks.delete_fat,
        name="fatlinks_delete_fat",
    ),
    # ajax calls :: dashboard
    url(
        r"^ajax/dashboard/fatlinks/recent/$",
        dashboard.ajax_get_recent_fatlinks,
        name="dashboard_ajax_get_recent_fatlinks",
    ),
    url(
        r"^ajax/dashboard/fats/character/(?P<charid>[0-9]+)/$",
        dashboard.ajax_get_fats_by_character,
        name="dashboard_ajax_get_fats_by_character",
    ),
    # ajax calls :: fatlinks
    url(
        r"^ajax/fatlinks/fatlinks/year/(?P<year>[0-9]+)/$",
        fatlinks.ajax_get_fatlinks_by_year,
        name="fatlinks_ajax_get_fatlinks_by_year",
    ),
    url(
        r"^ajax/fatlinks/fats/fatlink/(?P<fatlink_hash>[a-zA-Z0-9]+)/$",
        fatlinks.ajax_get_fats_by_fatlink,
        name="fatlinks_ajax_get_fats_by_fatlink",
    ),
]
