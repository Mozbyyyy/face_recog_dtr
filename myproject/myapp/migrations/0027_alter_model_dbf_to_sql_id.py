# Generated by Django 4.2.7 on 2024-01-04 04:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0026_model_dbf_to_sql'),
    ]

    operations = [
        migrations.AlterField(
            model_name='model_dbf_to_sql',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]