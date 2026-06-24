# ♻️ Madurai CleanAI — Multimodal Smart City Protocol

Madurai CleanAI is a cutting-edge, premium multimodal AI-powered waste management dashboard designed for modern smart city governance. Built on top of Streamlit, Tailwind CSS, and Hugging Face Transformers, the system leverages high-fidelity deep learning architectures to dynamically spot, quantify, and analyze waste accumulation incidents while integrating defensive forensic modules to counter false reports.

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=PyTorch&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

---
WEBPAGE
"https://smart-city-1.streamlit.app/"

## 🚀 Key Architectural Features

### 🧠 1. Multimodal AI Framework
* **Object Quantification Core:** Utilizes the End-to-End Object Detection Transformer (`facebook/detr-resnet-50`) to perform exact cluster counting and locate distinct objects (bottles, bags, debris) within unstructured images.
* **Semantic Matching Pipeline:** Embeds a zero-shot multi-modal classification vector engine via OpenAI’s CLIP (`clip-vit-base-patch32`) to associate context strings with target image matrices.
* **Deepfake & Fraud Prevention:** Integrates an image classification Vision Transformer (ViT) pipeline (`umm-maybe/AI-image-detector`) to execute 5-layer multi-spectral validation and weed out synthetically generated or adversarial reports.

### ⚡ 2. Automated Smart Governance Engine
* **Chronic Location Escalation:** Monitors citizen reports in real-time. If an asset area exceeds critical notification thresholds, it automatically triggers an SMTP-secure notification to municipal corporation authorities with precise coordinates.
* **Disaster SOS Override:** Actively monitors meteorology feeds using OpenWeatherMap API hooks. If flooding, thunderstorms, or critical infrastructure failure occurs, users can broadcast a high-priority geo-located vocal SOS signal.

### 🎮 3. Tactical User Experience & UI Core
* **Tactile Volumetric Theme:** Crafted using high-fidelity Custom CSS injection utilizing Vercel-inspired deep black gradients, glassmorphic layouts, and responsive fluid animations.
* **In-App RL Canvas Simulator:** An embedded JavaScript reinforcement learning canvas engine running a training cycle animation (`Generation: 42`), adding utility and a gaming layer for users awaiting pipeline executions.
* **Dual Language Localized Engine:** Full dynamic translation state machines across standard English and Tamil languages.

---

## 🛠️ Installation & Setup

### 1. Clone the Repository
BASH 
2. Configure Dependencies
Ensure you have Python 3.9+ installed. Run the command below to provision packages:

Bash
pip install streamlit pandas numpy plotly requests pillow torch transformers streamlit-geolocation    
