document.addEventListener('DOMContentLoaded', () => {
  // Get all our UI elements
  const loginForm = document.getElementById('login-form');
  const trackerUI = document.getElementById('tracker-ui');
  const messageEl = document.getElementById('message');
  
  // Login form elements
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const loginButton = document.getElementById('loginButton');
  
  // Tracker UI elements
  const trackButton = document.getElementById('trackButton');
  const logoutButton = document.getElementById('logoutButton');
  const dashboardButton = document.getElementById('dashboardButton');

  // We'll store the current URL here
  let currentUrl = '';

  // --- Main Function: Check login status ---
  function checkLoginStatus() {
    chrome.storage.local.get(['token'], (result) => {
      if (result.token) {
        // We have a token! Show the main tracker UI
        showTrackerUI();
      } else {
        // No token. Show the login form
        showLoginForm();
      }
    });
  }

  // --- UI Toggles ---
  function showLoginForm() {
    trackerUI.style.display = 'none';
    loginForm.style.display = 'block';
  }

  function showTrackerUI() {
    loginForm.style.display = 'none';
    trackerUI.style.display = 'block';
    
    // Check if this page is already tracked.
    checkIfPageIsTracked();
  }

  // --- Checks if the current tab's URL is already tracked ---
  async function checkIfPageIsTracked() {
    messageEl.textContent = 'Checking page status...';
    trackButton.disabled = true;

    // 1. Get current tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      const tab = tabs[0];
      if (!tab.url || !tab.url.startsWith('http')) {
        messageEl.textContent = 'This page cannot be tracked.';
        return;
      }
      currentUrl = tab.url; // Store it

      // 2. Get saved token
      chrome.storage.local.get(['token'], async (result) => {
        if (!result.token) {
          showLoginForm(); // Should not happen, but good check
          return;
        }

        // 3. Call our backend endpoint
        try {
          const response = await fetch(`http://localhost:8000/api/pages/by-url?url=${encodeURIComponent(currentUrl)}`, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${result.token}` }
          });

          if (response.status === 404) {
            // 404 means "Not Found" -> GOOD! We can track it.
            messageEl.textContent = 'Ready to track this page.';
            trackButton.textContent = 'Track This Page';
            trackButton.disabled = false;
          } else if (response.ok) {
            // 200 means "OK" -> It's already tracked.
            messageEl.textContent = 'This page is already being tracked.';
            trackButton.textContent = 'Already Tracked';
            trackButton.disabled = true;
          } else {
            // Other error
            const data = await response.json();
            throw new Error(data.detail || 'Could not check page status.');
          }
        } catch (error) {
          messageEl.textContent = `Error: ${error.message}`;
        }
      });
    });
  }

  // --- Event Listeners ---
  loginButton.addEventListener('click', handleLogin);
  logoutButton.addEventListener('click', handleLogout);
  trackButton.addEventListener('click', handleTrackPage);
  dashboardButton.addEventListener('click', handleGoToDashboard);

  // --- Logic Functions ---

  async function handleLogin() {
    const email = emailInput.value;
    const password = passwordInput.value;
    if (!email || !password) return;
    
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
      const response = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Login failed');

      // ----------------------------------------------------
      // THIS IS THE FIXED LINE
      // ----------------------------------------------------
      chrome.storage.local.set({ token: data.access_token }, () => {
        showTrackerUI(); // Switch to the main UI
      });
      // ----------------------------------------------------

    } catch (error) {
      alert(`Login Error: ${error.message}`);
    }
  }

  function handleLogout() {
    chrome.storage.local.remove(['token'], () => {
      showLoginForm(); // Switch back to the login form
    });
  }

  async function handleTrackPage() {
    trackButton.disabled = true;
    messageEl.textContent = 'Sending to backend...';

    chrome.storage.local.get(['token'], async (result) => {
      if (!result.token) {
        messageEl.textContent = 'Error: Token missing. Please log out and in again.';
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/pages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${result.token}`,
            'X-Request-Source': 'chrome-extension'  // ← ADDED THIS LINE
          },
          body: JSON.stringify({
            url: currentUrl, // Use the global var
            check_interval_minutes: 1440
            // Don't send display_name - let backend generate sequential name
          })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'API request failed');

        messageEl.textContent = 'Page tracked successfully!';
        checkIfPageIsTracked(); 
      } catch (error) {
        messageEl.textContent = `Error: ${error.message}`;
        trackButton.disabled = false;
      }
    });
  }

  function handleGoToDashboard() {
    chrome.tabs.create({ url: 'http://localhost:3000' });
  }

  // --- Run on start ---
  checkLoginStatus();
});