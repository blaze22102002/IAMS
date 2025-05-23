# Generated by Django 5.1.7 on 2025-05-15 13:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_user_role"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetAddition",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("asset_id", models.CharField(max_length=50, unique=True)),
                ("employee_id", models.CharField(max_length=50)),
                ("employee_name", models.CharField(max_length=100)),
                ("group", models.CharField(max_length=100)),
                ("business_impact", models.CharField(max_length=100)),
                ("asset_tag", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("product_name", models.CharField(max_length=100)),
                ("serial_number", models.CharField(max_length=100)),
                ("remarks", models.TextField(blank=True)),
                ("status", models.CharField(max_length=100)),
                ("it_poc_remarks", models.TextField(blank=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "branch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="api.branch"
                    ),
                ),
            ],
        ),
    ]
