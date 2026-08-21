# Scanline — Smart Resume & ATS Intelligence Suite

Scanline is an automated, single-file Applicant Tracking System (ATS) simulation platform and resume optimization engine[cite: 2]. It extracts, structures, audits, and benchmarks candidate resumes against enterprise recruitment algorithms and technical job descriptions using heuristic parsing[cite: 2].

---

## ⚡ Features

* **Single-File Architecture:** The entire full-stack application (Flask backend, API routes, SQLite storage, and responsive glassmorphism UI) runs out of a single `app.py` script.
* **Universal Document Ingestion:** Parses `.pdf`, `.docx`, and `.txt` files with automated text normalization and cleaning.
* **Strict Heuristic ATS Scoring (100-Point Model):**
  * **Contact Completeness (15 pts):** Email, phone, LinkedIn, and GitHub/portfolio URL validation.
  * **Section Hierarchy (20 pts):** Evaluates presence of Education, Skills, Projects, and Experience/Certifications.
  * **Content Density (15 pts):** Word count analysis calibrated to single-page/two-page ATS standards (350–850 words optimal).
  * **Action Verbs & Impact (15 pts):** Scans for strong impact verbs (e.g., *Architected*, *Engineered*, *Optimized*) and measurable metrics (`%`, `ms`, numbers).
  * **Role Alignment (25 pts):** Calculates alignment against target technical skills.
  * **Formatting Hygiene (10 pts):** Validates raw textual layer integrity.
* **Intelligent Auto-Role Detection:** If no target role is specified, the engine auto-determines the best-matching profile across 16+ technical roles (Frontend, Backend, AI/ML, DevOps, Cloud, etc.).
* **Invalid Document Filtering:** Rejects non-resume files (invoices, essays, code dumps) and alerts the user with an interactive modal.
* **Instant Export:** Generates downloadable A4 PDF reports (`html2pdf.js`) and machine-readable JSON exports[cite: 2, 3].
* **Session Security:** Automatic logout and session clearance upon closing the browser tab.

---

## 🛠️ Complete Terminal Setup & Run Commands

Execute the following commands in your terminal to set up, install, and run the project:

### 1. Project Initialization & Setup

```bash
# 1. Create project folder and navigate inside
mkdir scanline && cd scanline

# 2. (Optional) Create and activate a Python virtual environment
# Windows:
python -m venv venv
venv\Scripts\activate

# macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# 3. Install all required dependencies
pip install flask flask-cors pypdf python-docx
