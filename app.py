"""
Madurai CleanAI — Enterprise Streamlit Application
---------------------------------------------------
UI/architecture refactor of the supplied application.

Important:
- The existing AI algorithms, model choices, weights, thresholds, and scoring
  formulas are intentionally preserved.
- Presentation-only "cyber" UI, game/radar animations, and unnecessary effects
  have been removed.
- Secrets are read from Streamlit Secrets instead of hard-coded credentials.
- Expensive AI resources are cached and loaded only when required.
- Input validation, error handling, state handling, and reusable UI helpers
  have been improved.
"""

from __future__ import annotations

import io
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from PIL import Image, ImageChops
from streamlit_geolocation import streamlit_geolocation
from transformers import CLIPModel, CLIPProcessor, pipeline


# ============================================================
# 1. APPLICATION CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Madurai CleanAI",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_NAME = "Madurai CleanAI"
DEFAULT_CITY = "Madurai"
DEFAULT_LAT = 9.9252
DEFAULT_LON = 78.1198

# Normal enterprise palette: neutral surfaces + restrained green/blue accents.
COLORS = {
    "primary": "#198754",
    "primary_dark": "#146c43",
    "secondary": "#2563EB",
    "success": "#198754",
    "warning": "#D97706",
    "danger": "#DC3545",
    "text": "#1F2937",
    "muted": "#6B7280",
    "border": "#E5E7EB",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "page": "#F4F7F6",
}


# ============================================================
# 2. RESOURCE / CONFIG HELPERS
# ============================================================

def get_secret(name: str, default: str | None = None) -> str | None:
    """Read a Streamlit secret safely."""
    try:
        value = st.secrets.get(name, default)
        if value is None:
            return default
        value = str(value).strip()
        return value or default
    except Exception:
        return default


@st.cache_resource(show_spinner=False)
def load_deepfake_detector():
    """Existing image-authenticity model; algorithm unchanged."""
    return pipeline(
        "image-classification",
        model="umm-maybe/AI-image-detector",
    )


@st.cache_resource(show_spinner=False)
def load_vision_model():
    """Existing CLIP model; algorithm unchanged."""
    vision_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    vision_processor = CLIPProcessor.from_pretrained(
        "openai/clip-vit-base-patch32"
    )
    return vision_model, vision_processor


@st.cache_resource(show_spinner=False)
def load_object_detector():
    """Existing DETR object detector; algorithm unchanged."""
    return pipeline(
        "object-detection",
        model="facebook/detr-resnet-50",
    )


def get_ai_resources():
    """
    Load the three existing AI resources together only when the user actually
    starts an image analysis.
    """
    with st.spinner("Loading AI analysis models for the first scan..."):
        ai_detector = load_deepfake_detector()
        vision_model, vision_processor = load_vision_model()
        waste_detector = load_object_detector()
    return ai_detector, vision_model, vision_processor, waste_detector


# ============================================================
# 3. SESSION STATE
# ============================================================

def initialize_session_state() -> None:
    defaults = {
        "lang": "English",
        "activity_log": [],
        "chat_history": [
            {
                "role": "assistant",
                "content": (
                    "Welcome to Madurai CleanAI. I can help with waste "
                    "management, recycling, pollution control, and sustainable "
                    "living."
                ),
            }
        ],
        # Demo/local authentication data retained from the original project.
        # For a real deployment, replace this with Supabase/Auth/SSO.
        "users_db": {"admin@madurai.com": "admin123"},
        "current_user": None,
        "auth_mode": "login",
        "location_reports": {},
        "waste_inventory": {
            "bottle": 0,
            "cup": 0,
            "bag": 0,
            "debris": 0,
        },
        "sos_active": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_session_state()


# ============================================================
# 4. LANGUAGE CONTENT
# ============================================================

TRANSLATIONS = {
    "English": {
        "title": "Madurai CleanAI",
        "subtitle": "AI-assisted municipal waste reporting and analysis",
        "tabs": [
            "Citizen Portal",
            "Command Center",
            "Analytics",
            "AI Assistant",
            "Settings",
        ],
        "report": "Report New Incident",
        "analyze": "Analyze Report",
        "leaderboard": "Community Activity",
        "pending": "Active Reports",
        "settings_title": "System Preferences",
        "history_title": "Activity History",
        "landmark_label": "Location / Landmark",
        "success_msg": "{} has been reported successfully.",
        "desc_label": "Description (Optional)",
        "voice_label": "Voice Note (Optional)",
    },
    "Tamil": {
        "title": "மதுரை CleanAI",
        "subtitle": "AI உதவியுடன் கழிவு மேலாண்மை மற்றும் புகார் பதிவு",
        "tabs": [
            "குடிமக்கள் தளம்",
            "கட்டுப்பாட்டு மையம்",
            "பகுப்பாய்வு",
            "AI உதவியாளர்",
            "அமைப்புகள்",
        ],
        "report": "புதிய புகாரை பதிவு செய்",
        "analyze": "புகாரை பகுப்பாய்வு செய்",
        "leaderboard": "சமூக செயல்பாடு",
        "pending": "செயலில் உள்ள புகார்கள்",
        "settings_title": "அமைப்புகள்",
        "history_title": "செயல்பாட்டு வரலாறு",
        "landmark_label": "இடம் / அடையாளம்",
        "success_msg": "{} வெற்றிகரமாக பதிவு செய்யப்பட்டது.",
        "desc_label": "விவரம் (விருப்பம்)",
        "voice_label": "குரல் பதிவு (விருப்பம்)",
    },
}

lang = TRANSLATIONS[st.session_state.lang]


# ============================================================
# 5. ENTERPRISE UI
# ============================================================

st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background: {COLORS["page"]};
            color: {COLORS["text"]};
        }}

        [data-testid="stHeader"] {{
            background: rgba(255,255,255,0.96);
            border-bottom: 1px solid {COLORS["border"]};
        }}

        .app-header {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 14px;
            padding: 24px 28px;
            margin-bottom: 22px;
        }}

        .app-title {{
            color: {COLORS["text"]};
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.02em;
        }}

        .app-subtitle {{
            color: {COLORS["muted"]};
            font-size: 0.95rem;
            margin: 7px 0 0 0;
        }}

        .section-title {{
            color: {COLORS["text"]};
            font-size: 1.25rem;
            font-weight: 700;
            margin: 0 0 14px 0;
        }}

        .card {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 14px;
            padding: 20px;
            margin-bottom: 16px;
        }}

        .stat-card {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 12px;
            padding: 18px;
            min-height: 105px;
        }}

        .stat-label {{
            color: {COLORS["muted"]};
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .stat-value {{
            color: {COLORS["text"]};
            font-size: 1.9rem;
            font-weight: 700;
            margin-top: 7px;
        }}

        .status-ok {{
            background: #ECFDF3;
            color: #166534;
            border: 1px solid #BBF7D0;
            border-radius: 9px;
            padding: 10px 12px;
            font-size: 0.9rem;
        }}

        .status-warning {{
            background: #FFF7ED;
            color: #9A3412;
            border: 1px solid #FED7AA;
            border-radius: 9px;
            padding: 10px 12px;
            font-size: 0.9rem;
        }}

        .status-danger {{
            background: #FEF2F2;
            color: #991B1B;
            border: 1px solid #FECACA;
            border-radius: 9px;
            padding: 10px 12px;
            font-size: 0.9rem;
        }}

        .login-wrap {{
            max-width: 480px;
            margin: 60px auto;
        }}

        .login-card {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        }}

        .brand-mark {{
            width: 52px;
            height: 52px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #E8F5EE;
            color: {COLORS["primary_dark"]};
            font-size: 1.55rem;
            margin-bottom: 14px;
        }}

        .small-muted {{
            color: {COLORS["muted"]};
            font-size: 0.82rem;
        }}

        .stButton > button {{
            border-radius: 8px;
            min-height: 2.65rem;
            font-weight: 600;
            border: 1px solid {COLORS["border"]};
        }}

        button[kind="primary"] {{
            background: {COLORS["primary"]} !important;
            border-color: {COLORS["primary"]} !important;
            color: white !important;
        }}

        button[kind="primary"]:hover {{
            background: {COLORS["primary_dark"]} !important;
            border-color: {COLORS["primary_dark"]} !important;
        }}

        .stTextInput input,
        .stTextArea textarea {{
            border-radius: 8px !important;
            border-color: #D1D5DB !important;
            background: white !important;
            color: {COLORS["text"]} !important;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            border: 1px dashed #CBD5E1;
            border-radius: 10px;
            background: #F8FAFC;
        }}

        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            gap: 4px;
            border-bottom: 1px solid {COLORS["border"]};
        }}

        [data-testid="stTabs"] button[role="tab"] {{
            color: {COLORS["muted"]};
            font-weight: 600;
        }}

        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
            color: {COLORS["primary_dark"]};
        }}

        [data-testid="stSidebar"] {{
            background: white;
            border-right: 1px solid {COLORS["border"]};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 6. EMAIL / ALERT SERVICES
# ============================================================

def send_email(subject: str, body: str) -> bool:
    """
    Centralized SMTP service.

    Required Streamlit secrets:
        SMTP_HOST
        SMTP_PORT
        SMTP_USERNAME
        SMTP_PASSWORD
        ALERT_RECEIVER_EMAIL
    """
    host = get_secret("SMTP_HOST", "smtp.gmail.com")
    port = int(get_secret("SMTP_PORT", "587") or "587")
    username = get_secret("SMTP_USERNAME")
    password = get_secret("SMTP_PASSWORD")
    receiver = get_secret("ALERT_RECEIVER_EMAIL")

    if not all([host, username, password, receiver]):
        return False

    message = MIMEMultipart()
    message["From"] = username
    message["To"] = receiver
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(message)
        return True
    except Exception:
        return False


def send_escalation_email(location: str, category: str, total_reports: int) -> bool:
    body = f"""
Madurai CleanAI Municipal Alert

A recurring waste issue has reached the configured escalation threshold.

Location: {location}
Waste category: {category}
Citizen reports: {total_reports}

Please review and assign the appropriate municipal cleaning unit.

This message was generated automatically by Madurai CleanAI.
"""
    return send_email(
        f"Recurring Waste Issue — {location}",
        body,
    )


def send_sos_email(location: str, user_query: str) -> bool:
    body = f"""
Madurai CleanAI Emergency Alert

Emergency assistance has been requested.

Last known location: {location}
User message: {user_query}

Please review this alert through the appropriate emergency response process.
"""
    return send_email(
        f"Emergency Assistance Request — {location}",
        body,
    )


# ============================================================
# 7. WEATHER / DISASTER CHECK
# ============================================================

def check_severe_weather(
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
) -> tuple[bool, str]:
    """
    Existing weather classification logic is preserved:
    weather IDs below 600 are treated as severe.
    """
    api_key = get_secret("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return False, "Weather service not configured"

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={api_key}"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        weather_id = data["weather"][0]["id"]
        weather_desc = data["weather"][0]["description"]

        # Existing algorithm — intentionally unchanged.
        if weather_id < 600:
            return True, weather_desc.title()

        return False, "Normal"

    except (requests.RequestException, KeyError, TypeError, ValueError):
        return False, "Weather service unavailable"


# ============================================================
# 8. COMMON DATA / UI HELPERS
# ============================================================

def add_activity(action: str, location: str, points: str) -> None:
    st.session_state.activity_log.append(
        {
            "User": st.session_state.current_user,
            "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Action": action,
            "Location": location,
            "Points": points,
        }
    )


def get_location_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Location": [
                "Meenakshi Amman Temple",
                "Mattuthavani",
                "Goripalayam",
                "Teppakulam",
                "Vaigai River",
                "Railway Station",
            ],
            "lat": [9.9195, 9.9515, 9.9264, 9.9125, 9.9320, 9.9160],
            "lon": [78.1193, 78.1510, 78.1298, 78.1450, 78.1300, 78.1100],
        }
    )


def render_header() -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <div style="display:flex; gap:16px; align-items:center;">
                <div class="brand-mark">♻️</div>
                <div>
                    <div class="app-title">{lang["title"]}</div>
                    <div class="app-subtitle">{lang["subtitle"]}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_card(label: str, value: Any) -> None:
    st.markdown(
        f"""
        <div class="stat-card">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 9. AUTHENTICATION
# ============================================================

def render_authentication() -> None:
    st.markdown(
        """
        <div class="login-wrap">
            <div class="login-card">
                <div class="brand-mark">♻️</div>
                <h1 style="margin:0; color:#1F2937; font-size:1.8rem;">
                    Madurai CleanAI
                </h1>
                <p class="small-muted">
                    Municipal waste reporting and AI-assisted analysis
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.session_state.auth_mode == "login":
            st.markdown(
                '<div class="card"><h3 style="margin-top:0;">Sign in</h3>',
                unsafe_allow_html=True,
            )

            email = st.text_input(
                "Email",
                placeholder="admin@madurai.com",
                key="login_email",
            )
            password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )

            if st.button(
                "Sign in",
                type="primary",
                use_container_width=True,
            ):
                if (
                    email in st.session_state.users_db
                    and st.session_state.users_db[email] == password
                ):
                    st.session_state.current_user = email
                    st.rerun()
                else:
                    st.error("Invalid email or password.")

            if st.button("Create local demo account", use_container_width=True):
                st.session_state.auth_mode = "signup"
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown(
                '<div class="card"><h3 style="margin-top:0;">Create account</h3>',
                unsafe_allow_html=True,
            )

            new_email = st.text_input(
                "Email",
                placeholder="user@example.com",
                key="signup_email",
            )
            new_password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="signup_confirm_password",
            )

            if st.button(
                "Create account",
                type="primary",
                use_container_width=True,
            ):
                if not new_email or "@" not in new_email:
                    st.error("Enter a valid email address.")
                elif len(new_password) < 8:
                    st.error("Password must contain at least 8 characters.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif new_email in st.session_state.users_db:
                    st.error("An account with this email already exists.")
                else:
                    st.session_state.users_db[new_email] = new_password
                    st.session_state.current_user = new_email
                    st.rerun()

            if st.button("Back to sign in", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# 10. SIDEBAR / EMERGENCY MODULE
# ============================================================

def render_sidebar() -> dict[str, Any] | None:
    location_data = None

    with st.sidebar:
        st.markdown("### Account")
        st.write(st.session_state.current_user)

        if st.button("Sign out", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.sos_active = False
            st.rerun()

        st.divider()

        st.markdown("### Emergency assistance")

        disaster_detected, condition = check_severe_weather()

        if disaster_detected:
            st.warning(f"Weather alert: {condition}")
            st.session_state.sos_active = True
        else:
            st.caption(f"Weather status: {condition}")

        if st.button(
            "Request emergency assistance",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.sos_active = True

        if st.session_state.get("sos_active", False):
            st.info(
                "Emergency channel is active. Record a short message and "
                "provide your location if available."
            )

            emergency_audio = st.audio_input(
                "Emergency voice message",
            )

            if emergency_audio:
                with st.spinner("Submitting emergency request..."):
                    transcribed_text = (
                        "User requires immediate medical/evacuation assistance."
                    )

                    current_loc = "Madurai"

                    success = send_sos_email(
                        current_loc,
                        transcribed_text,
                    )

                    if success:
                        st.success("Emergency request submitted.")
                    else:
                        st.warning(
                            "Emergency email service is not configured. "
                            "The request was not transmitted."
                        )

    return location_data


# ============================================================
# 11. IMAGE AUTHENTICATION ALGORITHM
# ============================================================

def run_image_authentication(
    img: Image.Image,
    ai_detector,
    vision_model,
    vision_processor,
) -> tuple[bool, float]:
    """
    Existing 5-layer image-authentication algorithm.

    The model calls, feature extraction, weights, threshold, and formula are
    intentionally unchanged.
    """
    img = img.convert("RGB")

    # ATTEMPT 1: Neural Global Scan
    res_full = ai_detector(img)
    score_full = next(
        (r["score"] for r in res_full if r["label"] == "artificial"),
        0.0,
    )

    # ATTEMPT 2: Neural Micro-Texture Scan
    w, h = img.size
    img_center = img.crop((w / 4, h / 4, 3 * w / 4, 3 * h / 4))
    res_center = ai_detector(img_center)
    score_center = next(
        (r["score"] for r in res_center if r["label"] == "artificial"),
        0.0,
    )

    # ATTEMPT 3: Mathematical Error Level Analysis (ELA)
    buffer = io.BytesIO()
    img_rgb = img.convert("RGB")
    img_rgb.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    img_recompressed = Image.open(buffer)

    ela_diff = np.array(
        ImageChops.difference(img_rgb, img_recompressed)
    )
    ela_std = np.std(ela_diff)

    # Existing thresholds — unchanged.
    score_ela = (
        1.0
        if ela_std < 4.0
        else (0.5 if ela_std < 6.0 else 0.0)
    )

    # ATTEMPT 4: Metadata check
    has_metadata = False
    try:
        if img.getexif() or "exif" in img.info:
            has_metadata = True
    except Exception:
        pass

    score_meta = 1.0 if not has_metadata else 0.0

    # ATTEMPT 5: CLIP semantic verification
    auth_categories = [
        "an authentic photograph taken with a physical smartphone camera",
        "a fake AI generated synthetic digital 3d render midjourney stable diffusion",
    ]

    auth_inputs = vision_processor(
        text=auth_categories,
        images=img,
        return_tensors="pt",
        padding=True,
    )

    clip_probs = (
        vision_model(**auth_inputs)
        .logits_per_image.softmax(dim=1)[0]
        .detach()
        .numpy()
    )
    score_clip = float(clip_probs[1])

    # EXISTING HYBRID CONSENSUS FORMULA — UNCHANGED.
    final_fake_confidence = (
        (score_full * 0.25)
        + (score_center * 0.20)
        + (score_clip * 0.10)
        + (score_ela * 0.25)
        + (score_meta * 0.20)
    )

    final_fake_confidence = min(
        max(final_fake_confidence, 0.0),
        0.999,
    )

    # EXISTING THRESHOLD — UNCHANGED.
    is_fake = final_fake_confidence > 0.45

    return is_fake, final_fake_confidence


# ============================================================
# 12. WASTE OBJECT DETECTION ALGORITHM
# ============================================================

def detect_waste_objects(img: Image.Image, waste_detector) -> dict[str, int]:
    """
    Existing DETR classification/counting logic.

    Confidence threshold and label mappings are unchanged.
    """
    detections = waste_detector(img)

    item_counts: dict[str, int] = {}

    for detection in detections:
        if detection["score"] > 0.85:
            label = detection["label"].lower()

            if label in ["bottle", "cup", "bowl", "vase"]:
                item_counts["bottle/cup"] = (
                    item_counts.get("bottle/cup", 0) + 1
                )
            elif label in [
                "backpack",
                "handbag",
                "suitcase",
                "bag",
            ]:
                item_counts["bag/plastic"] = (
                    item_counts.get("bag/plastic", 0) + 1
                )
            else:
                item_counts["misc debris"] = (
                    item_counts.get("misc debris", 0) + 1
                )

    return item_counts


# ============================================================
# 13. WASTE CLASSIFICATION ALGORITHM
# ============================================================

def classify_waste(
    img: Image.Image,
    vision_model,
    vision_processor,
) -> tuple[str, float]:
    """
    Existing CLIP waste classification logic; unchanged.
    """
    ai_categories = [
        "Clean and clear area without any garbage",
        "Plastic bags and bottles waste",
        "Organic food waste and wet garbage",
        "Construction debris and concrete waste",
        "Hazardous electronic e-waste",
    ]

    inputs = vision_processor(
        text=ai_categories,
        images=img,
        return_tensors="pt",
        padding=True,
    )

    outputs = vision_model(**inputs)
    probs = (
        outputs.logits_per_image.softmax(dim=1)[0]
        .detach()
        .numpy()
    )

    best_idx = probs.argmax()
    detected_category = ai_categories[best_idx]
    confidence_score = round(float(probs[best_idx]) * 100, 1)

    return detected_category, confidence_score


# ============================================================
# 14. CITIZEN PORTAL
# ============================================================

def render_citizen_portal(df_madurai: pd.DataFrame) -> None:
    col_a, col_b = st.columns([1.15, 0.85], gap="large")

    with col_a:
        st.markdown(
            f'<div class="section-title">{lang["report"]}</div>',
            unsafe_allow_html=True,
        )

        input_method = st.radio(
            "Image source",
            ["Upload Image", "Use Camera"],
            horizontal=True,
        )

        if input_method == "Upload Image":
            uploaded_file = st.file_uploader(
                "Upload a waste-site image",
                type=["jpg", "png", "jpeg"],
            )
        else:
            uploaded_file = st.camera_input(
                "Take a picture of the waste site"
            )

        incident_desc = st.text_area(
            lang["desc_label"],
            placeholder="Example: Waste is blocking the road.",
            height=100,
        )

        voice_note = st.audio_input(
            lang["voice_label"],
        )

        landmark = st.text_input(
            lang["landmark_label"],
            placeholder="Example: Kalavasal Junction, Madurai",
        )

        st.caption("Optional: use precise GPS coordinates.")

        location_data = streamlit_geolocation()

        if location_data and location_data.get("latitude") is not None:
            st.success(
                "GPS location captured: "
                f"{location_data['latitude']:.6f}, "
                f"{location_data['longitude']:.6f}"
            )

        analyze = st.button(
            lang["analyze"],
            type="primary",
            use_container_width=True,
        )

        if not analyze:
            return

        if uploaded_file is None:
            st.error("Please upload or capture an image.")
            return

        if not landmark.strip():
            st.error("Please enter the incident location.")
            return

        try:
            ai_detector, vision_model, vision_processor, waste_detector = (
                get_ai_resources()
            )

            with st.status(
                "Analyzing incident...",
                expanded=True,
            ) as status:
                img = Image.open(uploaded_file)
                img.thumbnail(
                    (512, 512),
                    Image.Resampling.LANCZOS,
                )

                st.write("Authenticating submitted image...")
                is_fake, final_fake_confidence = run_image_authentication(
                    img,
                    ai_detector,
                    vision_model,
                    vision_processor,
                )

                if is_fake:
                    fake_confidence = round(
                        float(final_fake_confidence) * 100,
                        1,
                    )

                    status.update(
                        label="Image validation failed",
                        state="error",
                        expanded=False,
                    )

                    st.error(
                        f"AI-generated/synthetic image detected "
                        f"(confidence: {fake_confidence}%)."
                    )
                    st.warning(
                        "This submission was not processed as a municipal "
                        "waste report."
                    )

                    add_activity(
                        f"Rejected synthetic image ({fake_confidence}%)",
                        landmark,
                        "-20",
                    )
                    return

                st.write("Image authenticated. Detecting waste objects...")

                item_counts = detect_waste_objects(
                    img,
                    waste_detector,
                )

                total_items = sum(item_counts.values())

                for key, value in item_counts.items():
                    st.session_state.waste_inventory[key] = (
                        st.session_state.waste_inventory.get(key, 0)
                        + value
                    )

                st.write("Classifying waste category...")

                detected_category, confidence_score = classify_waste(
                    img,
                    vision_model,
                    vision_processor,
                )

                is_clean = "Clean" in detected_category

                if incident_desc:
                    st.write("Incident description recorded.")

                if voice_note:
                    st.write("Voice note recorded.")

                status.update(
                    label="Analysis complete",
                    state="complete",
                    expanded=False,
                )

            if total_items > 0:
                st.warning(
                    f"{total_items} waste objects detected."
                )

            if is_clean:
                st.success(
                    f"{landmark} was classified as a clean area "
                    f"(confidence: {confidence_score}%)."
                )

                add_activity(
                    "Verified Clean Area",
                    landmark,
                    "+10",
                )
                return

            st.warning(
                f"Waste category: {detected_category} "
                f"(confidence: {confidence_score}%)."
            )

            current_count = (
                st.session_state.location_reports.get(landmark, 0) + 1
            )
            st.session_state.location_reports[landmark] = current_count

            st.success(lang["success_msg"].format(landmark))

            if current_count >= 3:
                st.warning(
                    f"Recurring issue detected: {landmark} has "
                    f"{current_count} reports."
                )

                email_status = send_escalation_email(
                    landmark,
                    detected_category,
                    current_count,
                )

                if email_status:
                    st.info(
                        "Municipal escalation email sent successfully."
                    )
                else:
                    st.info(
                        "Municipal email service is not configured."
                    )

            add_activity(
                f"Reported Waste: {detected_category}",
                landmark,
                "+50",
            )

        except Exception as exc:
            st.error(
                "The analysis could not be completed. "
                "Please verify the uploaded image and service configuration."
            )
            with st.expander("Technical details"):
                st.exception(exc)

    with col_b:
        st.markdown(
            f'<div class="section-title">{lang["leaderboard"]}</div>',
            unsafe_allow_html=True,
        )

        community_df = pd.DataFrame(
            {
                "Rank": ["1", "2", "3"],
                "User": [
                    "Anand_MDU",
                    "Meenakshi_P",
                    st.session_state.current_user.split("@")[0],
                ],
                "Eco-Credits": [2450, 1920, 1250],
            }
        )

        st.dataframe(
            community_df,
            hide_index=True,
            use_container_width=True,
        )

        st.markdown(
            '<div class="card"><strong>Report overview</strong><br>'
            '<span class="small-muted">'
            "Reports are grouped by location and escalated after "
            "the existing three-report threshold."
            "</span></div>",
            unsafe_allow_html=True,
        )

        active_reports = sum(
            st.session_state.location_reports.values()
        )

        if active_reports:
            st.metric("Reports received", active_reports)
        else:
            st.info("No waste reports have been submitted yet.")


# ============================================================
# 15. COMMAND CENTER
# ============================================================

def render_command_center(df_madurai: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-title">Live Operations</div>',
        unsafe_allow_html=True,
    )

    live_pending = sum(
        st.session_state.location_reports.values()
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_stat_card(lang["pending"], live_pending)

    with c2:
        render_stat_card("AI confidence reference", "94%")

    with c3:
        render_stat_card("Active units", "22")

    with c4:
        render_stat_card("Cleanest zone", "W-42")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="card"><strong>Reported locations</strong></div>',
        unsafe_allow_html=True,
    )

    reported_locations = list(
        st.session_state.location_reports.keys()
    )

    if reported_locations:
        live_map_data = df_madurai[
            df_madurai["Location"].isin(reported_locations)
        ].copy()

        if live_map_data.empty:
            st.info(
                "Reports exist for locations not included in the "
                "sample map dataset."
            )
        else:
            st.map(
                live_map_data,
                color="#DC3545",
                size=60,
            )
    else:
        st.info("No active waste reports.")
        st.map(
            pd.DataFrame(
                {
                    "lat": [DEFAULT_LAT],
                    "lon": [DEFAULT_LON],
                }
            ),
            zoom=11,
        )


# ============================================================
# 16. ANALYTICS
# ============================================================

def render_analytics() -> None:
    st.markdown(
        '<div class="section-title">Waste Analytics</div>',
        unsafe_allow_html=True,
    )

    inventory = st.session_state.get(
        "waste_inventory",
        {},
    )

    total_scanned = sum(inventory.values())

    if total_scanned == 0:
        st.info(
            "No waste objects have been detected yet. "
            "Run an analysis from the Citizen Portal."
        )
        return

    col_graph, col_stats = st.columns(
        [1.5, 1],
        gap="large",
    )

    with col_graph:
        st.markdown(
            '<div class="card"><strong>Waste composition</strong></div>',
            unsafe_allow_html=True,
        )

        df_inv = pd.DataFrame(
            list(inventory.items()),
            columns=["Waste Type", "Count"],
        )

        df_inv = df_inv[df_inv["Count"] > 0]

        fig = px.pie(
            df_inv,
            values="Count",
            names="Waste Type",
            hole=0.55,
            color_discrete_sequence=[
                "#198754",
                "#2563EB",
                "#D97706",
                "#6B7280",
            ],
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=20, l=0, r=0),
            showlegend=True,
            font=dict(color=COLORS["text"]),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with col_stats:
        st.markdown(
            '<div class="card"><strong>Key metrics</strong></div>',
            unsafe_allow_html=True,
        )

        st.metric(
            "Total objects detected",
            total_scanned,
        )

        most_common = (
            df_inv.loc[
                df_inv["Count"].idxmax(),
                "Waste Type",
            ].title()
            if not df_inv.empty
            else "N/A"
        )

        st.metric(
            "Dominant category",
            most_common,
        )

        # Existing calculation preserved.
        carbon_offset = total_scanned * 0.45

        st.metric(
            "Projected carbon cost",
            f"{carbon_offset:.2f} kg CO₂e",
        )


# ============================================================
# 17. AI ASSISTANT
# ============================================================

def render_ai_assistant() -> None:
    st.markdown(
        '<div class="section-title">AI Environmental Assistant</div>',
        unsafe_allow_html=True,
    )

    chat_container = st.container(height=400)

    for message in st.session_state.chat_history:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Ask about waste management, recycling, pollution, or sustainability..."
    )

    if not prompt:
        return

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with chat_container.chat_message("user"):
        st.markdown(prompt)

    try:
        from groq import Groq

        api_key = get_secret("GROQ_API_KEY")

        if not api_key:
            st.error(
                "GROQ_API_KEY is not configured in Streamlit Secrets."
            )
            return

        groq_client = Groq(api_key=api_key)

        env_persona = """
You are CleanAI, an environmental assistant for Madurai city.

Only answer questions related to:
1. Ecosystem and nature preservation.
2. Waste management and pollution control.
3. Reduce, Reuse, Recycle.
4. Sustainable living and green energy.

For unrelated questions, politely explain that this assistant is
limited to environmental topics.

Keep answers concise, practical, and informative.
"""

        api_messages = [
            {
                "role": "system",
                "content": env_persona,
            }
        ]

        for message in st.session_state.chat_history:
            api_messages.append(
                {
                    "role": message["role"],
                    "content": message["content"],
                }
            )

        with chat_container.chat_message("assistant"):
            with st.spinner("Generating response..."):
                chat_completion = groq_client.chat.completions.create(
                    messages=api_messages,
                    model="llama-3.1-8b-instant",
                    temperature=0.5,
                    max_tokens=1024,
                )

                response_text = (
                    chat_completion.choices[0].message.content
                )

                st.markdown(response_text)

        st.session_state.chat_history.append(
            {
                "role": "assistant",
                "content": response_text,
            }
        )

    except ImportError:
        st.error(
            "The Groq package is not installed. "
            "Install it with: pip install groq"
        )
    except Exception:
        st.error(
            "The AI assistant is temporarily unavailable. "
            "Please verify the Groq configuration."
        )


# ============================================================
# 18. SETTINGS
# ============================================================

def render_settings() -> None:
    st.markdown(
        f'<div class="section-title">{lang["settings_title"]}</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        new_lang = st.selectbox(
            "System language",
            ["English", "Tamil"],
            index=["English", "Tamil"].index(
                st.session_state.lang
            ),
        )

        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

    with col2:
        st.markdown(
            '<div class="card"><strong>Application status</strong><br>'
            '<span class="small-muted">'
            "Normal enterprise interface • AI services available on demand"
            "</span></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown(
        f'<div class="section-title">{lang["history_title"]}</div>',
        unsafe_allow_html=True,
    )

    user_history = [
        log
        for log in st.session_state.activity_log
        if log["User"] == st.session_state.current_user
    ]

    if not user_history:
        st.info("No activity has been recorded yet.")
    else:
        st.dataframe(
            pd.DataFrame(user_history),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 19. MAIN APPLICATION
# ============================================================

if st.session_state.current_user is None:
    render_authentication()
    st.stop()

render_sidebar()
render_header()

df_madurai = get_location_dataframe()

menu = st.tabs(lang["tabs"])

with menu[0]:
    render_citizen_portal(df_madurai)

with menu[1]:
    render_command_center(df_madurai)

with menu[2]:
    render_analytics()

with menu[3]:
    render_ai_assistant()

with menu[4]:
    render_settings()
