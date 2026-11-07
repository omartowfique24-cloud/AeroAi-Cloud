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

# Google Gemini API Import (Stable Legacy SDK for Cloud Execution)
import google.generativeai as genai

# Safe Desktop Libraries Import (Won't crash on Cloud)
try:
    import pyautogui
    import pygame
    import speech_recognition as sr
    DESKTOP_LIBS_AVAILABLE = True
except ImportError:
    DESKTOP_LIBS_AVAILABLE = False

# Flask Import for Remote Web Interface
try:
    from flask import Flask, request, jsonify, render_template_string
    REMOTE_ACCESS_AVAILABLE = True
except ImportError:
    REMOTE_ACCESS_AVAILABLE = False

# ------------------------------------------------------------
# UTF-8 OUTPUT
# ------------------------------------------------------------
try:
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )
except Exception:
    pass

# ------------------------------------------------------------
# PYQT5 IMPORTS (Safe for Cloud)
# ------------------------------------------------------------
try:
    from PyQt5.QtCore import QObject, Qt, pyqtSignal, QPoint, QTimer
    from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QBrush
    from PyQt5.QtWidgets import (
        QApplication,
        QLabel,
        QMainWindow,
        QVBoxLayout,
        QWidget,
    )
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_MODEL = os.environ.get("AERO_OLLAMA_MODEL", "llama3")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

VOICE_TIMEOUT = 5
VOICE_PHRASE_LIMIT = 8
DUPLICATE_COMMAND_SECONDS = 1.5
# ============================================================
# UNIFIED AI BRAIN (Direct & Stable Gemini for Cloud)
# ============================================================

def ask_ai_brain(prompt, system_prompt=""):
    """
    Direct and reliable Google Gemini API call for Cloud execution.
    """
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Using the stable and universal gemini-2.5-flash model
            model = genai.GenerativeModel("gemini-2.5-flash")
            full_prompt = f"{system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
            response = model.generate_content(full_prompt)
            
            if response and response.text:
                return response.text
            return "Sorry Omar sir, empty response from Gemini cloud."
            
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return f"Gemini Error: {str(e)}"
    else:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
            return response["message"]["content"]
        except Exception as e:
            print(f"Ollama Error: {e}")
            return f"Ollama Error: {str(e)}"
# ============================================================
# GLOBAL OBJECTS
# ============================================================

command_queue = queue.Queue()
command_worker_running = True
processing_event = threading.Event()
tts_lock = threading.Lock()

duplicate_lock = threading.Lock()
last_command_text = ""
last_command_time = 0.0

# ============================================================
# COMMUNICATION SIGNALS
# ============================================================

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
# INITIALIZE AUDIO
# ============================================================

AUDIO_READY = False
if DESKTOP_LIBS_AVAILABLE:
    try:
        pygame.mixer.init()
        AUDIO_READY = True
    except Exception as e:
        print(f"Audio initialization error: {e}")

# ============================================================
# TEXT / SPEECH HELPERS
# ============================================================

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
            is_bangla = contains_bangla(text)
            language = "bn" if is_bangla else "en"
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
# WEBSITE OPENING FUNCTION
# ============================================================

def open_website(query):
    query = query.lower()
    websites = {
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
        "gemini": "https://gemini.google.com",
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
    
    matched = False
    for key, url in websites.items():
        if key in query:
            if DESKTOP_LIBS_AVAILABLE:
                webbrowser.open(url)
            speak(f"Opening {key}, sir.")
            matched = True
            break
    return matched

# ============================================================
# DESKTOP CONTROL (Safe for Cloud)
# ============================================================

def control_laptop(query_text):
    if not DESKTOP_LIBS_AVAILABLE or os.environ.get("RENDER"):
        return False

    low_q = query_text.lower().strip()
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))

    try:
        if "graphics" in low_q or "grafix" in low_q:
            if any(w in low_q for w in ["on", "start", "chalu", "enable", "open", "kholo", "khulo"]):
                os.system("start ms-settings:display-advancedgraphics")
                speak("Graphics settings opened, sir.")
                return True

        if any(k in low_q for k in ["close tab", "tab close"]):
            pyautogui.hotkey("ctrl", "w")
            speak("Tab closed, sir.")
            return True

        if "close window" in low_q or "window close" in low_q or "bondho koro" in low_q or "close this" in low_q:
            pyautogui.hotkey("alt", "f4")
            speak("Window closed, sir.")
            return True

        if "screenshot" in low_q:
            desktop = os.path.join(user_profile, "Desktop")
            shot_path = os.path.join(desktop, "screenshot.png")
            pyautogui.screenshot(shot_path)
            speak("Screenshot saved on Desktop, sir.")
            return True

        if not "close" in low_q:
            if open_website(low_q):
                return True

        if "volume up" in low_q or "increase volume" in low_q:
            pyautogui.press("volumeup", presses=5, interval=0.05)
            speak("Volume increased, sir.")
            return True

        if "volume down" in low_q or "decrease volume" in low_q:
            pyautogui.press("volumedown", presses=5, interval=0.05)
            speak("Volume decreased, sir.")
            return True

        if "mute" in low_q:
            pyautogui.press("volumemute")
            speak("Muted, sir.")
            return True

        if "lock pc" in low_q or "lock laptop" in low_q:
            speak("Locking the system, sir.")
            subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
            return True

        apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "chrome.exe",
            "cmd": "cmd.exe",
            "vscode": "code",
        }

        if not "close" in low_q:
            for app_name, executable in apps.items():
                if app_name in low_q:
                    subprocess.Popen(executable, shell=True)
                    speak(f"Opening {app_name}, sir.")
                    return True
    except Exception as e:
        print(f"Desktop Control Error: {e}")

    return False

# ============================================================
# NORMALIZATION & SPEECH RECOGNITION
# ============================================================

def normalize_query(text):
    if not text:
        return ""
    q = text.strip().lower()
    q = q.replace("?", " ?").replace("।", " ").replace(",", " ")
    replacements = {
        "khulo": "open", "kholo": "open", "khol": "open", "khul": "open",
        "chalu koro": "start", "bondho koro": "close",
        "koyta baje": "time", "ajker tarikh": "date",
    }
    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        q = q.replace(old, new)
    q = re.sub(r"\s+", " ", q).strip()
    return q

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
                    
                    handled = control_laptop(query)
                    if not handled:
                        try:
                            current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                            system_prompt = (
                                f"You are Aero AI, an advanced AI companion created for Omar. "
                                f"Current date and time is {current_date_time}. "
                                f"You understand and reply fluently in Bengali, English, and Banglish (Bengali written in English letters). "
                                f"Do NOT translate the user's question. Directly answer what the user is asking in a friendly, human-like, conversational tone within 1-2 short sentences."
                            )
                            reply = ask_ai_brain(query, system_prompt)
                            speak(reply)
                        except Exception as e:
                            print(f"AI Brain Error: {e}")
                            speak("Sorry Omar sir, error processing request.")
                time.sleep(0.1)
        except sr.WaitTimeoutError:
            comm.update_status.emit("STARK HUD // ONLINE")
            continue
        except Exception as e:
            print(f"Listener Error: {e}")
            time.sleep(1)

# ============================================================
# STARK INDUSTRIES / JARVIS HOLOGRAM HUD GUI (PyQt5)
# ============================================================

if PYQT_AVAILABLE:
    class HologramHUD(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.setGeometry(100, 100, 420, 420)

            self.angle = 0
            self.status_text = "STARK HUD // ONLINE"
            self.sub_text = "Aero is ready, Omar sir."

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_animation)
            self.timer.start(30)

            comm.update_status.connect(self.set_status)
            comm.update_subtitle.connect(self.set_subtitle)

            self.drag_position = QPoint()

        def update_animation(self):
            self.angle = (self.angle + 2) % 360
            self.update()

        def set_status(self, txt):
            self.status_text = txt
            self.update()

        def set_subtitle(self, txt):
            self.sub_text = txt
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

            width = self.width()
            height = self.height()
            center = QPoint(width // 2, height // 2)

            painter.setPen(QPen(QColor(0, 240, 255, 120), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, 190, 190)

            painter.save()
            painter.translate(center)
            painter.rotate(self.angle)
            painter.setPen(QPen(QColor(0, 255, 150, 180), 3, Qt.SolidLine))
            painter.drawArc(-160, -160, 320, 320, 45 * 16, 120 * 16)
            painter.drawArc(-160, -160, 320, 320, 225 * 16, 90 * 16)
            painter.restore()

            painter.save()
            painter.translate(center)
            painter.rotate(-self.angle * 1.5)
            painter.setPen(QPen(QColor(0, 240, 255, 200), 2, Qt.DotLine))
            painter.drawEllipse(-120, -120, 240, 240)
            painter.restore()

            core_brush = QBrush(QColor(0, 240, 255, 30))
            painter.setBrush(core_brush)
            painter.setPen(QPen(QColor(0, 240, 255, 220), 2))
            painter.drawEllipse(center, 80, 80)

            painter.setPen(QColor(0, 240, 255))
            painter.setFont(QFont("Consolas", 9, QFont.Bold))
            painter.drawText(center.x() - 55, center.y() - 25, "STARK EXPO")
            
            painter.setPen(QColor(57, 255, 20))
            painter.setFont(QFont("Consolas", 8))
            painter.drawText(center.x() - 45, center.y() - 5, "AEPO AI")

            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            painter.drawText(center.x() - 38, center.y() + 20, current_time)

            painter.setPen(QColor(0, 240, 255))
            painter.setFont(QFont("Consolas", 9))
            painter.drawText(20, height - 45, f">> {self.status_text}")

            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 9))
            painter.setBrush(QBrush(QColor(5, 15, 30, 200)))
            painter.setPen(QPen(QColor(0, 240, 255, 100), 1))
            painter.drawRoundedRect(15, height - 35, width - 30, 30, 6, 6)
            painter.drawText(25, height - 15, self.sub_text[:50])

# ============================================================
# MOBILE WEB CONTROL & INTERFACE (FLASK)
# ============================================================

HTML_INTERFACE = """<!DOCTYPE html>
<html>
<head>
    <title>AeRo Ai - Stark HUD</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #030810; color: #00f0ff; font-family: 'Consolas', 'Segoe UI', sans-serif; text-align: center; padding: 10px; margin: 0; overflow-x: hidden; }
        
        /* Stark Expo Top Bar */
        .top-bar { display: flex; justify-content: space-between; align-items: center; max-width: 440px; margin: 0 auto 8px auto; padding: 8px 14px; background: rgba(5, 20, 35, 0.85); border: 1px solid #00f0ff; border-radius: 8px; font-size: 13px; box-shadow: 0 0 15px rgba(0, 240, 255, 0.3); }
        .brand { color: #39ff14; font-weight: bold; text-shadow: 0 0 10px #39ff14; font-size: 17px; letter-spacing: 2px; }
        .info-pill { color: #00f0ff; font-weight: bold; text-shadow: 0 0 5px rgba(0, 240, 255, 0.5); }
        
        /* Hologram Earth Canvas Styles */
        .hud-container { position: relative; width: 120px; height: 120px; margin: 0 auto 8px auto; }
        canvas { width: 120px; height: 120px; border-radius: 50%; box-shadow: 0 0 20px rgba(0, 240, 255, 0.7), inset 0 0 15px rgba(0, 240, 255, 0.5); background: radial-gradient(circle, #011627 0%, #000 100%); }

        /* Main Stark Terminal Card */
        .card { background: rgba(5, 18, 32, 0.92); border: 2px solid #00f0ff; border-radius: 12px; padding: 18px; max-width: 410px; margin: 0 auto; box-shadow: 0 0 25px rgba(0, 240, 255, 0.4), inset 0 0 10px rgba(0, 240, 255, 0.15); }
        h1 { color: #39ff14; font-size: 20px; text-shadow: 0 0 12px #39ff14; margin: 2px 0 10px 0; letter-spacing: 1px; }
        p { margin: 5px 0 12px 0; font-size: 13px; color: #8ab4f8; }
        
        input[type="text"] { width: 85%; padding: 12px; border: 1px solid #00f0ff; background: #000; color: #39ff14; border-radius: 6px; font-size: 15px; margin-bottom: 12px; outline: none; box-shadow: inset 0 0 8px rgba(0, 240, 255, 0.3); }
        input[type="text"]::placeholder { color: rgba(0, 240, 255, 0.4); }

        .btn-group { display: flex; gap: 10px; justify-content: center; }
        button { background: #00f0ff; color: #000; border: none; padding: 10px 16px; border-radius: 6px; font-weight: bold; font-size: 14px; cursor: pointer; transition: 0.3s; flex: 1; box-shadow: 0 0 10px rgba(0, 240, 255, 0.4); }
        button:hover { background: #39ff14; box-shadow: 0 0 15px #39ff14; color: #000; }
        
        #mic-btn { background: #ff0055; color: #fff; box-shadow: 0 0 10px rgba(255, 0, 85, 0.4); }
        #mic-btn.listening { background: #39ff14; color: #000; box-shadow: 0 0 15px #39ff14; }
        
        #log { margin-top: 15px; color: #fff; font-size: 13px; text-align: left; background: #000; padding: 12px; border-radius: 6px; height: 130px; overflow-y: auto; border: 1px solid #39ff14; box-shadow: inset 0 0 10px rgba(57, 255, 20, 0.2); }
    </style>
</head>
<body>
    <!-- Stark Industries HUD Top Bar with AeRo Ai, Date & Temp -->
    <div class="top-bar">
        <div class="brand">AeRo Ai</div>
        <div class="info-pill" id="date-time">Loading...</div>
        <div class="info-pill" id="temp">28°C</div>
    </div>

    <!-- 3D Holographic Rotating Earth -->
    <div class="hud-container">
        <canvas id="earthCanvas" width="120" height="120"></canvas>
    </div>

    <!-- Main Stark Control Card -->
    <div class="card">
        <h1>⚡ STARK AERO HUD</h1>
        <p>Omar Sir's Remote Terminal</p>
        <input type="text" id="cmd" placeholder="Type or speak command..." onkeydown="if(event.key === 'Enter') sendCommand()">
        <br>
        <div class="btn-group">
            <button onclick="sendCommand()">EXECUTE</button>
            <button id="mic-btn" onclick="toggleVoice()">🎙️ SPEAK</button>
        </div>
        <div id="log">System Online...</div>
    </div>

    <script>
        // Live Date & Time Sync
        function updateDateTime() {
            const now = new Date();
            const options = { month: 'short', day: 'numeric' };
            const dateStr = now.toLocaleDateString('en-US', options);
            const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            document.getElementById("date-time").innerText = `${dateStr} | ${timeStr}`;
        }
        setInterval(updateDateTime, 1000);
        updateDateTime();

        // Holographic Rotating Earth Animation (Stark HUD Style)
        const canvas = document.getElementById('earthCanvas');
        const ctx = canvas.getContext('2d');
        let angle = 0;

        function drawEarth() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            let cx = canvas.width / 2;
            let cy = canvas.height / 2;
            let radius = 48;

            // Outer Radar Scan Ring
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 6, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(0, 240, 255, 0.25)';
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Earth Sphere Base
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.fillStyle = '#01192e';
            ctx.fill();
            ctx.strokeStyle = '#00f0ff';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Rotating Longitude Grid Lines
            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.clip();

            ctx.strokeStyle = 'rgba(0, 240, 255, 0.45)';
            ctx.lineWidth = 1.5;

            for (let i = -3; i <= 3; i++) {
                let xOffset = Math.sin(angle + i * 0.7) * radius;
                ctx.beginPath();
                ctx.ellipse(cx + xOffset * 0.5, cy, Math.abs(xOffset), radius, 0, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Latitude Equator Lines
            ctx.beginPath();
            ctx.moveTo(cx - radius, cy - 18); ctx.lineTo(cx + radius, cy - 18);
            ctx.moveTo(cx - radius, cy + 18); ctx.lineTo(cx + radius, cy + 18);
            ctx.strokeStyle = 'rgba(57, 255, 20, 0.45)';
            ctx.stroke();

            ctx.restore();
            angle += 0.025;
            requestAnimationFrame(drawEarth);
        }
        drawEarth();

        let recognition;
        let isListening = false;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            let SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onresult = function(event) {
                let speechText = event.results[0][0].transcript;
                document.getElementById("cmd").value = speechText;
                stopListening();
                sendCommand();
            };

            recognition.onerror = function(event) { stopListening(); };
            recognition.onend = function(event) { stopListening(); };
        }

        function toggleVoice() {
            if (!recognition) {
                alert("Speech recognition not supported in this browser.");
                return;
            }
            if (isListening) {
                recognition.stop();
                stopListening();
            } else {
                recognition.start();
                startListening();
            }
        }

        function startListening() {
            isListening = true;
            let micBtn = document.getElementById("mic-btn");
            micBtn.classList.add("listening");
            micBtn.innerHTML = "🔴 LISTENING...";
        }

        function stopListening() {
            isListening = false;
            let micBtn = document.getElementById("mic-btn");
            micBtn.classList.remove("listening");
            micBtn.innerHTML = "🎙️ SPEAK";
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
                let replyText = data.reply || data.message || "Executed successfully.";
                log.innerHTML += "<br><span style='color:#39ff14;'>AeRo Ai: " + replyText + "</span>";
                log.scrollTop = log.scrollHeight;
            })
            .catch(err => {
                log.innerHTML += "<br><span style='color:red;'>Error connecting to server.</span>";
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
            
            handled = control_laptop(query)
            if not handled:
                current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                system_prompt = (
                    f"You are AeRo Ai, an advanced AI companion created for Omar. "
                    f"Current date and time is {current_date_time}. "
                    f"You understand and reply fluently in Bengali, English, and Banglish (Bengali written in English letters). "
                    f"Do NOT translate the user's question. Directly answer what the user is asking in a friendly, human-like, conversational tone within 1-2 short sentences."
                )
                reply = ask_ai_brain(query, system_prompt)
                speak(reply)
                return jsonify({"status": "success", "reply": reply})
            else:
                return jsonify({"status": "success", "reply": f"Command '{query}' executed successfully."})
        except Exception as e:
            print(f"Phone Ask Error: {e}")
            try:
                reply = ask_ai_brain(query, "You are AeRo Ai, answer helpfully in 1-2 sentences.")
                return jsonify({"status": "success", "reply": reply})
            except Exception as ex:
                return jsonify({"status": "error", "message": str(ex)}), 500

def run_flask_server(port):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ============================================================
# MAIN APPLICATION EXECUTION
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    
    if os.environ.get("RENDER") or GEMINI_API_KEY:
        print(f"Starting AeRo Ai Cloud Web Server on port {port}...")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    else:
        if REMOTE_ACCESS_AVAILABLE:
            flask_thread = threading.Thread(target=run_flask_server, args=(port,), daemon=True)
            flask_thread.start()
            print(f"Flask Web Interface available at: http://127.0.0.1:{port}")

        if PYQT_AVAILABLE:
            qt_app = QApplication(sys.argv)
            voice_thread = threading.Thread(target=voice_listener_loop, daemon=True)
            voice_thread.start()

            hud = HologramHUD()
            hud.show()
            speak("Stark holographic HUD initialized, Omar sir.")
            sys.exit(qt_app.exec_())
        else:
            print("Running in console web-server mode.")
            run_flask_server(port)