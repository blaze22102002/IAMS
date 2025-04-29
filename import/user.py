import mysql.connector
import pandas as pd
import uuid
import os
import django
import sys
from django.contrib.auth.hashers import make_password

# Add the project root directory to the Python path
sys.path.append(r"C:\Users\bbnit\Desktop\AIAMS")  # Path to your project root

# Now set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')  # This should match the actual location of settings.py
django.setup()
# Connect to MySQL
conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="J9v@r#L2p!qX7d&B",
    database="asset_db"
)
cursor = conn.cursor()

# Create table (updated structure to match insert)
cursor.execute("""
CREATE TABLE IF NOT EXISTS api_user (
    uid CHAR(32) PRIMARY KEY,
    empid VARCHAR(150) UNIQUE,
    name VARCHAR(150),
    email VARCHAR(255),
    password VARCHAR(255),
    last_login DATETIME DEFAULT NULL,
    is_superuser BOOLEAN DEFAULT FALSE,
    is_staff BOOLEAN DEFAULT FALSE
)
""")

# Read CSV
csv_file = r"C:\Users\bbnit\Downloads\assets_export.csv"  # Make sure the CSV file path is correct
df = pd.read_csv(csv_file)

# Insert data into MySQL
for _, row in df.iterrows():
    uid = uuid.uuid4().hex  # Generate a unique user ID (without dashes)
    hashed_password = make_password(str(row['password']))  # Hash the password

    cursor.execute("""
        INSERT INTO api_user (uid, empid, name, email, password, last_login, is_superuser, is_staff)
        VALUES (%s, %s, %s, %s, %s, NULL, FALSE, FALSE)
    """, (
        uid,
        row['empid'],
        row['name'],
        row['email'],
        hashed_password
    ))

# Commit the changes and close the connection
conn.commit()
cursor.close()
conn.close()

print("Users imported successfully!")
