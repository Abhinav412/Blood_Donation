# db/connection.py

import mysql.connector
import streamlit as st
from mysql.connector import Error
import os

class DatabaseConnection:
    @staticmethod
    def init_database():
        """Initialize the database by running the SQL script"""
        try:
            
            config = {
                'host': 'localhost',
                'user': 'root@localhost',  
                'password': 'Resh@1234',  
            }
            
            
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor()
            
        
            cursor.execute("CREATE DATABASE IF NOT EXISTS blood_donation_system")
            cursor.execute("USE blood_donation_system")
            
            sql_file_path = os.path.join(os.path.dirname(__file__), 'functions.sql')
            with open(sql_file_path, 'r') as sql_file:
                sql_commands = sql_file.read()
                
                commands = sql_commands.split(';')
                
                for command in commands:
                    if command.strip():
                        cursor.execute(command)
                        
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Error as e:
            st.error(f"Error initializing database: {e}")
            return False

    @staticmethod
    @st.cache_resource
    def get_connection():
        """Create a database connection that can be reused"""
        try:
            conn = mysql.connector.connect(
                host='localhost',
                user='root@localhost',  
                password='Resh@1234', 
                database='blood_donation_system'
            )
            return conn
        except Error as e:
            st.error(f"Error connecting to database: {e}")
            return None

    @staticmethod
    def execute_query(query, params=None, fetch=False):
        """Execute a database query with error handling"""
        conn = DatabaseConnection.get_connection()
        if conn is None:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                conn.commit()
                cursor.close()
                return True
                
        except Error as e:
            st.error(f"Error executing query: {e}")
            return None