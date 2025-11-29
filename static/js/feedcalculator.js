/**
 * Feed Calculator JavaScript
 */

document.addEventListener("DOMContentLoaded", function() {
  // Form validation
  const form = document.getElementById('feedForm');
  
  if (form) {
    // Real-time validation
    const inputs = form.querySelectorAll('.form-input');
    
    inputs.forEach(input => {
      input.addEventListener('input', function() {
        validateField(this);
      });

      input.addEventListener('blur', function() {
        validateField(this);
      });
    });

    // Form submission
    form.addEventListener('submit', function(e) {
      let isValid = true;
      
      inputs.forEach(input => {
        if (!validateField(input)) {
          isValid = false;
        }
      });

      if (!isValid) {
        e.preventDefault();
        // Focus first invalid field
        const firstInvalid = form.querySelector('.form-input.error');
        if (firstInvalid) {
          firstInvalid.focus();
        }
        return;
      }

      // Show loading state
      const submitBtn = form.querySelector('.btn-calculate');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
          <svg class="spinner" xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 0 24 24" width="20px" fill="currentColor">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4" stroke-linecap="round">
              <animateTransform attributeName="transform" type="rotate" dur="1s" from="0 12 12" to="360 12 12" repeatCount="indefinite"/>
            </circle>
          </svg>
          <span>Calculating...</span>
        `;
      }
    });
  }

  /**
   * Validate individual field
   */
  function validateField(input) {
    const value = input.value.trim();
    const type = input.type;
    
    // Remove existing error states
    input.classList.remove('error', 'success');
    
    // Check required (if has value placeholder, it's expected to have value)
    if (type === 'number' && value === '') {
      return true; // Allow empty for optional fields
    }

    if (type === 'number') {
      const numValue = parseFloat(value);
      if (isNaN(numValue) || numValue < 0) {
        input.classList.add('error');
        return false;
      }
    }

    if (value) {
      input.classList.add('success');
    }

    return true;
  }

  // Add input formatting for number fields
  const numberInputs = document.querySelectorAll('input[type="number"]');
  numberInputs.forEach(input => {
    input.addEventListener('keydown', function(e) {
      // Allow: backspace, delete, tab, escape, enter, decimal point
      if ([46, 8, 9, 27, 13, 110, 190].indexOf(e.keyCode) !== -1 ||
          // Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
          (e.keyCode === 65 && e.ctrlKey === true) ||
          (e.keyCode === 67 && e.ctrlKey === true) ||
          (e.keyCode === 86 && e.ctrlKey === true) ||
          (e.keyCode === 88 && e.ctrlKey === true) ||
          // Allow: home, end, left, right
          (e.keyCode >= 35 && e.keyCode <= 39)) {
        return;
      }
      // Stop if not a number
      if ((e.shiftKey || (e.keyCode < 48 || e.keyCode > 57)) && (e.keyCode < 96 || e.keyCode > 105)) {
        e.preventDefault();
      }
    });
  });
});

/**
 * Clear form function
 */
function clearForm() {
  const form = document.getElementById('feedForm');
  if (form) {
    // Reset all inputs
    const inputs = form.querySelectorAll('.form-input');
    inputs.forEach(input => {
      input.value = '';
      input.classList.remove('error', 'success');
    });

    // Focus first input
    const firstInput = form.querySelector('.form-input');
    if (firstInput) {
      firstInput.focus();
    }

    // Remove scroll parameter from URL
    const url = new URL(window.location);
    url.searchParams.delete('scroll');
    window.history.replaceState({}, '', url);
  }
}

/**
 * Print results function (optional enhancement)
 */
function printResults() {
  window.print();
}