import os
import tempfile
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
from langdetect import detect
from pydub import AudioSegment

# ── Initialise ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Helpers ─────────────────────────────────────────────────────────────────────
def is_telugu(text: str) -> bool:
    """Detect if input text is Telugu."""
    try:
        return detect(text) == "te"
    except Exception:
        return False

def transcribe_voice(audio_url: str) -> str:
    """
    Download OGG from Twilio, convert to MP3, send to Whisper, return transcript.
    Returns a fallback string on failure.
    """
    try:
        print("📥  Downloading audio:", audio_url)
        res = requests.get(audio_url)
        if res.status_code != 200:
            print("❌  Download failed:", res.status_code)
            return "Couldn't download the audio message."

        # Save as temporary .ogg file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as ogg_file:
            ogg_file.write(res.content)
            ogg_path = ogg_file.name

        # Convert .ogg → .mp3 using pydub (requires ffmpeg in PATH)
        mp3_path = ogg_path.replace(".ogg", ".mp3")
        print("🎧  Converting OGG → MP3 …")
        AudioSegment.from_file(ogg_path, format="ogg").export(mp3_path, format="mp3")

        # Whisper transcription
        print("📤  Sending to Whisper …")
        with open(mp3_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        transcription = transcript.text.strip()
        print("📝  Transcription:", transcription)
        return transcription or "Voice message was silent."

    except Exception as e:
        print("❌  Transcription error:", e)
        return "Couldn't process your voice message."

def get_gpt_response(user_input: str, reply_in_telugu: bool) -> str:
    """Call GPT-4o with a always-answer Vannamei advisor prompt."""
    system_message = f"""
You are India's top shrimp farming expert with 20+ years of experience
advising Vannamei farmers in Andhra Pradesh.

• Always answer confidently, even if the question is unclear or seems silly.
• Never refuse; give your best guidance based on experience.
• Respond in {'Telugu' if reply_in_telugu else 'English'} using simple language
  local farmers understand.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message.strip()},
            {"role": "user",   "content": user_input}
        ],
        max_tokens=600
    )
    answer = response.choices[0].message.content.strip()
    print("🤖  GPT reply:", answer)
    return answer or "Couldn't generate advice right now – please try again."

# ── Webhook ─────────────────────────────────────────────────────────────────────
@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get("Body", "").strip()
    media_url   = request.values.get("MediaUrl0", "")
    media_type  = request.values.get("MediaContentType0", "")

    # Handle voice notes
    if media_type.startswith("audio") and media_url:
        incoming_msg = transcribe_voice(media_url)

    print("🟢  Incoming message:", incoming_msg)

    # Language detection & reply
    reply_in_telugu = is_telugu(incoming_msg)
    ai_response = get_gpt_response(incoming_msg, reply_in_telugu)

    # Twilio response
    resp = MessagingResponse()
    resp.message(ai_response)
    return str(resp)

# ── Render entrypoint ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

