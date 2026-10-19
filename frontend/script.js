// Dynamic Base URL detection
const API_BASE = window.location.port === "5500" || window.location.protocol === "file:" 
  ? "http://127.0.0.1:5000/api" 
  : "/api";

const hamburgerBtn = document.getElementById("hamburgerBtn");
const topNav = document.getElementById("topNav");
const appTopbar = document.getElementById("appTopbar");
const brandLogoTrigger = document.getElementById("brandLogoTrigger");
const navBtns = document.querySelectorAll(".nav-btn[data-view]");

const views = {
  scan: document.getElementById("view-scan"),
  history: document.getElementById("view-history"),
  admin: document.getElementById("view-admin"),
  about: document.getElementById("view-about"),
  login: document.getElementById("view-login"),
  signup: document.getElementById("view-signup"),
};

const themeToggleBtn = document.getElementById("themeToggleBtn");
const themeIcon = document.getElementById("themeIcon");

const authIndicator = document.getElementById("authIndicator");
const loginNavBtn = document.getElementById("loginNavBtn");
const signupNavBtn = document.getElementById("signupNavBtn");
const userProfileBadge = document.getElementById("userProfileBadge");
const navUserName = document.getElementById("navUserName");
const logoutBtn = document.getElementById("logoutBtn");

// Dedicated Navbar Elements
const navBtnScan = document.getElementById("navBtnScan");
const navBtnHistory = document.getElementById("navBtnHistory");
const adminNavBtn = document.getElementById("adminNavBtn");

const dropzone = document.getElementById("dropzone");
const paperBed = dropzone ? dropzone.querySelector(".paper-bed") : null;
const paperSheet = document.getElementById("paperSheet");
const fileInput = document.getElementById("fileInput");
const paperEmpty = document.getElementById("paperEmpty");
const paperFilled = document.getElementById("paperFilled");
const filenameText = document.getElementById("filenameText");
const clearFileBtn = document.getElementById("clearFile");
const scanSweep = document.getElementById("scanSweep");

const jobTitleInput = document.getElementById("jobTitle");
const jobDescriptionInput = document.getElementById("jobDescription");
const jdWordCount = document.getElementById("jdWordCount");

const scanForm = document.getElementById("scanForm");
const runBtn = document.getElementById("runBtn");
const formError = document.getElementById("formError");

const resultsSection = document.getElementById("results");
const gaugeFill = document.getElementById("gaugeFill");
const gaugeNumber = document.getElementById("gaugeNumber");
const gaugeCaption = document.getElementById("gaugeCaption");
const atsScoreEl = document.getElementById("atsScore");
const checkList = document.getElementById("checkList");
const statList = document.getElementById("statList");
const matchedSkillsEl = document.getElementById("matchedSkills");
const missingSkillsEl = document.getElementById("missingSkills");
const matchedCount = document.getElementById("matchedCount");
const missingCount = document.getElementById("missingCount");

const downloadReportBtn = document.getElementById("downloadReportBtn");
const downloadJsonBtn = document.getElementById("downloadJsonBtn");

const historyBody = document.getElementById("historyBody");

// Admin Elements
const adminTotalUsers = document.getElementById("adminTotalUsers");
const adminTotalScans = document.getElementById("adminTotalScans");
const adminAvgAts = document.getElementById("adminAvgAts");
const adminUsersBody = document.getElementById("adminUsersBody");
const adminScansBody = document.getElementById("adminScansBody");
const tabBtnUsers = document.getElementById("tabBtnUsers");
const tabBtnScans = document.getElementById("tabBtnScans");
const adminTabUsersContent = document.getElementById("adminTabUsersContent");
const adminTabScansContent = document.getElementById("adminTabScansContent");
const tabBtnLogins = document.getElementById("tabBtnLogins");
const adminTabLoginsContent = document.getElementById("adminTabLoginsContent");
const adminLoginsBody = document.getElementById("adminLoginsBody");

// Names/emails are typed by users, so always escape before putting them in innerHTML
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function formatDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return isNaN(d) ? "—" : d.toLocaleString();
}

// Admin Report Inspector Modal Elements
const adminReportModal = document.getElementById("adminReportModal");
const inspectCandidateName = document.getElementById("inspectCandidateName");
const inspectRoleDate = document.getElementById("inspectRoleDate");
const adminReportDetails = document.getElementById("adminReportDetails");
const closeAdminReportBtn = document.getElementById("closeAdminReportBtn");

// Secret Admin Modal Gateway
const adminGatewayModal = document.getElementById("adminGatewayModal");
const adminGatewayForm = document.getElementById("adminGatewayForm");
const gatewayEmail = document.getElementById("gatewayEmail");
const gatewayPassword = document.getElementById("gatewayPassword");
const gatewayError = document.getElementById("gatewayError");
const closeGatewayBtn = document.getElementById("closeGatewayBtn");
const footerAdminTrigger = document.getElementById("footerAdminTrigger");

const loginForm = document.getElementById("loginForm");
const loginEmailInput = document.getElementById("loginEmail");
const loginPasswordInput = document.getElementById("loginPassword");
const loginSubmitBtn = document.getElementById("loginSubmitBtn");
const loginError = document.getElementById("loginError");

const signupForm = document.getElementById("signupForm");
const signupNameInput = document.getElementById("signupName");
const signupEmailInput = document.getElementById("signupEmail");
const signupPasswordInput = document.getElementById("signupPassword");
const signupSubmitBtn = document.getElementById("signupSubmitBtn");
const signupError = document.getElementById("signupError");

const invalidResumeModal = document.getElementById("invalidResumeModal");
const invalidModalDesc = document.getElementById("invalidModalDesc");
const closeModalBtn = document.getElementById("closeModalBtn");

const GAUGE_CIRCUMFERENCE = 283;
let selectedFile = null;
let lastAnalysisResult = null;
let cachedAdminScans = [];

// Logo 3-Click Secret Gateway
let brandClickCount = 0;
let brandClickTimer = null;
if (brandLogoTrigger) {
  brandLogoTrigger.addEventListener("click", () => {
    brandClickCount++;
    clearTimeout(brandClickTimer);
    brandClickTimer = setTimeout(() => { brandClickCount = 0; }, 1200);

    if (brandClickCount >= 3) {
      brandClickCount = 0;
      if (isUserAdmin()) {
        switchView("admin");
      } else {
        openAdminGatewayModal();
      }
    }
  });
}

if (hamburgerBtn && topNav) {
  hamburgerBtn.addEventListener("click", () => {
    hamburgerBtn.classList.toggle("is-active");
    topNav.classList.toggle("is-open");
  });
}

function initTheme() {
  const saved = sessionStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  if (themeIcon) themeIcon.textContent = saved === "dark" ? "🌙" : "☀️";
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const target = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", target);
  sessionStorage.setItem("theme", target);
  if (themeIcon) themeIcon.textContent = target === "dark" ? "🌙" : "☀️";
}

if (themeToggleBtn) themeToggleBtn.addEventListener("click", toggleTheme);

function isUserLoggedIn() {
  return sessionStorage.getItem("isLoggedIn") === "true" && !!sessionStorage.getItem("authToken");
}

function isUserAdmin() {
  return sessionStorage.getItem("isAdmin") === "true";
}

function getAuthHeaders() {
  const token = sessionStorage.getItem("authToken");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function updateAuthStateUI() {
  const logged = isUserLoggedIn();
  const admin = isUserAdmin();
  const storedName = sessionStorage.getItem("userName") || "Operator";

  if (appTopbar) {
    appTopbar.classList.toggle("admin-topbar-mode", admin);
  }

  if (authIndicator) {
    authIndicator.classList.toggle("logged-in", logged);
    authIndicator.classList.toggle("logged-out", !logged);
    authIndicator.title = logged ? `Active: ${storedName}${admin ? ' (SuperAdmin)' : ''}` : "Offline / Guest";
  }

  // Differentiate Navbar between Admin and Candidate
  if (admin) {
    if (navBtnScan) navBtnScan.style.display = "none";
    if (navBtnHistory) navBtnHistory.style.display = "none";
    if (adminNavBtn) adminNavBtn.style.display = "inline-flex";
  } else {
    if (navBtnScan) navBtnScan.style.display = "inline-flex";
    if (navBtnHistory) navBtnHistory.style.display = "inline-flex";
    if (adminNavBtn) adminNavBtn.style.display = "none";
  }

  if (logged) {
    if (loginNavBtn) loginNavBtn.style.display = "none";
    if (signupNavBtn) signupNavBtn.style.display = "none";
    if (userProfileBadge) {
      userProfileBadge.style.display = "inline-flex";
      userProfileBadge.classList.toggle("admin-profile-badge", admin);
      navUserName.textContent = admin ? `${storedName} [Admin]` : storedName;
    }
    if (logoutBtn) logoutBtn.style.display = "inline-block";
  } else {
    if (loginNavBtn) loginNavBtn.style.display = "inline-block";
    if (signupNavBtn) signupNavBtn.style.display = "inline-block";
    if (userProfileBadge) userProfileBadge.style.display = "none";
    if (logoutBtn) logoutBtn.style.display = "none";
  }
}

navBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    switchView(btn.dataset.view);
    if (topNav && topNav.classList.contains("is-open")) {
      topNav.classList.remove("is-open");
      if (hamburgerBtn) hamburgerBtn.classList.remove("is-active");
    }
  });
});

function switchView(target) {
  navBtns.forEach((b) => b.classList.toggle("is-active", b.dataset.view === target));
  Object.entries(views).forEach(([key, el]) => {
    if (el) el.hidden = key !== target;
  });
  if (target === "history") loadHistory();
  if (target === "admin") {
    if (!isUserAdmin()) {
      openAdminGatewayModal();
      return;
    }
    loadAdminDashboard();
  }
}

// Sub-tabs in Admin View
if (tabBtnUsers && tabBtnScans) {
  const adminTabs = [
    [tabBtnUsers, adminTabUsersContent],
    [tabBtnScans, adminTabScansContent],
    [tabBtnLogins, adminTabLoginsContent],
  ];
  adminTabs.forEach(([btn]) => {
    if (!btn) return;
    btn.addEventListener("click", () => {
      adminTabs.forEach(([b, panel]) => {
        if (!b) return;
        b.classList.toggle("is-active", b === btn);
        if (panel) panel.hidden = b !== btn;
      });
    });
  });
}

// Shortcut: Ctrl + Shift + A (or Cmd + Shift + A)
window.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "a") {
    e.preventDefault();
    if (isUserAdmin()) {
      switchView("admin");
    } else {
      openAdminGatewayModal();
    }
  }
});

function openAdminGatewayModal() {
  if (adminGatewayModal) {
    adminGatewayModal.hidden = false;
    if (gatewayPassword) gatewayPassword.focus();
  }
}

if (footerAdminTrigger) {
  footerAdminTrigger.addEventListener("click", () => {
    if (isUserAdmin()) {
      switchView("admin");
    } else {
      openAdminGatewayModal();
    }
  });
}

if (closeGatewayBtn && adminGatewayModal) {
  closeGatewayBtn.addEventListener("click", () => {
    adminGatewayModal.hidden = true;
    if (gatewayError) gatewayError.hidden = true;
  });
}

if (adminGatewayForm) {
  adminGatewayForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (gatewayError) gatewayError.hidden = true;

    try {
      const res = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: gatewayEmail.value.trim(),
          password: gatewayPassword.value.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Admin authentication failed.");
      if (!data.is_admin) throw new Error("This account does not have Admin privileges.");

      sessionStorage.setItem("isLoggedIn", "true");
      sessionStorage.setItem("authToken", data.token);
      sessionStorage.setItem("userName", data.name);
      sessionStorage.setItem("userEmail", data.email);
      sessionStorage.setItem("isAdmin", "true");

      updateAuthStateUI();
      adminGatewayModal.hidden = true;
      adminGatewayForm.reset();
      switchView("admin");
    } catch (err) {
      if (gatewayError) {
        gatewayError.textContent = err.message;
        gatewayError.hidden = false;
      }
    }
  });
}

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    loginError.hidden = true;
    loginSubmitBtn.disabled = true;

    try {
      const res = await fetch(`${API_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: loginEmailInput.value.trim(),
          password: loginPasswordInput.value.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Login failed.");

      sessionStorage.setItem("isLoggedIn", "true");
      sessionStorage.setItem("authToken", data.token);
      sessionStorage.setItem("userName", data.name);
      sessionStorage.setItem("userEmail", data.email);
      sessionStorage.setItem("isAdmin", data.is_admin ? "true" : "false");

      updateAuthStateUI();
      loginForm.reset();
      switchView(data.is_admin ? "admin" : "scan");
    } catch (err) {
      loginError.textContent = err.message;
      loginError.hidden = false;
    } finally {
      loginSubmitBtn.disabled = false;
    }
  });
}

if (signupForm) {
  signupForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    signupError.hidden = true;
    signupSubmitBtn.disabled = true;

    try {
      const res = await fetch(`${API_BASE}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: signupNameInput.value.trim(),
          email: signupEmailInput.value.trim(),
          password: signupPasswordInput.value.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Signup failed.");

      sessionStorage.setItem("isLoggedIn", "true");
      sessionStorage.setItem("authToken", data.token);
      sessionStorage.setItem("userName", data.name);
      sessionStorage.setItem("userEmail", data.email);
      sessionStorage.setItem("isAdmin", "false");

      updateAuthStateUI();
      signupForm.reset();
      switchView("scan");
    } catch (err) {
      signupError.textContent = err.message;
      signupError.hidden = false;
    } finally {
      signupSubmitBtn.disabled = false;
    }
  });
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    sessionStorage.clear();
    updateAuthStateUI();
    switchView("login");
  });
}

function showInvalidResumePopup(message) {
  if (invalidModalDesc) {
    invalidModalDesc.textContent = message || "This file does not appear to be a resume. Please upload a valid resume only.";
  }
  if (invalidResumeModal) {
    invalidResumeModal.hidden = false;
  }
}

if (closeModalBtn) {
  closeModalBtn.addEventListener("click", () => {
    if (invalidResumeModal) invalidResumeModal.hidden = true;
    if (clearFileBtn) clearFileBtn.click();
  });
}

if (paperSheet) {
  paperSheet.addEventListener("click", () => {
    if (!isUserLoggedIn()) {
      showError("Please log in to upload files.");
      switchView("login");
      return;
    }
    fileInput.click();
  });
}

if (fileInput) {
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) setFile(fileInput.files[0]);
  });
}

if (paperBed) {
  ["dragenter", "dragover"].forEach((evt) => {
    paperBed.addEventListener(evt, (e) => {
      e.preventDefault();
      paperBed.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((evt) => {
    paperBed.addEventListener(evt, (e) => {
      e.preventDefault();
      paperBed.classList.remove("drag-over");
    });
  });
  paperBed.addEventListener("drop", (e) => {
    e.preventDefault();
    if (!isUserLoggedIn()) {
      showError("Please log in to upload files.");
      switchView("login");
      return;
    }
    if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  });
}

if (clearFileBtn) {
  clearFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    if (fileInput) fileInput.value = "";
    if (paperEmpty) paperEmpty.hidden = false;
    if (paperFilled) paperFilled.hidden = true;
  });
}

function setFile(file) {
  if (!/\.(pdf|docx|txt)$/i.test(file.name)) {
    showError("Unsupported file type. Please upload PDF, DOCX, or TXT.");
    return;
  }
  if (file.size > 8 * 1024 * 1024) {
    showError("File size exceeds 8MB limit.");
    return;
  }
  clearError();
  selectedFile = file;
  if (filenameText) filenameText.textContent = file.name;
  if (paperEmpty) paperEmpty.hidden = true;
  if (paperFilled) paperFilled.hidden = false;
}

if (jobDescriptionInput && jdWordCount) {
  jobDescriptionInput.addEventListener("input", () => {
    const words = jobDescriptionInput.value.trim().split(/\s+/).filter(Boolean);
    jdWordCount.textContent = jobDescriptionInput.value.trim() ? words.length : 0;
  });
}

if (scanForm) {
  scanForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();

    if (!isUserLoggedIn()) {
      showError("Please log in to run an ATS scan.");
      switchView("login");
      return;
    }

    if (!selectedFile) {
      showError("Please upload a resume file.");
      return;
    }

    const formData = new FormData();
    formData.append("resume", selectedFile);
    formData.append("job_title", jobTitleInput ? jobTitleInput.value.trim() : "");
    formData.append("job_description", jobDescriptionInput ? jobDescriptionInput.value.trim() : "");

    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 401) {
          sessionStorage.clear();
          updateAuthStateUI();
          showError("Session expired. Please log in again.");
          switchView("login");
          return;
        }
        if (res.status === 422 || data.is_invalid_resume) {
          showInvalidResumePopup(data.error);
          return;
        }
        throw new Error(data.error || "Analysis failed.");
      }

      lastAnalysisResult = {
        ...data,
        filename: selectedFile.name,
        target_role: data.effective_role || "General Role",
        scan_date: new Date().toISOString()
      };
      renderResults(data);
    } catch (err) {
      showError(err.message === "Failed to fetch" ? "Cannot connect to backend server. Ensure Flask is active." : err.message);
    } finally {
      setLoading(false);
    }
  });
}

function setLoading(isLoading) {
  if (!runBtn) return;
  runBtn.disabled = isLoading;
  const label = runBtn.querySelector(".run-btn-label");
  if (label) label.textContent = isLoading ? "Scanning..." : "Run Analysis";
  if (scanSweep) scanSweep.hidden = !isLoading;
}

function showError(msg) {
  if (!formError) return;
  formError.textContent = msg;
  formError.hidden = false;
}

function clearError() {
  if (!formError) return;
  formError.hidden = true;
  formError.textContent = "";
}

function renderResults(data) {
  if (!resultsSection) return;
  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });

  const matchScore = data.match_score;
  const atsScore = data.ats_score;

  animateGauge(matchScore);
  if (gaugeCaption) {
    const srcLabel = { job_description: "your job description", role_profile: "the role profile", closest_profile: "the closest known role profile", auto_detected: "the auto-detected role" }[data.match.source] || "the target role";
    gaugeCaption.textContent = `${data.match.matched_skills.length} of ${data.match.job_skills_total} target skills found, based on ${srcLabel} (${data.effective_role}).`;
  }

  if (atsScoreEl) {
    animateNumber(atsScoreEl, atsScore);
    atsScoreEl.style.color = colorForScore(atsScore);
  }

  if (checkList && data.ats && data.ats.checks) {
    checkList.innerHTML = "";
    data.ats.checks.forEach((check) => {
      const li = document.createElement("li");
      li.className = `check-item ${check.passed ? "pass" : "fail"}`;
      li.innerHTML = `<span class="check-icon">${check.passed ? "✓" : "✕"}</span><span>${check.label}<br><span style="opacity:.75">${check.detail}</span></span>`;
      checkList.appendChild(li);
    });
  }

  const suggestionsList = document.getElementById("suggestionsList");
  if (suggestionsList) {
    suggestionsList.innerHTML = "";
    if (data.suggestions && data.suggestions.length) {
      data.suggestions.forEach((sugg) => {
        const li = document.createElement("li");
        li.textContent = sugg;
        suggestionsList.appendChild(li);
      });
    } else {
      suggestionsList.innerHTML = "<li>All ATS standards and core skills have been validated successfully.</li>";
    }
  }

  if (statList && data.ats && data.contact) {
    statList.innerHTML = "";
    const stats = [
      ["Target Role", data.effective_role || "General"],
      ["Total Words", data.ats.word_count],
      ["Email Detected", data.contact.email || "Missing"],
      ["Phone Detected", data.contact.phone || "Missing"],
      ["LinkedIn Link", data.contact.linkedin ? "Verified" : "Missing"],
      ["Portfolio / Web", data.contact.portfolio ? "Detected" : "None"],
      ["Standard Sections", data.sections_found?.length ? data.sections_found.join(", ") : "Incomplete"],
    ];
    stats.forEach(([label, value]) => {
      const div = document.createElement("div");
      div.innerHTML = `<dt>${label}</dt><dd title="${value}">${value}</dd>`;
      statList.appendChild(div);
    });
  }

  if (data.match) {
    renderChips(matchedSkillsEl, data.match.matched_skills, "matched", "No matching skills identified.");
    renderChips(missingSkillsEl, data.match.missing_skills, "missing", "No target skills missing.");
    if (matchedCount) matchedCount.textContent = data.match.matched_skills.length;
    if (missingCount) missingCount.textContent = data.match.missing_skills.length;
  }
}

function renderChips(container, items, kind, emptyMsg) {
  if (!container) return;
  container.innerHTML = "";
  if (!items || !items.length) {
    container.innerHTML = `<p class="empty-note">${emptyMsg}</p>`;
    return;
  }
  items.forEach((skill) => {
    const chip = document.createElement("span");
    chip.className = `chip ${kind}`;
    chip.textContent = skill;
    container.appendChild(chip);
  });
}

function animateGauge(score) {
  if (!gaugeFill) return;
  const offset = GAUGE_CIRCUMFERENCE - (GAUGE_CIRCUMFERENCE * Math.min(score, 100)) / 100;
  gaugeFill.style.stroke = colorForScore(score);
  gaugeFill.style.strokeDashoffset = offset;
  if (gaugeNumber) animateNumber(gaugeNumber, score);
}

function animateNumber(el, target) {
  const duration = 600;
  const start = performance.now();
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(progress * target);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function colorForScore(score) {
  if (score >= 75) return "var(--green)";
  if (score >= 50) return "var(--amber)";
  return "var(--red)";
}

async function loadHistory() {
  if (!historyBody) return;

  if (!isUserLoggedIn()) {
    historyBody.innerHTML = `
      <tr>
        <td colspan="6" class="empty-note" style="padding: 30px; text-align: center;">
          <span>🔒 Please <strong>log in</strong> to view your scan history.</span>
        </td>
      </tr>`;
    return;
  }

  historyBody.innerHTML = `<tr><td colspan="6" class="empty-note">Loading scan logs...</td></tr>`;
  
  try {
    const res = await fetch(`${API_BASE}/history`, { headers: getAuthHeaders() });
    const data = await res.json();
    
    if (!res.ok) {
      if (res.status === 401) {
        sessionStorage.clear();
        updateAuthStateUI();
        historyBody.innerHTML = `<tr><td colspan="6" class="empty-note">Session expired. Please log in again.</td></tr>`;
        return;
      }
      throw new Error(data.error || "Failed to load history.");
    }

    if (!data.history || !data.history.length) {
      historyBody.innerHTML = `<tr><td colspan="6" class="empty-note">No scans logged for your account yet.</td></tr>`;
      return;
    }

    historyBody.innerHTML = "";
    data.history.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.filename}</td>
        <td>${row.job_title || "—"}</td>
        <td>${row.match_score ?? "—"}%</td>
        <td><strong style="color: ${colorForScore(row.ats_score)}">${row.ats_score ?? "—"}/100</strong></td>
        <td>${row.word_count ?? "—"}</td>
        <td>${new Date(row.created_at).toLocaleDateString()}</td>
      `;
      historyBody.appendChild(tr);
    });
  } catch (err) {
    historyBody.innerHTML = `<tr><td colspan="6" class="empty-note">Unable to connect to backend server.</td></tr>`;
  }
}

// Full Admin Report Inspection Modal
function openAdminReportInspector(scanIndex) {
  const scan = cachedAdminScans[scanIndex];
  if (!scan || !scan.report) {
    alert("Report data is unavailable for this entry.");
    return;
  }

  const r = scan.report;
  inspectCandidateName.textContent = `${scan.user_name} — Candidate ATS Audit`;
  inspectRoleDate.textContent = `Target Role: ${scan.job_title} | Audited on: ${new Date(scan.created_at).toLocaleString()}`;

  let checksHtml = "";
  if (r.ats && r.ats.checks) {
    r.ats.checks.forEach((chk) => {
      checksHtml += `
        <li class="check-item ${chk.passed ? "pass" : "fail"}">
          <span class="check-icon">${chk.passed ? "✓" : "✕"}</span>
          <span>${chk.label} — <span style="opacity:.8">${chk.detail}</span></span>
        </li>
      `;
    });
  }

  let suggestionsHtml = "";
  if (r.suggestions && r.suggestions.length) {
    r.suggestions.forEach((sugg) => {
      suggestionsHtml += `<li>${sugg}</li>`;
    });
  } else {
    suggestionsHtml = "<li>No critical flags surfaced during candidate parsing.</li>";
  }

  let matchedChips = r.match?.matched_skills?.map(s => `<span class="chip matched">${s}</span>`).join("") || "None";
  let missingChips = r.match?.missing_skills?.map(s => `<span class="chip missing">${s}</span>`).join("") || "None";

  adminReportDetails.innerHTML = `
    <div class="admin-inspector-grid">
      <div class="panel admin-stat-card">
        <div class="panel-label">ATS READABILITY SCORE</div>
        <div class="stat-big" style="color: ${colorForScore(r.ats_score)}">${r.ats_score} / 100</div>
      </div>
      <div class="panel admin-stat-card">
        <div class="panel-label">ROLE BENCHMARK MATCH</div>
        <div class="stat-big" style="color: ${colorForScore(r.match_score)}">${r.match_score}%</div>
      </div>
    </div>

    <div class="panel" style="margin-top: 14px;">
      <div class="panel-label">HEURISTIC AUDIT BREAKDOWN</div>
      <ul class="check-list">${checksHtml}</ul>
    </div>

    <div class="panel suggestions-panel" style="margin-top: 14px;">
      <div class="panel-label" style="color: var(--amber);">⚡ IMPROVEMENT RECOMMENDATIONS</div>
      <ul class="suggestions-list">${suggestionsHtml}</ul>
    </div>

    <div class="results-grid results-grid-skills" style="margin-top: 14px;">
      <div class="panel skills-panel">
        <div class="panel-label">MATCHED COMPETENCIES (${r.match?.matched_skills?.length || 0})</div>
        <div class="chip-row">${matchedChips}</div>
      </div>
      <div class="panel skills-panel">
        <div class="panel-label">MISSING ROLE COMPETENCIES (${r.match?.missing_skills?.length || 0})</div>
        <div class="chip-row">${missingChips}</div>
      </div>
    </div>
  `;

  adminReportModal.hidden = false;
}

if (closeAdminReportBtn && adminReportModal) {
  closeAdminReportBtn.addEventListener("click", () => {
    adminReportModal.hidden = true;
  });
}

async function loadAdminDashboard() {
  if (!isUserAdmin()) {
    openAdminGatewayModal();
    return;
  }

  try {
    const statsRes = await fetch(`${API_BASE}/admin/stats`, { headers: getAuthHeaders() });
    if (statsRes.ok) {
      const stats = await statsRes.json();
      if (adminTotalUsers) adminTotalUsers.textContent = stats.total_users;
      if (adminTotalScans) adminTotalScans.textContent = stats.total_scans;
      if (adminAvgAts) adminAvgAts.textContent = `${stats.average_ats} / 100`;
    }

    // Load Candidate Statistics
    const usersRes = await fetch(`${API_BASE}/admin/users`, { headers: getAuthHeaders() });
    const usersData = await usersRes.json();

    if (adminUsersBody) {
      if (usersRes.ok && usersData.users && usersData.users.length) {
        adminUsersBody.innerHTML = "";
        usersData.users.forEach((u) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>#${u.id}</td>
            <td><strong>${escapeHtml(u.name)}</strong></td>
            <td>${escapeHtml(u.email)}</td>
            <td>${u.is_admin ? "🛡️ Admin" : "Candidate"}</td>
            <td>${formatDateTime(u.created_at)}</td>
            <td>${u.last_login ? formatDateTime(u.last_login) : "Never"}</td>
            <td><strong>${u.login_count ?? 0}</strong></td>
            <td><strong>${u.scan_count}</strong></td>
          `;
          adminUsersBody.appendChild(tr);
        });
      } else {
        adminUsersBody.innerHTML = `<tr><td colspan="8" class="empty-note">No candidate records found.</td></tr>`;
      }
    }

    // Load Login Activity
    if (adminLoginsBody) {
      const loginsRes = await fetch(`${API_BASE}/admin/logins`, { headers: getAuthHeaders() });
      const loginsData = await loginsRes.json();
      if (loginsRes.ok && loginsData.logins && loginsData.logins.length) {
        adminLoginsBody.innerHTML = "";
        loginsData.logins.forEach((l) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><strong>${escapeHtml(l.name)}</strong></td>
            <td>${escapeHtml(l.email)}</td>
            <td>${l.event === "signup" ? "🆕 Sign-up" : "🔑 Login"}</td>
            <td>${formatDateTime(l.logged_in_at)}</td>
            <td>${escapeHtml(l.ip_address)}</td>
          `;
          adminLoginsBody.appendChild(tr);
        });
      } else {
        adminLoginsBody.innerHTML = `<tr><td colspan="5" class="empty-note">No login activity recorded yet.</td></tr>`;
      }
    }

    // Load Scan Records
    const scansRes = await fetch(`${API_BASE}/admin/scans`, { headers: getAuthHeaders() });
    const scansData = await scansRes.json();

    if (adminScansBody) {
      if (scansRes.ok && scansData.scans && scansData.scans.length) {
        cachedAdminScans = scansData.scans;
        adminScansBody.innerHTML = "";
        scansData.scans.forEach((scan, idx) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td><strong>${escapeHtml(scan.user_name)}</strong><br><span style="opacity:.7;font-size:12px">${escapeHtml(scan.user_email)}</span></td>
            <td>${escapeHtml(scan.job_title)}</td>
            <td><strong style="color: ${colorForScore(scan.ats_score)}">${scan.ats_score}/100</strong></td>
            <td>${new Date(scan.created_at).toLocaleString()}</td>
            <td><button class="inspect-btn" data-index="${idx}">🔍 View Report</button></td>
            <td><button class="history-delete admin-delete-btn" data-id="${scan.id}" title="Purge Record">✕ Purge</button></td>
          `;
          adminScansBody.appendChild(tr);
        });

        adminScansBody.querySelectorAll(".inspect-btn").forEach((btn) => {
          btn.addEventListener("click", () => {
            openAdminReportInspector(parseInt(btn.dataset.index, 10));
          });
        });

        adminScansBody.querySelectorAll(".admin-delete-btn").forEach((btn) => {
          btn.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to permanently delete this scan record?")) return;
            btn.disabled = true;
            try {
              const res = await fetch(`${API_BASE}/admin/scan/${btn.dataset.id}`, {
                method: "DELETE",
                headers: getAuthHeaders()
              });
              if (res.ok) {
                loadAdminDashboard();
              } else {
                const err = await res.json();
                alert(err.error || "Failed to delete.");
                btn.disabled = false;
              }
            } catch {
              alert("Network error.");
              btn.disabled = false;
            }
          });
        });
      } else {
        adminScansBody.innerHTML = `<tr><td colspan="6" class="empty-note">No scan logs in database.</td></tr>`;
      }
    }

  } catch (err) {
    if (adminScansBody) adminScansBody.innerHTML = `<tr><td colspan="6" class="empty-note">Error retrieving administrative data.</td></tr>`;
  }
}

if (downloadReportBtn) {
  downloadReportBtn.addEventListener("click", () => {
    if (!lastAnalysisResult) {
      alert("No report data to download. Please run a scan first.");
      return;
    }
    const reportElement = document.getElementById("results");
    const opt = {
      margin: 10,
      filename: `ATS_Report_${lastAnalysisResult.filename.replace(/\.[^/.]+$/, "")}_${Date.now()}.pdf`,
      image: { type: "jpeg", quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
    };
    html2pdf().set(opt).from(reportElement).save();
  });
}

if (downloadJsonBtn) {
  downloadJsonBtn.addEventListener("click", () => {
    if (!lastAnalysisResult) {
      alert("No report data available to export.");
      return;
    }
    const jsonString = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(lastAnalysisResult, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", jsonString);
    downloadAnchor.setAttribute("download", `ATS_Audit_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  });
}

initTheme();
updateAuthStateUI();  