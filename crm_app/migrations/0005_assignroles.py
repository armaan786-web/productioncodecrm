# Generated by Django 4.0.2 on 2023-09-29 10:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crm_app', '0004_alter_enquiry_lead_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssignRoles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('menu_name', models.CharField(choices=[('Dashboard', 'Dashboard'), ('Enquiry', 'Enquiry'), ('Application Management', 'Application Management'), ('Employee Management', 'Employee Management'), ('Master Module', 'Master Module'), ('Add Questions', 'Add Questions'), ('Roles Management', 'Roles Management'), ('Edit Client', 'Edit Client'), ('Client Profile', 'Client Profile'), ('Profile', 'Profile'), ('View Employee', 'View Employee'), ('General', 'General'), ('Add Leads', 'Add Leads'), ('Agent Management', 'Agent Management'), ('Personal Detail', 'Personal Detail'), ('Commission Management', 'Commission Management'), ('Add Commission', 'Add Commission'), ('Commission', 'Commission'), ('Add Follow up', 'Add Follow up'), ('Follow ups', 'Follow ups'), ('Packages', 'Packages'), ('View Notification', 'View Notification'), ('Chatting', 'Chatting'), ('Chat', 'Chat'), ('Settings', 'Settings'), ('Add Appointment', 'Add Appointment'), ('View Appointment', 'View Appointment'), ('Update Case Status', 'Update Case Status'), ('Add Enquiry', 'Add Enquiry'), ('Report', 'Report'), ('Appointments', 'Appointments')], max_length=100)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crm_app.department')),
                ('users', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]