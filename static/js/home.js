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


document.addEventListener("DOMContentLoaded", () => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const isoToday = today.toISOString().split("T")[0];

  function applyDateRestrictions(input) {
    input.max = isoToday;
    input.addEventListener("change", () => {
      const selectedDate = new Date(input.value);
      if (isNaN(selectedDate)) return;
      selectedDate.setHours(0, 0, 0, 0);
      if (selectedDate > today) {
        alert("Future dates are not allowed.");
        input.value = "";
      }
    });
  }

  // Apply to already-existing date inputs
  document.querySelectorAll('input[type="date"]').forEach(applyDateRestrictions);

  // Watch for dynamically added date inputs
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) {
          if (node.matches('input[type="date"]')) {
            applyDateRestrictions(node);
          }
          // In case the new node contains date inputs inside it
          node.querySelectorAll?.('input[type="date"]').forEach(applyDateRestrictions);
        }
      });
    });
  });

  observer.observe(document.body, { childList: true, subtree: true });
});

document.addEventListener("DOMContentLoaded", function () {
  // Disappearing flash messages
  setTimeout(function() {
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(msg => {
      msg.style.transition = 'opacity 0.5s ease';
      msg.style.opacity = '0';
      setTimeout(() => msg.remove(), 500); // Fully remove after fade-out
    });
  }, 5000); // 5 seconds
});
