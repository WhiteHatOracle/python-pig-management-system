/**
 * =============================================
 * NOTIFICATIONS.JS - PigFarm Manager (FIXED)
 * Handles all notification-related functionality
 * for both list.html and settings.html pages
 * =============================================
 */

(function() {
    'use strict';

    // ==========================================
    // CONFIGURATION & API ENDPOINTS
    // ==========================================
    const API = {
        markRead: (id) => `/notifications/api/mark-read/${id}`,
        dismiss: (id) => `/notifications/api/dismiss/${id}`,
        markAllRead: '/notifications/api/mark-all-read',
        refresh: '/notifications/api/refresh',
        updateSettings: '/notifications/api/update-settings'
    };

    // ==========================================
    // UTILITY FUNCTIONS
    // ==========================================
    
    /**
     * Get CSRF token from meta tag or cookie (for Flask-WTF)
     */
    function getCSRFToken() {
        // Try meta tag first
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }
        
        // Try cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') {
                return value;
            }
        }
        
        return null;
    }

    /**
     * Make an API request with error handling
     */
    async function apiRequest(url, method = 'POST', data = null) {
        try {
            const headers = { 
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'  // For Flask to recognize AJAX
            };
            
            // Add CSRF token if available
            const csrfToken = getCSRFToken();
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            const options = {
                method,
                headers,
                credentials: 'same-origin'  // Include cookies
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            const response = await fetch(url, options);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error Response:', errorText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    /**
     * Show a toast notification
     */
    function showToast(message, type = 'success') {
        // Check if toast container exists, if not create it
        let toastContainer = document.getElementById('toastContainer');
        
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.style.cssText = `
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-size: 0.9rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        `;

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };

        toast.innerHTML = `
            <i class="fas ${icons[type] || icons.info}"></i>
            <span>${message}</span>
        `;

        toastContainer.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Add CSS animations for toasts
     */
    function addToastStyles() {
        if (document.getElementById('toastStyles')) return;
        
        const style = document.createElement('style');
        style.id = 'toastStyles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }

    // ==========================================
    // DROPDOWN FUNCTIONALITY
    // ==========================================
    
    /**
     * Toggle dropdown menu visibility
     */
    window.toggleDropdown = function(btn) {
        // Prevent event bubbling
        event.stopPropagation();
        
        const menu = btn.nextElementSibling;
        if (!menu) {
            console.error('Dropdown menu not found');
            return;
        }
        
        const allMenus = document.querySelectorAll('.dropdown-menu.show');
        
        // Close all other dropdowns
        allMenus.forEach(m => {
            if (m !== menu) m.classList.remove('show');
        });
        
        // Toggle current dropdown
        menu.classList.toggle('show');
    };

    /**
     * Close all dropdowns when clicking outside
     */
    function closeDropdownsOnOutsideClick(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu.show').forEach(m => {
                m.classList.remove('show');
            });
        }
    }

    // ==========================================
    // NOTIFICATION LIST FUNCTIONALITY
    // ==========================================
    
    /**
     * Initialize filter tabs
     */
    function initFilterTabs() {
        const filterButtons = document.querySelectorAll('[data-filter]');
        
        if (filterButtons.length === 0) {
            console.log('No filter buttons found');
            return;
        }
        
        filterButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const filter = this.dataset.filter;
                
                // Update active state
                filterButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // Filter notifications
                filterNotifications(filter);
            });
        });
        
        console.log('Filter tabs initialized');
    }

    /**
     * Filter notifications based on selected filter
     */
    function filterNotifications(filter) {
        const items = document.querySelectorAll('.notification-item');
        let visibleCount = 0;
        
        console.log('Filtering by:', filter, 'Total items:', items.length);
        
        items.forEach(item => {
            let show = false;
            
            // Get data attributes - handle both string "true"/"false" and actual booleans
            const isRead = item.dataset.read === 'true' || item.dataset.read === 'True';
            const isOverdue = item.dataset.overdue === 'true' || item.dataset.overdue === 'True';
            const itemType = item.dataset.type;
            
            switch(filter) {
                case 'all':
                    show = true;
                    break;
                case 'unread':
                    show = !isRead;
                    break;
                case 'overdue':
                    show = isOverdue;
                    break;
                default:
                    // Filter by notification type (e.g., farrow_due, vaccination_due)
                    show = itemType === filter;
            }
            
            item.style.display = show ? 'flex' : 'none';
            if (show) visibleCount++;
        });

        console.log('Visible items after filter:', visibleCount);
        
        // Check if any items are visible
        checkEmptyState(visibleCount);
    }

    /**
     * Check if filtered list is empty and show appropriate message
     */
    function checkEmptyState(visibleCount) {
        const list = document.getElementById('notificationsList');
        let emptyMessage = document.getElementById('filterEmptyMessage');
        
        if (visibleCount === 0 && list) {
            if (!emptyMessage) {
                emptyMessage = document.createElement('div');
                emptyMessage.id = 'filterEmptyMessage';
                emptyMessage.className = 'empty-state';
                emptyMessage.innerHTML = `
                    <i class="fas fa-filter"></i>
                    <h5>No notifications match this filter</h5>
                    <p>Try selecting a different filter.</p>
                `;
                emptyMessage.style.cssText = 'padding: 40px; text-align: center; color: #6b7280;';
                list.appendChild(emptyMessage);
            }
            emptyMessage.style.display = 'block';
        } else if (emptyMessage) {
            emptyMessage.style.display = 'none';
        }
    }

    /**
     * Mark a single notification as read
     */
    async function markAsRead(id, buttonElement) {
        console.log('Marking notification as read:', id);
        
        try {
            const data = await apiRequest(API.markRead(id));
            
            const item = document.querySelector(`.notification-item[data-id="${id}"]`);
            if (item) {
                item.classList.remove('unread');
                item.dataset.read = 'true';
                
                const title = item.querySelector('.notification-title');
                if (title) title.classList.remove('unread');
            }
            
            // Remove the "Mark as Read" button
            if (buttonElement) {
                buttonElement.remove();
            }
            
            // Update unread count
            if (data && typeof data.unread_count !== 'undefined') {
                updateUnreadCount(data.unread_count);
            } else {
                // Recalculate manually
                recalculateUnreadCount();
            }
            
            // Close dropdown
            document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
            
            showToast('Notification marked as read', 'success');
        } catch (error) {
            console.error('Failed to mark as read:', error);
            showToast('Failed to mark as read', 'error');
        }
    }

    /**
     * Dismiss a notification
     */
    async function dismissNotification(id) {
        console.log('Dismissing notification:', id);
        
        try {
            await apiRequest(API.dismiss(id));
            
            const item = document.querySelector(`.notification-item[data-id="${id}"]`);
            if (item) {
                // Animate out
                item.style.transition = 'opacity 0.3s, transform 0.3s';
                item.style.opacity = '0';
                item.style.transform = 'translateX(20px)';
                
                setTimeout(() => {
                    item.remove();
                    updateBadgeCounts();
                    
                    // Check if list is now empty
                    const remainingItems = document.querySelectorAll('.notification-item');
                    if (remainingItems.length === 0) {
                        showEmptyListState();
                    }
                }, 300);
            }
            
            showToast('Notification dismissed', 'success');
        } catch (error) {
            console.error('Failed to dismiss:', error);
            showToast('Failed to dismiss notification', 'error');
        }
    }

    /**
     * Show empty state when all notifications are dismissed
     */
    function showEmptyListState() {
        const list = document.getElementById('notificationsList');
        if (list) {
            list.innerHTML = `
                <div class="empty-state" style="padding: 60px 20px; text-align: center;">
                    <i class="fas fa-bell-slash" style="font-size: 3rem; color: #9ca3af; margin-bottom: 1rem;"></i>
                    <h5>No notifications</h5>
                    <p>You're all caught up! Check back later for updates.</p>
                    <button class="btn btn-primary" id="refreshEmpty">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
            `;
            
            // Re-attach refresh button listener
            const refreshEmptyBtn = document.getElementById('refreshEmpty');
            if (refreshEmptyBtn) {
                refreshEmptyBtn.addEventListener('click', refreshNotifications);
            }
        }
    }

    /**
     * Mark all notifications as read
     */
    async function markAllAsRead() {
        const btn = document.getElementById('markAllRead');
        if (!btn) return;

        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Processing...</span>';
        btn.disabled = true;

        try {
            await apiRequest(API.markAllRead);
            
            // Update all notification items
            document.querySelectorAll('.notification-item').forEach(item => {
                item.classList.remove('unread');
                item.dataset.read = 'true';
                
                const title = item.querySelector('.notification-title');
                if (title) title.classList.remove('unread');
                
                // Remove "Mark as Read" buttons
                const markReadBtn = item.querySelector('.mark-read-btn');
                if (markReadBtn) markReadBtn.remove();
            });
            
            updateUnreadCount(0);
            
            btn.innerHTML = '<i class="fas fa-check"></i> <span>Done!</span>';
            
            showToast('All notifications marked as read', 'success');
            
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                // Keep disabled since all are read now
            }, 2000);
        } catch (error) {
            console.error('Failed to mark all as read:', error);
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            showToast('Failed to mark all as read', 'error');
        }
    }

    /**
     * Refresh notifications (reload page)
     */
    async function refreshNotifications() {
        const btn = document.getElementById('refreshNotifications') || document.getElementById('refreshEmpty');
        const icon = btn?.querySelector('i');
        
        if (icon) {
            icon.classList.add('fa-spin');
        }
        
        if (btn) {
            btn.disabled = true;
        }

        try {
            // Try to call the refresh API first
            await apiRequest(API.refresh);
            location.reload();
        } catch (error) {
            // If API fails, just reload the page
            console.log('Refresh API failed, reloading page directly');
            location.reload();
        }
    }

    /**
     * Update the unread count display
     */
    function updateUnreadCount(count) {
        const countElement = document.getElementById('unreadCount');
        if (countElement) {
            countElement.textContent = count;
        }
        
        // Update filter badge
        const unreadBadge = document.querySelector('[data-filter="unread"] .badge');
        if (unreadBadge) {
            unreadBadge.textContent = count;
        }

        // Update mark all read button state
        const markAllBtn = document.getElementById('markAllRead');
        if (markAllBtn) {
            markAllBtn.disabled = count === 0;
        }
    }

    /**
     * Recalculate unread count from DOM
     */
    function recalculateUnreadCount() {
        const unreadItems = document.querySelectorAll('.notification-item[data-read="false"], .notification-item[data-read="False"]');
        updateUnreadCount(unreadItems.length);
    }

    /**
     * Update all badge counts after a notification is dismissed
     */
    function updateBadgeCounts() {
        const items = document.querySelectorAll('.notification-item');
        
        // Count totals
        let total = items.length;
        let unread = 0;
        let overdue = 0;
        
        items.forEach(item => {
            const isRead = item.dataset.read === 'true' || item.dataset.read === 'True';
            const isOverdue = item.dataset.overdue === 'true' || item.dataset.overdue === 'True';
            
            if (!isRead) unread++;
            if (isOverdue) overdue++;
        });
        
        // Update badges
        const allBadge = document.querySelector('[data-filter="all"] .badge');
        const unreadBadge = document.querySelector('[data-filter="unread"] .badge');
        const overdueBadge = document.querySelector('[data-filter="overdue"] .badge');
        
        if (allBadge) allBadge.textContent = total;
        if (unreadBadge) unreadBadge.textContent = unread;
        if (overdueBadge) overdueBadge.textContent = overdue;
        
        updateUnreadCount(unread);
    }

    /**
     * Initialize notification list event listeners
     */
    function initNotificationList() {
        console.log('Initializing notification list...');
        
        // Mark as read buttons (using event delegation for dynamic content)
        document.addEventListener('click', function(e) {
            const markReadBtn = e.target.closest('.mark-read-btn');
            if (markReadBtn) {
                e.preventDefault();
                e.stopPropagation();
                markAsRead(markReadBtn.dataset.id, markReadBtn);
            }
            
            const dismissBtn = e.target.closest('.dismiss-btn');
            if (dismissBtn) {
                e.preventDefault();
                e.stopPropagation();
                dismissNotification(dismissBtn.dataset.id);
            }
        });
        
        // Mark all as read button
        const markAllBtn = document.getElementById('markAllRead');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                markAllAsRead();
            });
            console.log('Mark all read button initialized');
        }
        
        // Refresh buttons
        const refreshBtn = document.getElementById('refreshNotifications');
        const refreshEmptyBtn = document.getElementById('refreshEmpty');
        
        if (refreshBtn) {
            refreshBtn.addEventListener('click', function(e) {
                e.preventDefault();
                refreshNotifications();
            });
            console.log('Refresh button initialized');
        }
        
        if (refreshEmptyBtn) {
            refreshEmptyBtn.addEventListener('click', function(e) {
                e.preventDefault();
                refreshNotifications();
            });
        }
        
        // Initialize filter tabs
        initFilterTabs();
        
        console.log('Notification list initialized successfully');
    }

    // ==========================================
    // NOTIFICATION SETTINGS FUNCTIONALITY
    // ==========================================
    
    /**
     * Initialize settings toggle switches
     */
    function initSettingsToggles() {
        const toggles = document.querySelectorAll('[id^="enable_"]');
        
        console.log('Found', toggles.length, 'notification type toggles');
        
        toggles.forEach(toggle => {
            toggle.addEventListener('change', function() {
                toggleNotificationOptions(this);
            });
            
            // Initialize state on load
            toggleNotificationOptions(toggle);
        });
    }

    /**
     * Toggle notification options based on main switch state
     */
    function toggleNotificationOptions(toggle) {
        const container = toggle.closest('.notification-setting-item');
        if (!container) {
            console.error('Container not found for toggle:', toggle.id);
            return;
        }
        
        const options = container.querySelector('.notification-options');
        if (!options) {
            console.error('Options container not found for toggle:', toggle.id);
            return;
        }
        
        const inputs = options.querySelectorAll('input, select');
        
        if (toggle.checked) {
            options.classList.remove('disabled');
            inputs.forEach(input => input.disabled = false);
        } else {
            options.classList.add('disabled');
            inputs.forEach(input => input.disabled = true);
        }
    }

    /**
     * Collect all notification settings from the form
     */
    function collectSettings() {
        const settings = {};
        const toggles = document.querySelectorAll('[id^="enable_"]');
        
        toggles.forEach(toggle => {
            // Extract type from id (e.g., "enable_farrow_due" -> "farrow_due")
            const type = toggle.id.replace('enable_', '');
            
            const pushCheckbox = document.getElementById(`${type}_push`);
            const emailCheckbox = document.getElementById(`${type}_email`);
            const smsCheckbox = document.getElementById(`${type}_sms`);
            const daysSelect = document.querySelector(`[name="${type}_days_before"]`);
            
            settings[type] = {
                is_enabled: toggle.checked,
                push_enabled: pushCheckbox ? pushCheckbox.checked : false,
                email_enabled: emailCheckbox ? emailCheckbox.checked : false,
                sms_enabled: smsCheckbox ? smsCheckbox.checked : false,
                days_before: daysSelect ? parseInt(daysSelect.value) : 0
            };
            
            console.log('Collected settings for', type, ':', settings[type]);
        });
        
        return settings;
    }

    /**
     * Save notification settings
     */
    async function saveSettings() {
        const btn = document.getElementById('saveSettings');
        if (!btn) return;
        
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        btn.disabled = true;
        
        const settings = collectSettings();
        console.log('Saving settings:', settings);
        
        try {
            const data = await apiRequest(API.updateSettings, 'POST', settings);
            
            if (data.success) {
                btn.innerHTML = '<i class="fas fa-check"></i> Saved!';
                btn.classList.remove('btn-primary');
                btn.classList.add('btn-success');
                
                showToast('Settings saved successfully', 'success');
                
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-primary');
                    btn.disabled = false;
                }, 2000);
            } else {
                throw new Error(data.error || 'Failed to save');
            }
        } catch (error) {
            console.error('Save settings error:', error);
            btn.innerHTML = '<i class="fas fa-times"></i> Error';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-danger');
            
            showToast('Failed to save settings: ' + error.message, 'error');
            
            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.classList.remove('btn-danger');
                btn.classList.add('btn-primary');
                btn.disabled = false;
            }, 2000);
        }
    }

    /**
     * Enable all notification types
     */
    function enableAllNotifications() {
        const toggles = document.querySelectorAll('[id^="enable_"]');
        
        toggles.forEach(toggle => {
            toggle.checked = true;
            toggleNotificationOptions(toggle);
        });
        
        showToast('All notifications enabled - click Save to apply', 'info');
    }

    /**
     * Disable all notification types
     */
    function disableAllNotifications() {
        const toggles = document.querySelectorAll('[id^="enable_"]');
        
        toggles.forEach(toggle => {
            toggle.checked = false;
            toggleNotificationOptions(toggle);
        });
        
        showToast('All notifications disabled - click Save to apply', 'info');
    }

    /**
     * Initialize notification settings page
     */
    function initNotificationSettings() {
        console.log('Initializing notification settings...');
        
        // Initialize toggle switches
        initSettingsToggles();
        
        // Save settings button
        const saveBtn = document.getElementById('saveSettings');
        if (saveBtn) {
            saveBtn.addEventListener('click', function(e) {
                e.preventDefault();
                saveSettings();
            });
            console.log('Save button initialized');
        }
        
        // Enable all button
        const enableAllBtn = document.getElementById('enableAll');
        if (enableAllBtn) {
            enableAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                enableAllNotifications();
            });
            console.log('Enable all button initialized');
        }
        
        // Disable all button
        const disableAllBtn = document.getElementById('disableAll');
        if (disableAllBtn) {
            disableAllBtn.addEventListener('click', function(e) {
                e.preventDefault();
                disableAllNotifications();
            });
            console.log('Disable all button initialized');
        }
        
        console.log('Notification settings initialized successfully');
    }

    // ==========================================
    // KEYBOARD SHORTCUTS
    // ==========================================
    
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Escape to close dropdowns
            if (e.key === 'Escape') {
                document.querySelectorAll('.dropdown-menu.show').forEach(m => {
                    m.classList.remove('show');
                });
            }
            
            // Ctrl/Cmd + S to save settings (on settings page)
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                const saveBtn = document.getElementById('saveSettings');
                if (saveBtn && !saveBtn.disabled) {
                    e.preventDefault();
                    saveSettings();
                }
            }
            
            // R to refresh notifications (on list page)
            if (e.key === 'r' && !e.ctrlKey && !e.metaKey && !isTyping()) {
                const refreshBtn = document.getElementById('refreshNotifications');
                if (refreshBtn) {
                    e.preventDefault();
                    refreshNotifications();
                }
            }
        });
    }

    /**
     * Check if user is currently typing in an input
     */
    function isTyping() {
        const activeElement = document.activeElement;
        return activeElement && (
            activeElement.tagName === 'INPUT' ||
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.tagName === 'SELECT' ||
            activeElement.isContentEditable
        );
    }

    // ==========================================
    // INITIALIZATION
    // ==========================================
    
    /**
     * Detect which page we're on and initialize appropriate functionality
     */
    function detectPageAndInit() {
        console.log('Notifications.js initializing...');
        
        // Add toast styles
        addToastStyles();
        
        // Initialize dropdowns (common to both pages)
        document.addEventListener('click', closeDropdownsOnOutsideClick);
        
        // Initialize keyboard shortcuts
        initKeyboardShortcuts();
        
        // Check if we're on the notification list page
        const isListPage = document.getElementById('notificationsList') || 
                          document.getElementById('refreshNotifications') ||
                          document.getElementById('markAllRead');
        
        if (isListPage) {
            console.log('Detected: Notification List Page');
            initNotificationList();
        }
        
        // Check if we're on the settings page
        const isSettingsPage = document.getElementById('notificationSettingsForm') || 
                               document.getElementById('saveSettings');
        
        if (isSettingsPage) {
            console.log('Detected: Notification Settings Page');
            initNotificationSettings();
        }
        
        console.log('Notifications.js initialization complete');
    }

    // ==========================================
    // PUBLIC API
    // ==========================================
    
    // Expose functions globally for debugging and inline handlers
    window.NotificationManager = {
        markAsRead,
        dismissNotification,
        markAllAsRead,
        refreshNotifications,
        saveSettings,
        enableAllNotifications,
        disableAllNotifications,
        filterNotifications,
        showToast
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', detectPageAndInit);
    } else {
        detectPageAndInit();
    }

})();
