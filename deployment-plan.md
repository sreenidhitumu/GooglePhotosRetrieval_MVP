# Streamlit Deployment Plan: Google Photos AI Memory Retrieval MVP

## 1. Executive Summary & Objective

This document outlines the step-by-step plan to deploy the **Google Photos Visual Memory Retrieval MVP** on **Streamlit Community Cloud** while guaranteeing **100% visual and functional preservation** of the custom Google Photos dark-mode interface, animations, modal popups, context clusters, and memory state badges.

> [!IMPORTANT]
> **Zero UI / Functionality Alteration Guarantee**: To maintain the exact look and feel of the custom web app (`index.html`, `index.css`, `js/ui.js`, `js/engine.js`, `js/llm.js`), the deployment architecture uses a **Streamlit Full-Page Custom Component Architecture**. The Streamlit wrapper (`streamlit_app.py`) serves as the Python orchestration host and proxy backend for the Gemini API, while embedding the existing HTML/CSS/JS frontend without modifying any design elements.

---

## 2. Target Deployment Architecture

```mermaid
flowchart TD
    subgraph Streamlit Host ["Streamlit Community Cloud"]
        A[streamlit_app.py Wrapper] -->|Reads| B[Streamlit Secrets: GEMINI_API_KEY]
        A -->|Launches background server| C[Python API Backend (server.py)]
        A -->|Renders Component| D[Custom Frontend (index.html / CSS / JS)]
    end
    
    D -->|AJAX Requests| C
    C -->|google-genai SDK| E[Google Gemini API]
    D -->|Memory Engine| F[data/photos_dataset.json]
```

### Key Architectural Choices:
1. **Frontend Integrity**: `index.html`, `index.css`, `js/engine.js`, `js/ui.js`, and `js/llm.js` remain completely untouched.
2. **Backend API Integration**: `server.py` runs seamlessly within the Streamlit Python runtime container, handling `/api/interpret` and `/api/recommend_next_cue`.
3. **Streamlit Wrapper (`streamlit_app.py`)**: Configures wide layout, injects Streamlit Secrets (`GEMINI_API_KEY`), starts the backend thread, and renders the frontend full-bleed.

---

## 3. Required Deployment Files & Structure

To deploy on Streamlit Cloud, the workspace will include the following files:

```
GooglePhotosRetrievalMVP/
├── streamlit_app.py          # Streamlit launcher & UI container (NEW)
├── requirements.txt          # Python dependencies (NEW)
├── .streamlit/
│   ├── config.toml           # Theme & UI layout settings (NEW)
│   └── secrets.toml          # Local dev API keys (NEW, gitignored)
├── server.py                 # Existing Python backend API
├── index.html                # Existing HTML frontend (UNTOUCHED)
├── index.css                 # Existing Custom CSS (UNTOUCHED)
├── js/
│   ├── engine.js             # Existing Memory Retrieval Engine (UNTOUCHED)
│   ├── llm.js                # Existing LLM Client Interface (UNTOUCHED)
│   └── ui.js                 # Existing UI Renderer (UNTOUCHED)
├── data/
│   ├── photos_dataset.json   # Photo Dataset metadata
│   └── photos/               # Image assets
└── README.md
```

---

## 4. File Configurations

### A. `requirements.txt`
```text
streamlit>=1.30.0
google-genai>=0.1.0
pillow>=10.0.0
requests>=2.31.0
```

### B. `.streamlit/config.toml`
```toml
[theme]
primaryColor = "#38bdf8"
backgroundColor = "#0a0c10"
secondaryBackgroundColor = "#0d1117"
textColor = "#f3f4f6"

[server]
headless = true
enableCORS = false
enableXsrfProtection = false
```

### C. `streamlit_app.py`
```python
import streamlit as st
import streamlit.components.v1 as components
import threading
import time
import os

# 1. Page Configuration for Full-Width Immersive Experience
st.set_page_config(
    page_title="Google Photos AI Memory Retrieval",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide Streamlit default header/footer padding to ensure exact UI match
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .block-container {
            padding: 0rem !important;
            margin: 0rem !important;
            max-width: 100% !important;
        }
        iframe {
            border: none !important;
            width: 100vw !important;
            height: 100vh !important;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Inject Secrets into Environment Variable for Gemini SDK
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# 3. Start Backend Server in Background Thread
def run_backend():
    from server import main as start_server
    try:
        start_server()
    except Exception:
        pass

if "server_started" not in st.session_state:
    st.session_state.server_started = True
    server_thread = threading.Thread(target=run_backend, daemon=True)
    server_thread.start()
    time.sleep(1)

# 4. Read exact index.html and embed as full-height custom HTML component
def load_frontend():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return html_content

# Render the exact unchanged frontend inside Streamlit iframe
components.html(load_frontend(), height=950, scrolling=True)
```

---

## 5. Deployment Step-by-Step Execution Guide

### Step 1: Local Verification
1. Ensure `streamlit_app.py` and `requirements.txt` are created.
2. Create `.streamlit/secrets.toml` locally:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"
   ```
3. Test locally with Streamlit:
   ```bash
   streamlit run streamlit_app.py
   ```
4. Confirm that the interface, dark theme, search prompt ("quote in a cafe I visited"), chips, memory state card (`CUES NOT RECOGNIZED`), and modal popups look identical to the native application.

### Step 2: Push Repository to GitHub
1. Commit all files to your GitHub repository:
   ```bash
   git add streamlit_app.py requirements.txt .streamlit/config.toml index.html index.css js/ data/ server.py
   git commit -m "Add Streamlit deployment configuration with full UI preservation"
   git push origin main
   ```
   *(Ensure `.streamlit/secrets.toml` is in `.gitignore` to keep your API key secure)*.

### Step 3: Deploy to Streamlit Community Cloud
1. Navigate to **[share.streamlit.io](https://share.streamlit.io/)** and log in with your GitHub account.
2. Click **"New app"**.
3. Select your repository (`GooglePhotosRetrievalMVP`), branch (`main`), and set Main file path to `streamlit_app.py`.
4. Click **"Advanced settings..."** → **"Secrets"** and add your Gemini API Key:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   ```
5. Click **"Save"** and then **"Deploy!"**.

---

## 6. QA & Verification Checklist Post-Deployment

| Feature / UI Component | Expected Behavior | Verification Status |
| :--- | :--- | :--- |
| **Theme & Layout** | Full Google Photos dark layout, sidebar, stream grid | ⏳ Pending Deploy |
| **Memory Search** | Search "quote in a cafe I visited" triggers interpretation | ⏳ Pending Deploy |
| **Hierarchical Cues** | Recommends `Location (City)` first, then `Year` or `Month` | ⏳ Pending Deploy |
| **Cues Not Recognized** | Clicking "Not sure" / "None of these" adds cue to `CUES NOT RECOGNIZED` | ⏳ Pending Deploy |
| **Undo / Reset** | Restores skipped cues on Undo; clears all state on Reset All | ⏳ Pending Deploy |
| **Failure Loop Protection**| Displays *"We couldn't reconstruct enough of this memory. Let's try again"* banner & resets when all choices fail | ⏳ Pending Deploy |
| **Photo Inspection** | Clicking visit memory cue opens Lightbox modal | ⏳ Pending Deploy |

---

## 7. Troubleshooting & Edge-Case Handling

- **Issue**: API key missing or 403 Forbidden from Gemini.
  - *Fix*: Double check **Streamlit Secrets** in the Streamlit Cloud dashboard.
- **Issue**: Cross-Origin Request (CORS) blocked inside iframe.
  - *Fix*: `server.py` already includes `Access-Control-Allow-Origin: *` headers for `/api/interpret` and `/api/recommend_next_cue`.
- **Issue**: Scrollbars inside Streamlit container.
  - *Fix*: Streamlit CSS overrides in `streamlit_app.py` set `padding: 0` and `height: 100vh` on the component container.
