import subprocess
import pandas as pd
import logging
import re
import os
import csv
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import Http404
from django.db.utils import IntegrityError
from myapp.forms import EmployeeForm, ServeurForm
from myapp.models import Employee, EtatSysteme, Filiale, Serveur, Notification,CriticalNotification
from django.http import JsonResponse
import random
import string

def close_notification(request):
    if request.method == 'POST':
        request.session.pop('notification', None)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

def send_notification(request, etat_id):
    if request.session.get('role') != 'ADMIN':
        messages.error(request, "Vous n'avez pas l'autorisation d'envoyer des notifications.")
        return redirect('taches_view')

    etat = get_object_or_404(EtatSysteme, id=etat_id)
    Notification.objects.create(
        filiale=etat.filiale,
        message=f"L'état de votre serveur{etat.adresse_ip}est préoccupant. Merci d'intervenir dès que possible."
    )
    messages.success(request, "Notification envoyée avec succès.")
    return redirect('taches_view')

def generate_temporary_password(length=8):
    """Generate a random password of given length"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def password_reset_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            employee = Employee.objects.get(email=email)
            temp_password = generate_temporary_password()
            employee.set_password(temp_password)
            employee.save()
            send_mail(
                'Votre mot de passe oublié',
                f'Bonjour {employee.name},\n\nVotre mot de passe est : {temp_password}\n\nCordialement,\nVotre équipe',
                'poulina@gmail.com',
                [email],
                fail_silently=False,
            )
            messages.success(request, "Un email contenant votre mot de passe a été envoyé.")
            return redirect('login')
        except Employee.DoesNotExist:
            messages.error(request, "Aucun compte trouvé avec cet email.")
    return render(request, 'password_reset.html')
def taches_view(request):
    if not request.session.get('employee_id'):
        return redirect('login')
    
    if request.session.get('role') == 'ADMIN':
        etats_list = EtatSysteme.objects.all().order_by('-date')
        # Check for critical servers
        critical_servers = Serveur.objects.filter(statut='indispo')
        if critical_servers.exists():
            request.session['critical_notification'] = "Un ou plusieurs serveurs sont en état critique. Merci d'intervenir dès que possible."
    else:
        filiale_id = request.session.get('filiale_id')
        etats_list = EtatSysteme.objects.filter(filiale__id=filiale_id).order_by('-date')
        # Check for critical servers for users
        critical_servers = Serveur.objects.filter(filiale__id=filiale_id, statut='indispo')
        if critical_servers.exists():
            request.session['notification'] = "L'état de votre serveur est préoccupant. Merci d'intervenir dès que possible."

    paginator = Paginator(etats_list, 10)  # 10 tâches par page
    page = request.GET.get('page')
    try:
        etats = paginator.page(page)
    except PageNotAnInteger:
        etats = paginator.page(1)
    except EmptyPage:
        etats = paginator.page(paginator.num_pages)

    return render(request, 'tache.html', {'etats': etats})







def extract_system_information(ip_address, username, password):
    command = f"systeminfo /S {ip_address} /U {username} /P {password} "
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        output = output.decode('cp437', errors='replace')
        if process.returncode == 0:
            print("Command output:")
            print(output)
        else:
            print("Command error output:")
            print(error.decode('cp437'))
            if "RPC server is unavailable" in error.decode('cp437'):
                return {
                    "memoire_phy_tot": "Non spécifié",
                    "memoire_phy_dispo": "Non spécifié",
                    "memoire_virt_tot": "Non spécifié",
                    "memoire_virt_dispo": "Non spécifié",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            return None
    except Exception as e:
        print(f"Error executing systeminfo for {ip_address}: {e}")
        return None

    return parse_system_info(output)


def parse_system_info(output):
    data = {
        "memoire_phy_tot": extract_value(output, 'Mémoire physique totale'),
        "memoire_phy_dispo": extract_value(output, 'Mémoire physique disponible'),
        "memoire_virt_tot": extract_value2(output, 'Mémoire virtuelle : taille maximale'),
        "memoire_virt_dispo": extract_value2(output, 'Mémoire virtuelle : disponible')
    }
    data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return data

def extract_value(output, key):
    regex = rf"{key}:\s*([\d\s]+Mo)"
    match = re.search(regex, output)
    
    if match:
        return match.group(1).strip()
    return "Non spécifié"

def extract_value2(output, key):
    normalized_key = ' '.join(key.lower().split()) + ':'
    lines = output.split('\n')
    
    for line in lines:
        normalized_line = ' '.join(line.lower().split())
        if normalized_key in normalized_line:
            parts = normalized_line.split(normalized_key)
            if len(parts) > 1:
                return parts[1].strip()
    return "Non spécifié"


def insert_system_info_into_db(data, serveur):
    if data:
        if not EtatSysteme.objects.filter(adresse_ip=serveur.adresse, date=data["date"]).exists():
            try:
                EtatSysteme.objects.create(
                    adresse_ip=serveur.adresse,
                    memoire_phy_tot=data["memoire_phy_tot"],
                    memoire_phy_dispo=data["memoire_phy_dispo"],
                    memoire_virt_tot=data["memoire_virt_tot"],
                    memoire_virt_dispo=data["memoire_virt_dispo"],
                    date=data["date"],
                    filiale=serveur.filiale
                )
                if "Non spécifié" in data.values():
                    serveur.statut = "indispo"
                else:
                    serveur.statut = "dispo"
                serveur.save()
                append_system_info_to_csv(data, serveur)  # Ajouter les données au CSV
                print("New data inserted successfully into the database.")
            except IntegrityError as e:
                print(f"Integrity error occurred: {e}")
        else:
            print(f"Entry with adresse_ip {serveur.adresse} and date {data['date']} already exists.")



def clean_memory_value(value):
    # Supprimer les caractères non numériques et les espaces
    clean_value = re.sub(r'[^\d]', '', value)
    # Retourner la valeur nettoyée ou 0 si la valeur nettoyée est vide
    return clean_value if clean_value else '0'

def get_next_id(df, id_column='id'):
    if df.empty:
        return 1
    else:
        return df[id_column].max() + 1

def append_system_info_to_csv(data, serveur):
    csv_file = 'EtatSysteme_data.csv'
    file_exists = os.path.isfile(csv_file)
    
    if file_exists:
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=['id', 'date', 'adresse_ip', 'memoire_phy_tot', 'memoire_phy_dispo', 'memoire_virt_tot', 'memoire_virt_dispo', 'filiale_id'])

    # Nettoyage des valeurs de mémoire
    memoire_phy_tot = clean_memory_value(data['memoire_phy_tot'])
    memoire_phy_dispo = clean_memory_value(data['memoire_phy_dispo'])
    memoire_virt_tot = clean_memory_value(data['memoire_virt_tot'])
    memoire_virt_dispo = clean_memory_value(data['memoire_virt_dispo'])
    
    # Générer le prochain ID unique
    new_id = get_next_id(df)
    new_row = {
        'id': new_id,
        'date': data['date'],
        'adresse_ip': serveur.adresse,
        'memoire_phy_tot': memoire_phy_tot,
        'memoire_phy_dispo': memoire_phy_dispo,
        'memoire_virt_tot': memoire_virt_tot,
        'memoire_virt_dispo': memoire_virt_dispo,
        'filiale_id': int(serveur.filiale.id) if serveur.filiale else 'Inconnu'
    }
    
    # Vérifier les doublons dans le CSV
    if not df[(df['adresse_ip'] == new_row['adresse_ip']) & (df['date'] == new_row['date'])].empty:
        print("Duplicate entry found in CSV. Skipping insertion.")
    else:
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(csv_file, index=False)
        print("New data inserted successfully into the CSV.")

def send_critical_server_notification(request):
    if request.session.get('role') != 'ADMIN':
        messages.error(request, "Vous n'avez pas l'autorisation d'envoyer des notifications.")
        return redirect('taches_view')

    critical_servers = Serveur.objects.filter(statut='indispo')
    if critical_servers.exists():
        Notification.objects.create(
            filiale=None,  # Peut-être lié à une filiale si besoin
            message="Un ou plusieurs serveurs sont en état critique. Merci d'intervenir dès que possible."
        )
        messages.success(request, "Notification envoyée pour les serveurs en état critique.")
    else:
        messages.info(request, "Aucun serveur en état critique.")

    return redirect('taches_view')
def executer_commande(request):
    if not request.session.get('employee_id'):
        return redirect('login')

    role = request.session.get('role')
    filiale_id = request.session.get('filiale_id')

    if role == 'ADMIN':
        serveurs = Serveur.objects.all()
    elif role == 'USER':
        serveurs = Serveur.objects.filter(filiale_id=filiale_id)
    else:
        serveurs = []

    for serveur in serveurs:
        ip_address = serveur.adresse
        username = serveur.username 
        password = serveur.password
        data = extract_system_information(ip_address, username, password)
        if data is not None:
            insert_system_info_into_db(data, serveur)
            append_system_info_to_csv(data, serveur)  # Ajout des données dans le CSV
            if "Non spécifié" in data.values():
                CriticalNotification.objects.create(
                    filiale=serveur.filiale,
                    message=f"Serveur {serveur.nomserveur} (IP: {serveur.adresse}) a des données non spécifiées."
                )
        else:
            data = {
                "memoire_phy_tot": "Non spécifié",
                "memoire_phy_dispo": "Non spécifié",
                "memoire_virt_tot": "Non spécifié",
                "memoire_virt_dispo": "Non spécifié",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            insert_system_info_into_db(data, serveur)
            append_system_info_to_csv(data, serveur)  # Ajout des données dans le CSV
            CriticalNotification.objects.create(
                filiale=serveur.filiale,
                message=f"Serveur {serveur.nomserveur} (IP: {serveur.adresse}) a des données non spécifiées."
            )
        serveur.save()
        update_server_in_csv(serveur)  # Mettre à jour le serveur dans le CSV

    messages.success(request, "Informations système mises à jour avec succès.")
    return redirect('taches_view')


def close_critical_notification(request):
    if request.method == 'POST':
        request.session.pop('critical_servers', None)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)


def add_employee_to_csv(employee):
    csv_file = 'Employee_data.csv'
    df = pd.read_csv(csv_file)
    new_row = pd.Series(employee.__dict__).drop('_state').to_frame().T
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(csv_file, index=False)

def addnew(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            new_employee = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                new_employee.password = make_password(password)
            new_employee.save()
            add_employee_to_csv(new_employee)  # Ajout de l'employé dans le CSV
            messages.success(request, 'Nouvel employé ajouté avec succès!')
            return redirect('employee_view')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = EmployeeForm()
    filiales = Filiale.objects.all()  # Obtenez toutes les filiales
    return render(request, 'employee.html', {'form': form, 'filiales': filiales})



def update_employee_in_csv(employee):
    csv_file = 'Employee_data.csv'
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['id', 'name', 'email', 'contact', 'filiale_id', 'role', 'password'])
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=['id', 'name', 'email', 'contact', 'filiale_id', 'role', 'password'])

    # Rechercher l'index de l'employé existant
    df['id'] = df['id'].astype(int)
    index = df[df['id'] == employee.id].index
    if not index.empty:
        index = index[0]
        # Remplacer la ligne existante avec les nouvelles informations de l'employé
        df.loc[index, 'name'] = employee.name
        df.loc[index, 'email'] = employee.email
        df.loc[index, 'contact'] = employee.contact
        df.loc[index, 'filiale_id'] = employee.filiale.id if employee.filiale else None
        df.loc[index, 'role'] = employee.role
        df.loc[index, 'password'] = employee.password
    else:
        # Ajouter une nouvelle ligne si l'employé n'est pas trouvé
        new_row = pd.Series(employee.__dict__).drop('_state').to_frame().T
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(csv_file, index=False)

def update(request, id):
    employee = get_object_or_404(Employee, id=id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            updated_employee = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                updated_employee.set_password(password)  # Met à jour le mot de passe seulement s'il est fourni
            updated_employee.save()
            update_employee_in_csv(updated_employee)
            messages.success(request, 'Employé mis à jour avec succès!')
            return redirect('employee_view')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employee.html', {'form': form, 'employee': employee})

def remove_employee_from_csv(employee_id):
    csv_file = 'Employee_data.csv'
    df = pd.read_csv(csv_file)
    df = df[df['id'] != employee_id]
    df.to_csv(csv_file, index=False)

def destroy(request, id):  
    try:
        employee = Employee.objects.get(id=id)
    except Employee.DoesNotExist:
        raise Http404("L'employé n'existe pas")
    if request.method == "POST":
        employee.delete()
        remove_employee_from_csv(id)
        messages.success(request, "Employé supprimé avec succès!")
        return redirect('employee_view')
    return redirect('employee_view')

def edit_employee(request, id):  
    employee = get_object_or_404(Employee, id=id)  
    employees = Employee.objects.all()
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)  
        if form.is_valid():  
            form.save()  
            messages.success(request, "Employé mis à jour avec succès!")
            return render(request, 'employee.html', {'employees': employees})
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employee.html', {'form': form, 'employee': employee, 'employees': employees})


def login_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('pass')
        try:
            employee = Employee.objects.get(name=name)
            if check_password(password, employee.password):
                request.session['employee_id'] = employee.id
                request.session['filiale_id'] = employee.filiale.id if employee.filiale else None
                request.session['role'] = employee.role
                request.session['employee_name'] = employee.name

                # Récupérer la notification la plus récente pour la filiale de l'utilisateur
                notifications = Notification.objects.filter(filiale=employee.filiale)
                if notifications.exists():
                    request.session['notification'] = notifications.latest('created_at').message

                # Vérifier les serveurs critiques pour les administrateurs
                if request.session.get('role') == 'ADMIN':
                    critical_servers = Serveur.objects.filter(statut='indispo')
                    if critical_servers.exists():
                        request.session['critical_notification'] = "Un ou plusieurs serveurs sont en état critique. Merci d'intervenir dès que possible."

                return redirect('test')
            else:
                messages.error(request, "Mot de passe incorrect.")
        except Employee.DoesNotExist:
            messages.error(request, "Nom d'utilisateur non trouvé.")
    return render(request, 'login.html')

def out(request):
    request.session.flush()
    return redirect('login')


def employee_view(request):
    if not request.session.get('employee_id'):
        return redirect('login')
    
    filiales = Filiale.objects.all()
    if request.session.get('role') == 'ADMIN':
        employees_list = Employee.objects.all()
    else:
        filiale_id = request.session.get('filiale_id')
        employees_list = Employee.objects.filter(filiale_id=filiale_id)

    paginator = Paginator(employees_list, 10)  # 10 employés par page
    page = request.GET.get('page')
    try:
        employees = paginator.page(page)
    except PageNotAnInteger:
        employees = paginator.page(1)
    except EmptyPage:
        employees = paginator.page(paginator.num_pages)

    return render(request, 'employee.html', {'employees': employees, 'filiales': filiales})

def add_server_to_csv(server):
    csv_file = 'Serveur_data.csv'
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['id', 'nomserveur', 'adresse', 'date', 'unite', 'filiale_id', 'username', 'password'])
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=['id', 'nomserveur', 'adresse', 'date', 'unite', 'filiale_id', 'username', 'password'])

    new_row = pd.Series(server.__dict__).drop('_state').to_frame().T
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(csv_file, index=False)


def remove_server_from_csv(server_id):
    csv_file = 'Serveur_data.csv'
    df = pd.read_csv(csv_file)
    df = df[df['id'] != server_id]
    df.to_csv(csv_file, index=False)

def ADD(request):
    if request.method == 'POST':
        form = ServeurForm(request.POST)
        if form.is_valid():
            new_server = form.save(commit=False)
            new_server.save()
            add_server_to_csv(new_server)
            messages.success(request, 'Nouveau serveur ajouté avec succès!')
            return redirect('serveur_view')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ServeurForm()
    return render(request, 'serveur.html', {'form': form})

def update_server_in_csv(server):
    csv_file = 'Serveur_data.csv'
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['id', 'nomserveur', 'adresse', 'date', 'unite', 'filiale_id', 'username', 'password'])
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=['id', 'nomserveur', 'adresse', 'date', 'unite', 'filiale_id', 'username', 'password'])

    df['id'] = df['id'].astype(int)
    index = df[df['id'] == server.id].index
    if not index.empty:
        index = index[0]
        df.loc[index, 'nomserveur'] = server.nomserveur
        df.loc[index, 'adresse'] = server.adresse
        df.loc[index, 'date'] = server.date
        df.loc[index, 'unite'] = server.unite
        df.loc[index, 'filiale_id'] = server.filiale.id if server.filiale else None
        df.loc[index, 'username'] = server.username
        df.loc[index, 'password'] = server.password
    else:
        new_row = pd.Series(server.__dict__).drop('_state').to_frame().T
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(csv_file, index=False)

def Update(request, id):
    serveur = get_object_or_404(Serveur, id=id)
    if request.method == 'POST':
        form = ServeurForm(request.POST, instance=serveur)
        if form.is_valid():
            updated_server = form.save(commit=False)

            # Only update the password if it is provided
            password = form.cleaned_data.get('password')
            if password:
                updated_server.password = password

            updated_server.save()
            update_server_in_csv(updated_server)
            messages.success(request, 'Serveur mis à jour avec succès!')
            return redirect('serveur_view')
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ServeurForm(instance=serveur)
    return render(request, 'serveur.html', {'form': form, 'serveur': serveur})



def Delete(request, id):
    try:
        serveur = Serveur.objects.get(id=id)
    except Serveur.DoesNotExist:
        raise Http404("Le serveur n'existe pas")
    if request.method == "POST":
        serveur.delete()
        remove_server_from_csv(id)
        messages.success(request, "Serveur supprimé avec succès!")
        return redirect('serveur_view')
    return redirect('serveur_view')

def Edit(request, id):
    serveur = get_object_or_404(Serveur, id=id)
    serveurs = Serveur.objects.all()
    if request.method == 'POST':
        form = ServeurForm(request.POST, instance=serveur)
        if form.is_valid():
            form.save()
            update_server_in_csv(serveur)  # Mettez à jour le CSV ici
            messages.success(request, "Serveur mis à jour avec succès!")
            return render(request, 'serveur.html', {'serveurs': serveurs})
    else:
        form = ServeurForm(instance=serveur)
    return render(request, 'serveur.html', {'form': form, 'serveur': serveur, 'serveurs': serveurs})

def serveur_view(request):
    if not request.session.get('employee_id'):
        return redirect('login')

    filiales = Filiale.objects.all()
    user_role = request.session.get('role')

    if user_role == 'ADMIN':
        serveurs = Serveur.objects.all()
    else:
        filiale_id = request.session.get('filiale_id')
        serveurs = Serveur.objects.filter(filiale_id=filiale_id)

    return render(request, 'serveur.html', {'serveurs': serveurs, 'filiales': filiales, 'user_role': user_role})



def tableau_de_bord(request):
    return render(request, 'tableau_de_bord.html')

def test(request):
    notification = request.session.pop('notification', None)
    critical_notification = request.session.pop('critical_notification', None)
    return render(request, 'test.html', {'notification': notification, 'critical_notification': critical_notification})
