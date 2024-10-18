import streamlit as st
import mysql.connector as sqltor 
from mysql.connector import Error

st.title("Blood_donation")
username = st.text_input("Username")
password = st.text_input("Password", type='password')

try:
    connection = sqltor.connect(host='127.0.0.1', database='blood_donation', user='example', password='Project@123')
    if connection.is_connected():
        db_info = connection.get_server_info()
        print(f"Connected to MySQL Server version {db_info}")
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        record = cursor.fetchone()
        print(f"You're connected to database: {record}")

except Error as e:
    print(f"Error while connecting to MySQL: {e}")

finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")