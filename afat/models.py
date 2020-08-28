# -*- coding: utf-8 -*-
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

from django.contrib.auth.models import User
from django.db import models
from django.db.models.query import QuerySet
from django.utils import timezone

from . import __title__
from .utils import LoggerAddTag


logger = LoggerAddTag(get_extension_logger(__name__), __title__)


# Create your models here.
def get_sentinel_user():
    return User.objects.get_or_create(username="deleted")[0]


# Abstract model to allow for soft deletion
class SoftDeletionManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop("alive_only", True)
        super(SoftDeletionManager, self).__init__(*args, **kwargs)

    def get_queryset(self):
        if self.alive_only:
            return SoftDeletionQuerySet(self.model).filter(deleted_at=None)
        return SoftDeletionQuerySet(self.model)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class SoftDeletionModel(models.Model):
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SoftDeletionManager()
    all_objects = SoftDeletionManager(alive_only=False)

    class Meta:
        abstract = True

    def delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super(SoftDeletionModel, self).delete()


class SoftDeletionQuerySet(QuerySet):
    def delete(self):
        return super(SoftDeletionQuerySet, self).update(deleted_at=timezone.now())

    def hard_delete(self):
        return super(SoftDeletionQuerySet, self).delete()

    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        return self.exclude(deleted_at=None)


# AFatLinkType Model (StratOp, ADM, HD etc)
class AFatLinkType(SoftDeletionModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=254)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "{} - {}".format(self.id, self.name)


# AFatLink Model
class AFatLink(SoftDeletionModel):
    afattime = models.DateTimeField(default=timezone.now)
    fleet = models.CharField(max_length=254, null=True)
    hash = models.CharField(max_length=254)
    creator = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    deleted_at = models.DateTimeField(blank=True, null=True)
    link_type = models.ForeignKey(AFatLinkType, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.hash[6:]

    class Meta:
        permissions = (
            ("manage_afat", "Can manage the Another Fleet Activity Tracking module"),
            ("stats_corp_own", "Can see own corp stats"),
            ("stats_corp_other", "Can see stats of other corps."),
            (
                "stats_char_other",
                "Can see stats of characters not associated with current user.",
            ),
        )
        ordering = ("-afattime",)


# ClickAFatDuration Model
class ClickAFatDuration(models.Model):
    duration = models.PositiveIntegerField()
    fleet = models.ForeignKey(AFatLink, on_delete=models.CASCADE)


# AFat Model
class AFat(SoftDeletionModel):
    character = models.ForeignKey(EveCharacter, on_delete=models.CASCADE)
    afatlink = models.ForeignKey(AFatLink, on_delete=models.CASCADE)
    system = models.CharField(max_length=100, null=True)
    shiptype = models.CharField(max_length=100, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = (("character", "afatlink"),)

    def __str__(self):
        return "{} - {}".format(self.afatlink, self.character)


# ManualAFat Model
class ManualAFat(models.Model):
    creator = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    afatlink = models.ForeignKey(AFatLink, on_delete=models.CASCADE)
    character = models.ForeignKey(EveCharacter, on_delete=models.CASCADE)

    # Add property for getting the user for a character.

    def __str__(self):
        return "{} - {} ({})".format(self.afatlink, self.character, self.creator)


# AFatDelLog Model
class AFatDelLog(models.Model):
    # 0 for FatLink, 1 for Fat
    deltype = models.BooleanField(default=0)
    remover = models.ForeignKey(User, on_delete=models.SET(get_sentinel_user))
    string = models.CharField(max_length=100)

    def delt_to_str(self):
        if self.deltype == 0:
            return "AFatLink"
        else:
            return "AFat"

    def __str__(self):
        return "{}/{} - {}".format(self.delt_to_str(), self.string, self.remover)
