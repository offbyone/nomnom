# Generated by Django 5.2.dev20240707070739 on 2024-07-07 20:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("advise", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="proposal",
            options={"permissions": [("can_preview", "Can preview proposals")]},
        ),
    ]