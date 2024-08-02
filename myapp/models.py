from django.conf import settings
from django.db import models
from django.contrib.auth.hashers import make_password

class Filiale(models.Model):
    nom = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

class Notification(models.Model):
    filiale = models.ForeignKey(Filiale, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.filiale} at {self.created_at}"
    
class CriticalNotification(models.Model):
    filiale = models.ForeignKey(Filiale, on_delete=models.CASCADE, related_name='critical_notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Critical Notification for {self.filiale} at {self.created_at}"
class Employee(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contact = models.CharField(max_length=15)
    filiale = models.ForeignKey(Filiale, on_delete=models.SET_NULL, null=True, related_name='employees')
    role = models.CharField(max_length=5, choices=ROLE_CHOICES, default='USER')
    password = models.CharField(max_length=128)
    clear_password = models.CharField(max_length=128, blank=True, null=True)  # Champ pour mot de passe en clair

    class Meta:
        db_table = "tblemployee"

    def set_password(self, raw_password):
        self.password = make_password(raw_password)  # Hachage du mot de passe
        self.clear_password = raw_password  # Stockage du mot de passe en clair

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='profile')
    filiale = models.ForeignKey(Filiale, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.employee.name + ' Profile'

class Serveur(models.Model):
    nomserveur = models.CharField(max_length=100,unique=True)
    adresse = models.CharField(max_length=100)
    date = models.DateField()
    unite = models.CharField(max_length=50)
    filiale = models.ForeignKey(Filiale, on_delete=models.SET_NULL, null=True, related_name='serveurs')
    username = models.CharField(max_length=50)  
    password = models.CharField(max_length=128)  
    statut = models.CharField(max_length=100, default="non spécifié")

    def __str__(self):
        return self.nomserveur

class EtatSysteme(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.CharField(max_length=100, blank=True, null=True)
    memoire_phy_tot = models.CharField(max_length=100, blank=True, null=True)
    memoire_phy_dispo = models.CharField(max_length=100, blank=True, null=True)
    memoire_virt_tot = models.CharField(max_length=100, blank=True, null=True)
    memoire_virt_dispo = models.CharField(max_length=100, blank=True, null=True)
    filiale = models.ForeignKey(Filiale, on_delete=models.CASCADE)

    class Meta:
        db_table = 'myapp_etatsysteme'

    def __str__(self):
        return f"{self.date} - {self.adresse_ip}"
