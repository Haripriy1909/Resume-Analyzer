import os
import re
import io
import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify
import flask.cli
from flask_cors import CORS
from pypdf import PdfReader
import docx
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Silence Flask development banners cleanly
flask.cli.show_server_banner = lambda *args: None
logging.getLogger('werkzeug').setLevel(logging.ERROR)

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
        "tailwind", "redux", "zustand", "gsap", "framer motion", "vite", "webpack", 
        "responsive design", "rest api", "graphql", "sass", "bootstrap"
    ],
    "backend developer": [
        "node", "express", "python", "django", "flask", "fastapi", "java", "spring boot", 
        "golang", "c#", ".net", "sql", "postgresql", "mysql", "mongodb", "redis", 
        "rest api", "graphql", "docker", "microservices", "jwt", "kafka", "rabbitmq", "c"
    ],
    "full stack developer": [
        "html", "css", "javascript", "typescript", "react", "nextjs", "node", "express", 
        "python", "sql", "postgresql", "mongodb", "rest api", "graphql", "docker", 
        "tailwind", "git", "ci/cd", "aws"
    ],
    "web developer": [
        "html", "css", "javascript", "react", "responsive design", "tailwind", 
        "bootstrap", "rest api", "git", "seo", "web performance"
    ],
    "python developer": [
        "python", "django", "flask", "fastapi", "sql", "postgresql", "pandas", 
        "numpy", "pytest", "asyncio", "celery", "redis", "docker", "git"
    ],
    "ai/ml engineer": [
        "python", "machine learning", "deep learning", "nlp", "llms", "pytorch", 
        "tensorflow", "scikit-learn", "langchain", "llamaindex", "hugging face", 
        "vector database", "pinecone", "chroma", "rag", "opencv", "mlops"
    ],
    "generative ai engineer": [
        "python", "llms", "langchain", "llamaindex", "prompt engineering", "rag", 
        "vector database", "pinecone", "chroma", "fine-tuning", "hugging face", 
        "gemini api", "openai api", "pytorch", "deep learning"
    ],
    "data scientist": [
        "python", "r", "machine learning", "sql", "pandas", "numpy", "scikit-learn", 
        "scipy", "data visualization", "matplotlib", "seaborn", "tableau", "power bi", 
        "deep learning", "statistics"
    ],
    "data engineer": [
        "python", "sql", "apache spark", "hadoop", "kafka", "airflow", "snowflake", 
        "dbt", "bigquery", "postgresql", "etl", "data warehousing", "aws glue", "docker"
    ],
    "devops engineer": [
        "linux", "docker", "kubernetes", "terraform", "ansible", "aws", "azure", 
        "gcp", "ci/cd", "github actions", "jenkins", "helm", "prometheus", "grafana", "bash"
    ],
    "cloud architect / engineer": [
        "aws", "azure", "gcp", "terraform", "cloudformation", "iam", "serverless", 
        "lambda", "s3", "ec2", "docker", "kubernetes", "networking", "vpc"
    ],
    "cybersecurity analyst": [
        "network security", "penetration testing", "siem", "firewalls", "vulnerability assessment", 
        "soc", "incident response", "cryptography", "wireshark", "owasp", "metasploit", "python"
    ],
    "mobile app developer": [
        "react native", "flutter", "dart", "swift", "kotlin", "ios", "android", 
        "mobile ui", "sqlite", "rest api", "firebase", "state management"
    ],
    "qa / automation test engineer": [
        "selenium", "cypress", "playwright", "jest", "postman", "api testing", 
        "automation testing", "manual testing", "jira", "load testing", "python", "javascript"
    ],
    "blockchain / web3 developer": [
        "solidity", "ethereum", "smart contracts", "web3js", "ethersjs", "rust", 
        "metamask", "truffle", "hardhat", "defi", "cryptography"
    ],
    "ui/ux designer": [
        "figma", "wireframing", "prototyping", "user research", "ui design", "ux design", 
        "design systems", "information architecture", "interaction design", "adobe xd"
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

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
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
            report_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Ensure report_json column exists if database was previously initialized
    cursor.execute("PRAGMA table_info(analyses)")
    columns = [col[1] for col in cursor.fetchall()]
    if "report_json" not in columns:
        cursor.execute("ALTER TABLE analyses ADD COLUMN report_json TEXT")

    # Login tracking: per-user summary columns + a full login history table
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in cursor.fetchall()]
    if "last_login" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
    if "login_count" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            event TEXT NOT NULL DEFAULT 'login',
            ip_address TEXT,
            user_agent TEXT,
            logged_in_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute("SELECT id FROM users WHERE email = 'admin@scanline.com'")
    if not cursor.fetchone():
        admin_pass = generate_password_hash(os.environ.get("ADMIN_PASSWORD", "admin123456"))
        cursor.execute(
            "INSERT INTO users (name, email, password, is_admin, created_at) VALUES (?, ?, ?, ?, ?)",
            ("System Administrator", "admin@scanline.com", admin_pass, 1, datetime.now(timezone.utc).isoformat())
        )
    
    conn.commit()
    conn.close()

init_db()

def record_login(user_id, name, email, event="login"):
    """Save who logged in (name + email), when, and from where. Never blocks the login itself."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        ip = (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()
        agent = (request.headers.get("User-Agent") or "")[:200]
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO login_logs (user_id, name, email, event, ip_address, user_agent, logged_in_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, email, event, ip, agent, now)
        )
        cur.execute(
            "UPDATE users SET last_login = ?, login_count = COALESCE(login_count, 0) + 1 WHERE id = ?",
            (now, user_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error recording login: {e}")

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200
        
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication token missing. Please log in."}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format."}), 401
        
        token = parts[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_id = payload["user_id"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid session token."}), 401

        return f(current_user_id, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == "OPTIONS":
            return jsonify({"status": "ok"}), 200
            
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Admin credentials required."}), 401
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid token header."}), 401
        
        token = parts[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload["user_id"]
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user or user[0] != 1:
                return jsonify({"error": "Forbidden: Admin privileges required."}), 403

        except Exception:
            return jsonify({"error": "Invalid or expired admin session token."}), 401

        return f(user_id, *args, **kwargs)
    return decorated

# =====================================================================
#  SCORING ENGINE v2  (accurate, explainable, deterministic)
# =====================================================================

# Add a few universally expected skills that were missing from the matrix
for _r in ("frontend developer", "backend developer", "python developer"):
    if "git" not in ROLE_SKILL_MATRIX[_r]:
        ROLE_SKILL_MATRIX[_r].append("git")

# Extra role names people commonly type (merged into ROLE_ALIASES)
_EXTRA_ROLE_ALIASES = {
    "frontend developer": ["ui engineer", "next developer", "web ui developer", "frontend engineer", "front end engineer"],
    "backend developer": ["api developer", "server side developer", "golang developer", "go developer",
                          "c# developer", ".net developer", "dotnet developer", "backend engineer", "back end engineer"],
    "full stack developer": ["mern stack", "mean stack", "software developer", "web application developer", "full stack engineer"],
    "web developer": ["javascript developer", "html developer", "web designer"],
    "data scientist": ["data science intern", "ml scientist"],
    "devops engineer": ["devops", "platform engineer", "infrastructure engineer"],
    "mobile app developer": ["react native", "flutter", "android", "ios"],
}
for _k, _v in _EXTRA_ROLE_ALIASES.items():
    ROLE_ALIASES.setdefault(_k, [])
    ROLE_ALIASES[_k] = list(dict.fromkeys(ROLE_ALIASES[_k] + _v))
# "mean" on its own is a normal English word -> only the full phrase is safe
ROLE_ALIASES["full stack developer"] = [a for a in ROLE_ALIASES["full stack developer"] if a != "mean"]
# "python developer" has its own profile; do not also claim it for backend
ROLE_ALIASES["backend developer"] = [a for a in ROLE_ALIASES["backend developer"] if a != "python developer"]

# ---------------------------------------------------------------------
#  Skill aliases  (what people actually write on resumes)
# ---------------------------------------------------------------------
SKILL_ALIASES = {
    "html": ["html5"],
    "css": ["css3"],
    "python": ["python3", "python 3"],
    "bootstrap": ["bootstrap5", "bootstrap 5"],
    "javascript": ["js", "ecmascript", "es6", "es2015"],
    "react": ["reactjs", "react.js", "react js"],
    "nextjs": ["next.js", "next js"],
    "vue": ["vuejs", "vue.js", "vue js"],
    "angular": ["angularjs", "angular.js"],
    "tailwind": ["tailwindcss", "tailwind css"],
    "node": ["nodejs", "node.js", "node js"],
    "express": ["expressjs", "express.js", "express js", "express framework", "mern", "mern stack"],
    "rest api": ["rest", "restful", "restful api", "restful apis", "rest apis", "restful services", "rest services", "api development"],
    "postgresql": ["postgres", "psql"],
    "mongodb": ["mongo db", "mongo"],
    "sql": ["mysql", "postgresql", "postgres", "sqlite", "sql server", "mssql", "mariadb", "pl/sql", "plsql", "t-sql", "oracle db"],
    "ci/cd": ["cicd", "ci cd", "ci-cd", "continuous integration", "continuous deployment", "continuous delivery",
              "github actions", "jenkins", "gitlab ci"],
    "aws": ["amazon web services"],
    "gcp": ["google cloud", "google cloud platform"],
    "azure": ["microsoft azure"],
    "kubernetes": ["k8s"],
    "golang": ["go lang", "go programming", "go language"],
    "spring boot": ["springboot", "spring-boot", "spring framework"],
    "c#": ["csharp", "c sharp"],
    ".net": ["dotnet", "dot net", "asp.net", ".net core", "asp net"],
    "responsive design": ["responsive", "mobile-first", "mobile first", "cross-browser", "media queries"],
    "web performance": ["performance optimization", "core web vitals", "lighthouse", "page speed"],
    "llms": ["llm", "large language model", "large language models"],
    "nlp": ["natural language processing"],
    "machine learning": ["ml models", "ml model"],
    "deep learning": ["neural network", "neural networks", "cnn", "rnn"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "hugging face": ["huggingface", "hugging-face", "transformers library"],
    "rag": ["retrieval augmented generation", "retrieval-augmented generation"],
    "vector database": ["vector db", "vector store", "vector databases", "faiss"],
    "prompt engineering": ["prompt design", "prompting"],
    "fine-tuning": ["fine tuning", "finetuning", "lora", "qlora"],
    "data visualization": ["data visualisation", "dashboards", "data viz"],
    "power bi": ["powerbi"],
    "etl": ["elt", "data pipelines", "data pipeline"],
    "data warehousing": ["data warehouse", "data warehouses"],
    "apache spark": ["spark", "pyspark"],
    "penetration testing": ["pentest", "pen testing", "pentesting", "ethical hacking"],
    "vulnerability assessment": ["vapt", "vulnerability scanning", "vulnerability management"],
    "network security": ["network defense", "network defence"],
    "incident response": ["incident handling"],
    "firewalls": ["firewall"],
    "automation testing": ["test automation", "automated testing", "automation tester"],
    "manual testing": ["manual qa", "functional testing"],
    "api testing": ["api test", "rest assured"],
    "load testing": ["performance testing", "jmeter", "k6"],
    "web3js": ["web3.js", "web3 js"],
    "ethersjs": ["ethers.js", "ethers js"],
    "smart contracts": ["smart contract"],
    "ui design": ["user interface design", "visual design"],
    "ux design": ["user experience design", "ux/ui", "ui/ux"],
    "user research": ["usability testing", "user interviews", "ux research"],
    "design systems": ["design system", "component library"],
    "wireframing": ["wireframes", "wireframe"],
    "prototyping": ["prototypes", "prototype"],
    "state management": ["bloc", "provider", "riverpod", "getx"],
    "mobile ui": ["mobile ui design", "mobile interface"],
    "microservices": ["microservice", "micro-services"],
    "jwt": ["json web token", "json web tokens"],
    "github actions": ["gh actions"],
    "framer motion": ["framer-motion"],
    "linux": ["ubuntu", "unix"],
    "bash": ["shell scripting", "shell script"],
    "statistics": ["statistical analysis", "statistical modeling", "hypothesis testing"],
    "pandas": ["dataframes"],
    "ios": ["ios development", "ios app"],
    "android": ["android development", "android studio"],
    "ethereum": ["evm"],
    "mlops": ["ml ops", "model deployment"],
    "cryptography": ["encryption"],
    "serverless": ["aws lambda", "cloud functions"],
    "lambda": ["aws lambda"],
    "s3": ["amazon s3", "aws s3"],
    "ec2": ["amazon ec2", "aws ec2"],
    "iam": ["identity and access management"],
    "vpc": ["virtual private cloud"],
    "soc": ["security operations center", "security operations centre"],
    "siem": ["splunk", "qradar", "sentinel"],
    "agile": ["scrum", "kanban", "sprint planning"],
    "oop": ["object oriented", "object-oriented", "oops"],
    "unit testing": ["unit tests", "unit test", "tdd"],
    "data structures": ["dsa", "data structures and algorithms"],
}

# Skills that are too short / too ambiguous for plain word matching.
# They only count when they appear in a recognisable programming context.
_LIST_SEP_BEFORE = r"(?:(?<=,)|(?<=, )|(?<=/)|(?<=\| )|(?<=\|)|(?<=: )|(?<=• ))"
SPECIAL_SKILL_PATTERNS = {
    "c": r"(?<![a-z0-9+#.])(?:c\s*/\s*c\+\+|c\s*,\s*c\+\+|c\s+programming|c\s+language)(?![a-z0-9+#])"
         r"|" + _LIST_SEP_BEFORE + r"c(?=\s*(?:,|;|\||/\s*c\+\+))",
    "r": r"(?<![a-z0-9+#.])(?:r\s+programming|r\s+language|rstudio|ggplot2?|tidyverse)(?![a-z0-9+#])"
         r"|" + _LIST_SEP_BEFORE + r"r(?=\s*(?:,|;|\||/))",
    "express": r"(?<![a-z0-9])express(?:\.js|js)(?![a-z0-9])"
               r"|(?<![a-z0-9])express\s+(?:framework|server|app|api|middleware|routes?|router)(?![a-z0-9])"
               r"|node(?:\.js|js)?\s*[/,&+]\s*express(?![a-z0-9])"
               r"|(?<![a-z0-9])mern(?:\s+stack)?(?![a-z0-9])",
    "networking": r"(?<![a-z0-9])(?:computer\s+networks?|cloud\s+networking|tcp\s*/?\s*ip|"
                  r"networking\s+(?:fundamentals|protocols|concepts)|network\s+protocols|dns|vlan)(?![a-z0-9])",
}

# Role profiles: which skills are essential (core), which are "any one of" groups
# (e.g. a Java developer must not be punished for not knowing Python), and the rest.
# core weight = 3, group weight is given per group, normal weight = 1.
ROLE_PROFILES = {
    "frontend developer": {
        "core": ["html", "css", "javascript"],
        "groups": [(["react", "nextjs", "vue", "angular"], 1, 3), (["tailwind", "bootstrap", "sass"], 1, 1),
                   (["redux", "zustand"], 1, 1), (["vite", "webpack"], 1, 1), (["gsap", "framer motion"], 1, 1)],
    },
    "backend developer": {
        "core": ["rest api"],
        "groups": [(["node", "python", "java", "golang", "c#", "c"], 1, 3),
                   (["express", "django", "flask", "fastapi", "spring boot", ".net"], 1, 3),
                   (["sql", "postgresql", "mysql", "mongodb"], 1, 3), (["kafka", "rabbitmq"], 1, 1)],
    },
    "full stack developer": {
        "core": ["html", "css", "javascript", "rest api", "git"],
        "groups": [(["react", "nextjs"], 1, 3), (["node", "express", "python"], 1, 3),
                   (["sql", "postgresql", "mongodb"], 1, 3)],
    },
    "web developer": {
        "core": ["html", "css", "javascript", "responsive design"],
        "groups": [(["tailwind", "bootstrap"], 1, 1)],
    },
    "python developer": {
        "core": ["python"],
        "groups": [(["django", "flask", "fastapi"], 1, 3), (["sql", "postgresql"], 1, 3)],
    },
    "ai/ml engineer": {
        "core": ["python", "machine learning", "deep learning"],
        "groups": [(["pytorch", "tensorflow"], 1, 3), (["vector database", "pinecone", "chroma"], 1, 1),
                   (["langchain", "llamaindex"], 1, 1)],
    },
    "generative ai engineer": {
        "core": ["python", "llms", "rag", "prompt engineering"],
        "groups": [(["langchain", "llamaindex"], 1, 2), (["vector database", "pinecone", "chroma"], 1, 2),
                   (["gemini api", "openai api"], 1, 2)],
    },
    "data scientist": {
        "core": ["machine learning", "sql", "statistics"],
        "groups": [(["python", "r"], 1, 3), (["data visualization", "matplotlib", "seaborn", "tableau", "power bi"], 1, 2)],
    },
    "data engineer": {
        "core": ["sql", "etl", "python"],
        "groups": [(["apache spark", "hadoop"], 1, 2), (["snowflake", "bigquery", "postgresql", "data warehousing"], 1, 2)],
    },
    "devops engineer": {
        "core": ["linux", "docker", "kubernetes", "ci/cd"],
        "groups": [(["aws", "azure", "gcp"], 1, 3), (["terraform", "ansible"], 1, 2),
                   (["prometheus", "grafana"], 1, 1)],
    },
    "cloud architect / engineer": {
        "core": [],
        "groups": [(["aws", "azure", "gcp"], 1, 4), (["terraform", "cloudformation"], 1, 2),
                   (["lambda", "serverless"], 1, 1), (["s3", "ec2"], 1, 1)],
    },
    "cybersecurity analyst": {
        "core": ["network security", "vulnerability assessment", "incident response"],
        "groups": [],
    },
    "mobile app developer": {
        "core": [],
        "groups": [(["react native", "flutter", "dart", "swift", "kotlin"], 1, 4), (["ios", "android"], 1, 2)],
    },
    "qa / automation test engineer": {
        "core": [],
        "groups": [(["selenium", "cypress", "playwright"], 1, 3), (["automation testing", "manual testing"], 1, 2),
                   (["python", "javascript"], 1, 1)],
    },
    "blockchain / web3 developer": {
        "core": ["solidity", "smart contracts", "ethereum"],
        "groups": [(["web3js", "ethersjs"], 1, 2), (["truffle", "hardhat"], 1, 2)],
    },
    "ui/ux designer": {
        "core": ["wireframing", "prototyping", "user research"],
        "groups": [(["figma", "adobe xd"], 1, 3)],
    },
}

# Extra skills that are not part of any role profile but are common in job descriptions
EXTRA_JD_SKILLS = [
    "git", "agile", "jira", "linux", "bash", "figma", "excel", "oop", "data structures", "unit testing",
    "microservices", "jwt", "json", "ajax", "jquery", "php", "laravel", "ruby", "scala", "kotlin", "swift",
    "firebase", "nosql", "elasticsearch", "oauth", "websockets", "docker", "kubernetes", "ci/cd", "aws",
    "azure", "gcp", "redis", "graphql", "typescript", "sass", "tableau", "power bi", "etl", "airflow",
]

LISTED_ONLY_CREDIT = 0.8      # skill is only in a "Skills" list, never shown in projects/experience
CORE_WEIGHT = 3
NORMAL_WEIGHT = 1

# ---------------------------------------------------------------------
#  Skill matching helpers
# ---------------------------------------------------------------------
_SKILL_REGEX_CACHE = {}

def get_skill_regex(skill):
    rx = _SKILL_REGEX_CACHE.get(skill)
    if rx is not None:
        return rx
    if skill in SPECIAL_SKILL_PATTERNS:
        rx = re.compile(SPECIAL_SKILL_PATTERNS[skill])
    else:
        forms = [skill] + SKILL_ALIASES.get(skill, [])
        alts = []
        for f in forms:
            parts = [re.escape(p) for p in f.split()]
            alts.append(r"[\s\-]+".join(parts))
        rx = re.compile(r"(?<![a-z0-9+#])(?:" + "|".join(alts) + r")(?![a-z0-9+#])")
    _SKILL_REGEX_CACHE[skill] = rx
    return rx

def skill_present(skill, text_lower):
    return bool(text_lower) and bool(get_skill_regex(skill).search(text_lower))

def all_known_skills():
    seen = []
    for skills in ROLE_SKILL_MATRIX.values():
        for s in skills:
            if s not in seen:
                seen.append(s)
    for s in EXTRA_JD_SKILLS:
        if s not in seen:
            seen.append(s)
    return seen

# ---------------------------------------------------------------------
#  Text extraction
# ---------------------------------------------------------------------
def clean_extracted_text(text):
    if not text:
        return ""
    text = text.replace('\xa0', ' ').replace('\r\n', '\n').replace('\r', '\n').replace('\u200b', '')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_text_from_pdf(file_bytes):
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        # join pages with a newline so the last line of one page never glues to the first of the next
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return clean_extracted_text(text)
    except Exception:
        return ""

def extract_text_from_docx(file_bytes):
    try:
        document = docx.Document(io.BytesIO(file_bytes))
        chunks = []
        # contact details very often live in the page header
        for section in document.sections:
            try:
                chunks.extend(p.text for p in section.header.paragraphs)
            except Exception:
                pass
        chunks.extend(p.text for p in document.paragraphs)
        # many resume templates are built with tables
        for table in document.tables:
            for row in table.rows:
                seen_cells = set()
                for cell in row.cells:
                    if id(cell._tc) in seen_cells:
                        continue
                    seen_cells.add(id(cell._tc))
                    chunks.extend(p.text for p in cell.paragraphs)
        return clean_extracted_text("\n".join(chunks))
    except Exception:
        return ""

def normalize_text(text):
    t = (text or "").lower()
    t = t.replace('\u2013', '-').replace('\u2014', '-').replace('\u2019', "'")
    return t

# ---------------------------------------------------------------------
#  Section detection (by real headings, not by random words in the text)
# ---------------------------------------------------------------------
HEADING_PHRASES = {
    "Summary": ["summary", "professional summary", "profile", "career objective", "objective",
                "about me", "about", "career summary", "personal statement"],
    "Experience": ["experience", "work experience", "professional experience", "employment",
                   "employment history", "work history", "internship", "internships",
                   "internship experience", "industrial training", "training"],
    "Education": ["education", "academic background", "academics", "academic qualification",
                  "academic qualifications", "qualification", "qualifications", "education and training",
                  "educational background", "academic details"],
    "Skills": ["skills", "technical skills", "key skills", "core competencies", "technologies",
               "tech stack", "skills and tools", "skills and technologies", "technical proficiency",
               "technical expertise", "tools and technologies", "areas of expertise", "competencies"],
    "Projects": ["projects", "personal projects", "academic projects", "key projects",
                 "selected projects", "project work", "major projects", "project experience"],
    "Certifications": ["certifications", "certificates", "certification", "licenses", "licenses and certifications",
                       "courses", "achievements", "awards", "awards and achievements", "honors", "accomplishments"],
}
_HEADING_LOOKUP = {p: name for name, phrases in HEADING_PHRASES.items() for p in phrases}
_MIN_WORDS_FOR_SECTION = {"Skills": 2, "Summary": 5}

def _norm_heading(s):
    s = s.strip().lower().replace("&", " and ")
    s = re.sub(r"^[\W_]+|[\W_]+$", "", s)
    return re.sub(r"\s+", " ", s)

def detect_heading(line):
    raw = line.strip()
    if not raw:
        return None
    # inline heading  ->  "Skills: Python, SQL"
    m = re.match(r"^([A-Za-z &/]{3,40}?)\s*[:\-\u2013|]\s*(.+)$", raw)
    if m:
        name = _HEADING_LOOKUP.get(_norm_heading(m.group(1)))
        if name:
            return name, m.group(2)
    if len(raw) <= 45:
        name = _HEADING_LOOKUP.get(_norm_heading(raw))
        if name:
            return name, ""
    return None

def split_sections(raw_text):
    sections = {}
    current = "_header"
    for line in raw_text.split("\n"):
        h = detect_heading(line)
        if h:
            current, rest = h
            sections.setdefault(current, [])
            if rest:
                sections[current].append(rest)
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v) for k, v in sections.items()}

def real_sections(sections):
    """A heading only counts if there is real content below it ('Projects: none' is not a section)."""
    found = []
    for name, body in sections.items():
        if name == "_header":
            continue
        words = re.findall(r"[A-Za-z0-9+#]{2,}", body)
        if len(words) >= _MIN_WORDS_FOR_SECTION.get(name, 3):
            found.append(name)
    return found

# ---------------------------------------------------------------------
#  Contact detection
# ---------------------------------------------------------------------
_EMAIL_RE = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_PHONE_RES = [
    re.compile(r"(?<!\d)(?:\+?91[\s-]?)?0?[6-9]\d{4}[\s-]?\d{5}(?!\d)"),                       # India
    re.compile(r"(?<!\d)\+\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}(?!\d)"),      # +country code
    re.compile(r"(?<!\d)\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}(?!\d)"),                              # US style
]
_LINKEDIN_RE = re.compile(r"linkedin\.com/(?:in|pub)/[a-z0-9_%\-]+")
_GITHUB_RE = re.compile(r"github\.com/[a-z0-9_\-]+")
_PORTFOLIO_RES = [
    re.compile(r"(?:https?://|www\.)(?!(?:www\.)?(?:linkedin|github)\.com)[a-z0-9\-]+(?:\.[a-z0-9\-]+)*\.[a-z]{2,}[^\s,;|)]*"),
    re.compile(r"(?<![a-z0-9@.])[a-z0-9\-]+\.(?:vercel\.app|netlify\.app|github\.io|web\.app|pages\.dev|onrender\.com|herokuapp\.com|framer\.website|notion\.site)"),
]

def extract_contact(raw_text):
    email = _EMAIL_RE.search(raw_text)
    text_wo_email = _EMAIL_RE.sub(" ", raw_text)
    phone = None
    for rx in _PHONE_RES:
        m = rx.search(text_wo_email)
        if m:
            digits = re.sub(r"\D", "", m.group(0))
            if 10 <= len(digits) <= 13:
                phone = m.group(0).strip()
                break
    low = text_wo_email.lower()
    linkedin = _LINKEDIN_RE.search(low)
    github = _GITHUB_RE.search(low)
    low_wo_social = _LINKEDIN_RE.sub(" ", _GITHUB_RE.sub(" ", low))
    portfolio = None
    for rx in _PORTFOLIO_RES:
        m = rx.search(low_wo_social)
        if m:
            portfolio = m.group(0)
            break
    return {
        "email": email.group(0) if email else None,
        "phone": phone,
        "linkedin": linkedin.group(0) if linkedin else None,
        "github": github.group(0) if github else None,
        "portfolio": portfolio,
    }

# ---------------------------------------------------------------------
#  Impact: action verbs + quantified achievements
# ---------------------------------------------------------------------
_VERB_PATTERNS = {
    "build": r"built|build(?:s|ing)?", "develop": r"develop(?:ed|s|ing)?", "architect": r"architect(?:ed|ing)?",
    "engineer": r"engineered", "implement": r"implement(?:ed|s|ing)?", "design": r"designed|designing",
    "optimize": r"optimi[sz](?:ed|es|ing)", "deploy": r"deploy(?:ed|s|ing)?", "scale": r"scaled|scaling",
    "create": r"created|creating", "integrate": r"integrat(?:ed|es|ing)", "manage": r"managed|managing",
    "refactor": r"refactor(?:ed|ing)?", "automate": r"automat(?:ed|es|ing)", "execute": r"executed",
    "collaborate": r"collaborat(?:ed|es|ing)", "spearhead": r"spearhead(?:ed)?", "solve": r"solved|solving",
    "lead": r"led|leading", "launch": r"launch(?:ed|ing)", "improve": r"improv(?:ed|ing)",
    "reduce": r"reduc(?:ed|ing)", "increase": r"increas(?:ed|ing)", "deliver": r"deliver(?:ed|ing)",
    "migrate": r"migrat(?:ed|ing)", "configure": r"configur(?:ed|ing)", "maintain": r"maintain(?:ed|ing)",
    "mentor": r"mentor(?:ed|ing)", "analyze": r"analy[sz](?:ed|ing)", "test": r"tested",
    "debug": r"debugg?(?:ed|ing)", "enhance": r"enhanc(?:ed|ing)", "establish": r"establish(?:ed|ing)",
    "coordinate": r"coordinat(?:ed|ing)", "resolve": r"resolv(?:ed|ing)", "monitor": r"monitor(?:ed|ing)",
    "contribute": r"contribut(?:ed|ing)", "ship": r"shipped|shipping", "redesign": r"redesign(?:ed|ing)",
    "train": r"trained", "research": r"researched", "streamline": r"streamlin(?:ed|ing)",
    "accelerate": r"accelerat(?:ed|ing)", "secure": r"secured", "orchestrate": r"orchestrat(?:ed|ing)",
}
_VERB_RES = {k: re.compile(r"\b(?:" + v + r")\b") for k, v in _VERB_PATTERNS.items()}
ACTION_VERBS = list(_VERB_PATTERNS.keys())   # kept for backwards compatibility

_METRIC_RE = re.compile(
    r"(?<![\w.])\d+(?:[.,]\d+)?\s?(?:%|\+(?!\s?(?:years?|yrs?|months?))|x\b|k\b|m\b|ms\b|sec(?:ond)?s?\b|"
    r"users?\b|customers?\b|clients?\b|requests?\b|projects?\b|endpoints?\b|records?\b|documents?\b|"
    r"hours?\b|lpa\b|lakhs?\b|crores?\b|downloads?\b|students?\b|members?\b|stars?\b)"
    r"|[$\u20b9]\s?\d|\b(?:rs\.?|inr)\s?\d"
)
_EDU_NOISE = re.compile(r"cgpa|gpa|percentage|percentile|\bssc\b|\bhsc\b|marks|grade|sgpa|10th|12th|class x")

def count_action_verbs(text_lower):
    return [k for k, rx in _VERB_RES.items() if rx.search(text_lower)]

def count_metrics(sections, raw_text):
    if len(real_sections(sections)) >= 2:
        parts = [b for n, b in sections.items() if n not in ("Education", "_header")]
        body = "\n".join(parts)
    else:
        body = raw_text
    hits = 0
    for line in body.lower().split("\n"):
        if _EDU_NOISE.search(line):
            continue
        hits += len(_METRIC_RE.findall(line))
    return hits

# ---------------------------------------------------------------------
#  Role resolution
# ---------------------------------------------------------------------
_GENERIC_TITLE_WORDS = {
    "developer", "engineer", "analyst", "designer", "software", "senior", "junior", "jr", "sr", "intern",
    "trainee", "associate", "lead", "principal", "staff", "fresher", "entry", "level", "specialist",
    "consultant", "architect", "programmer", "executive", "manager", "and", "the", "a", "of", "for", "with",
    "remote", "full", "time", "part", "role", "position", "job", "technical", "technology", "it",
}

def _clean_title(t):
    t = (t or "").lower().strip()
    t = re.sub(r"(?<=[a-z])\.?js\b", "", t)          # node.js / reactjs -> node / react
    t = re.sub(r"[^a-z0-9+#/ ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

_ROLE_PHRASE_RES = None
def _role_phrase_regexes():
    global _ROLE_PHRASE_RES
    if _ROLE_PHRASE_RES is None:
        _ROLE_PHRASE_RES = []
        for role in ROLE_SKILL_MATRIX:
            phrases = [(_clean_title(role), True)] + [(_clean_title(a), False) for a in ROLE_ALIASES.get(role, [])]
            for ph, canonical in phrases:
                if ph:
                    rx = re.compile(r"(?<![a-z0-9])" + r"\s+".join(re.escape(w) for w in ph.split()) + r"(?![a-z0-9])")
                    _ROLE_PHRASE_RES.append((role, ph, canonical, rx))
    return _ROLE_PHRASE_RES

def resolve_role_keys(job_title_input):
    """Map a typed job title to 1-2 known role profiles. Returns [] when it cannot be done reliably."""
    cleaned = _clean_title(job_title_input)
    if not cleaned:
        return []
    found = []
    for role, ph, canonical, rx in _role_phrase_regexes():
        m = rx.search(cleaned)
        if m:
            found.append((m.end() - m.start(), canonical, m.start(), m.end(), role))
    if found:
        found.sort(key=lambda x: (-x[0], not x[1]))
        chosen, used = [], []
        for length, _c, s, e, role in found:
            if any(not (e <= us or s >= ue) for us, ue in used):
                continue                       # overlaps an already accepted, longer phrase
            used.append((s, e))
            if role not in chosen:
                chosen.append(role)
        return chosen[:2]

    # fallback: the title names a technology, e.g. "Tableau Specialist", "Django Intern"
    meaningful = " ".join(w for w in cleaned.split() if w not in _GENERIC_TITLE_WORDS)
    if not meaningful:
        return []
    votes = {}
    for role, skills in ROLE_SKILL_MATRIX.items():
        for s in skills:
            if skill_present(s, meaningful):
                votes[role] = votes.get(role, 0) + 1
    if not votes:
        return []
    top = max(votes.values())
    best = [r for r, v in votes.items() if v == top]
    return best if len(best) <= 2 else []

def match_target_roles(job_title_input):
    """Backward compatible helper: skills list for a typed role (None if unknown)."""
    keys = resolve_role_keys(job_title_input)
    if not keys:
        return None
    skills = []
    for k in keys:
        for s in ROLE_SKILL_MATRIX[k]:
            if s not in skills:
                skills.append(s)
    return skills

def build_role_units(role_keys):
    units, seen = [], set()
    for rk in role_keys:
        prof = ROLE_PROFILES.get(rk, {"core": [], "groups": []})
        for s in prof["core"]:
            if s not in seen:
                units.append({"kind": "skill", "skill": s, "weight": CORE_WEIGHT}); seen.add(s)
        for members, need, weight in prof["groups"]:
            members = [m for m in members if m not in seen]
            if members:
                units.append({"kind": "group", "members": members, "need": need, "weight": weight})
                seen.update(members)
        for s in ROLE_SKILL_MATRIX.get(rk, []):
            if s not in seen:
                units.append({"kind": "skill", "skill": s, "weight": NORMAL_WEIGHT}); seen.add(s)
    return units

def extract_jd_units(job_description):
    """Pull the skills a job description asks for, with importance weights."""
    jd = (job_description or "").lower()
    if len(jd.strip()) < 20:
        return []
    lines = [l for l in re.split(r"\n|(?<=[.;])\s", jd) if l.strip()]
    optional_re = re.compile(r"preferred|nice to have|good to have|bonus|\bplus\b|optional|desirable")
    must_re = re.compile(r"required|must|mandatory|essential|proficien|strong|expert|hands-on|minimum")
    units = []
    for skill in all_known_skills():
        if not skill_present(skill, jd):
            continue
        occurrences = len(get_skill_regex(skill).findall(jd))
        weight = 2 if occurrences >= 2 else 1
        for line in lines:
            if skill_present(skill, line):
                if optional_re.search(line):
                    weight = min(weight, 0.5)
                elif must_re.search(line):
                    weight = max(weight, 2)
                break
        units.append({"kind": "skill", "skill": skill, "weight": weight})
    return units

# ---------------------------------------------------------------------
#  Skill scoring
# ---------------------------------------------------------------------
def score_units(units, text_lower, context_lower):
    matched, missing, listed_only = [], [], []
    total_w = got_w = 0.0

    def credit_for(skill):
        return 1.0 if skill_present(skill, context_lower) else LISTED_ONLY_CREDIT

    for u in units:
        total_w += u["weight"]
        if u["kind"] == "skill":
            s = u["skill"]
            if skill_present(s, text_lower):
                c = credit_for(s)
                matched.append(s)
                if c < 1:
                    listed_only.append(s)
                got_w += u["weight"] * c
            else:
                missing.append(s)
        else:
            present = [m for m in u["members"] if skill_present(m, text_lower)]
            credits = [credit_for(m) for m in present]
            for m, c in zip(present, credits):
                matched.append(m)
                if c < 1:
                    listed_only.append(m)
            got_w += u["weight"] * min(1.0, sum(credits) / u["need"])
            if len(present) < u["need"]:
                missing.extend(m for m in u["members"] if m not in present)
            # when the group is satisfied the alternatives are NOT reported as missing
    pct = int(round(100 * got_w / total_w)) if total_w else 0
    return {"pct": pct, "matched": matched, "missing": missing, "listed_only": listed_only,
            "total": len(matched) + len(missing)}

def auto_detect_matching_roles(text_lower, resume_words_set=None, context_lower=None):
    context_lower = text_lower if context_lower is None else context_lower
    results = []
    for role in ROLE_SKILL_MATRIX:
        res = score_units(build_role_units([role]), text_lower, context_lower)
        if len(res["matched"]) < 3:
            continue
        pct = res["pct"] * (0.92 if role == "web developer" else 1.0)
        results.append({"role": role, "score": int(round(pct)), "matched_count": len(res["matched"]),
                        "matched_skills": res["matched"], "total_skills": res["total"]})
    results.sort(key=lambda x: (x["score"], x["matched_count"]), reverse=True)
    return results

# ---------------------------------------------------------------------
#  Resume validation
# ---------------------------------------------------------------------
def validate_is_resume(text_lower, contact_info, sections_found, word_count):
    has_contact = bool(contact_info["email"] or contact_info["phone"] or contact_info["linkedin"] or contact_info["github"])
    has_standard_sections = len(sections_found) >= 2
    resume_buzzwords = [
        "curriculum vitae", "resume", "experience", "education", "skills",
        "projects", "certifications", "bachelor", "b.tech", "bca", "college",
        "university", "academic", "developer", "engineer", "responsibilities"
    ]
    buzzword_count = sum(1 for w in resume_buzzwords if re.search(r'\b' + re.escape(w) + r'\b', text_lower))

    if word_count < 60:
        return False, "Insufficient document content (<60 words). Please upload a complete resume."
    if not has_contact and not has_standard_sections:
        return False, "Random file rejected. Document lacks contact details and standard sections (Skills, Projects, Education)."
    if buzzword_count < 2 and not has_standard_sections:
        return False, "Invalid document structure. Please upload a verified CV or Resume file."
    return True, ""

# ---------------------------------------------------------------------
#  Main analysis
# ---------------------------------------------------------------------
_DATE_RANGE_RE = re.compile(
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?,?\s+(?:19|20)\d{2}"
    r"|(?:19|20)\d{2}\s*(?:-|\u2013|\u2014|to)\s*(?:(?:19|20)\d{2}|present|current|now|ongoing)", re.I)
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

def _band(value, bands):
    """bands = [(min_inclusive, points), ...] sorted descending by min."""
    for lo, pts in bands:
        if value >= lo:
            return pts
    return bands[-1][1]

def analyze_resume_text(raw_text, job_title, job_desc):
    raw_text = raw_text or ""
    text_lower = normalize_text(raw_text)
    words = re.findall(r'\b[a-zA-Z0-9+#.-]+\b', text_lower)
    word_count = len(words)
    resume_words_set = set(words)

    contact_info = extract_contact(raw_text)

    # ---- sections (real headings with real content) ----
    sections = split_sections(raw_text)
    sections_found = real_sections(sections)
    if len(sections_found) < 2:
        # headings could not be separated (e.g. odd PDF layout) -> fall back to strong keywords only
        for name, kws in (("Experience", ["experience"]), ("Education", ["education"]), ("Skills", ["skills"]),
                          ("Projects", ["projects"]), ("Certifications", ["certifications", "certificates"])):
            if name not in sections_found and any(re.search(r"\b" + k + r"\b", text_lower) for k in kws):
                sections_found.append(name)
    structured = len(real_sections(sections)) >= 2

    # evidence text = everything except the plain "Skills" list and the header
    if structured:
        context_lower = normalize_text("\n".join(b for n, b in sections.items() if n not in ("Skills", "_header")))
    else:
        context_lower = text_lower

    detected_roles = auto_detect_matching_roles(text_lower, None, context_lower)

    # ---- decide what we score the resume against ----
    title = (job_title or "").strip()
    jd_units = extract_jd_units(job_desc)
    notes = []
    if len(jd_units) >= 3:
        units, source = jd_units, "job_description"
        effective_role = title if title else (detected_roles[0]["role"].title() if detected_roles else "Job Description")
    else:
        role_keys = resolve_role_keys(title) if title else []
        if role_keys:
            units, source = build_role_units(role_keys), "role_profile"
            effective_role = title
        elif title:
            if detected_roles:
                units = build_role_units([detected_roles[0]["role"]])
                source = "closest_profile"
                notes.append(f"'{title}' is not in our role library, so your resume was compared with the closest "
                             f"profile found in it ({detected_roles[0]['role'].title()}). Paste the job description "
                             f"for an exact match.")
            else:
                units, source = [], "none"
            effective_role = title
        elif detected_roles:
            units, source = build_role_units([detected_roles[0]["role"]]), "auto_detected"
            effective_role = detected_roles[0]["role"].title()
        else:
            units, source, effective_role = [], "none", "General Profile"
        if job_desc and job_desc.strip() and len(jd_units) < 3:
            notes.append("The job description had fewer than 3 recognisable skills, so it was not used for matching.")

    res = score_units(units, text_lower, context_lower) if units else \
        {"pct": 0, "matched": [], "missing": [], "listed_only": [], "total": 0}
    matched_skills, missing_skills = res["matched"], res["missing"]
    match_score = res["pct"]

    score_breakdown, suggestions = [], list(notes)

    # 1. Contact (15) --------------------------------------------------
    contact_pts = (4 if contact_info["email"] else 0) + (4 if contact_info["phone"] else 0) + \
                  (4 if contact_info["linkedin"] else 0) + (3 if (contact_info["github"] or contact_info["portfolio"]) else 0)
    score_breakdown.append({
        "label": f"Contact Completeness ({contact_pts}/15)",
        "passed": contact_pts >= 12,
        "detail": (f"Email: {'✓' if contact_info['email'] else '✕'} | Phone: {'✓' if contact_info['phone'] else '✕'} | "
                   f"LinkedIn: {'✓' if contact_info['linkedin'] else '✕'} | "
                   f"GitHub/Portfolio: {'✓' if (contact_info['github'] or contact_info['portfolio']) else '✕'}")
    })
    missing_contact = [n for n, ok in (("email", contact_info["email"]), ("mobile number", contact_info["phone"]),
                                        ("LinkedIn URL", contact_info["linkedin"]),
                                        ("GitHub/portfolio link", contact_info["github"] or contact_info["portfolio"])) if not ok]
    if missing_contact:
        suggestions.append("Add missing contact details: " + ", ".join(missing_contact) + ".")

    # 2. Sections (20) ------------------------------------------------
    has = set(sections_found)
    exp_pts = 5 if "Experience" in has else (3 if "Projects" in has else 0)
    sec_pts = (5 if "Skills" in has else 0) + (5 if "Education" in has else 0) + exp_pts + \
              (3 if "Projects" in has else 0) + (2 if ({"Summary", "Certifications"} & has) else 0)
    score_breakdown.append({
        "label": f"Section Hierarchy ({sec_pts}/20)",
        "passed": sec_pts >= 14,
        "detail": f"Detected {len(has)} sections: {', '.join(sorted(has)) if has else 'None'}"
    })
    for name in ("Skills", "Education", "Experience", "Projects"):
        if name not in has:
            suggestions.append(f"Add a clearly titled '{name}' section (a heading on its own line, with content below it).")

    # 3. Content density (15) -----------------------------------------
    if 350 <= word_count <= 850:
        len_pts = 15
    elif 250 <= word_count < 350 or 850 < word_count <= 1000:
        len_pts = 11
    elif 150 <= word_count < 250 or 1000 < word_count <= 1300:
        len_pts = 7
    else:
        len_pts = 3
    score_breakdown.append({
        "label": f"Content Density ({len_pts}/15)",
        "passed": len_pts >= 10,
        "detail": f"Resume contains {word_count} words (ideal: 350-850)."
    })
    if word_count < 350:
        suggestions.append("Your resume is short. Describe each project/job in 2-3 bullet points with the tools used and the result.")
    elif word_count > 1000:
        suggestions.append("Your resume is long. Aim for 1-2 pages (about 350-850 words) and keep only relevant points.")

    # 4. Impact (15) --------------------------------------------------
    verbs_found = count_action_verbs(text_lower)
    metric_hits = count_metrics(sections, raw_text)
    verb_pts = min(8, len(verbs_found))
    metric_pts = 7 if metric_hits >= 3 else (5 if metric_hits == 2 else (3 if metric_hits == 1 else 0))
    impact_pts = verb_pts + metric_pts
    score_breakdown.append({
        "label": f"Impact & Action Verbs ({impact_pts}/15)",
        "passed": impact_pts >= 10,
        "detail": f"Action verbs: {len(verbs_found)} | Quantified results: {metric_hits if metric_hits else 'Missing'}"
    })
    if verb_pts < 6:
        suggestions.append("Start bullet points with strong action verbs such as 'Built', 'Optimized', 'Deployed', 'Reduced'.")
    if metric_hits < 3:
        suggestions.append("Add measurable results (e.g. 'reduced load time by 40%', 'served 2,000+ users') - at least 3 across your resume.")

    # 5. Role skills (25) ---------------------------------------------
    if units:
        skill_pts = int(round(25 * match_score / 100))
        detail = f"Matched {len(matched_skills)} of {res['total']} skills for {effective_role}"
        if source == "job_description":
            detail += " (taken from your job description)"
        elif source == "closest_profile":
            detail += " (closest known profile - role not recognised)"
    else:
        generic_found = [s for s in all_known_skills() if skill_present(s, text_lower)]
        skill_pts = min(25, len(generic_found) * 2)
        detail = f"No target role could be determined; {len(generic_found)} recognised technical skills found."
    score_breakdown.append({
        "label": f"Role Skills Match ({skill_pts}/25)",
        "passed": skill_pts >= 15,
        "detail": detail
    })

    # 6. Parseability (10) --------------------------------------------
    nonblank_lines = [l for l in raw_text.split("\n") if l.strip()]
    single_letters = sum(1 for w in words if len(w) == 1 and w.isalpha() and w not in ("a", "i", "c", "r"))
    garbled = ("\ufffd" in raw_text) or (word_count > 0 and single_letters / word_count > 0.2)
    has_dates = bool(_DATE_RANGE_RE.search(raw_text)) or len(_YEAR_RE.findall(raw_text)) >= 2
    parse_pts = (0 if garbled else 4) + (3 if len(nonblank_lines) >= 8 else 0) + (3 if has_dates else 0)
    score_breakdown.append({
        "label": f"ATS Text Parseability ({parse_pts}/10)",
        "passed": parse_pts >= 8,
        "detail": (f"Readable text: {'✓' if not garbled else '✕'} | Line structure: {'✓' if len(nonblank_lines) >= 8 else '✕'} | "
                   f"Dates found: {'✓' if has_dates else '✕'}")
    })
    if garbled:
        suggestions.append("Text came out garbled when read. Export the resume as a text-based PDF (not an image/scan) with a standard font.")
    if not has_dates:
        suggestions.append("Add dates (e.g. 'Jun 2024 - Dec 2024', '2020 - 2024') to your education, internships and projects.")

    final_ats_score = max(0, min(100, contact_pts + sec_pts + len_pts + impact_pts + skill_pts + parse_pts))

    # ---- skill suggestions ----
    if units:
        weights = {}
        for u in units:
            if u["kind"] == "skill":
                weights[u["skill"]] = u["weight"]
        important_missing = [s for s in missing_skills if weights.get(s, 0) >= 2]
        if source == "job_description" and missing_skills:
            suggestions.append("Keywords from the job description that your resume does not mention: " +
                               ", ".join(missing_skills[:8]) + ". Add them only if you really have these skills.")
        elif important_missing:
            suggestions.append(f"High-priority {effective_role} skills not found: " + ", ".join(important_missing[:6]) + ".")
        elif missing_skills:
            suggestions.append(f"Consider adding relevant {effective_role} skills: " + ", ".join(missing_skills[:6]) + ".")
        lo = res["listed_only"]
        if len(lo) >= 4 and len(lo) >= 0.5 * max(1, len(matched_skills)):
            suggestions.append("These skills appear only in your Skills list, never in a project or job: " +
                               ", ".join(lo[:6]) + ". Show where you used them.")
    elif source == "none":
        suggestions.append("No recognisable technical skills were found. List your technologies under a 'Skills' heading.")

    return {
        "ats_score": final_ats_score,
        "match_score": match_score,
        "effective_role": effective_role,
        "is_custom_role": bool(title),
        "score_version": 2,
        "ats": {
            "score": final_ats_score,
            "word_count": word_count,
            "checks": score_breakdown
        },
        "contact": contact_info,
        "sections_found": sorted(set(sections_found)),
        "suggestions": suggestions,
        "match": {
            "match_score": match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "job_skills_total": res["total"],
            "source": source,
            "listed_only_skills": res["listed_only"]
        }
    }


# ----------------- ROUTES -----------------

@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "online", "service": "Scanline ATS Core"}), 200

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

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return jsonify({"error": "An account with this email already exists."}), 409

        cursor.execute(
            "INSERT INTO users (name, email, password, is_admin, created_at) VALUES (?, ?, ?, 0, ?)",
            (name, email, hashed_password, datetime.now(timezone.utc).isoformat())
        )
        user_id = cursor.lastrowid
        conn.commit()
        record_login(user_id, name, email, "signup")

        token = jwt.encode(
            {"user_id": user_id, "email": email, "is_admin": 0, "exp": datetime.now(timezone.utc) + timedelta(days=7)},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"success": True, "token": token, "name": name, "email": email, "is_admin": False}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
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

        is_admin = bool(user["is_admin"])
        record_login(user["id"], user["name"], user["email"], "login")
        token = jwt.encode(
            {"user_id": user["id"], "email": user["email"], "is_admin": int(is_admin), "exp": datetime.now(timezone.utc) + timedelta(days=7)},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"success": True, "token": token, "name": user["name"], "email": user["email"], "is_admin": is_admin}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/analyze", methods=["POST", "OPTIONS"])
@token_required
def analyze(current_user_id):
    if "resume" not in request.files:
        return jsonify({"error": "Please upload a resume file."}), 400
    
    file = request.files["resume"]
    raw_job_title = request.form.get("job_title", "").strip()
    job_description = request.form.get("job_description", "").strip()

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        return jsonify({"error": "Invalid format. Upload PDF (.pdf), Word (.docx), or Text (.txt) only."}), 400

    file_bytes = file.read()
    text = ""
    if ext == ".pdf":
        text = extract_text_from_pdf(file_bytes)
    elif ext == ".docx":
        text = extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            pass

    if not text.strip():
        return jsonify({"error": "Could not extract text. File might be blank or corrupted."}), 400

    analysis_data = analyze_resume_text(text, raw_job_title, job_description)

    is_valid, validation_msg = validate_is_resume(
        normalize_text(text),
        analysis_data["contact"],
        analysis_data["sections_found"],
        analysis_data["ats"]["word_count"]
    )

    if not is_valid:
        return jsonify({"error": validation_msg, "is_invalid_resume": True}), 422

    stored_history_title = raw_job_title if raw_job_title else f"Auto: {analysis_data['effective_role']}"

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analyses (user_id, filename, job_title, match_score, ats_score, word_count, report_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user_id,
            file.filename,
            stored_history_title,
            analysis_data["match_score"],
            analysis_data["ats_score"],
            analysis_data["ats"]["word_count"],
            json.dumps(analysis_data),
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving analysis: {e}")
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

# ----------------- ADMIN ENDPOINTS -----------------

@app.route("/api/admin/stats", methods=["GET", "OPTIONS"])
@admin_required
def admin_stats(admin_user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analyses")
        total_scans = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(ats_score) FROM analyses")
        avg_ats_row = cursor.fetchone()[0]
        avg_ats = round(avg_ats_row, 1) if avg_ats_row is not None else 0
        
        conn.close()
        return jsonify({
            "total_users": total_users,
            "total_scans": total_scans,
            "average_ats": avg_ats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/users", methods=["GET", "OPTIONS"])
@admin_required
def admin_users(admin_user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                u.id,
                u.name,
                u.email,
                u.is_admin,
                u.created_at,
                u.last_login,
                COALESCE(u.login_count, 0) AS login_count,
                COUNT(a.id) AS scan_count
            FROM users u
            LEFT JOIN analyses a ON u.id = a.user_id
            GROUP BY u.id
            ORDER BY u.id ASC
        ''')
        rows = cursor.fetchall()

        users_list = [{
            "id": r["id"],
            "name": r["name"],
            "email": r["email"],
            "is_admin": bool(r["is_admin"]),
            "created_at": r["created_at"],
            "last_login": r["last_login"],
            "login_count": r["login_count"],
            "scan_count": r["scan_count"]
        } for r in rows]

        conn.close()
        return jsonify({"users": users_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/scans", methods=["GET", "OPTIONS"])
@admin_required
def admin_scans(admin_user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                analyses.id, 
                analyses.ats_score, 
                analyses.match_score,
                analyses.word_count,
                analyses.job_title,
                analyses.report_json,
                analyses.created_at,
                users.name as user_name,
                users.email as user_email
            FROM analyses
            JOIN users ON analyses.user_id = users.id
            ORDER BY analyses.created_at DESC
        ''')
        rows = cursor.fetchall()
        
        scans = []
        for r in rows:
            parsed_report = None
            if r["report_json"]:
                try:
                    parsed_report = json.loads(r["report_json"])
                except Exception:
                    pass
            
            scans.append({
                "id": r["id"],
                "user_name": r["user_name"],
                "user_email": r["user_email"],
                "ats_score": r["ats_score"],
                "match_score": r["match_score"],
                "word_count": r["word_count"],
                "job_title": r["job_title"] or "General",
                "report": parsed_report,
                "created_at": r["created_at"]
            })
        
        conn.close()
        return jsonify({"scans": scans})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admin/logins", methods=["GET", "OPTIONS"])
@admin_required
def admin_logins(admin_user_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, user_id, name, email, event, ip_address, logged_in_at
            FROM login_logs
            ORDER BY logged_in_at DESC
            LIMIT 500
        ''')
        logins = [{
            "id": r["id"],
            "user_id": r["user_id"],
            "name": r["name"],
            "email": r["email"],
            "event": r["event"],
            "ip_address": r["ip_address"] or "—",
            "logged_in_at": r["logged_in_at"]
        } for r in cursor.fetchall()]
        return jsonify({"logins": logins})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route("/api/admin/scan/<int:scan_id>", methods=["DELETE", "OPTIONS"])
@admin_required
def admin_delete_scan(admin_user_id, scan_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses WHERE id = ?", (scan_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Scan record not found."}), 404
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  🚀 Scanline ATS Backend Service Online")
    print("  🔗 http://127.0.0.1:5000")
    print("=" * 55 + "\n")
    app.run(host="127.0.0.1", port=5000)