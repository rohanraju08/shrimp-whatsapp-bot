import os, subprocess, tempfile, requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from langdetect import detect 

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── helpers ─────────────────────────────────────────────────────────────
def is_telugu(text: str) -> bool:
    try:
        return detect(text) == "te"
    except Exception:
        return False

def ogg_to_mp3(ogg_path: str) -> str:
    mp3_path = ogg_path[:-4] + ".mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-i", ogg_path, mp3_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return mp3_path

def transcribe_voice(audio_url: str) -> str:
    try:
        r = requests.get(audio_url, timeout=10)
        if r.status_code != 200:
            return "Audio download failed."

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f:
            f.write(r.content)
            ogg_path = f.name

        mp3_path = ogg_to_mp3(ogg_path)

        with open(mp3_path, "rb") as f:
            tx = client.audio.transcriptions.create(model="whisper-1", file=f)
        return tx.text.strip() or "Voice message was silent."
    except Exception as e:
        print("voice-error:", e)
        return "Couldn't process voice message."

def gpt_reply(query: str, telugu: bool) -> str:
    system = (
        "You are India's top Vannamei-shrimp advisor for Andhra Pradesh. "
        "Answer every question confidently in "
        + ("Telugu." if telugu else "English.")
    )
    res = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": query}],
        max_tokens=600,
    )
    return res.choices[0].message.content.strip()

# ── webhook ─────────────────────────────────────────────────────────────
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    body = request.values.get("Body", "").strip()
    m_url  = request.values.get("MediaUrl0", "")
    m_type = request.values.get("MediaContentType0", "")

    if m_type.startswith("audio") and m_url:
        body = transcribe_voice(m_url)

    telugu = is_telugu(body)
    reply  = gpt_reply(body, telugu)

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


