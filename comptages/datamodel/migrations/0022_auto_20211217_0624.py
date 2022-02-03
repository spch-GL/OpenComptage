# Generated by Django 3.2.5 on 2021-12-17 05:24

import logging

from django.db import migrations


def get_console_logger():
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info("starting logger")
    return logger


def migrate_data(apps, schema_editor):
    logger = get_console_logger()
    count_details = []

    # We can't import the models directly as it may be a newer
    # version than this migration expects. We use the historical version.
    CountAggregateValueCls = apps.get_model('comptages', 'CountAggregateValueCls')
    CountDetail = apps.get_model('comptages', 'CountDetail')

    qs = CountAggregateValueCls.objects.all()
    logger.info('Start with count_aggregate_value_cls table')
    logger.info(f'Total rows: {len(qs)}')
    for idx, i in enumerate(qs):
        count_details.append(
            CountDetail(
                numbering=1,
                timestamp=i.id_count_aggregate.start,
                file_name=i.id_count_aggregate.file_name,
                import_status=i.id_count_aggregate.import_status,
                id_lane=i.id_count_aggregate.id_lane,
                id_count=i.id_count_aggregate.id_count,
                id_category=i.id_category,
                times=i.value,
                from_aggregate=True,
                )
            )

        if (idx % 1000) == 0:
            logger.info(f'{idx}')
            CountDetail.objects.bulk_create(count_details)
            count_details = []

    CountDetail.objects.bulk_create(count_details)
    count_details = []

    CountAggregateValueCnt = apps.get_model('comptages', 'CountAggregateValueCnt')
    qs = CountAggregateValueCnt.objects.all()
    logger.info('Start with count_aggregate_value_cnt table')
    logger.info(f'Total rows: {len(qs)}')
    for idx, i in enumerate(qs):
        count_details.append(
            CountDetail(
                numbering=1,
                timestamp=i.id_count_aggregate.start,
                file_name=i.id_count_aggregate.file_name,
                import_status=i.id_count_aggregate.import_status,
                id_lane=i.id_count_aggregate.id_lane,
                id_count=i.id_count_aggregate.id_count,
                times=i.value,
                from_aggregate=True,
                )
            )

        if (idx % 1000) == 0:
            logger.info(f'{idx}')
            CountDetail.objects.bulk_create(count_details)
            count_details = []

    CountDetail.objects.bulk_create(count_details)
    count_details = []

    CountAggregateValueDrn = apps.get_model('comptages', 'CountAggregateValueDrn')
    qs = CountAggregateValueDrn.objects.all()
    logger.info('Start with count_aggregate_value_drn table')
    logger.info(f'Total rows: {len(qs)}')
    for idx, i in enumerate(qs):
        count_details.append(
            CountDetail(
                numbering=1,
                timestamp=i.id_count_aggregate.start,
                file_name=i.id_count_aggregate.file_name,
                import_status=i.id_count_aggregate.import_status,
                id_lane=i.id_count_aggregate.id_lane,
                id_count=i.id_count_aggregate.id_count,
                times=i.value,
                from_aggregate=True,
                )
            )

        if (idx % 1000) == 0:
            logger.info(f'{idx}')
            CountDetail.objects.bulk_create(count_details)
            count_details = []

    CountDetail.objects.bulk_create(count_details)
    count_details = []

    CountAggregateValueLen = apps.get_model('comptages', 'CountAggregateValueLen')
    qs = CountAggregateValueLen.objects.all()
    logger.info('Start with count_aggregate_value_len table')
    logger.info(f'Total rows: {len(qs)}')
    for idx, i in enumerate(qs):
        count_details.append(
            CountDetail(
                numbering=1,
                timestamp=i.id_count_aggregate.start,
                length=int((i.low + i.high) / 2),
                file_name=i.id_count_aggregate.file_name,
                import_status=i.id_count_aggregate.import_status,
                id_lane=i.id_count_aggregate.id_lane,
                id_count=i.id_count_aggregate.id_count,
                times=i.value,
                from_aggregate=True,
                )
            )

        if (idx % 1000) == 0:
            logger.info(f'{idx}')
            CountDetail.objects.bulk_create(count_details)
            count_details = []

    CountDetail.objects.bulk_create(count_details)
    count_details = []

    CountAggregateValueSpd = apps.get_model('comptages', 'CountAggregateValueSpd')
    qs = CountAggregateValueSpd.objects.all()
    logger.info('Start with count_aggregate_value_spd table')
    logger.info(f'Total rows: {len(qs)}')
    for idx, i in enumerate(qs):
        count_details.append(
            CountDetail(
                numbering=1,
                timestamp=i.id_count_aggregate.start,
                speed=i.low + 5,
                file_name=i.id_count_aggregate.file_name,
                import_status=i.id_count_aggregate.import_status,
                id_lane=i.id_count_aggregate.id_lane,
                id_count=i.id_count_aggregate.id_count,
                times=i.value,
                from_aggregate=True,
                )
            )

        if (idx % 1000) == 0:
            logger.info(f'{idx}')
            CountDetail.objects.bulk_create(count_details)
            count_details = []

    CountDetail.objects.bulk_create(count_details)
    count_details = []


class Migration(migrations.Migration):

    dependencies = [
        ('comptages', '0021_alter_count_tjm'),
    ]

    operations = [
        migrations.RunPython(migrate_data),
        migrations.DeleteModel(name='CountAggregateValueCls'),
        migrations.DeleteModel(name='CountAggregateValueCnt'),
        migrations.DeleteModel(name='CountAggregateValueDrn'),
        migrations.DeleteModel(name='CountAggregateValueLen'),
        migrations.DeleteModel(name='CountAggregateValueSpd'),
        migrations.DeleteModel(name='CountAggregateValueSds'),
        migrations.DeleteModel(name='CountAggregate'),
    ]
