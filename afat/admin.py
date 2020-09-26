# -*- coding: utf-8 -*-

"""
admin pages configuration
"""

from django.contrib import admin

from .models import AFat, AFatLink, AFatLinkType


# Register your models here.
@admin.register(AFatLink)
class AFatLinkAdmin(admin.ModelAdmin):
    """
    config for fat link model
    """

    list_display = (
        "afattime",
        "creator",
        "fleet",
        "link_type",
        "is_esilink",
        "hash",
        "deleted_at",
    )
    ordering = ("-afattime",)


@admin.register(AFat)
class AFatAdmin(admin.ModelAdmin):
    """
    config for fat model
    """

    list_display = ("character", "system", "shiptype", "afatlink", "deleted_at")
    ordering = ("-character",)


@admin.register(AFatLinkType)
class AFatLinkTypeAdmin(admin.ModelAdmin):
    """
    config for fatlinktype model
    """

    list_display = ("id", "name")
    ordering = ("name",)
