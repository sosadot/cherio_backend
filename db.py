import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="username",
        password="password",
        database="database"
    )