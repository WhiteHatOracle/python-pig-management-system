// ============================================
// EXPENSES PAGE JAVASCRIPT
// ============================================

// Confirm Delete Dialog
function confirmDelete() {
    return confirm('Are you sure you want to delete this expense? This action cannot be undone.');
}

// Fetch Expense Totals
function fetchTotals() {
    fetch('/expense_totals')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            const totalExpense = document.getElementById('totalExpense');
            const totalExpenseHeader = document.getElementById('totalExpenseHeader');
            
            if (totalExpense) {
                totalExpense.innerText = data.total_expenses || 'K0.00';
            }
            if (totalExpenseHeader) {
                totalExpenseHeader.innerText = data.total_expenses || 'K0.00';
            }
        })
        .catch(error => {
            console.error('Error fetching totals:', error);
            const totalExpense = document.getElementById('totalExpense');
            const totalExpenseHeader = document.getElementById('totalExpenseHeader');
            
            if (totalExpense) totalExpense.innerText = 'Error loading';
            if (totalExpenseHeader) totalExpenseHeader.innerText = 'Error';
        });
}

// Format and validate amount input
function handleAmountInput(event) {
    const amountInput = document.querySelector('input[name="amount"]');
    if (!amountInput) return;
    
    let value = amountInput.value.trim().toLowerCase();

    // Remove currency symbols and letters like "k", "$"
    value = value.replace(/[^0-9.,]/g, '');

    // Count commas and dots
    const commaCount = (value.match(/,/g) || []).length;
    const dotCount = (value.match(/\./g) || []).length;

    // Case: comma as thousand separator, dot as decimal
    if (commaCount >= 1 && dotCount <= 1) {
        value = value.replace(/,/g, ''); // remove all commas
    }
    // Case: comma as decimal, dot as thousand separator (unlikely in your region)
    else if (commaCount === 1 && dotCount > 1) {
        value = value.replace(/\./g, '');
        value = value.replace(',', '.');
    }
    // Case: only comma used, assume it's decimal
    else if (commaCount === 1 && dotCount === 0) {
        value = value.replace(',', '.');
    }
    // Otherwise: remove all thousand separators (commas or dots)
    else {
        value = value.replace(/[,\.](?=\d{3}(?:[^\d]|$))/g, '');
    }

    const amount = parseFloat(value);
    if (isNaN(amount)) {
        showNotification('Invalid amount entered. Please enter a valid number.', 'error');
        event.preventDefault();
        return false;
    }

    amountInput.value = amount.toFixed(2);
    return true;
}

// Show notification helper
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.js-notification');
    existingNotifications.forEach(n => n.remove());
    
    const notification = document.createElement('div');
    notification.className = `flash-message flash-${type} js-notification`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    const iconSVG = type === 'error' 
        ? '<svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor"><path d="m336-280 144-144 144 144 56-56-144-144 144-144-56-56-144 144-144-144-56 56 144 144-144 144 56 56Z"/></svg>'
        : '<svg xmlns="http://www.w3.org/2000/svg" height="20px" viewBox="0 -960 960 960" width="20px" fill="currentColor"><path d="M480-280q17 0 28.5-11.5T520-320v-160q0-17-11.5-28.5T480-520q-17 0-28.5 11.5T440-480v160q0 17 11.5 28.5T480-280Zm0-320q17 0 28.5-11.5T520-640q0-17-11.5-28.5T480-680q-17 0-28.5 11.5T440-640q0 17 11.5 28.5T480-600Z"/></svg>';
    
    notification.innerHTML = `
        <span class="flash-icon">${iconSVG}</span>
        <span class="flash-text">${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()">
            <svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 -960 960 960" width="18px" fill="currentColor"><path d="m256-200-56-56 224-224-224-224 56-56 224 224 224-224 56 56-224 224 224 224-56 56-224-224-224 224Z"/></svg>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

// Add row hover effect enhancement
function addRowInteractions() {
    const rows = document.querySelectorAll('.expense-table tbody tr:not(.empty-row)');
    
    rows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.002)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

// Auto-hide flash messages
function autoHideFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message:not(.js-notification)');
    
    flashMessages.forEach((message, index) => {
        setTimeout(() => {
            message.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => message.remove(), 300);
        }, 5000 + (index * 500));
    });
}

// Add CSS for slideOut animation
function addSlideOutAnimation() {
    if (!document.getElementById('slideOutStyle')) {
        const style = document.createElement('style');
        style.id = 'slideOutStyle';
        style.textContent = `
            @keyframes slideOut {
                from {
                    opacity: 1;
                    transform: translateY(0);
                }
                to {
                    opacity: 0;
                    transform: translateY(-10px);
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Add animation styles
    addSlideOutAnimation();
    
    // Fetch totals on page load
    fetchTotals();
    
    // Set up periodic refresh for totals (every 30 seconds)
    setInterval(fetchTotals, 30000);
    
    // Add form submit handler
    const expenseForm = document.querySelector('.expense-form');
    if (expenseForm) {
        expenseForm.addEventListener('submit', function(event) {
            if (!handleAmountInput(event)) {
                event.preventDefault();
            }
        });
    }
    
    // Add row interactions
    addRowInteractions();
    
    // Auto-hide flash messages
    autoHideFlashMessages();
    
    // Add keyboard navigation for action buttons
    const actionButtons = document.querySelectorAll('.action-btn');
    actionButtons.forEach(btn => {
        btn.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.click();
            }
        });
    });
});

// Handle window resize for responsive adjustments
let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        addRowInteractions();
    }, 250);
});