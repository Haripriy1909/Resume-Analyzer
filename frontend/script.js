const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" || window.location.hostname.startsWith("192.168."))
  ? `http://${window.location.hostname}:5000/api`
  : "/api";

const hamburgerBtn = document.getElementById("hamburgerBtn");
const topNav = document.getElementById("topNav");
const navBtns = document.querySelectorAll(".nav-btn[data-view]");

const views = {
  scan: document.getElementById("view-scan"),
  history: document.getElementById("view-history"),
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

if (hamburgerBtn && topNav) {
  hamburgerBtn.addEventListener("click", () => {
    hamburgerBtn.classList.toggle("is-active");
    topNav.classList.toggle("is-open");
  });
}

function initTheme() {
  const saved = sessionStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  sessionStorage.setItem("theme", saved);
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

function getAuthHeaders() {
  const token = sessionStorage.getItem("authToken");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function updateAuthStateUI() {
  const logged = isUserLoggedIn();
  const storedName = sessionStorage.getItem("userName") || "Operator";

  if (authIndicator) {
    authIndicator.classList.toggle("logged-in", logged);
    authIndicator.classList.toggle("logged-out", !logged);
    authIndicator.title = logged ? `Active User: ${storedName}` : "Offline / Guest";
  }

  if (logged) {
    if (loginNavBtn) loginNavBtn.style.display = "none";
    if (signupNavBtn) signupNavBtn.style.display = "none";
    if (userProfileBadge) {
      userProfileBadge.style.display = "inline-flex";
      navUserName.textContent = storedName;
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

      let data;
      try {
        data = await res.json();
      } catch (jsonErr) {
        throw new Error("Server returned an invalid response.");
      }

      if (!res.ok) throw new Error(data.error || "Login failed.");

      sessionStorage.setItem("isLoggedIn", "true");
      sessionStorage.setItem("authToken", data.token);
      sessionStorage.setItem("userName", data.name);
      sessionStorage.setItem("userEmail", data.email);

      updateAuthStateUI();
      loginForm.reset();
      switchView("scan");
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

      let data;
      try {
        data = await res.json();
      } catch (jsonErr) {
        throw new Error("Server returned an invalid response.");
      }

      if (!res.ok) throw new Error(data.error || "Signup failed.");

      sessionStorage.setItem("isLoggedIn", "true");
      sessionStorage.setItem("authToken", data.token);
      sessionStorage.setItem("userName", data.name);
      sessionStorage.setItem("userEmail", data.email);

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
    sessionStorage.removeItem("isLoggedIn");
    sessionStorage.removeItem("authToken");
    sessionStorage.removeItem("userName");
    sessionStorage.removeItem("userEmail");
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

      let data;
      try {
        data = await res.json();
      } catch (jsonErr) {
        throw new Error("Invalid response received from server.");
      }

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
    gaugeCaption.textContent = `${data.match.matched_skills.length} of ${data.match.job_skills_total} target skills validated for ${data.effective_role}.`;
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
        <td colspan="7" class="empty-note" style="padding: 30px; text-align: center;">
          <span>🔒 Please <strong>log in</strong> to view and manage your private scan history.</span>
        </td>
      </tr>`;
    return;
  }

  historyBody.innerHTML = `<tr><td colspan="7" class="empty-note">Loading your scan logs...</td></tr>`;
  
  try {
    const res = await fetch(`${API_BASE}/history`, {
      headers: getAuthHeaders()
    });
    
    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error("Could not parse history response.");
    }
    
    if (!res.ok) {
      if (res.status === 401) {
        sessionStorage.clear();
        updateAuthStateUI();
        historyBody.innerHTML = `<tr><td colspan="7" class="empty-note">Session expired. Please log in again.</td></tr>`;
        return;
      }
      throw new Error(data.error || "Failed to load history.");
    }

    if (!data.history || !data.history.length) {
      historyBody.innerHTML = `<tr><td colspan="7" class="empty-note">No scans logged for your account yet.</td></tr>`;
      return;
    }

    historyBody.innerHTML = "";
    data.history.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.filename}</td>
        <td>${row.job_title || "—"}</td>
        <td>${row.match_score ?? "—"}%</td>
        <td>${row.ats_score ?? "—"}/100</td>
        <td>${row.word_count ?? "—"}</td>
        <td>${new Date(row.created_at).toLocaleDateString()}</td>
        <td><button class="history-delete" data-id="${row.id}" title="Delete Record">✕</button></td>
      `;
      historyBody.appendChild(tr);
    });

    historyBody.querySelectorAll(".history-delete").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to delete this scan entry?")) return;
        btn.disabled = true;
        try {
          const delRes = await fetch(`${API_BASE}/analysis/${btn.dataset.id}`, {
            method: "DELETE",
            headers: getAuthHeaders()
          });
          if (delRes.ok) {
            loadHistory();
          } else {
            const errData = await delRes.json();
            alert(errData.error || "Could not delete record.");
            btn.disabled = false;
          }
        } catch {
          alert("Network error deleting record.");
          btn.disabled = false;
        }
      });
    });
  } catch (err) {
    historyBody.innerHTML = `<tr><td colspan="7" class="empty-note">Unable to connect to backend server.</td></tr>`;
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
