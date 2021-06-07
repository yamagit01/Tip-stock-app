import os

from django import template

register = template.Library()


@register.filter
def get_filename(value):
    # ファイル名のみ抽出(保存時に追加したuuidを除く)
    return os.path.basename(value.file.name)[37:]
