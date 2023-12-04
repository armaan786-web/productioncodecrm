# Generated by Django 4.2.5 on 2023-10-05 08:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_app', '0012_document_enquiry_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='Address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='City',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='branch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='crm_app.branch'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='contact_no',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='country',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='file',
            field=models.ImageField(blank=True, null=True, upload_to='media/Employee/profile_pic/'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='state',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='status',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='employee',
            name='zipcode',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
