# Generated by Django 4.0.2 on 2023-10-13 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_app', '0036_remove_casecategorydocument_adharcard_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casecategorydocument',
            name='document',
            field=models.ManyToManyField(related_name='document', to='crm_app.Document'),
        ),
    ]