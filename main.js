/**
 * StudyAssist AI - Main JavaScript Utilities
 * =============================================
 * Shared utility functions used across all pages.
 * - Notifications
 * - Theme management
 * - General helpers
 */

// ─── Notification System ──────────────────────────────────────

/**
 * Show a notification toast message.
 * @param {string} message - The message to display
 * @param {string} type - 'success', 'error', or 'info'
 * @param {number} duration - How long to show (ms)
 */
function showNotification(message, type = 'info', duration = 3500) {
  const container = document.getElementById('notificationContainer');
  if (!container) return;

  const icons = { success: '✅', error: '❌', info: 'ℹ️' };

  const notif = document.createElement('div');
  notif.className = `notification ${type}`;
  notif.innerHTML = `
    <span>${icons[type] || icons.info}</span>
    <span>${message}</span>
  `;

  container.appendChild(notif);

  // Auto-remove after duration
  setTimeout(() => {
    notif.style.animation = 'slideOutRight 0.3s ease forwards';
    setTimeout(() => notif.remove(), 300);
  }, duration);
}

// Add slide-out animation
const style = document.createElement('style');
style.textContent = `
  @keyframes slideOutRight {
    to { transform: translateX(120%); opacity: 0; }
  }
`;
document.head.appendChild(style);


// ─── Theme Management ─────────────────────────────────────────

/**
 * Toggle between light and dark theme.
 */
function toggleTheme() {
  const html = document.documentElement;
  const currentTheme = html.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  applyTheme(newTheme);
}

/**
 * Apply a specific theme.
 * @param {string} theme - 'light' or 'dark'
 */
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('sa-theme', theme);

  // Update theme toggle button in sidebar if it exists
  const icon = document.getElementById('themeIcon');
  const label = document.getElementById('themeLabel');
  const themeSelect = document.getElementById('themeSelect');

  if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  if (label) label.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
  if (themeSelect) themeSelect.value = theme;
}

// Apply saved theme on page load
document.addEventListener('DOMContentLoaded', () => {
  const savedTheme = localStorage.getItem('sa-theme') || 'light';
  applyTheme(savedTheme);
});


// ─── Sidebar Toggle (Mobile) ──────────────────────────────────

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.toggle('open');
}


// ─── Loading State Helpers ────────────────────────────────────

/**
 * Show loading state on a button.
 * @param {string} btnId - Button element ID
 * @param {string} loadingText - Text to show while loading
 */
function setButtonLoading(btnId, loadingText = 'Loading...') {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = true;
  btn.dataset.originalText = btn.innerHTML;
  btn.innerHTML = `<span class="spinner"></span> ${loadingText}`;
}

/**
 * Reset a button from loading state.
 * @param {string} btnId - Button element ID
 */
function resetButton(btnId) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = false;
  if (btn.dataset.originalText) {
    btn.innerHTML = btn.dataset.originalText;
  }
}


// ─── API Helper ───────────────────────────────────────────────

/**
 * Make an API call to our Flask backend.
 * @param {string} url - API endpoint
 * @param {object} data - Request body (will be JSON encoded)
 * @returns {Promise<object>} - Response data
 */
async function apiCall(url, data = null, method = 'POST') {
  try {
    const options = {
      method,
      headers: { 'Content-Type': 'application/json' },
    };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    const json = await response.json();

    if (!response.ok) {
      throw new Error(json.error || `HTTP error ${response.status}`);
    }

    return json;

  } catch (error) {
    throw error;
  }
}


// ─── Responsive Helpers ───────────────────────────────────────

// Show mobile menu button on small screens
window.addEventListener('resize', () => {
  const mobileBtn = document.getElementById('mobileMenuBtn');
  if (mobileBtn) {
    mobileBtn.style.display = window.innerWidth <= 768 ? 'flex' : 'none';
  }
});

// Initial check
document.addEventListener('DOMContentLoaded', () => {
  const mobileBtn = document.getElementById('mobileMenuBtn');
  if (mobileBtn) {
    mobileBtn.style.display = window.innerWidth <= 768 ? 'flex' : 'none';
  }
});
