# Generated by Django 5.1.7 on 2025-04-04 08:31

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('analysis', '0007_drugname_reactionname_alter_demo_age_cod_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='year_end',
            field=models.IntegerField(default=-1, validators=[django.core.validators.MinValueValidator(2004), django.core.validators.MaxValueValidator(2025)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='query',
            name='year_start',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(2004), django.core.validators.MaxValueValidator(2025)]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='query',
            name='quarter_end',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(4)]),
        ),
        migrations.AlterField(
            model_name='query',
            name='quarter_start',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(4)]),
        ),
    ]
