import streamlit as st

st.set_page_config(page_title="Gram-Sahayak", page_icon="🚜")
st.title("🚜 Gram-Sahayak: Farmer Assistant")

st.header("1. Speak Your Request")
if st.button("🎤 Tap to Speak"):
    st.info("Listening... (Simulated)")
    st.success("You said: 'Majhya shetavar karj bhetel ka?'")

st.header("2. Upload 7/12 Document")
uploaded_file = st.file_uploader("Choose 7/12 Image", type=["jpg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption='Uploaded Document', use_column_width=True)
    st.success("Processing complete (Simulated)")

if st.button("✅ Generate Application"):
    st.balloons()
    st.success("Application Form Generated!")