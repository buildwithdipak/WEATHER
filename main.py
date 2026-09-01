import threading
import requests
import pyttsx3
import speech_recognition as sr
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta

# ==========================
# CONFIG
# ==========================
API_KEY = "ENTER YOUR OPEN WEATHER API KEY HERE"  # OpenWeatherMap
DEFAULT_LANG = "en"
APP_TITLE = "Weather Voice — Premium Assistant"

# ==========================
# TTS ENGINE (pyttsx3)
# ==========================
engine = pyttsx3.init()
engine.setProperty('rate', 200)
engine.setProperty('volume', 1.0)
voices = engine.getProperty('voices')

def pick_english_voice():
    for v in voices:
        name = (v.name or '').lower()
        if 'en' in name or 'english' in name or 'zira' in name or 'david' in name:
            return v.id
    return voices[0].id if voices else None

voice_id_en = pick_english_voice()

def speak(text: str):
    try:
        if voice_id_en:
            engine.setProperty('voice', voice_id_en)
        engine.say(text)
        engine.runAndWait()
    except Exception:
        print(text)

# ==========================
# NETWORK HELPERS (Free Plan Compatible)
# ==========================
SESSION = requests.Session()

def ip_location():
    try:
        r = SESSION.get("https://ipinfo.io/json", timeout=5)
        data = r.json()
        return data.get('city', '')
    except Exception:
        return ""

def fetch_current_weather(city: str):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": API_KEY, "units": "metric"}
        r = SESSION.get(url, params=params, timeout=5)
        return r.json()
    except Exception:
        return {}

def fetch_forecast(city: str):
    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {"q": city, "appid": API_KEY, "units": "metric"}
        r = SESSION.get(url, params=params, timeout=5)
        return r.json()
    except Exception:
        return {}

# ==========================
# UI HELPERS
# ==========================
WEATHER_EMOJI = [
    ("thunder", "⛈️"),
    ("storm", "⛈️"),
    ("rain", "🌧️"),
    ("drizzle", "🌦️"),
    ("snow", "❄️"),
    ("mist", "🌫️"),
    ("fog", "🌫️"),
    ("haze", "🌫️"),
    ("cloud", "☁️"),
    ("clear", "☀️"),
    ("sun", "☀️"),
]

def emoji_for(text: str) -> str:
    t = (text or '').lower()
    for k, e in WEATHER_EMOJI:
        if k in t:
            return e
    return "🌍"

# ==========================
# SPEECH
# ==========================
recognizer = sr.Recognizer()
recognizer.pause_threshold = 0.7

def listen_once(on_done):
    def _task():
        try:
            with sr.Microphone() as source:
                status_var.set("🎤 Speak: e.g., 'weather in Delhi' or 'weather here'")
                app.update_idletasks()
                audio = recognizer.listen(source, phrase_time_limit=4)
                status_var.set("⏳ Recognizing…")
                text = recognizer.recognize_google(audio, language="en-US")
        except:
            text = ""
        on_done(text)
    threading.Thread(target=_task, daemon=True).start()

# ==========================
# TKINTER PREMIUM UI
# ==========================
app = tk.Tk()
app.title(APP_TITLE)
app.geometry("880x600")
app.configure(bg="#0f1226")

style = ttk.Style()
style.theme_use('clam')
style.configure("Card.TFrame", background="#15193a")
style.configure("TLabel", background="#15193a", foreground="#e6e8ff", font=("Segoe UI", 11))
style.configure("Title.TLabel", background="#0f1226", foreground="#e6e8ff", font=("Segoe UI Semibold", 18))
style.configure("Small.TLabel", background="#15193a", foreground="#aab0ff", font=("Segoe UI", 9))
style.configure("TButton", background="#2a2f6b", foreground="#ffffff", font=("Segoe UI Semibold", 11))

header = ttk.Frame(app, style="Card.TFrame")
header.pack(fill="x", pady=(10, 5))

title_lbl = ttk.Label(header, text="🌤️ Weather Voice — Premium Assistant", style="Title.TLabel")
title_lbl.pack(side="left", padx=20)

btn_auto_loc = ttk.Button(header, text="📍 Use My Location")
btn_auto_loc.pack(side="right", padx=10)

card = ttk.Frame(app, style="Card.TFrame")
card.pack(fill="both", expand=True, padx=20, pady=10)

row_top = ttk.Frame(card, style="Card.TFrame")
row_top.pack(fill="x", pady=5, padx=16)

city_var = tk.StringVar()
city_entry = ttk.Entry(row_top, textvariable=city_var, font=("Segoe UI", 12))
city_entry.pack(side="left", fill="x", expand=True)

btn_speak = ttk.Button(row_top, text="🎤 Speak")
btn_speak.pack(side="left", padx=8)
btn_get = ttk.Button(row_top, text="🔍 Get Weather")
btn_get.pack(side="left")

status_var = tk.StringVar(value="Ready")
status_lbl = ttk.Label(card, textvariable=status_var, style="Small.TLabel")
status_lbl.pack(anchor="w", padx=18)

result_var = tk.StringVar(value="")
result_lbl = ttk.Label(card, textvariable=result_var, font=("Segoe UI", 13), wraplength=650)
result_lbl.pack(fill="x", padx=22, pady=(10, 4))

notebook = ttk.Notebook(card)
notebook.pack(fill="both", expand=True, padx=16, pady=12)

# Current tab
tab_current = ttk.Frame(notebook, style="Card.TFrame")
notebook.add(tab_current, text="Current")
cur_text = tk.Text(tab_current, height=10, wrap='word', bg="#15193a", fg="#e6e8ff", relief='flat')
cur_text.pack(fill="both", expand=True, padx=10, pady=10)

# Hourly tab
tab_hourly = ttk.Frame(notebook, style="Card.TFrame")
notebook.add(tab_hourly, text="Hourly (next 12h)")
hourly_tree = ttk.Treeview(tab_hourly, columns=("time","temp","desc"), show='headings', height=12)
hourly_tree.heading("time", text="Time")
hourly_tree.heading("temp", text="Temp °C")
hourly_tree.heading("desc", text="Description")
hourly_tree.pack(fill="both", expand=True, padx=10, pady=10)

# 7-Day tab
tab_daily = ttk.Frame(notebook, style="Card.TFrame")
notebook.add(tab_daily, text="7-Day")
daily_tree = ttk.Treeview(tab_daily, columns=("day","min","max","desc"), show='headings', height=10)
daily_tree.heading("day", text="Day")
daily_tree.heading("min", text="Min °C")
daily_tree.heading("max", text="Max °C")
daily_tree.heading("desc", text="Description")
daily_tree.pack(fill="both", expand=True, padx=10, pady=10)

# ==========================
# LOGIC
# ==========================

def render_current(data):
    try:
        desc = data['weather'][0]['description']
        temp = data['main']['temp']
        feels = data['main']['feels_like']
        hum = data['main']['humidity']
        wind = data['wind']['speed']
        txt = f"Description: {desc}\nTemperature: {temp}°C (feels like {feels}°C)\nHumidity: {hum}%\nWind: {wind} m/s"
        cur_text.delete('1.0','end')
        cur_text.insert('end', txt)
        result_var.set(f"{emoji_for(desc)}  {txt}")
        speak(f"{desc}. Temperature {temp} degrees, feels like {feels}.")
    except:
        result_var.set("Failed to parse current weather.")


def render_hourly(data):
    for i in hourly_tree.get_children():
        hourly_tree.delete(i)
    try:
        for h in data['list'][:12]:
            dt = datetime.fromtimestamp(h['dt']).strftime('%I:%M %p')
            t = h['main']['temp']
            d = h['weather'][0]['description']
            hourly_tree.insert('', 'end', values=(dt, f"{t}", d))
    except:
        pass


def render_daily(data):
    for i in daily_tree.get_children():
        daily_tree.delete(i)
    try:
        daily = {}
        for item in data['list']:
            date = datetime.fromtimestamp(item['dt']).date()
            if date not in daily:
                daily[date] = {'min': item['main']['temp_min'], 'max': item['main']['temp_max'], 'desc': item['weather'][0]['description']}
            else:
                daily[date]['min'] = min(daily[date]['min'], item['main']['temp_min'])
                daily[date]['max'] = max(daily[date]['max'], item['main']['temp_max'])
        for d, vals in list(daily.items())[:7]:
            daily_tree.insert('', 'end', values=(d.strftime('%a'), vals['min'], vals['max'], vals['desc']))
    except:
        pass


def fetch_and_render(city: str):
    if not city:
        result_var.set("Please enter a city or use 📍 Use My Location.")
        speak("Please enter a city or use my location.")
        return
    status_var.set("⏳ Fetching weather…")
    def _task():
        cur = fetch_current_weather(city)
        if not cur or cur.get('cod') != 200:
            result_var.set("City not found.")
            speak("Sorry, I could not find that city.")
            status_var.set("Ready")
            return
        render_current(cur)
        fore = fetch_forecast(city)
        if fore and fore.get('cod') == "200":
            render_hourly(fore)
            render_daily(fore)
        status_var.set(f"✅ {cur['name']}, {cur['sys']['country']}")
    threading.Thread(target=_task, daemon=True).start()


def fetch_and_render_by_ip():
    city = ip_location()
    if not city:
        result_var.set("Could not detect location. Please type a city.")
        speak("Could not detect location. Please type a city.")
        return
    fetch_and_render(city)

# ==========================
# BINDINGS
# ==========================
btn_get.configure(command=lambda: fetch_and_render(city_var.get().strip()))
btn_auto_loc.configure(command=fetch_and_render_by_ip)
btn_speak.configure(command=lambda: listen_once(lambda t: fetch_and_render(t.split('in')[-1].strip() if 'in' in t else t)))

app.bind('<Return>', lambda e: fetch_and_render(city_var.get().strip()))
app.bind('<Control-m>', lambda e: listen_once(lambda t: fetch_and_render(t.split('in')[-1].strip() if 'in' in t else t)))
app.bind('<Control-l>', lambda e: fetch_and_render_by_ip())

city_entry.focus_set()

app.mainloop()
