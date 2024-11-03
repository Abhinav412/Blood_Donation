import streamlit as st
import mysql.connector
from datetime import datetime, date
import pandas as pd
from hashlib import sha256

# Database connection
@st.cache_resource
def init_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root@localhost",
        password="Resh@134",
        database="blood_donation_system"
    )

# Helper functions
def hash_password(password):
    return sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE username = %s AND password_hash = %s",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    cursor.close()
    return user


def main():
    st.title("Blood Donation Management System")
    
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login()
    else:
        show_dashboard()

def show_login():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")

def show_dashboard():
    st.sidebar.title(f"Welcome, {st.session_state.user['username']}")
    user_type = st.session_state.user['user_type']
    
    menu_options = {
        'donor': ['Profile', 'Donate Blood', 'Donation History'],
        'hospital_staff': ['Blood Requests', 'Inventory Status', 'Request History'],
        'blood_bank_staff': ['Inventory Management', 'Donor Records', 'Process Requests'],
        'admin': ['User Management', 'System Statistics', 'Blood Bank Management']
    }
    
    selection = st.sidebar.selectbox("Menu", menu_options[user_type])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.experimental_rerun()
    
    
    if user_type == 'donor':
        if selection == 'Profile':
            show_donor_profile()
        elif selection == 'Donate Blood':
            show_donation_form()
        else:
            show_donation_history()
    elif user_type == 'hospital_staff':
        if selection == 'Blood Requests':
            show_blood_request_form()
        elif selection == 'Inventory Status':
            show_inventory_status()
        else:
            show_request_history()

def show_donor_profile():
    st.subheader("Donor Profile")
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute(
        "SELECT * FROM donor_profiles WHERE user_id = %s",
        (st.session_state.user['user_id'],)
    )
    profile = cursor.fetchone()
    
    if profile:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Name: {profile['full_name']}")
            st.write(f"Blood Type: {profile['blood_type']}")
            st.write(f"Date of Birth: {profile['date_of_birth']}")
        with col2:
            st.write(f"Contact: {profile['contact_number']}")
            st.write(f"Last Donation: {profile['last_donation_date']}")
            st.write(f"Eligible to Donate: {'Yes' if profile['is_eligible'] else 'No'}")
    
    cursor.close()

def show_donation_form():
    st.subheader("Schedule Blood Donation")
    
    blood_banks = get_blood_banks()
    selected_bank = st.selectbox("Select Blood Bank", blood_banks)
    
    donation_date = st.date_input("Select Donation Date", min_value=date.today())
    
    if st.button("Schedule Donation"):
        if schedule_donation(selected_bank, donation_date):
            st.success("Donation scheduled successfully!")
        else:
            st.error("Unable to schedule donation. Please try again.")

def show_inventory_status():
    st.subheader("Blood Inventory Status")
    
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT blood_type, SUM(units_available) as total_units
        FROM blood_inventory
        GROUP BY blood_type
    """)
    
    inventory_data = cursor.fetchall()
    cursor.close()
    
    if inventory_data:
        df = pd.DataFrame(inventory_data)
        st.bar_chart(df.set_index('blood_type'))
        
        st.table(df)
    else:
        st.write("No inventory data available")

def show_blood_request_form():
    st.subheader("Request Blood")
    
    blood_type = st.selectbox("Blood Type Required", 
                             ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
    units = st.number_input("Units Required", min_value=1, value=1)
    priority = st.selectbox("Priority Level", ['low', 'medium', 'high', 'critical'])
    
    if st.button("Submit Request"):
        if submit_blood_request(blood_type, units, priority):
            st.success("Blood request submitted successfully!")
        else:
            st.error("Unable to submit request. Please try again.")

def get_blood_banks():
    conn = init_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT bank_id, name FROM blood_banks")
    banks = cursor.fetchall()
    cursor.close()
    return banks

def schedule_donation(bank_id, donation_date):
    conn = init_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO donation_records (donor_id, bank_id, donation_date) VALUES (%s, %s, %s)",
            (st.session_state.user['user_id'], bank_id, donation_date)
        )
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        cursor.close()

def submit_blood_request(blood_type, units, priority):
    conn = init_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO blood_requests 
               (requesting_hospital_id, blood_type, units_required, priority) 
               VALUES (%s, %s, %s, %s)""",
            (st.session_state.user['user_id'], blood_type, units, priority)
        )
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        cursor.close()

if __name__ == "__main__":
    main()