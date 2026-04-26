import os
import mysql.connector

def bd_teacheasy():
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", 26878)),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            ssl_disabled=False
        )
        return conexion
    except mysql.connector.Error as e:
        print(e)
        return None