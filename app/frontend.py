import streamlit as st
import mysql.connector
from datetime import datetime

# Helper function to create MySQL connection
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="Resh@1234",  # Replace with your MySQL password
        database="blood_donation_db"
    )

# Authentication function
def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM User WHERE username=%s AND password=%s", (username, password))
    role = cursor.fetchone()
    conn.close()
    return role

# Signup function
def signup_user(username, password, role):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO User (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
        conn.commit()
        st.success("User signed up successfully! Please proceed to the login page.")
    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()

# Donor Dashboard Functions
# Function to register a new donor with an email field
def register_donor():
    st.subheader("Register a New Donation")
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")  # New field for donor email
    blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
    last_donation = st.date_input("Last Donation Date")
    eligibility_status = st.selectbox("Eligibility Status", ["Eligible", "Ineligible"])

    if st.button("Register Donor"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            # Insert with email
            cursor.execute(
                "INSERT INTO Donor (first_name, last_name, email, blood_type, last_donation, eligibility_status) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (first_name, last_name, email, blood_type, last_donation, eligibility_status)
            )
            conn.commit()
            st.success("Donor registered successfully!")
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def search_donor_info(first_name, last_name, email):
    conn = create_connection()
    cursor = conn.cursor()
    query = """
    SELECT donor_id, first_name, last_name, blood_type, last_donation, eligibility_status
    FROM Donor 
    WHERE first_name = %s AND last_name = %s AND email = %s
    """
    cursor.execute(query, (first_name, last_name, email))
    donor = cursor.fetchone()
    conn.close()
    return donor

def update_donor_info(donor_id, last_donation, eligibility_status):
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE Donor SET last_donation = %s, eligibility_status = %s WHERE donor_id = %s",
            (last_donation, eligibility_status, donor_id)
        )
        conn.commit()
        st.success("Donor information updated successfully!")
    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
    finally:
        conn.close()
def display_update_form():
    st.subheader("Update Donor Information")

    # Step 1: Search for the donor
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")  # Assuming email is stored in the Donor table

    if st.button("Search"):
        donor = search_donor_info(first_name, last_name, email)
        if donor:
            st.success("Donor found! You can now update the information.")
            donor_id, _, _, _, last_donation, eligibility_status = donor

            # Step 2: Display form to update information
            new_last_donation = st.date_input("Last Donation Date", last_donation)
            new_eligibility_status = st.selectbox("Eligibility Status", ["Eligible", "Ineligible"], 
                                                  index=0 if eligibility_status == "Eligible" else 1)

            if st.button("Update Information"):
                update_donor_info(donor_id, new_last_donation, new_eligibility_status)
        else:
            st.error("No donor found with the provided information.")


# Blood Bank Staff Dashboard Functions
def manage_inventory():
    st.subheader("Manage Blood Inventory")
    blood_type_inv = st.selectbox("Blood Type for Inventory", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
    units_available = st.number_input("Units Available", min_value=0)
    expiration_date = st.date_input("Expiration Date")
    is_safe = st.selectbox("Is Safe for Use", [True, False])

    if st.button("Add/Update Inventory"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.callproc('add_blood_inventory', (blood_type_inv, units_available, expiration_date, is_safe))
            conn.commit()
            st.success("Inventory updated successfully!")
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def view_inventory():
    st.subheader("View Blood Inventory")
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM BloodInventory")
    blood_inventory_data = cursor.fetchall()
    st.write(blood_inventory_data)
    conn.close()

# Medical Professional Dashboard Functions
def request_blood():
    st.subheader("Request Blood")
    requester_type = st.selectbox("Requester Type", ["Hospital", "Patient"])
    blood_type_req = st.selectbox("Blood Type for Request", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
    quantity = st.number_input("Quantity", min_value=1)
    
    if st.button("Place Request"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.callproc('place_blood_request', (requester_type, blood_type_req, quantity, None))
            conn.commit()
            cursor.execute("SELECT status FROM BloodRequests ORDER BY request_id DESC LIMIT 1")
            request_status = cursor.fetchone()[0]
            st.success(f"Blood request placed successfully! Status: {request_status}")
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

def view_error_logs():
    st.subheader("Error Logs")
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ErrorLogs")
    error_logs = cursor.fetchall()
    if error_logs:
        st.write(error_logs)
    else:
        st.write("No error logs found.")
    conn.close()

# Dashboard for each role
def donor_dashboard():
    st.sidebar.title("Donor Dashboard")
    choice = st.sidebar.radio("Select an option", ["Register Donation", "Update Information"])
    
    if choice == "Register Donation":
        register_donor()
    elif choice == "Update Information":
        display_update_form()

def blood_bank_staff_dashboard():
    st.sidebar.title("Blood Bank Staff Dashboard")
    choice = st.sidebar.radio("Select an option", ["Manage Inventory", "View Inventory"])
    if choice == "Manage Inventory":
        manage_inventory()
    elif choice == "View Inventory":
        view_inventory()

def medical_professional_dashboard():
    st.sidebar.title("Medical Professional Dashboard")
    choice = st.sidebar.radio("Select an option", ["Request Blood", "View Error Logs"])
    if choice == "Request Blood":
        request_blood()
    elif choice == "View Error Logs":
        view_error_logs()

# Main application
def main():
    # Initialize session state variables if not already set
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "role" not in st.session_state:
        st.session_state["role"] = None

    # Login and Signup Page if not logged in
    if not st.session_state["logged_in"]:
        page = st.sidebar.selectbox("Choose a page", ["Login", "Signup"])
        
        if page == "Signup":
            st.title("Signup Page")
            username = st.text_input("Choose a Username")
            password = st.text_input("Choose a Password", type="password")
            role = st.selectbox("Select Role", ["Donor", "Blood Bank Staff", "Medical Professional"])
            
            if st.button("Sign Up"):
                signup_user(username, password, role)

        elif page == "Login":
            st.title("Login Page")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                user_role = authenticate_user(username, password)
                if user_role:
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = user_role[0]
                    st.experimental_rerun()  # Reload the page to show dashboard
                else:
                    st.error("Invalid credentials")
    else:
        # Render role-specific dashboard based on user's role
        if st.session_state["role"] == "Donor":
            donor_dashboard()
        elif st.session_state["role"] == "Blood Bank Staff":
            blood_bank_staff_dashboard()
        elif st.session_state["role"] == "Medical Professional":
            medical_professional_dashboard()

# Run the application
if __name__ == "__main__":
    main()
