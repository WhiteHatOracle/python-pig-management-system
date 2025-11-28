const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggle-btn");
const body = document.body;

// Define the breakpoint for "small screens"
const smallScreenQuery = window.matchMedia("(max-width: 900px)");

// Function to apply sidebar state
function applySidebarState() {
    const isSmallScreen = smallScreenQuery.matches;

    if (isSmallScreen) {
        sidebar.classList.remove("close");
        body.classList.remove("sidebar-collapsed");
        return; // Always open on small screens (but hidden via CSS)
    }

    const isClosed = localStorage.getItem("sidebarClosed") === "true";
    sidebar.classList.toggle("close", isClosed);
    body.classList.toggle("sidebar-collapsed", isClosed);
}

// Run on initial load
document.addEventListener("DOMContentLoaded", function() {
    applySidebarState();
    setActiveNavLink();
});

// Also update state when screen is resized across the breakpoint
smallScreenQuery.addEventListener("change", applySidebarState);

// Toggle button logic
if (toggleBtn) {
    toggleBtn.addEventListener("click", function(event) {
        if (smallScreenQuery.matches) return; // Disable toggle on small screens

        sidebar.classList.toggle("close");
        body.classList.toggle("sidebar-collapsed");
        
        const isClosed = sidebar.classList.contains("close");
        localStorage.setItem("sidebarClosed", isClosed);

        event.stopPropagation();
    });
}

// Set active navigation link based on current URL
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

// Dark mode toggle
console.log("dark mode script loaded");
const toggleButton = document.getElementById('dark-mode-toggle');

// Check for saved dark mode preference in localStorage
const darkMode = localStorage.getItem('dark-mode');

if (darkMode === 'enabled') {
    body.classList.add('dark-mode');
}

// Toggle dark mode on button click
if (toggleButton) {
    toggleButton.onclick = function () {
        body.classList.toggle('dark-mode');

        if (body.classList.contains('dark-mode')) {
            localStorage.setItem('dark-mode', 'enabled');
        } else {
            localStorage.setItem('dark-mode', 'disabled');
        }
    };
}