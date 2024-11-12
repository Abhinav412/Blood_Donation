import streamlit as st
import mysql.connector
from datetime import datetime, time
import pandas as pd 


def create_connection():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="example",  
        password="Project@123", 
        database="blood_donation_db"
    )


def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, role FROM User WHERE username=%s AND password=%s", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user


def logout():
    st.session_state["logged_in"] = False
    st.session_state["role"] = None
    st.session_state["logged_out"] = True  # Trigger rerun outside of callback

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

# Function to retrieve blood banks from the database
def get_blood_banks():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT blood_bank_id, name FROM BloodBank")
    blood_banks = cursor.fetchall()
    conn.close()
    return blood_banks

# Function to register a new donor (without selecting blood bank here)
def register_donor():
    st.subheader("Register as a Donor")
    
    # Get list of blood banks for selection
    blood_banks = get_blood_banks()
    if not blood_banks:
        st.error("No blood banks available. Please contact administrator.")
        return
        
    # Create dictionary of blood bank names and IDs
    blood_bank_options = {name: id for id, name in blood_banks}
    
    # Form inputs
    first_name = st.text_input("First Name")
    last_name = st.text_input("Last Name")
    email = st.text_input("Email")
    blood_type = st.selectbox("Blood Type", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
    last_donation = st.date_input("Last Donation Date")
    eligibility_status = st.selectbox("Eligibility Status", ["Eligible", "Ineligible"])
    
    # Blood bank selection
    selected_blood_bank = st.selectbox("Choose a Blood Bank", options=list(blood_bank_options.keys()))
    selected_blood_bank_id = blood_bank_options[selected_blood_bank]

    if st.button("Register Donor"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Donor (first_name, last_name, email, blood_type, last_donation, eligibility_status, blood_bank_id) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (first_name, last_name, email, blood_type, last_donation, eligibility_status, selected_blood_bank_id)
            )
            conn.commit()
            st.success("Donor registered successfully!")
            
            # Store donor_id in session state for future use
            cursor.execute("SELECT LAST_INSERT_ID()")
            donor_id = cursor.fetchone()[0]
            st.session_state["donor_id"] = donor_id
            
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

# Function to schedule an appointment
def update_blood_inventory():
    st.subheader("Update Blood Bank Inventory")

    # Fetch all blood banks
    blood_banks = get_blood_banks()
    if blood_banks:
        # Create a dictionary with blood bank names as keys and IDs as values
        blood_bank_options = {name: id for id, name in blood_banks}

        # Dropdown to select a blood bank
        selected_blood_bank = st.selectbox("Choose a Blood Bank", options=blood_bank_options.keys())
        selected_blood_bank_id = blood_bank_options[selected_blood_bank]

        # Blood type selection and units input
        blood_type = st.selectbox("Select Blood Type", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        units_available = st.number_input("Update Units Available", min_value=0, step=1)

        if st.button("Update Inventory"):
            conn = create_connection()
            cursor = conn.cursor()
            try:
                # Call the stored procedure to update the inventory
                cursor.callproc('update_blood_inventory', (selected_blood_bank_id, blood_type, int(units_available)))
                conn.commit()
                st.success(f"Inventory updated for {blood_type} at {selected_blood_bank}.")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                conn.close()
    else:
        st.warning("No blood banks available. Please register a blood bank first.")
def schedule_appointment():
    st.subheader("Schedule an Appointment with a Blood Bank")

    # Fetch blood banks for dropdown
    blood_banks = get_blood_banks()
    if blood_banks:
        # Create dictionary with blood bank names as keys and IDs as values
        blood_bank_options = {name: id for id, name in blood_banks}
        
        # Display blood bank selection dropdown
        selected_blood_bank = st.selectbox("Choose a Blood Bank", options=list(blood_bank_options.keys()))
        # Get the correct blood bank ID from our dictionary
        selected_blood_bank_id = blood_bank_options[selected_blood_bank]

        # Blood type selection
        blood_type = st.selectbox("Select Blood Type for Donation", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

        # Appointment date and time inputs
        appointment_date = st.date_input("Select Appointment Date")
        appointment_time = st.time_input("Select Appointment Time", value=time(9, 0))

        if st.button("Schedule Appointment"):
            conn = create_connection()
            cursor = conn.cursor()
            try:
                # Start a transaction
                conn.start_transaction()

                # Get donor_id from session state
                donor_id = st.session_state.get("donor_id")
                if not donor_id:
                    raise ValueError("Donor ID not found in session")

                # First, insert the appointment
                cursor.execute(
                    """
                    INSERT INTO Appointments 
                    (donor_id, blood_bank_id, appointment_date, appointment_time) 
                    VALUES (%s, %s, %s, %s)
                    """,
                    (donor_id, selected_blood_bank_id, appointment_date, appointment_time)
                )

                # Then, update the inventory for the selected blood bank
                cursor.execute(
                    """
                    INSERT INTO BloodInventory 
                    (blood_bank_id, blood_type, units_available) 
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE 
                    units_available = units_available + 1,
                    blood_bank_id = VALUES(blood_bank_id)
                    """,
                    (selected_blood_bank_id, blood_type)
                )

                # Commit the transaction
                conn.commit()
                st.success(f"Appointment scheduled successfully at {selected_blood_bank}!")
                
                # Debug information
                st.info(f"Appointment and inventory updated for Blood Bank ID: {selected_blood_bank_id}")
                
            except mysql.connector.Error as e:
                conn.rollback()
                st.error(f"Database Error: {e}")
            except ValueError as e:
                st.error(f"Session Error: {e}")
            finally:
                conn.close()
    else:
        st.warning("No blood banks available. Please register a blood bank first.")





# Function to add a new blood bank (staff role)
def register_blood_bank():
    st.subheader("Register a New Blood Bank")
    name = st.text_input("Blood Bank Name")
    location = st.text_input("Location")
    contact_number = st.text_input("Contact Number")

    if st.button("Add Blood Bank"):
        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.callproc('add_blood_bank', (name, location, contact_number))
            conn.commit()
            st.success("Blood bank added successfully!")
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()

# Function to manage blood inventory (staff role)



def view_inventory():
    st.subheader("View Blood Inventory")
    
    # Fetch blood banks for dropdown
    blood_banks = get_blood_banks()
    if blood_banks:
        # Create a dictionary with blood bank names as keys and IDs as values
        blood_bank_options = {name: id for id, name in blood_banks}
        
        # Dropdown to select a blood bank
        selected_blood_bank = st.selectbox("Choose a Blood Bank", options=blood_bank_options.keys())
        selected_blood_bank_id = blood_bank_options[selected_blood_bank]

        # Now, fetch the inventory for the selected blood bank
        conn = create_connection()
        cursor = conn.cursor()
        
        # Modified query to only fetch existing columns
        cursor.execute("""
            SELECT blood_type, units_available 
            FROM BloodInventory 
            WHERE blood_bank_id = %s
        """, (selected_blood_bank_id,))
        
        # Fetch all records for the selected blood bank
        blood_inventory_data = cursor.fetchall()
        conn.close()

        # Display the inventory details
        if blood_inventory_data:
            st.write(f"### Inventory details for {selected_blood_bank}")
            
            # Create a more organized display using columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("*Blood Type*")
                for record in blood_inventory_data:
                    st.write(record[0])
                    
            with col2:
                st.write("*Units Available*")
                for record in blood_inventory_data:
                    st.write(record[1])
                    
        else:
            st.warning("No inventory found for this blood bank.")
    else:
        st.warning("No blood banks available. Please register a blood bank first.")


# Function to request blood (medical professional role)
def request_blood():
    st.subheader("Request Blood for Medical Purposes")

    # Fetch all blood banks
    blood_banks = get_blood_banks()
    if blood_banks:
        # Create a dictionary with blood bank names as keys and IDs as values
        blood_bank_options = {name: id for id, name in blood_banks}

        # Dropdown to select a blood bank
        selected_blood_bank = st.selectbox("Choose a Blood Bank", options=blood_bank_options.keys())
        selected_blood_bank_id = blood_bank_options[selected_blood_bank]

        # Blood type selection and units input
        blood_type = st.selectbox("Select Blood Type", ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
        units_needed = st.number_input("Number of Units Required", min_value=1, step=1)

        if st.button("Request Blood"):
            conn = create_connection()
            cursor = conn.cursor()
            try:
                # Insert blood request into BloodRequest table
                cursor.execute(
                    "INSERT INTO BloodRequest (blood_bank_id, blood_type, units_requested) "
                    "VALUES (%s, %s, %s)",
                    (selected_blood_bank_id, blood_type, units_needed)
                )
                conn.commit()

                # Decrease the available units in the BloodInventory
                cursor.execute("""
                    UPDATE BloodInventory 
                    SET units_available = units_available - %s 
                    WHERE blood_bank_id = %s AND blood_type = %s AND units_available >= %s
                """, (units_needed, selected_blood_bank_id, blood_type, units_needed))

                # Check if there are enough units available
                if cursor.rowcount == 0:
                    st.error(f"Not enough units of {blood_type} available in {selected_blood_bank}.")
                else:
                    conn.commit()
                    st.success(f"Blood request placed for {units_needed} units of {blood_type} from {selected_blood_bank}.")
            except mysql.connector.Error as e:
                st.error(f"Error: {e}")
            finally:
                conn.close()

    else:
        st.warning("No blood banks available. Please contact support.")

# Function to view inventories of all blood banks (medical professional role)
def view_all_inventories():
    st.subheader("View Blood Inventories of All Blood Banks")

    conn = create_connection()
    cursor = conn.cursor()

    # Query to fetch inventory data from all blood banks
    cursor.execute("""
        SELECT b.name, bi.blood_type, bi.units_available 
        FROM BloodBank b
        JOIN BloodInventory bi ON b.blood_bank_id = bi.blood_bank_id
        ORDER BY b.name, bi.blood_type
    """)
    
    blood_inventory_data = cursor.fetchall()

    # Query to fetch the total units of each blood type across all blood banks
    cursor.execute("""
        SELECT blood_type, SUM(units_available) AS total_units
        FROM BloodInventory
        GROUP BY blood_type
    """)
    
    aggregated_data = cursor.fetchall()
    conn.close()

    if blood_inventory_data:
        current_blood_bank = None
        for record in blood_inventory_data:
            blood_bank_name, blood_type, units_available = record
            if blood_bank_name != current_blood_bank:
                if current_blood_bank is not None:
                    st.write("---")  # Separator for different blood banks
                st.write(f"{blood_bank_name}:")
                current_blood_bank = blood_bank_name
            st.write(f"- Blood Type: {blood_type}, Units Available: {units_available}")
    else:
        st.warning("No blood inventory data available.")

    # Display the aggregated inventory details
    if aggregated_data:
        st.write("### Total Inventory across all Blood Banks")
        
        # Create a more organized display using columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Blood Type")
            for record in aggregated_data:
                st.write(record[0])
                
        with col2:
            st.write("Total Units")
            for record in aggregated_data:
                st.write(record[1])
def view_donors_for_blood_bank():
    st.subheader("View Donors for Blood Bank")

    # Fetch all blood banks
    blood_banks = get_blood_banks()
    if blood_banks:
        # Create a dictionary with blood bank names as keys and IDs as values
        blood_bank_options = {name: id for id, name in blood_banks}

        # Dropdown to select a blood bank
        selected_blood_bank = st.selectbox("Choose a Blood Bank", options=blood_bank_options.keys())
        selected_blood_bank_id = blood_bank_options[selected_blood_bank]

        conn = create_connection()
        cursor = conn.cursor()
        try:
            # Call the stored procedure to get the donors for the selected blood bank
            cursor.execute("""
                CALL get_donors_for_blood_bank(%s)
            """, (selected_blood_bank_id,))

            donor_data = cursor.fetchall()

            if donor_data:
                st.write(f"### Donors registered with {selected_blood_bank}")

                # Create a table for better display
                donor_df = pd.DataFrame(donor_data, columns=["First Name", "Last Name", "Email", "Blood Type", "Last Donation", "Eligibility Status"])

                # Format the 'Last Donation' column to display the date correctly
                donor_df["Last Donation"] = donor_df["Last Donation"].apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, datetime) else x)

                # Display the table
                st.dataframe(donor_df)

            else:
                st.warning(f"No donors found for {selected_blood_bank}.")
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            conn.close()
    else:
        st.warning("No blood banks available. Please register a blood bank first.")

def main():
    # Initialize session state variables if not already set
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "role" not in st.session_state:
        st.session_state["role"] = None
    if "logged_out" not in st.session_state:
        st.session_state["logged_out"] = False
    if "donor_id" not in st.session_state:
        st.session_state["donor_id"] = None

    # Check if logout was triggered
    if st.session_state["logged_out"]:
        st.session_state["logged_out"] = False  # Reset logout trigger
        st.experimental_rerun()  # Rerun to refresh the login/signup view

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
                user = authenticate_user(username, password)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["role"] = user[1]
                    st.session_state["donor_id"] = user[0]  # Store donor_id for scheduling appointments
                    st.experimental_rerun()  # Reload the page to show dashboard
                else:
                    st.error("Invalid credentials")
    else:
        # Display a logout button in the sidebar
        st.sidebar.button("Logout", on_click=logout)

        # Render role-specific dashboard based on user's role
        if st.session_state["role"] == "Donor":
            action = st.sidebar.selectbox("Select an option", ["Register as Donor", "Schedule Appointment"])
            if action == "Register as Donor":
                register_donor()
            elif action == "Schedule Appointment":
                schedule_appointment()
        elif st.session_state["role"] == "Blood Bank Staff":
            action = st.sidebar.selectbox("Select an option", ["Register Blood Bank", "Update Inventory","View Donors"])
            if action == "Register Blood Bank":
                register_blood_bank()
            
            elif action == "Update Inventory":
                update_blood_inventory()
            elif action=="View Donors":
                view_donors_for_blood_bank()

                
        elif st.session_state["role"] == "Medical Professional":
            action = st.sidebar.selectbox("Select an option", ["Request Blood", "View All Inventories"])
            if action == "Request Blood":
                request_blood()
            elif action == "View All Inventories":
                view_all_inventories()

# Run the application
if __name__ == "__main__":
    main()