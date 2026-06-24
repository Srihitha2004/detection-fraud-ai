Office.onReady((info) => {
  if (info.host === Office.HostType.Outlook) {
    document.getElementById("status").textContent = "Office.js initialized. Ready to scan.";
    initAddIn();
  } else {
    document.getElementById("status").textContent = "Not running in Outlook Host.";
  }
});

function initAddIn() {
  const btnAnalyze = document.getElementById("btn-analyze");
  const metaFrom = document.getElementById("meta-from");
  const metaSubject = document.getElementById("meta-subject");

  // Get active item
  const item = Office.context.mailbox.item;
  if (!item) {
    document.getElementById("status").textContent = "No active email message loaded.";
    return;
  }

  // Display metadata
  const sender = item.from ? item.from.emailAddress : "Unknown Sender";
  const subject = item.subject || "(No Subject)";
  
  metaFrom.textContent = sender;
  metaSubject.textContent = subject;
  
  // Enable the button
  btnAnalyze.disabled = false;

  btnAnalyze.addEventListener("click", () => {
    analyzeEmail(item, sender);
  });
}

function analyzeEmail(item, senderEmail) {
  const btnAnalyze = document.getElementById("btn-analyze");
  const statusDiv = document.getElementById("status");
  const resultsCard = document.getElementById("results-card");
  
  btnAnalyze.disabled = true;
  statusDiv.textContent = "Extracting email body...";
  resultsCard.style.display = "none";

  // Fetch body content asynchronously as plain text
  item.body.getAsync(Office.CoercionType.Text, (result) => {
    if (result.status === Office.AsyncResultStatus.Failed) {
      statusDiv.textContent = "Error: Failed to read email body content.";
      btnAnalyze.disabled = false;
      return;
    }

    const emailBody = result.value || "";
    statusDiv.textContent = "Sending to AI security agents...";

    // Send payload to the local Flask server
    fetch("http://localhost:5001/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        sender: senderEmail,
        caller: "Email Metadata",
        message: emailBody
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      statusDiv.textContent = "Analysis complete.";
      btnAnalyze.disabled = false;
      displayResults(data);
    })
    .catch(err => {
      console.error(err);
      statusDiv.textContent = "Connection failed. Please ensure backend server is running on http://localhost:5001.";
      btnAnalyze.disabled = false;
    });
  });
}

function displayResults(data) {
  const resultsCard = document.getElementById("results-card");
  const resClassification = document.getElementById("res-classification");
  const resConfidence = document.getElementById("res-confidence");
  const resRiskScore = document.getElementById("res-risk-score");
  const resKeywords = document.getElementById("res-keywords");
  const resReasons = document.getElementById("res-reasons");
  const resRecommendation = document.getElementById("res-recommendation");

  resultsCard.style.display = "block";

  // Classification Badge
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

  // Recommendations
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
