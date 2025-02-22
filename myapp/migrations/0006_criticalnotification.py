# Generated by Django 5.0.4 on 2024-07-13 00:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_employee_clear_password_alter_serveur_nomserveur'),
    ]

    operations = [
        migrations.CreateModel(
            name='CriticalNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('filiale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='critical_notifications', to='myapp.filiale')),
            ],
        ),
    ]
