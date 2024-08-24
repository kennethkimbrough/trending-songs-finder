
import mysql.connector
from mysql.connector import Error
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def save(data):
    try:
        mydb = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        mycursor = mydb.cursor()
        if len(data) > 0:
            for row in data:
                sql = "INSERT INTO records (name, duration, url) VALUES (%s,%s,%s)"
                val = (row[0], row[1], row[2])
                mycursor.execute(sql, val)
            mydb.commit()
    except Error as e:
        print(f"Error saving data to database: {e}")
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()
