/**
 * Confirm deletion of litter record
 */
function confirmDelete() {
  return confirm('Are you sure you want to delete this litter record? This action cannot be undone.');
}

/**
 * Navigate back to service records
 */
function goBackToServiceRecords() {
  const sowId = window.sowId;
  if (sowId) {
    window.location.href = `/sows/${sowId}`;
  } else {
    window.history.back();
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
        this.click();
      }
    });
  }

  // Auto-calculate stillborn based on total and alive
  const totalBornInput = document.querySelector('input[name="totalBorn"]');
  const bornAliveInput = document.querySelector('input[name="bornAlive"]');
  const stillBornInput = document.querySelector('input[name="stillBorn"]');

  if (totalBornInput && bornAliveInput && stillBornInput) {
    const calculateStillborn = () => {
      const total = parseInt(totalBornInput.value) || 0;
      const alive = parseInt(bornAliveInput.value) || 0;
      if (total > 0 && alive >= 0 && total >= alive) {
        stillBornInput.value = total - alive;
      }
    };

    totalBornInput.addEventListener('input', calculateStillborn);
    bornAliveInput.addEventListener('input', calculateStillborn);
  }

  // Add visual feedback for form submission
  const form = document.querySelector('.litter-form');
  if (form) {
    form.addEventListener('submit', function(e) {
      // Validate that bornAlive <= totalBorn
      const total = parseInt(totalBornInput?.value) || 0;
      const alive = parseInt(bornAliveInput?.value) || 0;
      
      if (alive > total) {
        e.preventDefault();
        alert('Born Alive cannot be greater than Total Born');
        bornAliveInput.focus();
        return;
      }

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
  const tableRows = document.querySelectorAll('.litter-table tbody tr:not(.empty-row)');
  tableRows.forEach(row => {
    row.addEventListener('touchstart', function() {
      this.style.filter = 'brightness(0.95)';
    }, { passive: true });
    
    row.addEventListener('touchend', function() {
      this.style.filter = '';
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

  // Add stage indicator tooltip on hover (desktop)
  const stageRows = document.querySelectorAll('.stage-row');
  stageRows.forEach(row => {
    const stage = row.classList.contains('stage-pre-weaning') ? 'Pre-weaning' :
                  row.classList.contains('stage-weaner') ? 'Weaner' :
                  row.classList.contains('stage-grower') ? 'Grower' :
                  row.classList.contains('stage-finisher') ? 'Finisher' : '';
    
    if (stage) {
      row.setAttribute('title', `Stage: ${stage}`);
    }
  });
});

/**
 * Format weight input to ensure consistent format
 */
function formatWeights() {
  const weightsInput = document.querySelector('input[name="weights"], textarea[name="weights"]');
  if (weightsInput) {
    weightsInput.addEventListener('blur', function() {
      // Clean up the weights input (remove extra spaces, ensure comma separation)
      let value = this.value;
      value = value.replace(/\s+/g, ' ').trim();
      value = value.replace(/,\s*/g, ', ');
      this.value = value;
    });
  }
}

// Initialize weight formatting
document.addEventListener('DOMContentLoaded', formatWeights);