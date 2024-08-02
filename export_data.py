import pandas as pd
from sqlalchemy import create_engine

def export_selected_tables():
    # Connexion à la base de données en utilisant SQLAlchemy
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

if __name__ == "__main__":
    export_selected_tables()
