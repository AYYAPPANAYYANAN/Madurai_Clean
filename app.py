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
# 18. ENTERPRISE DASHBOARD COMPONENTS
# ============================================================

def render_kpi(label: str, value: Any, helper: str = "", tone: str = "default") -> None:
    tone_map = {
        "default": ("#0F172A", "#64748B"),
        "green": ("#166534", "#15803D"),
        "blue": ("#1D4ED8", "#2563EB"),
        "amber": ("#92400E", "#D97706"),
        "red": ("#991B1B", "#DC2626"),
    }
    value_color, accent = tone_map.get(tone, tone_map["default"])

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-label">{label}</span>
                <span class="kpi-dot" style="background:{accent};"></span>
            </div>
            <div class="kpi-value" style="color:{value_color};">{value}</div>
            <div class="kpi-helper">{helper}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_title(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="page-title">
            <div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            <div class="live-status">
                <span class="live-dot"></span>
                System operational
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_enterprise() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-logo">♻</div>
                <div>
                    <div class="sidebar-name">CleanAI</div>
                    <div class="sidebar-sub">Municipal Intelligence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown("#### Workspace")
        st.caption(st.session_state.current_user)

        if st.button("Sign out", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.sos_active = False
            st.rerun()

        st.divider()

        st.markdown("#### Emergency support")
        disaster_detected, condition = check_severe_weather()

        if disaster_detected:
            st.error(f"Weather alert: {condition}")
        else:
            st.success(f"Weather: {condition}")

        if st.button(
            "Request emergency assistance",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.sos_active = True

        if st.session_state.get("sos_active", False):
            st.warning(
                "Emergency channel active. Record a message below."
            )

            emergency_audio = st.audio_input(
                "Emergency message",
            )

            if emergency_audio:
                current_loc = "Madurai"
                transcribed_text = (
                    "User requires immediate medical/evacuation assistance."
                )

                with st.spinner("Submitting emergency request..."):
                    sent = send_sos_email(
                        current_loc,
                        transcribed_text,
                    )

                if sent:
                    st.success("Emergency request submitted.")
                else:
                    st.warning(
                        "Emergency email is not configured."
                    )

        st.divider()
        st.caption("Madurai CleanAI")
        st.caption("Municipal waste intelligence platform")


# ============================================================
# 19. CITIZEN PORTAL — ENTERPRISE UI
# ============================================================

def render_citizen_enterprise() -> None:
    render_page_title(
        "Citizen Portal",
        "Submit a waste incident for AI-assisted validation and classification.",
    )

    total_reports = sum(
        st.session_state.location_reports.values()
    )
    total_objects = sum(
        st.session_state.waste_inventory.values()
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        render_kpi(
            "Active reports",
            total_reports,
            "Across submitted locations",
            "red" if total_reports else "green",
        )
    with k2:
        render_kpi(
            "Objects detected",
            total_objects,
            "Cumulative AI detections",
            "blue",
        )
    with k3:
        render_kpi(
            "Locations monitored",
            len(st.session_state.location_reports),
            "Reported locations",
            "amber",
        )
    with k4:
        render_kpi(
            "Reports today",
            len(
                [
                    x
                    for x in st.session_state.activity_log
                    if x["User"] == st.session_state.current_user
                    and x["Time"].startswith(
                        datetime.now().strftime("%Y-%m-%d")
                    )
                ]
            ),
            "Your submitted activity",
            "green",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns(
        [1.35, 0.65],
        gap="large",
    )

    with left:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>New waste incident</h3>
                    <p>Provide an image and location. AI validation runs before classification.</p>
                </div>
                <span class="step-badge">AI VERIFIED</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        input_method = st.radio(
            "Image source",
            ["Upload image", "Use camera"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if input_method == "Upload image":
            uploaded_file = st.file_uploader(
                "Drop an incident image here",
                type=["jpg", "jpeg", "png"],
            )
        else:
            uploaded_file = st.camera_input(
                "Capture incident image"
            )

        c1, c2 = st.columns(2)

        with c1:
            landmark = st.text_input(
                "Location / landmark",
                placeholder="e.g. Kalavasal Junction",
            )

        with c2:
            incident_desc = st.text_input(
                "Short description",
                placeholder="e.g. Waste blocking footpath",
            )

        location_data = streamlit_geolocation()

        if (
            location_data
            and location_data.get("latitude") is not None
        ):
            st.markdown(
                f"""
                <div class="location-confirm">
                    <span>●</span>
                    GPS captured: {location_data["latitude"]:.6f},
                    {location_data["longitude"]:.6f}
                </div>
                """,
                unsafe_allow_html=True,
            )

        voice_note = st.audio_input(
            "Optional voice note"
        )

        st.markdown(
            '<div class="analysis-note">'
            "<strong>Processing pipeline</strong>"
            "<span>Image authenticity → object detection → waste classification → escalation</span>"
            "</div>",
            unsafe_allow_html=True,
        )

        analyze = st.button(
            "Analyze and submit incident",
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
                "Running incident analysis",
                expanded=True,
            ) as status:
                img = Image.open(uploaded_file)
                img.thumbnail(
                    (512, 512),
                    Image.Resampling.LANCZOS,
                )

                st.write("1. Validating image authenticity")
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
                        f"Synthetic/AI-generated image detected "
                        f"(confidence: {fake_confidence}%)."
                    )

                    add_activity(
                        f"Rejected synthetic image ({fake_confidence}%)",
                        landmark,
                        "-20",
                    )
                    return

                st.write("2. Detecting individual waste objects")

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

                st.write("3. Classifying waste category")

                detected_category, confidence_score = classify_waste(
                    img,
                    vision_model,
                    vision_processor,
                )

                is_clean = "Clean" in detected_category

                if incident_desc:
                    st.write("4. Incident context recorded")

                if voice_note:
                    st.write("5. Voice note attached")

                status.update(
                    label="Analysis complete",
                    state="complete",
                    expanded=False,
                )

            # Analysis result panel
            result_left, result_right = st.columns(
                [1.3, 0.7]
            )

            with result_left:
                if is_clean:
                    st.success(
                        f"Clean area detected at {landmark} "
                        f"({confidence_score}% confidence)."
                    )
                else:
                    st.warning(
                        f"Waste detected: {detected_category} "
                        f"({confidence_score}% confidence)."
                    )

            with result_right:
                st.metric(
                    "Objects detected",
                    total_items,
                )

            if is_clean:
                add_activity(
                    "Verified Clean Area",
                    landmark,
                    "+10",
                )
                return

            current_count = (
                st.session_state.location_reports.get(
                    landmark,
                    0,
                )
                + 1
            )

            st.session_state.location_reports[
                landmark
            ] = current_count

            st.success(
                lang["success_msg"].format(landmark)
            )

            # Existing escalation logic: threshold remains 3.
            if current_count >= 3:
                st.warning(
                    f"Recurring issue: {landmark} has "
                    f"{current_count} reports."
                )

                email_status = send_escalation_email(
                    landmark,
                    detected_category,
                    current_count,
                )

                if email_status:
                    st.info(
                        "Municipal escalation notification sent."
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
                "Analysis could not be completed. "
                "Please verify the image and service configuration."
            )
            with st.expander("Technical details"):
                st.exception(exc)

    with right:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>How it works</h3>
                    <p>Existing AI pipeline</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        stages = [
            ("01", "Image validation", "5-factor authenticity analysis"),
            ("02", "Object detection", "DETR-based waste object counting"),
            ("03", "Classification", "CLIP-based waste category"),
            ("04", "Location tracking", "Incident grouped by location"),
            ("05", "Escalation", "Existing 3-report threshold"),
        ]

        for number, title, description in stages:
            st.markdown(
                f"""
                <div class="workflow-row">
                    <div class="workflow-number">{number}</div>
                    <div>
                        <div class="workflow-title">{title}</div>
                        <div class="workflow-description">{description}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# 20. OPERATIONS DASHBOARD
# ============================================================

def render_operations() -> None:
    render_page_title(
        "Operations Dashboard",
        "Monitor incoming waste reports and municipal response activity.",
    )

    reports = st.session_state.location_reports
    total_reports = sum(reports.values())
    locations = len(reports)
    recurring = sum(
        1 for value in reports.values() if value >= 3
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_kpi(
            "Open reports",
            total_reports,
            "Submitted waste incidents",
            "red" if total_reports else "green",
        )

    with c2:
        render_kpi(
            "Affected locations",
            locations,
            "Unique reported locations",
            "amber",
        )

    with c3:
        render_kpi(
            "Recurring issues",
            recurring,
            "Locations at escalation threshold",
            "red" if recurring else "green",
        )

    with c4:
        render_kpi(
            "Response units",
            22,
            "Configured operational units",
            "blue",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns(
        [1.35, 0.65],
        gap="large",
    )

    with left:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>Incident map</h3>
                    <p>Known locations represented in the current dataset.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        df_madurai = get_location_dataframe()
        reported_locations = list(reports.keys())

        if reported_locations:
            live_map_data = df_madurai[
                df_madurai["Location"].isin(
                    reported_locations
                )
            ].copy()

            if live_map_data.empty:
                st.info(
                    "Reports are present for locations outside "
                    "the current sample map dataset."
                )
            else:
                st.map(
                    live_map_data,
                    color="#DC3545",
                    size=60,
                )
        else:
            st.info(
                "No active reports. The operations map is clear."
            )
            st.map(
                pd.DataFrame(
                    {
                        "lat": [DEFAULT_LAT],
                        "lon": [DEFAULT_LON],
                    }
                ),
                zoom=11,
            )

    with right:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>Incident queue</h3>
                    <p>Locations ordered for review.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if reports:
            queue = pd.DataFrame(
                [
                    {
                        "Location": location,
                        "Reports": count,
                        "Status": (
                            "Escalation"
                            if count >= 3
                            else "Open"
                        ),
                    }
                    for location, count in reports.items()
                ]
            ).sort_values(
                "Reports",
                ascending=False,
            )

            st.dataframe(
                queue,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No incidents in the queue.")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="panel-heading">
            <div>
                <h3>Recent activity</h3>
                <p>Latest actions recorded by the application.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.activity_log:
        activity = pd.DataFrame(
            st.session_state.activity_log[-10:][::-1]
        )
        st.dataframe(
            activity,
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No activity has been recorded yet.")


# ============================================================
# 21. ANALYTICS DASHBOARD
# ============================================================

def render_analytics_enterprise() -> None:
    render_page_title(
        "Environmental Analytics",
        "Understand waste composition and incident activity.",
    )

    inventory = st.session_state.get(
        "waste_inventory",
        {},
    )

    total_scanned = sum(inventory.values())

    if total_scanned == 0:
        c1, c2, c3 = st.columns(3)
        with c1:
            render_kpi(
                "Objects detected",
                0,
                "Awaiting AI scans",
            )
        with c2:
            render_kpi(
                "Categories",
                0,
                "No classified waste yet",
            )
        with c3:
            render_kpi(
                "Projected carbon cost",
                "0.00 kg",
                "Existing project calculation",
            )

        st.info(
            "Run an image analysis from the Citizen Portal "
            "to populate analytics."
        )
        return

    df_inv = pd.DataFrame(
        list(inventory.items()),
        columns=["Waste Type", "Count"],
    )
    df_inv = df_inv[df_inv["Count"] > 0]

    most_common = (
        df_inv.loc[
            df_inv["Count"].idxmax(),
            "Waste Type",
        ].title()
        if not df_inv.empty
        else "N/A"
    )

    # Existing carbon formula preserved.
    carbon_offset = total_scanned * 0.45

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_kpi(
            "Objects detected",
            total_scanned,
            "Cumulative AI detections",
            "blue",
        )

    with c2:
        render_kpi(
            "Dominant category",
            most_common,
            "Highest detected count",
            "green",
        )

    with c3:
        render_kpi(
            "Waste categories",
            len(df_inv),
            "Categories with detections",
            "amber",
        )

    with c4:
        render_kpi(
            "Projected carbon cost",
            f"{carbon_offset:.2f} kg",
            "Existing project calculation",
            "red",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    chart_col, table_col = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    with chart_col:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>Waste composition</h3>
                    <p>Distribution of objects detected by the AI pipeline.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        fig = px.pie(
            df_inv,
            values="Count",
            names="Waste Type",
            hole=0.58,
            color_discrete_sequence=[
                "#198754",
                "#2563EB",
                "#D97706",
                "#64748B",
            ],
        )

        fig.update_traces(
            textposition="outside",
            textinfo="percent+label",
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(
                t=20,
                b=20,
                l=20,
                r=20,
            ),
            font=dict(
                color=COLORS["text"],
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with table_col:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>Detection breakdown</h3>
                    <p>Current object inventory.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.dataframe(
            df_inv.sort_values(
                "Count",
                ascending=False,
            ),
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# 22. AI ASSISTANT — ENTERPRISE UI
# ============================================================

def render_ai_enterprise() -> None:
    render_page_title(
        "AI Assistant",
        "Environmental guidance powered by the configured Groq model.",
    )

    left, right = st.columns(
        [1.55, 0.45],
        gap="large",
    )

    with left:
        chat_container = st.container(height=500)

        for message in st.session_state.chat_history:
            with chat_container.chat_message(
                message["role"]
            ):
                st.markdown(message["content"])

        prompt = st.chat_input(
            "Ask about recycling, waste management, pollution, or sustainability..."
        )

        if prompt:
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

                groq_client = Groq(
                    api_key=api_key
                )

                env_persona = """
You are CleanAI, an environmental assistant for Madurai city.

Only answer questions related to:
1. Ecosystem and nature preservation.
2. Waste management and pollution control.
3. Reduce, Reuse, Recycle.
4. Sustainable living and green energy.

For unrelated questions, politely explain that this assistant
is limited to environmental topics.

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

                with chat_container.chat_message(
                    "assistant"
                ):
                    with st.spinner(
                        "Generating response..."
                    ):
                        completion = (
                            groq_client
                            .chat
                            .completions
                            .create(
                                messages=api_messages,
                                model="llama-3.1-8b-instant",
                                temperature=0.5,
                                max_tokens=1024,
                            )
                        )

                        response_text = (
                            completion
                            .choices[0]
                            .message
                            .content
                        )

                        st.markdown(
                            response_text
                        )

                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                    }
                )

            except ImportError:
                st.error(
                    "Install the Groq package with: pip install groq"
                )
            except Exception:
                st.error(
                    "The AI assistant is temporarily unavailable."
                )

    with right:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>Assistant scope</h3>
                    <p>Configured knowledge areas</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for item in [
            "Waste management",
            "Recycling",
            "Pollution control",
            "Sustainable living",
            "Green energy",
        ]:
            st.markdown(
                f'<div class="scope-item">✓ {item}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button(
            "Clear conversation",
            use_container_width=True,
        ):
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": (
                        "Welcome to Madurai CleanAI. "
                        "How can I help with an environmental question?"
                    ),
                }
            ]
            st.rerun()


# ============================================================
# 23. SETTINGS / ADMIN
# ============================================================

def render_settings_enterprise() -> None:
    render_page_title(
        "Settings",
        "Application preferences, service configuration status, and activity.",
    )

    left, right = st.columns(
        [0.8, 1.2],
        gap="large",
    )

    with left:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>Preferences</h3>
                    <p>Personalize the application.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        new_lang = st.selectbox(
            "Language",
            ["English", "Tamil"],
            index=["English", "Tamil"].index(
                st.session_state.lang
            ),
        )

        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="info-box">
                <strong>Current architecture</strong><br>
                Streamlit UI → AI inference services → incident state → analytics
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="panel-heading">
                <div>
                    <h3>Service health</h3>
                    <p>Configuration status visible to the operator.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        services = [
            (
                "Groq AI Assistant",
                bool(get_secret("GROQ_API_KEY")),
            ),
            (
                "Weather service",
                bool(get_secret("OPENWEATHERMAP_API_KEY")),
            ),
            (
                "SMTP notifications",
                all(
                    [
                        get_secret("SMTP_USERNAME"),
                        get_secret("SMTP_PASSWORD"),
                        get_secret("ALERT_RECEIVER_EMAIL"),
                    ]
                ),
            ),
        ]

        for service, configured in services:
            status = "Configured" if configured else "Not configured"
            cls = "health-ok" if configured else "health-warning"

            st.markdown(
                f"""
                <div class="health-row">
                    <span>{service}</span>
                    <span class="{cls}">{status}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="panel-heading">
            <div>
                <h3>Activity history</h3>
                <p>Audit-friendly application activity for the current session.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.activity_log:
        st.dataframe(
            pd.DataFrame(
                st.session_state.activity_log[::-1]
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No activity recorded.")


# ============================================================
# 24. ENTERPRISE AUTHENTICATION
# ============================================================

def render_enterprise_login() -> None:
    st.markdown(
        """
        <div class="login-shell">
            <div class="login-brand">
                <div class="login-logo">♻</div>
                <div>
                    <div class="login-title">Madurai CleanAI</div>
                    <div class="login-subtitle">
                        Municipal waste intelligence platform
                    </div>
                </div>
            </div>
            <div class="login-trust">
                <span class="trust-dot"></span>
                Secure municipal workspace
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.08, 1])

    with center:
        with st.container(border=True):
            st.markdown(
                """
                <div class="login-card-header">
                    <div class="login-card-kicker">WELCOME BACK</div>
                    <h2>Sign in to CleanAI</h2>
                    <p>
                        Access incident reporting, AI analysis,
                        operations, and environmental analytics.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.auth_mode == "login":
                email = st.text_input(
                    "Email address",
                    placeholder="admin@madurai.com",
                    key="login_email",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password",
                )

                st.markdown(
                    '<div class="login-help">Use your registered CleanAI account to continue.</div>',
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Sign in",
                    type="primary",
                    use_container_width=True,
                    key="login_submit",
                ):
                    if (
                        email in st.session_state.users_db
                        and st.session_state.users_db[email] == password
                    ):
                        st.session_state.current_user = email
                        st.rerun()
                    else:
                        st.error("The email or password is incorrect.")

                st.markdown(
                    '<div class="or-divider"><span>OR</span></div>',
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Create a local demo account",
                    use_container_width=True,
                    key="open_signup",
                ):
                    st.session_state.auth_mode = "signup"
                    st.rerun()

            else:
                new_email = st.text_input(
                    "Email address",
                    placeholder="user@example.com",
                    key="signup_email",
                )

                new_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                    key="signup_password",
                )

                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="signup_confirm_password",
                )

                if st.button(
                    "Create account",
                    type="primary",
                    use_container_width=True,
                    key="signup_submit",
                ):
                    if not new_email or "@" not in new_email:
                        st.error("Enter a valid email address.")
                    elif len(new_password) < 8:
                        st.error(
                            "Password must contain at least 8 characters."
                        )
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif new_email in st.session_state.users_db:
                        st.error(
                            "An account with this email already exists."
                        )
                    else:
                        st.session_state.users_db[new_email] = new_password
                        st.session_state.current_user = new_email
                        st.rerun()

                if st.button(
                    "Back to sign in",
                    use_container_width=True,
                    key="back_to_login",
                ):
                    st.session_state.auth_mode = "login"
                    st.rerun()

    st.markdown(
        """
        <div class="login-footer">
            <span>Madurai CleanAI</span>
            <span>•</span>
            <span>AI-assisted municipal waste management</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 25. ENTERPRISE MAIN APPLICATION
# ============================================================

# Clean enterprise visual system.
st.markdown(
    f"""
    <style>
        :root {{
            --primary: {COLORS["primary"]};
            --primary-dark: {COLORS["primary_dark"]};
            --text: #0F172A;
            --muted: #64748B;
            --border: #D9E2EC;
            --surface: #FFFFFF;
            --page: #F3F7F5;
        }}

        /* ---------- APP FOUNDATION ---------- */
        .stApp {{
            background:
                linear-gradient(180deg, #F8FAF9 0%, #F1F5F3 100%) !important;
            color: var(--text) !important;
        }}

        [data-testid="stAppViewContainer"] {{
            background: transparent !important;
        }}

        [data-testid="stHeader"] {{
            background: rgba(255,255,255,.96) !important;
            border-bottom: 1px solid #E2E8F0 !important;
        }}

        .main .block-container {{
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }}

        /* ---------- GLOBAL TEXT CONTRAST ---------- */
        .stMarkdown,
        .stMarkdown p,
        .stMarkdown span,
        .stMarkdown div,
        label,
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span {{
            color: #334155 !important;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: #0F172A !important;
        }}

        /* ---------- SIDEBAR ---------- */
        [data-testid="stSidebar"] {{
            background: #FFFFFF !important;
            border-right: 1px solid #D9E2EC !important;
        }}

        [data-testid="stSidebar"] * {{
            color: #334155;
        }}

        .sidebar-brand {{
            display:flex;
            align-items:center;
            gap:11px;
            margin-bottom:8px;
        }}

        .sidebar-logo {{
            width:40px;
            height:40px;
            display:flex;
            align-items:center;
            justify-content:center;
            border-radius:10px;
            background:#E8F5EE;
            color:#146C43 !important;
            font-size:1.3rem;
            font-weight:700;
        }}

        .sidebar-name {{
            color:#0F172A !important;
            font-weight:750;
            font-size:1.05rem;
        }}

        .sidebar-sub {{
            color:#64748B !important;
            font-size:.7rem;
            margin-top:1px;
        }}

        /* ---------- PAGE HEADER ---------- */
        .page-title {{
            display:flex;
            justify-content:space-between;
            align-items:flex-start;
            gap:20px;
            margin-bottom:24px;
        }}

        .page-title h1 {{
            margin:0;
            color:#0F172A !important;
            font-size:1.85rem;
            line-height:1.2;
            font-weight:750;
            letter-spacing:-.025em;
        }}

        .page-title p {{
            margin:6px 0 0;
            color:#64748B !important;
            font-size:.9rem;
        }}

        .live-status {{
            display:flex;
            align-items:center;
            gap:8px;
            border:1px solid #BBF7D0;
            background:#F0FDF4;
            color:#166534 !important;
            border-radius:999px;
            padding:7px 12px;
            font-size:.75rem;
            font-weight:650;
            white-space:nowrap;
        }}

        .live-dot {{
            width:7px;
            height:7px;
            border-radius:50%;
            background:#16A34A;
        }}

        /* ---------- KPI ---------- */
        .kpi-card {{
            background:#FFFFFF;
            border:1px solid #D9E2EC;
            border-radius:12px;
            padding:17px 18px;
            min-height:112px;
            box-shadow:0 2px 6px rgba(15,23,42,.035);
        }}

        .kpi-label {{
            color:#64748B !important;
            font-size:.72rem;
            font-weight:700;
            text-transform:uppercase;
            letter-spacing:.055em;
        }}

        .kpi-value {{
            font-size:1.7rem;
            font-weight:750;
            margin-top:10px;
            line-height:1.1;
        }}

        .kpi-helper {{
            color:#94A3B8 !important;
            font-size:.72rem;
            margin-top:7px;
        }}

        /* ---------- PANELS ---------- */
        .panel-heading {{
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:14px;
            background:#FFFFFF;
            border:1px solid #D9E2EC;
            border-bottom:0;
            border-radius:12px 12px 0 0;
            padding:16px 18px 11px;
        }}

        .panel-heading h3 {{
            margin:0;
            color:#0F172A !important;
            font-size:1rem;
            font-weight:700;
        }}

        .panel-heading p {{
            margin:4px 0 0;
            color:#64748B !important;
            font-size:.76rem;
        }}

        /* ---------- WIDGET LABELS / INPUTS ---------- */
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p {{
            color:#334155 !important;
            font-size:.82rem !important;
            font-weight:600 !important;
        }}

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input {{
            background:#FFFFFF !important;
            color:#0F172A !important;
            -webkit-text-fill-color:#0F172A !important;
            border:1px solid #B8C4D1 !important;
            border-radius:8px !important;
            caret-color:#0F172A !important;
        }}

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder,
        .stNumberInput input::placeholder {{
            color:#94A3B8 !important;
            opacity:1 !important;
            -webkit-text-fill-color:#94A3B8 !important;
        }}

        .stTextInput input:focus,
        .stTextArea textarea:focus,
        .stNumberInput input:focus {{
            border-color:#198754 !important;
            box-shadow:0 0 0 3px rgba(25,135,84,.12) !important;
        }}

        /* Password eye button / BaseWeb controls */
        [data-baseweb="input"] button {{
            color:#475569 !important;
            background:#F8FAFC !important;
            border-left:1px solid #CBD5E1 !important;
        }}

        /* ---------- BUTTONS ---------- */
        .stButton > button {{
            border-radius:8px !important;
            min-height:2.65rem !important;
            font-weight:650 !important;
            border:1px solid #CBD5E1 !important;
            background:#FFFFFF !important;
            color:#1E293B !important;
        }}

        .stButton > button p,
        .stButton > button span {{
            color:inherit !important;
        }}

        .stButton > button:hover {{
            border-color:#94A3B8 !important;
            background:#F8FAFC !important;
            color:#0F172A !important;
        }}

        .stButton > button[kind="primary"],
        button[data-testid="baseButton-primary"] {{
            background:#198754 !important;
            border-color:#198754 !important;
            color:#FFFFFF !important;
        }}

        .stButton > button[kind="primary"] *,
        button[data-testid="baseButton-primary"] * {{
            color:#FFFFFF !important;
        }}

        .stButton > button[kind="primary"]:hover,
        button[data-testid="baseButton-primary"]:hover {{
            background:#146C43 !important;
            border-color:#146C43 !important;
        }}

        /* ---------- TABS ---------- */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {{
            gap:2px;
            border-bottom:1px solid #D9E2EC;
            background:transparent;
        }}

        [data-testid="stTabs"] button[role="tab"] {{
            color:#64748B !important;
            font-size:.8rem;
            font-weight:650;
            padding:11px 15px;
        }}

        [data-testid="stTabs"] button[role="tab"] p {{
            color:inherit !important;
        }}

        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
            color:#146C43 !important;
        }}

        /* ---------- FILE UPLOAD / RADIO / SELECT ---------- */
        [data-testid="stFileUploaderDropzone"] {{
            background:#F8FAFC !important;
            border:1px dashed #B8C4D1 !important;
            border-radius:10px !important;
        }}

        [data-testid="stFileUploaderDropzone"] * {{
            color:#475569 !important;
        }}

        [data-baseweb="select"] > div {{
            background:#FFFFFF !important;
            border-color:#B8C4D1 !important;
            color:#0F172A !important;
        }}

        [data-baseweb="select"] * {{
            color:#334155 !important;
        }}

        [role="radiogroup"] label,
        [role="radiogroup"] label p {{
            color:#334155 !important;
        }}

        /* ---------- DATAFRAME ---------- */
        [data-testid="stDataFrame"] {{
            border:1px solid #D9E2EC;
            border-radius:10px;
            overflow:hidden;
            background:#FFFFFF;
        }}

        /* ---------- WORKFLOW ---------- */
        .step-badge {{
            border:1px solid #BFDBFE;
            background:#EFF6FF;
            color:#1D4ED8 !important;
            border-radius:999px;
            padding:5px 9px;
            font-size:.64rem;
            font-weight:700;
        }}

        .workflow-row {{
            display:flex;
            gap:12px;
            align-items:flex-start;
            background:#FFFFFF;
            border:1px solid #D9E2EC;
            border-top:0;
            padding:13px 16px;
        }}

        .workflow-row:last-child {{
            border-radius:0 0 12px 12px;
        }}

        .workflow-number {{
            width:28px;
            height:28px;
            display:flex;
            align-items:center;
            justify-content:center;
            border-radius:7px;
            background:#E8F5EE;
            color:#146C43 !important;
            font-size:.7rem;
            font-weight:700;
            flex:0 0 28px;
        }}

        .workflow-title {{
            color:#1E293B !important;
            font-size:.82rem;
            font-weight:700;
        }}

        .workflow-description {{
            color:#64748B !important;
            font-size:.72rem;
            margin-top:2px;
        }}

        .location-confirm {{
            background:#F0FDF4;
            border:1px solid #BBF7D0;
            color:#166534 !important;
            padding:8px 10px;
            border-radius:8px;
            font-size:.75rem;
            margin:7px 0 12px;
        }}

        .analysis-note {{
            display:flex;
            justify-content:space-between;
            gap:15px;
            border:1px solid #DBEAFE;
            background:#F8FAFC;
            border-radius:8px;
            padding:10px 12px;
            margin:12px 0;
            font-size:.73rem;
        }}

        .analysis-note strong {{
            color:#334155 !important;
        }}

        .analysis-note span {{
            color:#64748B !important;
        }}

        .scope-item {{
            background:#F8FAFC;
            border:1px solid #D9E2EC;
            border-radius:8px;
            padding:9px 10px;
            margin-bottom:7px;
            color:#334155 !important;
            font-size:.78rem;
        }}

        /* ---------- HEALTH ---------- */
        .health-row {{
            display:flex;
            align-items:center;
            justify-content:space-between;
            border-bottom:1px solid #E2E8F0;
            padding:12px 2px;
            color:#334155 !important;
            font-size:.8rem;
        }}

        .health-ok {{
            color:#166534 !important;
            background:#F0FDF4;
            border:1px solid #BBF7D0;
            padding:3px 7px;
            border-radius:999px;
            font-size:.65rem;
            font-weight:700;
        }}

        .health-warning {{
            color:#92400E !important;
            background:#FFFBEB;
            border:1px solid #FDE68A;
            padding:3px 7px;
            border-radius:999px;
            font-size:.65rem;
            font-weight:700;
        }}

        .info-box {{
            background:#F8FAFC;
            border:1px solid #D9E2EC;
            border-radius:10px;
            padding:13px;
            color:#475569 !important;
            font-size:.77rem;
            line-height:1.6;
        }}

        /* ---------- LOGIN ---------- */
        .login-shell {{
            max-width:570px;
            margin:70px auto 18px;
            text-align:center;
        }}

        .login-brand {{
            display:flex;
            align-items:center;
            justify-content:center;
            gap:13px;
        }}

        .login-logo {{
            width:50px;
            height:50px;
            display:flex;
            align-items:center;
            justify-content:center;
            border-radius:12px;
            background:#E8F5EE;
            color:#146C43 !important;
            font-size:1.5rem;
            font-weight:750;
            border:1px solid #CDEDDD;
        }}

        .login-title {{
            font-size:1.55rem;
            font-weight:750;
            color:#0F172A !important;
            text-align:left;
        }}

        .login-subtitle {{
            color:#64748B !important;
            font-size:.78rem;
            margin-top:2px;
            text-align:left;
        }}

        .login-trust {{
            display:inline-flex;
            align-items:center;
            gap:7px;
            margin-top:14px;
            color:#166534 !important;
            background:#F0FDF4;
            border:1px solid #BBF7D0;
            border-radius:999px;
            padding:5px 10px;
            font-size:.68rem;
            font-weight:650;
        }}

        .trust-dot {{
            width:6px;
            height:6px;
            background:#16A34A;
            border-radius:50%;
        }}

        .login-card-header {{
            margin-bottom:18px;
        }}

        .login-card-header h2 {{
            color:#0F172A !important;
            margin:0;
            font-size:1.35rem;
            font-weight:750;
        }}

        .login-card-header p {{
            color:#64748B !important;
            font-size:.8rem;
            line-height:1.55;
            margin:6px 0 0;
        }}

        .login-card-kicker {{
            color:#198754 !important;
            font-size:.65rem;
            font-weight:750;
            letter-spacing:.1em;
            margin-bottom:6px;
        }}

        .login-help {{
            color:#64748B !important;
            font-size:.68rem;
            margin:7px 0 13px;
        }}

        .or-divider {{
            display:flex;
            align-items:center;
            gap:10px;
            color:#94A3B8 !important;
            font-size:.64rem;
            margin:14px 0;
        }}

        .or-divider::before,
        .or-divider::after {{
            content:"";
            height:1px;
            flex:1;
            background:#E2E8F0;
        }}

        .login-footer {{
            display:flex;
            justify-content:center;
            gap:8px;
            color:#94A3B8 !important;
            font-size:.67rem;
            margin:18px auto 40px;
        }}

        /* Streamlit bordered container used by login card */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background:#FFFFFF !important;
            border:1px solid #D9E2EC !important;
            border-radius:14px !important;
            box-shadow:0 12px 32px rgba(15,23,42,.055) !important;
        }}

        /* ---------- MOBILE ---------- */
        @media (max-width: 800px) {{
            .main .block-container {{
                padding:1rem;
            }}

            .page-title {{
                flex-direction:column;
            }}

            .live-status {{
                align-self:flex-start;
            }}

            .analysis-note {{
                flex-direction:column;
            }}

            .login-shell {{
                margin-top:30px;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)



if st.session_state.current_user is None:
    render_enterprise_login()
    st.stop()

render_sidebar_enterprise()

tabs = st.tabs(
    [
        "Citizen Portal",
        "Operations",
        "Analytics",
        "AI Assistant",
        "Settings",
    ]
)

with tabs[0]:
    render_citizen_enterprise()

with tabs[1]:
    render_operations()

with tabs[2]:
    render_analytics_enterprise()

with tabs[3]:
    render_ai_enterprise()

with tabs[4]:
    render_settings_enterprise()
