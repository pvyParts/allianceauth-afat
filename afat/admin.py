# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import AFat, AFatLink, AFatLinkType


# Register your models here.
admin.site.register(AFatLink)
admin.site.register(AFat)
admin.site.register(AFatLinkType)
