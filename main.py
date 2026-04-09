from flask import Flask, render_template, url_for, request, jsonify
import os
from dotenv import load_dotenv

# gemini api
from google import genai
from google.genai import types

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key = api_key)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    question = request.form.get("question")
        
    response = client.models.generate_content(
        model="gemini-3-flash-preview",            
        contents=f"You are a helpful personal assistant.\nUser: {question}",
        config={
            "temperature": 0.7,        # creativity
            "max_output_tokens": 512   # max length
        }
    )
        
    answer = response.text.strip()
    return jsonify({"response" : answer}), 200

@app.route("/summarize", methods=["POST"])
def summarize():
    email_text = request.form.get("email")
    prompt = f"""
You are an assistant that summarizes emails.

Instructions:
- Summarize clearly in 2-3 sentences
- Capture key points, decisions, and action items
- Keep it concise and easy to read

Email:
{email_text}
"""
        
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents = prompt,
        config={
            "temperature": 0.3,
            "max_output_tokens": 512
        }
    )
        
    summary = response.text.strip()
    return jsonify({"response" : summary}), 200

@app.route("/summarize-document", methods=["POST"])
def summarize_document():
    document = request.files.get("document")

    if document is None or document.filename == "":
        return jsonify({"response": "Please upload a PDF document."}), 400

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            types.Part.from_bytes(
                data=document.read(),
                mime_type=document.mimetype or "application/pdf"
            ),
            "Summarize this document clearly in simple bullet points."
        ],
        config={
            "temperature": 0.3,
            "max_output_tokens": 1024
        }
    )

    summary = response.text.strip()
    return jsonify({"response": summary}), 200


if __name__ == "__main__":
    app.run(debug = True)
