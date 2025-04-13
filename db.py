import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="cherio",
        password="cherio",
        database="cheriodb"
    )
