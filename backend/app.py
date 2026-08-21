import os
import re
import io
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from pypdf import PdfReader
import docx
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.debug = False

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "scanline-secure-jwt-ats-secret-key-2026")
DB_FILE = "/tmp/scanline.db" if os.environ.get("VERCEL") else "scanline.db"

CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

ROLE_SKILL_MATRIX = {
    "frontend developer": [
        "html", "css", "javascript", "typescript", "react", "nextjs", "vue", "angular", 
        "tailwind", "tailwind css", "redux", "zustand", "gsap", "framer motion", "vite", 
        "webpack", "responsive design", "rest api", "graphql", "sass", "bootstrap",
        "figma", "git", "github", "npm", "yarn", "es6", "dom", "ajax", "json"
    ],
    "backend developer": [
        "node", "nodejs", "express", "expressjs", "python", "django", "flask", "fastapi", 
        "java", "spring boot", "golang", "c#", ".net", "sql", "postgresql", "mysql", 
        "mongodb", "redis", "rest api", "graphql", "docker", "microservices", "jwt", 
        "kafka", "rabbitmq", "prisma", "orm", "mvc"
    ],
    "full stack developer": [
        "html", "css", "javascript", "typescript", "react", "nextjs", "node", "nodejs", 
        "express", "python", "sql", "postgresql", "mongodb", "rest api", "graphql", 
        "docker", "tailwind", "git", "ci/cd", "aws", "redux", "prisma"
    ],
    "web developer": [
        "html", "html5", "css", "css3", "javascript", "react", "responsive design", 
        "tailwind", "bootstrap", "rest api", "git", "github", "seo", "web performance", 
        "jquery", "sass", "wordpress"
    ],
    "python developer": [
        "python", "django", "flask", "fastapi", "sql", "postgresql", "pandas", 
        "numpy", "pytest", "asyncio", "celery", "redis", "docker", "git", 
        "sqlalchemy", "data structures", "algorithms"
    ],
    "ai/ml engineer": [
        "python", "machine learning", "deep learning", "nlp", "llms", "pytorch", 
        "tensorflow", "scikit-learn", "langchain", "llamaindex", "hugging face", 
        "vector database", "pinecone", "chroma", "rag", "opencv", "mlops", "numpy", "pandas"
    ],
    "generative ai engineer": [
        "python", "llms", "langchain", "llamaindex", "prompt engineering", "rag", 
        "vector database", "pinecone", "chroma", "fine-tuning", "hugging face", 
        "gemini api", "openai api", "pytorch", "deep learning", "agentic workflows"
    ],
    "data scientist": [
        "python", "r", "machine learning", "sql", "pandas", "numpy", "scikit-learn", 
        "scipy", "data visualization", "matplotlib", "seaborn", "tableau", "power bi", 
        "deep learning", "statistics", "feature engineering"
    ],
    "data engineer": [
        "python", "sql", "apache spark", "spark", "hadoop", "kafka", "airflow", 
        "snowflake", "dbt", "bigquery", "postgresql", "etl", "data warehousing", 
        "aws glue", "docker", "hive"
    ],
    "devops engineer": [
        "linux", "docker", "kubernetes", "terraform", "ansible", "aws", "azure", 
        "gcp", "ci/cd", "github actions", "jenkins", "helm", "prometheus", "grafana", 
        "bash", "shell scripting", "nginx"
    ],
    "cloud architect / engineer": [
        "aws", "azure", "gcp", "terraform", "cloudformation", "iam", "serverless", 
        "lambda", "s3", "ec2", "docker", "kubernetes", "networking", "vpc", "cloudwatch"
    ],
    "cybersecurity analyst": [
        "network security", "penetration testing", "siem", "firewalls", 
        "vulnerability assessment", "soc", "incident response", "cryptography", 
        "wireshark", "owasp", "metasploit", "python", "kali linux"
    ],
    "mobile app developer": [
        "react native", "flutter", "dart", "swift", "kotlin", "ios", "android", 
        "mobile ui", "sqlite", "rest api", "firebase", "state management", "redux"
    ],
    "qa / automation test engineer": [
        "selenium", "cypress", "playwright", "jest", "postman", "api testing", 
        "automation testing", "manual testing", "jira", "load testing", "python", 
        "javascript", "testng", "cucumber"
    ],
    "blockchain / web3 developer": [
        "solidity", "ethereum", "smart contracts", "web3js", "ethersjs", "rust", 
        "metamask", "truffle", "hardhat", "defi", "cryptography", "ipfs"
    ],
    "ui/ux designer": [
        "figma", "wireframing", "prototyping", "user research", "ui design", "ux design", 
        "design systems", "information architecture", "interaction design", "adobe xd", 
        "sketch", "usability testing"
    ]
}

ROLE_ALIASES = {
    "frontend developer": ["frontend", "front end", "front-end", "ui developer", "react developer", "vue developer", "angular developer"],
    "backend developer": ["backend", "back end", "back-end", "node developer", "python developer", "java developer", "spring developer"],
    "full stack developer": ["full stack", "fullstack", "full-stack", "mern", "mean", "software engineer", "sde"],
    "web developer": ["web developer", "web dev", "website developer"],
    "python developer": ["python developer", "python dev", "django developer", "fastapi developer"],
    "ai/ml engineer": ["ai", "ml", "ai/ml", "machine learning", "deep learning", "ml engineer"],
    "generative ai engineer": ["gen ai", "generative ai", "llm engineer", "prompt engineer", "rag developer"],
    "data scientist": ["data science", "data scientist", "data analytics", "data analyst"],
    "data engineer": ["data engineer", "etl developer", "big data engineer"],
    "devops engineer": ["devops", "site reliability engineer", "sre", "ci/cd engineer"],
    "cloud architect / engineer": ["cloud", "cloud engineer", "aws engineer", "azure engineer", "gcp engineer"],
    "cybersecurity analyst": ["cyber security", "cybersecurity", "security analyst", "infosec", "pen tester"],
    "mobile app developer": ["mobile developer", "app developer", "react native developer", "flutter developer", "android developer", "ios developer"],
    "qa / automation test engineer": ["qa", "tester", "quality assurance", "automation tester", "sdet"],
    "blockchain / web3 developer": ["blockchain", "web3", "solidity developer", "smart contract developer"],
    "ui/ux designer": ["ui/ux", "ui designer", "ux designer", "product designer"]
}

ACTION_VERBS = [
    "built", "developed", "architected", "engineered", "implemented", "designed", 
    "optimized", "deployed", "scaled", "created", "integrated", "managed", 
    "refactored", "automated", "executed", "collaborated", "spearheaded", "solved"
]

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            job_title TEXT,
            match_score INTEGER,
            ats_score INTEGER,
            word_count INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200
        
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication token is missing. Please log in."}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format."}), 401
        
        token = parts[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session token expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid session token. Please log in."}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated

def clean_extracted_text(text):
    if not text:
        return ""
    text = text.replace('\xa0', ' ').replace('\r', ' ')
    return re.sub(r'[ \t]+', ' ', text).strip()

def extract_text_from_pdf(file_bytes):
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        text = "".join([page.extract_text() or "" for page in reader.pages])
        return clean_extracted_text(text)
    except Exception:
        return ""

def extract_text_from_docx(file_bytes):
    try:
        docx_file = io.BytesIO(file_bytes)
        doc = docx.Document(docx_file)
        text = "\n".join([p.text for p in doc.paragraphs])
        return clean_extracted_text(text)
    except Exception:
        return ""

def normalize_text(text):
    t = text.lower()
    t = re.sub(r'\breact(?:\.js|js)?\b', 'react', t)
    t = re.sub(r'\bnode(?:\.js|js)?\b', 'node', t)
    t = re.sub(r'\bexpress(?:\.js|js)?\b', 'express', t)
    t = re.sub(r'\bhtml\s*5?\b', 'html', t)
    t = re.sub(r'\bcss\s*3?\b', 'css', t)
    t = re.sub(r'\bjavascript\b', 'javascript', t)
    t = re.sub(r'\bvue(?:\.js|js)?\b', 'vue', t)
    t = re.sub(r'\bnext(?:\.js|js)?\b', 'nextjs', t)
    return t

def parse_input_skills(raw_input):
    if not raw_input:
        return []
    items = re.split(r'[,;\n/]+', raw_input)
    parsed = []
    for item in items:
        cleaned = item.strip().lower()
        if cleaned:
            cleaned = normalize_text(cleaned)
            parsed.append(cleaned)
    return list(dict.fromkeys(parsed))

def auto_detect_matching_roles(text_lower, resume_words_set):
    role_match_scores = []
    
    for role_name, skills in ROLE_SKILL_MATRIX.items():
        matched = []
        for skill in skills:
            if " " in skill:
                if skill in text_lower:
                    matched.append(skill)
            else:
                if skill in resume_words_set or re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    matched.append(skill)
        
        density_factor = sum(len(re.findall(r'\b' + re.escape(s) + r'\b', text_lower)) for s in matched)
        score = int((len(matched) / len(skills)) * 100) if skills else 0
        
        if len(matched) > 0:
            role_match_scores.append({
                "role": role_name,
                "score": score,
                "matched_count": len(matched),
                "density": density_factor,
                "matched_skills": matched,
                "total_skills": len(skills)
            })
    
    role_match_scores.sort(key=lambda x: (x["matched_count"] * 2 + x["density"], x["score"]), reverse=True)
    return role_match_scores

def match_target_roles(job_title_input):
    cleaned_input = job_title_input.lower().strip()
    for canonical_key, aliases in ROLE_ALIASES.items():
        if canonical_key in cleaned_input or cleaned_input in canonical_key:
            return canonical_key, ROLE_SKILL_MATRIX.get(canonical_key, [])
        for alias in aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', cleaned_input):
                return canonical_key, ROLE_SKILL_MATRIX.get(canonical_key, [])
    return cleaned_input, []

def analyze_resume_text(raw_text, job_title, job_desc):
    text_lower = normalize_text(raw_text)
    words = re.findall(r'\b[a-zA-Z0-9+#.-]+\b', text_lower)
    word_count = len(words)
    resume_words_set = set(words)
    
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text)
    phone_match = re.search(r'(?:(?:\+?91|0)?[ -]?)?[6-9]\d{9}|(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw_text)
    linkedin_match = re.search(r'linkedin\.com/in/[a-zA-Z0-9_-]+', text_lower)
    github_match = re.search(r'github\.com/[a-zA-Z0-9_-]+', text_lower)
    portfolio_match = re.search(r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:vercel\.app|netlify\.app|github\.io|dev|me|io|com)', text_lower)

    contact_info = {
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else None,
        "linkedin": linkedin_match.group(0) if linkedin_match else None,
        "github": github_match.group(0) if github_match else None,
        "portfolio": portfolio_match.group(0) if portfolio_match else None
    }
    
    sections = {
        "Experience": ["experience", "employment", "work history", "internship", "work experience"],
        "Education": ["education", "academic", "degree", "qualification", "b.tech", "bachelor", "master", "diploma", "bca", "college", "university"],
        "Skills": ["skills", "technical skills", "technologies", "proficiencies", "tools", "core competencies"],
        "Projects": ["projects", "personal projects", "portfolio", "key projects"],
        "Certifications": ["certifications", "certificates", "achievements", "courses"]
    }
    
    sections_found = []
    for section_name, keywords in sections.items():
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                sections_found.append(section_name)
                break

    detected_roles = auto_detect_matching_roles(text_lower, resume_words_set)
    is_custom_role_provided = bool(job_title and job_title.strip())

    explicit_jd_skills = parse_input_skills(job_desc)

    if explicit_jd_skills and len(explicit_jd_skills) > 0 and (not job_title or not job_title.strip() or len(explicit_jd_skills) >= 3):
        all_target_skills = explicit_jd_skills
        effective_role = job_title.strip() if is_custom_role_provided else "Custom Required Skills"
    elif is_custom_role_provided:
        effective_role_name, resolved_skills = match_target_roles(job_title)
        effective_role = job_title.strip()
        all_target_skills = list(dict.fromkeys(resolved_skills + explicit_jd_skills))
    else:
        if detected_roles:
            effective_role = detected_roles[0]["role"].title()
            all_target_skills = ROLE_SKILL_MATRIX.get(detected_roles[0]["role"], [])
        else:
            effective_role = "General Profile"
            all_target_skills = []

    matched_skills = []
    missing_skills = []
    
    for skill in all_target_skills:
        if " " in skill:
            if skill in text_lower:
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)
        else:
            if skill in resume_words_set or re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

    if len(all_target_skills) > 0:
        match_score = int((len(matched_skills) / len(all_target_skills)) * 100)
    else:
        match_score = 0

    score_breakdown = []
    suggestions = []
    calculated_ats = 0

    contact_pts = 0
    if contact_info["email"]: contact_pts += 5
    if contact_info["phone"]: contact_pts += 4
    if contact_info["linkedin"]: contact_pts += 4
    if contact_info["github"] or contact_info["portfolio"]: contact_pts += 2
    calculated_ats += contact_pts
    score_breakdown.append({
        "label": f"Contact Complete ({contact_pts}/15)",
        "passed": contact_pts >= 12,
        "detail": f"Email: {'✓' if contact_info['email'] else '✕'} | Phone: {'✓' if contact_info['phone'] else '✕'} | Profiles: {'✓' if contact_info['linkedin'] or contact_info['github'] else '✕'}"
    })

    distinct_sections = len(set(sections_found))
    sec_pts = 20 if distinct_sections >= 4 else (14 if distinct_sections == 3 else (8 if distinct_sections == 2 else 4))
    calculated_ats += sec_pts
    score_breakdown.append({
        "label": f"Section Hierarchy ({sec_pts}/20)",
        "passed": sec_pts >= 14,
        "detail": f"Detected {distinct_sections} key sections: {', '.join(set(sections_found)) if sections_found else 'None'}"
    })

    if 350 <= word_count <= 850:
        len_pts = 15
    elif 220 <= word_count < 350:
        len_pts = 10
    elif word_count < 220:
        len_pts = 5
    else:
        len_pts = 8
    calculated_ats += len_pts
    score_breakdown.append({
        "label": f"Content Density ({len_pts}/15)",
        "passed": len_pts >= 10,
        "detail": f"Resume contains {word_count} words."
    })

    verbs_found = [v for v in ACTION_VERBS if re.search(r'\b' + re.escape(v) + r'\b', text_lower)]
    has_metrics = bool(re.search(r'\b\d+(?:%|\+|ms|k|x|\.\d+)\b', text_lower))
    impact_pts = min(10, len(verbs_found) * 2) + (5 if has_metrics else 0)
    calculated_ats += impact_pts
    score_breakdown.append({
        "label": f"Impact & Action Verbs ({impact_pts}/15)",
        "passed": impact_pts >= 10,
        "detail": f"Action verbs: {len(verbs_found)} | Quantifiable metrics: {'Found' if has_metrics else 'Missing'}"
    })

    skill_pts = int((match_score / 100) * 25) if all_target_skills else 10
    calculated_ats += skill_pts
    score_breakdown.append({
        "label": f"Role Skills Match ({skill_pts}/25)",
        "passed": skill_pts >= 15,
        "detail": f"Matched {len(matched_skills)} of {len(all_target_skills)} required skills for {effective_role}"
    })

    hygiene_pts = 10 if len(raw_text.strip()) >= 100 else 5
    calculated_ats += hygiene_pts
    score_breakdown.append({
        "label": f"ATS Text Parseability ({hygiene_pts}/10)",
        "passed": hygiene_pts == 10,
        "detail": "Clean textual layer parsed successfully."
    })

    final_ats_score = max(0, min(100, calculated_ats))
    
    top_suggested_roles = [
        {"role": r["role"].title(), "match_percent": r["score"], "matched_skills_count": r["matched_count"]}
        for r in detected_roles[:4]
    ]

    if not is_custom_role_provided and top_suggested_roles:
        breakdown_text = " | ".join([f"{r['role']}: {r['match_percent']}% ({r['matched_skills_count']} skills)" for r in top_suggested_roles])
        suggestions.append(f"🎯 Auto-Detected Primary Role: '{effective_role}'. Role Compatibility Breakdown ➔ {breakdown_text}")

    if contact_pts < 12:
        suggestions.append("Add missing contact credentials (Professional Email, Mobile Number, LinkedIn/GitHub).")
    if distinct_sections < 4:
        suggestions.append("Structure resume with standard headings: Education, Skills, Projects, and Experience.")
    if missing_skills:
        suggestions.append(f"Consider adding missing required skills: {', '.join(missing_skills[:6])}.")

    return {
        "ats_score": final_ats_score,            
        "match_score": match_score,
        "effective_role": effective_role,
        "is_custom_role": is_custom_role_provided,
        "suggested_roles": top_suggested_roles,
        "ats": {
            "score": final_ats_score,
            "word_count": word_count,
            "checks": score_breakdown
        },
        "contact": contact_info,
        "sections_found": list(set(sections_found)),
        "suggestions": suggestions,
        "match": {
            "match_score": match_score,
            "matched_skills": matched_skills,  
            "missing_skills": missing_skills,
            "job_skills_total": len(all_target_skills)
        }
    }

@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "online", "service": "Resume Analyzer Engine"}), 200

@app.route("/api/signup", methods=["POST", "OPTIONS"])
def signup():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return jsonify({"error": "A user with this email already exists."}), 409

        cursor.execute(
            "INSERT INTO users (name, email, password, created_at) VALUES (?, ?, ?, ?)",
            (name, email, hashed_password, datetime.now(timezone.utc).isoformat())
        )
        user_id = cursor.lastrowid
        conn.commit()

        token = jwt.encode(
            {"user_id": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(days=7)},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"success": True, "token": token, "name": name, "email": email}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid email or password."}), 401

        token = jwt.encode(
            {"user_id": user["id"], "email": user["email"], "exp": datetime.now(timezone.utc) + timedelta(days=7)},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"success": True, "token": token, "name": user["name"], "email": user["email"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/analyze", methods=["POST", "OPTIONS"])
@token_required
def analyze(current_user_id):
    if "resume" not in request.files:
        return jsonify({"error": "No resume file provided."}), 400
    
    file = request.files["resume"]
    raw_job_title = request.form.get("job_title", "").strip()
    job_description = request.form.get("job_description", "").strip()

    ext = os.path.splitext(file.filename)[1].lower()
    file_bytes = file.read()

    text = ""
    if ext == ".pdf":
        text = extract_text_from_pdf(file_bytes)
    elif ext == ".docx":
        text = extract_text_from_docx(file_bytes)
    elif ext in [".txt", ""]:
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            pass
    else:
        return jsonify({"error": "Unsupported file format. Please upload PDF, DOCX, or TXT."}), 400

    if not text.strip():
        return jsonify({"error": "Could not parse readable text from document."}), 400

    analysis_data = analyze_resume_text(text, raw_job_title, job_description)

    stored_history_title = raw_job_title if raw_job_title else analysis_data['effective_role']

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analyses (user_id, filename, job_title, match_score, ats_score, word_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user_id,
            file.filename,
            stored_history_title,
            analysis_data["match_score"],
            analysis_data["ats_score"],
            analysis_data["ats"]["word_count"],
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
    except Exception as e:
        print(f"Error logging analysis: {e}")
    finally:
        conn.close()

    return jsonify(analysis_data)

@app.route("/api/history", methods=["GET", "OPTIONS"])
@token_required
def get_history(current_user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM analyses WHERE user_id = ? ORDER BY created_at DESC", 
            (current_user_id,)
        )
        rows = cursor.fetchall()
        
        history = [{
            "id": r["id"],
            "filename": r["filename"],
            "job_title": r["job_title"] if r["job_title"] else "—",
            "match_score": r["match_score"],
            "ats_score": r["ats_score"],
            "word_count": r["word_count"],
            "created_at": r["created_at"]
        } for r in rows]
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/analysis/<int:analysis_id>", methods=["DELETE", "OPTIONS"])
@token_required
def delete_analysis(current_user_id, analysis_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM analyses WHERE id = ? AND user_id = ?", 
            (analysis_id, current_user_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Scan record not found or unauthorized."}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
