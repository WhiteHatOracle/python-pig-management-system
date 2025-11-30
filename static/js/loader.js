// ============================================
// LOADER FUNCTIONALITY
// ============================================

(function() {
    'use strict';

    // ============================================
    // PAGE LOADER
    // ============================================
    
    const pageLoader = document.getElementById('page-loader');
    const miniLoader = document.getElementById('mini-loader');
    
    // Hide page loader when DOM is ready
    function hidePageLoader() {
        if (pageLoader) {
            pageLoader.classList.add('hidden');
            // Remove from DOM after animation
            setTimeout(() => {
                pageLoader.style.display = 'none';
            }, 400);
        }
    }
    
    // Show page loader
    function showPageLoader() {
        if (pageLoader) {
            pageLoader.style.display = 'flex';
            pageLoader.classList.remove('hidden');
        }
    }
    
    // Hide loader when page is fully loaded
    window.addEventListener('load', function() {
        // Add small delay for smoother experience
        setTimeout(hidePageLoader, 300);
    });
    
    // Fallback: Hide loader after max 5 seconds
    setTimeout(hidePageLoader, 5000);
    
    // ============================================
    // NAVIGATION LOADER
    // ============================================
    
    // Show loader on page navigation (internal links)
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a');
        
        if (link && 
            link.href && 
            !link.target && 
            !link.hasAttribute('download') &&
            !link.href.startsWith('#') &&
            !link.href.startsWith('javascript:') &&
            !link.href.startsWith('mailto:') &&
            !link.href.startsWith('tel:') &&
            link.hostname === window.location.hostname) {
            
            // Don't show loader for same page links
            if (link.pathname === window.location.pathname && link.search === window.location.search) {
                return;
            }
            
            showPageLoader();
        }
    });
    
    // Show loader on browser back/forward
    window.addEventListener('pageshow', function(e) {
        if (e.persisted) {
            hidePageLoader();
        }
    });
    
    // ============================================
    // FORM SUBMISSION LOADER
    // ============================================
    
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"], .submit-btn');
        
        // Skip AJAX forms
        if (form.hasAttribute('data-ajax') || form.classList.contains('ajax-form')) {
            return;
        }
        
        // Add loading state to button
        if (submitBtn) {
            submitBtn.classList.add('btn-loading');
            submitBtn.disabled = true;
        }
        
        // Show mini loader
        showMiniLoader();
    });
    
    // ============================================
    // MINI LOADER (AJAX/Fetch)
    // ============================================
    
    function showMiniLoader() {
        if (miniLoader) {
            miniLoader.classList.add('active');
        }
    }
    
    function hideMiniLoader() {
        if (miniLoader) {
            miniLoader.classList.remove('active');
        }
    }
    
    // Intercept fetch requests
    const originalFetch = window.fetch;
    let activeRequests = 0;
    
    window.fetch = function(...args) {
        activeRequests++;
        showMiniLoader();
        
        return originalFetch.apply(this, args)
            .then(response => {
                activeRequests--;
                if (activeRequests === 0) {
                    hideMiniLoader();
                }
                return response;
            })
            .catch(error => {
                activeRequests--;
                if (activeRequests === 0) {
                    hideMiniLoader();
                }
                throw error;
            });
    };
    
    // ============================================
    // BUTTON LOADING STATE
    // ============================================
    
    function setButtonLoading(button, loading = true) {
        if (!button) return;
        
        if (loading) {
            button.classList.add('btn-loading');
            button.disabled = true;
            button.setAttribute('data-original-text', button.innerHTML);
        } else {
            button.classList.remove('btn-loading');
            button.disabled = false;
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
            }
        }
    }
    
    // ============================================
    // SECTION LOADER
    // ============================================
    
    function showSectionLoader(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return;
        
        // Create loader if doesn't exist
        let loader = section.querySelector('.section-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.className = 'section-loader';
            loader.innerHTML = '<div class="section-spinner"></div>';
            section.style.position = 'relative';
            section.appendChild(loader);
        }
        
        loader.classList.add('active');
    }
    
    function hideSectionLoader(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return;
        
        const loader = section.querySelector('.section-loader');
        if (loader) {
            loader.classList.remove('active');
        }
    }
    
    // ============================================
    // PROGRESS BAR LOADER
    // ============================================
    
    // Create progress bar if it doesn't exist
    function createProgressBar() {
        let progressLoader = document.querySelector('.progress-loader');
        if (!progressLoader) {
            progressLoader = document.createElement('div');
            progressLoader.className = 'progress-loader';
            progressLoader.innerHTML = '<div class="progress-bar"></div>';
            document.body.prepend(progressLoader);
        }
        return progressLoader;
    }
    
    function showProgressBar(indeterminate = true) {
        const progressLoader = createProgressBar();
        const progressBar = progressLoader.querySelector('.progress-bar');
        
        progressLoader.classList.add('active');
        
        if (indeterminate) {
            progressBar.classList.add('indeterminate');
            progressBar.style.width = '';
        }
    }
    
    function updateProgressBar(percent) {
        const progressLoader = createProgressBar();
        const progressBar = progressLoader.querySelector('.progress-bar');
        
        progressLoader.classList.add('active');
        progressBar.classList.remove('indeterminate');
        progressBar.style.width = `${Math.min(100, Math.max(0, percent))}%`;
    }
    
    function hideProgressBar() {
        const progressLoader = document.querySelector('.progress-loader');
        if (progressLoader) {
            const progressBar = progressLoader.querySelector('.progress-bar');
            progressBar.style.width = '100%';
            
            setTimeout(() => {
                progressLoader.classList.remove('active');
                progressBar.classList.remove('indeterminate');
                progressBar.style.width = '0%';
            }, 300);
        }
    }
    
    // ============================================
    // SKELETON LOADER HELPERS
    // ============================================
    
    function createSkeleton(type = 'text', options = {}) {
        const skeleton = document.createElement('div');
        skeleton.className = `skeleton skeleton-${type}`;
        
        if (type === 'text' && options.width) {
            skeleton.classList.add(options.width); // 'short', 'medium', 'long'
        }
        
        if (options.className) {
            skeleton.classList.add(options.className);
        }
        
        return skeleton;
    }
    
    function replaceSkeleton(skeletonElement, content) {
        if (skeletonElement && skeletonElement.parentNode) {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = content;
            const newElement = wrapper.firstChild;
            
            newElement.style.opacity = '0';
            skeletonElement.parentNode.replaceChild(newElement, skeletonElement);
            
            // Fade in animation
            requestAnimationFrame(() => {
                newElement.style.transition = 'opacity 0.3s ease';
                newElement.style.opacity = '1';
            });
        }
    }
    
    // ============================================
    // EXPOSE GLOBAL API
    // ============================================
    
    window.Loader = {
        // Page loader
        showPage: showPageLoader,
        hidePage: hidePageLoader,
        
        // Mini loader
        showMini: showMiniLoader,
        hideMini: hideMiniLoader,
        
        // Button loading
        setButton: setButtonLoading,
        
        // Section loader
        showSection: showSectionLoader,
        hideSection: hideSectionLoader,
        
        // Progress bar
        showProgress: showProgressBar,
        updateProgress: updateProgressBar,
        hideProgress: hideProgressBar,
        
        // Skeleton
        createSkeleton: createSkeleton,
        replaceSkeleton: replaceSkeleton
    };
    
})();