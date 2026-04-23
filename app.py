import fitz
import json
import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# Groq client - reads GROQ_API_KEY from environment variable
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def Extract_Text_From_PDF(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def Screen_Resume(resume_text, job_description):
    prompt = f"""
        You are a Senior Technical recruiter with 20 years of experience.
        Your goal is to objectively evaluate a candidate based on a job description (JD).

        JOB DESCRIPTION:
        {job_description}

        CANDIDATE RESUME:
        {resume_text}

        TASK:
        Analyze the resume against the JD. Look for key skills, experience levels,
        and project relevance.
        Be strict but fair. "React" matches "React.js". "AWS" matches "Amazon Web Services".

        OUTPUT FORMAT:
        Provide the response in valid JSON format only. Do not add any conversational text.
        Structure:
        {{
            "candidate_name": "extracted name",
            "match_score": "0-100",
            "key_strengths": ["list of 3 key strengths"],
            "missing_critical_skills": ["list of missing skills"],
            "recommendation": "Interview" or "Reject",
            "reasoning": "A 2-sentence summary of why."
        }}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return response.choices[0].message.content


@app.route('/ResumeScreener', methods=['POST'])
def resume_screener():
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file uploaded"}), 400

    resume_file = request.files['resume']
    job_description = request.form.get('job_description', '')

    if not job_description.strip():
        return jsonify({"error": "Job description is required"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        resume_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        resume_text = Extract_Text_From_PDF(tmp_path)
    except Exception as e:
        return jsonify({"error": f"Failed to read PDF: {str(e)}"}), 500
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    print(f"Resume loaded. Length: {len(resume_text)} characters.")
    print("AI analyzing resume...")

    result_json = Screen_Resume(resume_text, job_description)

    try:
        clean_json = result_json.replace("```json", "").replace("```", "").strip()
        result_data = json.loads(clean_json)
        return jsonify(result_data)
    except json.JSONDecodeError:
        return jsonify({"error": "AI returned invalid JSON", "raw": result_json}), 500


if __name__ == '__main__':
    print("Resume Screener API running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)