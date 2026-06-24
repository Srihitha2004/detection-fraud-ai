// Chrome Extension Content Script for AI Cargo Fraud Detector

let modalContainer = null;

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "show_loading") {
    createOrUpdateModal("Analyzing communication...", "Please wait while our lightweight security agents run ML predictions and scans.", true);
  } else if (message.action === "show_result") {
    renderAnalysisResult(message.data, message.text);
  } else if (message.action === "show_error") {
    createOrUpdateModal("Analysis Failed", message.error, false, true);
  }
});

function createOrUpdateModal(title, bodyHtml, isLoading = false, isError = false) {
  // If modal exists, remove it first
  if (modalContainer) {
    modalContainer.remove();
  }

  // Create outer modal container
  modalContainer = document.createElement("div");
  modalContainer.id = "cargo-fraud-detector-modal";
  
  // Inline styles for isolation from host page stylesheet rules
  Object.assign(modalContainer.style, {
    position: "fixed",
    top: "30px",
    right: "30px",
    width: "360px",
    backgroundColor: "#ffffff",
    boxShadow: "0 10px 30px rgba(0, 0, 0, 0.25)",
    borderRadius: "10px",
    zIndex: "2147483647", // Max z-index
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    border: "1px solid #dddddd",
    overflow: "hidden",
    boxSizing: "border-box",
    color: "#333333",
    lineHeight: "1.4"
  });

  // Header Banner styling
  const header = document.createElement("div");
  Object.assign(header.style, {
    background: "linear-gradient(135deg, #0040a0 0%, #002560 100%)",
    color: "#ffffff",
    padding: "15px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  });

  const headerTitle = document.createElement("span");
  headerTitle.textContent = "AI Cargo Fraud Detector";
  headerTitle.style.fontWeight = "bold";
  headerTitle.style.fontSize = "14px";
  headerTitle.style.letterSpacing = "0.5px";
  header.appendChild(headerTitle);

  // Close Button
  const closeBtn = document.createElement("button");
  closeBtn.textContent = "✕";
  Object.assign(closeBtn.style, {
    background: "none",
    border: "none",
    color: "#ffffff",
    fontSize: "16px",
    cursor: "pointer",
    fontWeight: "bold",
    opacity: "0.8",
    padding: "0 5px"
  });
  closeBtn.addEventListener("mouseover", () => closeBtn.style.opacity = "1");
  closeBtn.addEventListener("mouseout", () => closeBtn.style.opacity = "0.8");
  closeBtn.addEventListener("click", () => {
    modalContainer.remove();
    modalContainer = null;
  });
  header.appendChild(closeBtn);
  modalContainer.appendChild(header);

  // Body Container
  const body = document.createElement("div");
  body.style.padding = "20px";
  body.style.maxHeight = "500px";
  body.style.overflowY = "auto";

  if (isLoading) {
    const loadingSpinner = document.createElement("div");
    loadingSpinner.innerHTML = `
      <div style="text-align: center; padding: 20px 0;">
        <div style="display: inline-block; width: 30px; height: 30px; border: 3px solid rgba(0, 64, 160, 0.2); border-radius: 50%; border-top-color: #0040a0; animation: spin 1s linear infinite; margin-bottom: 12px;"></div>
        <h4 style="margin: 0 0 5px 0; color: #1a1a1a; font-size: 15px;">${title}</h4>
        <p style="margin: 0; color: #666666; font-size: 12px;">${bodyHtml}</p>
      </div>
      <style>
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      </style>
    `;
    body.appendChild(loadingSpinner);
  } else if (isError) {
    const errorBody = document.createElement("div");
    errorBody.innerHTML = `
      <div style="text-align: center; padding: 10px 0;">
        <span style="font-size: 32px; margin-bottom: 10px; display: block;">⚠️</span>
        <h4 style="margin: 0 0 8px 0; color: #dc3545; font-size: 15px;">${title}</h4>
        <p style="margin: 0; color: #444444; font-size: 12px; line-height: 1.5;">${bodyHtml}</p>
      </div>
    `;
    body.appendChild(errorBody);
  } else {
    body.innerHTML = bodyHtml;
  }

  modalContainer.appendChild(body);
  document.body.appendChild(modalContainer);
}

function renderAnalysisResult(data, text) {
  const isSafe = data.classification === "SAFE";
  const isSuspicious = data.classification === "SUSPICIOUS";
  
  let badgeColor = "rgba(220, 53, 69, 0.15)";
  let badgeTextColor = "#dc3545";
  let badgeBorder = "1px solid rgba(220, 53, 69, 0.3)";
  let checkColor = "#dc3545";

  if (isSafe) {
    badgeColor = "rgba(25, 135, 84, 0.15)";
    badgeTextColor = "#198754";
    badgeBorder = "1px solid rgba(25, 135, 84, 0.3)";
    checkColor = "#198754";
  } else if (isSuspicious) {
    badgeColor = "rgba(255, 193, 7, 0.15)";
    badgeTextColor = "#b58100";
    badgeBorder = "1px solid rgba(255, 193, 7, 0.3)";
    checkColor = "#b58100";
  }

  // Build detected keywords markup
  let keywordsHtml = '<span style="color: #888; font-style: italic; font-size: 12px;">None</span>';
  if (data.detected_keywords && data.detected_keywords.length > 0) {
    keywordsHtml = data.detected_keywords
      .map(kw => `<span style="display: inline-block; background-color: #e9ecef; color: #495057; font-size: 11px; padding: 2px 8px; border-radius: 20px; margin-right: 4px; margin-bottom: 4px; font-weight: 500;">${kw}</span>`)
      .join("");
  }

  // Build reasons markup
  let reasonsHtml = `
    <li style="margin-bottom: 6px; display: flex; align-items: flex-start;">
      <span style="color: #198754; font-weight: bold; margin-right: 8px;">✓</span>
      <span style="font-size: 12px;">No active phishing or fraud matches detected.</span>
    </li>`;
  if (data.reasons && data.reasons.length > 0) {
    reasonsHtml = data.reasons
      .map(r => `
        <li style="margin-bottom: 6px; display: flex; align-items: flex-start;">
          <span style="color: ${checkColor}; font-weight: bold; margin-right: 8px;">✓</span>
          <span style="font-size: 12px; color: #444;">${r}</span>
        </li>`)
      .join("");
  }

  // Build recommendations markup
  let recsHtml = `
    <li style="margin-bottom: 6px; display: flex; align-items: flex-start;">
      <span style="color: #0040a0; font-weight: bold; margin-right: 8px;">→</span>
      <span style="font-size: 12px;">Standard operational guidelines apply.</span>
    </li>`;
  if (data.recommendation && data.recommendation.length > 0) {
    recsHtml = data.recommendation
      .map(rec => `
        <li style="margin-bottom: 6px; display: flex; align-items: flex-start;">
          <span style="color: #0040a0; font-weight: bold; margin-right: 8px;">→</span>
          <span style="font-size: 12px; color: #444;">${rec}</span>
        </li>`)
      .join("");
  }

  const resultBodyHtml = `
    <div style="text-align: center; margin-bottom: 15px;">
      <div style="font-size: 11px; text-transform: uppercase; color: #666666; font-weight: bold; margin-bottom: 4px; letter-spacing: 0.5px;">Classification</div>
      <span style="display: inline-block; padding: 4px 16px; font-size: 14px; font-weight: bold; border-radius: 20px; text-transform: uppercase; background-color: ${badgeColor}; color: ${badgeTextColor}; border: ${badgeBorder};">${data.classification}</span>
    </div>

    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
      <div style="flex: 1; background-color: #f8f9fa; border: 1px solid #eeeeee; border-radius: 6px; padding: 8px; text-align: center;">
        <div style="font-size: 10px; color: #666; text-transform: uppercase; font-weight: bold; margin-bottom: 2px;">Confidence</div>
        <div style="font-size: 16px; font-weight: bold; color: #1a1a1a;">${data.confidence}%</div>
      </div>
      <div style="flex: 1; background-color: #f8f9fa; border: 1px solid #eeeeee; border-radius: 6px; padding: 8px; text-align: center;">
        <div style="font-size: 10px; color: #666; text-transform: uppercase; font-weight: bold; margin-bottom: 2px;">Risk Score</div>
        <div style="font-size: 16px; font-weight: bold; color: #1a1a1a;">${data.risk_score}</div>
      </div>
    </div>

    <div style="border-top: 1px solid #eeeeee; padding-top: 12px;">
      <h5 style="margin: 0 0 6px 0; font-size: 12px; color: #1a1a1a; font-weight: bold; text-transform: uppercase; letter-spacing: 0.3px;">Detected Keywords</h5>
      <div style="margin-bottom: 12px;">${keywordsHtml}</div>

      <h5 style="margin: 0 0 6px 0; font-size: 12px; color: #1a1a1a; font-weight: bold; text-transform: uppercase; letter-spacing: 0.3px;">Reasons</h5>
      <ul style="list-style: none; padding-left: 0; margin: 0 0 12px 0;">${reasonsHtml}</ul>

      <h5 style="margin: 0 0 6px 0; font-size: 12px; color: #1a1a1a; font-weight: bold; text-transform: uppercase; letter-spacing: 0.3px;">Recommendation</h5>
      <ul style="list-style: none; padding-left: 0; margin: 0;">${recsHtml}</ul>
    </div>
  `;

  createOrUpdateModal(null, resultBodyHtml, false, false);
}
