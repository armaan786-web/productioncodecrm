# Generated by Django 4.0.2 on 2023-10-12 05:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_app', '0027_alter_agent_activeinactive_alter_agent_profile_pic_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='visacategory',
            name='subcategory',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='visasubcategory',
            name='category_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_category', to='crm_app.visacategory'),
        ),
        migrations.AlterField(
            model_name='visasubcategory',
            name='subcategory_name',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pricing_subcategory', to='crm_app.visacategory'),
        ),
        migrations.AlterModelTable(
            name='visasubcategory',
            table='Pricing',
        ),
    ]