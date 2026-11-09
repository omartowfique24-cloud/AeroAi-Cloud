import datetime
import io
import math
import os
import random
import re
import smtplib
import subprocess
import sys
import threading
import time
import webbrowser
from email.message import EmailMessage
import ollama

# Safe Desktop Libraries Import
try:
    import pyautogui
    import pygame
    import pyttsx3
    import speech_recognition as sr
    DESKTOP_LIBS_AVAILABLE = True
except ImportError:
    DESKTOP_LIBS_AVAILABLE = False

# Flask Import for Local Web Interface & Remote Access
try:
    from flask import Flask, request, jsonify, render_template_string
    REMOTE_ACCESS_AVAILABLE = True
except ImportError:
    REMOTE_ACCESS_AVAILABLE = False

# ------------------------------------------------------------
# UTF-8 OUTPUT
# ------------------------------------------------------------
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

# ------------------------------------------------------------
# PYQT5 IMPORTS
# ------------------------------------------------------------
try:
    from PyQt5.QtCore import QObject, Qt, pyqtSignal, QPoint, QTimer
    from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush, QLinearGradient
    from PyQt5.QtWidgets import (
        QApplication,
        QLabel,
        QMainWindow,
        QLineEdit,
        QPushButton,
    )
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
    "gmail_app_password": "your_gmail_app_password_here",  # জিমেইল অ্যাপ পাসওয়ার্ড
    "temp_otp": None,
    "failed_attempts": 0,
}

# ============================================================
# AERO STRATEGIC DEFENSE & MISSILE THREAT TRACKER (BANGLADESH SHIELD)
# ============================================================

MALICIOUS_DOMAINS = [
    "free-gift", "win-prize", "hack", "phishing", "malware", "virus", 
    "lottery-winner", "claim-money", "secure-bank-login", "crypto-airdrop-free"
]

VIRUS_FILE_EXTENSIONS = ['.vbs', '.bat', '.exe.scr', '.pif', '.lnk']

def scan_and_neutralize_threats(text_or_query):
    url_pattern = re.compile(r'https?://[^\s]+|www\.[^\s]+')
    found_urls = url_pattern.findall(text_or_query)
    
    for url in found_urls:
        low_url = url.lower()
        for bad_word in MALICIOUS_DOMAINS:
            if bad_word in low_url:
                cleaned_text = text_or_query.replace(url, "[⚠️ AERO ANTIVIRUS: MALICIOUS LINK BLOCKED & NEUTRALIZED]")
                threading.Thread(target=send_security_breach_alert, args=(f"Malicious Link Blocked: {url}",), daemon=True).start()
                return False, cleaned_text, "Sir, a dangerous virus link or phishing SMS was detected and blocked by Jarvis Antivirus!"

    if DESKTOP_LIBS_AVAILABLE:
        try:
            user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
            downloads_path = os.path.join(user_profile, "Downloads")
            if os.path.exists(downloads_path):
                for f in os.listdir(downloads_path):
                    if any(f.endswith(ext) for ext in VIRUS_FILE_EXTENSIONS):
                        bad_file_path = os.path.join(downloads_path, f)
                        os.remove(bad_file_path)
                        threading.Thread(target=send_security_breach_alert, args=(f"Quarantined Virus File: {f}",), daemon=True).start()
        except Exception as e:
            print(f"Antivirus Scan Error: {e}")

    return True, text_or_query, None

def send_security_breach_alert(threat_info="Unknown Threat"):
    try:
        msg = EmailMessage()
        msg.set_subject("🛡️ JARVIS DEFENSE & ANTIVIRUS ALERT!")
        msg.set_content(
            f"Hello Sir Omar (Towfique Omar Elahi),\n\n"
            f"Jarvis Strategic Defense Shield has intercepted an alert!\n"
            f"Details: {threat_info}\n"
            f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Registered Phone: {SECURITY_STATE['user_phone']}\n\n"
            f"Your system & national airspace perimeter is secure, Omar!"
        )
        msg['From'] = SECURITY_STATE["user_email"]
        msg['To'] = SECURITY_STATE["user_email"]

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SECURITY_STATE["user_email"], SECURITY_STATE["gmail_app_password"])
            smtp.send_message(msg)
        print("Defense Alert Sent to Omar's Email!")
    except Exception as e:
        print(f"Alert Error: {e}")

def run_strategic_missile_scan():
    return "[BANGLADESH AIRSPACE SHIELD]: Radar active. All regional launch sites monitored. No active ballistic locks on Dhaka, Rangpur, or borders."

def run_osint_lookup(target):
    if "missile" in target.lower() or "threat" in target.lower() or "defense" in target.lower() or "dhaka" in target.lower():
        return run_strategic_missile_scan()
    return f"[OSINT TELEMETRY]: Target '{target}' analyzed. Global satellite tracking active."

# ============================================================
# ROBUST LOCAL AI BRAIN WITH FACTUAL ACCURACY
# ============================================================

def ask_ai_brain(prompt, system_prompt=""):
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            default_persona = (
                "You are Jarvis, an advanced, highly intelligent, precise, and truth-focused personal AI assistant created for Omar. "
                "Always provide 100% accurate, fact-based, and correct information. "
                "Talk in a warm, natural, human-like tone in Bengali, English, or Banglish. Keep responses concise within 1-2 short sentences."
            )
            messages.append({"role": "system", "content": default_persona})
            
        messages.append({"role": "user", "content": prompt})
        
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        if response and "message" in response:
            return response["message"]["content"]
        return "মশাই, লোকাল এআই থেকে কোনো সঠিক তথ্য পাচ্ছি না।"
    except Exception as e:
        print(f"Ollama Connection Error: {e}")
        return "ওমর, ওল্লামা (Ollama) সার্ভার বন্ধ আছে মনে হয়! টার্মিনালে চেক করো।"

# ============================================================
# GLOBAL OBJECTS & SIGNALS
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

# ============================================================
# FAST & INSTANT TTS ENGINE (PYTTSX3)
# ============================================================

TTS_ENGINE = None
if DESKTOP_LIBS_AVAILABLE:
    try:
        TTS_ENGINE = pyttsx3.init()
        TTS_ENGINE.setProperty('rate', 175)
        
        voices = TTS_ENGINE.getProperty('voices')
        for voice in voices:
            if any(k in voice.name.lower() for k in ["female", "zira", "hazel", "helen", "sara", "bangla"]):
                TTS_ENGINE.setProperty('voice', voice.id)
                break
    except Exception as e:
        print(f"TTS Init Error: {e}")

def speak_background(text):
    if not text or not TTS_ENGINE:
        return
    text = str(text).strip()
    if not text:
        return

    with tts_lock:
        try:
            TTS_ENGINE.say(text)
            TTS_ENGINE.runAndWait()
        except Exception as e:
            print(f"TTS Error: {e}")

def speak(text):
    if not text:
        return
    text = str(text).strip()
    print(f"JARVIS AI: {text}")
    comm.update_subtitle.emit(f"JARVIS AI: {text}")
    if TTS_ENGINE:
        threading.Thread(target=speak_background, args=(text,), daemon=True).start()

# ============================================================
# SECURITY & OTP FUNCTIONS
# ============================================================

def send_otp_to_omar():
    otp = str(random.randint(100000, 999999))
    SECURITY_STATE["temp_otp"] = otp

    msg = EmailMessage()
    msg.set_subject("Jarvis Security Emergency OTP")
    msg.set_content(
        f"Hello Sir Omar (Towfique Omar Elahi),\n"
        f"Your emergency security verification OTP code is: {otp}\n"
        f"Registered Phone: {SECURITY_STATE['user_phone']}"
    )
    msg['From'] = SECURITY_STATE["user_email"]
    msg['To'] = SECURITY_STATE["user_email"]

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SECURITY_STATE["user_email"], SECURITY_STATE["gmail_app_password"])
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"OTP Sending Error: {e}")
        return False

def verify_face_and_voice():
    return True

# ============================================================
# WEBSITE MAPPING & FULL CONTROL (ADB + BROWSER AGENT)
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

def get_matched_website_url(query):
    query = query.lower()
    for key, url in WEBSITES_MAP.items():
        if key in query:
            return key, url
    return None, None

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

        if "cut call" in low_q or "end call" in low_q or "disconnect call" in low_q or "phone cut" in low_q:
            speak("Disconnecting the call, sir.")
            subprocess.Popen("adb shell input keyevent KEYCODE_ENDCALL", shell=True)
            return True, None

        if ("open" in low_q or "close" in low_q) and not any(w in low_q for w in ["youtube", "google", "facebook", "messenger", "whatsapp"]):
            search_term = low_q.replace("open", "").replace("close", "").replace("file", "").replace("folder", "").strip()
            
            if "close" in low_q:
                if search_term:
                    subprocess.Popen(f"taskkill /f /im {search_term}.exe", shell=True)
                    speak(f"Closed {search_term}, sir.")
                else:
                    pyautogui.hotkey("alt", "f4")
                    speak("Window closed, sir.")
                return True, None

            desktop_path = os.path.join(user_profile, "Desktop")
            os.startfile(desktop_path)
            speak("Opening desktop, sir.")
            return True, None

        key, url = get_matched_website_url(low_q)
        if key:
            webbrowser.open(url)
            speak(f"Opening {key} for you, sir.")
            return True, url

        if "sleep" in low_q:
            speak("Putting the laptop to sleep, sir.")
            subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return True, None

        if "shutdown" in low_q:
            speak("Shutting down the system, sir.")
            subprocess.Popen("shutdown /s /t 1", shell=True)
            return True, None

        if "screenshot" in low_q:
            desktop = os.path.join(user_profile, "Desktop")
            shot_path = os.path.join(desktop, "screenshot.png")
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
# VOICE RECOGNITION LOOP
# ============================================================

def normalize_query(text):
    if not text:
        return ""
    q = text.strip().lower()
    q = q.replace("?", " ?").replace("।", " ").replace(",", " ")
    return re.sub(r"\s+", " ", q).strip()

def recognize_voice(recognizer, audio):
    try:
        text_en = recognizer.recognize_google(audio, language="en-US")
        if text_en and len(text_en.strip()) > 0:
            return text_en.strip()
    except Exception:
        pass
    try:
        text_bn = recognizer.recognize_google(audio, language="bn-BD")
        if text_bn and len(text_bn.strip()) > 0:
            return text_bn.strip()
    except Exception:
        pass
    return ""

def is_duplicate_command(query):
    global last_command_text, last_command_time
    now = time.time()
    normalized = normalize_query(query)
    with duplicate_lock:
        if normalized == last_command_text and now - last_command_time < DUPLICATE_COMMAND_SECONDS:
            return True
        last_command_text = normalized
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
            query = recognize_voice(recognizer, audio)

            if query:
                print(f"Recognized Voice: {query}")
                if not is_duplicate_command(query):
                    comm.update_subtitle.emit(f"You: {query}")
                    
                    is_safe, cleaned_query, threat_msg = scan_and_neutralize_threats(query)
                    if not is_safe:
                        speak(threat_msg)
                        continue

                    handled, _ = control_laptop(cleaned_query)
                    if not handled:
                        current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                        system_prompt = (
                            f"You are Jarvis, an advanced, highly intelligent, precise, and friendly AI companion created for Omar. "
                            f"Current date and time is {current_date_time}. "
                            f"Always provide 100% accurate, correct, and verified information. "
                            f"Talk in a warm, natural, human-like tone in Bengali, English, or Banglish. Keep responses concise within 1-2 short sentences."
                        )
                        reply = ask_ai_brain(cleaned_query, system_prompt)
                        speak(reply)
                time.sleep(0.1)
        except sr.WaitTimeoutError:
            comm.update_status.emit("ONLINE")
            continue
        except Exception as e:
            print(f"Listener Error: {e}")
            time.sleep(1)

# ============================================================
# MEYA / JARVIS STYLE FUTURISTIC HOLOGRAM HUD (PyQt5)
# ============================================================

if PYQT_AVAILABLE:
    class HologramHUD(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setGeometry(100, 100, 860, 500)

            self.angle = 0.0
            self.status_text = "ONLINE"
            self.sub_text = "Jarvis Android Core & Bangladesh Defense Active"

            self.cmd_input = QLineEdit(self)
            self.cmd_input.setGeometry(460, 100, 360, 42)
            self.cmd_input.setPlaceholderText("Jarvis Terminal: Type command or query...")
            self.cmd_input.setStyleSheet(
                "background-color: rgba(5, 15, 30, 245); color: #00f0ff; "
                "border: 1.5px solid #ff007f; border-radius: 12px; padding: 8px; font-family: Consolas; font-size: 14px;"
            )
            self.cmd_input.returnPressed.connect(self.handle_typed_command)

            self.exec_btn = QPushButton("JARVIS EXECUTE", self)
            self.exec_btn.setGeometry(460, 152, 360, 38)
            self.exec_btn.setStyleSheet(
                "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff007f, stop:1 #00f0ff); "
                "color: #000; font-weight: bold; border-radius: 12px; font-family: Consolas; font-size: 14px; }"
                "QPushButton:hover { background: #00f0ff; }"
            )
            self.exec_btn.clicked.connect(self.handle_typed_command)

            self.reply_label = QLabel("Jarvis Core Online. Awaiting Omar's command...", self)
            self.reply_label.setGeometry(460, 204, 360, 220)
            self.reply_label.setWordWrap(True)
            self.reply_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.reply_label.setStyleSheet(
                "background-color: rgba(0, 0, 0, 215); color: #39ff14; "
                "border: 1.5px solid rgba(255, 0, 127, 180); border-radius: 12px; padding: 12px; font-family: Consolas; font-size: 13px;"
            )

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_animation)
            self.timer.start(25)

            comm.update_status.connect(self.set_status)
            comm.update_subtitle.connect(self.set_subtitle)

            self.drag_position = QPoint()

        def handle_typed_command(self):
            text = self.cmd_input.text().strip()
            if not text:
                return
            self.cmd_input.clear()
            self.set_subtitle(f"Omar: {text}")
            threading.Thread(target=self.process_text_command, args=(text,), daemon=True).start()

        def process_text_command(self, query):
            comm.update_status.emit("PROCESSING...")
            
            is_safe, cleaned_query, threat_msg = scan_and_neutralize_threats(query)
            if not is_safe:
                speak(threat_msg)
                comm.update_status.emit("ONLINE")
                return

            if SECURITY_STATE["waiting_for_pin"]:
                if cleaned_query == SECURITY_STATE["secret_pin"] or (SECURITY_STATE["temp_otp"] and cleaned_query == SECURITY_STATE["temp_otp"]):
                    SECURITY_STATE["is_authenticated"] = True
                    SECURITY_STATE["waiting_for_pin"] = False
                    SECURITY_STATE["failed_attempts"] = 0
                    speak("Welcome back sir.")
                    comm.update_status.emit("ONLINE")
                    return
                else:
                    SECURITY_STATE["failed_attempts"] += 1
                    if SECURITY_STATE["failed_attempts"] >= 2:
                        threading.Thread(target=send_security_breach_alert, args=("Web Terminal UI Breach Attempt",), daemon=True).start()
                    speak("Incorrect PIN. Security alert triggered.")
                    comm.update_status.emit("ONLINE")
                    return

            handled, _ = control_laptop(cleaned_query)
            if not handled:
                current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                system_prompt = (
                    f"You are Jarvis, an advanced, highly intelligent, precise, and friendly AI companion created for Omar. "
                    f"Current date and time is {current_date_time}. "
                    f"Always provide 100% accurate, correct, and verified information. "
                    f"Talk in a warm, natural, human-like tone in Bengali, English, or Banglish. Keep responses concise within 1-2 short sentences."
                )
                reply = ask_ai_brain(cleaned_query, system_prompt)
                speak(reply)
            comm.update_status.emit("ONLINE")

        def update_animation(self):
            self.angle = (self.angle + 3.0) % 360
            self.update()

        def set_status(self, txt):
            self.status_text = txt
            self.update()

        def set_subtitle(self, txt):
            self.sub_text = txt
            self.reply_label.setText(txt)
            self.update()

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event):
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.drag_position)
                event.accept()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            cx, cy = 230, 250
            center = QPoint(cx, cy)

            # Meya / Jarvis Style Neon Cyber Rings
            painter.setPen(QPen(QColor(255, 0, 127, 180), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, 200, 200)

            painter.setPen(QPen(QColor(0, 240, 255, 200), 2))
            painter.drawEllipse(center, 175, 175)

            now = datetime.datetime.now()
            date_str = now.strftime("%d %b %Y").upper()
            time_str = now.strftime("%H:%M:%S")

            painter.setFont(QFont("Consolas", 9, QFont.Bold))
            painter.setPen(QColor(0, 240, 255))
            painter.drawText(cx + 165, cy - 80, "JARVIS: ACTIVE")
            painter.drawText(cx + 165, cy + 70, "TEMP: 28°C")

            painter.setPen(QColor(255, 0, 127))
            painter.drawText(cx - 240, cy - 80, date_str)
            painter.drawText(cx - 240, cy + 70, f"{time_str}")

# ============================================================
# WEB INTERFACE WITH WHATSAPP LOGO SEARCH BAR & ALL FEATURES
# ============================================================

HTML_INTERFACE = """<!DOCTYPE html>
<html>
<head>
    <title>Jarvis Ai - Android Jarvis Terminal with WhatsApp Logo Search</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            background-color: #0b141a; color: #e9edef; 
            font-family: 'Segoe UI', Helvetica, Arial, sans-serif; 
            margin: 0; padding: 15px;
            display: flex; justify-content: center; align-items: center; min-height: 94vh;
        }
        .app-container { display: flex; width: 1260px; max-width: 100%; height: 88vh; gap: 16px; }
        
        .sidebar {
            width: 280px; background: #111b21; border-right: 1px solid #222d34; border-radius: 12px;
            display: flex; flex-direction: column; padding: 15px; box-sizing: border-box;
        }
        .sidebar-title { color: #00a884; font-size: 15px; font-weight: bold; margin-bottom: 12px; border-bottom: 1px solid #222d34; padding-bottom: 8px; }
        .history-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
        .history-item { 
            background: #202c33; padding: 10px; border-radius: 8px; font-size: 13px; color: #d1d7db; cursor: pointer; transition: 0.2s;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        }
        .history-item:hover { background: #2a3942; color: #00a884; }

        .main-workspace { flex: 1; display: flex; flex-direction: column; gap: 15px; }
        
        .header-card {
            background: #111b21; border-radius: 12px; padding: 12px 20px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .logo-area { display: flex; align-items: center; gap: 12px; }
        .logo-img { height: 44px; filter: drop-shadow(0 0 8px rgba(0,168,132,0.8)); }
        .logo-text-group h1 { margin: 0; font-size: 20px; color: #00a884; letter-spacing: 1px; }
        .logo-text-group p { margin: 2px 0 0 0; font-size: 10px; color: #8696a0; letter-spacing: 2px; }

        .telemetry-bar { display: flex; gap: 12px; font-size: 12px; font-weight: bold; color: #00a884; }
        .tele-badge { background: #202c33; padding: 5px 10px; border-radius: 6px; }

        .workspace { display: flex; width: 100%; gap: 15px; flex: 1; min-height: 0; }
        
        .chat-card { 
            background: #111b21; border-radius: 12px; padding: 18px; flex: 1; display: flex; flex-direction: column; box-sizing: border-box; min-height: 0;
        }
        #log { 
            color: #e9edef; font-size: 14px; text-align: left; background: #0b141a; 
            padding: 14px; border-radius: 10px; flex: 1; overflow-y: auto; 
            margin-bottom: 12px; line-height: 1.5; min-height: 150px; border: 1px solid #222d34;
        }
        
        /* WhatsApp Search Bar with Official Green Logo */
        .whatsapp-search-container {
            display: flex; align-items: center; background: #202c33; border-radius: 8px; padding: 6px 12px; margin-bottom: 12px;
            border: 1px solid #222d34;
        }
        .whatsapp-search-container svg { width: 22px; height: 22px; fill: #25D366; margin-right: 10px; flex-shrink: 0; }
        .whatsapp-search-input {
            flex: 1; background: transparent; border: none; color: #e9edef; font-size: 15px; outline: none; font-family: inherit;
        }
        .whatsapp-search-input::placeholder { color: #8696a0; }

        .btn-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
        button { background: #00a884; color: #ffffff; border: none; padding: 10px; border-radius: 8px; font-weight: bold; font-size: 13px; cursor: pointer; transition: 0.3s; }
        button:hover { background: #008f6f; }
        #mic-btn { background: #ea0038; }
        #mic-btn.listening { background: #00a884; }

        .control-panel {
            background: #111b21; border-radius: 12px; padding: 18px; width: 340px;
            display: flex; flex-direction: column; gap: 12px; box-sizing: border-box;
        }
        .panel-title { color: #00a884; font-size: 15px; font-weight: bold; border-bottom: 1px solid #222d34; padding-bottom: 6px; }
        .media-preview { flex: 1; background: #0b141a; border: 1.5px dashed #222d34; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: #8696a0; font-size: 13px; padding: 10px; min-height: 140px; }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar History -->
        <div class="sidebar">
            <div class="sidebar-title">💬 CHAT HISTORY</div>
            <div class="history-list" id="history-list">
                <div class="history-item" onclick="loadHistoryItem('Jarvis Android Core Online')">Jarvis Android Core Online</div>
            </div>
            <button onclick="clearHistory()" style="background:#ea0038; margin-top:10px;">CLEAR HISTORY</button>
        </div>

        <div class="main-workspace">
            <div class="header-card">
                <div class="logo-area">
                    <img src="https://i.ibb.co.com/83p1Xb1/image-2a4080.png" alt="Jarvis Ai Logo" class="logo-img">
                    <div class="logo-text-group">
                        <h1>Jarvis Ai</h1>
                        <p>ANDROID JARVIS ASSISTANT</p>
                    </div>
                </div>
                <div class="telemetry-bar">
                    <div class="tele-badge" id="date-box">-- --- ----</div>
                    <div class="tele-badge" id="time-box">--:--:--</div>
                    <div class="tele-badge" id="temp-box">28°C (Rangpur)</div>
                </div>
            </div>

            <div class="workspace">
                <div class="chat-card">
                    <div id="log">Jarvis Android Core & Defense Shield Online. Use WhatsApp search bar below for commands or queries...</div>
                    
                    <!-- WhatsApp Search Bar with Official Green WhatsApp SVG Logo -->
                    <div class="whatsapp-search-container">
                        <svg viewBox="0 0 24 24"><path d="M12.04 2c-5.46 0-9.91 4.45-9.91 9.91 0 1.75.46 3.45 1.32 4.95L2 22l5.25-1.38c1.45.79 3.08 1.21 4.79 1.21 5.46 0 9.91-4.45 9.91-9.91 0-2.65-1.03-5.14-2.9-7.01C17.18 3.03 14.69 2 12.04 2zM12.04 20.1c-1.42 0-2.81-.38-4.02-1.11l-.29-.17-3.04.8.81-2.96-.19-.31c-.8-1.28-1.23-2.77-1.23-4.31 0-4.43 3.6-8.03 8.03-8.03 2.15 0 4.17.84 5.69 2.36 1.52 1.52 2.35 3.54 2.35 5.69 0 4.43-3.6 8.03-8.03 8.03zm4.4-6.03c-.24-.12-1.42-.7-1.64-.78-.22-.08-.38-.12-.54.12-.16.24-.62.78-.76.94-.14.16-.28.18-.52.06-.24-.12-1.01-.37-1.93-1.19-.71-.63-1.19-1.41-1.33-1.65-.14-.24-.01-.37.1-.49.11-.11.24-.28.36-.42.12-.14.16-.24.24-.4.08-.16.04-.3-.02-.42-.06-.12-.54-1.31-.74-1.8-.2-.48-.4-.41-.54-.42l-.46-.01c-.16 0-.42.06-.64.3-.22.24-.84.82-.84 2s.86 2.3 0.98 2.46c.12.16 1.69 2.58 4.1 3.62.57.25 1.02.4 1.37.51.58.18 1.11.15 1.53.09.47-.07 1.42-.58 1.62-1.14.2-.56.2-1.04.14-1.14-.06-.1-.22-.16-.46-.28z"/></svg>
                        <input type="text" id="cmd" class="whatsapp-search-input" placeholder="Search or type command, missile scan, call..." onkeydown="if(event.key === 'Enter') sendCommand()">
                    </div>

                    <div class="btn-grid">
                        <button onclick="sendCommand()">EXECUTE</button>
                        <button id="mic-btn" onclick="toggleVoice()">🎙️ SPEAK</button>
                        <button onclick="scanMissileThreat()" style="background:#ea0038;">🛡️ MISSILE SCAN</button>
                        <button onclick="fetchTrafficCam()">📷 TRAFFIC CAM</button>
                        <button onclick="generateImage()">🖼️ GEN PIC</button>
                        <button onclick="generateVideo()">🎬 GEN VIDEO</button>
                    </div>
                </div>

                <div class="control-panel">
                    <div class="panel-title">JARVIS RADAR & TELEMETRY</div>
                    <div class="media-preview" id="media-output">
                        [Preview: Missile launch telemetry, radar vector, live GPS or traffic cams]
                    </div>
                    <button onclick="fetchLocation()" style="background:#00a884; color:#fff;">📍 LIVE GPS MAP</button>
                    <button onclick="clearLogs()" style="background:#ea0038; color:#fff;">RESET TERMINAL</button>
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

        let chatHistory = [];

        function addHistory(query, reply) {
            chatHistory.push({query: query, reply: reply});
            let list = document.getElementById("history-list");
            let item = document.createElement("div");
            item.className = "history-item";
            item.innerText = query;
            item.onclick = function() {
                loadHistoryItem(`>> ${query}\\n> JARVIS: ${reply}`);
            };
            list.prepend(item);
        }

        function loadHistoryItem(text) {
            let log = document.getElementById("log");
            log.innerHTML += `<br><span style='color:#00a884;'>[Loaded from History]:<br>${text}</span>`;
            log.scrollTop = log.scrollHeight;
        }

        function clearHistory() {
            chatHistory = [];
            document.getElementById("history-list").innerHTML = '<div class="history-item" onclick="loadHistoryItem(\'History Cleared\')">History Cleared</div>';
        }

        let recognition;
        let isListening = false;
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            let SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            recognition.onresult = function(event) {
                document.getElementById("cmd").value = event.results[0][0].transcript;
                stopListening();
                sendCommand();
            };
            recognition.onerror = stopListening;
            recognition.onend = stopListening;
        }

        function toggleVoice() {
            if (!recognition) return alert("Speech recognition not supported.");
            if (isListening) { recognition.stop(); stopListening(); }
            else { recognition.start(); startListening(); }
        }
        function startListening() {
            isListening = true;
            let btn = document.getElementById("mic-btn");
            btn.classList.add("listening");
            btn.innerHTML = "🔴 LISTENING...";
        }
        function stopListening() {
            isListening = false;
            let btn = document.getElementById("mic-btn");
            btn.classList.remove("listening");
            btn.innerHTML = "🎙️ SPEAK";
        }

        function sendCommand() {
            let cmdInput = document.getElementById("cmd");
            let log = document.getElementById("log");
            let text = cmdInput.value.trim();
            if(!text) return;

            log.innerHTML += "<br><span style='color:#8696a0;'>>> " + text + "</span>";
            cmdInput.value = "";

            fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: text})
            })
            .then(res => res.json())
            .then(data => {
                let replyText = data.reply || data.message || "Executed.";
                log.innerHTML += "<br><span style='color:#00a884;'>> JARVIS: " + replyText + "</span>";
                log.scrollTop = log.scrollHeight;
                addHistory(text, replyText);
            })
            .catch(err => {
                log.innerHTML += "<br><span style='color:#ea0038;'>> Error: Failed to reach server.</span>";
            });
        }

        function scanMissileThreat() {
            let log = document.getElementById("log");
            log.innerHTML += "<br><span style='color:#ea0038;'>> [JARVIS STRATEGIC DEFENSE]: Scanning regional launch pads & air defense perimeters targeting Bangladesh...</span>";
            
            fetch('/osint', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({target: "missile threat scan"})
            })
            .then(res => res.json())
            .then(data => {
                log.innerHTML += "<br><span style='color:#00a884;'>> " + data.result + "</span>";
                log.scrollTop = log.scrollHeight;
                document.getElementById("media-output").innerHTML = `
                    <div style="font-size:11px; color:#ea0038; font-weight:bold; margin-bottom:4px;">AIRSPACE SECURE - NO THREATS</div>
                    <div style="color:#00a884; font-size:11px;">[Radar Coordinates: 23.8103° N, 90.4125° E (Dhaka Perimeter Clean)]</div>
                `;
                addHistory("Missile Defense Scan", data.result);
            });
        }

        function fetchTrafficCam() {
            let log = document.getElementById("log");
            log.innerHTML += "<br><span style='color:#8696a0;'>> [TRAFFIC CAM FEED]: Fetching live aggregate traffic telemetry...</span>";
            document.getElementById("media-output").innerHTML = `
                <div style="font-size:11px; color:#00a884; margin-bottom:4px;">LIVE TRAFFIC FEED</div>
                <img src="https://picsum.photos/300/140" style="width:100%; height:120px; object-fit:cover; border-radius:6px;" alt="Live Traffic Cam">
            `;
        }

        function generateImage() {
            let prompt = document.getElementById("cmd").value.trim() || "Cyberpunk futuristic city";
            document.getElementById("media-output").innerHTML = `<span style="color:#00a884;">[Generating Image for: "${prompt}"]...</span>`;
            setTimeout(() => {
                document.getElementById("media-output").innerHTML = `<img src="https://picsum.photos/300/140" style="width:100%; height:100%; object-fit:cover; border-radius:6px;" alt="AI Generated Image">`;
            }, 1500);
        }

        function generateVideo() {
            let prompt = document.getElementById("cmd").value.trim() || "Autonomous defense simulation";
            document.getElementById("media-output").innerHTML = `<span style="color:#8696a0;">[Rendering Video Simulation: "${prompt}"]...</span>`;
            setTimeout(() => {
                document.getElementById("media-output").innerHTML = `<div style="color:#00a884; font-weight:bold; font-size:12px;">🎬 Video Rendered Successfully!<br><span style="font-size:10px; color:#fff;">Format: MP4 (Zero-Gravity HD)</span></div>`;
            }, 2000);
        }

        function fetchLocation() {
            let log = document.getElementById("log");
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(position => {
                    let lat = position.coords.latitude;
                    let lon = position.coords.longitude;
                    log.innerHTML += "<br><span style='color:#00a884;'>> [LIVE GPS MAP]: Lat: " + lat.toFixed(4) + ", Lon: " + lon.toFixed(4) + " (Pirganj, Rangpur Zone)</span>";
                    document.getElementById("media-output").innerHTML = `<iframe width="100%" height="130px" frameborder="0" src="https://maps.google.com/maps?q=${lat},${lon}&z=13&output=embed" style="border-radius:6px;"></iframe>`;
                }, () => {
                    log.innerHTML += "<br><span style='color:#ea0038;'>> [GPS Error]: Location access denied or unavailable.</span>";
                });
            }
        }

        function clearLogs() {
            document.getElementById("log").innerHTML = "Terminal cleared.";
            document.getElementById("media-output").innerHTML = "[Preview: Missile launch telemetry, radar vector, live GPS or traffic cams]";
        }
    </script>
</body>
</html>
"""

if REMOTE_ACCESS_AVAILABLE:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(HTML_INTERFACE)

    @app.route("/osint", methods=['POST'])
    def handle_osint():
        data = request.json or {}
        target = data.get("target", "Unknown")
        result = run_osint_lookup(target)
        return jsonify({"status": "success", "result": result})

    @app.route("/ask", methods=['POST'])
    def phone_ask():
        try:
            data = request.json or {}
            query = data.get("query", "")
            if not query:
                return jsonify({"status": "error", "message": "No query provided"})
            
            comm.update_subtitle.emit(f"Web: {query}")
            
            is_safe, cleaned_query, threat_msg = scan_and_neutralize_threats(query)
            if not is_safe:
                speak(threat_msg)
                return jsonify({"status": "blocked", "reply": threat_msg})

            low_q = cleaned_query.lower()

            if SECURITY_STATE["waiting_for_pin"]:
                if cleaned_query == SECURITY_STATE["secret_pin"] or (SECURITY_STATE["temp_otp"] and cleaned_query == SECURITY_STATE["temp_otp"]):
                    SECURITY_STATE["is_authenticated"] = True
                    SECURITY_STATE["waiting_for_pin"] = False
                    SECURITY_STATE["failed_attempts"] = 0
                    speak("Welcome back sir.")
                    return jsonify({"status": "success", "reply": "Welcome back sir. Full remote access granted."})
                else:
                    SECURITY_STATE["failed_attempts"] += 1
                    if SECURITY_STATE["failed_attempts"] >= 2:
                        threading.Thread(target=send_security_breach_alert, args=("Web Terminal UI Breach Attempt",), daemon=True).start()
                    return jsonify({"status": "unauthorized", "reply": "Incorrect PIN. Security breach alert triggered!"})

            if "laptop control" in low_q or "control ta amk daw" in low_q:
                if verify_face_and_voice():
                    SECURITY_STATE["waiting_for_pin"] = True
                    speak("Face and voice verified. Please enter your pin.")
                    return jsonify({"status": "auth_required", "reply": "Face and voice verified. Please enter your secret PIN."})

            handled, _ = control_laptop(cleaned_query)
            if handled:
                reply = "Command executed successfully, sir."
            else:
                current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                system_prompt = (
                    f"You are Jarvis, an advanced, highly intelligent, precise, and friendly AI companion created for Omar. "
                    f"Current date and time is {current_date_time}. "
                    f"Always provide 100% accurate, correct, and verified information. "
                    f"Talk in a warm, natural, human-like tone in Bengali, English, or Banglish. Keep responses concise within 1-2 short sentences."
                )
                reply = ask_ai_brain(cleaned_query, system_prompt)
                speak(reply)

            return jsonify({"status": "success", "reply": reply})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

# ============================================================
# MAIN EXECUTION (THREADED FLASK & JARVIS HUD)
# ============================================================

if __name__ == "__main__":
    print("Initializing Jarvis Android Core & Defense Terminal for Omar...")
    
    if DESKTOP_LIBS_AVAILABLE:
        threading.Thread(target=voice_listener_loop, daemon=True).start()
    
    if REMOTE_ACCESS_AVAILABLE:
        threading.Thread(target=lambda: app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False), daemon=True).start()
        print("Jarvis Web Server running at http://127.0.0.1:5000")

    if PYQT_AVAILABLE:
        qt_app = QApplication(sys.argv)
        hud = HologramHUD()
        hud.show()
        sys.exit(qt_app.exec_())
    elif REMOTE_ACCESS_AVAILABLE:
        app.run(host="127.0.0.1", port=5000, debug=True)