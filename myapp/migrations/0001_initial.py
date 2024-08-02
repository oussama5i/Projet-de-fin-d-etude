# Generated by Django 5.0.4 on 2024-05-03 15:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EtatSysteme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('adresse_ip', models.CharField(blank=True, max_length=100, null=True)),
                ('memoire_phy_tot', models.CharField(blank=True, max_length=100, null=True)),
                ('memoire_phy_dispo', models.CharField(blank=True, max_length=100, null=True)),
                ('memoire_virt_tot', models.CharField(blank=True, max_length=100, null=True)),
                ('memoire_virt_dispo', models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                'db_table': 'myapp_etatsysteme',
            },
        ),
        migrations.CreateModel(
            name='Filiale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('contact', models.CharField(max_length=15)),
                ('role', models.CharField(choices=[('ADMIN', 'Admin'), ('USER', 'User')], default='USER', max_length=5)),
                ('password', models.CharField(max_length=128)),
                ('filiale', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='myapp.filiale')),
            ],
            options={
                'db_table': 'tblemployee',
            },
        ),
        migrations.CreateModel(
            name='Serveur',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nomserveur', models.CharField(max_length=100)),
                ('adresse', models.CharField(max_length=100)),
                ('date', models.DateField()),
                ('unite', models.CharField(max_length=50)),
                ('filiale', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='serveurs', to='myapp.filiale')),
                ('username', models.CharField(max_length=(50))),
                ('password', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='myapp.employee')),
                ('filiale', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.filiale')),
            ],
        ),
    ]
