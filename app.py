import streamlit as st
import mysql.connector as sqltor 

st.title("Blood_donation")
username = st.text_input("Username")
password = st.text_input("Password", type='password')