import pandas as pd
from sqlalchemy import create_engine
from myapp.models import Employee, Serveur, EtatSysteme
from django.db import transaction

disable_signals = False

def export_selected_tables():
    engine = create_engine('mysql+mysqlconnector://root:@localhost/django')
    
    tables = {
        'tblemployee': 'Employee_data.csv',
        'myapp_serveur': 'Serveur_data.csv',
        'myapp_etatsysteme': 'EtatSysteme_data.csv'
    }
    
    for table, filename in tables.items():
        query = f"SELECT * FROM {table}"
        df = pd.read_sql(query, engine)
        df.to_csv(filename, index=False)

def sync_data_from_csv():
    global disable_signals
    if disable_signals:
        return

    disable_signals = True  # Désactiver temporairement les signaux

    csv_files = {
        'Employee': 'Employee_data.csv',
        'Serveur': 'Serveur_data.csv',
        'EtatSysteme': 'EtatSysteme_data.csv'
    }

    for model_name, csv_file in csv_files.items():
        csv_data = pd.read_csv(csv_file)

        if model_name == 'Employee':
            Model = Employee
        elif model_name == 'Serveur':
            Model = Serveur
        elif model_name == 'EtatSysteme':
            Model = EtatSysteme

        with transaction.atomic():
            for index, row in csv_data.iterrows():
                if model_name == 'Employee':
                    # Check if an employee with the same email already exists
                    try:
                        instance = Model.objects.get(email=row['email'])
                        for field, value in row.items():
                            setattr(instance, field, value)
                        instance.save()
                    except Model.DoesNotExist:
                        Model.objects.create(**row.to_dict())
                else:
                    instance, created = Model.objects.update_or_create(
                        id=row['id'],
                        defaults=row.to_dict()
                    )

            csv_ids = csv_data['id'].tolist()
            Model.objects.exclude(id__in=csv_ids).delete()

    disable_signals = False  # Réactiver les signaux

