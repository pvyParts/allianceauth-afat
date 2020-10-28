# coding=utf-8

"""
import FAT data from ImicusFAT module
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from afat.models import (
    AFat,
    AFatLink,
    AFatDelLog,
    AFatLinkType,
    ClickAFatDuration,
    ManualAFat,
)

from imicusfat.models import (
    IFat,
    IFatLink,
    ClickIFatDuration,
    IFatDelLog,
    IFatLinkType,
    ManualIFat,
)


def get_input(text):
    """
    wrapped input to enable import
    """

    return input(text)


def imicusfat_installed() -> bool:
    """
    check if aa-timezones is installed
    :return: bool
    """

    return "imicusfat" in settings.INSTALLED_APPS


class Command(BaseCommand):
    """
    Initial import of FAT data from AA FAT module
    """

    help = "Imports FAT data from ImicusFAT module"

    def _import_from_imicusfat(self) -> None:
        # check if AA FAT is active
        if imicusfat_installed():
            self.stdout.write(
                self.style.SUCCESS("ImicusFAT module is active, let's go!")
            )

            # first we check if the target tables are really empty ...
            current_afat_count = AFat.objects.all().count()
            current_afat_dellog_count = AFatDelLog.objects.all().count()
            current_afat_links_count = AFatLink.objects.all().count()
            current_afat_linktype_count = AFatLinkType.objects.all().count()
            current_afat_clickduration_count = ClickAFatDuration.objects.all().count()
            current_afat_manualfat_count = ManualAFat.objects.all().count()

            if (
                current_afat_count > 0
                or current_afat_dellog_count > 0
                or current_afat_links_count > 0
                or current_afat_linktype_count > 0
                or current_afat_clickduration_count > 0
                or current_afat_manualfat_count > 0
            ):
                self.stdout.write(
                    self.style.WARNING(
                        "You already have FAT data with the AFAT module. "
                        "Import cannot be continued."
                    )
                )

                return

            # import fatlinktype
            imicusfat_fleettypes = IFatLinkType.objects.all()
            for imicusfat_fleettype in imicusfat_fleettypes:
                self.stdout.write(
                    "Importing fleet type '{fleet_type}'.".format(
                        fleet_type=imicusfat_fleettype.name
                    )
                )

                afat_fleettype = AFatLinkType()

                afat_fleettype.id = imicusfat_fleettype.id
                afat_fleettype.name = imicusfat_fleettype.name
                afat_fleettype.deleted_at = imicusfat_fleettype.deleted_at
                afat_fleettype.is_enabled = imicusfat_fleettype.is_enabled

                afat_fleettype.save()

            # import FAT links
            imicusfat_fatlinks = IFatLink.objects.all()
            for imicusfat_fatlink in imicusfat_fatlinks:
                self.stdout.write(
                    "Importing FAT link for fleet '{fleet}' with hash '{fatlink_hash}'.".format(
                        fleet=imicusfat_fatlink.fleet,
                        fatlink_hash=imicusfat_fatlink.hash,
                    )
                )

                afatlink = AFatLink()

                afatlink.id = imicusfat_fatlink.id
                afatlink.afattime = imicusfat_fatlink.ifattime
                afatlink.fleet = imicusfat_fatlink.fleet
                afatlink.hash = imicusfat_fatlink.hash
                afatlink.creator_id = imicusfat_fatlink.creator_id
                afatlink.deleted_at = imicusfat_fatlink.deleted_at
                afatlink.link_type_id = imicusfat_fatlink.link_type_id
                afatlink.is_esilink = imicusfat_fatlink.is_esilink

                afatlink.save()

            # import FATs
            imicustaf_fats = IFat.objects.all()
            for imicusfat_fat in imicustaf_fats:
                self.stdout.write(
                    "Importing FATs for FAT link ID '{fatlink_id}'.".format(
                        fatlink_id=imicusfat_fat.id
                    )
                )

                afat = AFat()

                afat.id = imicusfat_fat.id
                afat.system = imicusfat_fat.system
                afat.shiptype = imicusfat_fat.shiptype
                afat.character_id = imicusfat_fat.character_id
                afat.afatlink_id = imicusfat_fat.ifatlink_id
                afat.deleted_at = imicusfat_fat.deleted_at

                afat.save()

            # import click FAT durations
            imicusfat_clickfatdurations = ClickIFatDuration.objects.all()
            for imicusfat_clickfatduration in imicusfat_clickfatdurations:
                self.stdout.write(
                    "Importing FAT duration with ID '{duration_id}'.".format(
                        duration_id=imicusfat_clickfatduration.id
                    )
                )

                afat_clickfatduration = ClickAFatDuration()

                afat_clickfatduration.id = imicusfat_clickfatduration.id
                afat_clickfatduration.duration = imicusfat_clickfatduration.duration
                afat_clickfatduration.fleet_id = imicusfat_clickfatduration.fleet_id

                afat_clickfatduration.save()

            # import dellog
            imicusfat_dellogs = IFatDelLog.objects.all()
            for imicusfat_dellog in imicusfat_dellogs:
                self.stdout.write(
                    "Importing FAT dellogwith ID '{dellog_id}'.".format(
                        dellog_id=imicusfat_dellog.id
                    )
                )

                afat_dellog = AFatDelLog()

                afat_dellog.id = imicusfat_dellog.id
                afat_dellog.deltype = imicusfat_dellog.deltype
                afat_dellog.string = imicusfat_dellog.string
                afat_dellog.remover_id = imicusfat_dellog.remover_id

                afat_dellog.save()

            # import manual fat
            imicusfat_manualfats = ManualIFat.objects.all()
            for imicusfat_manualfat in imicusfat_manualfats:
                self.stdout.write(
                    "Importing manual FAT with ID '{manualfat_id}'.".format(
                        manualfat_id=imicusfat_manualfat.id
                    )
                )

                afat_manualfat = ManualAFat()

                afat_manualfat.id = imicusfat_manualfat.id
                afat_manualfat.character_id = imicusfat_manualfat.character_id
                afat_manualfat.creator_id = imicusfat_manualfat.creator_id
                afat_manualfat.afatlink_id = imicusfat_manualfat.ifatlink_id
                afat_manualfat.created_at = imicusfat_manualfat.created_at

                afat_manualfat.save()

            self.stdout.write(
                self.style.SUCCESS(
                    "Import complete! "
                    "You can now deactivate the ImicusFAT module in your local.py"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "ImicusFAT module is not active. "
                    "Please make sure you have it in your INSTALLES_APPS in your local.py!"
                )
            )

    def handle(self, *args, **options):
        """
        ask before running ...
        :param args:
        :param options:
        """

        self.stdout.write(
            "Importing all FAT/FAT link data from ImicusFAT module. "
            "This can only be done once during the very first installation. "
            "As soon as you have data collected with your AFAT module, this import will fail!"
        )

        user_input = get_input("Are you sure you want to proceed? (yes/no)?")

        if user_input == "yes":
            self.stdout.write("Starting import. Please stand by.")
            self._import_from_imicusfat()
        else:
            self.stdout.write(self.style.WARNING("Aborted."))
