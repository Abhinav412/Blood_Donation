import streamlit as st
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime, timedelta
from contextlib import contextmanager

# Database connection
@st.cache_resource
def init_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="Resh@1234",
            database="blood_donation_system"
        )
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return None

conn = init_connection()

@contextmanager
def get_cursor(conn):
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
    finally:
        cursor.close()

# Helper functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def execute_query(query, params=None):
    if conn is None:
        st.error("Database connection not established.")
        return None

    with get_cursor(conn) as cursor:
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
        except Error as e:
            st.error(f"Error executing query: {e}")
            return None

# Authentication
def login(username, password):
    query = "SELECT * FROM users WHERE username = %s"
    results = execute_query(query, (username,))
    
    if results and len(results) > 0:
        user = results[0]
        if verify_password(password, user['password_hash'].encode('utf-8')):
            return user
    return None

def register(username, password, email, user_type):
    hashed_password = hash_password(password)
    query = "INSERT INTO users (username, password_hash, email, user_type) VALUES (%s, %s, %s, %s)"
    result = execute_query(query, (username, hashed_password, email, user_type))
    return result is not None and result > 0

# Donor functions
def get_donor_profile(user_id):
    query = "SELECT * FROM donor_profiles WHERE user_id = %s"
    results = execute_query(query, (user_id,))
    return results[0] if results else None

def update_donor_profile(user_id, full_name, dob, blood_type, contact, address, medical_history):
    query = """
    INSERT INTO donor_profiles 
    (user_id, full_name, date_of_birth, blood_type, contact_number, address, medical_history) 
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    full_name = VALUES(full_name),
    date_of_birth = VALUES(date_of_birth),
    blood_type = VALUES(blood_type),
    contact_number = VALUES(contact_number),
    address = VALUES(address),
    medical_history = VALUES(medical_history)
    """
    return execute_query(query, (user_id, full_name, dob, blood_type, contact, address, medical_history))

def schedule_donation(donor_id, bank_id, donation_date):
    query = "INSERT INTO donation_records (donor_id, bank_id, donation_date, blood_type, units_donated) VALUES (%s, %s, %s, (SELECT blood_type FROM donor_profiles WHERE donor_id = %s), 1)"
    return execute_query(query, (donor_id, bank_id, donation_date, donor_id))

def get_donation_history(donor_id):
    query = """
    SELECT dr.donation_date, bb.name as bank_name, dr.blood_type, dr.units_donated, dr.quality_test_status
    FROM donation_records dr
    JOIN blood_banks bb ON dr.bank_id = bb.bank_id
    WHERE dr.donor_id = %s
    ORDER BY dr.donation_date DESC
    """
    return execute_query(query, (donor_id,))

# Hospital staff functions
def get_inventory_status():
    query = "SELECT blood_type, SUM(units_available) as total_units FROM blood_inventory GROUP BY blood_type"
    return execute_query(query)

def submit_blood_request(hospital_id, blood_type, units, priority):
    query = "INSERT INTO blood_requests (requesting_hospital_id, blood_type, units_required, priority) VALUES (%s, %s, %s, %s)"
    return execute_query(query, (hospital_id, blood_type, units, priority))

def get_blood_requests(hospital_id):
    query = "SELECT * FROM blood_requests WHERE requesting_hospital_id = %s ORDER BY request_date DESC"
    return execute_query(query, (hospital_id,))

# Blood bank staff functions
def update_inventory(bank_id, blood_type, units):
    query = """
    INSERT INTO blood_inventory (bank_id, blood_type, units_available)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
    units_available = units_available + VALUES(units_available)
    """
    return execute_query(query, (bank_id, blood_type, units))

def get_donor_records(bank_id):
    query = """
    SELECT dp.full_name, dp.blood_type, dr.donation_date, dr.units_donated, dr.quality_test_status
    FROM donation_records dr
    JOIN donor_profiles dp ON dr.donor_id = dp.donor_id
    WHERE dr.bank_id = %s
    ORDER BY dr.donation_date DESC
    """
    return execute_query(query, (bank_id,))

def process_blood_request(request_id, bank_id):
    with get_cursor(conn) as cursor:
        try:
            cursor.callproc('process_blood_request', (request_id, bank_id, 0))
            for result in cursor.stored_results():
                status_message = result.fetchone()[0]
            conn.commit()
            return status_message
        except Error as e:
            st.error(f"Error: {e}")
            return None

# Main app
def main():
    st.title("Blood Donation Management System")

    if conn is None:
        st.error("Unable to connect to the database. Please check your connection settings.")
        return

    if 'user' not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        show_login_register()
    else:
        show_dashboard()

def show_login_register():
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        new_username = st.text_input("New Username", key="register_username")
        new_password = st.text_input("New Password", type="password", key="register_password")
        email = st.text_input("Email")
        user_type = st.selectbox("User Type", ["donor", "hospital_staff", "blood_bank_staff"])
        if st.button("Register"):
            if register(new_username, new_password, email, user_type):
                st.success("Registered successfully! Please log in.")
            else:
                st.error("Registration failed. Please try again.")

def show_dashboard():
    st.sidebar.title(f"Welcome, {st.session_state.user['username']}")
    user_type = st.session_state.user['user_type']

    if user_type == 'donor':
        show_donor_dashboard()
    elif user_type == 'hospital_staff':
        show_hospital_dashboard()
    elif user_type == 'blood_bank_staff':
        show_blood_bank_dashboard()

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.experimental_rerun()

def show_donor_dashboard():
    tab1, tab2, tab3 = st.tabs(["Profile", "Schedule Donation", "Donation History"])

    with tab1:
        profile = get_donor_profile(st.session_state.user['user_id'])
        if profile:
            st.write(f"Name: {profile['full_name']}")
            st.write(f"Date of Birth: {profile['date_of_birth']}")
            st.write(f"Blood Type: {profile['blood_type']}")
            st.write(f"Contact: {profile['contact_number']}")
            st.write(f"Address: {profile['address']}")
            st.write(f"Last Donation: {profile['last_donation_date']}")
        else:
            st.warning("Please update your profile")

        with st.form("update_profile"):
            full_name = st.text_input("Full Name")
            dob = st.date_input("Date of Birth")
            blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
            contact = st.text_input("Contact Number")
            address = st.text_area("Address")
            medical_history = st.text_area("Medical History")
            if st.form_submit_button("Update Profile"):
                if update_donor_profile(st.session_state.user['user_id'], full_name, dob, blood_type, contact, address, medical_history):
                    st.success("Profile updated successfully!")
                else:
                    st.error("Failed to update profile. Please try again.")

    with tab2:
        blood_banks = execute_query("SELECT bank_id, name FROM blood_banks")
        if blood_banks:
            bank_id = st.selectbox("Select Blood Bank", options=blood_banks, format_func=lambda x: x['name'])
            donation_date = st.date_input("Donation Date", min_value=datetime.now().date())
            if st.button("Schedule Donation"):
                donor_profile = get_donor_profile(st.session_state.user['user_id'])
                if donor_profile:
                    if schedule_donation(donor_profile['donor_id'], bank_id['bank_id'], donation_date):
                        st.success("Donation scheduled successfully!")
                    else:
                        st.error("Failed to schedule donation. Please try again.")
                else:
                    st.error("Please update your profile before scheduling a donation")
        else:
            st.error("No blood banks available. Please contact the administrator.")

    with tab3:
        donor_profile = get_donor_profile(st.session_state.user['user_id'])
        if donor_profile:
            history = get_donation_history(donor_profile['donor_id'])
            if history:
                st.table(history)
            else:
                st.info("No donation history found")
        else:
            st.warning("Please update your profile to view donation history")

def show_hospital_dashboard():
    tab1, tab2, tab3 = st.tabs(["Inventory Status", "Request Blood", "Request History"])

    with tab1:
        inventory = get_inventory_status()
        if inventory:
            st.table(inventory)
        else:
            st.info("No inventory data available")

    with tab2:
        blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        units = st.number_input("Units Required", min_value=1, value=1)
        priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])
        if st.button("Submit Request"):
            if submit_blood_request(st.session_state.user['user_id'], blood_type, units, priority):
                st.success("Blood request submitted successfully!")
            else:
                st.error("Failed to submit blood request. Please try again.")

    with tab3:
        requests = get_blood_requests(st.session_state.user['user_id'])
        if requests:
            st.table(requests)
        else:
            st.info("No request history found")

def show_blood_bank_dashboard():
    tab1, tab2, tab3 = st.tabs(["Manage Inventory", "Donor Records", "Process Requests"])

    with tab1:
        blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        units = st.number_input("Units", min_value=1, value=1)
        if st.button("Update Inventory"):
            if update_inventory(st.session_state.user['user_id'], blood_type, units):
                st.success("Inventory updated successfully!")
            else:
                st.error("Failed to update inventory. Please try again.")

    with tab2:
        records = get_donor_records(st.session_state.user['user_id'])
        if records:
            st.table(records)
        else:
            st.info("No donor records found")

    with tab3:
        requests = get_blood_requests(st.session_state.user['user_id'])
        if requests:
            for request in requests:
                st.write(f"Request ID: {request['request_id']}")
                st.write(f"Blood Type: {request['blood_type']}")
                st.write(f"Units Required: {request['units_required']}")
                st.write(f"Priority: {request['priority']}")
                st.write(f"Status: {request['status']}")
                if request['status'] == 'pending':
                    if st.button(f"Process Request {request['request_id']}"):
                        status_message = process_blood_request(request['request_id'], st.session_state.user['user_id'])
                        st.write(status_message)
                st.write("---")
        else:
            st.info("No pending requests found")

if __name__ == "__main__":
    main()