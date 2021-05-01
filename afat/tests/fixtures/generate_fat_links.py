# flake8: noqa
"""scripts generates large amount of fat links for load testing

This script can be executed directly from shell.
"""

import os
import sys
from pathlib import Path

myauth_dir = Path(__file__).parent.parent.parent.parent.parent / "myauth"
sys.path.insert(0, str(myauth_dir))

import django
from django.apps import apps

# init and setup django project
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myauth.settings.local")
django.setup()

"""SCRIPT"""
import random
from pathlib import Path

from django.contrib.auth.models import User

from allianceauth.eveonline.models import EveCharacter
from app_utils.helpers import random_string

from afat.models import AFat, AFatLink, AFatLinkType

LINKS_NUMBER = 50

characters = list(EveCharacter.objects.all())
print(
    f"Creating {LINKS_NUMBER} FAT links "
    f"with up to {len(characters)} characters each..."
)
user = User.objects.first()
creator = user.profile.main_character
link_type, _ = AFatLinkType.objects.get_or_create(name="Generated Fleet")
for _ in range(LINKS_NUMBER):
    fat_link = AFatLink.objects.create(
        fleet=f"Generated Fleet #{random.randint(1, 1000000000)}",
        hash=random_string(20),
        creator=user,
        character=creator,
        link_type=link_type,
    )
    for character in random.sample(characters, k=random.randint(1, len(characters))):
        AFat.objects.create(
            character_id=character.id,
            afatlink=fat_link,
            system="Jita",
            shiptype="Ibis",
        )


print("DONE")
