document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("popup-form");
  const messageInput = document.getElementById("message");
  const btnSubmit = document.getElementById("btn-submit");
  
  const resultsCard = document.getElementById("results-card");
  const placeholder = document.getElementById("no-results-placeholder");
  
  const resClassification = document.getElementById("res-classification");
  const resConfidence = document.getElementById("res-confidence");
  const resRiskScore = document.getElementById("res-risk-score");
  const resKeywords = document.getElementById("res-keywords");
  const resReasons = document.getElementById("res-reasons");
  const resRecommendation = document.getElementById("res-recommendation");

  // Load cached analysis on open
  chrome.storage.local.get(["lastResult", "lastText"], (items) => {
    if (items.lastResult) {
      if (items.lastText) {
        messageInput.value = items.lastText;
      }
      displayResults(items.lastResult);
    }
  });

  // Handle manual input form submit
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (!text) return;

    btnSubmit.disabled = true;
    btnSubmit.textContent = "Analyzing...";

    try {
      const response = await fetch("http://localhost:5001/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          sender: "Extension Manual Paste",
          caller: "Unknown",
          message: text
        })
      });

      if (!response.ok) {
        throw new Error("Local backend server returned an error.");
      }

      const data = await response.json();
      
      // Store in storage
      chrome.storage.local.set({ lastResult: data, lastText: text });
      
      // Render
      displayResults(data);
    } catch (err) {
      console.error(err);
      alert("Failed to analyze. Please ensure the Flask app is running at http://localhost:5001.");
    } finally {
      btnSubmit.disabled = false;
      btnSubmit.textContent = "Analyze Message";
    }
  });

  function displayResults(data) {
    placeholder.style.display = "none";
    resultsCard.style.display = "block";

    // Set classification badge
    resClassification.textContent = data.classification;
    resClassification.className = "badge";
    if (data.classification === "SAFE") {
      resClassification.classList.add("badge-safe");
    } else if (data.classification === "SUSPICIOUS") {
      resClassification.classList.add("badge-suspicious");
    } else {
      resClassification.classList.add("badge-fraud");
    }

    // Scores
    resConfidence.textContent = `${data.confidence}%`;
    resRiskScore.textContent = data.risk_score;

    // Keywords
    resKeywords.innerHTML = "";
    if (data.detected_keywords && data.detected_keywords.length > 0) {
      data.detected_keywords.forEach(kw => {
        const pill = document.createElement("span");
        pill.className = "keyword-pill";
        pill.textContent = kw;
        resKeywords.appendChild(pill);
      });
    } else {
      resKeywords.innerHTML = '<span style="color: #888; font-style: italic; font-size: 0.75rem;">None</span>';
    }

    // Reasons
    resReasons.innerHTML = "";
    const isSafe = data.classification === "SAFE";
    const checkColor = isSafe ? "text-success" : "text-danger";
    
    if (data.reasons && data.reasons.length > 0) {
      data.reasons.forEach(reason => {
        const li = document.createElement("li");
        li.innerHTML = `<span class="check-icon ${checkColor}">✓</span> <span>${reason}</span>`;
        resReasons.appendChild(li);
      });
    } else {
      resReasons.innerHTML = `<li><span class="check-icon text-success">✓</span> <span>No fraud indicators detected</span></li>`;
    }

    // Recommendation
    resRecommendation.innerHTML = "";
    if (data.recommendation && data.recommendation.length > 0) {
      data.recommendation.forEach(rec => {
        const li = document.createElement("li");
        li.innerHTML = `<span class="check-icon text-primary">→</span> <span>${rec}</span>`;
        resRecommendation.appendChild(li);
      });
    } else {
      resRecommendation.innerHTML = `<li><span class="check-icon text-success">→</span> <span>Standard verification guidelines apply</span></li>`;
    }
  }
});
