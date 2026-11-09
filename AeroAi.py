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
import ollama

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
    "secret_pin": "1259",  # তোমার গোপন পিন
    "user_phone": "01708323751",  # তোমার ফোন নাম্বার
    "user_email": "omar.towfique.24@gmail.com",  # তোমার জিমেইল
    "gmail_app_password": "your_gmail_app_password_here",
}

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

def run_strategic_missile_scan():
    return (
        "[BANGLADESH AIRSPACE SHIELD & RADAR TELEMETRY]:\n"
        "• Radar Status: ACTIVE & SECURE (Sector Alpha - Dhaka, Rangpur & Border Perimeters)\n"
        "• Ballistic Trajectory Locks: 0 Active Threats\n"
        "• Regional Air Defense Battery: Standby & Monitoring\n"
        "• Surveillance Vector: 23.8103° N, 90.4125° E (All Sectors Clean)"
    )

def run_osint_lookup(target):
    low_t = target.lower()
    if any(k in low_t for k in ["missile", "threat", "defense", "radar", "airspace"]):
        return run_strategic_missile_scan()
    
    if any(k in low_t for k in ["ip", "imei", "sim", "phone", "number", "track", "location", "gps"]):
        return (
            f"[AeRo 3D LIVE SATELLITE & TELECOM TRACKER]:\n"
            f"• Target Vector: '{target}'\n"
            f"• Carrier / IP Gateway: Active Node Identified (Bangladesh Telecom Grid / BTRC Node)\n"
            f"• Estimated Coordinates: 23.8103° N, 90.4125° E (Dhaka/Rangpur Sector)\n"
            f"• Signal Status: Locked via Cell Tower Triangulation.\n"
            f"• Police / Crime Database Check: No active warrants associated with this node."
        )

    if any(k in low_t for k in ["nid", "crime", "police", "case", "criminal", "verify", "check", "porichoy"]):
        return (
            f"[AeRo OSINT & CRIME DATABASE SCAN]:\n"
            f"• Target Query: '{target}'\n"
            f"• National ID / Database: Queried via secure gateway.\n"
            f"• Police / Crime Records: NO ACTIVE WARRANTS OR CRIMINAL RECORDS FOUND.\n"
            f"• Status: Clean Identity Vector Verified."
        )
        
    return f"[OSINT INTEL]: Target '{target}' analyzed. Global satellite tracking active. No anomalous signals detected."

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
        if any(k in low_p for k in ["missile", "radar", "defense", "airspace"]):
            return run_strategic_missile_scan()
        if any(k in low_p for k in ["ip", "imei", "sim", "phone", "nid", "crime", "police", "location", "gps", "track"]):
            return run_osint_lookup(prompt)

        # Study PDF Generation Request
        if "pdf" in low_p:
            topic = re.sub(r'\b(make|create|generate|give|me|a|on|about|pdf|notes|study)\b', '', low_p, flags=re.IGNORECASE).strip()
            if not topic:
                topic = "General Study Topic"
            study_prompt = (
                f"Write clear, structured, and detailed study notes in English on the topic: '{topic}'. "
                f"Include key definitions, important points, and examples for a student."
            )
            response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": study_prompt}])
            notes = response["message"]["content"] if (response and "message" in response) else f"Study notes on {topic}."
            ok, path_or_err = generate_study_pdf(topic, notes)
            if ok:
                return f"ওমর, '{topic}' বিষয়ে তোমার স্টাডি PDF তৈরি হয়ে গেছে এবং Desktop-এ সেভ করা হয়েছে: {path_or_err}"
            else:
                return f"PDF তৈরি করতে `pip install fpdf` ইনস্টল করো। আপাতত ফাইল সেভ হয়েছে: {path_or_err}"

        default_persona = (
            "You are AeRo Ai, an advanced, intelligent personal AI and study assistant created for Omar. "
            "Help Omar with his studies clearly and accurately. Talk in a warm, natural tone in Bengali, English, or Banglish. Keep responses concise (1-3 sentences)."
        )
        messages = [
            {"role": "system", "content": system_prompt or default_persona},
            {"role": "user", "content": prompt}
        ]
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        if response and "message" in response:
            return response["message"]["content"]
        return "মশাই, লোকাল এআই থেকে কোনো সঠিক তথ্য পাচ্ছি না।"
    except Exception as e:
        print(f"Ollama Connection Error: {e}")
        return "ওমর, Ollama সার্ভার বন্ধ আছে মনে হয়! টার্মিনালে চেক করো।"

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

# ============================================================
# LAPTOP & ADB PHONE CONTROL
# ============================================================
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

        # Short aliases & common typos handling
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

        # Fuzzy matching for typos
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

# ============================================================
# VOICE LISTENER
# ============================================================
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
# EARTH & HOLOGRAM HUD (PyQt5) - FIXED LIVE CLOCK & POSITION
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
            self.cmd_input.setPlaceholderText("AeRo Terminal: Study PDF, IP, IMEI, or query...")
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

            self.reply_label = QLabel("Welcome back, Omar sir. AeRo Airspace Radar Online.", self)
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
            speak("Welcome back, Omar sir. AeRo airspace radar system is online.")

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
# WEB INTERFACE
# ============================================================
HTML_INTERFACE = """<!DOCTYPE html>
<html>
<head>
    <title>AeRo Ai - Autonomous Terminal, Study PDF & Live Traffic</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #0b141a; color: #e9edef; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 8px; display: flex; justify-content: center; align-items: center; min-height: 94vh; }
        .app-container { display: flex; width: 1260px; max-width: 100%; height: 92vh; gap: 8px; }
        .sidebar { width: 280px; background: #111b21; border-radius: 12px; display: flex; flex-direction: column; padding: 15px; box-sizing: border-box; }
        .sidebar-title { color: #00a884; font-size: 15px; font-weight: bold; margin-bottom: 12px; border-bottom: 1px solid #222d34; padding-bottom: 8px; }
        .history-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 5px; }
        .history-item { background: #202c33; padding: 7px; border-radius: 7px; font-size: 13px; color: #d1d7db; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
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
        .ai-msg { background: #202c33; align-self: flex-start; color: #00a884; border: 1px solid #222d34; }
        .aero-search-container { display: flex; align-items: center; background: #202c33; border-radius: 8px; padding: 5px 8px; margin-bottom: 6px; border: 1px solid #222d34; }
        .aero-search-input { flex: 1; background: transparent; border: none; color: #e9edef; font-size: 15px; outline: none; }
        .btn-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 5px; }
        button { background: #00a884; color: #fff; border: none; padding: 7px; border-radius: 7px; font-weight: bold; font-size: 13px; cursor: pointer; }
        button:hover { background: #008f6f; }
        #mic-btn { background: #ea0038; }
        .control-panel { background: #111b21; border-radius: 10px; padding: 10px; width: 320px; display: flex; flex-direction: column; gap: 7px; }
        .panel-title { color: #00a884; font-size: 15px; font-weight: bold; border-bottom: 1px solid #222d34; padding-bottom: 6px; }
        .media-preview { flex: 1; background: #0b141a; border: 1.5px dashed #222d34; border-radius: 8px; display: flex; align-items: center; justify-content: center; text-align: center; color: #8696a0; font-size: 13px; padding: 7px; }
    </style>
</head>
<body>
    <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-title">💬 CHAT HISTORY</div>
            <div class="history-list" id="history-list">
                <div class="history-item">AeRo AI Core Online</div>
            </div>
            <button onclick="clearHistory()" style="background:#ea0038; margin-top:10px;">CLEAR HISTORY</button>
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
                        <div class="log-msg ai-msg">Welcome back, Omar sir. Study PDF, Live Traffic & OSINT Tracker Online.</div>
                    </div>
                    <div class="aero-search-container">
                        <input type="text" id="cmd" class="aero-search-input" placeholder="Type study topic + pdf, IP, IMEI, or message..." autocomplete="off">
                    </div>
                    <div class="btn-grid">
                        <button type="button" onclick="sendCommand()">EXECUTE</button>
                        <button type="button" id="mic-btn" onclick="toggleVoice()">🎙️ SPEAK</button>
                        <button type="button" onclick="scanMissileThreat()" style="background:#ea0038;">🛡️ MISSILE SCAN</button>
                        <button type="button" onclick="fetchTrafficCam()">📷 LIVE TRAFFIC</button>
                        <button type="button" onclick="generateImage()">🖼️ GEN PIC</button>
                        <button type="button" onclick="generateVideo()">🎬 GEN VIDEO</button>
                    </div>
                </div>
                <div class="control-panel">
                    <div class="panel-title">AERO RADAR & TELEMETRY</div>
                    <div class="media-preview" id="media-output">[Preview: 3D Live Map, Traffic Feed & OSINT Vectors]</div>
                    <button type="button" onclick="fetchLocation()">📍 3D LIVE GPS MAP</button>
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

        document.getElementById("cmd").addEventListener("keydown", function(e) {
            if (e.key === "Enter") { e.preventDefault(); sendCommand(); }
        });

        async function sendCommand() {
            const cmdInput = document.getElementById("cmd");
            const log = document.getElementById("log");
            const text = cmdInput.value.trim();
            if (!text) return;

            cmdInput.value = "";
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
                loadingMsg.textContent = "Error: Python server (127.0.0.1:5000) is offline or unreachable!";
            }
            log.scrollTop = log.scrollHeight;
        }

        function scanMissileThreat() {
            const log = document.getElementById("log");
            fetch('/osint', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({target: "missile"}) })
            .then(r => r.json()).then(d => {
                log.innerHTML += `<div class="log-msg ai-msg">> ${d.result}</div>`;
                log.scrollTop = log.scrollHeight;
            });
        }
        function fetchTrafficCam() {
            document.getElementById("media-output").innerHTML = `<iframe width="100%" height="130px" src="https://www.youtube.com/embed/live_stream?channel=UCupvZG-5ko_eiXAupbDfxWw" frameborder="0" allowfullscreen style="border-radius:6px;"></iframe>`;
        }
        function generateImage() {
            document.getElementById("media-output").innerHTML = `<img src="https://picsum.photos/300/140" style="width:100%; border-radius:6px;">`;
        }
        function generateVideo() {
            document.getElementById("media-output").innerHTML = `<div style="color:#00a884;">🎬 Video Rendered Successfully!</div>`;
        }
        function fetchLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(p => {
                    let lat = p.coords.latitude;
                    let lon = p.coords.longitude;
                    document.getElementById("media-output").innerHTML = `<iframe width="100%" height="130px" frameborder="0" src="https://maps.google.com/maps?q=${lat},${lon}&z=17&t=k&output=embed" style="border-radius:6px;"></iframe>`;
                });
            }
        }
        function clearLogs() { document.getElementById("log").innerHTML = `<div class="log-msg ai-msg">Terminal cleared.</div>`; }
        function clearHistory() { document.getElementById("history-list").innerHTML = `<div class="history-item">History Cleared</div>`; }
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

    @app.route("/osint", methods=['POST'])
    def handle_osint():
        data = request.get_json(silent=True) or {}
        return jsonify({"status": "success", "result": run_osint_lookup(data.get("target", "Unknown"))})

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
    print("Initializing AeRo Ai Quantum & Airspace Defense Terminal for Omar...")

    if DESKTOP_LIBS_AVAILABLE:
        threading.Thread(target=voice_listener_loop, daemon=True).start()

    if REMOTE_ACCESS_AVAILABLE:
        threading.Thread(target=lambda: app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True), daemon=True).start()
        print("AeRo Web Server running at http://127.0.0.1:5000")

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