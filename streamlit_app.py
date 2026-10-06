import os
import sys
import time
import socket
import threading
import streamlit as st
import streamlit.components.v1 as components

# ==============================================================================
# 1. STREAMLIT PAGE & THEME CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Google Photos AI Memory Retrieval",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject CSS to hide default Streamlit padding, header, and footer for 100% full-bleed UI
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
            height: 98vh !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SECRETS & ENVIRONMENT SETUP
# ==============================================================================
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

# ==============================================================================
# 3. BACKGROUND BACKEND SERVER INITIALIZATION
# ==============================================================================
def find_available_port(default_port=8080):
    for port in range(default_port, default_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return default_port

SERVER_PORT = getattr(st.session_state, 'server_port', 8080)

def start_backend_server(port):
    try:
        import server
        server.PORT = port
        server.socketserver.TCPServer.allow_reuse_address = True
        with server.socketserver.TCPServer(("", port), server.SecureRetrievalServer) as httpd:
            print(f"[Streamlit App] Secure Retrieval Server started on port {port}")
            httpd.serve_forever()
    except Exception as err:
        print(f"[Streamlit App] Backend server start notice: {err}")

if "server_started" not in st.session_state:
    target_port = find_available_port(8080)
    st.session_state.server_port = target_port
    SERVER_PORT = target_port
    
    server_thread = threading.Thread(target=start_backend_server, args=(target_port,), daemon=True)
    server_thread.start()
    st.session_state.server_started = True
    time.sleep(0.5)

# ==============================================================================
# 4. FRONTEND BUNDLER & RENDERER (INLINES CSS & JS FOR 100% RELIABILITY)
# ==============================================================================
def get_bundled_html(server_port):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(base_dir, "index.html")
    css_path = os.path.join(base_dir, "index.css")
    engine_js_path = os.path.join(base_dir, "js", "engine.js")
    llm_js_path = os.path.join(base_dir, "js", "llm.js")
    ui_js_path = os.path.join(base_dir, "js", "ui.js")

    if not os.path.exists(index_path):
        return "<h3>Error: index.html not found in application directory.</h3>"

    with open(index_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    import json
    import base64
    dataset_path = os.path.join(base_dir, "data", "photos_dataset.json")
    dataset_json = "[]"
    if os.path.exists(dataset_path):
        with open(dataset_path, "r", encoding="utf-8") as f:
            dataset_data = json.load(f)
            for item in dataset_data:
                url = item.get("url", "")
                if url.startswith("images/"):
                    img_file = os.path.join(base_dir, url)
                    if os.path.exists(img_file):
                        with open(img_file, "rb") as img_f:
                            encoded = base64.b64encode(img_f.read()).decode('utf-8')
                            ext = img_file.split('.')[-1].lower()
                            mime = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
                            item["url"] = f"data:{mime};base64,{encoded}"
            dataset_json = json.dumps(dataset_data)

    # Inlining CSS for 100% guaranteed UI rendering
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        if '<link rel="stylesheet" href="index.css">' in html_content:
            html_content = html_content.replace(
                '<link rel="stylesheet" href="index.css">',
                f'<style>\n{css_content}\n</style>'
            )
        elif '</head>' in html_content:
            html_content = html_content.replace('</head>', f'<style>\n{css_content}\n</style>\n</head>')

    # Inlining Dataset JSON
    dataset_script = f'<script>window.PHOTO_DATASET = {dataset_json};</script>'
    if '<head>' in html_content:
        html_content = html_content.replace('<head>', f'<head>\n  {dataset_script}', 1)

    # Inlining JS scripts
    if os.path.exists(engine_js_path):
        with open(engine_js_path, "r", encoding="utf-8") as f:
            engine_js = f.read()
        html_content = html_content.replace('<script src="js/engine.js"></script>', f'<script>\n{engine_js}\n</script>')

    if os.path.exists(llm_js_path):
        with open(llm_js_path, "r", encoding="utf-8") as f:
            llm_js = f.read()
        html_content = html_content.replace('<script src="js/llm.js"></script>', f'<script>\n{llm_js}\n</script>')

    if os.path.exists(ui_js_path):
        with open(ui_js_path, "r", encoding="utf-8") as f:
            ui_js = f.read()
        html_content = html_content.replace('<script src="js/ui.js"></script>', f'<script>\n{ui_js}\n</script>')

    # Inject <base> tag to route relative fetches (data/photos, API endpoints) to backend server port
    base_tag = f'<base href="http://127.0.0.1:{server_port}/">'
    if "<head>" in html_content:
        html_content = html_content.replace("<head>", f"<head>\n  {base_tag}", 1)
    else:
        html_content = f"{base_tag}\n{html_content}"

    return html_content

# Render exact unchanged frontend inside Streamlit iframe component
bundled_html = get_bundled_html(SERVER_PORT)
components.html(bundled_html, height=950, scrolling=True)
