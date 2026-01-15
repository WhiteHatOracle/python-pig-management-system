// Auto-dismiss flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(function(message) {
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            dismissFlash(message);
        }, 5000);
    });
});

function dismissFlash(element) {
    element.classList.add('dismissing');
    setTimeout(function() {
        element.remove();
    }, 300); // Match animation duration
}

// Update close button to use smooth animation
document.addEventListener('click', function(e) {
    if (e.target.closest('.flash-close')) {
        e.preventDefault();
        const flashMessage = e.target.closest('.flash-message');
        dismissFlash(flashMessage);
    }
});