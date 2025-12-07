# 1_user_dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
from utils import get_data,load_css,save_data, call_llm # Import the shared functions

st.set_page_config(page_title="User Dashboard", layout="centered")

load_css("style.css")

st.title("🔥Spill It!")
st.markdown("Instant AI-Powered Response")
# --- User Form ---
with st.form("feedback_form", clear_on_submit=True):
    # Select a star rating
    rating = st.select_slider(
        "Select your star rating:",
        options=[1, 2, 3, 4, 5],
        value=5
    )
    
    # Write a short review
    review = st.text_area("✍️Write your short review:", max_chars=500)

    submitted = st.form_submit_button("Submit & Get AI Response")

    if submitted:
        if review:
            # 1. Get AI-generated user-facing response (Requirement: User-facing responses)
            response_prompt = f"""
            You are a kind customer service agent. Given the user's {rating}-star review: '{review}', 
            write a short, empathetic, and professional response back to them (max 3 sentences).
            """
            ai_response = call_llm(response_prompt)
            
            # 2. Store the data
            new_submission = pd.DataFrame([{
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'user_rating': rating,
                'user_review': review,
                'ai_user_response': ai_response,
                'ai_summary': None,  # Will be filled by Admin Dashboard
                'ai_action': None    # Will be filled by Admin Dashboard
            }])
            
            # Read, append, and save
            df = get_data()
            df = pd.concat([df, new_submission], ignore_index=True)
            save_data(df)
            
            # 3. Display the AI response
            st.success("💖 We appreciate your response!")
            st.subheader("🤖 AI Customer Service Response:")
            st.info(ai_response)
        else:
            st.error("📝Please write a review before submitting.")