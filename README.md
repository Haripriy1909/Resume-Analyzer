# ◎ Scanline – Smart Resume & ATS Analyzer

A web app that reads a resume (PDF, DOCX or TXT), checks how well it will perform in an
Applicant Tracking System (ATS), and shows how closely it matches a target job role or a pasted
job description. It gives an explainable score, a list of missing skills, and concrete suggestions
to improve the resume.

Built with a **Flask (Python)** backend and a **plain HTML / CSS / JavaScript** frontend.
Includes user accounts, scan history, an admin console with login tracking, and a fully
mobile-responsive interface.

---

## Table of contents

1. [Features](#features)
2. [Tech stack](#tech-stack)
3. [Project structure](#project-structure)
4. [How the scoring works](#how-the-scoring-works)
5. [Run locally](#run-locally)
6. [Deploy on Vercel](#deploy-on-vercel)
7. [Environment variables](#environment-variables)
8. [API reference](#api-reference)
9. [Database](#database)
10. [Admin console](#admin-console)
11. [Running the tests](#running-the-tests)
12. [Limitations](#limitations)
13. [Security notes](#security-notes)
14. [Roadmap](#roadmap)

---

## Features

**Resume analysis**
- Upload a resume as `.pdf`, `.docx` or `.txt`.
- **ATS score (0-100)** built from six transparent parts, each shown with its own points and reason.
- **Role match score (0-100)** against a chosen role, an auto-detected role, or a **pasted job description**.
- Matched and missing skills, with "any one of" logic (a Java developer is not penalised for not knowing Python).
- Detects skills that are only listed in a Skills section but never shown in a project or job.
- Actionable improvement suggestions.
- Download the report as **PDF** or **JSON**.
- Rejects files that are clearly not resumes.

**Accounts and history**
- Sign up / log in with JWT authentication (7-day tokens).
- Personal scan history.

**Admin console**
- Totals: registered users, total scans, average ATS score.
- **Candidate Statistics:** name, email, role, registered date, last login, login count, scan count.
- **Global ATS Logs:** every scan with candidate name and email, full report inspector, delete option.
- **Login Activity:** who logged in or signed up, when, and from which IP address.

**Interface**
- Dark / light theme toggle.
- Mobile-first responsive layout (tested at 320, 375, 414 and 768 px wide screens).
- Drag-and-drop file upload.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3, Flask-CORS |
| Resume parsing | pypdf (PDF), python-docx (DOCX) |
| Auth | PyJWT, Werkzeug password hashing |
| Database | SQLite |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Hosting | Vercel (Python serverless function + static frontend) |

---

## Project structure

```
resume-analyzer/
├── api/
│   └── index.py            # Vercel entry point (exposes the Flask app)
├── backend/
│   └── app.py              # Flask app: routes, database, scoring engine
├── frontend/
│   ├── index.html          # Single-page UI
│   ├── style.css           # Styles, including the mobile responsive layer
│   └── script.js           # UI logic and API calls
├── tests/
│   ├── sample_resumes.py   # Sample resumes used by the tests
│   ├── test_scoring.py     # Scoring engine tests
│   └── test_login_tracking.py  # Login tracking tests
├── requirements.txt        # Python dependencies
├── vercel.json             # Vercel configuration
├── .gitignore
├── .vercelignore
└── README.md
```

---

## How the scoring works

The scoring is deterministic: the same resume always gets the same score, and every point can be explained.

### ATS score (out of 100)

| Part | Points | What is checked |
|---|---|---|
| Contact completeness | 15 | Email (4), phone (4), LinkedIn (4), GitHub or portfolio (3) |
| Section hierarchy | 20 | Skills, Education, Experience, Projects, plus Summary or Certifications. A heading only counts if real content sits below it |
| Content density | 15 | 350-850 words is ideal; very short or very long resumes lose points |
| Impact and action verbs | 15 | Up to 8 points for strong action verbs, up to 7 for quantified results (for example "reduced load time by 40%") |
| Role skills match | 25 | Weighted match against the target role or job description |
| ATS text parseability | 10 | Text reads cleanly, has line structure, and contains dates |

### Role / job description match

- **Core skills carry more weight** than nice-to-have skills (for example HTML, CSS and JavaScript count more than GSAP for a frontend role).
- **"Any one of" groups:** knowing React, Vue *or* Angular is enough. Alternatives are not reported as missing once the group is satisfied.
- **Job description mode:** skills are extracted from the pasted text. Lines containing words such as *required* or *must* weigh more; *nice to have* or *plus* weigh less.
- **Evidence check:** a skill that appears only in the Skills list gets 80% credit; a skill that is also shown in a project or job gets 100%. This stops keyword stuffing from inflating the score.
- **Skill aliases:** `Node.js`, `NodeJS`, `React.js`, `HTML5`, `RESTful APIs`, `Postgres`, `sklearn`, `C#`, `.NET` and many other spellings are recognised.
- **Unknown roles:** if the typed role is not in the library, the closest known profile is used and the report says so.

### Supported role profiles

Frontend Developer, Backend Developer, Full Stack Developer, Web Developer, Python Developer,
AI/ML Engineer, Generative AI Engineer, Data Scientist, Data Engineer, DevOps Engineer,
Cloud Architect / Engineer, Cybersecurity Analyst, Mobile App Developer,
QA / Automation Test Engineer, Blockchain / Web3 Developer, UI/UX Designer.

---

## Run locally

**Requirements:** Python 3.10 or newer.

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/resume-analyzer.git
cd resume-analyzer

# 2. (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the backend
cd backend
python app.py                    # API runs on http://127.0.0.1:5000
```

Then open `frontend/index.html`:

- With **VS Code Live Server** (port 5500), or
- Any static server, for example `python -m http.server 5500` run inside the `frontend/` folder.

The frontend detects port 5500 or a `file://` address and talks to `http://127.0.0.1:5000/api`.
On any other host it uses the relative `/api` path (this is what Vercel uses).

A default admin account is created on first start:

| Email | Password |
|---|---|
| `admin@scanline.com` | `admin123456` (change this with `ADMIN_PASSWORD`) |

---

## Deploy on Vercel

1. Push this repository to GitHub. `vercel.json` must be in the **root** of the repository.
2. Go to [vercel.com](https://vercel.com), choose **Add New → Project**, and import the repository.
3. Keep the default settings (Framework: **Other**).
4. Before deploying, open **Environment Variables** and add:
   - `JWT_SECRET_KEY`
   - `ADMIN_PASSWORD`
5. Click **Deploy**.

Every later `git push` to the main branch is deployed automatically.

How it works on Vercel: `frontend/` is served as static files, and every `/api/*` request is
rewritten to `api/index.py`, which runs the Flask app as a serverless function.

> **Important:** on Vercel the SQLite database is stored in `/tmp`, which is temporary. Accounts,
> history and login logs can disappear after a cold start or a new deployment. For permanent data,
> move to an external database (for example Postgres on Supabase or Neon, or Turso).

---

## Environment variables

| Name | Required | Default | Purpose |
|---|---|---|---|
| `JWT_SECRET_KEY` | **Yes** (in production) | A built-in development key | Secret used to sign login tokens. Use a long random string |
| `ADMIN_PASSWORD` | **Yes** (in production) | `admin123456` | Password of `admin@scanline.com`. Only applied when the admin account is first created |
| `VERCEL` | No | Set by Vercel | When present, the database is stored at `/tmp/scanline.db` |

---

## API reference

All endpoints are under `/api`. Protected endpoints need the header
`Authorization: Bearer <token>`.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/signup` | – | Create an account. Body: `name`, `email`, `password` |
| POST | `/api/login` | – | Log in. Returns a token, name, email and `is_admin` |
| POST | `/api/analyze` | User | Analyze a resume. Form-data: `resume` (file), `job_title` (optional), `job_description` (optional) |
| GET | `/api/history` | User | The signed-in user's previous scans |
| GET | `/api/admin/stats` | Admin | Total users, total scans, average ATS score |
| GET | `/api/admin/users` | Admin | All users with email, role, dates, login count and scan count |
| GET | `/api/admin/scans` | Admin | All scans with candidate name, email and full report |
| GET | `/api/admin/logins` | Admin | Login and signup activity, newest first (last 500) |
| DELETE | `/api/admin/scan/<id>` | Admin | Delete a scan record |

**Example response of `/api/analyze` (shortened):**

```json
{
  "ats_score": 82,
  "match_score": 84,
  "effective_role": "Frontend Developer",
  "ats": {
    "score": 82,
    "word_count": 420,
    "checks": [
      { "label": "Contact Completeness (15/15)", "passed": true, "detail": "Email: ✓ | Phone: ✓ | LinkedIn: ✓ | GitHub/Portfolio: ✓" }
    ]
  },
  "match": {
    "match_score": 84,
    "matched_skills": ["html", "css", "javascript", "react"],
    "missing_skills": ["graphql"],
    "job_skills_total": 21,
    "source": "role_profile"
  },
  "suggestions": ["Add measurable results ..."]
}
```

`match.source` tells you what the match was based on: `job_description`, `role_profile`,
`closest_profile` or `auto_detected`.

---

## Database

SQLite, created automatically on first start. Older databases are upgraded automatically
(new columns are added without deleting data).

| Table | Purpose |
|---|---|
| `users` | id, name, email, password hash, is_admin, created_at, last_login, login_count |
| `analyses` | Saved scan results (user, filename, role, scores, word count, report, timestamp) |
| `login_logs` | One row per successful login or signup: user, name, email, event, IP address, browser, time |

Failed login attempts are not stored.

---

## Admin console

1. Log in with the admin account, or click the **logo three times** to open the hidden admin gateway.
2. Open **🛡️ Admin Console** in the menu.
3. Use the three tabs:
   - **👥 Candidate Statistics**
   - **📄 Global ATS Logs & Reports** (view a full report or purge a record)
   - **🔐 Login Activity**

---

## Running the tests

```bash
python tests/test_scoring.py
python tests/test_login_tracking.py
```

The scoring tests cover role detection, contact and phone parsing, metrics, skill aliases,
job description weighting, DOCX headers and tables, and the Flask API. The login test checks
that logins are recorded and that only admins can read them. Tests use a temporary database.

---

## Limitations

- Scoring reads **text only**. It cannot judge columns, images, icons or visual design.
- Scanned (image-only) PDFs have no text and cannot be analyzed.
- The role library covers 16 technical roles. Non-technical resumes get a general score only.
- On Vercel, requests are limited to about 4.5 MB, so very large resumes will fail.
- SQLite on Vercel is temporary (see [Deploy on Vercel](#deploy-on-vercel)).

---

## Security notes

Before making the site public:

- Set a strong `JWT_SECRET_KEY` and `ADMIN_PASSWORD`.
- Never commit `.db` files or `.env` files (they are already listed in `.gitignore`).
- User-provided names and emails are HTML-escaped before display to prevent script injection.
- Consider restricting CORS origins in `backend/app.py` to your own domain (it currently allows all origins).
- Consider hiding the three-click admin gateway on a public deployment.

---

## Roadmap

- Permanent database (Postgres) for Vercel deployments.
- OCR support for scanned PDFs.
- More role profiles, including non-technical roles.
- Rate limiting on login and analyze endpoints.

---

## License

Add a license of your choice (for example MIT) before publishing.
