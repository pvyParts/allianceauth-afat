# -*- coding: utf-8 -*-

"""
app config
"""

default_app_config: str = "afat.apps.AfatConfig"

__title__ = "Fleet Activity Tracking"
__version__ = "1.4.2"
__verbose_name__ = "AFAT Fleet Activity Tracking for Alliance Auth"
__user_agent_name__ = "AFAT-Fleet-Activity-Tracking-for-Alliance-Auth"
__user_agent__ = "{verbose_name} v{version} {github_url}".format(
    verbose_name=__user_agent_name__,
    version=__version__,
    github_url="https://github.com/ppfeufer/allianceauth-afat",
)
