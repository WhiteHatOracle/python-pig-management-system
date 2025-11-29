/**
 * Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
  // Handle iframe loading state
  const iframe = document.querySelector('.dashboard-iframe');
  
  if (iframe) {
    // Show loading state
    iframe.style.opacity = '0';
    iframe.style.transition = 'opacity 0.3s ease';

    iframe.addEventListener('load', function() {
      // Fade in when loaded
      iframe.style.opacity = '1';
      
      // Try to apply dark mode to iframe if needed
      applyDarkModeToIframe();
    });
  }

  // Listen for dark mode changes
  const darkModeObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      if (mutation.attributeName === 'class') {
        applyDarkModeToIframe();
      }
    });
  });

  darkModeObserver.observe(document.body, {
    attributes: true,
    attributeFilter: ['class']
  });
});

/**
 * Apply dark mode to iframe content
 */
function applyDarkModeToIframe() {
  const iframe = document.querySelector('.dashboard-iframe');
  const isDarkMode = document.body.classList.contains('dark-mode');

  if (iframe && iframe.contentDocument) {
    try {
      const iframeBody = iframe.contentDocument.body;
      if (iframeBody) {
        if (isDarkMode) {
          iframeBody.classList.add('dark-mode');
        } else {
          iframeBody.classList.remove('dark-mode');
        }
      }
    } catch (e) {
      // Cross-origin restriction, can't access iframe content
      console.log('Cannot access iframe content due to cross-origin policy');
    }
  }
}

/**
 * Refresh dashboard data (can be called manually)
 */
function refreshDashboard() {
  const iframe = document.querySelector('.dashboard-iframe');
  if (iframe) {
    iframe.contentWindow.location.reload();
  }
}

/**
 * Handle visibility change to pause/resume updates
 */
document.addEventListener('visibilitychange', function() {
  const iframe = document.querySelector('.dashboard-iframe');
  if (iframe && iframe.contentWindow) {
    // Could send message to iframe to pause/resume updates
    // This would require additional setup in the Dash app
  }
});