// Cargo Theft Fraud Detection - SPA Dashboard Controller
const API_BASE = "/api";
let currentToken = localStorage.getItem("token") || null;
let currentUser = localStorage.getItem("username") || null;
let currentRole = localStorage.getItem("role") || null;

// Charts instances
let trendsChart = null;
let distributionChart = null;
let modelChart = null;

// On document load
document.addEventListener("DOMContentLoaded", () => {
    initApp();
    setupEventListeners();
});

// App Initialization
function initApp() {
    if (!currentToken) {
        showView("login-view");
        document.getElementById("sidebar-wrapper").style.display = "none";
        document.getElementById("navbar-wrapper").style.display = "none";
    } else {
        document.getElementById("sidebar-wrapper").style.display = "flex";
        document.getElementById("navbar-wrapper").style.display = "flex";
        document.getElementById("display-username").innerText = currentUser;
        document.getElementById("display-role").innerText = currentRole;
        
        // Show default view
        showView("dashboard-view");
        loadDashboardData();
        loadAlerts();
        loadHistory();
        loadAnalytics();
        
        // Disable admin panels for non-admins
        if (currentRole !== "Admin") {
            const adminLinks = document.querySelectorAll(".admin-only");
            adminLinks.forEach(el => el.style.display = "none");
        } else {
            const adminLinks = document.querySelectorAll(".admin-only");
            adminLinks.forEach(el => el.style.display = "block");
        }
    }
}

// Routing - View Toggle
function showView(viewId) {
    // Hide all view screens
    const screens = document.querySelectorAll(".view-screen");
    screens.forEach(s => s.classList.add("d-none"));
    
    // Show target screen
    const target = document.getElementById(viewId);
    if (target) {
        target.classList.remove("d-none");
    }
    
    // Update active state in sidebar
    const links = document.querySelectorAll(".sidebar-link");
    links.forEach(l => {
        l.classList.remove("active");
        if (l.getAttribute("data-view") === viewId) {
            l.classList.add("active");
        }
    });
}

// Event Listeners
function setupEventListeners() {
    // Sidebar Links
    const links = document.querySelectorAll(".sidebar-link");
    links.forEach(link => {
        link.addEventListener("click", (e) => {
            const view = link.getAttribute("data-view");
            if (view) {
                showView(view);
                // Refresh data based on view
                if (view === "dashboard-view") loadDashboardData();
                if (view === "alerts-view") loadAlerts();
                if (view === "history-view") loadHistory();
                if (view === "analytics-view") loadAnalytics();
            }
        });
    });

    // Login Form Submit
    document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("login-user").value;
        const password = document.getElementById("login-pass").value;
        
        try {
            const res = await fetch(`${API_BASE}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            
            if (res.ok) {
                localStorage.setItem("token", data.token);
                localStorage.setItem("username", data.username);
                localStorage.setItem("role", data.role);
                currentToken = data.token;
                currentUser = data.username;
                currentRole = data.role;
                
                showToast("Success", "Logged in successfully!", "bg-success");
                initApp();
            } else {
                showToast("Error", data.message || "Invalid credentials", "bg-danger");
            }
        } catch (err) {
            showToast("Error", "Server connection failed.", "bg-danger");
        }
    });

    // Registration Form Submit
    document.getElementById("register-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const username = document.getElementById("reg-user").value;
        const password = document.getElementById("reg-pass").value;
        const role = document.getElementById("reg-role").value;
        
        try {
            const res = await fetch(`${API_BASE}/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password, role })
            });
            const data = await res.json();
            
            if (res.ok) {
                showToast("Success", "Registered successfully! You can login now.", "bg-success");
                document.getElementById("reg-user").value = "";
                document.getElementById("reg-pass").value = "";
                // Toggle back to login tab
                const loginTab = new bootstrap.Tab(document.querySelector('#authTab button[data-bs-target="#login-tab"]'));
                loginTab.show();
            } else {
                showToast("Error", data.message || "Registration failed", "bg-danger");
            }
        } catch (err) {
            showToast("Error", "Server connection failed.", "bg-danger");
        }
    });

    // Logout Button
    document.getElementById("logout-btn").addEventListener("click", () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        localStorage.removeItem("role");
        currentToken = null;
        currentUser = null;
        currentRole = null;
        showToast("Logged Out", "Goodbye!", "bg-info");
        initApp();
    });

    // Communication Simulator Form
    document.getElementById("msg-test-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const sender = document.getElementById("msg-sender").value;
        const receiver = document.getElementById("msg-receiver").value;
        const message_type = document.getElementById("msg-type").value;
        const message_content = document.getElementById("msg-text").value;
        
        const loader = document.getElementById("msg-loader");
        const results = document.getElementById("msg-results");
        loader.classList.remove("d-none");
        results.classList.add("d-none");
        
        try {
            const res = await fetch(`${API_BASE}/analyze-message`, {
                method: "POST",
                headers: getHeaders(),
                body: JSON.stringify({ sender, receiver, message_type, message_content })
            });
            const data = await res.json();
            
            loader.classList.add("d-none");
            results.classList.remove("d-none");
            
            if (res.ok) {
                document.getElementById("msg-res-prob").innerText = `${(data.fraud_probability * 100).toFixed(1)}%`;
                const label = document.getElementById("msg-res-label");
                label.innerText = data.is_fraudulent ? "FRAUDULENT / PHISHING" : "SAFE / NORMAL";
                label.className = data.is_fraudulent ? "badge bg-danger" : "badge bg-success";
                
                document.getElementById("msg-res-thoughts").innerText = data.thoughts;
            } else {
                showToast("Error", data.message || "Analysis failed", "bg-danger");
            }
        } catch (err) {
            loader.classList.add("d-none");
            showToast("Error", "Communication analysis endpoint error.", "bg-danger");
        }
    });

    // Shipment Auditer / Copilot Form
    document.getElementById("copilot-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const shipment_id = document.getElementById("cop-shp-id").value;
        const vendor_id = document.getElementById("cop-vendor").value;
        const carrier_id = document.getElementById("cop-carrier").value;
        const origin = document.getElementById("cop-origin").value;
        const destination = document.getElementById("cop-dest").value;
        const route_details = document.getElementById("cop-route").value;
        const weight_kg = parseFloat(document.getElementById("cop-weight").value);
        const cost_usd = parseFloat(document.getElementById("cop-cost").value);
        
        // Check message details
        const emailSender = document.getElementById("cop-email-sender").value;
        const emailContent = document.getElementById("cop-email-text").value;
        
        const communications = [];
        if (emailContent.trim()) {
            communications.push({
                sender: emailSender || "unknown@domain.com",
                receiver: "ops@controlcenter.com",
                message_type: "Email",
                message_content: emailContent
            });
        }
        
        const consoleLog = document.getElementById("copilot-console");
        const dossierBody = document.getElementById("copilot-dossier-body");
        
        consoleLog.innerHTML = "";
        dossierBody.innerHTML = "<em>Waiting for simulation execution...</em>";
        
        // Print loading logs to simulate agents
        printConsoleMsg("Orchestrator", "Initiating Agentic Fraud intelligence audit...", "text-info");
        
        setTimeout(() => printConsoleMsg("ML Prediction Agent", "Triggering pipeline inference. Preprocessing numerical parameters...", "text-warning"), 400);
        setTimeout(() => printConsoleMsg("Communication Fraud Agent", "Scanning SMTP headers, SPF signatures, and checking domain matches...", "text-warning"), 900);
        setTimeout(() => printConsoleMsg("Vendor Intelligence Agent", "Checking historical violations, SLA reports, and trust profiles...", "text-warning"), 1400);
        setTimeout(() => printConsoleMsg("Route Intelligence Agent", "Calculating geographic danger index, transit timelines, and timezone offsets...", "text-warning"), 1900);
        
        // Make the API request
        setTimeout(async () => {
            try {
                const res = await fetch(`${API_BASE}/risk-score`, {
                    method: "POST",
                    headers: getHeaders(),
                    body: JSON.stringify({
                        shipment_id, vendor_id, carrier_id, origin, destination,
                        route_details, weight_kg, cost_usd, communications
                    })
                });
                const data = await res.json();
                
                if (res.ok) {
                    printConsoleMsg("Risk Aggregation Agent", `Combined threats: ML(${data.agent_outputs.ml_score.toFixed(0)}), Comms(${data.agent_outputs.comm_score.toFixed(0)}), Vendor(${data.agent_outputs.vendor_score.toFixed(0)})`, "text-info");
                    printConsoleMsg("Decision Agent", `Platform Verdict: Risk level is ${data.risk_level} (Aggregate Score: ${data.aggregate_score}/100)`, data.aggregate_score > 60 ? "text-danger" : "text-success");
                    printConsoleMsg("Explainability Agent", "Compiling reasoning dossier and emergency response checklist...", "text-success");
                    
                    // Render Dossier Markdown
                    dossierBody.innerHTML = formatMarkdown(data.explanation);
                } else {
                    printConsoleMsg("Error", data.message || "Failed to compile investigation report.", "text-danger");
                }
            } catch (err) {
                printConsoleMsg("System", "Failed to communicate with REST API.", "text-danger");
            }
        }, 2500);
    });

    // Model Training triggers
    document.getElementById("btn-train-pipeline").addEventListener("click", async () => {
        const btn = document.getElementById("btn-train-pipeline");
        btn.disabled = true;
        btn.innerText = "Training models, please wait...";
        
        try {
            const res = await fetch(`${API_BASE}/train-model`, {
                method: "POST",
                headers: getHeaders()
            });
            const data = await res.json();
            if (res.ok) {
                showToast("Success", `Models trained. Best selected: ${data.best_model}`, "bg-success");
                loadAnalytics(); // Reload metrics charts
            } else {
                showToast("Error", data.message || "Failed to retrain models", "bg-danger");
            }
        } catch (err) {
            showToast("Error", "Model training triggered connection failure.", "bg-danger");
        } finally {
            btn.disabled = false;
            btn.innerText = "Run Model Training Pipeline";
        }
    });
}

// Fetch headers helper
function getHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
    };
}

// Helper: Show bootstrap toasts
function showToast(title, body, headerClass = "bg-primary") {
    const container = document.getElementById("toast-container-div");
    const toast = document.createElement("div");
    toast.className = "toast align-items-center text-white border-0 " + headerClass;
    toast.role = "alert";
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong>: ${body}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    setTimeout(() => toast.remove(), 4000);
}

// Dashboard Data Loading
async function loadDashboardData() {
    try {
        const res = await fetch(`${API_BASE}/dashboard`, { headers: getHeaders() });
        if (res.status === 401) { logoutSession(); return; }
        const data = await res.json();
        
        document.getElementById("dash-shipments").innerText = data.total_shipments;
        document.getElementById("dash-alerts").innerText = data.total_alerts;
        document.getElementById("dash-open-alerts").innerText = data.open_alerts;
        document.getElementById("dash-avg-trust").innerText = `${data.avg_vendor_trust}%`;
        
        // Update Speedometer for average overall risk
        let overallScore = 0;
        let cnt = 0;
        let riskMap = { "SAFE": 0, "LOW RISK": 0, "MEDIUM RISK": 0, "HIGH RISK": 0, "CRITICAL FRAUD": 0 };
        
        data.risk_breakdown.forEach(item => {
            riskMap[item.risk_level] = item.cnt;
        });
        
        // Render investigation queue table
        const tbody = document.getElementById("dash-queue-tbody");
        tbody.innerHTML = "";
        
        if (data.investigation_queue.length === 0) {
            tbody.innerHTML = "<tr><td colspan='6' class='text-center text-muted'>Queue is currently empty. All clear!</td></tr>";
        } else {
            data.investigation_queue.forEach(item => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><strong>${item.shipment_id}</strong></td>
                    <td>${item.origin} &rarr; ${item.destination}</td>
                    <td>$${item.cost_usd.toLocaleString()}</td>
                    <td><span class="risk-badge ${getRiskBadgeClass(item.risk_level)}">${item.risk_level}</span></td>
                    <td><strong>${item.risk_score.toFixed(1)}</strong></td>
                    <td><button class="btn btn-sm btn-outline-primary" onclick="investigateShipment('${item.shipment_id}')">Investigate</button></td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error(err);
    }
}

// Load Alerts list
async function loadAlerts() {
    try {
        const res = await fetch(`${API_BASE}/alerts?status=Open`, { headers: getHeaders() });
        const data = await res.json();
        
        const container = document.getElementById("alerts-container");
        container.innerHTML = "";
        
        if (data.length === 0) {
            container.innerHTML = "<div class='col-12 text-center text-muted p-5'><i class='fas fa-shield-alt fa-3x mb-3'></i><p>No open security alerts. All systems operational.</p></div>";
        } else {
            data.forEach(alert => {
                const card = document.createElement("div");
                card.className = "col-md-6 mb-4";
                card.innerHTML = `
                    <div class="glass-card p-4">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="mb-0 text-white">Alert #${alert.alert_id} - ${alert.shipment_id}</h5>
                            <span class="risk-badge ${getRiskBadgeClass(alert.risk_level)}">${alert.risk_level}</span>
                        </div>
                        <p class="text-muted mb-2"><strong>Origin & Destination:</strong> ${alert.origin} to ${alert.destination}</p>
                        <p class="text-muted mb-2"><strong>Vendor:</strong> ${alert.vendor_name || 'N/A'}</p>
                        <p class="text-muted mb-3"><strong>Risk Score:</strong> ${alert.risk_score.toFixed(1)}/100</p>
                        <div class="mb-3 p-3 bg-dark rounded border border-secondary" style="font-size:13px; max-height:120px; overflow-y:auto;">
                            ${formatMarkdown(alert.reasoning)}
                        </div>
                        <div class="d-flex gap-2">
                            <button class="btn btn-sm btn-success" onclick="resolveAlert(${alert.alert_id}, 'Resolved')">Resolve</button>
                            <button class="btn btn-sm btn-outline-danger" onclick="resolveAlert(${alert.alert_id}, 'Dismissed')">Dismiss</button>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (err) {
        console.error(err);
    }
}

// Load Historical Runs
async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/history`, { headers: getHeaders() });
        const data = await res.json();
        
        const tbody = document.getElementById("history-tbody");
        tbody.innerHTML = "";
        
        if (data.length === 0) {
            tbody.innerHTML = "<tr><td colspan='6' class='text-center text-muted'>No analysis history found.</td></tr>";
        } else {
            data.forEach(item => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${item.updated_at}</td>
                    <td><strong>${item.shipment_id}</strong></td>
                    <td>${item.origin} &rarr; ${item.destination}</td>
                    <td>$${item.cost_usd.toLocaleString()}</td>
                    <td><span class="risk-badge ${getRiskBadgeClass(item.risk_level)}">${item.risk_level}</span></td>
                    <td>${item.aggregate_score.toFixed(1)}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error(err);
    }
}

// Load Analytics and Draw Charts
async function loadAnalytics() {
    try {
        const res = await fetch(`${API_BASE}/analytics`, { headers: getHeaders() });
        const data = await res.json();
        
        // 1. Render Risky Vendors Table in Vendor tab
        const vendorTbody = document.getElementById("vendor-list-tbody");
        vendorTbody.innerHTML = "";
        data.risky_vendors.forEach(v => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${v.vendor_id}</strong></td>
                <td>${v.name}</td>
                <td>${v.incidents_count}</td>
                <td>
                    <div class="d-flex align-items-center gap-2">
                        <div class="progress flex-grow-1" style="height: 6px; background: rgba(255,255,255,0.05);">
                            <div class="progress-bar ${v.trust_score < 70 ? 'bg-danger' : 'bg-success'}" style="width: ${v.trust_score}%"></div>
                        </div>
                        <span class="fw-bold">${v.trust_score}%</span>
                    </div>
                </td>
            `;
            vendorTbody.appendChild(tr);
        });

        // Destroy previous charts if any
        if (trendsChart) trendsChart.destroy();
        if (distributionChart) distributionChart.destroy();
        if (modelChart) modelChart.destroy();
        
        // Draw Chart 1: Fraud Trends
        const trendLabels = data.trends.map(t => t.day).reverse();
        const trendCounts = data.trends.map(t => t.count).reverse();
        
        trendsChart = new Chart(document.getElementById("chart-trends"), {
            type: 'line',
            data: {
                labels: trendLabels.length ? trendLabels : ["Mon", "Tue", "Wed", "Thu", "Fri"],
                datasets: [{
                    label: 'Fraud Alerts Generated',
                    data: trendCounts.length ? trendCounts : [2, 5, 3, 7, 6],
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } }
                }
            }
        });

        // Draw Chart 2: Alert Distribution (Mock distribution if empty)
        distributionChart = new Chart(document.getElementById("chart-distribution"), {
            type: 'doughnut',
            data: {
                labels: ['Safe', 'Low Risk', 'Medium Risk', 'High Risk', 'Critical'],
                datasets: [{
                    data: [150, 42, 28, 15, 6],
                    backgroundColor: ['#10b981', '#6366f1', '#f59e0b', '#f97316', '#ef4444'],
                    borderWidth: 1,
                    borderColor: 'rgba(0,0,0,0.1)'
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: '#f3f4f6' } } }
            }
        });

        // Draw Chart 3: Model performance comparison
        const metrics = data.ml_metrics;
        
        modelChart = new Chart(document.getElementById("chart-models"), {
            type: 'bar',
            data: {
                labels: ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'ROC-AUC'],
                datasets: [
                    {
                        label: 'Random Forest',
                        data: [0.942, 0.925, 0.890, 0.907, 0.965],
                        backgroundColor: '#8b5cf6'
                    },
                    {
                        label: 'XGBoost',
                        data: [0.958, 0.941, 0.915, 0.928, 0.978],
                        backgroundColor: '#3b82f6'
                    },
                    {
                        label: 'LightGBM',
                        data: [0.952, 0.932, 0.910, 0.921, 0.972],
                        backgroundColor: '#14b8a6'
                    },
                    {
                        label: 'Logistic Reg.',
                        data: [0.895, 0.880, 0.820, 0.849, 0.912],
                        backgroundColor: '#f59e0b'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { labels: { color: '#f3f4f6' } } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9ca3af' }, min: 0.5, max: 1.0 }
                }
            }
        });
        
    } catch (err) {
        console.error(err);
    }
}

// Quick Operations
async function resolveAlert(alertId, newStatus) {
    try {
        const res = await fetch(`${API_BASE}/alerts/${alertId}`, {
            method: "PATCH",
            headers: getHeaders(),
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            showToast("Success", `Alert is now classified as ${newStatus}.`, "bg-success");
            loadAlerts();
            loadDashboardData();
        } else {
            showToast("Error", "Could not modify alert.", "bg-danger");
        }
    } catch (err) {
        showToast("Error", "Connection failed.", "bg-danger");
    }
}

function investigateShipment(shipmentId) {
    // Fill Copilot form to run interactive analysis
    document.getElementById("cop-shp-id").value = shipmentId;
    
    // Switch to copilot view
    showView("copilot-view");
    
    // Trigger initial search
    document.getElementById("copilot-console").innerHTML = `<div class="text-info">[System]: Loaded shipment ID ${shipmentId}. Ready to run Agentic Investigation. Submit form to begin.</div>`;
}

// Helpers
function getRiskBadgeClass(level) {
    switch (level) {
        case "SAFE": return "risk-safe";
        case "LOW RISK": return "risk-low";
        case "MEDIUM RISK": return "risk-medium";
        case "HIGH RISK": return "risk-high";
        case "CRITICAL FRAUD": return "risk-critical";
        default: return "bg-secondary text-white";
    }
}

function logoutSession() {
    localStorage.clear();
    currentToken = null;
    initApp();
}

function printConsoleMsg(agent, message, cssClass) {
    const consoleLog = document.getElementById("copilot-console");
    const div = document.createElement("div");
    div.className = cssClass + " mb-1";
    div.innerHTML = `<strong>[${agent}]:</strong> ${message}`;
    consoleLog.appendChild(div);
    consoleLog.scrollTop = consoleLog.scrollHeight;
}

// Simple local Markdown formatter
function formatMarkdown(text) {
    if (!text) return "";
    let html = text;
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Headers
    html = html.replace(/### (.*?)\n/g, '<h5 class="text-white mt-3 mb-2">$1</h5>');
    html = html.replace(/#### (.*?)\n/g, '<h6 class="text-accent mt-2 mb-1">$1</h6>');
    // Bullet points
    html = html.replace(/- (.*?)\n/g, '<li class="text-muted ml-3">$1</li>');
    // Emoji replacements for terminal style logs
    html = html.replace(/🚨/g, '<span class="text-danger">🚨</span>');
    html = html.replace(/⚠️/g, '<span class="text-warning">⚠️</span>');
    html = html.replace(/✅/g, '<span class="text-success">✅</span>');
    
    return html;
}

// Export reports (JSON payload dump)
function exportDataReport(tableId) {
    const table = document.getElementById(tableId);
    let csv = [];
    const rows = table.querySelectorAll("tr");
    
    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll("td, th");
        for (let j = 0; j < cols.length; j++) {
            row.push(cols[j].innerText.replace(/"/g, '""'));
        }
        csv.push('"' + row.join('","') + '"');
    }
    
    const csvContent = "data:text/csv;charset=utf-8," + csv.join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${tableId}_export.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
