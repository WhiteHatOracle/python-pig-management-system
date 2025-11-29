/**
 * Invoices List JavaScript
 */

let debounceTimer;

/**
 * Filter invoices based on search input
 */
function filterInvoices() {
  clearTimeout(debounceTimer);

  debounceTimer = setTimeout(function() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const table = document.getElementById('invoiceTable');
    const rows = table.querySelectorAll('tbody tr:not(.empty-row)');

    if (searchInput === '') {
      resetHighlights(rows);
      showAllRows(rows);
      return;
    }

    resetHighlights(rows);

    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      let match = false;

      cells.forEach(cell => {
        const text = cell.textContent.toLowerCase();
        if (text.includes(searchInput)) {
          match = true;
        }
      });

      if (match) {
        row.style.display = '';
        highlightRow(row);
      } else {
        row.style.display = 'none';
      }
    });
  }, 300);
}

/**
 * Highlight matching row
 */
function highlightRow(row) {
  row.style.backgroundColor = 'var(--hover-accent)';
}

/**
 * Reset all row highlights
 */
function resetHighlights(rows) {
  rows.forEach(row => {
    row.style.backgroundColor = '';
  });
}

/**
 * Show all rows
 */
function showAllRows(rows) {
  rows.forEach(row => {
    row.style.display = '';
  });
}

/**
 * Clear search input
 */
function clearSearch() {
  document.getElementById('searchInput').value = '';
  filterInvoices();
}

/**
 * Confirm invoice deletion
 */
function confirmDelete() {
  return confirm('Are you sure you want to delete this invoice? This action cannot be undone.');
}

/**
 * Fetch and update totals
 */
function fetchTotals() {
  fetch('/invoice_totals')
    .then(response => response.json())
    .then(data => {
      animateValue('totalPigs', data.total_pigs);
      animateValue('totalWeight', data.total_weight);
      animateValue('averageWeight', data.average_weight);
      animateValue('totalRevenue', data.total_revenue);
    })
    .catch(error => {
      console.error('Error fetching totals:', error);
      document.getElementById('totalPigs').textContent = '--';
      document.getElementById('totalWeight').textContent = '--';
      document.getElementById('averageWeight').textContent = '--';
      document.getElementById('totalRevenue').textContent = '--';
    });
}

/**
 * Animate value update
 */
function animateValue(elementId, newValue) {
  const element = document.getElementById(elementId);
  if (element) {
    element.style.transition = 'opacity 0.2s ease';
    element.style.opacity = '0.5';
    
    setTimeout(() => {
      element.textContent = newValue;
      element.style.opacity = '1';
    }, 200);
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
  fetchTotals();
  
  // Add keyboard shortcut for search (Ctrl/Cmd + K)
  document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      document.getElementById('searchInput').focus();
    }
  });
});

// Refresh totals periodically
setInterval(fetchTotals, 30000);