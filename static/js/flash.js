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
        }, 2000); // Wait for the transition to complete (2 second here)
    });
    }, 5000); // 5000 milliseconds = 5 seconds delay
}
});
