import fitz
import ollama
import json

def Extract_Text_From_PDF(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def Screen_Resume(resume_text, job_description):
    prompt = f"""

        You are a Senior Technical recruiter with 20 years of experience.
        your goal is to objectively evaluate based on a job description (JD).

        JOB DESCRIPTION:
        {job_description}

        CANDIDATE RESUME:
        {resume_text}

        TASK:
        Analyze the resume against the JD. Look for key skills, experience levels,
        and project relevence.
        Be strict but fair. "React" matches "React.js". "AWS" matches "Amazon Web Services".

        OUTPUT FORMAT:
        Provide the response in valid JSON format only. Do not add any conversational text.
        structure:
        {{
            "candidate_name": "extracted name",
            "match_score": "0-100",
            "key_strengths": ["list of 3 key strengths"],
            "missing_critical_skills": ["list of missing skills"],
            "recommendation": "Interview" or "Reject",
            "reasoning": "A 2-sentence summary of why."
        }}
    """

    response = ollama.chat(model='gemma3:1b', messages=[
        {'role': 'user', 'content': prompt},
    ])

    return response['message']['content']

job_description = """
We are looking for a Junior Web Developer.
Must have:
-React
-Experience with REST APIs
-Basic understanding of Next.js
-Good communication skills
Nice to have:
-Experience with AWS or Cloud deployment
-Knowledge of TypeScript
"""

try:
    resume_text = Extract_Text_From_PDF(r"E:\MSc-AI-ML\Projects\ChatApp\ResumeScreener\frontend\ChokwalaKishanResume.pdf")
    print(f"Resume loaded. length: {len(resume_text)} characters.")
except Exception as e:
    print(f"Error loading resume: {e}")
    exit()

print("AI is analyzing the candidate... {This may take a few minutes}")
result_json = Screen_Resume(resume_text, job_description)

try:
    clean_json = result_json.replace("```json", "").replace("```", "").strip()
    result_data = json.loads(clean_json)

    print("-"*30)
    print("SCREENING REPORT")
    print("-"*30)
    print(f"Candidate: {result_data.get('candidate_name', 'Uknown')}")
    print(f"Score: {result_data.get('match_score')}/100")
    print(f"Decision: {result_data.get('recommendation').upper()}")
    print(f"Reasoning: {result_data.get('reasoning')}")
    print(f"Missing skills: {', '.join(result_data.get('missing_critical_skills', []))}")

except json.JSONDecodeError:
    print("Failed to parse JSON. Raw output: ")
    print(result_json)
