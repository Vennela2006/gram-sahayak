import streamlit as st
import os
from dotenv import load_dotenv

# 1. Load Secrets
load_dotenv()

# 2. Page Setup
st.set_page_config(page_title="Gram-Sahayak", page_icon="🚜")

st.title("🚜 Gram-Sahayak")
st.success("System is Online! (v1.0)")

# 3. Simple Upload Demo
uploaded_file = st.file_uploader("Upload 7/12 Document", type=['jpg', 'png'])

if uploaded_file:
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    if st.button("Analyze with AI"):
        with st.spinner("Processing..."):
            import time
            time.sleep(2) # Fake delay
        st.balloons()
        st.write("### ✅ Eligibility Confirmed")
        st.json({"Name": "Ramesh Patil", "Status": "Eligible"})