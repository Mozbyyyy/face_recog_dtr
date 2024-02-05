# Generated by Django 4.2.7 on 2024-01-07 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0027_alter_model_dbf_to_sql_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='model_dbf_to_sql',
            old_name='name',
            new_name='ACCTNO',
        ),
        migrations.RenameField(
            model_name='model_dbf_to_sql',
            old_name='bank',
            new_name='UDATE',
        ),
        migrations.RemoveField(
            model_name='model_dbf_to_sql',
            name='status',
        ),
        migrations.AddField(
            model_name='model_dbf_to_sql',
            name='OLDACCT',
            field=models.DecimalField(decimal_places=1, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='model_dbf_to_sql',
            name='UDIBAL',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]
