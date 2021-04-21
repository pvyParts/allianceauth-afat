"""
import FAT data from bFAT module
"""

from bfat.models import ClickFatDuration as BfatClickFatDuration
from bfat.models import Fat as BfatFat
from bfat.models import FatLink as BfatFatLink
from bfat.models import ManualFat as BfatManualFat

from django.conf import settings
from django.core.management.base import BaseCommand

from afat.models import AFat, AFatLink, AFatLog, AFatLogEvent, ClickAFatDuration


def get_input(text) -> str:
    """
    wrapped input to enable import
    :param text:
    :type text:
    :return:
    :rtype:
    """

    return input(text)


def bfat_installed() -> bool:
    """
    check if bfat is installed
    :return:
    :rtype:
    """

    return "bfat" in settings.INSTALLED_APPS


class Command(BaseCommand):
    """
    Initial import of FAT data from AA FAT module
    """

    help = "Imports FAT data from ImicusFAT module"

    def _import_from_imicusfat(self) -> None:
        """
        start the import
        :return:
        :rtype:
        """

        # check if AA FAT is active
        if bfat_installed():
            self.stdout.write(
                self.style.SUCCESS("ImicusFAT module is active, let's go!")
            )

            # first we check if the target tables are really empty ...
            current_afat_count = AFat.objects.all().count()
            current_afat_links_count = AFatLink.objects.all().count()
            current_afat_clickduration_count = ClickAFatDuration.objects.all().count()

            if (
                current_afat_count > 0
                or current_afat_links_count > 0
                or current_afat_clickduration_count > 0
            ):
                self.stdout.write(
                    self.style.WARNING(
                        "You already have FAT data with the AFAT module. "
                        "Import cannot be continued."
                    )
                )

                return

            # import FAT links
            bfat_fatlinks = BfatFatLink.objects.all()
            for bfat_fatlink in bfat_fatlinks:
                self.stdout.write(
                    f'Importing FAT link for fleet "{bfat_fatlink.fleet}" '
                    f'with hash "{bfat_fatlink.hash}".'
                )

                afatlink = AFatLink()

                afatlink.id = bfat_fatlink.id
                afatlink.afattime = bfat_fatlink.fattime
                afatlink.fleet = bfat_fatlink.fleet
                afatlink.hash = bfat_fatlink.hash
                afatlink.creator_id = bfat_fatlink.creator_id

                afatlink.save()

                # write to log table
                try:
                    fleet_duration = BfatClickFatDuration.objects.get(
                        fleet_id=bfat_fatlink.id
                    )

                    log_text = (
                        f'FAT link "{bfat_fatlink.hash}" with name '
                        f'"{bfat_fatlink.fleet}" and a duration of '
                        f"{fleet_duration.duration} minutes was created "
                        f"by {bfat_fatlink.creator}"
                    )
                except BfatClickFatDuration.DoesNotExist:
                    log_text = (
                        f'FAT link "{bfat_fatlink.hash}" with name '
                        f'"{bfat_fatlink.fleet}" was created by {bfat_fatlink.creator}'
                    )

                if bfat_fatlink.fattime is not None:
                    afatlog = AFatLog()
                    afatlog.log_time = bfat_fatlink.fattime
                    afatlog.log_event = AFatLogEvent.CREATE_FATLINK
                    afatlog.log_text = log_text
                    afatlog.user_id = bfat_fatlink.creator_id
                    afatlog.save()

            # import FATs
            bfat_fats = BfatFat.objects.all()
            for bfat_fat in bfat_fats:
                self.stdout.write(f"Importing FATs for FAT link ID {bfat_fat.id}.")

                afat = AFat()

                afat.id = bfat_fat.id
                afat.system = bfat_fat.system
                afat.shiptype = bfat_fat.shiptype
                afat.character_id = bfat_fat.character_id
                afat.afatlink_id = bfat_fat.fatlink_id

                afat.save()

            # import click FAT durations
            bfat_clickfatdurations = BfatClickFatDuration.objects.all()
            for bfat_clickfatduration in bfat_clickfatdurations:
                self.stdout.write(
                    f"Importing FAT duration with ID {bfat_clickfatduration.id}."
                )

                afat_clickfatduration = ClickAFatDuration()

                afat_clickfatduration.id = bfat_clickfatduration.id
                afat_clickfatduration.duration = bfat_clickfatduration.duration
                afat_clickfatduration.fleet_id = bfat_clickfatduration.fleet_id

                afat_clickfatduration.save()

            # import manual fat
            bfat_manualfats = BfatManualFat.objects.all()
            for bfat_manualfat in bfat_manualfats:
                self.stdout.write(f"Importing manual FAT with ID {bfat_manualfat.id}.")

                fatlink = BfatFatLink.objects.get(manualfat=bfat_manualfat)
                log_text = (
                    f"Pilot {bfat_manualfat.character.character_name} was manually "
                    f'added to FAT link with hash "{fatlink.hash}"'
                )

                afatlog = AFatLog()
                afatlog.log_time = bfat_manualfat.created_at
                afatlog.log_event = AFatLogEvent.MANUAL_FAT
                afatlog.log_text = log_text
                afatlog.user_id = bfat_manualfat.creator_id
                afatlog.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Import complete! "
                    "You can now deactivate the bFAT module in your local.py"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "bFAT module is not active. "
                    "Please make sure you have it in your "
                    "INSTALLED_APPS in your local.py!"
                )
            )

    def handle(self, *args, **options):
        """
        ask before running ...
        :param args:
        :type args:
        :param options:
        :type options:
        :return:
        :rtype:
        """

        self.stdout.write(
            "Importing all FAT/FAT link data from bFAT module. "
            "This can only be done once during the very first installation. "
            "As soon as you have data collected with your AFAT module, "
            "this import will fail!"
        )

        user_input = get_input("Are you sure you want to proceed? (yes/no)?")

        if user_input == "yes":
            self.stdout.write("Starting import. Please stand by.")
            self._import_from_imicusfat()
        else:
            self.stdout.write(self.style.WARNING("Aborted."))
