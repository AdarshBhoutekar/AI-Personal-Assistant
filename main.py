from flask import Flask, render_template, url_for, request, jsonify
import os
from dotenv import load_dotenv

# gemini api
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file.")

client = genai.Client(api_key = api_key)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

def gemini_response(*, contents, temperature=0.3, max_output_tokens=512):
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=contents,
            config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens
            }
        )
    except Exception:
        app.logger.exception("Gemini request failed")
        return None, jsonify({"response": "AI service is unavailable right now. Please try again."}), 502

    text = (getattr(response, "text", None) or "").strip()
    if not text:
        return None, jsonify({"response": "AI service returned an empty response. Please try again."}), 502

    return text, None, None

@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    question = (request.form.get("question") or "").strip()
    if not question:
        return jsonify({"response": "Please enter a question."}), 400

    answer, error_response, status_code = gemini_response(
        contents=f"You are a helpful personal assistant.\nUser: {question}",
        temperature=0.7
    )
    if error_response:
        return error_response, status_code

    return jsonify({"response" : answer}), 200

@app.route("/summarize", methods=["POST"])
def summarize():
    email_text = (request.form.get("email") or "").strip()
    if not email_text:
        return jsonify({"response": "Please enter email text to summarize."}), 400

    prompt = f"""
You are an assistant that summarizes emails.

Instructions:
- Summarize clearly in 2-3 sentences
- Capture key points, decisions, and action items
- Keep it concise and easy to read

Email:
{email_text}
"""

    summary, error_response, status_code = gemini_response(
        contents = prompt,
    )
    if error_response:
        return error_response, status_code

    return jsonify({"response" : summary}), 200

@app.route("/summarize-document", methods=["POST"])
def summarize_document():
    document = request.files.get("document")

    if document is None or document.filename == "":
        return jsonify({"response": "Please upload a PDF document."}), 400

    if document.mimetype != "application/pdf":
        return jsonify({"response": "Only PDF documents are supported."}), 400

    summary, error_response, status_code = gemini_response(
        contents=[
            types.Part.from_bytes(
                data=document.read(),
                mime_type=document.mimetype
            ),
            "Summarize this document clearly in simple bullet points."
        ],
        max_output_tokens=1024
    )
    if error_response:
        return error_response, status_code

    return jsonify({"response": summary}), 200


if __name__ == "__main__":
    app.run(debug = True)
