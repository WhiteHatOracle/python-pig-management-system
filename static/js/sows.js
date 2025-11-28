function confirmDelete() {
  return confirm('Are you sure you want to delete this sow? This action cannot be undone.');
}

document.addEventListener("DOMContentLoaded", function () {
  // Make table rows clickable (except action column)
  const tableRows = document.querySelectorAll('.sow-table tbody tr[data-href]');
  tableRows.forEach(row => {
    row.addEventListener('click', function(e) {
      // Don't navigate if clicking on actions column or buttons
      if (e.target.closest('.actions-column') || 
          e.target.closest('.action-btn') || 
          e.target.closest('.menu-btn') ||
          e.target.closest('.dropdown-menu')) {
        return;
      }
      window.location.href = this.dataset.href;
    });
  });

  // Select all three-dot buttons for dropdown menu
  const menuButtons = document.querySelectorAll(".menu-btn");

  menuButtons.forEach(button => {
    button.addEventListener("click", function (event) {
      event.stopPropagation();

      // Close any other open menus before opening a new one
      document.querySelectorAll(".dropdown-menu").forEach(menu => {
        if (menu !== button.nextElementSibling) {
          menu.classList.remove("show");
        }
      });

      // Toggle the dropdown menu for this specific button
      const dropdown = button.nextElementSibling;
      dropdown.classList.toggle("show");
    });
  });

  // Close the dropdown when clicking anywhere outside
  document.addEventListener("click", function (e) {
    if (!e.target.closest('.dropdown-menu') && !e.target.closest('.menu-btn')) {
      document.querySelectorAll(".dropdown-menu").forEach(menu => {
        menu.classList.remove("show");
      });
    }
  });
});

// Search functionality with debounce
let debounceTimer;

function filterInvoices() {
  clearTimeout(debounceTimer);

  debounceTimer = setTimeout(function () {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const table = document.getElementById('sowTable');
    const rows = table.getElementsByTagName('tr');

    if (searchInput === '') {
      resetHighlights();
      showAllRows(rows);
      return;
    }

    resetHighlights();

    for (let i = 1; i < rows.length; i++) {
      const cells = rows[i].getElementsByTagName('th');
      let match = false;

      for (let j = 0; j < cells.length; j++) {
        if (cells[j]) {
          const cellText = cells[j].textContent || cells[j].innerText;
          if (cellText.toLowerCase().indexOf(searchInput) > -1) {
            match = true;
            highlightRow(rows[i]);
          }
        }
      }

      rows[i].style.display = match ? '' : 'none';
    }
  }, 300);
}

function highlightRow(row) {
  row.style.backgroundColor = 'var(--hover-accent)';
  row.style.fontWeight = '500';
}

function resetHighlights() {
  const table = document.getElementById('sowTable');
  const rows = table.getElementsByTagName('tr');
  for (let i = 1; i < rows.length; i++) {
    rows[i].style.backgroundColor = '';
    rows[i].style.fontWeight = '';
  }
}

function showAllRows(rows) {
  for (let i = 1; i < rows.length; i++) {
    rows[i].style.display = '';
  }
}

function clearSearch() {
  document.getElementById("searchInput").value = "";
  filterInvoices();
}