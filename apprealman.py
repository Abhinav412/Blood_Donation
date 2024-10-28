import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

# Add custom CSS with medical theme
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(to bottom right, #ffe6ea, #fff0f3);
        }
        
        .stButton button {
            background-color: #ff4d6d !important;
            color: white !important;
        }
        
        .stButton button:hover {
            background-color: #ff3355 !important;
            color: white !important;
        }
        
        h1, h2, h3 {
            color: #d81b60 !important;
        }
        
        .stMetric {
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .css-1d391kg {
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 10px;
            padding: 10px;
        }
        
        .stSidebar .stButton button {
            width: 100%;
        }
        
        .stDataFrame {
            background-color: rgba(255, 255, 255, 0.7) !important;
            border-radius: 10px;
            padding: 10px;
        }
        
        .stAlert {
            background-color: rgba(255, 255, 255, 0.7) !important;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'donors' not in st.session_state:
    st.session_state.donors = pd.DataFrame({
        'id': [],
        'name': [],
        'age': [],
        'blood_type': [],
        'phone': [],
        'last_donation': []
    })

if 'inventory' not in st.session_state:
    st.session_state.inventory = pd.DataFrame({
        'blood_type': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
        'units': [10, 5, 8, 4, 6, 3, 15, 7]
    })

if 'requests' not in st.session_state:
    st.session_state.requests = pd.DataFrame({
        'id': [],
        'hospital': [],
        'blood_type': [],
        'units': [],
        'status': [],
        'date': []
    })



def main():
    st.title("Blood Donation Management System")
    
    # Sidebar menu
    menu = st.sidebar.selectbox(
        "Menu",
        ["Home", "Donor Registration", "Donor Search", "Blood Inventory", 
         "Blood Requests", "Reports", "Admin Panel"]
    )
    
    if menu == "Home":
        show_home()
    elif menu == "Donor Registration":
        show_donor_registration()
    elif menu == "Donor Search":
        show_donor_search()
    elif menu == "Blood Inventory":
        show_blood_inventory()
    elif menu == "Blood Requests":
        show_blood_requests()
    elif menu == "Reports":
        show_reports()
    elif menu == "Admin Panel":
        show_admin_panel()

def show_home():
    st.header("Welcome to Blood Donation Management System")
    
    # Display key statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Donors", len(st.session_state.donors))
    
    with col2:
        total_blood_units = st.session_state.inventory['units'].sum()
        st.metric("Total Blood Units", total_blood_units)
    
    with col3:
        total_requests = len(st.session_state.requests)
        st.metric("Active Requests", total_requests)
    
    # Display recent donations
    st.subheader("Recent Blood Inventory Status")
    st.dataframe(st.session_state.inventory)

def show_donor_registration():
    st.header("Donor Registration")
    
    with st.form("donor_registration"):
        name = st.text_input("Full Name")
        age = st.number_input("Age", 18, 65, 25)
        blood_type = st.selectbox(
            "Blood Type",
            ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        )
        phone = st.text_input("Phone Number")
        
        if st.form_submit_button("Register Donor"):
            if name and phone:
                new_donor = pd.DataFrame({
                    'id': [len(st.session_state.donors) + 1],
                    'name': [name],
                    'age': [age],
                    'blood_type': [blood_type],
                    'phone': [phone],
                    'last_donation': [None]
                })
                st.session_state.donors = pd.concat([st.session_state.donors, new_donor], ignore_index=True)
                st.success("Donor registered successfully!")
            else:
                st.error("Please fill in all required fields.")

def show_donor_search():
    st.header("Donor Search")
    
    search_term = st.text_input("Search by name or blood type")
    
    if search_term:
        results = st.session_state.donors[
            st.session_state.donors['name'].str.contains(search_term, case=False, na=False) |
            st.session_state.donors['blood_type'].str.contains(search_term, case=False, na=False)
        ]
        if not results.empty:
            st.dataframe(results)
        else:
            st.info("No donors found.")

def show_blood_inventory():
    st.header("Blood Inventory Management")
    
    # Display current inventory
    st.subheader("Current Inventory")
    st.dataframe(st.session_state.inventory)
    
    # Update inventory
    st.subheader("Update Inventory")
    with st.form("update_inventory"):
        blood_type = st.selectbox(
            "Blood Type",
            st.session_state.inventory['blood_type'].tolist()
        )
        action = st.selectbox("Action", ["Add Units", "Remove Units"])
        units = st.number_input("Number of Units", 1, 100, 1)
        
        if st.form_submit_button("Update Inventory"):
            idx = st.session_state.inventory.index[
                st.session_state.inventory['blood_type'] == blood_type
            ].tolist()[0]
            
            if action == "Add Units":
                st.session_state.inventory.at[idx, 'units'] += units
                st.success(f"Added {units} units of {blood_type}")
            else:
                current_units = st.session_state.inventory.at[idx, 'units']
                if current_units >= units:
                    st.session_state.inventory.at[idx, 'units'] -= units
                    st.success(f"Removed {units} units of {blood_type}")
                else:
                    st.error("Insufficient units available")

def show_blood_requests():
    st.header("Blood Requests")
    
    # Create new request
    st.subheader("New Blood Request")
    with st.form("blood_request"):
        hospital = st.text_input("Hospital Name")
        blood_type = st.selectbox(
            "Blood Type Required",
            st.session_state.inventory['blood_type'].tolist()
        )
        units = st.number_input("Units Required", 1, 100, 1)
        
        if st.form_submit_button("Submit Request"):
            if hospital:
                new_request = pd.DataFrame({
                    'id': [len(st.session_state.requests) + 1],
                    'hospital': [hospital],
                    'blood_type': [blood_type],
                    'units': [units],
                    'status': ['Pending'],
                    'date': [datetime.now().strftime("%Y-%m-%d")]
                })
                st.session_state.requests = pd.concat([st.session_state.requests, new_request], ignore_index=True)
                st.success("Request submitted successfully!")
            else:
                st.error("Please fill in all required fields.")
    
    # Display active requests
    st.subheader("Active Requests")
    if not st.session_state.requests.empty:
        st.dataframe(st.session_state.requests)
    else:
        st.info("No active requests.")

def show_reports():
    st.header("Reports")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Donation Statistics", "Inventory Status", "Request History"]
    )
    
    if report_type == "Donation Statistics":
        st.subheader("Donation Statistics")
        if not st.session_state.donors.empty:
            st.write("Total Registered Donors:", len(st.session_state.donors))
            blood_type_counts = st.session_state.donors['blood_type'].value_counts()
            st.bar_chart(blood_type_counts)
        else:
            st.info("No donor data available.")
            
    elif report_type == "Inventory Status":
        st.subheader("Current Inventory Status")
        st.bar_chart(st.session_state.inventory.set_index('blood_type')['units'])
        
    elif report_type == "Request History":
        st.subheader("Blood Request History")
        if not st.session_state.requests.empty:
            st.dataframe(st.session_state.requests)
            status_counts = st.session_state.requests['status'].value_counts()
            st.pie_chart(status_counts)
        else:
            st.info("No request history available.")

def show_admin_panel():
    st.header("Admin Panel")
    
    action = st.selectbox(
        "Select Action",
        ["Manage Users", "System Settings", "Database Backup"]
    )
    
    if action == "Manage Users":
        st.subheader("User Management")
        if not st.session_state.donors.empty:
            st.dataframe(st.session_state.donors)
            
            # Delete user functionality
            user_id = st.number_input("Enter User ID to Delete", min_value=1)
            if st.button("Delete User"):
                st.session_state.donors = st.session_state.donors[
                    st.session_state.donors['id'] != user_id
                ]
                st.success(f"User {user_id} deleted successfully!")
                
    elif action == "System Settings":
        st.subheader("System Settings")
        st.write("System settings functionality would go here...")
        
    elif action == "Database Backup":
        st.subheader("Database Backup")
        if st.button("Generate Backup"):
            st.success("Backup generated successfully!")
            st.download_button(
                label="Download Backup",
                data=st.session_state.donors.to_csv(index=False),
                file_name="donors_backup.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()