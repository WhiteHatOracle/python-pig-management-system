// disappearing flask messages
document.addEventListener('DOMContentLoaded', function() {
const flashMessages = document.querySelectorAll('.flash'); // Select all elements with class 'alert'
if (flashMessages.length > 0) {
    setTimeout(function() {
    flashMessages.forEach(function(message) {
        message.style.transition = 'opacity 1s ease-out'; // Add a fade-out transition
        message.style.opacity = '0'; // Start fading out
        setTimeout(function() {
        message.remove(); // Remove the element after the fade-out
        }, 1000); // Wait for the transition to complete (1 second here)
    });
    }, 3000); // 3000 milliseconds = 3 seconds delay
}
});
