# Generated by Django 5.0.6 on 2024-05-13 01:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("nominate", "0020_rank_unique_rank"),
    ]

    operations = [
        migrations.AddField(
            model_name="rank",
            name="rank_date",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
