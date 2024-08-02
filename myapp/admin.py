from django.contrib import admin
from .models import UserProfile, Filiale, Employee, Serveur

admin.site.register(UserProfile)
admin.site.register(Filiale)
admin.site.register(Employee)
admin.site.register(Serveur)
from django.contrib import admin
from myapp.models import Notification

admin.site.register(Notification)