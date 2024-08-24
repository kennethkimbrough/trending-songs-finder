
import mysql.connector
from mysql.connector import Error
import logging
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.info("Successfully saved data to the database")
    except Error as e:
        logger.error(f"Error saving data to database: {e}")
    finally:
        if mydb.is_connected():
            mycursor.close()
            mydb.close()
