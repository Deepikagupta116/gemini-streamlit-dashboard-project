import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from google import genai
from google.genai import types
from google.api_core.exceptions import ResourceExhausted

MODEL = "gemini-2.5-flash"
CSV_FILE = "submissions.csv"
PAUSE_DURATION = 2 # a pause duration variable to respect API limits

# Variables to hold the client and key, initialized to None
client = None

# --- Client Initialization Function ---
@st.cache_resource
def initialize_client():
    """Initializes the Gemini client, handling secrets and errors safely."""
    
    try:
        # Read the key securely from the secrets file (or environment)
        api_key = st.secrets["GEMINI_API_KEY"] 
        
        # Initialize and return the client
        return genai.Client(api_key=api_key)
    except KeyError:
        # Streamlit warning that won't crash the app if the key is missing
        st.warning("GEMINI_API_KEY secret not found. LLM calls will fail.")
        return None
    except Exception as e:
        st.error(f"Failed to initialize Gemini Client: {e}")
        return None
    
# Call the initializer once to set the global client variable 
# This runs only once per session due to @st.cache_resource
client = initialize_client()

def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # This will silently fail if the file isn't there, preventing crashes
        pass


@st.cache_data
def get_data():
    # Columns: ['timestamp', 'user_rating', 'user_review', 'ai_user_response', 'ai_summary', 'ai_action']
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=['timestamp', 'user_rating', 'user_review', 
                                   'ai_user_response', 'ai_summary', 'ai_action'])
        df.to_csv(CSV_FILE, index=False)
        return df
    return pd.read_csv(CSV_FILE)

def save_data(df):
    df.to_csv(CSV_FILE, index=False)
    get_data.clear() # Clear the cache so new data is loaded

def call_llm(prompt):
    if not client:
        return "LLM Error: Client not initialized due to missing API Key."
        
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt],
        )
        return response.text
    except ResourceExhausted as e:
        # Better to return an error than sleep in a function called by UI
        return f"LLM Error (Rate Limit): Please try again later. {e}"
    except Exception as e:
        return f"LLM Error: {e}"
    
def process_pending_reviews(pending_df, master_df):
    """ Runs LLM analysis (summary and action) on new reviews. """
    if pending_df.empty:
        st.info("No new reviews need processing.")
        return master_df

    st.toast(f"Starting analysis for {len(pending_df)} pending submissions. This will take time.")
    
    progress_bar = st.progress(0, text="AI Analysis in progress...")
    
    for i, (index, row) in enumerate(pending_df.iterrows()):
        review_text = row['user_review']
        rating = row['user_rating']
        
        # 1. LLM Call for Review Summarization (Requirement: Review summarisation)
        summary_prompt = f"Summarize the following {rating}-star review in one short sentence: '{review_text}'"
        ai_summary = call_llm(summary_prompt)

        # 2. LLM Call for Recommended Next Actions (Requirement: Recommended next actions)
        action_prompt = f"""
        Based on this {rating}-star review: "{review_text}", suggest ONE concrete, actionable step 
        a business manager should take to address the feedback. Keep it very short and direct.
        """
        ai_action = call_llm(action_prompt)

        # Update the master DataFrame using the index safely
        master_df.loc[index, 'ai_summary'] = ai_summary
        master_df.loc[index, 'ai_action'] = ai_action
        
        progress_bar.progress((i + 1) / len(pending_df), text=f"Processed {i + 1} of {len(pending_df)} reviews.")
        
        # CRITICAL: Pause to respect API rate limits during the batch job
        if i < len(pending_df) - 1:
            time.sleep(PAUSE_DURATION) 

    save_data(master_df)
    progress_bar.empty()
    st.toast("Analysis complete. Dashboard refreshed.")
    return master_df