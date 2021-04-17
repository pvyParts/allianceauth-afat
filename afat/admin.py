"""
admin pages configuration
"""

from django.contrib import admin

from afat.models import AFat, AFatLink, AFatLinkType, AFatLog, ManualAFat


def custom_filter(title):
    """
    defining custom filter titles
    :param title:
    :return:
    """

    class Wrapper(admin.FieldListFilter):
        """
        Wrapper
        """

        def expected_parameters(self):
            """
            expected parameters
            """

            pass

        def choices(self, changelist):
            """
            choices
            :param changelist:
            """

            pass

        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title

            return instance

    return Wrapper


# Register your models here.
@admin.register(AFatLink)
class AFatLinkAdmin(admin.ModelAdmin):
    """
    config for fat link model
    """

    list_display = ("afattime", "creator", "fleet", "_link_type", "is_esilink", "hash")
    list_filter = ("is_esilink", ("link_type__name", custom_filter(title="fleet type")))
    ordering = ("-afattime",)

    def _link_type(self, obj):
        if obj.link_type:
            return obj.link_type.name

        return "-"

    _link_type.short_description = "Fleet Type"
    _link_type.admin_order_field = "link_type__name"


@admin.register(AFat)
class AFatAdmin(admin.ModelAdmin):
    """
    config for fat model
    """

    list_display = ("character", "system", "shiptype", "afatlink")
    list_filter = ("character", "system", "shiptype")
    ordering = ("-character",)


@admin.register(AFatLinkType)
class AFatLinkTypeAdmin(admin.ModelAdmin):
    """
    config for fatlinktype model
    """

    list_display = ("id", "_name", "_is_enabled")
    list_filter = ("is_enabled",)
    ordering = ("name",)

    def _name(self, obj):
        return obj.name

    _name.short_description = "Fleet Type"
    _name.admin_order_field = "name"

    def _is_enabled(self, obj):
        return obj.is_enabled

    _is_enabled.boolean = True
    _is_enabled.short_description = "Is Enabled"
    _is_enabled.admin_order_field = "is_enabled"

    actions = (
        "mark_as_active",
        "mark_as_inactive",
    )

    def mark_as_active(self, request, queryset):
        """
        Mark fleet type as active
        :param request:
        :param queryset:
        """

        notifications_count = 0

        for obj in queryset:
            obj.is_enabled = True
            obj.save()

            notifications_count += 1

        self.message_user(
            request, f"{notifications_count} fleet types marked as active"
        )

    mark_as_active.short_description = "Activate selected fleet type(s)"

    def mark_as_inactive(self, request, queryset):
        """
        Mark fleet type as inactive
        :param request:
        :param queryset:
        """

        notifications_count = 0

        for obj in queryset:
            obj.is_enabled = False
            obj.save()

            notifications_count += 1

        self.message_user(
            request, f"{notifications_count} fleet types marked as inactive"
        )

    mark_as_inactive.short_description = "Deactivate selected fleet type(s)"


@admin.register(ManualAFat)
class ManualAFatAdmin(admin.ModelAdmin):
    """
    manual fat log config
    """

    list_display = ("creator", "_character", "_afatlink", "created_at")
    exclude = ("creator", "character", "afatlink", "created_at")
    readonly_fields = ("creator", "character", "afatlink", "created_at")
    ordering = ("-created_at",)
    list_filter = (
        ("creator", admin.RelatedOnlyFieldListFilter),
        ("character", admin.RelatedOnlyFieldListFilter),
        ("afatlink", admin.RelatedOnlyFieldListFilter),
    )

    def _afatlink(self, obj):
        return f"Fleet: {obj.afatlink.fleet} (FAT link hash: {obj.afatlink.hash})"

    _afatlink.short_description = "FAT Link"
    _afatlink.admin_order_field = "afatlink"

    def _character(self, obj):
        return obj.character

    _character.short_description = "Pilot added"
    _character.admin_order_field = "character"


@admin.register(AFatLog)
class AFatLogAdmin(admin.ModelAdmin):
    """
    config for admin log
    """

    list_display = ("log_time", "log_event", "user", "fatlink_hash", "log_text")
    ordering = ("-log_time",)
    readonly_fields = ("log_time", "log_event", "user", "fatlink_hash", "log_text")

    list_filter = ("log_event",)
