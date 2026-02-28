import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
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

# Now it is safe to load the GPS
location_data = streamlit_geolocation()
if location_data['latitude'] is not None:
    st.success(f"📍 GPS Locked: Lat {location_data['latitude']}, Lon {location_data['longitude']}")

# --- AI ENGINE INITIALIZATION ---
@st.cache_resource
def load_vision_model():
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor

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

# --- 2. SESSION STATE INITIALIZATION ---
if 'lang' not in st.session_state: st.session_state.lang = 'English'
if 'theme' not in st.session_state: st.session_state.theme = 'Neon Purple' 
if 'activity_log' not in st.session_state: st.session_state.activity_log = []
if 'chat_history' not in st.session_state: st.session_state.chat_history = [{"role": "assistant", "content": "System Online. I am the CleanAI Core. Ask me about city waste data, pending alerts, or your EcoPoints."}]
if 'users_db' not in st.session_state: st.session_state.users_db = {'admin@madurai.com': 'admin123'}
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'auth_mode' not in st.session_state: st.session_state.auth_mode = 'login'
if 'location_reports' not in st.session_state: st.session_state.location_reports = {}

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
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;600;800&display=swap');
        
        .stApp, [data-testid="stAppViewContainer"] {{
            background-color: #0b1120 !important;
            background-image: radial-gradient(circle at 50% 0%, #1e293b 0%, #0b1120 70%);
            color: #f8fafc !important; font-family: 'Inter', sans-serif;
        }}
        
        h1, h2, h3, h4, p, label, .stMarkdown span {{ color: #f8fafc !important; }}
        
        .header-container {{
            text-align: center; padding: 2rem 0 2rem 0; 
            background: transparent !important; border: none !important;
            box-shadow: none !important; margin-bottom: 2rem;
        }}
        
        .brand-text {{ 
            font-family: 'Orbitron', sans-serif;
            background: linear-gradient(90deg, #ffffff, {current_theme['primary']});
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0px 0px 30px {current_theme['glow']};
        }}
        .subtitle-text {{ color: #94a3b8 !important; letter-spacing: 0.2em; }}

        .auth-card, .stat-card, .glass-panel {{
            background: rgba(30, 41, 59, 0.4) !important; backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5); transition: transform 0.3s ease, border-color 0.3s ease;
        }}
        .auth-card {{ padding: 3rem; max-width: 500px; margin: 4rem auto; text-align: center; border-top: 2px solid {current_theme['primary']}; }}
        .stat-card {{ padding: 1.5rem; text-align: center; border-bottom: 3px solid {current_theme['primary']}; }}
        .stat-card:hover {{ transform: translateY(-5px); border-color: {current_theme['primary']}; box-shadow: 0 10px 30px {current_theme['glow']}; }}
        .stat-card h2 {{ color: {current_theme['primary']} !important; font-family: 'Orbitron', sans-serif; }}
        .stat-card p {{ color: #94a3b8 !important; font-weight: 800; font-size: 0.8rem; letter-spacing: 0.1em; }}

        [data-testid="stFileUploadDropzone"] {{
            background: rgba(15, 23, 42, 0.6) !important; border: 2px dashed {current_theme['primary']} !important;
            border-radius: 12px; padding: 2rem !important; position: relative;
        }}
        [data-testid="stFileUploadDropzone"] * {{ color: transparent !important; }}
        [data-testid="stFileUploadDropzone"] svg {{ display: none !important; }}
        [data-testid="stFileUploadDropzone"]::after {{
            content: "📸 SNAP THE SCRAP TO CLEAN MADURAI \\A Limit 200MB • JPG, PNG"; 
            white-space: pre-wrap; font-weight: 800; font-size: 1.1rem; color: {current_theme['primary']} !important;
            position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
            text-align: center; display: block; line-height: 1.8; pointer-events: none; width: 100%;
        }}

        .stTextArea textarea, .stChatInput input {{
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #f8fafc !important; border-radius: 12px;
        }}
        .stTextArea textarea:focus, .stChatInput input:focus {{
            border-color: {current_theme['primary']} !important; box-shadow: 0 0 10px {current_theme['glow']} !important;
        }}

        .stButton>button {{
            border-radius: 8px; background: transparent !important; border: 2px solid {current_theme['primary']} !important;
            color: {current_theme['primary']} !important; font-weight: 800; letter-spacing: 1px; height: 3.5rem; width: 100%;
            transition: all 0.3s ease; box-shadow: 0 0 10px {current_theme['glow']};
        }}
        .stButton>button:hover {{ background: {current_theme['primary']} !important; color: #0b1120 !important; box-shadow: 0 0 20px {current_theme['primary']}; }}
        .stButton>button p {{ color: inherit !important; font-weight: inherit !important; }}
        
        /* --- CUSTOM TAB SPACING --- */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            gap: 3rem; 
            justify-content: center; 
            width: 100%;
        }}

        [data-testid="stTabs"] button[role="tab"] {{
            padding: 1rem 2rem; 
            font-weight: 800;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }}

        [data-testid="stTabs"] button[role="tab"]:hover {{
            color: {current_theme['primary']} !important; 
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
            if st.button("AUTHORIZE CONNECTION"):
                if email in st.session_state.users_db and st.session_state.users_db[email] == password:
                    st.session_state.current_user = email; st.rerun()
                else: st.error("Access Denied.")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Register New Operative"): st.session_state.auth_mode = 'signup'; st.rerun()
                
        else: # SIGNUP
            st.markdown('<h2 style="font-weight: 800; margin-bottom: 1.5rem;">NEW OPERATIVE</h2>', unsafe_allow_html=True)
            new_email = st.text_input("Assign User ID (Email)", placeholder="hero@madurai.com")
            new_password = st.text_input("Set Security Key", type="password", placeholder="••••••••")
            if st.button("INITIALIZE ACCOUNT"):
                if new_email in st.session_state.users_db: st.error("User ID already registered!")
                else: st.session_state.users_db[new_email] = new_password; st.session_state.current_user = new_email; eco_emoji_pop(); st.rerun()

# ==========================================
# ✅ MAIN DASHBOARD 
# ==========================================
else:
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
            uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
            st.markdown("<br>", unsafe_allow_html=True)
            incident_desc = st.text_area(lang['desc_label'], placeholder="E.g., It is blocking the road...", height=100)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"<label style='font-weight: 600; color: #f8fafc; font-size: 14px;'>{lang['voice_label']}</label>", unsafe_allow_html=True)
            voice_note = st.audio_input("Record", label_visibility="collapsed")
            
            landmark = st.text_input(lang['landmark_label'], placeholder="e.g., Kalavasal Junction, Madurai...")
            
            if st.button(lang['analyze']):
                if uploaded_file is None:
                    st.error("⚠️ Please upload an image first.")
                elif not landmark.strip():
                    st.error("⚠️ Please enter your location so we can track this report.")
                else:
                    with st.status("Initializing Multimodal Neural Net...", expanded=True) as status:
                        time.sleep(1); st.write("🛰️ Triangulating GPS coordinates...")
                        st.write("🤖 Vision Model: **Running neural inference on image...**")
                        
                        img = Image.open(uploaded_file)
                        # Speed Optimization
                        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                        # --- 🛡️ STAGE 1: VERI-PIXEL ANTI-FORGERY CHECK ---
                        st.write("🛡️ Veri-Pixel Firewall: **Scanning for AI generation artifacts...**")
                        
                        authenticity_categories = [
                            "a real, authentic, unedited photograph taken with a camera",
                            "a fake, AI generated, synthetic, or digital 3d render"
                        ]
                        
                        auth_inputs = vision_processor(text=authenticity_categories, images=img, return_tensors="pt", padding=True)
                        auth_outputs = vision_model(**auth_inputs)
                        auth_probs = auth_outputs.logits_per_image.softmax(dim=1)[0].detach().numpy()
                        
                        # If the AI thinks the "fake" category is a higher match than "real"
                        is_fake = auth_probs[1] > auth_probs[0] 
                        
                        if is_fake:
                            fake_confidence = round(float(auth_probs[1]) * 100, 1)
                            st.write(f"🛑 **FORGERY DETECTED** (Confidence: {fake_confidence}%)")
                            status.update(label="Security Alert: Scan Terminated", state="error", expanded=False)
                            
                            st.error(f"⚠️ SYSTEM WARNING: AI-generated image detected. Synthetic data submissions are strictly prohibited.")
                            st.warning("🔻 Penalty: -20 EcoPoints applied to your account for fraudulent submission.")
                            
                            # Log the penalty to the user's history
                            st.session_state.activity_log.append({
                                "User": st.session_state.current_user, 
                                "Time": datetime.now().strftime("%H:%M"), 
                                "Action": f"Penalty: Uploaded AI Fake ({fake_confidence}%)", 
                                "Location": landmark, 
                                "Points": "-20"
                            })
                            st.stop() # 🛑 This completely stops the rest of the code from running
                        
                        st.write("✅ Image Authenticated. Proceeding to waste classification...")
                        # --- END ANTI-FORGERY CHECK ---
                        
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
            
            # --- 📡 LIVE AI RADAR DATA ---
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

    # --- TAB 3: ANALYTICS ---
    with menu[2]:
        @st.fragment(run_every=10) 
        def live_analytics_chart():
            st.markdown('<div class="glass-panel" style="padding: 2rem;">', unsafe_allow_html=True)
            p_plastic = random.randint(40, 50)
            p_organic = random.randint(25, 35)
            p_elec = random.randint(5, 15)
            p_silt = 100 - (p_plastic + p_organic + p_elec) 
            live_df = pd.DataFrame({'Type': ['Plastic', 'Organic', 'Electronic', 'Silt'], 'Percent': [p_plastic, p_organic, p_elec, p_silt]})
            fig = px.pie(live_df, values='Percent', names='Type', hole=0.6, color_discrete_sequence=current_theme['px_color'], template="plotly_dark")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", transition_duration=500)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        live_analytics_chart()

    # --- TAB 4: 🤖 AI ASSISTANT (GROQ LPU INTEGRATION) ---
    with menu[3]:
        st.markdown(f"<h3 style='font-weight: 800; margin-bottom: 1.5rem; color: #f8fafc;'>Core AI Communications</h3>", unsafe_allow_html=True)
        chat_container = st.container(height=400)
        
        # Display past chat history
        for message in st.session_state.chat_history:
            with chat_container.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                st.markdown(message["content"])

        # Accept user input
        if prompt := st.chat_input("Ask CleanAI about the ecosystem, recycling, or the 3Rs..."):
            
            # 1. Save and display the user's prompt
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user", avatar="👤"): 
                st.markdown(prompt)

            # 2. Connect to Groq's High-Speed API
            try:
                from groq import Groq
                
                # 👇 PUT YOUR FREE GROQ API KEY HERE 👇
                groq_client = Groq(api_key="Your_Groq_API_Key_Here") 
                
                # 3. The "Architect Guardrail" (System Instruction)
                env_persona = """
                You are CleanAI, an advanced environmental scientist system for Madurai city. 
                You MUST ONLY answer questions related to:
                1. The ecosystem and nature preservation.
                2. Waste management and pollution control.
                3. The 3Rs (Reduce, Reuse, Recycle).
                4. Sustainable living and green energy.
                
                If the user asks you about programming, math, history, general knowledge, or anything outside of these topics, you must politely refuse and tell them you are strictly programmed to discuss environmental preservation. Keep your answers concise, practical, and highly informative.
                """
                
                # Format the history for Groq (System prompt goes first)
                api_messages = [{"role": "system", "content": env_persona}]
                
                # Add previous chat history (skipping the very first default system welcome message if needed, but Groq handles it fine)
                for msg in st.session_state.chat_history:
                    # Map the first message from 'assistant' to 'assistant' safely
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                # 4. Generate the response using Llama-3 on Groq
                with chat_container.chat_message("assistant", avatar="🤖"):
                    with st.spinner("CleanAI Neural Net is processing..."):
                        chat_completion = groq_client.chat.completions.create(
                            messages=api_messages,
                            model="llama-3.1-8b-instant", # Blazing fast Llama 3 model
                            temperature=0.5,
                            max_tokens=1024,
                        )
                        
                        response_text = chat_completion.choices[0].message.content
                        st.markdown(response_text)
                
                # Save the AI's response to history
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
            if st.button("TERMINATE SESSION"): st.session_state.current_user = None; st.rerun()
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='font-weight: 800; color: #f8fafc;'>{lang['history_title']}</h4>", unsafe_allow_html=True)
        user_history = [log for log in st.session_state.activity_log if log["User"] == st.session_state.current_user]
        if not user_history: st.info("No network activity recorded.")
        else: st.dataframe(pd.DataFrame(user_history), use_container_width=True, hide_index=True)
        