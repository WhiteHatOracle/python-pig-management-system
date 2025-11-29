// ============================================
// HOME.JS - GLOBAL SCRIPTS
// ============================================

const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggle-btn");
const body = document.body;

// Define the breakpoint for "small screens"
const smallScreenQuery = window.matchMedia("(max-width: 900px)");

// ============================================
// SIDEBAR FUNCTIONALITY
// ============================================

function applySidebarState() {
    if (!sidebar) return;
    
    const isSmallScreen = smallScreenQuery.matches;

    if (isSmallScreen) {
        sidebar.classList.remove("close");
        body.classList.remove("sidebar-collapsed");
        return;
    }

    const isClosed = localStorage.getItem("sidebarClosed") === "true";
    sidebar.classList.toggle("close", isClosed);
    body.classList.toggle("sidebar-collapsed", isClosed);
}

// Run on initial load
document.addEventListener("DOMContentLoaded", function() {
    applySidebarState();
    setActiveNavLink();
    initGlobalDarkMode();
    initThemeToggle(); // Set up the settings page toggle
});

// Update state when screen is resized across the breakpoint
smallScreenQuery.addEventListener("change", applySidebarState);

// Toggle button logic
if (toggleBtn) {
    toggleBtn.addEventListener("click", function(event) {
        if (smallScreenQuery.matches) return;

        sidebar.classList.toggle("close");
        body.classList.toggle("sidebar-collapsed");
        
        const isClosed = sidebar.classList.contains("close");
        localStorage.setItem("sidebarClosed", isClosed);

        event.stopPropagation();
    });
}

// ============================================
// NAVIGATION ACTIVE STATE
// ============================================

function setActiveNavLink() {
    const currentPath = window.location.pathname;
    
    // Desktop nav links
    const desktopLinks = document.querySelectorAll('#sidebar .nav-link');
    desktopLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href.includes('dashboard'))) {
            link.classList.add('active');
        }
    });
    
    // Mobile nav links
    const mobileLinks = document.querySelectorAll('.mobile-nav-item');
    mobileLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href.includes('dashboard'))) {
            link.classList.add('active');
        }
    });
}

// ============================================
// GLOBAL DARK MODE
// ============================================

const THEME_KEY = 'theme';

function initGlobalDarkMode() {
    // One-time migration from old key
    const oldDarkMode = localStorage.getItem('dark-mode');
    if (oldDarkMode !== null) {
        localStorage.setItem(THEME_KEY, oldDarkMode === 'enabled' ? 'dark' : 'light');
        localStorage.removeItem('dark-mode');
    }
    
    // Check saved preference or system preference
    const savedTheme = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Apply saved theme or system preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        body.classList.add('dark-mode');
    } else {
        body.classList.remove('dark-mode');
    }
}

// ============================================
// THEME TOGGLE (Settings Page)
// ============================================

function initThemeToggle() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const themeCheckbox = document.getElementById('theme-toggle-checkbox');
    
    // Only run if we're on a page with the toggle
    if (!darkModeToggle || !themeCheckbox) return;
    
    // Sync checkbox with current state
    themeCheckbox.checked = body.classList.contains('dark-mode');
    
    // Handle click on the entire row (excluding toggle switch)
    darkModeToggle.addEventListener('click', function(e) {
        // If clicking on the toggle switch area, let the checkbox handle it
        if (e.target.closest('.toggle-switch')) {
            return;
        }
        // Otherwise, toggle the checkbox
        themeCheckbox.checked = !themeCheckbox.checked;
        applyTheme(themeCheckbox.checked);
    });
    
    // Handle checkbox change directly
    themeCheckbox.addEventListener('change', function() {
        applyTheme(this.checked);
    });
}

function applyTheme(isDark) {
    if (isDark) {
        body.classList.add('dark-mode');
        localStorage.setItem(THEME_KEY, 'dark');
    } else {
        body.classList.remove('dark-mode');
        localStorage.setItem(THEME_KEY, 'light');
    }
    
    // Show notification
    showThemeNotification(isDark ? 'Dark mode enabled' : 'Light mode enabled');
}

function syncThemeCheckbox() {
    const themeCheckbox = document.getElementById('theme-toggle-checkbox');
    if (themeCheckbox) {
        themeCheckbox.checked = body.classList.contains('dark-mode');
    }
}

// ============================================
// NOTIFICATIONS
// ============================================

function showThemeNotification(message) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.theme-notification');
    existingNotifications.forEach(n => n.remove());
    
    const notification = document.createElement('div');
    notification.className = 'theme-notification';
    notification.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor">
            <path d="m424-296 282-282-56-56-226 226-114-114-56 56 170 170Zm56 216q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Z"/>
        </svg>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Trigger animation
    requestAnimationFrame(() => {
        notification.classList.add('show');
    });
    
    // Remove after 2 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    const savedTheme = localStorage.getItem(THEME_KEY);
    if (!savedTheme) {
        if (e.matches) {
            body.classList.add('dark-mode');
        } else {
            body.classList.remove('dark-mode');
        }
        syncThemeCheckbox();
    }
});

// Make functions globally available
window.toggleDarkMode = function(showNotif = true) {
    const isDark = body.classList.toggle('dark-mode');
    localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light');
    syncThemeCheckbox();
    if (showNotif) showThemeNotification(isDark ? 'Dark mode enabled' : 'Light mode enabled');
    return isDark;
};
window.isDarkMode = () => body.classList.contains('dark-mode');
window.syncThemeCheckbox = syncThemeCheckbox;