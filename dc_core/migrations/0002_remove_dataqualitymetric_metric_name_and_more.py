# Generated by Django 5.1.5 on 2025-02-02 08:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dc_core", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dataqualitymetric",
            name="metric_name",
        ),
        migrations.RemoveField(
            model_name="dataqualitymetric",
            name="metric_value",
        ),
        migrations.RemoveField(
            model_name="dataqualitymetric",
            name="weight",
        ),
        migrations.AddField(
            model_name="dataqualitymetric",
            name="accuracy_score",
            field=models.FloatField(
                default=0.0,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(1),
                ],
                verbose_name="准确性分数",
            ),
        ),
        migrations.AddField(
            model_name="dataqualitymetric",
            name="completeness_score",
            field=models.FloatField(
                default=0.0,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(1),
                ],
                verbose_name="完整性分数",
            ),
        ),
        migrations.AddField(
            model_name="dataqualitymetric",
            name="consistency_score",
            field=models.FloatField(
                default=0.0,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(1),
                ],
                verbose_name="一致性分数",
            ),
        ),
        migrations.AddField(
            model_name="dataqualitymetric",
            name="total_score",
            field=models.FloatField(
                default=0.0,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(1),
                ],
                verbose_name="总分",
            ),
        ),
    ]
