const submitBtn = document.getElementById("submitBtn");
const videoInput = document.getElementById("videoInput");
const preview = document.getElementById("preview");
const resultDiv = document.getElementById("result");
const loadingDiv = document.getElementById("loading");

const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);

const API_URL = isLocal
  ? "http://localhost:8000/predict"
  : "https://your-production-backend.com/predict";

const ACTION = document.body.dataset.action; // "kick" or "punch", from the <body> tag

videoInput.addEventListener("change", () => {
  const file = videoInput.files[0];
  if (file) {
    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";
  }
});

submitBtn.addEventListener("click", async () => {
  const file = videoInput.files[0];

  if (!file) {
    resultDiv.textContent = "Please select a video file first.";
    resultDiv.style.color = "black";
    return;
  }

  if (!ACTION) {
    resultDiv.textContent = "Page is missing a data-action attribute on <body>.";
    resultDiv.style.color = "red";
    return;
  }

  resultDiv.textContent = "";
  loadingDiv.style.display = "block";
  submitBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("action", ACTION);

    const response = await fetch(API_URL, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Server returned ${response.status}: ${errorText}`);
    }

    const data = await response.json();

    if (data.error) {
      resultDiv.textContent = `Error: ${data.error}`;
      resultDiv.style.color = "red";
    } else {
      resultDiv.textContent = `Result: ${data.label} (confidence: ${(data.confidence * 100).toFixed(1)}%)`;
      resultDiv.style.color = data.label === "good" ? "green" : "red";
    }

  } catch (err) {
    resultDiv.textContent = "Something went wrong analyzing the video.";
    resultDiv.style.color = "red";
    console.error(err);
  } finally {
    loadingDiv.style.display = "none";
    submitBtn.disabled = false;
  }
});