// ============================================
// SETTINGS PAGE JAVASCRIPT
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initThemeToggle();
    autoHideFlashMessages();
});

// Theme Toggle Functionality
function initThemeToggle() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const themeCheckbox = document.getElementById('theme-toggle-checkbox');
    
    if (!darkModeToggle || !themeCheckbox) return;
    
    // Check saved preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial state
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-mode');
        themeCheckbox.checked = true;
    }
    
    // Handle toggle click (on the entire item)
    darkModeToggle.addEventListener('click', function(e) {
        // Prevent double triggering if clicking directly on checkbox
        if (e.target === themeCheckbox || e.target.closest('.toggle-label')) {
            return;
        }
        themeCheckbox.checked = !themeCheckbox.checked;
        toggleTheme();
    });
    
    // Handle checkbox change
    themeCheckbox.addEventListener('change', function() {
        toggleTheme();
    });
}

function toggleTheme() {
    const themeCheckbox = document.getElementById('theme-toggle-checkbox');
    const isDark = themeCheckbox.checked;
    
    if (isDark) {
        document.body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
        showNotification('Dark mode enabled', 'success');
    } else {
        document.body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
        showNotification('Light mode enabled', 'success');
    }
}

// Show notification helper
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.js-notification');
    existingNotifications.forEach(n => n.remove());
    
    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type} js-notification`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 300px;
        animation: slideIn 0.3s ease-out;
    `;
    
    const iconSVG = type === 'success' 
        ? '<svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor"><path d="m424-296 282-282-56-56-226 226-114-114-56 56 170 170Z"/></svg>'
        : '<svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor"><path d="M480-280q17 0 28.5-11.5T520-320v-160q0-17-11.5-28.5T480-520q-17 0-28.5 11.5T440-480v160q0 17 11.5 28.5T480-280Z"/></svg>';
    
    notification.innerHTML = `
        <span class="flash-icon">${iconSVG}</span>
        <span class="flash-text">${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()">
            <svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 -960 960 960" width="18px" fill="currentColor"><path d="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z"/></svg>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 2 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => notification.remove(), 300);
        }
    }, 2000);
}

// Auto-hide flash messages
function autoHideFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message:not(.js-notification)');
    
    flashMessages.forEach((message, index) => {
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => message.remove(), 300);
        }, 5000 + (index * 500));
    });
}

// Add slideOut animation if not present
if (!document.getElementById('slideOutStyle')) {
    const style = document.createElement('style');
    style.id = 'slideOutStyle';
    style.textContent = `
        @keyframes slideOut {
            from {
                opacity: 1;
                transform: translateY(0);
            }
            to {
                opacity: 0;
                transform: translateY(-10px);
            }
        }
    `;
    document.head.appendChild(style);
}

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
    const savedTheme = localStorage.getItem('theme');
    // Only auto-switch if user hasn't set a preference
    if (!savedTheme) {
        const themeCheckbox = document.getElementById('theme-toggle-checkbox');
        if (themeCheckbox) {
            themeCheckbox.checked = e.matches;
            if (e.matches) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
        }
    }
});