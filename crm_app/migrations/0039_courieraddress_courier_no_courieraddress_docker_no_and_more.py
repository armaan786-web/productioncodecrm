# Generated by Django 4.0.2 on 2023-10-14 04:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_app', '0038_alter_casecategorydocument_subcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='courieraddress',
            name='courier_no',
            field=models.CharField(default=1, max_length=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courieraddress',
            name='docker_no',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courieraddress',
            name='receiver_address',
            field=models.CharField(default=1, max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courieraddress',
            name='receiver_no',
            field=models.CharField(default=1, max_length=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courieraddress',
            name='sender_address',
            field=models.CharField(default=1, max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courieraddress',
            name='sender_no',
            field=models.CharField(default=1, max_length=15),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='courieraddress',
            name='status',
            field=models.CharField(choices=[('Pick', 'Pick'), ('In Transit', 'In Transit'), ('Receive', 'Receive')], default='Pick', max_length=50),
            preserve_default=False,
        ),
    ]
