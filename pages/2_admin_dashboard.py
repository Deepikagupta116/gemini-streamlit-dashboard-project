# pages/2_admin_dashboard.py
import sys
import os

# 1. Add the root directory to the system path so Python can find 'utils.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Your original imports (these will now work)
from utils import get_data,load_css,process_pending_reviews, save_data # Import the shared functions
import streamlit as st
import pandas as pd
from utils import get_data,load_css,process_pending_reviews, save_data # Import the shared functions

st.set_page_config(page_title="Admin Dashboard", layout="wide")

load_css("style.css")
st.title("🛡️ Admin Dashboard")

#  Load Data and Identify Pending Reviews 
df_master = get_data()

# Identify submissions where the AI summary has NOT been generated yet
pending_df = df_master[df_master['ai_summary'].isnull()] 

#  Display Analytics 
st.header("Analytics Summary")
col1, col2, col3 = st.columns(3)
col1.metric("📥Total Submissions", len(df_master))
col2.metric("⏳Pending AI Analysis", len(pending_df), delta_color="inverse")
col3.metric("📈Average Rating", f"{df_master['user_rating'].mean():.2f}")


# -AI Processing Trigger 
st.subheader("Batch AI Processing")
if st.button(f"Run AI Analysis on {len(pending_df)} Pending Reviews", disabled=pending_df.empty):
    # This calls the function that performs the loop and saves the data
    df_master = process_pending_reviews(pending_df, df_master) 
    st.rerun() # Rerun to refresh the data display

st.markdown("---")

#  Display All Submissions 
st.subheader("Live-Updating List")
# Display the required columns
st.dataframe(
    df_master[['timestamp', 'user_rating', 'user_review', 'ai_user_response', 'ai_summary', 'ai_action']], 
    width='stretch'
)
