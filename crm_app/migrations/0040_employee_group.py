# Generated by Django 4.0.2 on 2023-10-14 05:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_app', '0039_courieraddress_courier_no_courieraddress_docker_no_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm_app.group'),
        ),
    ]
