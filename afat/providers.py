"""
providers
"""

from allianceauth.services.hooks import get_extension_logger
from esi.clients import EsiClientProvider

from afat import __title__
from afat.constants import USER_AGENT
from afat.utils import LoggerAddTag

logger = LoggerAddTag(get_extension_logger(__name__), __title__)

esi = EsiClientProvider(app_info_text=USER_AGENT)
