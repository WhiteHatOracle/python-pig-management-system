// const toggleButton = document.getElementById('toggle-btn');
// const sidebar = document.getElementById('sidebar');

// function toggleSidebar() {
//   const isClosed = sidebar.classList.toggle('close');
//   toggleButton.classList.toggle('rotate');
// }

document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("sidebar");
    const hamburger = document.getElementById("hamburger");
    const closeBtn = document.getElementById("close-btn");
  
    hamburger.addEventListener("click", function () {
      sidebar.classList.add("active");
    });
  
    closeBtn.addEventListener("click", function () {
      sidebar.classList.remove("active");
    });
  });
  