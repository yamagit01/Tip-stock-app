# Generated by Django 3.2.3 on 2021-07-16 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_tip_delete_file_and_url_add_tweet'),
    ]

    operations = [
        migrations.AddField(
            model_name='tip',
            name='has_tweeted',
            field=models.BooleanField(default=False),
        ),
    ]
