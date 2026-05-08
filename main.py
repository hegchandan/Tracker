import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# --- CONFIGURATION ---
DB_FILE = "docket_db.csv"
DATE_FORMAT = "%d-%b-%Y"  # Standard: DD-MMM-YYYY

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Convert strings back to date objects for calculation
        df['Event Date'] = pd.to_datetime(df['Event Date'], format=DATE_FORMAT).dt.date
        df['Form-3'] = df['Form-3'].apply(lambda x: pd.to_datetime(x, format=DATE_FORMAT).date() if x != "N/A" else "N/A")
        df['Final Deadline'] = pd.to_datetime(df['Final Deadline'], format=DATE_FORMAT).dt.date
        return df
    return pd.DataFrame(columns=["Docket", "Type", "Event Date", "Form-3", "Final Deadline", "Status"])

def save_data(df):
    # Format dates as strings before saving to CSV
    save_df = df.copy()
    save_df['Event Date'] = save_df['Event Date'].apply(lambda x: x.strftime(DATE_FORMAT))
    save_df['Form-3'] = save_df['Form-3'].apply(lambda x: x.strftime(DATE_FORMAT) if x != "N/A" else "N/A")
    save_df['Final Deadline'] = save_df['Final Deadline'].apply(lambda x: x.strftime(DATE_FORMAT))
    save_df.to_csv(DB_FILE, index=False)

def get_dates(notice_type, d):
    if notice_type == "FER":
        f3 = d + relativedelta(months=3) - timedelta(days=5)
        final = d + relativedelta(months=6)
        return f3, final
    return "N/A", d + timedelta(days=15)

# --- UI SETUP ---
st.set_page_config(page_title="IP Docket System", layout="wide")
st.title("⚖️ IP Docket & Reminder Dashboard")

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- SIDEBAR: INPUT ---
with st.sidebar.form("add_entry", clear_on_submit=True):
    st.header("New Docket Entry")
    doc_id = st.text_input("Docket Number")
    n_type = st.selectbox("Type", ["FER", "Hearing"])
    # Date input UI (still uses standard selector, but we format the result)
    date_val = st.date_input("Notice/Hearing Date")
    
    if st.form_submit_button("Add to System"):
        if doc_id:
            f3, final = get_dates(n_type, date_val)
            new_row = pd.DataFrame([{
                "Docket": doc_id, "Type": n_type, "Event Date": date_val,
                "Form-3": f3, "Final Deadline": final, "Status": "Pending"
            }])
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            save_data(st.session_state.df)
            st.success(f"Added {doc_id}")
            st.rerun()

# --- DASHBOARD ---
df = st.session_state.df.copy()
if not df.empty:
    today = datetime.now().date()
    df['Days Left'] = df['Final Deadline'].apply(lambda x: (x - today).days)
    
    # Logic for Alerts
    urgent = df[(df['Days Left'] <= 7) & (df['Status'] == "Pending")]
    
    if not urgent.empty:
        # Create a display-friendly version for the alert
        display_urgent = urgent.copy()
        display_urgent['Event Date'] = display_urgent['Event Date'].apply(lambda x: x.strftime(DATE_FORMAT))
        display_urgent['Final Deadline'] = display_urgent['Final Deadline'].apply(lambda x: x.strftime(DATE_FORMAT))
        st.error(f"⚠️ {len(urgent)} Deadlines due within 7 days!")
        st.table(display_urgent[["Docket", "Type", "Final Deadline", "Days Left"]])

    st.divider()
    
    # --- MASTER TABLE ---
    st.subheader("Master Docket List")
    
    # Prepare the dataframe for the editor with formatted strings
    display_df = df.copy()
    display_df['Event Date'] = display_df['Event Date'].apply(lambda x: x.strftime(DATE_FORMAT))
    display_df['Form-3'] = display_df['Form-3'].apply(lambda x: x.strftime(DATE_FORMAT) if x != "N/A" else "N/A")
    display_df['Final Deadline'] = display_df['Final Deadline'].apply(lambda x: x.strftime(DATE_FORMAT))
    
    edited_df = st.data_editor(display_df, num_rows="dynamic", use_container_width=True, key="main_editor")
    
    if st.button("Save Changes"):
        # Convert strings back to dates to save properly
        edited_df['Event Date'] = pd.to_datetime(edited_df['Event Date'], format=DATE_FORMAT).dt.date
        edited_df['Final Deadline'] = pd.to_datetime(edited_df['Final Deadline'], format=DATE_FORMAT).dt.date
        # Note: Form-3 remains a mix of string/date, save_data handles it.
        st.session_state.df = edited_df
        save_data(edited_df)
        st.toast("Database Updated!")
        st.rerun()
else:
    st.info("No data found. Add an entry in the sidebar.")
