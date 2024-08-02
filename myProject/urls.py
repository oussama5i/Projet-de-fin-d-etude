from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from myapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('out/', views.out, name='out'),
    path('addnew/', views.addnew, name='addnew'),
    path('update/<int:id>/', views.update, name='update'),
    path('delete/<int:id>/', views.destroy, name='destroy'),
    path('employee/', views.employee_view, name='employee_view'),
    path('serveur/', views.serveur_view, name='serveur_view'),
    path('add/', views.ADD, name='add'),
    path('test/', views.test, name='test'),
    path('edit_serveur/<int:id>/', views.Edit, name='edit_serveur'),
    path('edit_employee/<int:id>/', views.edit_employee, name='edit_employee'),
    path('delete_serveur/<int:id>/', views.Delete, name='delete_serveur'),
    path('update_serveur/<int:id>/', views.Update, name='update_serveur'),
    path('tache/', views.taches_view, name='taches_view'),
    path('executer/', views.executer_commande, name='executer'),
    path('tableau-de-bord/', views.tableau_de_bord, name='tableau_de_bord'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('send_notification/<int:etat_id>/', views.send_notification, name='send_notification'),
    path('close_notification/', views.close_notification, name='close_notification'),
    path('send_critical_notification/', views.send_critical_server_notification, name='send_critical_notification'),
    path('close_critical_notification/', views.close_critical_notification, name='close_critical_notification'),
    path('send_critical_notification/', views.send_critical_server_notification, name='send_critical_notification'),
# Nouvelle URL
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
