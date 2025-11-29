// ============================================
// SETTINGS PAGE JAVASCRIPT
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    autoHideFlashMessages();
});

// ============================================
// FLASH MESSAGES
// ============================================

function autoHideFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach((message, index) => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            setTimeout(() => message.remove(), 300);
        }, 5000 + (index * 500));
    });
}