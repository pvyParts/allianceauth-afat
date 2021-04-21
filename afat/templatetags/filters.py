import calendar

from django.template.defaulttags import register


@register.filter
def month_name(value):
    """
    template tag :: get month name from month number
    example: {{ event.month|month_name }}
    :param value:
    :type value:
    :return:
    :rtype:
    """

    value = int(value)

    return calendar.month_name[value]
