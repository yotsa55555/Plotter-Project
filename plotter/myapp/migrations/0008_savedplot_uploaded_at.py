# Generated by Django 5.1 on 2024-10-24 16:45

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0007_remove_savedplot_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='savedplot',
            name='uploaded_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
