import datetime
import io
import math
import os
import queue
import re
import subprocess
import sys
import threading
import time
import webbrowser
from gtts import gTTS
import ollama

# Safe Desktop Libraries Import
try:
    import pyautogui
    import pygame
    import speech_recognition as sr
    DESKTOP_LIBS_AVAILABLE = True
except ImportError:
    DESKTOP_LIBS_AVAILABLE = False

# Flask Import for Local Web Interface
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
    from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush
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
# CONFIGURATION (100% LOCAL)
# ============================================================

OLLAMA_MODEL = os.environ.get("AERO_OLLAMA_MODEL", "llama3")
VOICE_TIMEOUT = 5
VOICE_PHRASE_LIMIT = 8
DUPLICATE_COMMAND_SECONDS = 1.5

# ============================================================
# LOCAL AI BRAIN (OLLAMA ONLY)
# ============================================================

def ask_ai_brain(prompt, system_prompt=""):
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        print(f"Ollama Error: {e}")
        return f"Local AI Error: {str(e)} (Check if Ollama is running)"

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
# AUDIO & TTS
# ============================================================

AUDIO_READY = False
if DESKTOP_LIBS_AVAILABLE:
    try:
        pygame.mixer.init()
        AUDIO_READY = True
    except Exception as e:
        print(f"Audio initialization error: {e}")

def contains_bangla(text):
    return any("\u0980" <= c <= "\u09FF" for c in text)

def speak_background(text):
    if not text or not AUDIO_READY:
        return
    text = str(text).strip()
    if not text:
        return

    with tts_lock:
        filename = None
        try:
            language = "bn" if contains_bangla(text) else "en"
            tts = gTTS(text=text, lang=language, slow=False)
            filename = os.path.join(
                os.getcwd(),
                f"aero_voice_{threading.get_ident()}_{int(time.time() * 1000)}.mp3"
            )
            tts.save(filename)
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.05)

            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
        except Exception as e:
            print(f"TTS Error: {e}")
        finally:
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                except Exception:
                    pass

def speak(text):
    if not text:
        return
    text = str(text).strip()
    print(f"AERO AI: {text}")
    comm.update_subtitle.emit(f"AERO AI: {text}")
    if AUDIO_READY:
        threading.Thread(target=speak_background, args=(text,), daemon=True).start()

# ============================================================
# WEBSITE MAPPING & DESKTOP CONTROL
# ============================================================

WEBSITES_MAP = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "messenger": "https://www.messenger.com",
    "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com",
    "chatgpt": "https://chatgpt.com",
    "github": "https://github.com",
    "stackoverflow": "https://stackoverflow.com",
    "vscode": "https://code.visualstudio.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "twitch": "https://www.twitch.tv",
    "daraz": "https://www.daraz.com.bd",
    "prothomalo": "https://www.prothomalo.com",
    "bikroy": "https://bikroy.com",
    "10minuteschool": "https://10minuteschool.com"
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
        key, url = get_matched_website_url(low_q)
        if key:
            webbrowser.open(url)
            speak(f"Opening {key}, sir.")
            return True, url

        # Specific file or app opening support using os.startfile
        if "open file" in low_q or "file kholo" in low_q:
            # Example target file path (Change or extend based on needs)
            target_file = os.path.join(user_profile, "Desktop", "example.txt")
            if os.path.exists(target_file):
                os.startfile(target_file)
                speak("File opened successfully, sir.")
                return True, None
            else:
                speak("File not found on Desktop, sir.")
                return True, None

        if "graphics" in low_q or "grafix" in low_q:
            if any(w in low_q for w in ["on", "start", "chalu", "enable", "open", "kholo", "khulo"]):
                os.system("start ms-settings:display-advancedgraphics")
                speak("Graphics settings opened, sir.")
                return True, None

        if any(k in low_q for k in ["close tab", "tab close"]):
            pyautogui.hotkey("ctrl", "w")
            speak("Tab closed, sir.")
            return True, None

        if "close window" in low_q or "window close" in low_q or "bondho koro" in low_q or "close this" in low_q:
            pyautogui.hotkey("alt", "f4")
            speak("Window closed, sir.")
            return True, None

        if "screenshot" in low_q:
            desktop = os.path.join(user_profile, "Desktop")
            shot_path = os.path.join(desktop, "screenshot.png")
            pyautogui.screenshot(shot_path)
            speak("Screenshot saved on Desktop, sir.")
            return True, None

        if "volume up" in low_q or "increase volume" in low_q:
            pyautogui.press("volumeup", presses=5, interval=0.05)
            speak("Volume increased, sir.")
            return True, None

        if "volume down" in low_q or "decrease volume" in low_q:
            pyautogui.press("volumedown", presses=5, interval=0.05)
            speak("Volume decreased, sir.")
            return True, None

        if "mute" in low_q:
            pyautogui.press("volumemute")
            speak("Muted, sir.")
            return True, None

        if "lock pc" in low_q or "lock laptop" in low_q:
            speak("Locking the system, sir.")
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            return True, None

        apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "chrome.exe",
            "cmd": "cmd.exe",
            "vscode": "code",
        }

        if "close" not in low_q:
            for app_name, executable in apps.items():
                if app_name in low_q:
                    subprocess.Popen(executable, shell=True)
                    speak(f"Opening {app_name}, sir.")
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
    replacements = {
        "khulo": "open", "kholo": "open", "khol": "open", "khul": "open",
        "chalu koro": "start", "bondho koro": "close",
    }
    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        q = q.replace(old, new)
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
                    
                    key, target_url = get_matched_website_url(query)
                    if key:
                        webbrowser.open(target_url)
                        speak(f"Opening {key}, sir.")
                    else:
                        handled, _ = control_laptop(query)
                        if not handled:
                            current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                            system_prompt = (
                                f"You are AeRo Ai, an advanced AI companion created for Omar. "
                                f"Current date and time is {current_date_time}. "
                                f"Reply fluently in Bengali, English, or Banglish in 1-2 short sentences."
                            )
                            reply = ask_ai_brain(query, system_prompt)
                            speak(reply)
                time.sleep(0.1)
        except sr.WaitTimeoutError:
            comm.update_status.emit("ONLINE")
            continue
        except Exception as e:
            print(f"Listener Error: {e}")
            time.sleep(1)

# ============================================================
# DESKTOP HOLOGRAM HUD (PyQt5)
# ============================================================

if PYQT_AVAILABLE:
    class HologramHUD(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setGeometry(100, 100, 820, 460)

            self.angle = 0.0
            self.status_text = "ONLINE"
            self.sub_text = "AeRo Ai Ready"

            self.cmd_input = QLineEdit(self)
            self.cmd_input.setGeometry(450, 95, 340, 42)
            self.cmd_input.setPlaceholderText("Type your command here, Omar sir...")
            self.cmd_input.setStyleSheet(
                "background-color: rgba(2, 10, 20, 235); color: #39ff14; "
                "border: 1.5px solid #00f0ff; border-radius: 8px; padding: 8px; font-family: Consolas; font-size: 14px;"
            )
            self.cmd_input.returnPressed.connect(self.handle_typed_command)

            self.exec_btn = QPushButton("EXECUTE", self)
            self.exec_btn.setGeometry(450, 147, 340, 36)
            self.exec_btn.setStyleSheet(
                "QPushButton { background-color: #00f0ff; color: #000; font-weight: bold; "
                "border-radius: 8px; font-family: Consolas; font-size: 14px; }"
                "QPushButton:hover { background-color: #39ff14; }"
            )
            self.exec_btn.clicked.connect(self.handle_typed_command)

            self.reply_label = QLabel("System Online (Local Server)...", self)
            self.reply_label.setGeometry(450, 195, 340, 195)
            self.reply_label.setWordWrap(True)
            self.reply_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.reply_label.setStyleSheet(
                "background-color: rgba(0, 0, 0, 195); color: #ffffff; "
                "border: 1.5px solid rgba(57, 255, 20, 160); border-radius: 8px; padding: 10px; font-family: Consolas; font-size: 13px;"
            )

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_animation)
            self.timer.start(35)

            comm.update_status.connect(self.set_status)
            comm.update_subtitle.connect(self.set_subtitle)

            self.drag_position = QPoint()

        def handle_typed_command(self):
            text = self.cmd_input.text().strip()
            if not text:
                return
            self.cmd_input.clear()
            self.set_subtitle(f"You: {text}")
            threading.Thread(target=self.process_text_command, args=(text,), daemon=True).start()

        def process_text_command(self, query):
            comm.update_status.emit("PROCESSING...")
            
            key, target_url = get_matched_website_url(query)
            if key:
                webbrowser.open(target_url)
                speak(f"Opening {key}, sir.")
                comm.update_status.emit("ONLINE")
                return

            handled, _ = control_laptop(query)
            if not handled:
                current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                system_prompt = (
                    f"You are AeRo Ai, an advanced AI companion created for Omar. "
                    f"Current date and time is {current_date_time}. "
                    f"Reply fluently in Bengali, English, or Banglish in 1-2 short sentences."
                )
                reply = ask_ai_brain(query, system_prompt)
                speak(reply)
            comm.update_status.emit("ONLINE")

        def update_animation(self):
            self.angle = (self.angle + 1.5) % 360
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

            cx, cy = 220, 230
            center = QPoint(cx, cy)

            painter.setPen(QPen(QColor(0, 240, 255, 90), 1, Qt.DotLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, 185, 185)

            painter.save()
            painter.translate(center)
            painter.rotate(self.angle * 0.4)
            painter.setPen(QPen(QColor(0, 240, 255, 130), 1.5))
            for i in range(0, 360, 15):
                rad = math.radians(i)
                r1 = 175
                r2 = 185 if i % 45 == 0 else 180
                painter.drawLine(
                    int(math.cos(rad) * r1), int(math.sin(rad) * r1),
                    int(math.cos(rad) * r2), int(math.sin(rad) * r2)
                )
            painter.restore()

            painter.save()
            painter.translate(center)
            painter.rotate(self.angle)
            painter.setPen(QPen(QColor(0, 240, 255, 200), 3, Qt.SolidLine))
            painter.drawArc(-155, -155, 310, 310, 20 * 16, 80 * 16)
            painter.drawArc(-155, -155, 310, 310, 140 * 16, 60 * 16)
            painter.drawArc(-155, -155, 310, 310, 260 * 16, 75 * 16)
            painter.restore()

            painter.save()
            painter.translate(center)
            painter.rotate(-self.angle * 1.3)
            painter.setPen(QPen(QColor(57, 255, 20, 170), 2, Qt.SolidLine))
            painter.drawArc(-135, -135, 270, 270, 45 * 16, 100 * 16)
            painter.drawArc(-135, -135, 270, 270, 225 * 16, 90 * 16)
            painter.restore()

            globe_r = 95
            painter.setBrush(QBrush(QColor(0, 15, 32, 210)))
            painter.setPen(QPen(QColor(0, 240, 255, 220), 2))
            painter.drawEllipse(center, globe_r, globe_r)

            rad_angle = math.radians(self.angle * 1.5)
            step = 7
            for x in range(-globe_r + 6, globe_r - 5, step):
                for y in range(-globe_r + 6, globe_r - 5, step):
                    if x * x + y * y <= (globe_r - 6) ** 2:
                        nx = x + math.sin(rad_angle + y * 0.06) * 18
                        asia_land = math.sin(nx * 0.09) * math.cos(y * 0.09) + math.cos((nx - y) * 0.07)
                        if asia_land > 0.2:
                            alpha = int(150 + 100 * math.sin(rad_angle * 2 + x * 0.1))
                            painter.fillRect(cx + x, cy + y, 3, 3, QColor(0, 255, 204, max(60, min(255, alpha))))
                        elif asia_land > -0.05:
                            painter.fillRect(cx + x, cy + y, 2, 2, QColor(0, 240, 255, 85))

            now = datetime.datetime.now()
            date_str = now.strftime("%d %b %Y").upper()
            time_str = now.strftime("%H:%M:%S")

            painter.setPen(QPen(QColor(0, 240, 255, 160), 1))
            painter.drawLine(cx + 95, cy - 35, cx + 145, cy - 65)
            painter.drawLine(cx + 145, cy - 65, cx + 205, cy - 65)
            painter.drawLine(cx + 95, cy + 35, cx + 145, cy + 65)
            painter.drawLine(cx + 145, cy + 65, cx + 205, cy + 65)
            painter.drawLine(cx - 95, cy - 35, cx - 145, cy - 65)
            painter.drawLine(cx - 145, cy - 65, cx - 210, cy - 65)
            painter.drawLine(cx - 95, cy + 35, cx - 145, cy + 65)
            painter.drawLine(cx - 145, cy + 65, cx - 210, cy + 65)

            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.setPen(QColor(57, 255, 20))
            painter.drawText(cx + 148, cy - 70, "SYS: ON")
            painter.drawText(cx + 148, cy + 60, "TEMP: 28°C")

            painter.setPen(QColor(0, 240, 255))
            painter.drawText(cx - 210, cy - 70, date_str)
            painter.drawText(cx - 210, cy + 60, f"{time_str}")
            painter.drawText(cx - 210, cy + 80, self.status_text[:12])

            painter.setBrush(QBrush(QColor(2, 8, 18, 220)))
            painter.setPen(QPen(QColor(57, 255, 20, 200), 1.5))
            painter.drawRoundedRect(cx - 42, cy - 14, 84, 28, 8, 8)

            painter.setPen(QColor(57, 255, 20))
            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            painter.drawText(cx - 28, cy + 5, "AeRo Ai")

            painter.setBrush(QBrush(QColor(3, 12, 24, 225)))
            painter.setPen(QPen(QColor(0, 240, 255, 180), 1.5))
            painter.drawRoundedRect(435, 50, 370, 360, 14, 14)

            painter.setPen(QColor(57, 255, 20))
            painter.setFont(QFont("Consolas", 11, QFont.Bold))
            painter.drawText(450, 80, "AERO LOCAL TERMINAL")

# ============================================================
# LOCAL WEB INTERFACE (FLASK)
# ============================================================

HTML_INTERFACE = """<!DOCTYPE html>
<html>
<head>
    <title>AeRo Ai - Local HUD</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            background-color: #010612; color: #00f0ff; 
            font-family: 'Consolas', 'Segoe UI', sans-serif; 
            margin: 0; padding: 20px;
            background-image: radial-gradient(circle, rgba(0,240,255,0.08) 1px, transparent 1px);
            background-size: 24px 24px;
            display: flex; justify-content: center; align-items: center; min-height: 92vh;
        }
        .main-wrapper { display: flex; flex-wrap: wrap; justify-content: center; align-items: center; max-width: 1050px; width: 100%; gap: 24px; }
        .hud-panel { 
            display: flex; flex-direction: column; align-items: center; 
            background: rgba(3, 12, 24, 0.94); border: 1.5px solid rgba(0, 240, 255, 0.6); 
            border-radius: 16px; padding: 18px; box-shadow: 0 0 30px rgba(0, 240, 255, 0.3); width: 310px; 
        }
        canvas { width: 250px; height: 250px; border-radius: 50%; background: radial-gradient(circle, #001c38 0%, #00040a 100%); box-shadow: 0 0 25px rgba(0, 240, 255, 0.5); }
        .telemetry-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; width: 100%; margin-top: 14px; }
        .tele-box { background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 8px; padding: 8px; font-size: 13px; color: #39ff14; font-weight: bold; text-align: center; }
        .chat-card { 
            background: rgba(3, 12, 24, 0.96); border: 2px solid #00f0ff; border-radius: 16px; 
            padding: 24px; flex: 1; min-width: 340px; max-width: 620px;
            box-shadow: 0 0 40px rgba(0, 240, 255, 0.4), inset 0 0 15px rgba(0, 240, 255, 0.15); 
            display: flex; flex-direction: column;
        }
        .brand-title { color: #39ff14; font-size: 26px; font-weight: bold; text-shadow: 0 0 14px #39ff14; margin: 0 0 16px 0; letter-spacing: 2px; text-align: left; }
        #log { 
            color: #fff; font-size: 14px; text-align: left; background: #000; 
            padding: 16px; border-radius: 10px; height: 280px; overflow-y: auto; 
            border: 1.5px solid #39ff14; box-shadow: inset 0 0 12px rgba(57, 255, 20, 0.2); 
            margin-bottom: 16px; line-height: 1.5;
        }
        .input-row { display: flex; gap: 10px; margin-bottom: 12px; }
        input[type="text"] { 
            flex: 1; padding: 14px; border: 1.5px solid #00f0ff; background: #000; 
            color: #39ff14; border-radius: 8px; font-size: 16px; outline: none; 
            box-shadow: inset 0 0 8px rgba(0, 240, 255, 0.3); 
        }
        input[type="text"]::placeholder { color: rgba(0, 240, 255, 0.45); }
        .btn-group { display: flex; gap: 12px; }
        button { background: #00f0ff; color: #000; border: none; padding: 13px 18px; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; transition: 0.3s; flex: 1; box-shadow: 0 0 12px rgba(0, 240, 255, 0.4); }
        button:hover { background: #39ff14; box-shadow: 0 0 18px #39ff14; color: #000; }
        #mic-btn { background: #ff0055; color: #fff; box-shadow: 0 0 12px rgba(255, 0, 85, 0.4); }
        #mic-btn.listening { background: #39ff14; color: #000; box-shadow: 0 0 18px #39ff14; }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="hud-panel">
            <canvas id="earthCanvas" width="250" height="250"></canvas>
            <div class="telemetry-grid">
                <div class="tele-box">SYS: ON</div>
                <div class="tele-box">TEMP: 28°C</div>
                <div class="tele-box" id="date-box">-- --- ----</div>
                <div class="tele-box" id="time-box">--:--:--</div>
            </div>
        </div>

        <div class="chat-card">
            <div class="brand-title">AeRo Ai // LOCAL TERMINAL</div>
            <div id="log">System Online (Local Server)...</div>
            <div class="input-row">
                <input type="text" id="cmd" placeholder="Type your command or message here..." onkeydown="if(event.key === 'Enter') sendCommand()">
            </div>
            <div class="btn-group">
                <button onclick="sendCommand()">EXECUTE</button>
                <button id="mic-btn" onclick="toggleVoice()">🎙️ SPEAK</button>
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

        const canvas = document.getElementById('earthCanvas');
        const ctx = canvas.getContext('2d');
        let angle = 0;

        function drawAsianTechEarth() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            let cx = canvas.width / 2;
            let cy = canvas.height / 2;
            let radius = 105;

            ctx.beginPath();
            ctx.arc(cx, cy, radius + 8, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(0, 240, 255, 0.4)';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([5, 4]);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.fillStyle = '#001428';
            ctx.fill();
            ctx.strokeStyle = '#00f0ff';
            ctx.lineWidth = 2.5;
            ctx.stroke();

            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.clip();

            let dotSpacing = 6;
            for (let x = -radius; x <= radius; x += dotSpacing) {
                for (let y = -radius; y <= radius; y += dotSpacing) {
                    if (x*x + y*y <= radius*radius) {
                        let nx = x + Math.sin(angle + y * 0.06) * 20;
                        let asiaLand = Math.sin(nx * 0.09) * Math.cos(y * 0.09) + Math.cos((nx - y) * 0.07);
                        if (asiaLand > 0.18) {
                            let alpha = (0.6 + 0.4 * Math.sin(angle * 3 + x * 0.1));
                            ctx.fillStyle = `rgba(57, 255, 20, ${alpha})`;
                            ctx.fillRect(cx + x, cy + y, 3, 3);
                        } else if (asiaLand > -0.1) {
                            ctx.fillStyle = 'rgba(0, 240, 255, 0.35)';
                            ctx.fillRect(cx + x, cy + y, 2, 2);
                        }
                    }
                }
            }
            ctx.restore();

            ctx.beginPath();
            ctx.arc(cx, cy, 28, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(2, 6, 16, 0.92)';
            ctx.fill();
            ctx.strokeStyle = '#39ff14';
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.fillStyle = '#39ff14';
            ctx.font = 'bold 12px Consolas';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText("AeRo", cx, cy - 5);
            ctx.fillStyle = '#00f0ff';
            ctx.fillText("AI", cx, cy + 9);

            angle += 0.015;
            requestAnimationFrame(drawAsianTechEarth);
        }
        drawAsianTechEarth();

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

            log.innerHTML += "<br><span style='color:#00f0ff;'>>> " + text + "</span>";
            cmdInput.value = "";

            fetch('/ask', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: text})
            })
            .then(res => res.json())
            .then(data => {
                let replyText = data.reply || data.message || "Executed.";
                log.innerHTML += "<br><span style='color:#39ff14;'>AeRo Ai: " + replyText + "</span>";
                log.scrollTop = log.scrollHeight;
                if(data.url) window.open(data.url, '_blank');
            })
            .catch(() => {
                log.innerHTML += "<br><span style='color:red;'>Error connecting to local server.</span>";
            });
        }
    </script>
</body>
</html>"""

if REMOTE_ACCESS_AVAILABLE:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(HTML_INTERFACE)

    @app.route("/ask", methods=["POST"])
    def phone_ask():
        try:
            data = request.json or {}
            query = data.get("query", "")
            if not query:
                return jsonify({"status": "error", "message": "No query provided"}), 400
            
            comm.update_subtitle.emit(f"Web: {query}")
            
            key, target_url = get_matched_website_url(query)
            if key:
                webbrowser.open(target_url)
                speak(f"Opening {key}, sir.")
                return jsonify({
                    "status": "success", 
                    "reply": f"Opening {key} for you, Omar sir!",
                    "url": target_url
                })

            handled, desktop_url = control_laptop(query)
            if handled:
                return jsonify({
                    "status": "success", 
                    "reply": f"Command '{query}' executed successfully.",
                    "url": desktop_url
                })
            
            current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
            system_prompt = (
                f"You are AeRo Ai, an advanced AI companion created for Omar. "
                f"Current date and time is {current_date_time}. "
                f"Reply fluently in Bengali, English, or Banglish in 1-2 short sentences."
            )
            reply = ask_ai_brain(query, system_prompt)
            speak(reply)
            return jsonify({"status": "success", "reply": reply})

        except Exception as e:
            print(f"Ask Error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

def run_flask_server(port):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ============================================================
# MAIN EXECUTION (100% LOCAL)
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    if REMOTE_ACCESS_AVAILABLE:
        flask_thread = threading.Thread(target=run_flask_server, args=(port,), daemon=True)
        flask_thread.start()
        print(f"Local Web Interface available at: http://127.0.0.1:{port}")

    if PYQT_AVAILABLE:
        qt_app = QApplication(sys.argv)
        voice_thread = threading.Thread(target=voice_listener_loop, daemon=True)
        voice_thread.start()

        hud = HologramHUD()
        hud.show()
        speak("Local AeRo Ai initialized, Omar sir.")
        sys.exit(qt_app.exec_())
    else:
        print("Running in console local web-server mode.")
        run_flask_server(port)