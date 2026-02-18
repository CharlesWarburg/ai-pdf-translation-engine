const form = document.getElementById("translate-form");
const fileInput = document.getElementById("file");
const fileInputWrap = fileInput.closest(".file-input");
const fileSelection = document.getElementById("file-selection");
const fileSelectionName = document.getElementById("file-selection-name");
const fileClear = document.getElementById("file-clear");
const targetSelect = document.getElementById("target_language");
const submitBtn = document.getElementById("submit-btn");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error");
const progressWrap = document.getElementById("progress-wrap");
const progressBar = document.getElementById("progress-bar");

let isSubmitting = false;
let progressRampId = null;
let progressCreepId = null;
let statusTimers = [];

function canSubmit() {
  const hasFile = fileInput?.files && fileInput.files.length > 0;
  const hasLang = !!targetSelect?.value;
  const isLocked = form.classList.contains("is-loading") || isSubmitting;
  const isErrored = form.classList.contains("is-error");
  return hasFile && hasLang && !isLocked && !isErrored;
}

function updateFileSelectionUI() {
  const file = fileInput.files[0];
  if (file) {
    fileSelectionName.textContent = file.name;
    fileSelection.classList.add("is-visible");
    fileClear.tabIndex = 0;
  } else {
    fileSelectionName.textContent = "";
    fileSelection.classList.remove("is-visible");
    fileClear.tabIndex = -1;
  }
}

function setProgress(pct) {
  if (progressBar) progressBar.style.width = pct + "%";
}

function stopFakeProgress() {
  if (progressRampId !== null) {
    window.clearInterval(progressRampId);
    progressRampId = null;
  }
  if (progressCreepId !== null) {
    window.clearInterval(progressCreepId);
    progressCreepId = null;
  }
}

function clearStatusTimers() {
  statusTimers.forEach((id) => {
    window.clearTimeout(id);
    window.clearInterval(id);
  });
  statusTimers = [];
}

function setIdleState() {
  statusEl.textContent = "";
  statusEl.innerHTML = "";
  errorEl.textContent = "";
  progressWrap.classList.remove("is-visible", "is-complete");
  form.classList.remove("is-loading", "is-error");
  submitBtn.disabled = false;
  fileInput.disabled = false;
  targetSelect.disabled = false;
  fileClear.disabled = false;
  clearStatusTimers();
  stopFakeProgress();
  setProgress(0);
}

function setLoadingState() {
  stopFakeProgress();
  clearStatusTimers();
  setProgress(0);
  statusEl.textContent = "Translating document…";
  progressWrap.classList.remove("is-complete");
  progressWrap.classList.add("is-visible");
  form.classList.add("is-loading");
  errorEl.textContent = "";

  statusTimers.push(
    window.setTimeout(() => {
      if (form.classList.contains("is-loading") && statusEl) statusEl.textContent = "Translating complex content…";
    }, 10000)
  );
  statusTimers.push(
    window.setTimeout(() => {
      if (form.classList.contains("is-loading") && statusEl) statusEl.textContent = "Large document detected — this may take a little longer…";
    }, 30000)
  );
  statusTimers.push(
    window.setTimeout(() => {
      if (form.classList.contains("is-loading") && statusEl) statusEl.textContent = "Still working — almost there.";
      let alternate = false;
      const intervalId = window.setInterval(() => {
        if (!form.classList.contains("is-loading") || !statusEl) return;
        alternate = !alternate;
        statusEl.textContent = alternate ? "Processing large document…" : "Still working — almost there.";
      }, 60000);
      statusTimers.push(intervalId);
    }, 60000)
  );

  const rampDuration = 2000;
  const start = performance.now();

  progressRampId = window.setInterval(() => {
    const elapsed = performance.now() - start;
    if (elapsed >= rampDuration) {
      window.clearInterval(progressRampId);
      progressRampId = null;
      setProgress(80);
      let creepProgress = 80;
      progressCreepId = window.setInterval(() => {
        creepProgress += 0.15;
        if (creepProgress >= 95) {
          creepProgress = 95;
          window.clearInterval(progressCreepId);
          progressCreepId = null;
        }
        setProgress(creepProgress);
      }, 400);
      return;
    }
    const t = elapsed / rampDuration;
    const eased = 1 - Math.pow(1 - t, 1.6);
    setProgress(eased * 80);
  }, 50);
}

function setErrorState(message) {
  statusEl.textContent = "";
  errorEl.textContent = message || "Something went wrong while processing your document. Please try again.";
  progressWrap.classList.remove("is-visible", "is-complete");
  form.classList.remove("is-loading");
  form.classList.add("is-error");
  submitBtn.disabled = true;
  fileInput.disabled = false;
  targetSelect.disabled = false;
  fileClear.disabled = false;
  clearStatusTimers();
  stopFakeProgress();
  setProgress(0);
  isSubmitting = false;
}

function clearErrorLock() {
  errorEl.textContent = "";
  form.classList.remove("is-error");
  submitBtn.disabled = false;
}

targetSelect.addEventListener("change", () => {
  targetSelect.blur();
  clearErrorLock();
});

fileInput.addEventListener("change", () => {
  fileInput.blur();
  clearErrorLock();
  updateFileSelectionUI();
});

fileClear.addEventListener("click", (e) => {
  e.preventDefault();
  clearErrorLock();
  fileSelection.classList.remove("is-visible");
  const duration = 320;
  window.setTimeout(() => {
    fileInput.value = "";
    fileSelectionName.textContent = "";
  }, duration);
});

submitBtn.addEventListener("click", (e) => {
  if (isSubmitting || form.classList.contains("is-loading") || form.classList.contains("is-error")) e.preventDefault();
});

form.addEventListener("keydown", (e) => {
  if (form.classList.contains("is-loading")) {
    e.preventDefault();
    e.stopPropagation();
    return;
  }

  if (e.key !== "Enter") return;

  if (!canSubmit()) {
    e.preventDefault();
    e.stopPropagation();
    return;
  }

  e.preventDefault();
  e.stopPropagation();
  if (typeof form.requestSubmit === "function") {
    form.requestSubmit();
  } else {
    submitBtn.click();
  }
});

updateFileSelectionUI();

window.addEventListener("pageshow", (event) => {
  stopFakeProgress();
  isSubmitting = false;
  if (event.persisted && form && (form.classList.contains("is-loading") || form.classList.contains("is-error"))) {
    setIdleState();
  }
});

if (fileInputWrap) {
  fileInputWrap.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.stopPropagation();
    fileInputWrap.classList.add("drag-over");
  });
  fileInputWrap.addEventListener("dragleave", (e) => {
    e.preventDefault();
    e.stopPropagation();
    fileInputWrap.classList.remove("drag-over");
  });
  fileInputWrap.addEventListener("drop", (e) => {
    e.preventDefault();
    e.stopPropagation();
    fileInputWrap.classList.remove("drag-over");
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (isSubmitting || form.classList.contains("is-loading")) return;
  if (form.classList.contains("is-error")) return;

  isSubmitting = true;

  errorEl.textContent = "";
  statusEl.textContent = "";
  statusEl.innerHTML = "";

  fileInput.disabled = true;
  targetSelect.disabled = true;
  submitBtn.disabled = true;
  fileClear.disabled = true;
  form.classList.add("is-loading");

  const file = fileInput.files[0];
  if (!file) {
    setErrorState("Please choose a PDF file to translate.");
    return;
  }
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    setErrorState("Only PDF files are supported.");
    return;
  }

  const targetLanguage = targetSelect.value;
  if (!targetLanguage) {
    setErrorState("Please select a target language.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_language", targetLanguage);

  setLoadingState();

  try {
    const response = await fetch("/translate", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      stopFakeProgress();
      let message = "Something went wrong while processing your document. Please try again.";
      if (response.status === 400) {
        message =
          "The uploaded file could not be processed. Please upload a valid PDF document.";
      } else if (response.status === 502) {
        message =
          "Translation service is temporarily unavailable. Please try again.";
      } else if (response.status === 500) {
        message = "Server error. Please try again later.";
      }
      setErrorState(message);
      return;
    }

    stopFakeProgress();
    setProgress(100);
    await new Promise((r) => setTimeout(r, 350));

    progressWrap.classList.add("is-complete");
    await new Promise((r) => setTimeout(r, 320));

    const blob = await response.blob();

    const contentDisposition = response.headers.get("Content-Disposition");
    const match = contentDisposition && contentDisposition.match(/filename="?([^";]+)"?/i);
    let filename = match && match[1] ? match[1] : null;
    if (!filename) {
      const base = file.name ? file.name.replace(/\.pdf$/i, "") : "document";
      filename = `${base}_translated.pdf`;
    }

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

    setIdleState();
  } catch (err) {
    stopFakeProgress();
    setErrorState(
      "Something went wrong while processing your document. Please try again.",
    );
  } finally {
    clearStatusTimers();
    stopFakeProgress();
    isSubmitting = false;
  }
});
