import os
import time
import json
import requests
import logging
import tkinter as tk
from tkinter import messagebox
from chlorophyll import CodeView
import pygments.lexers
from nava import play

config = json.load(open("config.json"))
# Azure Config
AZURE_SPEECH_KEY = config["AZURE_SPEECH_KEY"]
AZURE_SPEECH_REGION = config["AZURE_SPEECH_REGION"]
OUTPUT_FORMAT = "audio-16khz-128kbitrate-mono-mp3"
FILE_NAME = "voice.mp3"
SSML_FILE = "ssml_saved.xml"

def synthesize_and_play(ssml):
    try:
        start_time = time.time()

        token_url = f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
        token_headers = {"Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY}
        token_response = requests.post(token_url, headers=token_headers)
        token_response.raise_for_status()
        access_token = token_response.text

        tts_url = f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": OUTPUT_FORMAT,
        }

        response = requests.post(tts_url, headers=headers, data=ssml.encode("utf-8"), stream=True)
        response.raise_for_status()

        with open(FILE_NAME, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        elapsed = time.time() - start_time
        logging.info(f"Saved audio in {elapsed:.2f}s")

        play(FILE_NAME)

    except Exception as e:
        logging.error(str(e))
        messagebox.showerror("Error", str(e))

def load_ssml():
    if os.path.exists(SSML_FILE):
        with open(SSML_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return """<speak version='1.0' xml:lang='th-TH'>
  <voice name='th-TH-PremwadeeNeural'>
    สวัสดีค่ะ นี่คือข้อความทดสอบจากบริการแปลงข้อความเป็นเสียงของ Microsoft Azure
  </voice>
</speak>
"""

def save_ssml(content):
    with open(SSML_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def run_gui():
    window = tk.Tk()
    window.title("Azure TTS Synthesizer")

    # Center the window
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window_width = 900
    window_height = 700
    x = (screen_width // 2) - (window_width // 2)
    y = (screen_height // 2) - (window_height // 2)
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    window.minsize(700, 500)

    window.grid_columnconfigure(0, weight=1)
    window.grid_rowconfigure(1, weight=1)

    tk.Label(window, text="🔊 Enter SSML for Azure Text-to-Speech:", font=("Arial", 18, "bold")).grid(row=0, column=0, pady=10, padx=10, sticky="w")

    code_view = CodeView(window, tab_width=4, lexer=pygments.lexers.XmlLexer, font=("Arial", 14))
    code_view.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    code_view.insert("1.0", load_ssml())

    def on_save():
        content = code_view.get("1.0", "end-1c").strip()
        save_ssml(content)
        messagebox.showinfo("Saved", "SSML has been saved successfully.")

    def on_click():
        ssml = code_view.get("1.0", "end-1c").strip()
        if not ssml:
            messagebox.showwarning("Empty SSML", "Please enter SSML before clicking.")
            return
        synthesize_and_play(ssml)

    tk.Button(window, text="💾 Save SSML", font=("Arial", 14), command=on_save).grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 0))
    tk.Button(window, text="🎤 Synthesize and Play", font=("Arial", 16), width=25, command=on_click).grid(row=3, column=0, pady=15, sticky="ew", padx=10)

    def on_close():
        save_ssml(code_view.get("1.0", "end-1c").strip())
        window.destroy()

    window.lift()
    window.attributes('-topmost', True)
    window.after_idle(lambda: window.attributes('-topmost', False))

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()

if __name__ == "__main__":
    run_gui()
