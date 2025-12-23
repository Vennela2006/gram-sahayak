import google.generativeai as genai
import os
from dotenv import load_dotenv
from PIL import Image

# 1. Load the secret key from .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 2. Configure the AI
if api_key:
    genai.configure(api_key=api_key)
else:
    print("⚠️ Error: GOOGLE_API_KEY not found in .env file")

def ask_gemini(image_file, user_prompt):
    """
    The main function that connects the App to the Brain.
    Args:
        image_file: The uploaded image (or None)
        user_prompt: The text question from the user
    """
    try:
        # We use 'gemini-1.5-flash' because it is fast and free
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Scenario 1: Image + Text (Scanning 7/12)
        if image_file:
            # Streamlit gives a "BytesIO" object, we convert it to an Image
            img = Image.open(image_file)
            
            # We send both the text AND the image to the AI
            response = model.generate_content([user_prompt, img])
            
        # Scenario 2: Text Only (Voice/Chat)
        else:
            response = model.generate_content(user_prompt)
            
        return response.text

    except Exception as e:
        return f"❌ AI Error: {str(e)}"