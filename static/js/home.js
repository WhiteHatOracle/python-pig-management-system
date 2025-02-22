// const sidebar = document.getElementById("sidebar");
// const toggleBtn = document.getElementById("toggle-btn");

// toggleBtn.addEventListener("click", function() {
//     sidebar.classList.toggle("close");
// });
const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggle-btn");

toggleBtn.addEventListener("click", function(event) {
    sidebar.classList.toggle("close");
    event.stopPropagation(); // Prevents unintended clicks elsewhere
});


// dark theme
document.addEventListener("DOMContentLoaded", function () {
const toggleBtn = document.getElementById("darkModeToggle");
const body = document.body;
const modeText = document.querySelector(".mode-text");

// Check Local Storage for Dark Mode Preference
if (localStorage.getItem("dark-mode") === "enabled") {
    enableDarkMode();
}

toggleBtn.addEventListener("click", function (e) {
    e.preventDefault(); // Prevent link navigation
    if (body.classList.contains("dark-mode")) {
        disableDarkMode();
    } else {
        enableDarkMode();
    }
});

function enableDarkMode() {
    body.classList.add("dark-mode");
    body.classList.remove("light-mode");
    localStorage.setItem("dark-mode", "enabled");
    modeText.textContent = "Light Mode";
}

function disableDarkMode() {
    body.classList.remove("dark-mode");
    body.classList.add("light-mode");
    localStorage.setItem("dark-mode", "disabled");
    modeText.textContent = "Dark Mode";
}
});