from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
from googletrans import Translator
import os

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
translator = Translator()

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()

    # Translate to English
    translated = translator.translate(incoming_msg, dest='en')
    question_en = translated.text

    # Prompt GPT-4o
    prompt = f"""
You are a helpful, experienced shrimp aquaculture expert from Andhra Pradesh.
Answer in friendly, simple Telugu that farmers can understand easily.

Question: {question_en}
Answer:
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    answer_te = response.choices[0].message["content"]

    # Send WhatsApp reply
    reply = MessagingResponse()
    reply.message(answer_te)
    return str(reply)

if __name__ == "__main__":
    app.run(debug=True)
