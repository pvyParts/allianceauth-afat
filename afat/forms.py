"""
the forms we use
"""

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from afat.app_settings import AFAT_DEFAULT_FATLINK_EXPIRY_TIME
from afat.models import AFatLinkType


def get_mandatory_form_label_text(text):
    """
    label text for mandatory form fields
    :param text:
    :type text:
    :return:
    :rtype:
    """

    required_text = _("This field is mandatory")
    required_marker = (
        f'<span aria-label="{required_text}" class="form-required-marker">*</span>'
    )

    return mark_safe(
        f'<span class="form-field-required">{text} {required_marker}</span>'
    )


class AFatEsiFatForm(forms.Form):
    """
    fatlink form
    used to create ESI fatlinks
    """

    name_esi = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(_("Fleet Name")),
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Enter fleet name")}),
    )
    type_esi = forms.ModelChoiceField(
        required=False,
        label=_("Fleet Type (optional)"),
        queryset=AFatLinkType.objects.all(),
    )


class AFatManualFatForm(forms.Form):
    """
    manual fat form
    """

    character = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(_("Character Name")),
        max_length=255,
    )
    system = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(_("System")),
        max_length=100,
    )
    shiptype = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(_("Ship Type")),
        max_length=100,
    )


class AFatClickFatForm(forms.Form):
    """
    fatlink form
    used to create clickable fatlinks
    """

    name = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(_("Fleet Name")),
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": _("Enter fleet name")}),
    )
    type = forms.ModelChoiceField(
        required=False,
        label=_("Fleet Type (optional)"),
        queryset=AFatLinkType.objects.all(),
    )
    duration = forms.IntegerField(
        required=True,
        label=get_mandatory_form_label_text(_("FAT link expiry time in minutes")),
        min_value=1,
        initial=AFAT_DEFAULT_FATLINK_EXPIRY_TIME,
        widget=forms.TextInput(attrs={"placeholder": _("Expiry time in minutes")}),
    )


class FatLinkEditForm(forms.Form):
    """
    fatlink edit form
    used in edit view to change the fatlink name
    """

    fleet = forms.CharField(
        required=True,
        label=get_mandatory_form_label_text(_("Fleet Name")),
        max_length=255,
    )


# class ExtendFatLinkDuration(forms.Form):
#     """
#     extending the duration time of a fatlink
#     """
#
#     duration = forms.IntegerField(label=_("Re-open for (in minutes)"), min_value=1)
