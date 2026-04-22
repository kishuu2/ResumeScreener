import fitz
import json
import tempfile

from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

from dotenv import load_dotenv
load_dotenv()
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

app = Flask(__name__)
CORS(app)


# -------------------------
# Extract text from PDF
# -------------------------
def Extract_Text_From_PDF(pdf_file):

    text = ""

    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    for page in doc:
        text += page.get_text()

    return text


# -------------------------
# AI Screening
# -------------------------
def Screen_Resume(resume_text, job_description):

    prompt = f"""
    Evaluate resume vs job description.

    JD:
    {job_description}

    Resume:
    {resume_text}

    Return JSON:
    candidate_name, match_score, key_strengths,
    missing_critical_skills, recommendation, reasoning
    """

    completion = client.chat.completions.create(

        model="llama3-70b-8192",

        messages=[
            {"role": "user", "content": prompt}
        ],

        temperature=0
    )

    result = completion.choices[0].message.content

    clean_json = result.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(clean_json)
    except:
        return {
            "candidate_name": "Unknown",
            "match_score": "0",
            "key_strengths": [],
            "missing_critical_skills": [],
            "recommendation": "Error",
            "reasoning": result
        }


# -------------------------
# Job description
# -------------------------
# Default job description
DEFAULT_JOB_DESCRIPTION = """
We are looking for a Junior Web Developer.

Must have:
React
REST APIs
Next.js
Communication skills

Nice to have:
AWS
TypeScript
"""


# -------------------------
# API endpoint
# -------------------------
@app.route("https://resumescreener-g9fy.onrender.com/screen_resume", methods=["POST"])
def screen_resume():

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]

    # get custom JD from frontend
    job_description = request.form.get("job_description")

    # fallback to default
    if not job_description or job_description.strip() == "":
        job_description = DEFAULT_JOB_DESCRIPTION


    resume_text = Extract_Text_From_PDF(file)

    result = Screen_Resume(resume_text, job_description)

    return jsonify(result)


# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":

    app.run(debug=True, port=5000)