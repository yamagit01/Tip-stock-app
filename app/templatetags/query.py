import urllib.parse

from django import template

register = template.Library()


@register.filter
def get_query(value, arg):
    # urlから引数のクエリの値を返す
    qs = urllib.parse.urlparse(value).query
    qs_d = urllib.parse.parse_qs(qs)
    qs_arg = qs_d.get(arg, '')
    if qs_arg == '':
        return ''
    else:
        return qs_arg[0]
