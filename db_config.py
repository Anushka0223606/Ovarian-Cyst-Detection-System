import mysql.connector

def get_connection():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="anushka0223",
        database="ovarian_cyst_db"
    )

    return conn