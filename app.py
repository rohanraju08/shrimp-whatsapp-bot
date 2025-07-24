from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os
import requests
import langdetect

# Init
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Detect Telugu
def is_telugu(text):
    try:
        lang = langdetect.detect(text)
        return lang == "te"
    except:
        return False

# Transcribe audio from Twilio voice message
def transcribe_voice(audio_url):
    audio_data = requests.get(audio_url).content
    with open("temp.ogg", "wb") as f:
        f.write(audio_data)
    with open("temp.ogg", "rb") as f:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
        return transcript.text.strip()

# Generate response from GPT
def get_gpt_response(user_input, reply_in_telugu=False):
    prompt = f"""
You are a shrimp farming advisor helping Andhra Pradesh farmers.

{"Always respond in simple Telugu." if reply_in_telugu else "Respond in clear English."}

Question: {user_input}
Answer:
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# Main webhook
@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get("Body", "").strip()
    media_type = request.values.get("MediaContentType0", "")
    media_url = request.values.get("MediaUrl0", "")

    # Process voice message
    if media_type == "audio/ogg" and media_url:
        incoming_msg = transcribe_voice(media_url)

    reply_in_telugu = is_telugu(incoming_msg)
    ai_response = get_gpt_response(incoming_msg, reply_in_telugu)

    # Return Twilio response
    resp = MessagingResponse()
    resp.message(ai_response)
    return str(resp)

# Render-compatible run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
