# Generated by Django 3.2.3 on 2021-07-09 05:07

import accounts.models
import app.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_icon_add_validation'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='follows',
            field=models.ManyToManyField(blank=True, related_name='followed_by', to=settings.AUTH_USER_MODEL, verbose_name='フォロー'),
        ),
        migrations.AddField(
            model_name='user',
            name='self_introduction',
            field=models.CharField(blank=True, max_length=250, verbose_name='自己紹介'),
        ),
        migrations.AlterField(
            model_name='user',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to=accounts.models._user_profile_icon_upload_to, validators=[app.validators.FileSizeValidator(byte_type='kb', val=500)], verbose_name='アイコン'),
        ),
    ]
