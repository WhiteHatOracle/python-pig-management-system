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
