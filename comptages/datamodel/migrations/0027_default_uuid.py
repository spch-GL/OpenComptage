# Generated by Django 3.2.5 on 2022-02-25 06:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comptages', '0026_alter_modelclass_id'),
    ]

    operations = [
        migrations.RunSQL('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'),
        migrations.RunSQL(
            'ALTER TABLE class_category ALTER COLUMN id SET DEFAULT uuid_generate_v4();'
            ),
        migrations.RunSQL(
            'ALTER TABLE model_class ALTER COLUMN id SET DEFAULT uuid_generate_v4();'
            ),
        migrations.RunSQL(
            'ALTER TABLE sensor_type_class ALTER COLUMN id SET DEFAULT uuid_generate_v4();'
            ),
        migrations.RunSQL(
            'ALTER TABLE sensor_type_installation ALTER COLUMN id SET DEFAULT uuid_generate_v4();'
            ),
        migrations.RunSQL(
            'ALTER TABLE sensor_type_model ALTER COLUMN id SET DEFAULT uuid_generate_v4();'
            ),
    ]
