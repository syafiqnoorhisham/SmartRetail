/**
 * SmartRetail Mobile Navigation
 * Handles mobile menu toggle and responsive behavior
 */

(function() {
    'use strict';
    
    // Wait for DOM to be fully loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        // Create mobile menu button
        createMobileMenuButton();
        
        // Setup event listeners
        setupEventListeners();
        
        // Handle window resize
        handleResize();
        window.addEventListener('resize', debounce(handleResize, 250));
    }
    
    /**
     * Create the mobile menu button and overlay
     */
    function createMobileMenuButton() {
        const dashboardContainer = document.querySelector('.dashboard-container');
        if (!dashboardContainer) return;
        
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.id = 'sidebarOverlay';
        dashboardContainer.appendChild(overlay);
        
        // Create mobile menu button
        const menuButton = document.createElement('button');
        menuButton.className = 'mobile-menu-btn';
        menuButton.id = 'mobileMenuBtn';
        menuButton.setAttribute('aria-label', 'Toggle menu');
        menuButton.setAttribute('aria-expanded', 'false');
        menuButton.innerHTML = `
            <div class="hamburger">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        document.body.appendChild(menuButton);
    }
    
    /**
     * Setup all event listeners
     */
    function setupEventListeners() {
        const menuBtn = document.getElementById('mobileMenuBtn');
        const overlay = document.getElementById('sidebarOverlay');
        const sidebar = document.querySelector('.sidebar');
        const navItems = document.querySelectorAll('.nav-item');
        
        if (!menuBtn || !sidebar) return;
        
        // Toggle menu on button click
        menuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMenu();
        });
        
        // Close menu on overlay click
        if (overlay) {
            overlay.addEventListener('click', closeMenu);
        }
        
        // Close menu when navigation item is clicked on mobile
        navItems.forEach(function(item) {
            item.addEventListener('click', function() {
                if (window.innerWidth < 768) {
                    closeMenu();
                }
            });
        });
        
        // Handle escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) {
                closeMenu();
            }
        });
        
        // Prevent body scroll when menu is open
        document.body.addEventListener('touchmove', function(e) {
            if (sidebar.classList.contains('open') && !sidebar.contains(e.target)) {
                e.preventDefault();
            }
        }, { passive: false });
    }
    
    /**
     * Toggle mobile menu
     */
    function toggleMenu() {
        const sidebar = document.querySelector('.sidebar');
        const menuBtn = document.getElementById('mobileMenuBtn');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (!sidebar || !menuBtn) return;
        
        const isOpen = sidebar.classList.contains('open');
        
        if (isOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }
    
    /**
     * Open mobile menu
     */
    function openMenu() {
        const sidebar = document.querySelector('.sidebar');
        const menuBtn = document.getElementById('mobileMenuBtn');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (!sidebar || !menuBtn) return;
        
        sidebar.classList.add('open');
        menuBtn.classList.add('active');
        menuBtn.setAttribute('aria-expanded', 'true');
        
        if (overlay) {
            overlay.classList.add('active');
        }
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        // Focus trap
        trapFocus(sidebar);
    }
    
    /**
     * Close mobile menu
     */
    function closeMenu() {
        const sidebar = document.querySelector('.sidebar');
        const menuBtn = document.getElementById('mobileMenuBtn');
        const overlay = document.getElementById('sidebarOverlay');
        
        if (!sidebar || !menuBtn) return;
        
        sidebar.classList.remove('open');
        menuBtn.classList.remove('active');
        menuBtn.setAttribute('aria-expanded', 'false');
        
        if (overlay) {
            overlay.classList.remove('active');
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
        
        // Return focus to menu button
        menuBtn.focus();
    }
    
    /**
     * Handle window resize
     */
    function handleResize() {
        const sidebar = document.querySelector('.sidebar');
        const menuBtn = document.getElementById('mobileMenuBtn');
        
        if (!sidebar || !menuBtn) return;
        
        // Close menu if window is resized to desktop size
        if (window.innerWidth >= 768 && sidebar.classList.contains('open')) {
            closeMenu();
        }
        
        // Show/hide menu button based on screen size
        if (window.innerWidth >= 768) {
            menuBtn.style.display = 'none';
            document.body.style.overflow = '';
        } else {
            menuBtn.style.display = 'flex';
        }
    }
    
    /**
     * Trap focus within sidebar when menu is open
     * @param {HTMLElement} element - The element to trap focus within
     */
    function trapFocus(element) {
        const focusableElements = element.querySelectorAll(
            'a[href], button:not([disabled]), input:not([disabled])'
        );
        
        if (focusableElements.length === 0) return;
        
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        
        element.addEventListener('keydown', function(e) {
            if (e.key !== 'Tab') return;
            
            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstFocusable) {
                    e.preventDefault();
                    lastFocusable.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastFocusable) {
                    e.preventDefault();
                    firstFocusable.focus();
                }
            }
        });
    }
    
    /**
     * Debounce function to limit function calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = function() {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Smooth scroll to top for mobile
     */
    function addScrollToTop() {
        // Create scroll to top button
        const scrollBtn = document.createElement('button');
        scrollBtn.className = 'scroll-to-top';
        scrollBtn.innerHTML = '↑';
        scrollBtn.setAttribute('aria-label', 'Scroll to top');
        scrollBtn.style.cssText = `
            display: none;
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 48px;
            height: 48px;
            background: #fff;
            border: 2px solid #00C853;
            border-radius: 50%;
            color: #00C853;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 999;
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(scrollBtn);
        
        // Show/hide button based on scroll position
        window.addEventListener('scroll', debounce(function() {
            if (window.pageYOffset > 300) {
                scrollBtn.style.display = 'flex';
                scrollBtn.style.alignItems = 'center';
                scrollBtn.style.justifyContent = 'center';
            } else {
                scrollBtn.style.display = 'none';
            }
        }, 100));
        
        // Scroll to top on click
        scrollBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Add scroll to top button on mobile
    if (window.innerWidth < 768) {
        addScrollToTop();
    }
    
    /**
     * Handle touch swipe to close menu
     */
    function setupSwipeGesture() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;
        
        let touchStartX = 0;
        let touchEndX = 0;
        
        sidebar.addEventListener('touchstart', function(e) {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        sidebar.addEventListener('touchend', function(e) {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });
        
        function handleSwipe() {
            const swipeDistance = touchEndX - touchStartX;
            // Swipe left to close (threshold: 50px)
            if (swipeDistance < -50 && sidebar.classList.contains('open')) {
                closeMenu();
            }
        }
    }
    
    setupSwipeGesture();
    
    // Log initialization
    console.log('SmartRetail Mobile Navigation initialized');
})();
