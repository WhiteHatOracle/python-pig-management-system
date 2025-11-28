/**
 * Confirm deletion of service record
 */
function confirmDelete() {
  return confirm('Are you sure you want to delete this service record? This action cannot be undone.');
}

/**
 * Navigate back to sow manager
 */
function goBack() {
  // Check if there's a previous page in history
  if (document.referrer && document.referrer.includes(window.location.host)) {
    window.history.back();
  } else {
    window.location.href = "/sow-manager";
  }
}

/**
 * Initialize page functionality
 */
document.addEventListener("DOMContentLoaded", function() {
  // Add keyboard support for back button
  const backBtn = document.querySelector('.back-btn');
  if (backBtn) {
    backBtn.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        goBack();
      }
    });
  }

  // Add visual feedback for form submission
  const form = document.querySelector('.service-form');
  if (form) {
    form.addEventListener('submit', function() {
      const submitBtn = form.querySelector('.btn-primary');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
          <svg class="spinner" xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 0 24 24" width="20px" fill="currentColor">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4" stroke-linecap="round">
              <animateTransform attributeName="transform" type="rotate" dur="1s" from="0 12 12" to="360 12 12" repeatCount="indefinite"/>
            </circle>
          </svg>
          <span>Adding...</span>
        `;
      }
    });
  }

  // Highlight row on hover for better UX (touch devices)
  const tableRows = document.querySelectorAll('.service-table tbody tr:not(.empty-row)');
  tableRows.forEach(row => {
    row.addEventListener('touchstart', function() {
      this.style.backgroundColor = 'var(--bg-lightest)';
    }, { passive: true });
    
    row.addEventListener('touchend', function() {
      this.style.backgroundColor = '';
    }, { passive: true });
  });

  // Add animation to flash messages
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach((flash, index) => {
    flash.style.opacity = '0';
    flash.style.transform = 'translateY(-10px)';
    flash.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    
    setTimeout(() => {
      flash.style.opacity = '1';
      flash.style.transform = 'translateY(0)';
    }, index * 100);

    // Auto-hide success messages after 5 seconds
    if (flash.classList.contains('success')) {
      setTimeout(() => {
        flash.style.opacity = '0';
        flash.style.transform = 'translateY(-10px)';
        setTimeout(() => flash.remove(), 300);
      }, 5000);
    }
  });
});