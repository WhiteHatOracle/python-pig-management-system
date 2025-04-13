//side bar toggle
const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggle-btn");

toggleBtn.addEventListener("click", function(event) {
    sidebar.classList.toggle("close");
    event.stopPropagation(); // Prevents unintended clicks elsewhere
});

//  //dark mode toggle
// console.log("dark mode script loaded");
// const toggleButton = document.getElementById('dark-mode-toggle');
// const body = document.body;

// //check for saved darkmode in local storage
// const darkMode = localStorage.getItem('dark-mode');

// if (darkMode === 'enabled') {
//     body.classList.add('dark-mode');
// }

// toggleButton.onclick = function() {
//   body.classList.toggle('dark-mode');

//   localStorage.setItem('dark-mode', body.classList.contains('dark-mode'));
// }

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
