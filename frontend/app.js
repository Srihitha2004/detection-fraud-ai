document.addEventListener("DOMContentLoaded", () => {
    const analyzeForm = document.getElementById("analyze-form");
    const btnSubmit = document.getElementById("btn-submit");
    const submitSpinner = document.getElementById("submit-spinner");
    const submitIcon = document.getElementById("submit-icon");
    const submitText = document.getElementById("submit-text");
    
    const resultsPlaceholder = document.getElementById("results-placeholder");
    const resultsContent = document.getElementById("results-content");
    
    const resClassification = document.getElementById("res-classification");
    const resConfidence = document.getElementById("res-confidence");
    const resRiskScore = document.getElementById("res-risk-score");
    const resTrustedDomain = document.getElementById("res-trusted-domain");
    const resTrustedSender = document.getElementById("res-trusted-sender");
    const resDomainSpoofing = document.getElementById("res-domain-spoofing");
    const resRepeatedMessage = document.getElementById("res-repeated-message");
    const resKeywords = document.getElementById("res-keywords");
    const resReasons = document.getElementById("res-reasons");
    const resRecommendation = document.getElementById("res-recommendation");

    // Email validation regex (must contain @ and domain name)
    const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    analyzeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const senderNumber = document.getElementById("sender_number").value.trim();
        const senderEmail = document.getElementById("sender_email").value.trim();
        const message = document.getElementById("message").value.trim();
        
        // 1. Client-side Validation: At least one contact detail must be provided
        if (!senderNumber && !senderEmail) {
            alert("Please enter Sender Number or Sender Email.");
            return;
        }

        // 2. Client-side Validation: Sender Number (optional but must contain digits only, 10-15 digits)
        if (senderNumber) {
            const isDigits = /^\d+$/.test(senderNumber);
            if (!isDigits || senderNumber.length < 10 || senderNumber.length > 15) {
                alert("Sender Number must contain digits only (no spaces, dashes, or + signs) and be between 10 and 15 digits.");
                return;
            }
        }

        // 3. Client-side Validation: Sender Email (optional but must contain @ and domain)
        if (senderEmail) {
            if (!EMAIL_REGEX.test(senderEmail)) {
                alert("Sender Email must follow a valid email format (e.g. tracking@fedex.com).");
                return;
            }
        }

        // 4. Client-side Validation: Message is required
        if (!message) {
            alert("Message text is required!");
            return;
        }

        // UI Feedback: Loading state
        btnSubmit.disabled = true;
        submitSpinner.classList.remove("d-none");
        submitIcon.classList.add("d-none");
        submitText.textContent = "Analyzing...";

        try {
            // POST request to backend
            const response = await fetch("/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    sender_number: senderNumber,
                    sender_email: senderEmail,
                    message: message
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to analyze message");
            }

            // UI Feedback: Show results
            resultsPlaceholder.classList.add("d-none");
            resultsContent.classList.remove("d-none");

            // 1. Classification Badge setting
            resClassification.textContent = data.classification;
            resClassification.className = "badge px-4 py-2 fs-5 fw-bold";
            if (data.classification === "SAFE") {
                resClassification.classList.add("badge-safe");
            } else if (data.classification === "SUSPICIOUS") {
                resClassification.classList.add("badge-suspicious");
            } else {
                resClassification.classList.add("badge-fraud");
            }

            // 2. Confidence and Risk Score
            resConfidence.textContent = `${data.confidence}%`;
            resRiskScore.textContent = data.risk_score;

            // 3. Whitelists & Lookalikes & Duplicate Displays
            resTrustedDomain.textContent = data.trusted_domain;
            resTrustedDomain.className = data.trusted_domain !== "No" ? "fw-bold text-success text-end col-6" : "fw-semibold text-dark text-end col-6";
            
            resTrustedSender.textContent = data.trusted_sender;
            resTrustedSender.className = data.trusted_sender !== "No" ? "fw-bold text-success text-end col-6" : "fw-semibold text-dark text-end col-6";

            resDomainSpoofing.textContent = data.domain_spoofing;
            resDomainSpoofing.className = data.domain_spoofing !== "No" ? "fw-bold text-danger text-end col-6 animate-pulse" : "fw-semibold text-dark text-end col-6";

            resRepeatedMessage.textContent = data.repeated_message;
            resRepeatedMessage.className = data.repeated_message !== "New" ? "fw-bold text-warning text-end col-6" : "fw-semibold text-dark text-end col-6";

            // 4. Detected Fraud Phrases
            resKeywords.innerHTML = "";
            if (data.detected_keywords && data.detected_keywords.length > 0) {
                data.detected_keywords.forEach(kw => {
                    const pill = document.createElement("span");
                    pill.className = "keyword-pill";
                    pill.textContent = kw;
                    resKeywords.appendChild(pill);
                });
            } else {
                const emptyMsg = document.createElement("span");
                emptyMsg.className = "text-muted small italic";
                emptyMsg.textContent = "None detected";
                resKeywords.appendChild(emptyMsg);
            }

            // 5. Reasons
            resReasons.innerHTML = "";
            if (data.reasons && data.reasons.length > 0) {
                data.reasons.forEach(reason => {
                    const li = document.createElement("li");
                    li.className = "reason-item";
                    
                    let checkClass = "text-danger";
                    if (reason.startsWith("Trusted") || reason === "No phishing indicators detected") {
                        checkClass = "text-success";
                    } else if (reason.startsWith("Repeated") || reason.startsWith("Message already")) {
                        checkClass = "text-warning";
                    }
                    
                    li.innerHTML = `<span class="${checkClass} fw-bold me-2">✓</span> ${reason}`;
                    resReasons.appendChild(li);
                });
            } else {
                const li = document.createElement("li");
                li.className = "reason-item text-muted small";
                li.innerHTML = `<span class="text-success fw-bold me-2">✓</span> Normal communication characteristics`;
                resReasons.appendChild(li);
            }

            // 6. Recommendations
            resRecommendation.innerHTML = "";
            if (data.recommendation && data.recommendation.length > 0) {
                data.recommendation.forEach(rec => {
                    const li = document.createElement("li");
                    li.className = "rec-item";
                    
                    let iconClass = "fa-arrow-right-long text-primary";
                    if (rec === "Safe to proceed") {
                        iconClass = "fa-check text-success";
                    } else if (rec.includes("Warning") || rec.includes("unverified")) {
                        iconClass = "fa-triangle-exclamation text-warning";
                    } else if (rec.includes("Block")) {
                        iconClass = "fa-ban text-danger";
                    }
                    
                    li.innerHTML = `<i class="fa-solid ${iconClass} me-2"></i> ${rec}`;
                    resRecommendation.appendChild(li);
                });
            } else {
                const li = document.createElement("li");
                li.className = "rec-item text-muted small";
                li.innerHTML = `<i class="fa-solid fa-arrow-right-long text-success me-2"></i> Maintain standard procedure`;
                resRecommendation.appendChild(li);
            }

        } catch (error) {
            console.error(error);
            alert(`Error: ${error.message}`);
        } finally {
            // Restore button state
            btnSubmit.disabled = false;
            submitSpinner.classList.add("d-none");
            submitIcon.classList.remove("d-none");
            submitText.textContent = "Analyze Communication";
        }
    });
});
