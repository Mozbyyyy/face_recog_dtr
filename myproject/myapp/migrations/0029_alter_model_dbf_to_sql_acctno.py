# Generated by Django 4.2.7 on 2024-01-07 19:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0028_rename_name_model_dbf_to_sql_acctno_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='model_dbf_to_sql',
            name='ACCTNO',
            field=models.DecimalField(decimal_places=1, max_digits=10, null=True),
        ),
    ]