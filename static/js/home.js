// const toggleButton = document.getElementById('toggle-btn')
// const sidebar = document.getElementById('sidebar')

// function toggleSidebar(){
//   sidebar.classList.toggle('close')
//   toggleButton.classList.toggle('rotate')
// }

const toggleButton = document.getElementById('toggle-btn');
const sidebar = document.getElementById('sidebar');

// Load the saved state from local storage
document.addEventListener('DOMContentLoaded', () => {
  const isClosed = localStorage.getItem('sidebarClosed') === 'true';
  if (isClosed) {
    sidebar.classList.add('close');
    toggleButton.classList.add('rotate');
  }
});

// Function to toggle the sidebar and save the state
function toggleSidebar() {
  const isClosed = sidebar.classList.toggle('close');
  toggleButton.classList.toggle('rotate');
  
  // Save the current state to local storage
  localStorage.setItem('sidebarClosed', isClosed);
}
