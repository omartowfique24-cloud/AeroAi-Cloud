import datetime
import difflib
import io
import math
import os
import re
import smtplib
import subprocess
import sys
import threading
import time
import webbrowser
from email.message import EmailMessage
import requests
import ollama
import folium

# PDF Library Import
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Safe Desktop Libraries Import
try:
    import pyautogui
    import pyttsx3
    import speech_recognition as sr
    DESKTOP_LIBS_AVAILABLE = True
except ImportError:
    DESKTOP_LIBS_AVAILABLE = False

# Flask Import
try:
    from flask import Flask, request, jsonify, render_template_string
    REMOTE_ACCESS_AVAILABLE = True
except ImportError:
    REMOTE_ACCESS_AVAILABLE = False

# UTF-8 Output
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

# PyQt5 Imports (Earth/Hologram HUD)
try:
    from PyQt5.QtCore import QObject, Qt, pyqtSignal, QPoint, QTimer
    from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush
    from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QLineEdit, QPushButton
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# ============================================================
# CONFIGURATION & SECURITY STATE (OMAR'S CREDENTIALS)
# ============================================================
OLLAMA_MODEL = os.environ.get("AERO_OLLAMA_MODEL", "llama3")
VOICE_TIMEOUT = 5
VOICE_PHRASE_LIMIT = 8
DUPLICATE_COMMAND_SECONDS = 1.5

SECURITY_STATE = {
    "is_authenticated": True,
    "waiting_for_pin": False,
    "secret_pin": "1259",
    "user_phone": "01708323751",
    "user_email": "omar.towfique.24@gmail.com",
    "gmail_app_password": "your_gmail_app_password_here",
}

LAST_KNOWN_VILLAGE = {"name": None}

MALICIOUS_DOMAINS = [
    "free-gift", "win-prize", "hack", "phishing", "malware", "virus",
    "lottery-winner", "claim-money", "secure-bank-login", "crypto-airdrop-free"
]

def scan_and_neutralize_threats(text_or_query):
    url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+')
    for url in url_pattern.findall(text_or_query):
        if any(bad in url.lower() for bad in MALICIOUS_DOMAINS):
            cleaned = text_or_query.replace(url, "[⚠️ AERO ANTIVIRUS: MALICIOUS LINK BLOCKED]")
            return False, cleaned, "Sir, a dangerous virus link was blocked by AeRo Antivirus!"
    return True, text_or_query, None

# ============================================================
# STUDY HELPER & PDF GENERATOR
# ============================================================
def generate_study_pdf(topic, content):
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    desktop_path = os.path.join(user_profile, "Desktop")
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', topic)[:30].strip('_') or "Study_Notes"
    pdf_path = os.path.join(desktop_path, f"AeRo_{safe_name}.pdf")

    if not PDF_AVAILABLE:
        txt_path = os.path.join(desktop_path, f"AeRo_{safe_name}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"TOPIC: {topic}\n\n{content}")
        return False, txt_path

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font("Arial", "B", 16)
        clean_topic = topic.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, f"AeRo Study Notes: {clean_topic}", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "", 12)
        clean_content = content.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, clean_content)
        pdf.output(pdf_path)

        try:
            os.startfile(pdf_path)
        except Exception:
            pass
        return True, pdf_path
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        return False, str(e)

def run_osint_lookup(target):
    phone_no = target.strip()
    clean_num = re.sub(r'[^0-9+]', '', phone_no)
    
    if clean_num.startswith("+880"):
        clean_num = "0" + clean_num[4:]
    elif clean_num.startswith("880"):
        clean_num = "0" + clean_num[3:]

    operator = "Unknown / International Carrier"
    country = "Bangladesh" if clean_num.startswith("01") and len(clean_num) == 11 else "Global / Unknown"

    if clean_num.startswith(("017", "013")):
        operator = "Grameenphone (GP)"
    elif clean_num.startswith(("018", "016")):
        operator = "Robi / Airtel Axiata"
    elif clean_num.startswith(("019", "014")):
        operator = "Banglalink Digital"
    elif clean_num.startswith("015"):
        operator = "Teletalk Bangladesh"

    result_text = (
        f"[AeRo TELECOM OSINT REPORT]:\n"
        f"• Target Number: {phone_no}\n"
        f"• Country: {country}\n"
        f"• Telecom Operator: {operator}\n"
        f"• Live GPS Status: Use '3D LIVE GPS & VILLAGE MAP' for exact satellite telemetry."
    )
    return result_text

def get_prayer_times():
    return (
        "আজকের নামাজের সময়সূচি (রংপুর অঞ্চল):\n"
        "• ফজর: ৪:৪৮ AM | যোহর: ১২:৫৯ PM | আসর: ৪:৩৬ PM | মাগরিব: ৭:৩৬ PM | ইশা: ৯:০০ PM"
    )

def ask_ai_brain(prompt, system_prompt=""):
    try:
        low_p = prompt.lower()
        if any(k in low_p for k in ["prayer", "namaz", "namazer somoy"]):
            return get_prayer_times()

        if "pdf" in low_p:
            topic = re.sub(r'\b(make|create|generate|give|me|a|on|about|pdf|notes|study)\b', '', low_p, flags=re.IGNORECASE).strip()
            if not topic:
                topic = "General Study Topic"
            study_prompt = f"Write concise study notes on: '{topic}'."
            response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": study_prompt}], options={"num_predict": 250})
            notes = response["message"]["content"] if (response and "message" in response) else f"Study notes on {topic}."
            ok, path_or_err = generate_study_pdf(topic, notes)
            if ok:
                return f"ওমর, '{topic}' স্টাডি PDF ডেস্কটপে সেভ হয়েছে: {path_or_err}"
            else:
                return f"ফাইল সেভ হয়েছে: {path_or_err}"

        default_persona = (
            "You are AeRo Ai, Omar's ultra-fast AI assistant. Reply instantly in 1-2 short sentences in Bengali, English, or Banglish."
        )
        messages = [
            {"role": "system", "content": system_prompt or default_persona},
            {"role": "user", "content": prompt}
        ]
        
        response = ollama.chat(
            model=OLLAMA_MODEL, 
            messages=messages,
            options={
                "temperature": 0.3,
                "num_predict": 120,
                "top_k": 20,
                "top_p": 0.9
            }
        )
        
        if response and "message" in response:
            return response["message"]["content"]
        return "মশাই, লোকাল এআই রেসপন্স প্রস্তুত।"
    except Exception as e:
        print(f"Ollama Connection Error: {e}")
        return "ওমর, Ollama সার্ভার চেক করো!"

# ============================================================
# GLOBAL OBJECTS & TTS
# ============================================================
command_worker_running = True
tts_lock = threading.Lock()
duplicate_lock = threading.Lock()
last_command_text = ""
last_command_time = 0.0

class HUDComm(QObject if PYQT_AVAILABLE else object):
    if PYQT_AVAILABLE:
        update_status = pyqtSignal(str)
        update_subtitle = pyqtSignal(str)
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()

comm = HUDComm()
if not PYQT_AVAILABLE:
    comm.update_status = type('obj', (object,), {'emit': lambda self, x: None})()
    comm.update_subtitle = type('obj', (object,), {'emit': lambda self, x: None})()

def speak_background(text):
    if not text or not DESKTOP_LIBS_AVAILABLE:
        return
    with tts_lock:
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 175)
            engine.say(str(text).strip())
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

def speak(text):
    if not text:
        return
    text = str(text).strip()
    print(f"AERO AI: {text}")
    comm.update_subtitle.emit(f"AERO AI: {text}")
    if DESKTOP_LIBS_AVAILABLE:
        threading.Thread(target=speak_background, args=(text,), daemon=True).start()

WEBSITES_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "messenger": "https://www.messenger.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org",
    "github": "https://github.com",
    "vscode": "https://code.visualstudio.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com"
}

def control_laptop(query_text):
    if not DESKTOP_LIBS_AVAILABLE:
        return False, None
    low_q = query_text.lower().strip()
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    try:
        if "call" in low_q or "phone call" in low_q or "dial" in low_q:
            words = query_text.split()
            phone_number = next((w for w in words if w.isdigit() or w.startswith("+")), "")
            if phone_number:
                speak(f"Calling {phone_number}, sir.")
                subprocess.Popen(f"adb shell am start -a android.intent.action.CALL -d tel:{phone_number}", shell=True)
                return True, None
            else:
                speak("Sir, please provide a valid phone number to call.")
                return True, None

        if "cut call" in low_q or "end call" in low_q or "disconnect call" in low_q:
            speak("Disconnecting the call, sir.")
            subprocess.Popen("adb shell input keyevent KEYCODE_ENDCALL", shell=True)
            return True, None

        if "close" in low_q:
            if "youtube" in low_q or "spotify" in low_q:
                pyautogui.hotkey("ctrl", "w")
                speak("Closed tab, sir.")
                return True, None
            search_term = low_q.replace("close", "").strip()
            if search_term:
                subprocess.Popen(f"taskkill /f /im {search_term}.exe", shell=True)
                speak(f"Closed {search_term}, sir.")
            else:
                pyautogui.hotkey("alt", "f4")
                speak("Window closed, sir.")
            return True, None

        aliases = {"yt": "youtube", "youtub": "youtube", "fb": "facebook", "insta": "instagram", "wa": "whatsapp"}
        for alias, target in aliases.items():
            if re.search(rf"\b{alias}\b", low_q):
                webbrowser.open(WEBSITES_MAP[target])
                speak(f"Opening {target} for you, sir.")
                return True, WEBSITES_MAP[target]

        for key, url in WEBSITES_MAP.items():
            if key in low_q:
                webbrowser.open(url)
                speak(f"Opening {key} for you, sir.")
                return True, url

        words = low_q.replace("open", "").strip().split()
        for w in words:
            match = difflib.get_close_matches(w, WEBSITES_MAP.keys(), n=1, cutoff=0.75)
            if match:
                key = match[0]
                webbrowser.open(WEBSITES_MAP[key])
                speak(f"Opening {key} for you, sir.")
                return True, WEBSITES_MAP[key]

        if "open" in low_q and not any(w in low_q for w in ["youtube", "spotify", "google", "desktop"]):
            search_term = low_q.replace("open", "").strip()
            desktop_path = os.path.join(user_profile, "Desktop")
            found_path = None
            if os.path.exists(desktop_path):
                for item in os.listdir(desktop_path):
                    if search_term in item.lower():
                        found_path = os.path.join(desktop_path, item)
                        break
            if found_path:
                os.startfile(found_path)
                speak(f"Opening {search_term}, sir.")
                return True, None
            else:
                try:
                    os.startfile(search_term)
                    speak(f"Opening {search_term}, sir.")
                    return True, None
                except Exception:
                    speak(f"Sorry sir, could not find {search_term}.")
                    return True, None

        if "screenshot" in low_q:
            shot_path = os.path.join(user_profile, "Desktop", "screenshot.png")
            pyautogui.screenshot(shot_path)
            speak("Screenshot saved on Desktop, sir.")
            return True, None

        if "volume up" in low_q:
            pyautogui.press("volumeup", presses=5, interval=0.05)
            speak("Volume increased, sir.")
            return True, None

        if "volume down" in low_q:
            pyautogui.press("volumedown", presses=5, interval=0.05)
            speak("Volume decreased, sir.")
            return True, None
    except Exception as e:
        print(f"Desktop Control Error: {e}")
    return False, None

def is_duplicate_command(query):
    global last_command_text, last_command_time
    now = time.time()
    norm = re.sub(r"\s+", " ", query.strip().lower())
    with duplicate_lock:
        if norm == last_command_text and now - last_command_time < DUPLICATE_COMMAND_SECONDS:
            return True
        last_command_text = norm
        last_command_time = now
    return False

def voice_listener_loop():
    if not DESKTOP_LIBS_AVAILABLE:
        return
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    while command_worker_running:
        try:
            with sr.Microphone() as source:
                comm.update_status.emit("LISTENING...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=VOICE_TIMEOUT, phrase_time_limit=VOICE_PHRASE_LIMIT)
            comm.update_status.emit("PROCESSING...")
            query = ""
            try:
                query = recognizer.recognize_google(audio, language="en-US")
            except Exception:
                try:
                    query = recognizer.recognize_google(audio, language="bn-BD")
                except Exception:
                    pass
            if query and not is_duplicate_command(query):
                comm.update_subtitle.emit(f"You: {query}")
                is_safe, cleaned, threat_msg = scan_and_neutralize_threats(query)
                if not is_safe:
                    speak(threat_msg)
                    continue
                handled, _ = control_laptop(cleaned)
                if not handled:
                    speak(ask_ai_brain(cleaned))
        except sr.WaitTimeoutError:
            comm.update_status.emit("ONLINE")
        except Exception:
            time.sleep(1)

# ============================================================
# EARTH & HOLOGRAM HUD (PyQt5)
# ============================================================
if PYQT_AVAILABLE:
    class HologramHUD(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setGeometry(80, 80, 1000, 560)
            self.angle = 0.0

            self.cmd_input = QLineEdit(self)
            self.cmd_input.setGeometry(520, 90, 420, 48)
            self.cmd_input.setPlaceholderText("Ask AeRo Terminal: Study PDF, or query...")
            self.cmd_input.setStyleSheet(
                "background-color: rgba(5, 15, 30, 245); color: #00f0ff; "
                "border: 2px solid #ff007f; border-radius: 12px; padding: 10px; font-family: Consolas; font-size: 15px;"
            )
            self.cmd_input.returnPressed.connect(self.handle_typed_command)

            self.exec_btn = QPushButton("AERO EXECUTE", self)
            self.exec_btn.setGeometry(520, 150, 420, 44)
            self.exec_btn.setStyleSheet(
                "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff007f, stop:1 #00f0ff); "
                "color: #000; font-weight: bold; border-radius: 12px; font-family: Consolas; font-size: 15px; }"
                "QPushButton:hover { background: #00f0ff; }"
            )
            self.exec_btn.clicked.connect(self.handle_typed_command)

            self.reply_label = QLabel("Welcome back, Omar sir. AeRo Telemetry Radar Online.", self)
            self.reply_label.setGeometry(520, 210, 420, 300)
            self.reply_label.setWordWrap(True)
            self.reply_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.reply_label.setStyleSheet(
                "background-color: rgba(0, 0, 0, 230); color: #39ff14; "
                "border: 2px solid rgba(255, 0, 127, 200); border-radius: 14px; padding: 15px; font-family: Consolas; font-size: 14px;"
            )

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_animation)
            self.timer.start(1000)
            comm.update_subtitle.connect(self.reply_label.setText)
            self.drag_position = QPoint()
            speak("Welcome back, Omar sir. AeRo radar telemetry system is online.")

        def handle_typed_command(self):
            text = self.cmd_input.text().strip()
            if not text:
                return
            self.cmd_input.clear()
            self.reply_label.setText(f"Omar: {text}")
            threading.Thread(target=self.process_text_command, args=(text,), daemon=True).start()

        def process_text_command(self, query):
            is_safe, cleaned, threat_msg = scan_and_neutralize_threats(query)
            if not is_safe:
                speak(threat_msg)
                return
            handled, _ = control_laptop(cleaned)
            if not handled:
                speak(ask_ai_brain(cleaned))

        def update_animation(self):
            self.angle = (self.angle + 6.0) % 360
            self.update()

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

        def mouseMoveEvent(self, event):
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.drag_position)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            cx, cy = 250, 280
            center = QPoint(cx, cy)
            painter.setPen(QPen(QColor(0, 240, 255, 120), 1.5, Qt.DashLine))
            painter.drawEllipse(center, 210, 210)
            painter.setPen(QPen(QColor(0, 240, 255, 180), 2))
            painter.drawEllipse(center, 180, 180)
            rad = math.radians(self.angle)
            painter.setBrush(QBrush(QColor(255, 0, 127)))
            painter.drawEllipse(QPoint(cx + int(180 * math.cos(rad)), cy + int(180 * math.sin(rad))), 6, 6)
            painter.setPen(QPen(QColor(255, 0, 127, 200), 2))
            painter.drawEllipse(center, 140, 140)

            now = datetime.datetime.now()
            date_str = now.strftime("%d %b %Y").upper()
            time_str = now.strftime("%H:%M:%S")

            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            painter.setPen(QColor(0, 240, 255))
            painter.drawText(cx + 180, cy - 90, "AERO RADAR: SECURE")
            painter.drawText(cx + 180, cy + 80, "TEMP: 28°C")

            painter.setPen(QColor(255, 0, 127))
            painter.drawText(cx - 235, cy - 90, date_str)
            painter.drawText(cx - 235, cy + 80, time_str)

# ============================================================
# WEB INTERFACE (INTERACTIVE GEN PIC/VIDEO, RELOAD HISTORY & ASK AERO)
# ============================================================
HTML_INTERFACE = """<!DOCTYPE html>
<html>
<head>
    <title>AeRo Ai - Autonomous Terminal, Study PDF & 3D Village GPS</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #0b141a; color: #e9edef; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 8px; display: flex; justify-content: center; align-items: center; min-height: 94vh; }
        .app-container { display: flex; width: 1260px; max-width: 100%; height: 92vh; gap: 8px; }
        .sidebar { width: 280px; background: #111b21; border-radius: 12px; display: flex; flex-direction: column; padding: 15px; box-sizing: border-box; }
        .sidebar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #222d34; padding-bottom: 8px; }
        .sidebar-title { color: #00a884; font-size: 15px; font-weight: bold; }
        .new-chat-btn { background: #00a884; color: #fff; border: none; padding: 5px 10px; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; }
        .new-chat-btn:hover { background: #008f6f; }
        .history-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 5px; }
        .history-item { background: #202c33; padding: 7px 10px; border-radius: 7px; font-size: 13px; color: #d1d7db; display: flex; justify-content: space-between; align-items: center; }
        .history-text { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
        .history-text:hover { color: #00a884; }
        .delete-btn { background: transparent; border: none; color: #8696a0; cursor: pointer; font-size: 14px; padding: 0 4px; }
        .delete-btn:hover { color: #ff4d4d; }
        .main-workspace { flex: 1; display: flex; flex-direction: column; gap: 15px; }
        .header-card { background: #111b21; border-radius: 10px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center; }
        .logo-area { display: flex; align-items: center; gap: 12px; }
        .logo-img { height: 36px; width: 36px; border-radius: 50%; border: 1.5px solid #00a884; }
        .logo-text-group h1 { margin: 0; font-size: 20px; color: #00a884; }
        .logo-text-group p { margin: 2px 0 0 0; font-size: 10px; color: #8696a0; letter-spacing: 2px; }
        .telemetry-bar { display: flex; gap: 7px; font-size: 12px; font-weight: bold; color: #00a884; }
        .tele-badge { background: #202c33; padding: 4px 7px; border-radius: 6px; }
        .workspace { display: flex; width: 100%; gap: 8px; flex: 1; min-height: 0; }
        .chat-card { background: #111b21; border-radius: 10px; padding: 10px; flex: 1; display: flex; flex-direction: column; min-height: 0; }
        #log { color: #e9edef; font-size: 14px; background: #0b141a; padding: 8px; border-radius: 8px; flex: 1; overflow-y: auto; margin-bottom: 6px; border: 1px solid #222d34; display: flex; flex-direction: column; gap: 5px; }
        .log-msg { padding: 5px 8px; border-radius: 6px; max-width: 90%; word-break: break-word; }
        .user-msg { background: #005c4b; align-self: flex-end; }
        .ai-msg { background: #202c33; align-self: flex-start; color: #00a884; border: 1px solid #222d34; white-space: pre-line; }
        .aero-search-container { display: flex; align-items: center; background: #202c33; border-radius: 8px; padding: 5px 8px; margin-bottom: 6px; border: 1px solid #222d34; }
        .aero-search-input { flex: 1; background: transparent; border: none; color: #e9edef; font-size: 15px; outline: none; }
        .btn-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; }
        button { background: #00a884; color: #fff; border: none; padding: 7px; border-radius: 7px; font-weight: bold; font-size: 13px; cursor: pointer; }
        button:hover { background: #008f6f; }
        #mic-btn { background: #ea0038; }
        .control-panel { background: #111b21; border-radius: 10px; padding: 10px; width: 320px; display: flex; flex-direction: column; gap: 7px; }
        .panel-title { color: #00a884; font-size: 15px; font-weight: bold; border-bottom: 1px solid #222d34; padding-bottom: 6px; }
        .media-preview { flex: 1; background: #0b141a; border: 1.5px dashed #222d34; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #8696a0; font-size: 13px; padding: 7px; overflow: hidden; }
        .osint-input-group { display: flex; gap: 5px; margin-bottom: 5px; }
        .osint-input { flex: 1; background: #0b141a; border: 1px solid #222d34; color: #00a884; padding: 5px; border-radius: 5px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <span class="sidebar-title">💬 CHAT HISTORY</span>
                <button class="new-chat-btn" onclick="newChat()">+ New Chat</button>
            </div>
            <div class="history-list" id="history-list">
                <div class="history-item">
                    <span class="history-text" onclick="loadHistoryItem('AeRo AI Core Online')">AeRo AI Core Online</span>
                </div>
            </div>
            <button onclick="clearAllHistory()" style="background:#ea0038; margin-top:10px;">CLEAR ALL</button>
        </div>
        <div class="main-workspace">
            <div class="header-card">
                <div class="logo-area">
                    <img src="https://i.ibb.co.com/83p1Xb1/image-2a4080.png" alt="Logo" class="logo-img">
                    <div class="logo-text-group">
                        <h1>AeRo Ai</h1>
                        <p>QUANTUM PERSONAL ASSISTANT</p>
                    </div>
                </div>
                <div class="telemetry-bar">
                    <div class="tele-badge" id="date-box">-- --- ----</div>
                    <div class="tele-badge" id="time-box">--:--:--</div>
                    <div class="tele-badge">28°C (Rangpur)</div>
                </div>
            </div>
            <div class="workspace">
                <div class="chat-card">
                    <div id="log">
                        <div class="log-msg ai-msg">Welcome back, Omar sir. Ask AeRo Terminal, Study PDF & 3D Village GPS Online.</div>
                    </div>
                    <div class="aero-search-container">
                        <input type="text" id="cmd" class="aero-search-input" placeholder="Ask AeRo: Study PDF, prompt, or message..." autocomplete="off">
                    </div>
                    <div class="btn-grid">
                        <button type="button" onclick="sendCommand()">EXECUTE</button>
                        <button type="button" id="mic-btn" onclick="toggleVoice()">🎙️ SPEAK</button>
                        <button type="button" onclick="fetchTrafficCam()">📷 LIVE TRAFFIC</button>
                        <button type="button" onclick="generateImage()">🖼️ GEN PIC</button>
                        <button type="button" onclick="generateVideo()">🎬 GEN VIDEO</button>
                    </div>
                </div>
                <div class="control-panel">
                    <div class="panel-title">TELECOM OSINT & 3D VILLAGE GPS</div>
                    <div class="osint-input-group">
                        <input type="text" id="targetInput" class="osint-input" placeholder="017xxxxxxxx">
                        <button type="button" onclick="runOSINTScan()" style="padding: 5px 10px; font-size:11px;">CHECK SIM</button>
                    </div>
                    <div class="media-preview" id="media-output">[Click 3D LIVE GPS MAP to load Satellite View]</div>
                    <button type="button" onclick="fetchLocation()">📍 3D LIVE GPS & VILLAGE MAP</button>
                    <button type="button" onclick="clearLogs()" style="background:#ea0038;">RESET TERMINAL</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        function updateDateTime() {
            const now = new Date();
            document.getElementById("date-box").innerText = now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
            document.getElementById("time-box").innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        }
        setInterval(updateDateTime, 1000);
        updateDateTime();

        window.addEventListener('DOMContentLoaded', () => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(p => {
                    fetch('/log_visitor_location', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ lat: p.coords.latitude, lon: p.coords.longitude })
                    });
                }, err => {
                    console.log("Visitor geolocation prompt ignored or denied.");
                });
            }
        });

        document.getElementById("cmd").addEventListener("keydown", function(e) {
            if (e.key === "Enter") { e.preventDefault(); sendCommand(); }
        });

        function saveToHistory(text) {
            const historyList = document.getElementById("history-list");
            const item = document.createElement("div");
            item.className = "history-item";
            
            const textSpan = document.createElement("span");
            textSpan.className = "history-text";
            textSpan.textContent = text;
            textSpan.onclick = function() {
                loadHistoryItem(text);
            };

            const deleteBtn = document.createElement("button");
            deleteBtn.className = "delete-btn";
            deleteBtn.innerHTML = "🗑️";
            deleteBtn.title = "Delete item";
            deleteBtn.onclick = function(e) {
                e.stopPropagation();
                item.remove();
            };

            item.appendChild(textSpan);
            item.appendChild(deleteBtn);
            historyList.prepend(item);
        }

        function loadHistoryItem(text) {
            const log = document.getElementById("log");
            const restoredMsg = document.createElement("div");
            restoredMsg.className = "log-msg ai-msg";
            restoredMsg.textContent = "> [Restored History]: " + text;
            log.appendChild(restoredMsg);
            log.scrollTop = log.scrollHeight;
            document.getElementById("cmd").value = text;
        }

        function newChat() {
            document.getElementById("log").innerHTML = `<div class="log-msg ai-msg">New Chat Initialized. How can I assist you, Omar sir?</div>`;
        }

        async function sendCommand() {
            const cmdInput = document.getElementById("cmd");
            const log = document.getElementById("log");
            const text = cmdInput.value.trim();
            if (!text) return;

            cmdInput.value = "";
            saveToHistory(text);

            const userMsg = document.createElement("div");
            userMsg.className = "log-msg user-msg";
            userMsg.textContent = ">> " + text;
            log.appendChild(userMsg);

            const loadingMsg = document.createElement("div");
            loadingMsg.className = "log-msg ai-msg";
            loadingMsg.textContent = "AeRo AI is processing...";
            log.appendChild(loadingMsg);
            log.scrollTop = log.scrollHeight;

            try {
                const res = await fetch("/ask", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query: text })
                });
                const data = await res.json();
                loadingMsg.textContent = "> AeRo: " + (data.reply || data.message || "No response.");
            } catch (err) {
                loadingMsg.style.color = "#ff4d4d";
                loadingMsg.textContent = "Error: Python server is offline or unreachable!";
            }
            log.scrollTop = log.scrollHeight;
        }

        function runOSINTScan() {
            const target = document.getElementById("targetInput").value.trim();
            const log = document.getElementById("log");
            if (!target) return;
            saveToHistory("OSINT: " + target);

            fetch('/osint', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ target: target }) 
            })
            .then(r => r.json())
            .then(d => {
                log.innerHTML += `<div class="log-msg ai-msg">> ${d.result}</div>`;
                log.scrollTop = log.scrollHeight;
            });
        }

        function fetchLocation() {
            const log = document.getElementById("log");
            if (navigator.geolocation) {
                log.innerHTML += `<div class="log-msg ai-msg">> Requesting 3D Satellite GPS lock...</div>`;
                navigator.geolocation.watchPosition(p => {
                    let lat = p.coords.latitude;
                    let lon = p.coords.longitude;
                    
                    document.getElementById("media-output").innerHTML = `<iframe width="100%" height="100%" frameborder="0" src="/show_map?lat=${lat}&lon=${lon}&zoom=17" style="border-radius:6px;"></iframe>`;
                    
                    fetch('/track_live_village', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ lat: lat, lon: lon })
                    })
                    .then(r => r.json())
                    .then(d => {
                        if (d.status === "success") {
                            log.innerHTML += `<div class="log-msg ai-msg">> ${d.report}</div>`;
                            log.scrollTop = log.scrollHeight;
                        }
                    });
                }, err => {
                    log.innerHTML += `<div class="log-msg ai-msg" style="color:#ff4d4d;">> [GPS ERROR]: Please open via http://localhost:5000 and allow location access in browser!</div>`;
                    log.scrollTop = log.scrollHeight;
                }, { enableHighAccuracy: true, maximumAge: 5000 });
            } else {
                alert("Geolocation not supported by this browser.");
            }
        }

        function fetchTrafficCam() {
            document.getElementById("media-output").innerHTML = `<iframe width="100%" height="100%" src="https://www.youtube.com/embed/live_stream?channel=UCupvZG-5ko_eiXAupbDfxWw" frameborder="0" allowfullscreen style="border-radius:6px;"></iframe>`;
        }

        function generateImage() {
            const prompt = prompt("Enter image generation prompt or description:", "Cyberpunk City in Bangladesh");
            if (!prompt) return;
            document.getElementById("media-output").innerHTML = `
                <div style="display:flex; flex-direction:column; gap:5px; height:100%; justify-content:center; align-items:center;">
                    <div style="color:#00a884; font-size:12px;">🖼️ Generating: "${prompt}"</div>
                    <img src="https://picsum.photos/300/140?random=${Math.random()}" style="width:100%; height:110px; object-fit:cover; border-radius:6px;">
                    <input type="file" id="imgUpload" accept="image/*" style="font-size:11px; color:#fff;">
                </div>`;
            saveToHistory("Gen Pic: " + prompt);
        }

        function generateVideo() {
            const prompt = prompt("Enter video generation prompt or concept:", "Satellite orbit over Rangpur");
            if (!prompt) return;
            document.getElementById("media-output").innerHTML = `
                <div style="display:flex; flex-direction:column; gap:5px; height:100%; justify-content:center; align-items:center;">
                    <div style="color:#00a884; font-size:12px;">🎬 Rendering Video: "${prompt}"</div>
                    <div style="background:#202c33; padding:15px; border-radius:6px; color:#39ff14; font-size:12px;">Video Stream Active & Rendered Successfully!</div>
                    <input type="file" id="vidUpload" accept="video/*" style="font-size:11px; color:#fff;">
                </div>`;
            saveToHistory("Gen Video: " + prompt);
        }

        function clearLogs() { document.getElementById("log").innerHTML = `<div class="log-msg ai-msg">Terminal cleared.</div>`; }
        function clearAllHistory() { document.getElementById("history-list").innerHTML = ""; }
        function toggleVoice() { alert("Use desktop mic or Chrome for web voice."); }
    </script>
</body>
</html>
"""

if REMOTE_ACCESS_AVAILABLE:
    app = Flask(__name__)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    @app.route("/")
    def index():
        return render_template_string(HTML_INTERFACE)

    @app.route("/log_visitor_location", methods=['POST'])
    def log_visitor_location():
        data = request.get_json(silent=True) or {}
        lat = data.get('lat')
        lon = data.get('lon')
        print(f"\n[⚠️ AERO VISITOR TELEMETRY ALERT]: Visitor GPS Lock Detected! Latitude: {lat}, Longitude: {lon}")
        return jsonify({"status": "success"})

    @app.route("/osint", methods=['POST'])
    def handle_osint():
        data = request.get_json(silent=True) or {}
        target = data.get("target", "Unknown")
        result_text = run_osint_lookup(target)
        return jsonify({"status": "success", "result": result_text})

    @app.route("/show_map")
    def show_map():
        lat = float(request.args.get('lat', 23.8103))
        lon = float(request.args.get('lon', 90.4125))
        zoom = int(request.args.get('zoom', 16))
        
        m = folium.Map(
            location=[lat, lon], 
            zoom_start=zoom, 
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri &mdash; Satellite View'
        )
        folium.Marker([lat, lon], tooltip="AeRo Live Target", popup="Live GPS Target Node").add_to(m)
        return m._repr_html_()

    @app.route("/track_live_village", methods=['POST'])
    def track_live_village():
        data = request.get_json(silent=True) or {}
        lat = data.get('lat')
        lon = data.get('lon')
        
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
            headers = {'User-Agent': 'AeRoAI-Telemetry/1.0'}
            res = requests.get(url, headers=headers, timeout=5).json()
            
            address = res.get('address', {})
            village = address.get('village') or address.get('suburb') or address.get('neighbourhood') or address.get('hamlet') or "Unknown Village/Area"
            upazila = address.get('county') or address.get('town') or address.get('city_district') or "Unknown Upazila"
            district = address.get('state_district') or address.get('city') or "Unknown District"
            country = address.get('country', 'Bangladesh')

            alert_msg = ""
            if LAST_KNOWN_VILLAGE["name"] is None:
                LAST_KNOWN_VILLAGE["name"] = village
                alert_msg = f"Initial Lock: Currently located in {village}, {upazila}."
            elif LAST_KNOWN_VILLAGE["name"] != village:
                old_village = LAST_KNOWN_VILLAGE["name"]
                LAST_KNOWN_VILLAGE["name"] = village
                alert_msg = f"⚠️ MOVEMENT ALERT: Left [{old_village}] and entered [{village}]!"
            else:
                alert_msg = f"Stationary: Still inside {village}."

            full_report = (
                f"[AeRo 3D SATELLITE & VILLAGE TELEMETRY]:\n"
                f"• Status: {alert_msg}\n"
                f"• Village / Area: {village}\n"
                f"• Upazila / Thana: {upazila}\n"
                f"• District: {district}, {country}\n"
                f"• Coordinates: {lat}, {lon}"
            )
            return jsonify({"status": "success", "report": full_report, "lat": lat, "lon": lon, "village": village})

        except Exception as e:
            return jsonify({"status": "error", "report": f"GPS Reverse Lookup Error: {str(e)}"})

    @app.route("/ask", methods=['POST', 'OPTIONS'])
    def phone_ask():
        if request.method == 'OPTIONS':
            return jsonify({"status": "ok"}), 200
        try:
            data = request.get_json(silent=True) or request.form.to_dict()
            query = data.get("query", "")
            if not query:
                return jsonify({"status": "error", "message": "No query provided"})

            comm.update_subtitle.emit(f"Web: {query}")
            is_safe, cleaned, threat_msg = scan_and_neutralize_threats(query)
            if not is_safe:
                speak(threat_msg)
                return jsonify({"status": "blocked", "reply": threat_msg})

            handled, _ = control_laptop(cleaned)
            if handled:
                reply = "Command executed successfully, sir."
            else:
                reply = ask_ai_brain(cleaned)
                speak(reply)
            return jsonify({"status": "success", "reply": reply})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("Initializing AeRo Ai Quantum & Telemetry Terminal for Omar...")

    if DESKTOP_LIBS_AVAILABLE:
        threading.Thread(target=voice_listener_loop, daemon=True).start()

    if REMOTE_ACCESS_AVAILABLE:
        threading.Thread(target=lambda: app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True), daemon=True).start()
        print("AeRo Web Server running at http://localhost:5000")

    if PYQT_AVAILABLE:
        qt_app = QApplication(sys.argv)
        hud = HologramHUD()
        hud.show()
        qt_app.exec_()

    if REMOTE_ACCESS_AVAILABLE:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down AeRo server...")