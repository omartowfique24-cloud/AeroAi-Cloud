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
import urllib.request
import json
import webbrowser
from gtts import gTTS
import ollama

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
# UNIFIED AI BRAIN (Direct REST API for Cloud, Ollama for Local)
# ============================================================

def ask_ai_brain(prompt, system_prompt=""):
    """
    Uses direct Google Gemini REST API with stable v1 endpoint to bypass 404/440 errors on Cloud.
    """
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            full_text = f"{system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
            
            payload = {
                "contents": [{
                    "parts": [{"text": full_text}]
                }]
            }
            
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req, timeout=12) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidate = result.get("candidates", [{}])[0]
                text = candidate.get("content", {}).get("parts", [{}])[0].get("text", "")
                if text:
                    return text
            return "Sorry Omar sir, empty response from Gemini cloud."
        except Exception as e:
            print(f"Gemini REST Error: {e}")
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
# WEBSITE MAPPING & URL RESOLUTION
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

def get_matched_website_url(query):
    query = query.lower()
    for key, url in WEBSITES_MAP.items():
        if key in query:
            return key, url
    return None, None

# ============================================================
# DESKTOP CONTROL (Safe for Cloud)
# ============================================================

def control_laptop(query_text):
    if not DESKTOP_LIBS_AVAILABLE or os.environ.get("RENDER"):
        return False, None

    low_q = query_text.lower().strip()
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))

    try:
        key, url = get_matched_website_url(low_q)
        if key:
            webbrowser.open(url)
            speak(f"Opening {key}, sir.")
            return True, url

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

        if not "close" in low_q:
            for app_name, executable in apps.items():
                if app_name in low_q:
                    subprocess.Popen(executable, shell=True)
                    speak(f"Opening {app_name}, sir.")
                    return True, None
    except Exception as e:
        print(f"Desktop Control Error: {e}")

    return False, None

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
                    
                    handled, _ = control_laptop(query)
                    if not handled:
                        try:
                            current_date_time = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
                            system_prompt = (
                                f"You are AeRo Ai, an advanced AI companion created for Omar. "
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
            self.status_text = "HUD // ONLINE"
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

            core_brush = QBrush(QColor(0, 240, 255, 30))
            painter.setBrush(core_brush)
            painter.setPen(QPen(QColor(0, 240, 255, 220), 2))
            painter.drawEllipse(center, 80, 80)

            painter.setPen(QColor(57, 255, 20))
            painter.setFont(QFont("Consolas", 10, QFont.Bold))
            painter.drawText(center.x() - 35, center.y() - 5, "AeRo Ai")

            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Consolas", 9, QFont.Bold))
            painter.drawText(center.x() - 32, center.y() + 18, current_time)

# ============================================================
# MOBILE WEB CONTROL & INTERFACE (FLASK) - UPDATED DESIGN
# ============================================================

HTML_INTERFACE = """<!DOCTYPE html>
<html>
<head>
    <title>AeRo Ai - Neural Terminal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { background-color: #02060c; color: #00f0ff; font-family: 'Consolas', 'Segoe UI', sans-serif; text-align: center; padding: 10px; margin: 0; overflow-x: hidden; }
        
        .main-wrapper { display: flex; flex-direction: row; justify-content: center; align-items: flex-start; max-width: 520px; margin: 15px auto; gap: 12px; }
        
        /* Left Side: Earth Map & Temperature Widget */
        .left-panel { display: flex; flex-direction: column; align-items: center; background: rgba(5, 18, 32, 0.9); border: 1px solid #00f0ff; border-radius: 12px; padding: 10px; box-shadow: 0 0 15px rgba(0, 240, 255, 0.3); width: 130px; }
        .globe-container { position: relative; width: 110px; height: 110px; margin-bottom: 8px; }
        
        /* Detailed Earth Map Canvas with Country Borders & Continents */
        canvas { width: 110px; height: 110px; border-radius: 50%; box-shadow: 0 0 15px rgba(0, 240, 255, 0.6), inset 0 0 12px rgba(0, 240, 255, 0.4); background: radial-gradient(circle, #002b49 0%, #000b18 100%); }
        
        .temp-box { background: rgba(0, 240, 255, 0.1); border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 6px; padding: 6px; width: 100%; font-size: 13px; color: #39ff14; font-weight: bold; text-shadow: 0 0 5px #39ff14; }

        /* Right / Center Panel: Typing Pad & Main Terminal */
        .card { background: rgba(5, 18, 32, 0.95); border: 2px solid #00f0ff; border-radius: 12px; padding: 16px; flex: 1; box-shadow: 0 0 25px rgba(0, 240, 255, 0.4), inset 0 0 10px rgba(0, 240, 255, 0.15); text-align: center; }
        
        .brand-title { color: #39ff14; font-size: 22px; font-weight: bold; text-shadow: 0 0 12px #39ff14; margin: 0 0 12px 0; letter-spacing: 2px; }
        
        input[type="text"] { width: 90%; padding: 12px; border: 1px solid #00f0ff; background: #000; color: #39ff14; border-radius: 6px; font-size: 15px; margin-bottom: 12px; outline: none; box-shadow: inset 0 0 8px rgba(0, 240, 255, 0.3); }
        input[type="text"]::placeholder { color: rgba(0, 240, 255, 0.4); }

        .btn-group { display: flex; gap: 8px; justify-content: center; }
        button { background: #00f0ff; color: #000; border: none; padding: 10px 14px; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; transition: 0.3s; flex: 1; box-shadow: 0 0 10px rgba(0, 240, 255, 0.4); }
        button:hover { background: #39ff14; box-shadow: 0 0 15px #39ff14; color: #000; }
        
        #mic-btn { background: #ff0055; color: #fff; box-shadow: 0 0 10px rgba(255, 0, 85, 0.4); }
        #mic-btn.listening { background: #39ff14; color: #000; box-shadow: 0 0 15px #39ff14; }
        
        #log { margin-top: 14px; color: #fff; font-size: 12px; text-align: left; background: #000; padding: 10px; border-radius: 6px; height: 120px; overflow-y: auto; border: 1px solid #39ff14; box-shadow: inset 0 0 10px rgba(57, 255, 20, 0.2); }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <!-- Left Side: Earth Map & Temperature -->
        <div class="left-panel">
            <div class="globe-container">
                <canvas id="earthCanvas" width="110" height="110"></canvas>
            </div>
            <div class="temp-box" id="temp-display">28°C</div>
        </div>

        <!-- Center/Right Panel: Main Typing Pad & Terminal -->
        <div class="card">
            <div class="brand-title">AeRo Ai</div>
            <input type="text" id="cmd" placeholder="Type or speak command..." onkeydown="if(event.key === 'Enter') sendCommand()">
            <div class="btn-group">
                <button onclick="sendCommand()">EXECUTE</button>
                <button id="mic-btn" onclick="toggleVoice()">🎙️ SPEAK</button>
            </div>
            <div id="log">System Online...</div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('earthCanvas');
        const ctx = canvas.getContext('2d');
        let angle = 0;

        function drawEarthMap() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            let cx = canvas.width / 2;
            let cy = canvas.height / 2;
            let radius = 50;

            // Outer ring
            ctx.beginPath();
            ctx.arc(cx, cy, radius + 3, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(0, 240, 255, 0.3)';
            ctx.lineWidth = 1;
            ctx.setLineDash([2, 2]);
            ctx.stroke();
            ctx.setLineDash([]);

            // Base globe ocean
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.fillStyle = '#001830';
            ctx.fill();
            ctx.strokeStyle = '#00f0ff';
            ctx.lineWidth = 2;
            ctx.stroke();

            ctx.save();
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, Math.PI * 2);
            ctx.clip();

            // Simulated Detailed Country Borders & Continents (Polygon Grid)
            ctx.fillStyle = 'rgba(57, 255, 20, 0.25)';
            ctx.strokeStyle = 'rgba(57, 255, 20, 0.7)';
            ctx.lineWidth = 1;

            // Drawing dynamic continent landmasses representing country borders
            for (let i = -4; i <= 4; i++) {
                let xShift = Math.sin(angle + i * 0.8) * (radius * 0.7);
                ctx.beginPath();
                ctx.ellipse(cx + xShift, cy + (i * 8), 18, 32, i * 0.3, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            }

            // Meridian & Latitude Grid lines for Map navigation
            ctx.strokeStyle = 'rgba(0, 240, 255, 0.35)';
            ctx.lineWidth = 1;
            for(let j = -2; j <= 2; j++) {
                ctx.beginPath();
                ctx.arc(cx + (j * 15), cy, radius, -Math.PI/2, Math.PI/2);
                ctx.stroke();
            }

            ctx.restore();

            // Center Logo inside Earth
            ctx.beginPath();
            ctx.arc(cx, cy, 20, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(3, 8, 16, 0.85)';
            ctx.fill();
            ctx.strokeStyle = '#39ff14';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            ctx.fillStyle = '#39ff14';
            ctx.font = 'bold 9px Consolas';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText("AeRo", cx, cy - 3);
            ctx.fillStyle = '#00f0ff';
            ctx.fillText("AI", cx, cy + 7);

            angle += 0.015;
            requestAnimationFrame(drawEarthMap);
        }
        drawEarthMap();

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

                if(data.url) {
                    window.open(data.url, '_blank');
                }
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
            
            # Direct Website Opening Check (Fast & Reliable)
            key, target_url = get_matched_website_url(query)
            if key:
                if not os.environ.get("RENDER"):
                    webbrowser.open(target_url)
                speak(f"Opening {key}, sir.")
                return jsonify({
                    "status": "success", 
                    "reply": f"Opening {key} for you, Omar sir!",
                    "url": target_url
                })

            # Normal Desktop Controls
            handled, desktop_url = control_laptop(query)
            if handled:
                return jsonify({
                    "status": "success", 
                    "reply": f"Command '{query}' executed successfully.",
                    "url": desktop_url
                })
            
            # Fallback to AI Brain (Gemini REST / Ollama)
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

        except Exception as e:
            print(f"Phone Ask Error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

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