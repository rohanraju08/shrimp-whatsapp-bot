from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

# 🔁 Use GPT-4o to translate Telugu to English
def translate_to_english(text):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Translate the following Telugu text to English. Only return the translated sentence."},
            {"role": "user", "content": text}
        ],
        max_tokens=100
    )
    return response.choices[0].message["content"].strip()

# 🧠 Main WhatsApp route
@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()

    # 1. Translate to English (using GPT)
    question_en = translate_to_english(incoming_msg)

    # 2. Prompt GPT-4o with expert instructions
    prompt = f"""
You are a helpful and experienced shrimp farming expert from Andhra Pradesh ,  with immense knowdlege on vannami shrimp.
Always answer in clear and simple Telugu so that local farmers understand.
If the question is unclear or dangerous, ask for clarification or give safe advice.

Question: {question_en}
Answer:
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    answer_te = response.choices[0].message["content"].strip()

    # 3. Send WhatsApp reply
    reply = MessagingResponse()
    reply.message(answer_te)
    return str(reply)

# 🔁 Render-compatible run config
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
