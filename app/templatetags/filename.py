import os

from django import template

register = template.Library()


@register.filter
def get_filename(value):
    return os.path.basename(value.file.name)
