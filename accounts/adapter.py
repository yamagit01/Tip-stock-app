import base64

import django
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured
from django.db.models.fields import (
    BinaryField,
    DateField,
    DateTimeField,
    TimeField,
)
from django.db.models.fields.files import ImageField
from django.utils import dateparse
from django.utils.encoding import force_bytes

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

SERIALIZED_DB_FIELD_PREFIX = "_db_"


# UserのImageFieldに対応するためallauthの既存の関数にImageFieldの条件追加
def custom_deserialize_instance(model, data):
    ret = model()
    for k, v in data.items():
        is_db_value = False
        if k.startswith(SERIALIZED_DB_FIELD_PREFIX):
            k = k[len(SERIALIZED_DB_FIELD_PREFIX) :]
            is_db_value = True
        if v is not None:
            try:
                f = model._meta.get_field(k)
                if isinstance(f, DateTimeField):
                    v = dateparse.parse_datetime(v)
                elif isinstance(f, TimeField):
                    v = dateparse.parse_time(v)
                elif isinstance(f, DateField):
                    v = dateparse.parse_date(v)
                elif isinstance(f, BinaryField):
                    v = force_bytes(base64.b64decode(force_bytes(v)))
                elif isinstance(f, ImageField):  # 追加
                    v = str(v)
                elif is_db_value:
                    try:
                        # This is quite an ugly hack, but will cover most
                        # use cases...
                        # The signature of `from_db_value` changed in Django 3
                        # https://docs.djangoproject.com/en/3.0/releases/3.0/#features-removed-in-3-0
                        if django.VERSION < (3, 0):
                            v = f.from_db_value(v, None, None, None)
                        else:
                            v = f.from_db_value(v, None, None)
                    except Exception:
                        raise ImproperlyConfigured(
                            "Unable to auto serialize field '{}', custom"
                            " serialization override required".format(k)
                        )
            except FieldDoesNotExist:
                pass
        setattr(ret, k, v)
    return ret

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom SocialAccountAdapter for django-allauth.
    Replaced standard behavior for serialization of Imagefield.

    Need set it in project settings:
    SOCIALACCOUNT_ADAPTER = 'accounts.adapter.CustomSocialAccountAdapter'
    """

    def __init__(self, request=None):
        super().__init__(request=request)

    def deserialize_instance(self, model, data):
        return custom_deserialize_instance(model, data)
