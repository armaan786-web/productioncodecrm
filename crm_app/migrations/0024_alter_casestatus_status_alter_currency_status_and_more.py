# Generated by Django 4.2.5 on 2023-10-10 09:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_app', '0023_agent_adhar_card_back_agent_adhar_card_front_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casestatus',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='currency',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='documentcategory',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='followup_status',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='followuppayment_status',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='followuptype',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='news',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='offerbanner',
            name='status',
            field=models.BooleanField(default=True),
        ),
    ]
