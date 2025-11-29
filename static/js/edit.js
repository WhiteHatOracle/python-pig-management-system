/**
 * Edit Form Page JavaScript
 */

document.addEventListener("DOMContentLoaded", function() {
  // Track form changes
  const form = document.querySelector('.edit-form');
  const originalValues = {};
  let hasChanges = false;

  if (form) {
    // Store original values
    const inputs = form.querySelectorAll('.form-input');
    inputs.forEach(input => {
      originalValues[input.name] = input.value;
      
      // Track changes
      input.addEventListener('input', function() {
        checkForChanges();
        validateField(this);
      });

      // Add focus effects
      input.addEventListener('focus', function() {
        this.closest('.form-group').classList.add('focused');
      });

      input.addEventListener('blur', function() {
        this.closest('.form-group').classList.remove('focused');
        validateField(this);
      });
    });
  }

  /**
   * Check if form has been modified
   */
  function checkForChanges() {
    const inputs = form.querySelectorAll('.form-input');
    hasChanges = false;

    inputs.forEach(input => {
      if (input.value !== originalValues[input.name]) {
        hasChanges = true;
      }
    });

    // Visual feedback for changes
    const submitBtn = form.querySelector('.btn-primary');
    if (submitBtn) {
      if (hasChanges) {
        submitBtn.classList.add('has-changes');
      } else {
        submitBtn.classList.remove('has-changes');
      }
    }
  }

  /**
   * Basic field validation
   */
  function validateField(input) {
    const value = input.value.trim();
    const formGroup = input.closest('.form-group');
    
    // Remove existing error states
    input.classList.remove('error', 'success');
    const existingError = formGroup.querySelector('.field-error');
    if (existingError) {
      existingError.remove();
    }

    // Required field validation
    if (input.hasAttribute('required') && !value) {
      input.classList.add('error');
      showFieldError(formGroup, 'This field is required');
      return false;
    }

    // Sow ID validation (alphanumeric)
    if (input.name === 'sowID' && value) {
      if (!/^[a-zA-Z0-9-_]+$/.test(value)) {
        input.classList.add('error');
        showFieldError(formGroup, 'Only letters, numbers, hyphens, and underscores allowed');
        return false;
      }
    }

    if (value) {
      input.classList.add('success');
    }

    return true;
  }

  /**
   * Show field error message
   */
  function showFieldError(formGroup, message) {
    const error = document.createElement('span');
    error.className = 'field-error';
    error.textContent = message;
    formGroup.appendChild(error);
  }

  /**
   * Form submission handler
   */
  if (form) {
    form.addEventListener('submit', function(e) {
      // Validate all fields
      let isValid = true;
      const inputs = form.querySelectorAll('.form-input');
      
      inputs.forEach(input => {
        if (!validateField(input)) {
          isValid = false;
        }
      });

      if (!isValid) {
        e.preventDefault();
        // Focus first error field
        const firstError = form.querySelector('.form-input.error');
        if (firstError) {
          firstError.focus();
        }
        return;
      }

      // Show loading state
      const submitBtn = form.querySelector('.btn-primary');
      if (submitBtn) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
          <svg class="spinner" xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 0 24 24" width="18px" fill="currentColor">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="31.4" stroke-linecap="round">
              <animateTransform attributeName="transform" type="rotate" dur="1s" from="0 12 12" to="360 12 12" repeatCount="indefinite"/>
            </circle>
          </svg>
          <span>Saving...</span>
        `;
      }
    });
  }

  /**
   * Warn about unsaved changes
   */
  window.addEventListener('beforeunload', function(e) {
    if (hasChanges) {
      e.preventDefault();
      e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
  });

  /**
   * Cancel button confirmation if changes exist
   */
  const cancelBtn = document.querySelector('.btn-secondary');
  if (cancelBtn) {
    cancelBtn.addEventListener('click', function(e) {
      if (hasChanges) {
        const confirmed = confirm('You have unsaved changes. Are you sure you want to cancel?');
        if (!confirmed) {
          e.preventDefault();
        } else {
          // Disable the beforeunload warning
          hasChanges = false;
        }
      }
    });
  }

  /**
   * Keyboard shortcuts
   */
  document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      const submitBtn = form?.querySelector('.btn-primary');
      if (submitBtn && !submitBtn.disabled) {
        form.requestSubmit();
      }
    }

    // Escape to cancel
    if (e.key === 'Escape') {
      const cancelBtn = document.querySelector('.btn-secondary');
      if (cancelBtn) {
        cancelBtn.click();
      }
    }
  });

  /**
   * Flash message animations
   */
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

  /**
   * Back button keyboard accessibility
   */
  const backBtn = document.querySelector('.back-btn');
  if (backBtn) {
    backBtn.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (hasChanges) {
          const confirmed = confirm('You have unsaved changes. Are you sure you want to go back?');
          if (confirmed) {
            hasChanges = false;
            this.click();
          }
        } else {
          this.click();
        }
      }
    });

    // Also handle click with unsaved changes
    backBtn.addEventListener('click', function(e) {
      if (hasChanges) {
        e.preventDefault();
        const confirmed = confirm('You have unsaved changes. Are you sure you want to go back?');
        if (confirmed) {
          hasChanges = false;
          window.location.href = this.href;
        }
      }
    });
  }
});