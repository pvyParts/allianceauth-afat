"""
providers
"""

from esi.clients import EsiClientProvider

from afat.constants import USER_AGENT

esi = EsiClientProvider(app_info_text=USER_AGENT)
