document.getElementById('fillBtn').addEventListener('click', async () => {
  setStatus('Injecting autofill script...');
  let [tab] = await chrome.tabs.query({active: true, currentWindow: true});
  chrome.scripting.executeScript({
    target: {tabId: tab.id},
    files: ['content.js']
  }, () => {
    if (chrome.runtime.lastError) {
      setStatus('❌ Failed to inject script: ' + chrome.runtime.lastError.message);
    } else {
      setStatus('🤖 Autofill script running...');
      // Wait for status updates from content.js
    }
  });
});

// Listen for status messages from content.js
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'autofill-status') {
    setStatus(msg.text);
  }
});

function setStatus(text) {
  document.getElementById('status').textContent = text;
} 