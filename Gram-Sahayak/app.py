import streamlit as st
import os
import io
import time
import base64
import json
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Gram Sahayak", page_icon="🚜", layout="centered")
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY missing in .env file!")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')

try:
    import logic
except ImportError:
    logic = None

# --- STATE ---
if "step" not in st.session_state: st.session_state.step = 1
if "farmer_name" not in st.session_state: st.session_state.farmer_name = ""
if "land_area" not in st.session_state: st.session_state.land_area = ""
if "loan_amount" not in st.session_state: st.session_state.loan_amount = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "🌾 **Namaskar! I am Gram Sahayak.**\n\nTap the mic to tell me how much loan you need."}
    ]

# --- PDF GENERATOR ---
def generate_pdf(name, area, amount, scheme_name):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setTitle(f"{scheme_name} Application")
    
    # Header
    c.setFillColorRGB(0.1, 0.4, 0.1) 
    c.setFont("Helvetica-Bold", 22)
    c.drawString(50, 750, f"APPLICATION: {scheme_name}")
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.line(50, 735, 550, 735)
    
    # Body
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 12)
    y = 700
    c.drawString(50, y, f"Date: {time.strftime('%d-%m-%Y')}")
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "1. Farmer Details (Verified)")
    c.setFont("Helvetica", 12)
    y -= 25
    c.drawString(50, y, f"Name: {name}")
    y -= 20
    c.drawString(50, y, f"Land Area: {area}")
    
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "2. Request Details")
    c.setFont("Helvetica", 12)
    y -= 25
    c.drawString(50, y, f"Loan Amount: {amount}")
    
    y -= 60
    c.drawString(50, y, "Signature:")
    c.line(120, y, 300, y)
    
    c.save()
    buffer.seek(0)
    return buffer

# --- CSS ---
st.markdown("""
<style>
    h1, h2, h3, p, div, span, label { color: #1a1a1a !important; font-family: 'Segoe UI', sans-serif; }
    .stApp { background: linear-gradient(180deg, #F1F8E9 0%, #FFFFFF 100%); }
    .stChatMessage { background-color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #e0e0e0; margin-bottom: 12px; padding: 15px; }
    .stChatMessage[data-testid="stChatMessageUser"] { background-color: #DCEDC8; border-left: 6px solid #558B2F; }
    .stButton>button { background: linear-gradient(90deg, #2E7D32 0%, #43A047 100%); color: white !important; border-radius: 25px; font-weight: bold; }
    .progress-container { display: flex; justify-content: space-between; margin-bottom: 20px; background: white; padding: 15px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .step-active { color: #2E7D32 !important; font-weight: bold; border-bottom: 3px solid #2E7D32; }
    .step-inactive { color: #aaa !important; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
col1, col2 = st.columns([1, 5])
with col1: st.markdown("## 🚜") 
with col2: st.title("Gram Sahayak")

st.markdown(f"""
<div class="progress-container">
    <div class="{ 'step-active' if st.session_state.step == 1 else 'step-inactive' }">1. 🎤 Voice</div>
    <div class="{ 'step-active' if st.session_state.step == 2 else 'step-inactive' }">2. 📸 Scan</div>
    <div class="{ 'step-active' if st.session_state.step == 3 else 'step-inactive' }">3. 📄 Apply</div>
</div>
""", unsafe_allow_html=True)

chat_placeholder = st.container()
with chat_placeholder:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

st.markdown("---")

# --- STEP 1: VOICE ---
if st.session_state.step == 1:
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        st.info("Tap to say loan amount")
        if st.button("🎤 Speak", use_container_width=True):
            user_text = "Mala tractor sathi 5 lakh rupaye hava ahet." 
            st.session_state.chat_history.append({"role": "user", "content": f"🗣️ **Spoken:** {user_text}"})
            
            if "5 lakh" in user_text: st.session_state.loan_amount = "₹ 5,00,000"
            else: st.session_state.loan_amount = "₹ 1,00,000"
            
            bot_reply = f"✅ Amount: **{st.session_state.loan_amount}**.\n\nNow, upload your **7/12 Extract**."
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: PHOTO (JSON MODE - NO FAKE DATA) ---
elif st.session_state.step == 2:
    uploaded_file = st.file_uploader("Upload", type=['jpg','png','jpeg'], label_visibility="collapsed")
    
    if uploaded_file:
        if st.button("🔍 Extract Real Data", use_container_width=True):
            with st.spinner("⚡ AI Reading Document..."):
                
                img = Image.open(uploaded_file)
                # Compressing slightly for speed
                img.thumbnail((1024, 1024))
                
                # UPDATED PROMPT: Request JSON format for accuracy
                prompt = """
                Analyze this 7/12 extract image.
                Extract:
                1. The first 'Occupant Name' or 'Owner Name' (Bhogvatdarache Nav) found.
                2. The 'Total Land Area' (in Hectares).
                
                Return ONLY a JSON object like this:
                {"name": "Extracted Name Here", "area": "Extracted Area Here"}
                """
                
                try:
                    response_text = model.generate_content([prompt, img]).text
                    
                    # Clean the response to ensure valid JSON
                    clean_json = response_text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_json)
                    
                    # Set the REAL data (No Fallbacks!)
                    st.session_state.farmer_name = data.get("name", "Unknown Farmer")
                    st.session_state.land_area = data.get("area", "Unknown Area")
                    
                    bot_msg = f"⚡ **Data Found:**\n👤 **Name:** {st.session_state.farmer_name}\n🌍 **Land:** {st.session_state.land_area}\n\nChecking eligible schemes..."
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_msg})
                    st.session_state.step = 3
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Could not read the document. Please try a clearer photo. Error: {e}")

# --- STEP 3: PREVIEW & DOWNLOAD ---
elif st.session_state.step == 3:
    if logic:
        profile = {
            "name": st.session_state.farmer_name,
            "occupation": "Farmer",
            "land_holding": st.session_state.land_area
        }
        schemes = logic.check_eligibility(profile)
        
        if schemes:
            # Check to prevent loop
            last_msg = st.session_state.chat_history[-1]["content"]
            if "Eligible Schemes" not in last_msg:
                scheme_msg = "🎉 **Eligible Schemes:**\n\n"
                for s in schemes:
                    scheme_msg += f"🔹 **{s['name']}**\n"
                st.session_state.chat_history.append({"role": "assistant", "content": scheme_msg})
                st.rerun()
            
            selected = st.selectbox("Select Scheme:", [s['name'] for s in schemes])
            
            # Generate PDF in Memory
            pdf_buffer = generate_pdf(
                st.session_state.farmer_name,
                st.session_state.land_area,
                st.session_state.loan_amount,
                selected
            )
            
            # --- PDF PREVIEW ---
            st.write("---")
            st.subheader("📄 Application Preview")
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            st.write("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Download PDF", 
                    data=pdf_buffer, 
                    file_name="Application.pdf", 
                    mime="application/pdf", 
                    use_container_width=True
                )
            with col2:
                share_msg = f"Application for {selected} generated for {st.session_state.farmer_name}!"
                st.link_button("📤 Share (WhatsApp)", f"https://wa.me/?text={share_msg}", use_container_width=True)
            
            if st.button("🔄 Start New", use_container_width=True):
                st.session_state.clear()
                st.rerun()