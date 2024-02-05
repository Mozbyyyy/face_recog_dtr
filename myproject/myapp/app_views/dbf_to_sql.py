from django.shortcuts import render
import tempfile
from myapp.models import model_dbf_to_sql
from simpledbf import Dbf5
from sqlalchemy import create_engine
import pandas as pd  # Add this line for the pandas library

def dbf_to_sql(request):
    if request.method == 'POST':
        # Assuming your form has an input field named 'dbf_file'
        dbf_file = request.FILES['dbf_file']

        # Save the contents of the InMemoryUploadedFile to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_dbf_file:
            temp_dbf_file.write(dbf_file.read())

        # Read DBF file using simpledbf with a different encoding
        dbf_data = Dbf5(temp_dbf_file.name, codec='iso-8859-1')  
        df = dbf_data.to_dataframe()

        engine = create_engine('sqlite:///djangodb.db')

        # Convert pandas DataFrame to SQL
        df.to_sql('md_dbf_to_sql', engine, index=False, if_exists='replace')

        # Loop through the DataFrame and create model instances
        for index, row in df.iterrows():
            udate_value = row['UDATE'] if pd.notna(row['UDATE']) else None
            oldacct_value = row['OLDACCT'] if pd.notna(row['OLDACCT']) else None

            model_dbf_to_sql.objects.create(
                ACCTNO=row['ACCTNO'],
                UDATE=udate_value,
                UDIBAL=row['UDIBAL'],
                OLDACCT=oldacct_value
            )

        return render(request, 'temp_myapp/dbf_to_sql.html')

    return render(request, 'temp_myapp/dbf_to_sql.html')
