// ============================================
// AUTH PAGES JAVASCRIPT
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initThemeToggle();
    initPasswordToggle();
    initPasswordStrength();
    autoHideFlashMessages();
});

// ============================================
// THEME TOGGLE
// ============================================

function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    // Check saved preference
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.body.classList.add('dark-mode');
    }
    
    themeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

// ============================================
// PASSWORD VISIBILITY TOGGLE
// ============================================

function initPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.toggle-password');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const wrapper = this.closest('.input-wrapper');
            const input = wrapper.querySelector('input');
            const eyeIcon = this.querySelector('.eye-icon');
            const eyeOffIcon = this.querySelector('.eye-off-icon');
            
            if (input.type === 'password') {
                input.type = 'text';
                eyeIcon.style.display = 'none';
                eyeOffIcon.style.display = 'block';
            } else {
                input.type = 'password';
                eyeIcon.style.display = 'block';
                eyeOffIcon.style.display = 'none';
            }
        });
    });
}

// ============================================
// PASSWORD STRENGTH INDICATOR
// ============================================

function initPasswordStrength() {
    const passwordInput = document.getElementById('password');
    const strengthFill = document.getElementById('strength-fill');
    const strengthText = document.getElementById('strength-text');
    
    if (!passwordInput || !strengthFill || !strengthText) return;
    
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        const strength = checkPasswordStrength(password);
        
        strengthFill.style.width = strength.percent + '%';
        strengthFill.className = 'strength-fill ' + strength.class;
        strengthText.textContent = strength.text;
        strengthText.className = 'strength-text ' + strength.class;
    });
}

function checkPasswordStrength(password) {
    let score = 0;
    
    if (password.length === 0) {
        return { percent: 0, class: '', text: 'Password strength' };
    }
    
    // Length checks
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Character type checks
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;
    
    if (score <= 2) {
        return { percent: 25, class: 'weak', text: 'Weak' };
    } else if (score <= 4) {
        return { percent: 50, class: 'fair', text: 'Fair' };
    } else if (score <= 5) {
        return { percent: 75, class: 'good', text: 'Good' };
    } else {
        return { percent: 100, class: 'strong', text: 'Strong' };
    }
}

// ============================================
// FLASH MESSAGES
// ============================================

function autoHideFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach((message, index) => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            message.style.transition = 'all 0.3s ease';
            setTimeout(() => message.remove(), 300);
        }, 5000 + (index * 500));
    });
}

// ============================================
// FORM VALIDATION FEEDBACK
// ============================================

// Add real-time validation feedback
const formInputs = document.querySelectorAll('.auth-form input');
formInputs.forEach(input => {
    input.addEventListener('blur', function() {
        if (this.value.trim() === '' && this.hasAttribute('required')) {
            this.style.borderColor = '#dc3545';
        }
    });
    
    input.addEventListener('focus', function() {
        this.style.borderColor = '';
    });
});