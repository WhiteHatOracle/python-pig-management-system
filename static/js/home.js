const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggle-btn");

// Define the breakpoint for "small screens"
const smallScreenQuery = window.matchMedia("(max-width: 768px)");

// Function to apply sidebar state
function applySidebarState() {
    const isSmallScreen = smallScreenQuery.matches;

    if (isSmallScreen) {
        sidebar.classList.remove("close");
        return; // Always open on small screens
    }

    const isClosed = localStorage.getItem("sidebarClosed") === "true";
    sidebar.classList.toggle("close", isClosed);
}

// Run on initial load
document.addEventListener("DOMContentLoaded", applySidebarState);

// Also update state when screen is resized across the breakpoint
smallScreenQuery.addEventListener("change", applySidebarState);

// Toggle button logic
toggleBtn.addEventListener("click", function(event) {
    if (smallScreenQuery.matches) return; // Disable toggle on small screens

    sidebar.classList.toggle("close");
    const isClosed = sidebar.classList.contains("close");
    localStorage.setItem("sidebarClosed", isClosed);

    event.stopPropagation();
});


// Dark mode toggle
console.log("dark mode script loaded");
const toggleButton = document.getElementById('dark-mode-toggle');
const body = document.body;

// Check for saved dark mode preference in localStorage
const darkMode = localStorage.getItem('dark-mode');

if (darkMode === 'enabled') {
  body.classList.add('dark-mode');
}

// Toggle dark mode on button click
toggleButton.onclick = function () {
  body.classList.toggle('dark-mode');

  if (body.classList.contains('dark-mode')) {
    localStorage.setItem('dark-mode', 'enabled');
  } else {
    localStorage.setItem('dark-mode', 'disabled');
  }
};
