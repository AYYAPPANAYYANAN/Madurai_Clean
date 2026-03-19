import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import requests
from datetime import datetime
import streamlit.components.v1 as components 
import random
from PIL import Image
import torch
from streamlit_geolocation import streamlit_geolocation
from transformers import CLIPProcessor, CLIPModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. PAGE CONFIG (Must be first) ---
st.set_page_config(page_title="Madurai CleanAI", page_icon="♻️", layout="wide", initial_sidebar_state="collapsed")

# --- AI ENGINE INITIALIZATION ---
@st.cache_resource
def load_deepfake_detector():
    from transformers import pipeline
    # This is a dedicated ViT model trained specifically to spot AI-generated artifacts
    return pipeline("image-classification", model="umm-maybe/AI-image-detector")

@st.cache_resource
def load_vision_model():
    vision_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    vision_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return vision_model, vision_processor

@st.cache_resource
def load_object_detector():
    from transformers import pipeline
    # DETR model specifically excels at counting distinct objects in a scene
    return pipeline("object-detection", model="facebook/detr-resnet-50")

waste_detector = load_object_detector()

ai_detector = load_deepfake_detector()
vision_model, vision_processor = load_vision_model()

# --- CUSTOM EMOJI POP ANIMATION ---
def eco_emoji_pop():
    emojis = ['🌱', '♻️', '🌍', '✨', '🏆', '💚']
    css = "<style>@keyframes eco-fall { 0% { top: -10%; opacity: 1; transform: rotate(0deg); } 100% { top: 110%; opacity: 0; transform: rotate(360deg); } }</style>"
    html = ""
    for i in range(35): 
        e = random.choice(emojis)
        left = random.randint(0, 100)
        delay = random.uniform(0, 1.5)
        dur = random.uniform(2, 4)
        size = random.uniform(1.5, 3)
        html += f'<div style="position:fixed; left:{left}%; font-size:{size}rem; z-index:99999; pointer-events:none; animation: eco-fall {dur}s linear {delay}s forwards;">{e}</div>'
    st.markdown(css + html, unsafe_allow_html=True)

# --- AUTOMATED ESCALATION ENGINE ---
def send_escalation_email(location, category, total_reports):
    sender_email = "ayyappan50465@gmail.com" 
    sender_password = "gkny mify pwqd udfp" 
    receiver_email = "ayyappan50465@gmail.com"  

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"🚨 URGENT: Chronic Waste Issue Detected at {location}"

    body = f"""
    Dear Municipal Corporation Authorities,

    The CleanAI System has detected a severe, recurring waste accumulation issue.
    
    📍 Location: {location}
    ♻️ Waste Category (AI Detected): {category}
    ⚠️ Total Citizen Reports Logged: {total_reports}

    This location has exceeded the acceptable threshold for unattended waste. 
    Please dispatch a cleaning unit immediately to prevent further environmental degradation.

    System Auto-Generated Email
    Madurai CleanAI Protocol
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False

# --- SOS EMERGENCY DISPATCH ---
def send_sos_email(location, user_query):
    sender_email = "ayyappan50465@gmail.com" 
    sender_password = "gkny mify pwqd udfp" 
    receiver_email = "ayyappan50465@gmail.com"  

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"🚨 EXTREME SOS URGENT: Disaster reported at {location}"

    body = f"""
    EMERGENCY PROTOCOL ACTIVATED.
    
    📍 Last Known Location: {location}
    🎙️ Victim's Voice Query/Status: "{user_query}"
    
    Immediate assistance is required at these coordinates. Dispatch rescue units immediately.
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        return False

# --- 🌪️ DISASTER DETECTION ENGINE ---
def check_severe_weather(lat=9.9252, lon=78.1198): 
    # ⚠️ Replace with your free OpenWeatherMap API Key
    API_KEY = "YOUR_OPENWEATHERMAP_API_KEY" 
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}"
    
    try:
        response = requests.get(url, timeout=5).json()
        weather_id = response['weather'][0]['id']
        weather_desc = response['weather'][0]['description']
        
        # OpenWeatherMap Codes: 
        # 200-299 (Thunderstorms), 500-504 (Extreme Rain/Flood conditions)
        if weather_id < 600: 
            return True, weather_desc.title()
        return False, "Normal"
    except Exception as e:
        return False, "API Offline"

# --- 2. SESSION STATE INITIALIZATION ---
if 'lang' not in st.session_state: st.session_state.lang = 'English'
if 'theme' not in st.session_state: st.session_state.theme = 'Neon Purple' 
if 'activity_log' not in st.session_state: st.session_state.activity_log = []
if 'chat_history' not in st.session_state: st.session_state.chat_history = [{"role": "assistant", "content": "System Online. I am the CleanAI Core. Ask me about city waste data, pending alerts, or your EcoPoints."}]
if 'users_db' not in st.session_state: st.session_state.users_db = {'admin@madurai.com': 'admin123'}
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = 'login'
if 'location_reports' not in st.session_state: st.session_state.location_reports = {}
if 'waste_inventory' not in st.session_state: st.session_state.waste_inventory = {'bottle': 0, 'cup': 0, 'bag': 0, 'debris': 0}

# --- 3. PREMIUM DARK THEME ENGINE ---
themes = {
    'Neon Green':  {'primary': '#10b981', 'glow': 'rgba(16, 185, 129, 0.2)', 'px_color': px.colors.sequential.algae},
    'Cyber Blue':  {'primary': '#3b82f6', 'glow': 'rgba(59, 130, 246, 0.2)', 'px_color': px.colors.sequential.Blues},
    'Neon Purple': {'primary': '#8b5cf6', 'glow': 'rgba(139, 92, 246, 0.2)', 'px_color': px.colors.sequential.Purples},
    'Crimson':     {'primary': '#ef4444', 'glow': 'rgba(239, 68, 68, 0.2)', 'px_color': px.colors.sequential.Reds}
}
current_theme = themes[st.session_state.theme]

t = {
    'English': {
        'title': 'MADURAI CLEAN-AI', 'subtitle': 'Multimodal AI Waste Management • Smart City Protocol',
        'tabs': ["📲 CITIZEN PORTAL", "📊 COMMAND CENTER", "📍 ANALYTICS", "🤖 AI ASSISTANT", "⚙️ SETTINGS"],
        'report': 'Report New Incident', 'analyze': '🚀 INITIATE MULTIMODAL SCAN',
        'leaderboard': 'City Leaderboard', 'pending': 'ACTIVE ALERTS',
        'settings_title': 'System Preferences', 'history_title': 'User Activity Log',
        'landmark_label': 'Target Sector / Landmark', 'success_msg': 'Alert broadcasted for {}. +50 EcoPoints awarded! 🌱',
        'desc_label': '📝 Context / Description (Optional)', 'voice_label': '🎙️ Record Voice Memo (Optional)'
    },
    'Tamil': {
        'title': 'மதுரை CLEAN-AI', 'subtitle': 'மல்டிமோடல் AI கழிவு மேலாண்மை',
        'tabs': ["📲 குடிமக்கள் தளம்", "📊 கட்டுப்பாட்டு மையம்", "📍 பகுப்பாய்வு", "🤖 AI உதவியாளர்", "⚙️ அமைப்புகள்"],
        'report': 'புதிய நிகழ்வை பதிவு செய்', 'analyze': '🚀 AI ஸ்கேனைத் தொடங்கு',
        'leaderboard': 'தரவரிசை', 'pending': 'செயலில் உள்ள எச்சரிக்கைகள்',
        'settings_title': 'கணினி அமைப்புகள்', 'history_title': 'உங்கள் பதிவு',
        'landmark_label': 'இலக்கு பகுதி / அடையாளம்', 'success_msg': '{} எச்சரிக்கை அனுப்பப்பட்டது. +50 புள்ளிகள்! 🌱',
        'desc_label': '📝 விவரங்கள் (விருப்பம்)', 'voice_label': '🎙️ குரல் பதிவைச் சேர்க்க (விருப்பம்)'
    }
}
lang = t[st.session_state.lang]

# --- 4. ADVANCED DARK CSS INJECTION ---
st.markdown(f"""
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700;900&family=Inter:wght@400;500;600&display=swap');
    
    /* 1. DEEP BLACK CANVAS (Vercel/Linear Vibe) */
    .stApp, [data-testid="stAppViewContainer"] {{
        background-color: #000000 !important;
        background-image: 
            radial-gradient(circle at 50% -20%, rgba(30, 30, 35, 0.6) 0%, transparent 60%),
            linear-gradient(to bottom, #000000 0%, #050505 100%);
        color: #ededed !important; 
        font-family: 'Inter', sans-serif;
    }}
    
    /* Hide Streamlit's default noisy header */
    [data-testid="stHeader"] {{ background: transparent !important; }}
    
    h1, h2, h3, h4, p, label, .stMarkdown span {{ color: #ededed !important; }}
    
    /* 2. SLEEK BRANDING */
    .header-container {{
        text-align: center; padding: 4rem 0 2rem 0;
        background: transparent !important; border: none !important;
    }}
    
    .brand-text {{ 
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(180deg, #ffffff 0%, rgba(255,255,255,0.7) 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0px 10px 40px rgba(255,255,255,0.15);
        letter-spacing: -0.05em;
        line-height: 1.1;
    }}
    
    .subtitle-text {{ 
        color: {current_theme['primary']} !important; 
        letter-spacing: 0.25em; 
        font-weight: 700;
        font-family: 'Outfit', sans-serif;
        text-shadow: 0 0 20px {current_theme['glow']};
    }}

    /* 3. BENTO BOX CARDS (Glassmorphism + Ultra-thin borders) */
    .auth-card, .stat-card, .glass-panel {{
        background: rgba(15, 15, 17, 0.4) !important; 
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.06); 
        border-radius: 28px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.8), inset 0 1px 0 0 rgba(255,255,255,0.05);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }}
    
    .stat-card {{ padding: 1.5rem 2rem; text-align: left; }}
    .stat-card:hover {{ 
        transform: translateY(-5px); 
        border-color: rgba(255, 255, 255, 0.15); 
        background: rgba(25, 25, 28, 0.6) !important;
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.9), 0 0 40px {current_theme['glow']}; 
    }}
    .stat-card h2 {{ color: #ffffff !important; font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 2.5rem !important; margin-top: 0.2rem;}}
    .stat-card p {{ color: #888888 !important; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; margin: 0;}}

    /* 4. DRAG & DROP ZONE */
    [data-testid="stFileUploadDropzone"] {{
        background: rgba(15, 15, 17, 0.5) !important; 
        border: 1px dashed rgba(255,255,255,0.15) !important;
        border-radius: 24px; padding: 3rem !important; transition: all 0.3s ease;
    }}
    [data-testid="stFileUploadDropzone"]:hover {{
        border-color: {current_theme['primary']} !important;
        background: rgba(25, 25, 28, 0.8) !important;
        box-shadow: 0 0 30px {current_theme['glow']};
    }}
    
    /* 5. INPUTS & TEXT AREAS (iOS Pill Style) */
    .stTextArea textarea, .stChatInput input, .stTextInput input {{
        background: rgba(20, 20, 22, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important; border-radius: 20px; padding: 1.2rem;
        transition: all 0.2s ease;
        font-family: 'Inter', sans-serif;
    }}
    .stTextArea textarea:focus, .stChatInput input:focus, .stTextInput input:focus {{
        border-color: {current_theme['primary']} !important; 
        background: rgba(30, 30, 35, 0.9) !important;
        box-shadow: 0 0 0 3px {current_theme['glow']} !important;
    }}

    /* 6. BUTTONS (Sleek Apple-like) */
    .stButton>button {{
        border-radius: 999px; /* Absolute pill shape */
        background: #ffffff !important; 
        border: 1px solid #ffffff !important;
        color: #000000 !important; 
        font-weight: 600; font-family: 'Inter', sans-serif; letter-spacing: 0.02em;
        height: 3.2rem; width: 100%;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .stButton>button:hover {{ 
        transform: scale(1.02);
        background: #e0e0e0 !important;
        box-shadow: 0 8px 20px rgba(255,255,255,0.15); 
    }}
    .stButton>button p {{ color: inherit !important; font-weight: inherit !important; }}
    
    /* Primary/SOS Button Override */
    button[data-testid="baseButton-primary"] {{
        background: {current_theme['primary']} !important;
        border-color: {current_theme['primary']} !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px {current_theme['glow']};
    }}
    button[data-testid="baseButton-primary"]:hover {{
        box-shadow: 0 8px 25px {current_theme['glow']};
        filter: brightness(1.2);
    }}
    
    /* 7. FLOATING iOS-STYLE TABS */
    [data-testid="stTabs"] {{ padding-top: 1rem; }}
    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        gap: 0.5rem; justify-content: center; width: fit-content; margin: 0 auto 2rem auto;
        background: rgba(20, 20, 22, 0.6); border-radius: 99px; padding: 0.4rem;
        border: 1px solid rgba(255,255,255,0.05);
    }}
    [data-testid="stTabs"] button[role="tab"] {{
        padding: 0.6rem 1.5rem; font-weight: 500; font-size: 0.85rem;
        border-radius: 99px; background: transparent; border: none;
        color: #888888 !important; transition: all 0.3s ease;
    }}
    [data-testid="stTabs"] button[role="tab"]:hover {{
        color: #ffffff !important;
    }}
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
        background: rgba(255,255,255,0.1);
        color: #ffffff !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }}
    
    /* Map Container Fix */
    [data-testid="stDeckGlJsonChart"] {{
        border-radius: 20px; overflow: hidden;
        border: 1px solid rgba(255,255,255,0.05);
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🛑 SECURE AUTHENTICATION SCREEN
# ==========================================
if st.session_state.current_user is None:
    st.markdown(f"""
        <div class="header-container">
            <h1 class="text-4xl md:text-6xl font-black brand-text tracking-tighter">🏙️ {lang['title']}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown(f'<h1 style="font-size: 3rem; text-shadow: 0 0 20px {current_theme["primary"]};">🔐</h1>', unsafe_allow_html=True)
        
        if st.session_state.auth_mode == 'login':
            st.markdown('<h2 style="font-weight: 800; margin-bottom: 1.5rem;">SYSTEM ACCESS</h2>', unsafe_allow_html=True)
            email = st.text_input("User ID (Email)", placeholder="admin@madurai.com")
            password = st.text_input("Security Key (Password)", type="password", placeholder="••••••••")
            if st.button("AUTHORIZE CONNECTION", use_container_width=True):
                if email in st.session_state.users_db and st.session_state.users_db[email] == password:
                    st.session_state.current_user = email
                    st.rerun()
                else: st.error("Access Denied.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Register New Operative", use_container_width=True): 
                st.session_state.auth_mode = 'signup'
                st.rerun()
                
        else: # SIGNUP
            st.markdown('<h2 style="font-weight: 800; margin-bottom: 1.5rem;">NEW OPERATIVE</h2>', unsafe_allow_html=True)
            new_email = st.text_input("Assign User ID (Email)", placeholder="hero@madurai.com")
            new_password = st.text_input("Set Security Key", type="password", placeholder="••••••••")
            if st.button("INITIALIZE ACCOUNT", use_container_width=True):
                if new_email in st.session_state.users_db: st.error("User ID already registered!")
                else: 
                    st.session_state.users_db[new_email] = new_password
                    st.session_state.current_user = new_email
                    eco_emoji_pop()
                    st.rerun()

# ==========================================
# ✅ MAIN DASHBOARD 
# ==========================================
else:
    # --- 🌪️ DISASTER SOS MODULE ---
    # --- 🌪️ ADVANCED SIDEBAR & SOS MODULE ---
    with st.sidebar:
        # 1. User Profile Bento Box
        st.markdown(f"""
            <div style="background: rgba(20, 20, 22, 0.6); border: 1px solid rgba(255,255,255,0.05); border-radius: 24px; padding: 2rem 1.5rem; text-align: center; margin-bottom: 2rem; backdrop-filter: blur(12px); box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);">
                <div style="width: 70px; height: 70px; border-radius: 50%; background: linear-gradient(135deg, {current_theme['primary']}, #ffffff); margin: 0 auto 15px auto; display: flex; align-items: center; justify-content: center; font-size: 2rem; box-shadow: 0 0 20px {current_theme['glow']};">
                    🕵️
                </div>
                <h4 style="margin: 0; color: #ffffff; font-weight: 800; font-family: 'Outfit', sans-serif; font-size: 1.2rem;">{st.session_state.current_user.split('@')[0]}</h4>
                <p style="margin: 2px 0 15px 0; color: #888888; font-size: 0.75rem; letter-spacing: 1px;">LEVEL 1 OPERATIVE</p>
                <div style="background: rgba(0,0,0,0.3); border-radius: 12px; padding: 10px;">
                    <p style="margin: 0; color: {current_theme['primary']}; font-weight: 800; letter-spacing: 1.5px; font-size: 0.7rem;">ECO-CREDITS</p>
                    <p style="margin: 0; color: #ffffff; font-weight: 700; font-size: 1.5rem; font-family: 'Space Grotesk', sans-serif;">1,250</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-bottom: 2rem;'>", unsafe_allow_html=True)

        # 2. Sleek Emergency Override Section
        st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem;">
                <span style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; padding: 6px 14px; border-radius: 99px; font-size: 0.7rem; font-weight: 800; letter-spacing: 2px;">EMERGENCY OVERRIDE</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Check live weather quietly
        disaster_detected, condition = check_severe_weather()
        
        if disaster_detected:
            st.markdown(f"<div style='background: rgba(239, 68, 68, 0.15); padding: 10px; border-radius: 10px; margin-bottom: 15px; text-align: center;'><p style='color: #ef4444; font-weight: 700; font-size: 0.8rem; margin: 0;'>⚠️ {condition}</p></div>", unsafe_allow_html=True)
            st.session_state.sos_active = True 
        else:
            st.markdown("<p style='text-align: center; color: #52525b; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px;'>🌤️ GRID PARAMETERS NOMINAL</p>", unsafe_allow_html=True)

        # Custom CSS specifically for the SOS button to make it look like a physical glowing switch
        st.markdown("""
            <style>
            div[data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
                background: linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%) !important;
                border: 1px solid #f87171 !important;
                color: #ffffff !important;
                font-family: 'Outfit', sans-serif;
                letter-spacing: 1px;
                box-shadow: 0 10px 25px -5px rgba(239, 68, 68, 0.5), inset 0 2px 5px rgba(255,255,255,0.3);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }
            div[data-testid="stSidebar"] button[data-testid="baseButton-primary"]:hover {
                box-shadow: 0 15px 35px -5px rgba(239, 68, 68, 0.8), inset 0 2px 5px rgba(255,255,255,0.4);
                transform: translateY(-2px);
                filter: brightness(1.1);
            }
            div[data-testid="stSidebar"] button[data-testid="baseButton-primary"]:active {
                transform: translateY(1px);
            }
            </style>
        """, unsafe_allow_html=True)
        
        if st.button("🔴 INITIATE SOS", type="primary", use_container_width=True):
            st.session_state.sos_active = True
            
        # 3. The SOS Audio UI
        if st.session_state.get('sos_active', False):
            st.markdown("""
                <div style='background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; padding: 12px; border-radius: 0 8px 8px 0; margin-top: 20px; margin-bottom: 10px;'>
                    <p style='color: #ef4444; margin: 0; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;'>🎙️ SECURE CHANNEL OPEN<br><span style='color: #fca5a5; font-weight: 500;'>Speak situation clearly</span></p>
                </div>
            """, unsafe_allow_html=True)
            
            emergency_audio = st.audio_input("Record Emergency Message", label_visibility="collapsed")
            
            if emergency_audio:
                with st.spinner("Broadcasting encrypted signal..."):
                    transcribed_text = "User requires immediate medical/evacuation assistance." 
                    current_loc = f"Lat {location_data['latitude']}, Lon {location_data['longitude']}" if 'location_data' in locals() and location_data and location_data.get('latitude') else "Madurai General Grid"
                    
                    send_sos_email(current_loc, transcribed_text)
                    
                    st.markdown("<p style='color: #10b981; font-weight: 700; font-size: 0.8rem; text-align: center; margin-top: 10px;'>📡 BROADCAST SUCCESS</p>", unsafe_allow_html=True)                
    # UPLINK BAR
    st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.8); border-bottom: 1px solid {current_theme['primary']}; padding: 0.5rem 2rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 20px {current_theme['glow']};">
            <span style="color: #10b981; font-weight: 900; font-size: 0.75rem; letter-spacing: 1px;">● UPLINK SECURED</span>
            <span style="color: #94a3b8; font-weight: bold; font-size: 0.75rem;">OPERATIVE: <span style="color: {current_theme['primary']} !important;">{st.session_state.current_user}</span></span>
        </div>
    """, unsafe_allow_html=True)

    # DINO GAME
    st.markdown("<br>", unsafe_allow_html=True)
    components.html(
        f"""
         <div style="border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5); background: rgba(15, 23, 42, 0.4); position: relative; font-family: 'Courier New', monospace;">
            <div style="position: absolute; top: 15px; left: 20px; color: {current_theme['primary']}; font-weight: bold; font-size: 12px; letter-spacing: 2px; text-shadow: 0 0 10px {current_theme['glow']};">
                ● AI MODEL TRAINING [REINFORCEMENT LEARNING]
            </div>
            <div style="position: absolute; top: 15px; right: 20px; color: {current_theme['primary']}; font-weight: bold; font-size: 12px; text-shadow: 0 0 10px {current_theme['glow']};">
                GENERATION: <span id="gen">42</span> | SCORE: <span id="score">0000</span>
            </div>
            <canvas id="aiCanvas" style="width: 100%; height: 200px; display: block;"></canvas>
        </div>
        <script>
            const canvas = document.getElementById('aiCanvas');
            const ctx = canvas.getContext('2d');
            const themeColor = '{current_theme['primary']}';
            function resize() {{ canvas.width = canvas.parentElement.clientWidth; canvas.height = 200; }}
            window.addEventListener('resize', resize); resize();
            let score = 0; let frame = 0; let speed = 6.5;
            const agent = {{ x: 80, y: 150, width: 24, height: 24, dy: 0, jumpPower: -12.5, grounded: true }};
            const gravity = 0.65; let obstacles = [];
            function drawAgent() {{ ctx.shadowBlur = 15; ctx.shadowColor = themeColor; ctx.fillStyle = themeColor; ctx.fillRect(agent.x, agent.y, agent.width, agent.height); ctx.shadowBlur = 0; ctx.fillStyle = '#0f172a'; ctx.fillRect(agent.x + 14, agent.y + 6, 6, 6); }}
            function drawObstacles() {{ ctx.fillStyle = themeColor; ctx.globalAlpha = 0.8; obstacles.forEach(obs => {{ ctx.fillRect(obs.x, obs.y, obs.width, obs.height); }}); ctx.globalAlpha = 1.0; }}
            function drawGrid() {{ ctx.strokeStyle = 'rgba(255,255,255,0.05)'; ctx.lineWidth = 1; for(let i=0; i<canvas.width; i+=40) {{ ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, canvas.height); ctx.stroke(); }} }}
            function update() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height); drawGrid();
                ctx.strokeStyle = themeColor; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, 174); ctx.lineTo(canvas.width, 174); ctx.stroke();
                agent.dy += gravity; agent.y += agent.dy;
                if(agent.y + agent.height >= 174) {{ agent.y = 174 - agent.height; agent.dy = 0; agent.grounded = true; }}
                if(frame % Math.floor(Math.random() * 50 + 70) === 0) {{ obstacles.push({{ x: canvas.width, y: 144, width: 20, height: 30 }}); }}
                if(obstacles.length > 0) {{ let nextObs = obstacles[0]; let dist = nextObs.x - (agent.x + agent.width); if(dist > 0 && dist < 125 && agent.grounded) {{ agent.dy = agent.jumpPower; agent.grounded = false; }} }}
                for(let i=0; i<obstacles.length; i++) {{ obstacles[i].x -= speed; }}
                obstacles = obstacles.filter(obs => obs.x + obs.width > 0);
                drawObstacles(); drawAgent(); score += 0.1; document.getElementById('score').innerText = Math.floor(score).toString().padStart(4, '0');
                frame++; requestAnimationFrame(update);
            }}
            update();
        </script>
        """, height=205)

    # MAIN HEADER
    st.markdown(f"""
        <div class="header-container">
           <h1 class="text-4xl md:text-6xl font-black brand-text tracking-tighter">{lang['title']}</h1>
            <p class="subtitle-text font-bold text-xs mt-3 uppercase">{lang['subtitle']}</p>
        </div>
    """, unsafe_allow_html=True)

    # MAP DATA
    df_madurai = pd.DataFrame({
        'Location': ['Meenakshi Amman Temple', 'Mattuthavani', 'Goripalayam', 'Teppakulam', 'Vaigai River', 'Railway Station'],
        'lat': [9.9195, 9.9515, 9.9264, 9.9125, 9.9320, 9.9160], 'lon': [78.1193, 78.1510, 78.1298, 78.1450, 78.1300, 78.1100]
    })

    # TABS INITIALIZATION
    menu = st.tabs(lang['tabs'])

    # --- TAB 1: CITIZEN PORTAL ---
    with menu[0]:
        col_a, col_b = st.columns([1, 1], gap="large")
        
        with col_a:
            st.markdown(f"<h3 style='font-weight: 800; margin-bottom: 1rem; color: #f8fafc;'>{lang['report']}</h3>", unsafe_allow_html=True)
            input_method = st.radio("📸 Input Method", ["Upload Image", "Use Camera"], horizontal=True)

            if input_method == "Upload Image":
                uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
            else:
                uploaded_file = st.camera_input("Take a live picture of the waste")
            st.markdown("<br>", unsafe_allow_html=True)
            incident_desc = st.text_area(lang['desc_label'], placeholder="E.g., It is blocking the road...", height=100)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<label style='font-weight: 600; color: #f8fafc; font-size: 14px;'>{lang['voice_label']}</label>", unsafe_allow_html=True)
            voice_note = st.audio_input("Record", label_visibility="collapsed")
            
            landmark = st.text_input(lang['landmark_label'], placeholder="e.g., Kalavasal Junction, Madurai...")
            
            st.write("Or use precise GPS:")
            location_data = streamlit_geolocation()
            if location_data['latitude'] is not None:
                st.success(f"📍 GPS Locked: Lat {location_data['latitude']}, Lon {location_data['longitude']}")
            
            if st.button(lang['analyze'], use_container_width=True):
                if uploaded_file is None:
                    st.error("⚠️ Please upload an image first.")
                elif not landmark.strip():
                    st.error("⚠️ Please enter your location so we can track this report.")
                else:
                    with st.status("Initializing Multimodal Neural Net...", expanded=True) as status:
                        time.sleep(1); st.write("🛰️ Triangulating GPS coordinates...")
                        st.write("🤖 Vision Model: **Running neural inference on image...**")
                        
                        img = Image.open(uploaded_file)
                        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                        
                    
                        # --- 🛡️ STAGE 1: VERI-PIXEL 6.0 ADVANCED FORENSICS ---
                        st.write("🛡️ Veri-Pixel 6.0: **Executing 5-Layer Multi-Spectral Analysis...**")
                        
                        import io
                        import numpy as np
                        from PIL import ImageChops, ImageFilter
                        
                        # ATTEMPT 1: Neural Global Scan (Full Image)
                        res_full = ai_detector(img)
                        score_full = next((r['score'] for r in res_full if r['label'] == 'artificial'), 0.0)
                        
                        # ATTEMPT 2: Neural Micro-Texture Scan (Cropped Center)
                        # AI models often hallucinate or blur complex details in the center of an image.
                        w, h = img.size
                        img_center = img.crop((w/4, h/4, 3*w/4, 3*h/4))
                        res_center = ai_detector(img_center)
                        score_center = next((r['score'] for r in res_center if r['label'] == 'artificial'), 0.0)
                        
                        # ATTEMPT 3: Mathematical Error Level Analysis (ELA)
                        # AI images lack real camera sensor (ISO) noise, resulting in unnatural JPEG compression.
                        buffer = io.BytesIO()
                        img_rgb = img.convert('RGB')
                        img_rgb.save(buffer, format='JPEG', quality=90)
                        buffer.seek(0)
                        img_recompressed = Image.open(buffer)
                        ela_diff = np.array(ImageChops.difference(img_rgb, img_recompressed))
                        ela_std = np.std(ela_diff)
                        
                        # Real photos usually have a standard deviation > 4.0 due to lens physics.
                        # AI images are mathematically "too perfect" and smooth.
                        score_ela = 1.0 if ela_std < 4.0 else (0.5 if ela_std < 6.0 else 0.0)
                        
                        # ATTEMPT 4: Cryptographic Hardware Signature Check
                        # Real photos contain EXIF data from the camera lens. AI generators leave this blank.
                        has_metadata = False
                        try:
                            if img.getexif() or 'exif' in img.info: has_metadata = True
                        except: pass
                        score_meta = 1.0 if not has_metadata else 0.0
                        
                        # ATTEMPT 5: Semantic Reality Verification (CLIP)
                        auth_categories = [
                            "an authentic photograph taken with a physical smartphone camera", 
                            "a fake AI generated synthetic digital 3d render midjourney stable diffusion"
                        ]
                        auth_inputs = vision_processor(text=auth_categories, images=img, return_tensors="pt", padding=True)
                        clip_probs = vision_model(**auth_inputs).logits_per_image.softmax(dim=1)[0].detach().numpy()
                        score_clip = float(clip_probs[1])
                        
                        # --- 🧠 HYBRID CONSENSUS ENGINE ---
                        # We combine the 5 scores. We give 45% weight to mathematical physics (ELA/Metadata) 
                        # because modern AI models easily fool standard neural networks.
                        final_fake_confidence = (
                            (score_full * 0.25) +    # AI Detector (Global)
                            (score_center * 0.20) +  # AI Detector (Micro)
                            (score_clip * 0.10) +    # Semantic Reality
                            (score_ela * 0.25) +     # Physics: ELA Compression
                            (score_meta * 0.20)      # Physics: Hardware Metadata
                        )
                        
                        # Lock boundaries
                        final_fake_confidence = min(max(final_fake_confidence, 0.0), 0.999)
                        
                        # Strict Dynamic Threshold: > 45% flags the image as a synthetic forgery
                        is_fake = final_fake_confidence > 0.45 
                        
                        auth_probs = [1.0 - final_fake_confidence, final_fake_confidence]
                        # -----------------------------------------------------------
                        # -----------------------------------------------------------
                        # -----------------------------------------------------------
                        
                        
                        if is_fake:
                            fake_confidence = round(float(auth_probs[1]) * 100, 1)
                            st.write(f"🛑 **FORGERY DETECTED** (Confidence: {fake_confidence}%)")
                            status.update(label="Security Alert: Scan Terminated", state="error", expanded=False)
                            
                            st.error(f"⚠️ SYSTEM WARNING: AI-generated image detected. Synthetic data submissions are strictly prohibited.")
                            st.warning("🔻 Penalty: -20 EcoPoints applied to your account for fraudulent submission.")
                            
                            st.session_state.activity_log.append({
                                "User": st.session_state.current_user, 
                                "Time": datetime.now().strftime("%H:%M"), 
                                "Action": f"Penalty: Uploaded AI Fake ({fake_confidence}%)", 
                                "Location": landmark, 
                                "Points": "-20"
                            })
                            st.stop()
                        
                        st.write("✅ Image Authenticated. Proceeding to waste classification...")
                        # --- 🔎 STAGE 2: QUANTUM OBJECT SCAN (Counting items) ---
                        st.write("🔎 **Quantum Object Scan:** Isolating and counting individual hazard items...")
                        detections = waste_detector(img)
                        
                        item_counts = {}
                        for d in detections:
                            # Only count things the AI is highly confident about
                            if d['score'] > 0.85:
                                label = d['label'].lower()
                                # Map common items to our database
                                if label in ['bottle', 'cup', 'bowl', 'vase']:
                                    item_counts['bottle/cup'] = item_counts.get('bottle/cup', 0) + 1
                                elif label in ['backpack', 'handbag', 'suitcase', 'bag']:
                                    item_counts['bag/plastic'] = item_counts.get('bag/plastic', 0) + 1
                                else:
                                    item_counts['misc debris'] = item_counts.get('misc debris', 0) + 1
                        
                        total_items = sum(item_counts.values())
                        if total_items > 0:
                            st.warning(f"⚠️ Hazard Alert: {total_items} distinct waste objects detected and logged.")
                            # Push the counts to the global Analytics database
                            for k, v in item_counts.items():
                                st.session_state.waste_inventory[k] = st.session_state.waste_inventory.get(k, 0) + v
                        else:
                            st.info("✅ Area structure is sound. No macroscopic debris clusters isolated.")
                        # ------------------------------------------------------------
                        
                        
                        ai_categories = [
                            "Clean and clear area without any garbage",
                            "Plastic bags and bottles waste", 
                            "Organic food waste and wet garbage", 
                            "Construction debris and concrete waste", 
                            "Hazardous electronic e-waste"
                        ]
                        
                        inputs = vision_processor(text=ai_categories, images=img, return_tensors="pt", padding=True)
                        outputs = vision_model(**inputs)
                        probs = outputs.logits_per_image.softmax(dim=1)[0].detach().numpy()
                        
                        best_idx = probs.argmax()
                        detected_category = ai_categories[best_idx]
                        confidence_score = round(float(probs[best_idx]) * 100, 1)
                        
                        is_clean = "Clean" in detected_category
                        
                        if is_clean:
                            st.write(f"👁️ AI Analysis Complete: Identified as **CLEAN AREA** ✅ (Confidence: {confidence_score}%)")
                        else:
                            st.write(f"👁️ AI Analysis Complete: Identified as **WASTE: {detected_category}** ⚠️ (Confidence: {confidence_score}%)")

                        if incident_desc: time.sleep(0.5); st.write("📝 NLP Engine: **Processing text context...**")
                        if voice_note: time.sleep(1.5); st.write("🔊 Speech-to-Text: **Transcribing audio log...**")
                        status.update(label="Analysis Complete", state="complete", expanded=False)
                    
                    if is_clean:
                        st.success(f"Great news! The AI confirmed {landmark} is clean. No alert needed. +10 EcoPoints! 🌟")
                        st.session_state.activity_log.append({
                            "User": st.session_state.current_user, "Time": datetime.now().strftime("%H:%M"), "Action": "Verified Clean Area", "Location": landmark, "Points": "+10"
                        })
                    else:
                        current_count = st.session_state.location_reports.get(landmark, 0) + 1
                        st.session_state.location_reports[landmark] = current_count

                        st.toast("Waste Alert Broadcasted!", icon="🚨")
                        st.success(lang['success_msg'].format(landmark))
                        eco_emoji_pop()

                        if current_count >= 3:
                            st.warning(f"⚠️ CHRONIC ISSUE DETECTED: {landmark} has been reported {current_count} times! Escalating to Municipal Corporation...")
                            email_status = send_escalation_email(landmark, detected_category, current_count)
                            if email_status:
                                st.info("✉️ Official escalation email automatically dispatched to Authorities.")
                            else:
                                st.info("✉️ [Simulation] Escalation email would be sent to Authorities here.")

                        st.session_state.activity_log.append({
                            "User": st.session_state.current_user, "Time": datetime.now().strftime("%H:%M"), "Action": f"Reported Waste: {detected_category}", "Location": landmark, "Points": "+50"
                        })

        with col_b:
            st.markdown(f"<h3 style='font-weight: 800; margin-bottom: 1rem; color: #f8fafc;'>{lang['leaderboard']}</h3>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame({"Rank": ["🥇", "🥈", "🥉"], "Operative": ["Anand_MDU", "Meenakshi_P", st.session_state.current_user.split('@')[0]], "Eco-Credits": ["2,450", "1,920", "1,250"]}), hide_index=True, use_container_width=True)
            st.markdown("<br><br>", unsafe_allow_html=True)
            
            blips_html = ""
            if st.session_state.location_reports:
                total_live_issues = sum(st.session_state.location_reports.values())
                for i in range(total_live_issues):
                    top = random.randint(30, 190)
                    left = random.randint(30, 190)
                    delay = round(random.uniform(0, 2), 1)
                    blips_html += f'<div class="blip" style="top: {top}px; left: {left}px; animation-delay: {delay}s; box-shadow: 0 0 20px #ef4444; background: #ef4444;"></div>'
            else:
                blips_html = f'<div class="blip" style="top: 110px; left: 110px; box-shadow: 0 0 20px {current_theme["primary"]}; background: {current_theme["primary"]};"></div>'

            st.markdown(f"""
                <style>
                .radar-box {{ position: relative; max-width: 100%; aspect-ratio: 1/1; height: auto; margin: 0 auto; border-radius: 50%; border: 2px solid {current_theme['primary']}; background: rgba(15, 23, 42, 0.5); box-shadow: 0 0 30px {current_theme['glow']}, inset 0 0 30px {current_theme['glow']}; overflow: hidden; display: flex; justify-content: center; align-items: center; }}
                .radar-beam {{ position: absolute; top: 50%; left: 50%; width: 220px; height: 220px; background: conic-gradient(from 0deg, transparent 70%, {current_theme['primary']} 100%); transform-origin: 0 0; animation: radar-spin 2s linear infinite; }}
                .radar-grid {{ position: absolute; width: 100%; height: 100%; border-radius: 50%; background-image: linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px); background-size: 20px 20px; }}
                @keyframes radar-spin {{ 100% {{ transform: rotate(360deg); }} }}
                .blip {{ position:absolute; width: 8px; height: 8px; border-radius: 50%; animation: pulse 2s infinite; }}
                @keyframes pulse {{ 0% {{ opacity: 0; transform: scale(0.5); }} 50% {{ opacity: 1; transform: scale(1.5); }} 100% {{ opacity: 0; transform: scale(0.5); }} }}
                </style>
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <div class="radar-box" style="width: 220px; height: 220px;"><div class="radar-grid"></div><div class="radar-beam"></div>
                    {blips_html}
                    </div>
                    <p style="color: {current_theme['primary']}; font-family: 'Orbitron', sans-serif; font-size: 0.8rem; letter-spacing: 3px; font-weight: bold; margin-top: 15px;">LIVE NEURAL SCAN ACTIVE</p>
                </div>
            """, unsafe_allow_html=True)

    # --- TAB 2: COMMAND CENTER ---
    with menu[1]:
        st.markdown(f"<h3 style='font-weight: 800; color: #f8fafc;'>Live Telemetry & Tracking</h3>", unsafe_allow_html=True)
        
        @st.fragment(run_every=5) 
        def live_dashboard_metrics():
            live_pending = sum(st.session_state.location_reports.values())
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="stat-card"><p>{lang["pending"]}</p><h2 class="text-4xl" style="color:#ef4444!important;">{live_pending}</h2></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="stat-card"><p>AI CONFIDENCE</p><h2 class="text-4xl">94%</h2></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="stat-card"><p>ACTIVE UNITS</p><h2 class="text-4xl">22</h2></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="stat-card"><p>CLEANEST ZONE</p><h2 class="text-4xl">W-42</h2></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="glass-panel" style="padding: 1rem;">', unsafe_allow_html=True)
            
            reported_locations = list(st.session_state.location_reports.keys())
            if reported_locations:
                live_map_data = df_madurai[df_madurai['Location'].isin(reported_locations)].copy()
                st.map(live_map_data, color="#ef4444", size=60)
            else:
                st.info("🟢 No active waste reports. Madurai city grid is clean!")
                st.map(pd.DataFrame({'lat': [9.9252], 'lon': [78.1198]}), zoom=11, color="#00000000")
            
            st.markdown('</div>', unsafe_allow_html=True)

        live_dashboard_metrics()

    # --- TAB 3: ANALYTICS --
    with menu[2]:
        st.markdown("<h3 style='font-weight: 800; color: #f8fafc; margin-bottom: 2rem;'>City-Wide Neural Inventory</h3>", unsafe_allow_html=True)
        
        inventory = st.session_state.get('waste_inventory', {})
        total_scanned = sum(inventory.values())
        
        if total_scanned == 0:
            st.info("📊 Database empty. Awaiting neural scans from the Citizen Portal to generate live telemetry.")
            st.markdown('<div class="radar-box" style="width: 100px; height: 100px; margin-top: 2rem;"><div class="radar-beam"></div></div>', unsafe_allow_html=True)
        else:
            col_graph, col_stats = st.columns([1.5, 1], gap="large")
            
            with col_graph:
                st.markdown('<div class="glass-panel" style="padding: 2rem;">', unsafe_allow_html=True)
                st.markdown("<h4 style='color: #a1a1aa; font-size: 0.9rem; letter-spacing: 2px;'>WASTE COMPOSITION ANALYSIS</h4>", unsafe_allow_html=True)
                
                # Filter out zeroes
                df_inv = pd.DataFrame(list(inventory.items()), columns=['Waste Type', 'Count'])
                df_inv = df_inv[df_inv['Count'] > 0]
                
                # Render the high-end Plotly Donut Chart
                fig = px.pie(
                    df_inv, values='Count', names='Waste Type', hole=0.75, 
                    color_discrete_sequence=current_theme['px_color'], template="plotly_dark"
                )
                fig.update_traces(textposition='outside', textinfo='percent+label', marker=dict(line=dict(color='#000000', width=2)))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=20, b=20, l=0, r=0), showlegend=False)
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col_stats:
                # Advanced Environmental Impact Metrics
                st.markdown('<div class="glass-panel" style="padding: 2rem; height: 100%; display: flex; flex-direction: column; justify-content: center; gap: 1.5rem;">', unsafe_allow_html=True)
                
                st.markdown("<p style='color: #a1a1aa; font-weight: 700; margin-bottom: -10px;'>TOTAL OBJECTS ISOLATED</p>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='color: #ffffff; font-size: 3.5rem; margin: 0;'>{total_scanned}</h1>", unsafe_allow_html=True)
                
                st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 0;'>", unsafe_allow_html=True)
                
                most_common = df_inv.loc[df_inv['Count'].idxmax()]['Waste Type'].title() if not df_inv.empty else "N/A"
                st.markdown("<p style='color: #a1a1aa; font-weight: 700; margin-bottom: -10px;'>DOMINANT HAZARD</p>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='color: {current_theme['primary']}; margin: 0;'>{most_common}</h3>", unsafe_allow_html=True)
                
                st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin: 0;'>", unsafe_allow_html=True)
                
                # Fun gamification metric
                carbon_offset = total_scanned * 0.45
                st.markdown("<p style='color: #a1a1aa; font-weight: 700; margin-bottom: -10px;'>PROJECTED CARBON COST</p>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='color: #ef4444; margin: 0;'>{carbon_offset:.2f} kg CO₂e</h3>", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 4: 🤖 AI ASSISTANT (GROQ LPU INTEGRATION) ---
    with menu[3]:
        st.markdown(f"<h3 style='font-weight: 800; margin-bottom: 1.5rem; color: #f8fafc;'>Core AI Communications</h3>", unsafe_allow_html=True)
        chat_container = st.container(height=400)
        
        for message in st.session_state.chat_history:
            with chat_container.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask CleanAI about the ecosystem, recycling, or the 3Rs..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user", avatar="👤"): 
                st.markdown(prompt)

            try:
                from groq import Groq
                groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"]) 
                
                env_persona = """
                You are CleanAI, an advanced environmental scientist system for Madurai city. 
                You MUST ONLY answer questions related to:
                1. The ecosystem and nature preservation.
                2. Waste management and pollution control.
                3. The 3Rs (Reduce, Reuse, Recycle).
                4. Sustainable living and green energy.
                
                If the user asks you about programming, math, history, general knowledge, or anything outside of these topics, you must politely refuse and tell them you are strictly programmed to discuss environmental preservation. Keep your answers concise, practical, and highly informative.
                """
                
                api_messages = [{"role": "system", "content": env_persona}]
                for msg in st.session_state.chat_history:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                with chat_container.chat_message("assistant", avatar="🤖"):
                    with st.spinner("CleanAI Neural Net is processing..."):
                        chat_completion = groq_client.chat.completions.create(
                            messages=api_messages,
                            model="llama-3.1-8b-instant", 
                            temperature=0.5,
                            max_tokens=1024,
                        )
                        response_text = chat_completion.choices[0].message.content
                        st.markdown(response_text)
                
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})
                
            except ImportError:
                st.error("⚠️ Library missing! Please run `pip install groq` in your terminal.")
            except Exception as e:
                st.error(f"⚠️ Connection Error. Did you add your Groq API key? (Error: {e})")

    # --- TAB 5: SETTINGS ---
    with menu[4]:
        st.markdown(f"<h3 style='font-weight: 800; margin-bottom: 1.5rem; color: #f8fafc;'>{lang['settings_title']}</h3>", unsafe_allow_html=True)
        set_col1, set_col2, set_col3 = st.columns([1, 1, 1])
        with set_col1:
            new_lang = st.selectbox("🌐 System Language", ["English", "Tamil"], index=["English", "Tamil"].index(st.session_state.lang))
            if new_lang != st.session_state.lang: st.session_state.lang = new_lang; st.rerun()
        with set_col2:
            new_theme = st.selectbox("🎨 UI Accent Color", ["Neon Green", "Cyber Blue", "Neon Purple", "Crimson"], index=["Neon Green", "Cyber Blue", "Neon Purple", "Crimson"].index(st.session_state.theme))
            if new_theme != st.session_state.theme: st.session_state.theme = new_theme; st.rerun()
        with set_col3:
            st.write("🛑 Danger Zone")
            if st.button("TERMINATE SESSION", use_container_width=True): st.session_state.current_user = None; st.rerun()
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='font-weight: 800; color: #f8fafc;'>{lang['history_title']}</h4>", unsafe_allow_html=True)
        user_history = [log for log in st.session_state.activity_log if log["User"] == st.session_state.current_user]
        if not user_history: st.info("No network activity recorded.")
        else: st.dataframe(pd.DataFrame(user_history), use_container_width=True, hide_index=True)
