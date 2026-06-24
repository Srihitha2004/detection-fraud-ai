// Chrome Extension Service Worker for AI Cargo Fraud Detector

// Create context menu item on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "analyze-fraud",
    title: "Analyze Fraud",
    contexts: ["selection"]
  });
  console.log("Analyze Fraud context menu registered.");
});

// Listen for context menu click events
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "analyze-fraud") {
    const selectedText = info.selectionText;
    if (!selectedText || !tab || !tab.id) return;

    // Send loading status to content script
    chrome.tabs.sendMessage(tab.id, { action: "show_loading" }).catch(() => {
      // In case content script is not injected yet or tab active state changed
      console.log("Could not send show_loading to content script.");
    });

    // Request analysis from the local Flask API
    fetch("http://localhost:5001/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        sender: "Browser Highlight",
        caller: "Unknown",
        message: selectedText
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      // Store in local storage for popup
      chrome.storage.local.set({ lastResult: data, lastText: selectedText });
      
      // Update content script to show results
      chrome.tabs.sendMessage(tab.id, {
        action: "show_result",
        data: data,
        text: selectedText
      }).catch(err => console.error("Error sending show_result to content script:", err));
    })
    .catch(err => {
      console.error("API error:", err);
      chrome.tabs.sendMessage(tab.id, {
        action: "show_error",
        error: "Failed to connect to AI server. Please make sure the Flask backend is running on http://localhost:5001."
      }).catch(e => console.error("Error sending show_error to content script:", e));
    });
  }
});
