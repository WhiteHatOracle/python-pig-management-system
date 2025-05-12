// static/js/scripts.js
document.addEventListener('DOMContentLoaded', () => {
    // Add any interactivity here, e.g., for the info icons
    const infoIcons = document.querySelectorAll('.info-icon');
    infoIcons.forEach(icon => {
        icon.addEventListener('click', () => {
            alert('More info coming soon!');
        });
    });
});