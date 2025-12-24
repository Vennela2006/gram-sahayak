import streamlit as st
import os
import io
import time
import base64
import json
import csv
import re
import requests
from gtts import gTTS
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Gram Sahayak", page_icon="🚜", layout="centered")
load_dotenv()

# --- API KEYS ---
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

# --- 🗣️ TRANSLATIONS ---
translations = {
    "English": {
        "title": "Gram Sahayak",
        "greeting": "Welcome! I am Gram Sahayak. How can I help you today?",
        "step1_btn": "🎤 Tap to Speak",
        "step1_info": "Click the button below and say 'I need 5 Lakh loan'",
        "step1_confirm": "I heard you need {amount}. If this is correct, I will take you to the next step.",
        "step2_intro": "Now, please upload your 7/12 Extract document by clicking the 'Browse files' button.",
        "step2_upload": "Upload 7/12 Extract",
        "step2_btn": "🔍 Extract Data",
        "step2_click_hint": "File uploaded! Now click the 'Extract Data' button to analyze it.",
        "step2_analyzing": "I am analyzing your document... Reading Name... Reading Area... Please wait.",
        "step2_verify": "Analysis Complete. I found the following details. Name: {name}. Land Area: {area}. Is this correct? Click Yes to confirm.",
        "btn_yes": "✅ Yes, Correct",
        "btn_no": "❌ No, Retry",
        "step3_eligible": "Congratulations! Based on your land area of {area}, you are eligible for these schemes. Please select one.",
        "step3_preview": "I have created your application form below. Please check if the details are correct. If yes, click the Submit button.",
        "step3_btn_submit": "✅ Submit Application",
        "success": "Your application has been submitted successfully! I have sent a confirmation to your phone. You can download the PDF now."
    },
    "Marathi": {
        "title": "ग्राम सहाय्यक",
        "greeting": "स्वागत आहे! मी ग्राम सहाय्यक आहे. आज मी तुम्हाला कशी मदत करू शकतो?",
        "step1_btn": "🎤 बोला",
        "step1_info": "खालील बटण दाबा आणि सांगा 'मला ५ लाखांचे कर्ज हवे आहे'",
        "step1_confirm": "तुम्हाला {amount} हवे आहेत हे मला समजले. हे बरोबर असल्यास, आपण पुढच्या पायरीवर जाऊया.",
        "step2_intro": "आता, कृपया 'Browse files' वर क्लिक करून तुमचा ७/१२ उतारा अपलोड करा.",
        "step2_upload": "७/१२ उतारा अपलोड करा",
        "step2_btn": "🔍 माहिती तपासा",
        "step2_click_hint": "फाइल अपलोड झाली! आता विश्लेषण करण्यासाठी 'माहिती तपासा' बटणावर क्लिक करा.",
        "step2_analyzing": "मी तुमच्या कागदपत्राची तपासणी करत आहे... नाव वाचत आहे... क्षेत्र वाचत आहे... कृपया थांबा.",
        "step2_verify": "तपासणी पूर्ण झाली. मला ही माहिती सापडली आहे. नाव: {name}. क्षेत्र: {area}. हे बरोबर आहे का? असल्यास 'होय' वर क्लिक करा.",
        "btn_yes": "✅ होय, बरोबर आहे",
        "btn_no": "❌ नाही, पुन्हा प्रयत्न करा",
        "step3_eligible": "अभिनंदन! तुमच्या {area} जमिनीच्या क्षेत्रानुसार तुम्ही या योजनांसाठी पात्र आहात. एक योजना निवडा.",
        "step3_preview": "मी तुमचा अर्ज तयार केला आहे. कृपया खालील प्रिव्ह्यू तपासा. सर्व माहिती बरोबर असल्यास 'जमा करा' बटण दाबा.",
        "step3_btn_submit": "✅ अर्ज जमा करा",
        "success": "तुमचा अर्ज यशस्वीरित्या जमा झाला आहे! मी तुमच्या मोबाईलवर मेसेज पाठवला आहे. तुम्ही आता PDF डाउनलोड करू शकता."
    },
    "Hindi": {
        "title": "ग्राम सहायक",
        "greeting": "स्वागत है! मैं ग्राम सहायक हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
        "step1_btn": "🎤 बोलें",
        "step1_info": "नीचे दिया गया बटन दबाएं और कहें 'मुझे 5 लाख का लोन चाहिए'",
        "step1_confirm": "मुझे समझ आया कि आपको {amount} चाहिए। यदि यह सही है, तो हम अगले चरण पर चलेंगे।",
        "step2_intro": "अब, कृपया 'Browse files' पर क्लिक करके अपना 7/12 दस्तावेज अपलोड करें।",
        "step2_upload": "7/12 अपलोड करें",
        "step2_btn": "🔍 डेटा निकालें",
        "step2_click_hint": "फाइल अपलोड हो गई! अब विश्लेषण के लिए 'डेटा निकालें' बटन पर क्लिक करें।",
        "step2_analyzing": "मैं आपके दस्तावेज़ का विश्लेषण कर रहा हूँ... नाम पढ़ रहा हूँ... क्षेत्र पढ़ रहा हूँ... कृपया प्रतीक्षा करें।",
        "step2_verify": "विश्लेषण पूरा हुआ। मुझे यह जानकारी मिली है। नाम: {name}। भूमि क्षेत्र: {area}। क्या यह सही है? पुष्टि करने के लिए 'हाँ' पर क्लिक करें।",
        "btn_yes": "✅ हाँ, सही है",
        "btn_no": "❌ नहीं, पुनः प्रयास करें",
        "step3_eligible": "बधाई हो! आपके {area} भूमि क्षेत्र के आधार पर आप इन योजनाओं के लिए पात्र हैं। कृपया एक चुनें।",
        "step3_preview": "मैंने आपका आवेदन पत्र तैयार कर लिया है। कृपया नीचे पूर्वावलोकन (Preview) देखें। यदि सब कुछ सही है, तो सबमिट बटन पर क्लिक करें।",
        "step3_btn_submit": "✅ आवेदन जमा करें",
        "success": "आपका आवेदन सफलतापूर्वक जमा कर दिया गया है! मैंने आपके मोबाइल पर संदेश भेज दिया है। आप अब PDF डाउनलोड कर सकते हैं."
    }
}

# --- 🔊 FUNCTION: AUDIO (ROBUST) ---
def speak_text(text, lang='mr'):
    try:
        tts = gTTS(text=text, lang=lang) 
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_b64 = base64.b64encode(audio_buffer.read()).decode()
        
        # We use a tiny visible player so you can see if it loaded
        # But we set width=1 to make it almost invisible but "active"
        audio_html = f"""
            <audio autoplay="true" style="width:1px; height:1px;">
            <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        # Show error if internet is down
        st.error(f"Audio Error (Check Internet): {e}")

# --- 📊 FUNCTION: DB ---
def save_to_csv(name, area, amount, scheme):
    file_name = "gram_sahayak_db.csv"
    if not os.path.exists(file_name):
        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Farmer Name", "Land Area", "Scheme", "Loan Amount"])
    try:
        with open(file_name, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([timestamp, name, area, scheme, amount])
        return True
    except Exception as e:
        st.error(f"Save Error: {e}")
        return False

# --- 🌦️ WEATHER ---
def get_weather(city="Solapur"):
    api_key = os.getenv("OPENWEATHER_API_KEY") 
    if not api_key: return None, None, None
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        data = requests.get(url).json()
        if data.get("cod") == 200:
            return data['main']['temp'], data['weather'][0]['description'], data['weather'][0]['icon']
    except:
        pass
    return None, None, None

# --- 📄 PDF ---
def generate_pdf(name, area, amount, scheme_name):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setTitle(f"{scheme_name} Application")
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 750, f"APPLICATION: {scheme_name}")
    c.line(50, 735, 550, 735)
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Date: {time.strftime('%d-%m-%Y')}")
    c.drawString(50, 660, f"Name: {name}")
    c.drawString(50, 640, f"Land Area: {area}")
    c.drawString(50, 600, f"Loan Amount: {amount}")
    c.save()
    buffer.seek(0)
    return buffer

# --- CSS ---
st.markdown("""
<style>
    h1, h2, h3, p, div, span, label, .stMetric { color: #1a1a1a !important; font-family: 'Segoe UI', sans-serif; }
    .stApp { background: linear-gradient(180deg, #F1F8E9 0%, #FFFFFF 100%); }
    section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 2px solid #e0e0e0; }
    .stChatMessage { background-color: white; border-radius: 12px; border: 1px solid #e0e0e0; padding: 15px; }
    .stChatMessage[data-testid="stChatMessageUser"] { background-color: #DCEDC8; border-left: 6px solid #558B2F; }
    .stButton>button { background: linear-gradient(90deg, #2E7D32 0%, #43A047 100%); color: white !important; font-weight: bold; border: none; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    lang_choice = st.radio("Language / भाषा:", ["Marathi", "Hindi", "English"])
    
    if "last_lang" not in st.session_state: st.session_state.last_lang = lang_choice
    if st.session_state.last_lang != lang_choice:
        st.session_state.clear()
        st.session_state.last_lang = lang_choice
        st.rerun()

    t = translations[lang_choice]
    voice_lang = 'mr' if lang_choice == "Marathi" else ('hi' if lang_choice == "Hindi" else 'en')

    st.divider()
    st.header("📍 Weather")
    temp, desc, icon = get_weather("Solapur")
    if temp:
        col1, col2 = st.columns([1, 2])
        with col1: st.image(f"http://openweathermap.org/img/wn/{icon}@2x.png", width=50)
        with col2: st.metric("Solapur", f"{temp}°C", desc.title())

# --- STATE ---
if "step" not in st.session_state: st.session_state.step = 0 # Start at 0 for Welcome Screen
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "review_mode" not in st.session_state: st.session_state.review_mode = False
if "schemes_shown" not in st.session_state: st.session_state.schemes_shown = False
if "preview_shown" not in st.session_state: st.session_state.preview_shown = False
if "pdf_ready" not in st.session_state: st.session_state.pdf_ready = False

# --- MAIN UI ---
col1, col2 = st.columns([1, 5])
with col1: st.markdown("## 🚜") 
with col2: st.title(t['title'])

chat_placeholder = st.container()
with chat_placeholder:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

st.markdown("---")

# --- STEP 0: WELCOME SCREEN (NEW) ---
if st.session_state.step == 0:
    st.info("👋 Click Start to begin.")
    if st.button("🚀 Start App / अ‍ॅप सुरू करा", use_container_width=True):
        st.session_state.chat_history.append({"role": "assistant", "content": t['greeting']})
        speak_text(t['greeting'], lang=voice_lang)
        st.session_state.step = 1
        st.rerun()

# --- STEP 1: VOICE ---
elif st.session_state.step == 1:
    col_b = st.columns([1, 2, 1])[1]
    with col_b:
        st.info(t['step1_info'])
        if st.button(t['step1_btn'], use_container_width=True):
            if lang_choice == "English": user_text = "I need a loan of 5 Lakh rupees."
            elif lang_choice == "Hindi": user_text = "Mujhe 5 lakh rupaye ka loan chahiye."
            else: user_text = "Mala 5 lakh rupaye hava ahet."

            st.session_state.chat_history.append({"role": "user", "content": f"🗣️ **{user_text}**"})
            
            if "5" in user_text: st.session_state.loan_amount = "₹ 5,00,000"
            else: st.session_state.loan_amount = "₹ 1,00,000"
            
            msg = t['step1_confirm'].format(amount=st.session_state.loan_amount)
            st.session_state.chat_history.append({"role": "assistant", "content": msg})
            speak_text(msg, lang=voice_lang)
            
            # ⏳ INCREASED DELAY TO 5 SECONDS so audio finishes
            with st.spinner("Listening..."):
                time.sleep(5)
            
            st.session_state.step = 2
            st.rerun()

# --- STEP 2: SCAN & VERIFY ---
elif st.session_state.step == 2:
    if not st.session_state.review_mode:
        if "step2_intro_spoken" not in st.session_state:
            speak_text(t['step2_intro'], lang=voice_lang)
            st.session_state.step2_intro_spoken = True

        st.write(t['step2_intro'])
        uploaded_file = st.file_uploader(t['step2_upload'], type=['jpg','png','jpeg'], label_visibility="collapsed")
        
        if uploaded_file:
            if "step2_hint_spoken" not in st.session_state:
                speak_text(t['step2_click_hint'], lang=voice_lang)
                st.session_state.step2_hint_spoken = True
            
            st.info(t['step2_click_hint'])
            
            if st.button(t['step2_btn'], use_container_width=True):
                with st.spinner("AI Processing..."):
                    speak_text(t['step2_analyzing'], lang=voice_lang)
                    img = Image.open(uploaded_file)
                    
                    prompt = """
                    Extract from this 7/12 document:
                    1. Name (Bhogvatdarache Nav)
                    2. Area (Hectare)
                    Return JSON: {"name": "...", "area": "..."}
                    """
                    try:
                        response = model.generate_content([prompt, img])
                        match = re.search(r'\{.*\}', response.text, re.DOTALL)
                        
                        if match:
                            data = json.loads(match.group(0))
                            st.session_state.farmer_name = data.get("name", "Farmer")
                            st.session_state.land_area = data.get("area", "1.00")
                            st.session_state.review_mode = True 
                            st.rerun()
                        else:
                            st.error("Could not read image.")
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        verify_msg = t['step2_verify'].format(name=st.session_state.farmer_name, area=st.session_state.land_area)
        if "verified_spoken" not in st.session_state:
            st.session_state.chat_history.append({"role": "assistant", "content": verify_msg})
            speak_text(verify_msg, lang=voice_lang)
            st.session_state.verified_spoken = True

        st.success(f"**Name:** {st.session_state.farmer_name}")
        st.success(f"**Area:** {st.session_state.land_area}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t['btn_yes'], use_container_width=True):
                st.session_state.step = 3
                st.rerun()
        with col2:
            if st.button(t['btn_no'], use_container_width=True):
                st.session_state.review_mode = False 
                if "verified_spoken" in st.session_state: del st.session_state.verified_spoken
                st.rerun()

# --- STEP 3: PREVIEW & SUBMIT ---
elif st.session_state.step == 3:
    if logic:
        profile = {"name": st.session_state.farmer_name, "occupation": "Farmer", "land_holding": st.session_state.land_area}
        schemes = logic.check_eligibility(profile)
        
        if schemes:
            if not st.session_state.schemes_shown:
                msg = t['step3_eligible'].format(area=st.session_state.land_area)
                scheme_list = "\n".join([f"- {s['name']}" for s in schemes])
                st.session_state.chat_history.append({"role": "assistant", "content": f"🎉 **{msg}**\n\n{scheme_list}"})
                speak_text(msg, lang=voice_lang)
                st.session_state.schemes_shown = True
                st.rerun()
            
            selected = st.selectbox("Select Scheme:", [s['name'] for s in schemes])
            pdf_buffer = generate_pdf(st.session_state.farmer_name, st.session_state.land_area, st.session_state.loan_amount, selected)
            
            st.divider()
            
            if not st.session_state.preview_shown:
                speak_text(t['step3_preview'], lang=voice_lang)
                st.session_state.preview_shown = True
            
            st.markdown("### 📝 Application Review")
            base64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
            st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(t['step3_btn_submit'], use_container_width=True):
                    save_to_csv(st.session_state.farmer_name, st.session_state.land_area, st.session_state.loan_amount, selected)
                    st.toast("Saved!", icon="💾")
                    speak_text(t['success'], lang=voice_lang)
                    st.session_state.pdf_ready = True
                    st.rerun()
            
            with col2:
                if st.session_state.pdf_ready:
                    st.download_button("⬇️ Download PDF", pdf_buffer, "Application.pdf", "application/pdf", use_container_width=True)

            if st.button("🔄 Restart"):
                st.session_state.clear()
                st.rerun()