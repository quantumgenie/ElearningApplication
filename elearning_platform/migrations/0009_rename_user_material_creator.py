# Generated by Django 5.0.6 on 2024-08-31 21:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elearning_platform', '0008_alter_chat_user_alter_enrollment_student_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='material',
            old_name='user',
            new_name='creator',
        ),
    ]
