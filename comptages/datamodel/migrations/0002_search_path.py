# Generated by Django 3.2.4 on 2021-06-09 15:38

from django.db import migrations
from django.db import connection

def alter_search_path(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(f"ALTER DATABASE {connection.settings_dict['NAME']} SET search_path TO comptages,transfer,public,topology;")


class Migration(migrations.Migration):

    dependencies = [
        ('comptages', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(alter_search_path)
    ]