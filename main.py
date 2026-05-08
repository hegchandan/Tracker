import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# --- CONFIGURATION ---
DB_FILE = "docket_db.csv"
DATE_FORMAT = "%d-%b-%Y"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df['Event Date'] = pd.to_datetime(df['Event Date'], format=DATE_FORMAT).dt.date
        df['Final Deadline'] = pd.to_datetime(df['Final Deadline'], format=DATE_FORMAT).dt.date
        return df
    return pd.DataFrame(columns=["Docket", "Type", "Event Date", "Form-3", "Final Deadline", "Status"])

def save_data(df):
    save_df = df.copy()
    save_df['Event Date'] = save_df['Event Date'].apply(lambda x: x.strftime(DATE_FORMAT))
    # Form-3 can be "N/A" string or a date object
    save_df['Form-3'] = save_df['Form-3'].apply(lambda x: x.strftime(DATE_FORMAT) if hasattr(x, 'strftime') else x)
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

# --- SIDEBAR: ACTIONS ---
st.sidebar.header("Management Center")

# 1. ADD NEW ENTRY
with st.sidebar.expander("➕ Add New Docket", expanded=False):
    with st.form("add_form", clear_on_submit=True):
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

# 2. EDIT OR DELETE ENTRY
if not st.session_state.df.empty:
    with st.sidebar.expander("📝 Edit / Delete Docket", expanded=True):
        target_docket = st.selectbox("Select Docket to Modify", st.session_state.df["Docket"].unique())
        
        # Get current values for the selected docket
        idx = st.session_state.df.index[st.session_state.df['Docket'] == target_docket].tolist()[0]
        current_status = st.session_state.df.at[idx, "Status"]
        
        new_status = st.selectbox("Update Status", ["Pending", "Completed", "Abandoned"], 
                                  index=["Pending", "Completed", "Abandoned"].index(current_status))
        
        col1, col2 = st.columns(2)
        if col1.button("💾 Save Edit"):
            st.session_state.df.at[idx, "Status"] = new_status
            save_data(st.session_state.df)
            st.success("Updated!")
            st.rerun()
            
        if col2.button("🗑️ Delete Entry"):
            st.session_state.df = st.session_state.df.drop(idx).reset_index(drop=True)
            save_data(st.session_state.df)
            st.warning("Deleted!")
            st.rerun()

# --- MAIN DASHBOARD ---
df = st.session_state.df.copy()
if not df.empty:
    today = datetime.now().date()
    df['Days Left'] = df['Final Deadline'].apply(lambda x: (x - today).days)
    
    # Urgent Alerts
    urgent = df[(df['Days Left'] <= 7) & (df['Status'] == "Pending")]
    if not urgent.empty:
        st.error(f"⚠️ {len(urgent)} Deadlines due within 7 days!")
        st.table(urgent[["Docket", "Final Deadline", "Days Left"]])

    st.divider()
    
    # MASTER LIST (READ ONLY)
    st.subheader("Master Docket List (Read-Only)")
    
    # Formatted display
    disp = df.copy()
    disp['Event Date'] = disp['Event Date'].apply(lambda x: x.strftime(DATE_FORMAT))
    disp['Form-3'] = disp['Form-3'].apply(lambda x: x.strftime(DATE_FORMAT) if hasattr(x, 'strftime') else x)
    disp['Final Deadline'] = disp['Final Deadline'].apply(lambda x: x.strftime(DATE_FORMAT))
    
    # Using st.dataframe instead of data_editor makes it read-only
    st.dataframe(disp, use_container_width=True, hide_index=True)
else:
    st.info("No data found. Add an entry in the sidebar.")
