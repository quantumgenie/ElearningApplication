# Generated by Django 5.0.6 on 2024-09-05 21:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elearning_platform', '0009_rename_user_material_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='status',
            field=models.TextField(blank=True, null=True),
        ),
    ]
