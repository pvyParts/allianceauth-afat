# -*- coding: utf-8 -*-

"""
the models
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone

from afat import __title__
from afat.utils import LoggerAddTag

from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


# Create your models here.
def get_sentinel_user():
    """
    get user or create one
    :return:
    """

    return User.objects.get_or_create(username="deleted")[0]


class AaAfat(models.Model):
    """Meta model for app permissions"""

    class Meta:  # pylint: disable=too-few-public-methods
        """AaAfat :: Meta"""

        managed = False
        default_permissions = ()
        permissions = (
            # can acces and register his own participation to a FAT link
            ("basic_access", "Can access the AFAT module"),
            # Can manage the whole FAT module
            # Has:
            #   » add_fatlink
            #   » change_fatlink
            #   » delete_fatlink
            #   » add_fat
            #   » delete_fat
            ("manage_afat", "Can manage the AFAT module"),
            # Can add a new FAT link
            ("add_fatlink", "Can create FAT Links"),
            ("stats_corporation_own", "Can see own corporation statistics"),
            # Can see the stats of all corps
            ("stats_corporation_other", "Can see statistics of other corporations"),
        )
        verbose_name = "Alliance Auth AFAT"


# Abstract model to allow for soft deletion
class SoftDeletionManager(models.Manager):
    """
    SoftDeletionManager
    """

    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop("alive_only", True)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        """
        get_queryset
        :return:
        """

        if self.alive_only:
            return SoftDeletionQuerySet(self.model).filter(deleted_at=None)

        return SoftDeletionQuerySet(self.model)

    def hard_delete(self):
        """
        hard_delete
        :return:
        """

        return self.get_queryset().hard_delete()


class SoftDeletionModel(models.Model):
    """
    SoftDeletionModel
    """

    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeletionManager()
    all_objects = SoftDeletionManager(alive_only=False)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        delete
        """

        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        """
        hard_delete
        """

        super().delete()


class SoftDeletionQuerySet(QuerySet):
    """
    SoftDeletionQuerySet
    """

    def delete(self):
        """
        delete
        :return:
        """

        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        """
        hard_delete
        :return:
        """

        return super().delete()

    def alive(self):
        """
        alive
        :return:
        """

        return self.filter(deleted_at=None)

    def dead(self):
        """
        dead
        :return:
        """

        return self.exclude(deleted_at=None)


# AFatLinkType Model (StratOp, ADM, HD etc)
class AFatLinkType(SoftDeletionModel):
    """
    AFatLinkType
    """

    id = models.AutoField(primary_key=True)

    name = models.CharField(
        max_length=254, help_text="Descriptive name of your fleet type"
    )

    is_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this fleettype is active or not",
    )

    deleted_at = models.DateTimeField(
        blank=True, null=True, help_text="Has this been deleted?"
    )

    def __str__(self):
        return "{} - {}".format(self.id, self.name)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        default_permissions = ()
        verbose_name = "FAT Link Fleet Type"
        verbose_name_plural = "FAT Link Fleet Types"


# AFatLink Model
class AFatLink(SoftDeletionModel):
    """
    AFatLink
    """

    afattime = models.DateTimeField(
        default=timezone.now, help_text="When was this fatlink created"
    )

    fleet = models.CharField(
        max_length=254,
        null=True,
        help_text="The fatlinks fleet name",
    )

    hash = models.CharField(max_length=254, help_text="The fatlinks hash")

    creator = models.ForeignKey(
        User,
        on_delete=models.SET(get_sentinel_user),
        help_text="Who created the fatlink?",
    )

    character = models.ForeignKey(
        EveCharacter,
        on_delete=models.CASCADE,
        default=None,
        null=True,
        help_text="Character this fatlink has been created with",
    )

    deleted_at = models.DateTimeField(
        blank=True, null=True, help_text="Has been deleted or not"
    )

    link_type = models.ForeignKey(
        AFatLinkType,
        on_delete=models.CASCADE,
        null=True,
        help_text="The fatlinks fleet type, if it's set",
    )

    is_esilink = models.BooleanField(
        default=False,
        help_text="Whether this fatlink was created via ESI or not",
    )

    is_registered_on_esi = models.BooleanField(
        default=False,
        help_text="Whether this is an ESI fat link is registered on ESI",
    )

    esi_fleet_id = models.BigIntegerField(blank=True, null=True)

    def __str__(self):
        # return self.hash[6:]
        return "{} - {}".format(self.fleet, self.hash)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        default_permissions = ()
        ordering = ("-afattime",)
        verbose_name = "FAT Link"
        verbose_name_plural = "FAT Links"


# ClickAFatDuration Model
class ClickAFatDuration(models.Model):
    """
    ClickAFatDuration
    """

    duration = models.PositiveIntegerField()
    fleet = models.ForeignKey(AFatLink, on_delete=models.CASCADE)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        default_permissions = ()
        verbose_name = "FAT Duration"
        verbose_name_plural = "FAT Durations"


# AFat Model
class AFat(SoftDeletionModel):
    """
    AFat
    """

    character = models.ForeignKey(
        EveCharacter,
        on_delete=models.CASCADE,
        help_text="Character who registered this fat",
    )

    afatlink = models.ForeignKey(
        AFatLink,
        on_delete=models.CASCADE,
        help_text="The fatlink the character registered at",
    )

    system = models.CharField(
        max_length=100, null=True, help_text="The system the character is in"
    )

    shiptype = models.CharField(
        max_length=100, null=True, help_text="The ship the character was flying"
    )

    deleted_at = models.DateTimeField(
        blank=True, null=True, help_text="Has been deleted or not"
    )

    def __str__(self):
        return "{} - {}".format(self.afatlink, self.character)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        default_permissions = ()
        unique_together = (("character", "afatlink"),)
        verbose_name = "FAT"
        verbose_name_plural = "FATs"


# ManualAFat Model
class ManualAFat(models.Model):
    """
    ManualAFat
    """

    creator = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    afatlink = models.ForeignKey(AFatLink, on_delete=models.CASCADE)
    character = models.ForeignKey(EveCharacter, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        blank=True, null=True, help_text="Time this FAT has been added manually"
    )

    # Add property for getting the user for a character.
    def __str__(self):
        return "{} - {} ({})".format(self.afatlink, self.character, self.creator)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        default_permissions = ()
        verbose_name = "Manual FAT Log"
        verbose_name_plural = "Manual FAT Logs"


# AFatDelLog Model
class AFatDelLog(models.Model):
    """
    AFatDelLog
    """

    # 0 for FatLink, 1 for Fat
    deltype = models.BooleanField(default=0)
    remover = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    string = models.CharField(max_length=100)

    def delt_to_str(self):
        """
        delt_to_str
        :return:
        """

        if self.deltype == 0:
            return "AFatLink"

        return "AFat"

    def __str__(self):
        return "{}/{} - {}".format(self.delt_to_str(), self.string, self.remover)

    class Meta:  # pylint: disable=too-few-public-methods
        """
        Meta
        """

        default_permissions = ()
        verbose_name = "Delete Log"
        verbose_name_plural = "Delete Logs"
