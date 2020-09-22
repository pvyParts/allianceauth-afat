# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import AFat, AFatLink, AFatLinkType


# Register your models here.
@admin.register(AFatLink)
class AFatLinkAdmin(admin.ModelAdmin):
    list_display = ("afattime", "creator", "fleet", "link_type", "hash", "deleted_at")
    ordering = ("-afattime",)


@admin.register(AFat)
class AFatAdmin(admin.ModelAdmin):
    list_display = ("character", "system", "shiptype", "afatlink", "deleted_at")
    ordering = ("-character",)


@admin.register(AFatLinkType)
class AFatLinkTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    ordering = ("name",)
