import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# --- CONFIGURATION & DATABASE ---
DB_FILE = "docket_db.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Event Date'] = pd.to_datetime(df['Event Date']).dt.date
        df['Final Deadline'] = pd.to_datetime(df['Final Deadline']).dt.date
        return df
    return pd.DataFrame(columns=["Docket", "Type", "Event Date", "Form-3", "Final Deadline", "Status"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- LOGIC ---
def get_dates(notice_type, d):
    if notice_type == "FER":
        f3 = d + relativedelta(months=3) - timedelta(days=5)
        final = d + relativedelta(months=6)
        return f3, final
    return "N/A", d + timedelta(days=15)

# --- UI SETUP ---
st.set_page_config(page_title="IP Docket System", layout="wide")
st.title("⚖️ IP Docket & Reminder Dashboard")

# Load existing data
if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- SIDEBAR: INPUT ---
with st.sidebar.form("add_entry", clear_on_submit=True):
    st.header("New Docket Entry")
    doc_id = st.text_input("Docket Number")
    n_type = st.selectbox("Type", ["FER", "Hearing"])
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
            st.rerun()

# --- DASHBOARD CALCS ---
df = st.session_state.df
if not df.empty:
    today = datetime.now().date()
    df['Days Left'] = df['Final Deadline'].apply(lambda x: (x - today).days)
    
    # Filter for Upcoming (1 week)
    urgent = df[(df['Days Left'] <= 7) & (df['Status'] == "Pending")]
    
    if not urgent.empty:
        st.error(f"⚠️ {len(urgent)} Deadlines due within 7 days!")
        st.dataframe(urgent, use_container_width=True)
    else:
        st.success("✅ No urgent deadlines this week.")

    st.divider()
    
    # --- MASTER TABLE ---
    st.subheader("Master Docket List")
    
    # Allow status updates directly in the app
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
    if st.button("Save Changes"):
        st.session_state.df = edited_df
        save_data(edited_df)
        st.toast("Data Saved!")
else:
    st.info("No data found. Add a docket in the sidebar to begin.")